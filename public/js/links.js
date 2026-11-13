// Inline links in kit text (skills, mechanics, sub-moves, DMG colours) and jump/highlight.
import {$, COLOR_HEX, detailView, DMG_SUFFIXES, regexEsc, state} from './core.js';
import {setTab} from './detail.js';
import {t} from './i18n.js';
import {openMechanic} from './mechanics.js';

export function linkifyAll() {
  const c = state.current;
  if (!c) return;
  const byText = new Map();
  (c.skills || []).forEach((s, i) => {
    if (s.name && !byText.has(s.name)) byText.set(s.name, {type: 'skill', index: i, text: s.name});
  });
  for (const m of state.mechanics) {
    // Resonator-specific mechanics only link on their owner's page.
    if (m.owners?.length && !m.owners.includes(c.slug)) continue;
    for (const text of [m.term, ...(m.aliases || [])]) {
      if (!byText.has(text)) byText.set(text, {type: 'mech', term: m.term, text});
    }
  }
  const moveNames = [...movesOf(c).keys()];
  const moveSet = new Set(moveNames);
  const typePref = /^(?:Basic Attack|Heavy Attack|Mid-air Attack|Dodge Counter|Plunging Attack|Resonance Skill|Resonance Liberation|Intro Skill|Outro Skill|Forte Circuit|Inherent Skill|Echo Skill|Enhanced Heavy Attack|Enhanced Basic Attack)\s+-\s+(.+)$/;
  for (const name of moveNames) {
    const m = name.match(typePref);
    if (m && moveSet.has(m[1])) continue; // prefer linking the bare move name inside "Type - Name"
    if (!byText.has(name)) byText.set(name, {type: 'move', term: name, text: name});
  }
  for (const text of state.noLink) {
    if (!byText.has(text)) byText.set(text, {type: 'plain', text});
  }
  for (const el of Object.keys(COLOR_HEX)) {
    for (const suffix of DMG_SUFFIXES) {
      const text = el + suffix;
      if (!byText.has(text)) byText.set(text, {type: 'dmg', el: el.toLowerCase(), text});
    }
  }
  const terms = [...byText.values()].sort((a, b) => b.text.length - a.text.length);
  if (!terms.length) return;
  const re = new RegExp('(?<![A-Za-z0-9])(' + terms.map((t) => regexEsc(t.text)).join('|') + ')(?![A-Za-z0-9])', 'g');

  detailView.querySelectorAll('.skill-body, .chain-body').forEach((body) => {
    const section = body.closest('.skill');
    const ownIndex = section ? Number(section.dataset.index) : -1;
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        if (node.parentElement?.closest('a,button,.scaling')) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    // Only the first mention of a term in each section gets the full link style;
    // later mentions stay clickable but quiet, so long descriptions aren't noisy.
    const seen = new Set();
    for (const node of nodes) {
      const text = node.nodeValue;
      re.lastIndex = 0;
      let match, last = 0;
      const frag = document.createDocumentFragment();
      while ((match = re.exec(text))) {
        const matched = match[1];
        const term = byText.get(matched);
        if (!term) continue;
        if (term.type === 'skill' && term.index === ownIndex) continue;
        if (term.type === 'plain') {  // consumed as plain text: no link
          if (match.index > last) frag.appendChild(document.createTextNode(text.slice(last, match.index)));
          frag.appendChild(document.createTextNode(matched));
          last = match.index + matched.length;
          continue;
        }
        if (match.index > last) frag.appendChild(document.createTextNode(text.slice(last, match.index)));
        const tn = makeTermNode(term, matched);
        if (term.type !== 'dmg') {
          const key = term.type + ':' + (term.term ?? term.index);
          if (seen.has(key)) tn.classList.add('repeat'); else seen.add(key);
        }
        frag.appendChild(tn);
        last = match.index + matched.length;
      }
      if (!last) continue;
      if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    }
  });
}

/* ---------- sub-moves ("Basic Attack Hounds Roar", "Heavy Attack - Thunderoar: Backstep") ---------- */
// Named sub-moves of one Resonator ("Basic Attack Hounds Roar", Heavy Attack "Mercy"), each with
// the line that best defines it. Derived at build time (scripts/kit_rules.py -> /api/index).
export const moveCache = new Map();
export function movesOf(c) {
  if (!moveCache.has(c.slug)) moveCache.set(c.slug, new Map(Object.entries(state.index.chars[c.slug]?.moves || {})));
  return moveCache.get(c.slug);
}

export function openMove(name) {
  const c = state.current;
  const ref = movesOf(c).get(name);
  if (!ref) return;
  const src = ref.kind === 'skill' ? c.skills[ref.index] : (c.resonance_chain || []).find((n) => n.node === ref.index);
  const lines = (state.showEn || !(src.desc_vi || []).length ? src.desc : src.desc_vi) || [];
  const def = (lines[ref.line] || '').replace(/^• /, '');
  openMechanic({term: name, kind: 'move', owners: [c.slug], summary_vi: def, summary_en: def,
    source: t('move_from', {skill: ref.title}), target: (ref.kind === 'skill' ? 'skill-' : 'chain-') + ref.index});
}

export function makeTermNode(term, text) {
  if (term.type === 'move') {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'term-link move-link';
    b.dataset.move = term.term;
    b.textContent = text;
    return b;
  }
  if (term.type === 'dmg') {
    const span = document.createElement('span');
    span.className = `dmg dmg-${term.el}`;
    span.textContent = text;
    return span;
  }
  if (term.type === 'skill') {
    const a = document.createElement('a');
    a.href = `#skill-${term.index}`;
    a.className = 'term-link skill-link';
    a.dataset.skill = String(term.index);
    a.textContent = text;
    return a;
  }
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'term-link mech-link';
  b.dataset.mech = term.term;
  b.textContent = text;
  return b;
}

export function scrollToSkill(index) {
  scrollToId('skill-' + index);
}

// Scroll to a skill/chain section (switching to its tab). With a term, highlight
// only the paragraphs that mention it, and the term itself, instead of the whole section.
export function scrollToId(id, term = '', line = null) {
  if (id.startsWith('skill-')) setTab('skills');
  else if (id.startsWith('chain-')) setTab('chain');
  const el = $(id);
  if (!el) return;
  detailView.querySelectorAll('.hit, .hit-term').forEach((x) => x.classList.remove('hit', 'hit-term'));
  let hits = [];
  if (line !== null && line !== '' && !Number.isNaN(Number(line))) {
    hits = [...el.querySelectorAll(`.skill-body [data-line="${Number(line)}"], .chain-body [data-line="${Number(line)}"]`)];
  }
  if (!hits.length && term) {
    const terms = [...el.querySelectorAll('.mech-link, .move-link')].filter((b) => (b.dataset.mech || b.dataset.move) === term);
    terms.forEach((b) => b.classList.add('hit-term'));
    hits = [...new Set(terms.map((b) => b.closest('p, li')).filter(Boolean))];
    if (!hits.length) hits = [...el.querySelectorAll('.skill-body p, .skill-body li, .chain-body p, .chain-body li')].filter((x) => x.textContent.includes(term));
  }
  if (hits.length) {
    hits.forEach((h) => h.classList.add('hit'));
    hits[0].scrollIntoView({behavior: 'smooth', block: 'center'});
    // one timer at a time: an older highlight's timer must not wipe this one
    clearTimeout(scrollToId.timer);
    scrollToId.timer = setTimeout(() => detailView.querySelectorAll('.hit, .hit-term').forEach((x) => x.classList.remove('hit', 'hit-term')), 6000);
  } else {
    el.scrollIntoView({behavior: 'smooth', block: 'start'});
    el.classList.remove('flash');
    void el.offsetWidth;
    el.classList.add('flash');
    setTimeout(() => el.classList.remove('flash'), 1900);
  }
  el.focus({preventScroll: true});
}

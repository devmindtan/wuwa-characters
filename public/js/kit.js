// Profile tabs: combat skills, level scaling, Forte tree, Resonance Chain, materials, references.
import {$, dChain, detailView, dSkills, esc, state} from './core.js';
import {t} from './i18n.js';
import {linkifyAll} from './links.js';

export function lineHTML(line) {
  if (line.startsWith('• ')) return {li: true, text: line.slice(2)};
  const short = line.length < 72 && !/[.!?]$/.test(line);
  return {li: false, text: line, sub: short};
}

export function linesHTML(lines) {
  let body = '', inList = false;
  for (const [i, line] of lines.entries()) {
    const l = lineHTML(line);
    if (l.li) {
      if (!inList) { body += '<ul>'; inList = true; }
      body += `<li data-line="${i}">${esc(l.text)}</li>`;
    } else {
      if (inList) { body += '</ul>'; inList = false; }
      body += `<p data-line="${i}"${l.sub ? ' class="sub"' : ''}>${esc(l.text)}</p>`;
    }
  }
  if (inList) body += '</ul>';
  return body;
}

export function renderSkills() {
  const c = state.current;
  if (!c) return;
  let out = '';
  (c.skills || []).forEach((s, i) => {
    const body = linesHTML((state.showEn ? s.desc : s.desc_vi) || []) || `<p>${esc(t('no_desc'))}</p>`;
    out += `<section class="skill" id="skill-${i}" data-index="${i}" tabindex="-1">
      <div class="skill-head">${skillIcon(s, 'skill-ico')}<span class="skill-type">${esc(s.type)}</span><h3>${esc(s.name)}</h3></div>
      <div class="skill-body">${body}</div>
      ${scaleHTML(s, i)}
    </section>`;
  });
  dSkills.innerHTML = out;
  dSkills.lang = state.showEn ? 'en' : 'vi';
  renderTree();
  renderChain();
  renderIntro();
  linkifyAll();
  applyLevel();
}

/* ---------- level scaling: slider + progress bars ---------- */
export const LEVELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
export const valueAt = (row, lv) => (row.values.length === 1 ? row.values[0] : row.values[lv - 1] ?? '—');
export const leveled = (s) => (s.scaling?.rows || []).filter((r) => r.values.length > 1);
export const constants = (s) => (s.scaling?.rows || []).filter((r) => r.values.length === 1);

// Total multiplier of a wiki value such as "19.61%+9.81%*3" (= 49.04). NaN if not numeric.
export function totalOf(v) {
  if (typeof v !== 'string' || !/\d/.test(v)) return NaN;
  let sum = 0;
  for (const term of v.replace(/%/g, '').replace(/\s/g, '').split('+')) {
    const [a, n] = term.split('*');
    const x = parseFloat(a) * (n === undefined ? 1 : parseFloat(n));
    if (!Number.isFinite(x)) return NaN;
    sum += x;
  }
  return sum;
}

export const TYPE_MONO = {'Basic Attack': 'BA', 'Resonance Skill': 'RS', 'Forte Circuit': 'FC', 'Resonance Liberation': 'RL',
  'Intro Skill': 'IN', 'Outro Skill': 'OU', 'Inherent Skill': 'IS'};
export const skillIcon = (s, cls) => `<span class="${cls}" aria-hidden="true">${s.icon
  ? `<img src="${esc(s.icon)}" alt="" loading="lazy" referrerpolicy="no-referrer">`
  : `<b>${esc(TYPE_MONO[s.type] || '?')}</b>`}</span>`;

/* Multipliers panel: "Lv. N" slider + striped rows (label left, value right). */
export function scaleHTML(s, i, open = false) {
  const rows = leveled(s);
  const consts = constants(s);
  if (!rows.length && !consts.length) {
    return open ? `<p class="tn-muted">${esc(t('no_scaling'))}</p>` : '';
  }
  return `<details class="mult" data-si="${i}"${open ? ' open' : ''}>
    <summary>${esc(t('mult_title'))} <svg viewBox="0 0 12 8" aria-hidden="true"><path d="M1 6.5 6 1.5l5 5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></summary>
    <div class="mult-body">
      ${rows.length ? `<label class="mult-lv"><span>Lv. <b class="lv-num">${state.level}</b></span>
        <input type="range" class="lv-range" min="1" max="10" step="1" value="${state.level}" aria-label="${esc(t('lv_aria'))}"></label>` : ''}
      <ul class="mult-rows">
        ${rows.map((r, ri) => `<li data-ri="${ri}"><span>${esc(r.label)}</span><b class="sr-val"></b></li>`).join('')}
        ${consts.map((r) => `<li><span>${esc(r.label)}</span><b>${esc(r.values[0])}</b></li>`).join('')}
      </ul>
      ${s.scaling?.source ? `<p class="scaling-src">${esc(t('source'))}: <a href="${esc(s.scaling.source)}" target="_blank" rel="noopener noreferrer">Wuthering Waves Wiki — ${esc(s.name)}</a></p>` : ''}
    </div>
  </details>`;
}

// Push state.level into every slider, value and tree badge on the detail page.
export function applyLevel() {
  const c = state.current;
  if (!c) return;
  const lv = state.level;
  detailView.querySelectorAll('.lv-range').forEach((r) => { r.value = String(lv); r.style.setProperty('--p', `${((lv - 1) / 9) * 100}%`); });
  detailView.querySelectorAll('.lv-num').forEach((n) => { n.textContent = String(lv); });
  detailView.querySelectorAll('.mult[data-si]').forEach((box) => {
    const rows = leveled(c.skills[Number(box.dataset.si)]);
    box.querySelectorAll('.mult-rows li[data-ri]').forEach((li) => {
      li.querySelector('.sr-val').textContent = valueAt(rows[Number(li.dataset.ri)], lv);
    });
  });
  detailView.querySelectorAll('.fn-lv b').forEach((b) => { b.textContent = String(lv); });
}

/* ---------- skill tree (in-game Forte layout) ---------- */
export const TREE_COLS = [
  {type: 'Basic Attack', label: 'Normal Attack', pos: 'outer'},
  {type: 'Resonance Skill', label: 'Resonance Skill', pos: 'inner'},
  {type: 'Forte Circuit', label: 'Forte Circuit', pos: 'center'},
  {type: 'Resonance Liberation', label: 'Resonance Liberation', pos: 'inner'},
  {type: 'Intro Skill', label: 'Intro Skill', pos: 'outer'},
];
export const TUNE_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" width="22" height="22"><path d="M3 12h3l2-5 3 10 3-12 2 7h5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
export const selKey = (sel) => 'skill-' + sel.i;

export function treeParts(c) {
  const skills = (c.skills || []).map((s, i) => ({...s, i}));
  const fortes = skills.filter((s) => s.type === 'Forte Circuit');
  const tune = fortes.filter((s) => /^Tune Break/.test(s.name));
  const mainForte = fortes.filter((s) => !/^Tune Break/.test(s.name));
  return {
    skills,
    byType: (type) => (type === 'Forte Circuit' ? mainForte.slice(0, 1) : skills.filter((s) => s.type === type).slice(0, 1)),
    inherent: skills.filter((s) => s.type === 'Inherent Skill'),
    outro: skills.find((s) => s.type === 'Outro Skill'),
    bottomExtra: [...tune, ...mainForte.slice(1)],
  };
}

export function renderTree() {
  const c = state.current;
  const parts = treeParts(c);
  if (!state.treeSel || (state.treeSel.kind === 'skill' && !c.skills[state.treeSel.i])) {
    const f = parts.byType('Forte Circuit')[0] || parts.skills[0];
    state.treeSel = {kind: 'skill', i: f ? f.i : 0};
  }
  const sk = selKey(state.treeSel);
  const diamond = (s, label, withLv = true) => `<button type="button" class="fn fn-diamond${sk === 'skill-' + s.i ? ' is-sel' : ''}" data-sel="skill-${s.i}" title="${esc(s.name)}" aria-label="${esc(label)}: ${esc(s.name)}">
      <span class="fn-shape">${skillIcon(s, 'fn-ico')}</span>
      ${withLv ? `<span class="fn-lv">Lv.<b>${state.level}</b>/10</span>` : ''}
      <span class="fn-label">${esc(label)}</span>
    </button>`;
  const circle = (key, inner, label, title) => `<button type="button" class="fn fn-circle${sk === key ? ' is-sel' : ''}" data-sel="${key}" title="${esc(title)}" aria-label="${esc(title)}">
      <span class="fn-shape">${inner}</span>${label ? `<span class="fn-label">${esc(label)}</span>` : ''}
    </button>`;
  const cols = TREE_COLS.map((col, ci) => {
    const main = parts.byType(col.type)[0];
    let nodes = '';
    if (col.pos === 'center') {
      const [in1, in2] = parts.inherent;
      // Both nodes are Inherent Skills: label each with its own name.
      nodes = (in2 ? diamond(in2, 'Inherent Skill: ' + in2.name, false) : '')
        + (in1 ? circle('skill-' + in1.i, skillIcon(in1, 'fn-ico'), 'Inherent Skill: ' + in1.name, 'Inherent Skill: ' + in1.name) : '');
    }
    return `<div class="fcol fcol-${col.pos}">${nodes}${main ? diamond(main, col.label) : `<span class="fn-empty">${esc(col.label)}</span>`}</div>`;
  }).join('');
  const bottom = [
    parts.outro ? circle('skill-' + parts.outro.i, skillIcon(parts.outro, 'fn-ico'), 'Outro Skill', 'Outro Skill: ' + parts.outro.name) : '',
    ...parts.bottomExtra.map((s) => {
      const tb = /^Tune Break/.test(s.name);
      const inner = tb && !s.icon ? `<span class="fn-ico">${TUNE_ICON}</span>` : skillIcon(s, 'fn-ico');
      return circle('skill-' + s.i, inner, tb ? 'Tune Break' : 'Forte Circuit', s.name);
    }),
  ].join('');
  $('d-tree').innerHTML = `<div class="forte-board">
      <div class="forte-cols">${cols}</div>
      <div class="forte-bottom">${bottom}</div>
    </div>`;
  renderTreeDetail();
  $('d-tree-note').textContent = t('tree_note');
}

export function renderTreeDetail() {
  const c = state.current;
  const sel = state.treeSel;
  const s = c.skills[sel.i];
  if (!s) { $('d-tree-detail').innerHTML = ''; return; }
  const lines = ((state.showEn ? s.desc : s.desc_vi) || []).filter((l) => !lineHTML(l).sub).slice(0, 2);
  $('d-tree-detail').innerHTML = `<div class="td-head">${skillIcon(s, 'td-ico')}
      <div><p class="td-type">${esc(s.type)}</p><h3>${esc(s.name)}</h3></div>
      <button type="button" class="btn td-go" data-goto="skill-${sel.i}">${esc(t('view_full'))} <span aria-hidden="true">→</span></button>
    </div>
    ${lines.length ? `<p class="td-desc">${esc(lines.map((l) => l.replace(/^• /, '')).join(' '))}</p>` : ''}
    ${scaleHTML(s, sel.i, true)}`;
}

/* ---------- resonance chain ---------- */
export function renderChain() {
  const c = state.current;
  const chain = c.resonance_chain || [];
  dChain.lang = state.showEn ? 'en' : 'vi';
  if (!chain.length) {
    dChain.innerHTML = `<p class="empty-note">${esc(t('chain_empty', {name: c.name}))}</p>`;
    return;
  }
  dChain.innerHTML = chain.map((n) => {
    const lines = (state.showEn || !(n.desc_vi || []).length) ? n.desc : n.desc_vi;
    return `<article class="chain-node" id="chain-${n.node}" tabindex="-1">
      <div class="chain-head">
        <div class="chain-icon">${n.img ? `<img src="${esc(n.img)}" alt="" loading="lazy" referrerpolicy="no-referrer" width="56" height="56">` : ''}<span>S${n.node}</span></div>
        <div><p class="chain-seq">Sequence Node · ${esc(t('sequence_node', {n: n.node}))}</p><h3>${esc(n.name)}</h3></div>
      </div>
      <div class="chain-body">${linesHTML(lines || [])}</div>
    </article>`;
  }).join('');
}

/* ---------- materials & upgrade costs ---------- */
export const MAT_GROUPS = [['ascension', 'mat_ascension'], ['forte', 'mat_forte'], ['inherent', 'mat_inherent'], ['stat_bonus', 'mat_stat']];
export const qtyFmt = (n) => n.toLocaleString('vi-VN');

export function matCards(items) {
  return `<ul class="mat-list">${items.map((it) => `<li class="mat r${it.rarity}" title="${esc(it.name)}">
    <span class="mat-img">${it.img ? `<img src="${esc(it.img)}" alt="" loading="lazy" referrerpolicy="no-referrer" width="48" height="48">` : ''}</span>
    <span class="mat-qty">${qtyFmt(it.qty)}</span>
    <span class="mat-name">${esc(it.name)}</span>
  </li>`).join('')}</ul>`;
}

export function sumSteps(rows, upto) {
  const acc = new Map();
  rows.slice(0, upto).forEach((r) => r.items.forEach((it) => {
    const cur = acc.get(it.name);
    acc.set(it.name, cur ? {...cur, qty: cur.qty + it.qty} : {...it});
  }));
  // Shell Credit first, then by rarity and name (same order as the wiki totals).
  return [...acc.values()].sort((a, b) => (b.name === 'Shell Credit') - (a.name === 'Shell Credit')
    || a.rarity - b.rarity || a.name.localeCompare(b.name));
}

export function renderMaterials(c) {
  const mats = c.materials || {};
  const costs = c.level_costs || {};
  const groups = MAT_GROUPS.filter(([key]) => mats[key]?.items?.length || costs[key]?.length);
  $('tab-btn-mats').hidden = !groups.length;
  $('d-mats').innerHTML = groups.map(([key, tkey]) => {
    const title = t(tkey);
    const hint = t(tkey + '_hint');
    const rows = costs[key] || [];
    let body;
    if (key === 'forte' && rows.length) {
      const to = Math.min(state.forteTo, rows.length + 1);
      body = `<div class="upgrade" data-key="forte">
        <div class="up-head"><span>${t('up_from_to_html', {to})}</span><small class="up-steps-count">${esc(t('up_steps', {n: to - 1}))}</small></div>
        <input type="range" class="up-range" min="2" max="${rows.length + 1}" step="1" value="${to}" aria-label="${esc(t('up_aria'))}">
        <ol class="up-track">${rows.map((r, idx) => `<li class="${idx < to - 1 ? 'on' : ''}" title="${esc(r.level)}${r.ascension !== '-' ? ' · ' + esc(t('up_need', {a: r.ascension})) : ''}">
          <span class="up-dot">${idx + 2}</span>${r.ascension !== '-' ? `<span class="up-gate">${esc(r.ascension)}</span>` : ''}</li>`).join('')}</ol>
        <p class="up-note">${esc(t('up_note'))}</p>
        <div class="up-total">${matCards(sumSteps(rows, to - 1))}</div>
      </div>`;
    } else if (rows.length && key !== 'ascension') {
      body = `<ol class="steps">${rows.map((r, idx) => `<li class="step">
        <div class="step-head"><span class="step-no">${esc(t('step_no', {n: idx + 1}))}</span>${r.ascension !== '-' ? `<span class="up-gate">${esc(t('gate_need', {a: r.ascension}))}</span>` : ''}</div>
        ${matCards(r.items)}
      </li>`).join('')}</ol>`;
    } else {
      body = matCards(mats[key].items);
    }
    return `<section class="mat-group" data-key="${key}">
      <header><h3>${esc(title)}</h3><p>${esc(hint)}</p></header>
      ${body}
    </section>`;
  }).join('');
}

export function updateUpgrade(input) {
  const c = state.current;
  const rows = (c.level_costs || {}).forte || [];
  const to = Number(input.value);
  state.forteTo = to;
  const box = input.closest('.upgrade');
  box.querySelector('.up-to').textContent = `Lv ${to}`;
  box.querySelector('.up-steps-count').textContent = t('up_steps', {n: to - 1});
  box.querySelectorAll('.up-track li').forEach((li, idx) => li.classList.toggle('on', idx < to - 1));
  input.style.setProperty('--p', `${((to - 2) / (rows.length - 1)) * 100}%`);
  box.querySelector('.up-total').innerHTML = matCards(sumSteps(rows, to - 1));
}

export function renderReferences(c) {
  const refs = c.references || [{title: 'prydwen.gg', url: c.source, used_for: ''}];
  $('d-refs').innerHTML = refs.map((r) => {
    let host = '';
    try { host = new URL(r.url).hostname.replace(/^www\./, ''); } catch { /* keep empty */ }
    return `<li><a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.title)}</a>
      <span class="ref-host">${esc(host)}</span>${(state.showEn ? r.used_for_en : r.used_for) ? `<span class="ref-use">${esc(state.showEn ? r.used_for_en : r.used_for)}</span>` : ''}</li>`;
  }).join('');
}

export function renderIntro() {
  const c = state.current;
  const introEl = $('d-intro');
  const text = state.showEn ? c.intro : c.intro_vi;
  introEl.textContent = text || '';
  introEl.hidden = !text;
  introEl.lang = state.showEn ? 'en' : 'vi';
}

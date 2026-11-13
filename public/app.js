const EL_VI = {Spectro:'Quang Phổ',Havoc:'Hỗn Độn',Aero:'Khí',Electro:'Lôi',Fusion:'Nhiệt',Glacio:'Băng'};
const WEAP_VI = {Sword:'Kiếm',Broadblade:'Đại Kiếm',Pistols:'Súng Lục',Gauntlets:'Găng Tay',Rectifier:'Pháp Khí'};
// Official element text colors (in-game / Wuthering Waves Wiki dark theme).
const COLOR_HEX = {Spectro:'#F8E56C',Havoc:'#E649A6',Aero:'#55FFB5',Electro:'#B46BFF',Fusion:'#F0744E',Glacio:'#41AEFB'};
// "<Element> DMG ..." phrases are coloured by element (colour only, no bold).
const DMG_SUFFIXES = [' DMG Bonus', ' DMG Amplification', ' DMG RES', ' DMG', ' RES'];

const state = {
  meta: null,
  characters: [],
  mechanics: [],
  index: {rules: {}, chars: {}, mech_users: {}},  // /api/index (scripts/build_index.py)
  noLink: [],
  level: 10,
  treeSel: null,
  forteTo: 10,
  tab: 'tree',
  pendingTarget: null,
  roleFilter: 'all',
  mechTerm: null,
  bySlug: new Map(),
  current: null,
  lang: (() => { try { return localStorage.getItem('lang') === 'en' ? 'en' : 'vi'; } catch { return 'vi'; } })(),
  get showEn() { return this.lang === 'en'; },
  savedScroll: 0,
  detailOpen: false,
};

const $ = (id) => document.getElementById(id);
const grid = $('grid');
const empty = $('empty');
const loading = $('loading');
const errorBox = $('error');
const shown = $('shown');
const listView = $('listView');
const detailView = $('detailView');
const q = $('q');
const fEl = $('f-el');
const fWeap = $('f-weap');
const fR = $('f-r');
const backBtn = $('back');
const dSkills = $('d-skills');
const dChain = $('d-chain');
const mechDialog = $('mechDialog');

const esc = (s) => (s ?? '').toString().replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const stars = (r) => r ? '★'.repeat(r) : '';
const elColor = (el) => COLOR_HEX[el] || '#d6c4a1';
const regexEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const elVi = (el) => EL_VI[el] || el || '';
const weapVi = (w) => WEAP_VI[w] || w || '';

/* ---------- language ---------- */
function applyStaticI18n() {
  document.documentElement.lang = t('html_lang');
  document.querySelector('meta[name="description"]')?.setAttribute('content', t('meta_desc'));
  document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-html]').forEach((el) => { el.innerHTML = t(el.dataset.i18nHtml); });
  document.querySelectorAll('[data-i18n-attr]').forEach((el) => {
    for (const pair of el.dataset.i18nAttr.split(';')) {
      const [attr, key] = pair.split(':');
      el.setAttribute(attr, t(key));
    }
  });
  document.querySelectorAll('.lang-switch [data-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === state.lang)));
}

// (Re)build the three filter dropdowns in the current language, keeping selections.
function buildFilters() {
  const keep = {el: fEl.value, weap: fWeap.value, r: fR.value};
  document.querySelectorAll('.toolbar .dd').forEach((dd) => dd.remove());
  const vi = !state.showEn;
  const els = [...new Set(state.characters.map((c) => c.element).filter(Boolean))].sort();
  const weaps = [...new Set(state.characters.map((c) => c.weapon).filter(Boolean))].sort();
  const opts = (sel, all, values, label) => {
    sel.innerHTML = '';
    fillSelect(sel, [''], () => all);
    fillSelect(sel, values, label);
  };
  opts(fEl, t('all_elements'), els, (v) => (vi && EL_VI[v] ? `${v} · ${EL_VI[v]}` : v));
  opts(fWeap, t('all_weapons'), weaps, (v) => (vi && WEAP_VI[v] ? `${v} · ${WEAP_VI[v]}` : v));
  opts(fR, t('all_rarities'), ['5', '4'], (v) => t('rarity_n', {n: v}));
  fEl.value = keep.el; fWeap.value = keep.weap; fR.value = keep.r;
  enhanceSelect(fEl, elDot);
  enhanceSelect(fWeap, weapDot);
  enhanceSelect(fR, rarityMark);
}

function setLang(lang) {
  state.lang = lang === 'en' ? 'en' : 'vi';
  try { localStorage.setItem('lang', state.lang); } catch { /* private mode */ }
  if (mechDialog.open) mechDialog.close();
  applyStaticI18n();
  if (!state.meta) return;
  renderMeta();
  buildFilters();
  apply();
  if (state.current) {
    renderDetail(state.current);
    renderSkills();
    setTab(state.tab);
  }
}

function fillSelect(sel, values, labelFn) {
  values.forEach((v) => {
    const o = document.createElement('option');
    o.value = v;
    o.textContent = labelFn(v);
    sel.appendChild(o);
  });
}

/* ---------- custom dropdown (enhances a native <select>) ---------- */
let ddSeq = 0;
const openDropdowns = new Set();

function enhanceSelect(sel, decorate = () => '') {
  const id = 'dd' + (++ddSeq);
  const wrap = document.createElement('div');
  wrap.className = 'dd';
  wrap.innerHTML = `<button type="button" class="dd-btn" id="${id}-btn" aria-haspopup="listbox" aria-expanded="false" aria-controls="${id}-list">
      <span class="dd-value"></span><svg class="dd-caret" viewBox="0 0 12 8" aria-hidden="true"><path d="M1 1.5 6 6.5 11 1.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>
    </button>
    <ul class="dd-list" id="${id}-list" role="listbox" tabindex="-1" aria-label="${esc(sel.getAttribute('aria-label') || '')}" hidden></ul>`;
  sel.after(wrap);
  sel.hidden = true;
  sel.tabIndex = -1;
  const btn = wrap.querySelector('.dd-btn');
  const list = wrap.querySelector('.dd-list');
  const valueEl = wrap.querySelector('.dd-value');
  btn.setAttribute('aria-label', sel.getAttribute('aria-label') || '');
  const opts = [...sel.options];
  list.innerHTML = opts.map((o, i) =>
    `<li role="option" id="${id}-o${i}" data-i="${i}" class="dd-opt${o.value ? '' : ' dd-all'}">${decorate(o.value)}<span>${esc(o.textContent)}</span></li>`
  ).join('');
  const items = [...list.children];
  let active = 0;

  const sync = () => {
    const i = sel.selectedIndex;
    valueEl.innerHTML = decorate(sel.value) + `<span>${esc(opts[i].textContent)}</span>`;
    wrap.classList.toggle('has-value', !!sel.value);
    items.forEach((li, j) => li.setAttribute('aria-selected', String(j === i)));
  };
  const setActive = (i) => {
    active = (i + items.length) % items.length;
    items.forEach((li, j) => li.classList.toggle('active', j === active));
    list.setAttribute('aria-activedescendant', items[active].id);
    items[active].scrollIntoView({block: 'nearest'});
  };
  const open = () => {
    openDropdowns.forEach((close) => close());
    list.hidden = false;
    list.classList.remove('align-right');
    if (list.getBoundingClientRect().right > document.documentElement.clientWidth - 8) list.classList.add('align-right');
    btn.setAttribute('aria-expanded', 'true');
    wrap.classList.add('open');
    setActive(sel.selectedIndex);
    list.focus({preventScroll: true});
    openDropdowns.add(close);
  };
  function close(focusBtn) {
    if (list.hidden) return;
    list.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    wrap.classList.remove('open');
    openDropdowns.delete(close);
    if (focusBtn) btn.focus();
  }
  const choose = (i) => {
    if (sel.selectedIndex !== i) {
      sel.selectedIndex = i;
      sel.dispatchEvent(new Event('input', {bubbles: true}));
    }
    sync();
    close(true);
  };

  btn.addEventListener('click', () => (list.hidden ? open() : close(true)));
  btn.addEventListener('keydown', (e) => {
    if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) { e.preventDefault(); open(); }
  });
  list.addEventListener('keydown', (e) => {
    const k = e.key;
    if (k === 'ArrowDown') setActive(active + 1);
    else if (k === 'ArrowUp') setActive(active - 1);
    else if (k === 'Home') setActive(0);
    else if (k === 'End') setActive(items.length - 1);
    else if (k === 'Enter' || k === ' ') choose(active);
    else if (k === 'Escape') { e.stopPropagation(); close(true); }
    else if (k === 'Tab') { close(false); return; }
    else if (k.length === 1) {
      const from = active + 1;
      const hit = [...items.slice(from), ...items.slice(0, from)].find((li) => li.textContent.trim().toLowerCase().startsWith(k.toLowerCase()));
      if (hit) setActive(Number(hit.dataset.i));
      else return;
    } else return;
    e.preventDefault();
  });
  list.addEventListener('mousemove', (e) => {
    const li = e.target.closest('.dd-opt');
    if (li && Number(li.dataset.i) !== active) setActive(Number(li.dataset.i));
  });
  list.addEventListener('click', (e) => {
    const li = e.target.closest('.dd-opt');
    if (li) choose(Number(li.dataset.i));
  });
  list.addEventListener('focusout', (e) => { if (!wrap.contains(e.relatedTarget)) close(false); });
  sync();
}

document.addEventListener('pointerdown', (e) => {
  if (!e.target.closest('.dd')) openDropdowns.forEach((close) => close(false));
});

// Official in-game element/weapon icons, served from public/assets/icons/.
const icon = (kind, v, cls = '') => v
  ? `<img class="ico ico-${kind} ${cls}" src="assets/icons/${kind}/${esc(v.toLowerCase())}.png" alt="" aria-hidden="true" width="18" height="18" decoding="async">`
  : '';
const elIcon = (v, cls) => icon('element', v, cls);
const weapIcon = (v, cls) => icon('weapon', v, cls);
const elDot = (v) => elIcon(v, 'dd-ico');
const weapDot = (v) => weapIcon(v, 'dd-ico');
const rarityMark = (v) => v ? `<i class="dd-star r${v}">★</i>` : '';

function cardHTML(c) {
  const col = elColor(c.element);
  return `<article class="card" data-slug="${esc(c.slug)}" tabindex="0" role="button" aria-label="${esc(t('card_aria', {name: c.name}))}" style="--el:${col};--tint-soft:${col}22">
    <div class="card-media">
      <img src="${esc(c.img_card || c.img_icon)}" alt="${esc(c.name)}" loading="lazy" onerror="this.onerror=null;this.src='${esc(c.img_icon)}'">
      <span class="card-badge">${elIcon(c.element)}${esc(c.element)}</span>
      <span class="card-rarity ${c.rarity===4?'r4':''}">${stars(c.rarity)}</span>
    </div>
    <div class="card-info">
      <h3>${esc(c.name)}</h3>
      <p><b>${esc(c.element)}</b><span class="sep">·</span>${weapIcon(c.weapon)}${esc(c.weapon)}</p>
    </div>
  </article>`;
}

function apply() {
  const term = q.value.trim().toLowerCase();
  const el = fEl.value, w = fWeap.value, r = fR.value;
  const list = state.characters.filter((c) => {
    if (el && c.element !== el) return false;
    if (w && c.weapon !== w) return false;
    if (r && String(c.rarity) !== r) return false;
    if (term) {
      const blob = [
        c.name, c.slug, c.element, elVi(c.element), c.weapon, weapVi(c.weapon),
        c.intro, c.intro_vi,
        (c.changes || []).map((ch) => ch.note).join(' '),
        (c.skills || []).map((s) => [s.name, (s.desc_vi || []).join(' '), (s.desc || []).join(' ')].join(' ')).join(' '),
        (c.resonance_chain || []).map((n) => [n.name, (n.desc_vi || []).join(' '), (n.desc || []).join(' ')].join(' ')).join(' '),
      ].join(' ').toLowerCase();
      if (!blob.includes(term)) return false;
    }
    return true;
  }).sort((a, b) => (b.rarity - a.rarity) || a.name.localeCompare(b.name));
  grid.innerHTML = list.map(cardHTML).join('');
  shown.textContent = list.length;
  empty.style.display = list.length ? 'none' : 'block';
}

function renderHero() {
  const featured = state.bySlug.get('jinhsi') || state.characters[0];
  if (!featured) return;
  const img = $('hero-img');
  img.src = featured.img_full || featured.img_card || featured.img_icon;
  img.alt = featured.name;
  img.hidden = false;
  img.onerror = () => { img.onerror = null; img.src = featured.img_icon; };
  $('hero-name').textContent = featured.name;
  $('hero-tags').innerHTML = `${elIcon(featured.element)}${esc(featured.element)}<span class="sep">·</span>${weapIcon(featured.weapon)}${esc(featured.weapon)}`;
}

function renderMeta() {
  const m = state.meta;
  $('patch-label').innerHTML = `Patch ${esc(m.patch)}<span class="hide-sm"> · ${esc(m.characters)} Resonators</span>`;
  $('stat-count').textContent = m.characters;
  $('stat-elements').textContent = new Set(state.characters.map((c) => c.element).filter(Boolean)).size;
  $('stat-weapons').textContent = new Set(state.characters.map((c) => c.weapon).filter(Boolean)).size;
  $('total').textContent = m.characters;
  $('list-foot').innerHTML = t('list_foot_html', {p: esc(m.patch)});
  if (!state.current) document.title = t('title_list', {p: m.patch});
}

function lineHTML(line) {
  if (line.startsWith('• ')) return {li: true, text: line.slice(2)};
  const short = line.length < 72 && !/[.!?]$/.test(line);
  return {li: false, text: line, sub: short};
}

function linesHTML(lines) {
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

function renderSkills() {
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
const LEVELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const valueAt = (row, lv) => (row.values.length === 1 ? row.values[0] : row.values[lv - 1] ?? '—');
const leveled = (s) => (s.scaling?.rows || []).filter((r) => r.values.length > 1);
const constants = (s) => (s.scaling?.rows || []).filter((r) => r.values.length === 1);

// Total multiplier of a wiki value such as "19.61%+9.81%*3" (= 49.04). NaN if not numeric.
function totalOf(v) {
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

const TYPE_MONO = {'Basic Attack': 'BA', 'Resonance Skill': 'RS', 'Forte Circuit': 'FC', 'Resonance Liberation': 'RL',
  'Intro Skill': 'IN', 'Outro Skill': 'OU', 'Inherent Skill': 'IS'};
const skillIcon = (s, cls) => `<span class="${cls}" aria-hidden="true">${s.icon
  ? `<img src="${esc(s.icon)}" alt="" loading="lazy" referrerpolicy="no-referrer">`
  : `<b>${esc(TYPE_MONO[s.type] || '?')}</b>`}</span>`;

/* Multipliers panel: "Lv. N" slider + striped rows (label left, value right). */
function scaleHTML(s, i, open = false) {
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
function applyLevel() {
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
const TREE_COLS = [
  {type: 'Basic Attack', label: 'Normal Attack', pos: 'outer'},
  {type: 'Resonance Skill', label: 'Resonance Skill', pos: 'inner'},
  {type: 'Forte Circuit', label: 'Forte Circuit', pos: 'center'},
  {type: 'Resonance Liberation', label: 'Resonance Liberation', pos: 'inner'},
  {type: 'Intro Skill', label: 'Intro Skill', pos: 'outer'},
];
const TUNE_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" width="22" height="22"><path d="M3 12h3l2-5 3 10 3-12 2 7h5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const selKey = (sel) => 'skill-' + sel.i;

function treeParts(c) {
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

function renderTree() {
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

function renderTreeDetail() {
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
function renderChain() {
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
const MAT_GROUPS = [['ascension', 'mat_ascension'], ['forte', 'mat_forte'], ['inherent', 'mat_inherent'], ['stat_bonus', 'mat_stat']];
const qtyFmt = (n) => n.toLocaleString('vi-VN');

function matCards(items) {
  return `<ul class="mat-list">${items.map((it) => `<li class="mat r${it.rarity}" title="${esc(it.name)}">
    <span class="mat-img">${it.img ? `<img src="${esc(it.img)}" alt="" loading="lazy" referrerpolicy="no-referrer" width="48" height="48">` : ''}</span>
    <span class="mat-qty">${qtyFmt(it.qty)}</span>
    <span class="mat-name">${esc(it.name)}</span>
  </li>`).join('')}</ul>`;
}

function sumSteps(rows, upto) {
  const acc = new Map();
  rows.slice(0, upto).forEach((r) => r.items.forEach((it) => {
    const cur = acc.get(it.name);
    acc.set(it.name, cur ? {...cur, qty: cur.qty + it.qty} : {...it});
  }));
  // Shell Credit first, then by rarity and name (same order as the wiki totals).
  return [...acc.values()].sort((a, b) => (b.name === 'Shell Credit') - (a.name === 'Shell Credit')
    || a.rarity - b.rarity || a.name.localeCompare(b.name));
}

function renderMaterials(c) {
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

function updateUpgrade(input) {
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

function renderReferences(c) {
  const refs = c.references || [{title: 'prydwen.gg', url: c.source, used_for: ''}];
  $('d-refs').innerHTML = refs.map((r) => {
    let host = '';
    try { host = new URL(r.url).hostname.replace(/^www\./, ''); } catch { /* keep empty */ }
    return `<li><a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.title)}</a>
      <span class="ref-host">${esc(host)}</span>${(state.showEn ? r.used_for_en : r.used_for) ? `<span class="ref-use">${esc(state.showEn ? r.used_for_en : r.used_for)}</span>` : ''}</li>`;
  }).join('');
}

function renderIntro() {
  const c = state.current;
  const introEl = $('d-intro');
  const text = state.showEn ? c.intro : c.intro_vi;
  introEl.textContent = text || '';
  introEl.hidden = !text;
  introEl.lang = state.showEn ? 'en' : 'vi';
}

function linkifyAll() {
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
  for (const name of movesOf(c).keys()) {
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
const moveCache = new Map();
function movesOf(c) {
  if (!moveCache.has(c.slug)) moveCache.set(c.slug, new Map(Object.entries(state.index.chars[c.slug]?.moves || {})));
  return moveCache.get(c.slug);
}

function openMove(name) {
  const c = state.current;
  const ref = movesOf(c).get(name);
  if (!ref) return;
  const src = ref.kind === 'skill' ? c.skills[ref.index] : (c.resonance_chain || []).find((n) => n.node === ref.index);
  const lines = (state.showEn || !(src.desc_vi || []).length ? src.desc : src.desc_vi) || [];
  const def = (lines[ref.line] || '').replace(/^• /, '');
  openMechanic({term: name, kind: 'move', owners: [c.slug], summary_vi: def, summary_en: def,
    source: t('move_from', {skill: ref.title}), target: (ref.kind === 'skill' ? 'skill-' : 'chain-') + ref.index});
}

function makeTermNode(term, text) {
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

function scrollToSkill(index) {
  scrollToId('skill-' + index);
}

// Scroll to a skill/chain section (switching to its tab). With a term, highlight
// only the paragraphs that mention it, and the term itself, instead of the whole section.
function scrollToId(id, term = '', line = null) {
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
    setTimeout(() => detailView.querySelectorAll('.hit, .hit-term').forEach((x) => x.classList.remove('hit', 'hit-term')), 6000);
  } else {
    el.scrollIntoView({behavior: 'smooth', block: 'start'});
    el.classList.remove('flash');
    void el.offsetWidth;
    el.classList.add('flash');
    setTimeout(() => el.classList.remove('flash'), 1900);
  }
  el.focus({preventScroll: true});
}

function renderChanges(c) {
  const box = $('d-changes');
  const list = [...(c.changes || [])].reverse();
  $('d-changes-list').innerHTML = list.map((ch) =>
    `<li><b>Patch ${esc(ch.version)}</b> · ${esc(ch.date)} — ${esc(ch.note)}</li>`
  ).join('');
  box.style.display = list.length ? '' : 'none';
  box.open = list.length > 1;
}

function openDetail(slug) {
  const c = state.bySlug.get(slug);
  if (!c) { location.hash = '#/'; return; }
  state.current = c;
  renderDetail(c);
  state.treeSel = null;
  renderSkills();
  setTab(state.tab);
  if (!state.detailOpen) state.savedScroll = window.scrollY;
  state.detailOpen = true;
  listView.style.display = 'none';
  detailView.classList.add('open');
  window.scrollTo({top: 0, behavior: 'instant'});
  backBtn.focus({preventScroll: true, focusVisible: false});
  if (state.pendingTarget) {
    const {id, term, line} = state.pendingTarget;
    state.pendingTarget = null;
    requestAnimationFrame(() => scrollToId(id, term, line ?? null));
  }
}

// Everything on the profile that depends on the language, except the skill/tree/chain bodies.
function renderDetail(c) {
  const col = elColor(c.element);
  $('d-frame').style.setProperty('--tint-soft', col + '22');
  const img = $('d-img');
  img.src = c.img_full || c.img_card || c.img_icon;
  img.alt = c.name;
  img.onerror = () => { img.onerror = null; img.src = c.img_icon; };
  $('d-name').textContent = c.name;
  const vi = !state.showEn;
  $('d-element').innerHTML = `${elIcon(c.element)}${esc(c.element)}${vi ? ' · ' + esc(elVi(c.element)) : ''}`;
  $('d-weapon').innerHTML = `${weapIcon(c.weapon)}${esc(c.weapon)}${vi ? ' · ' + esc(weapVi(c.weapon)) : ''}`;
  $('d-version').textContent = `Patch ${state.meta.patch}`;
  $('d-crumb').innerHTML = `${elIcon(c.element)}<span>${esc(c.name)}</span>`;
  $('d-tags').innerHTML =
    `<span class="tag el" style="--c:${col}">${elIcon(c.element)}${esc(c.element)}</span>
     <span class="tag">${weapIcon(c.weapon)}${esc(c.weapon)}</span>
     <span class="tag" style="color:${c.rarity===5?'var(--r5)':'var(--r4)'}">${stars(c.rarity)}</span>`;
  $('d-stats').innerHTML = `
    <div class="stat"><div class="k">${esc(t('k_element'))}</div><div class="v v-ico" style="color:${col}">${elIcon(c.element, 'ico-lg')}<span>${esc(c.element)}${vi ? `<small>${esc(elVi(c.element))}</small>` : ''}</span></div></div>
    <div class="stat"><div class="k">${esc(t('k_weapon'))}</div><div class="v v-ico">${weapIcon(c.weapon, 'ico-lg')}<span>${esc(c.weapon)}${vi ? `<small>${esc(weapVi(c.weapon))}</small>` : ''}</span></div></div>
    <div class="stat"><div class="k">${esc(t('k_rarity'))}</div><div class="v" style="color:${c.rarity===5?'var(--r5)':'var(--r4)'}">${c.rarity ? c.rarity + '★' : '—'}</div></div>
    <div class="stat"><div class="k">${esc(t('k_skills'))}</div><div class="v">${(c.skills || []).length}<small>${esc(t('skills_unit'))}</small></div></div>`;
  renderTraits(c);
  renderMaterials(c);
  renderReferences(c);
  renderChanges(c);
  document.title = t('title_detail', {name: c.name, p: state.meta.patch});
}

function closeDetail() {
  state.current = null;
  state.detailOpen = false;
  if (state.meta) document.title = t('title_list', {p: state.meta.patch});
  listView.style.display = '';
  detailView.classList.remove('open');
  window.scrollTo({top: state.savedScroll || 0, behavior: 'instant'});
}

function route() {
  const m = location.hash.match(/^#\/nhan-vat\/(.+)$/);
  if (m) openDetail(decodeURIComponent(m[1]));
  else closeDetail();
}

// Same term can be a global mechanic or a kit term of several Resonators: prefer the one for this page.
function findMechanic(term) {
  const slug = state.current?.slug;
  const list = state.mechanics.filter((x) => x.term === term);
  return list.find((x) => x.owners?.includes(slug)) || list.find((x) => !x.owners?.length) || list[0];
}

// "Definition.\n• point\n• point" -> paragraph + bullet list
function summaryHTML(text) {
  const lines = String(text).split('\n').filter((l) => l.trim());
  const head = lines.filter((l) => !l.startsWith('• '));
  const items = lines.filter((l) => l.startsWith('• '));
  return head.map((l) => `<span class="ms-p">${esc(l)}</span>`).join('')
    + (items.length ? `<ul class="ms-list">${items.map((l) => `<li>${esc(l.slice(2))}</li>`).join('')}</ul>` : '');
}

function autoQuote(m, cur) {
  // A kit term mentioned in another Resonator's kit (Phrolova: Cantarella's "Hazy Dream")
  // is explained with the owner's own definition, naming that owner.
  let c = cur;
  let ref = c && m.defs?.[c.slug];
  if (!ref && m.defs) {
    const owner = Object.keys(m.defs)[0];
    c = state.bySlug.get(owner);
    ref = m.defs[owner];
  }
  if (!c || !ref) return {text: '', title: ''};
  const src = ref.kind === 'skill' ? c.skills[ref.index] : (c.resonance_chain || []).find((n) => n.node === ref.index);
  if (!src) return {text: '', title: ''};
  const lines = (state.showEn || !(src.desc_vi || []).length ? src.desc : src.desc_vi) || [];
  const text = lines.slice(ref.line, ref.line + (ref.n || 1)).map((l) => l.replace(/^• /, '')).join(' ');
  const title = ref.kind === 'skill' ? src.name : `S${src.node} · ${src.name}`;
  return {text, title: c === cur ? title : `${title} (${c.name})`};
}

function openMechanic(termOrObj) {
  const m = typeof termOrObj === 'string' ? findMechanic(termOrObj) : termOrObj;
  if (!m) return;
  $('mech-kind').textContent = t('kind_' + m.kind) || t('mech_kind');
  $('mech-title').textContent = m.term;
  let summary = (state.showEn ? m.summary_en : m.summary_vi) || m.summary_vi;
  let source = m.source === 'wiki' ? t('src_wiki') : (m.source || '');
  if (m.auto) {  // kit term: quote the defining lines of the data, never a written summary
    const q = autoQuote(m, state.current);
    summary = q.text;
    source = q.title ? t('move_from', {skill: q.title}) : '';
  }
  $('mech-summary').innerHTML = summaryHTML(summary || '');
  $('mech-source').hidden = !source;
  $('mech-source').textContent = source;
  document.querySelector('.mech-lead').hidden = !summary && !source;
  const c = state.current;
  const occurrences = [];
  const seen = new Set();
  const sources = [
    ...(c?.skills || []).map((s, i) => ({title: s.name, target: 'skill-' + i, go: t('go_skill'), lines: (state.showEn ? s.desc : s.desc_vi) || []})),
    ...(c?.resonance_chain || []).map((n) => ({title: `S${n.node} · ${n.name}`, target: 'chain-' + n.node, go: t('go_chain'),
      lines: (state.showEn || !(n.desc_vi || []).length ? n.desc : n.desc_vi) || []})),
  ];
  const cap = {skill: 8, chain: 6};
  const used = {skill: 0, chain: 0};
  if (m.occ) occurrences.push(...m.occ);
  else for (const src of sources) {
    const kind = src.target.startsWith('chain-') ? 'chain' : 'skill';
    for (const line of src.lines) {
      if (used[kind] >= cap[kind]) break;
      if (!line.includes(m.term)) continue;
      const key = src.target + '|' + line;
      if (seen.has(key)) continue;
      seen.add(key);
      used[kind] += 1;
      occurrences.push({...src, line});
    }
  }
  const occBox = $('mech-occ-list');
  if (occurrences.length) {
    occBox.innerHTML = occurrences.map((o) =>
      `<div class="mech-occ-item">
        <div class="mech-occ-head"><b>${esc(o.title)}</b><button type="button" class="mech-go" data-target="${esc(o.target)}" data-term="${m.trait ? '' : esc(m.term)}" data-line="${o.lineIndex ?? ''}">${esc(o.go)} <span aria-hidden="true">↓</span></button></div>
        <p class="mech-occ-text">${esc(o.line)}</p>
        <button type="button" class="mech-more" hidden aria-expanded="false">${esc(t('more'))}</button>
      </div>`
    ).join('');
  } else {
    occBox.innerHTML = `<p class="mech-occ-item" style="cursor:default">${esc((state.showEn ? m.sample_en : m.sample_vi) || t('no_occ'))}</p>`;
  }
  state.mechTerm = m;
  state.roleFilter = 'all';
  renderMechUsers();
  mechDialog.showModal();
  mechDialog.scrollTop = 0;
  // Offer "Xem thêm" only where the clamped text is actually cut off.
  occBox.querySelectorAll('.mech-occ-item').forEach((item) => {
    const text = item.querySelector('.mech-occ-text');
    const more = item.querySelector('.mech-more');
    if (text && more) more.hidden = text.scrollHeight <= text.clientHeight + 1;
  });
}

// Role labels (keyword heuristics, see scripts/kit_rules.py ROLE_RULES), in display order.
const roleKeys = () => (state.index.rules?.roles || []).map((r) => r.key);
const roleKeywords = (k) => (state.index.rules?.roles || []).find((r) => r.key === k)?.kw || '';
const roleLabel = (k) => t('role_' + k);

function mechUsers(m) {
  if (m.trait) {
    return state.characters.map((c) => ({c, ev: traitsOf(c)[m.trait] || []}))
      .filter((u) => u.ev.length)
      .map(({c, ev}) => ({c, roles: [], target: ev[0].target, line: ev[0].lineIndex, count: ev.length}))
      .sort((a, b) => b.count - a.count || a.c.name.localeCompare(b.c.name));
  }
  return (state.index.mech_users[m.term] || [])
    .map((u) => ({...u, c: state.bySlug.get(u.slug)}))
    .filter((u) => u.c);
}

// Kit traits with their evidence lines, derived at build time (scripts/kit_rules.py -> /api/index).
const STATUS_KEYS = new Set(['spectro_frazzle', 'aero_erosion', 'havoc_bane', 'fusion_burst', 'glacio_chafe', 'electro_flare']);
const traitKeys = () => (state.index.rules?.traits || []).map((r) => r.key);
const traitKeywords = (k) => (state.index.rules?.traits || []).find((r) => r.key === k)?.kw || '';
const traitsOf = (c) => state.index.chars[c.slug]?.traits || {};
const traitLabel = (k) => ('trait_' + k) in I18N.vi ? t('trait_' + k) : k.split('_').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ');

const traitDesc = (k, full = false) => {
  if (('traitd_' + k) in I18N.vi) return t('traitd_' + k);
  const m = state.mechanics.find((x) => x.term === traitLabel(k) && !x.owners?.length);
  const sum = m && ((state.showEn ? m.summary_en : m.summary_vi) || m.summary_vi);
  if (!sum) return t('trait_status_desc', {name: traitLabel(k)});
  return full ? sum : sum.split('\n')[0];
};

function renderTraits(c) {
  const tr = traitsOf(c);
  const keys = traitKeys().filter((k) => tr[k]);
  $('d-traits').hidden = !keys.length;
  $('d-traits-list').innerHTML = keys.map((k) =>
    `<button type="button" class="trait trait-${k}" data-trait="${k}" data-tip="${esc(traitDesc(k))}">${esc(traitLabel(k))}<small>${tr[k].length}</small></button>`).join('');
}

function openTrait(key) {
  const c = state.current;
  const ev = traitsOf(c)[key] || [];
  const lineOf = (o) => {
    const [kind, idx] = o.target.split('-');
    const src = kind === 'skill' ? c.skills[Number(idx)] : (c.resonance_chain || []).find((n) => n.node === Number(idx));
    const lines = (state.showEn || !(src?.desc_vi || []).length ? src?.desc : src?.desc_vi) || [];
    return lines[o.lineIndex] || '';
  };
  const occ = ev.slice(0, 14).map((o) => ({...o, line: lineOf(o), go: o.target.startsWith('chain-') ? t('go_chain') : t('go_skill')}));
  const desc = traitDesc(key, true);
  openMechanic({term: traitLabel(key), kind: 'trait', trait: key, owners: [], occ,
    summary_vi: desc, summary_en: desc,
    source: (STATUS_KEYS.has(key) ? t('src_wiki') + ' · ' : '') + t('trait_note', {kw: traitKeywords(key) || traitLabel(key), n: ev.length})});
}

function renderMechUsers() {
  const m = state.mechTerm;
  const users = mechUsers(m);
  const box = $('mech-users');
  box.hidden = !users.length || m.kind === 'move';  // moves belong to one Resonator
  const hasRoles = users.some((u) => u.roles.length);
  $('role-help').hidden = !hasRoles;
  if (hasRoles) {
    $('role-help-list').innerHTML = roleKeys().map((k) =>
      `<div><dt><i class="role role-${k}">${esc(roleLabel(k))}</i></dt><dd>${esc(t('roled_' + k))} <small>${esc(t('role_kw', {kw: roleKeywords(k)}))}</small></dd></div>`).join('');
  }
  $('mech-users-count').textContent = `(${users.length})`;
  const present = roleKeys().filter((k) => users.some((u) => u.roles.includes(k)));
  $('mech-roles').innerHTML = users.length > 1 && present.length > 1
    ? [['all', t('role_all')], ...present.map((k) => [k, roleLabel(k)])].map(([k, label]) =>
      `<button type="button" class="role-chip" data-role="${k}"${k === 'all' ? '' : ` data-tip="${esc(t('roled_' + k))}"`} aria-pressed="${state.roleFilter === k}">${esc(label)}${k === 'all' ? '' : ` <small>${users.filter((u) => u.roles.includes(k)).length}</small>`}</button>`).join('')
    : '';
  const shown = state.roleFilter === 'all' ? users : users.filter((u) => u.roles.includes(state.roleFilter));
  const me = users.find((u) => u.c.slug === state.current?.slug);
  const others = shown.filter((u) => u !== me);
  const row = ({c, roles, target, count, line}, mine) => `<li${mine ? ' class="mu-me"' : ''}>
    <button type="button" class="mech-user${mine ? ' is-current' : ''}" data-slug="${esc(c.slug)}" data-target="${esc(target)}" data-line="${line ?? ''}">
      <img src="${esc(c.img_icon)}" alt="" width="${mine ? 52 : 40}" height="${mine ? 52 : 40}">
      <span class="mu-main">${mine ? `<span class="mu-badge">${esc(t('me_badge'))}</span>` : ''}<b>${esc(c.name)}</b>${elIcon(c.element)}<small>${esc(t('n_places', {n: count}))}</small></span>
      <span class="mu-roles">${roles.map((r) => `<i class="role role-${r}" data-tip="${esc(t('roled_' + r))}">${esc(roleLabel(r))}</i>`).join('')}</span>
      <span class="mu-go">${esc(mine ? t('go_here') : t('open_profile'))} <span aria-hidden="true">→</span></span>
    </button></li>`;
  $('mech-users-list').innerHTML = (me ? row(me, true) : '')
    + (others.length && me ? `<li class="mu-sep">${esc(t('others', {n: others.length}))}</li>` : '')
    + others.map((u) => row(u, false)).join('');
}

async function boot() {
  try {
    const [charsRes, mechRes, indexRes] = await Promise.all([
      fetch('/api/characters'),
      fetch('/api/mechanics'),
      fetch('/api/index'),
    ]);
    if (!charsRes.ok) throw new Error(`API /api/characters → HTTP ${charsRes.status}`);
    const chars = await charsRes.json();
    state.meta = chars.meta;
    state.characters = chars.characters;
    state.bySlug = new Map(state.characters.map((c) => [c.slug, c]));
    if (mechRes.ok) {
      const mech = await mechRes.json();
      state.mechanics = mech.mechanics || [];
      state.noLink = mech.no_link || [];
    }
    if (indexRes.ok) {
      state.index = await indexRes.json();
    }
    loading.style.display = 'none';
    renderMeta();
    renderHero();
    buildFilters();
    apply();
    route();
  } catch (err) {
    loading.style.display = 'none';
    errorBox.style.display = 'block';
    errorBox.innerHTML = t('error_html', {msg: esc(err.message)});
  }
}

grid.addEventListener('click', (e) => {
  const card = e.target.closest('.card');
  if (card) location.hash = '#/nhan-vat/' + encodeURIComponent(card.dataset.slug);
});
grid.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    const card = e.target.closest('.card');
    if (card) { e.preventDefault(); location.hash = '#/nhan-vat/' + encodeURIComponent(card.dataset.slug); }
  }
});
backBtn.addEventListener('click', () => { location.hash = '#/'; });
document.addEventListener('click', (e) => {
  const b = e.target.closest('.lang-switch [data-lang]');
  if (b && b.dataset.lang !== state.lang) setLang(b.dataset.lang);
});
[q, fEl, fWeap, fR].forEach((el) => el.addEventListener('input', apply));
window.addEventListener('hashchange', route);
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && state.current && !mechDialog.open) location.hash = '#/';
});

const onTermClick = (e) => {
  const skill = e.target.closest('[data-skill]');
  if (skill) { e.preventDefault(); scrollToSkill(Number(skill.dataset.skill)); return; }
  const mech = e.target.closest('[data-mech]');
  if (mech) { e.preventDefault(); openMechanic(mech.dataset.mech); return; }
  const move = e.target.closest('[data-move]');
  if (move) { e.preventDefault(); openMove(move.dataset.move); }
};
dSkills.addEventListener('click', onTermClick);
dChain.addEventListener('click', onTermClick);

$('mech-close').addEventListener('click', () => mechDialog.close());
$('mech-roles').addEventListener('click', (e) => {
  const chip = e.target.closest('.role-chip');
  if (!chip) return;
  state.roleFilter = chip.dataset.role;
  renderMechUsers();
});
$('mech-users-list').addEventListener('click', (e) => {
  const btn = e.target.closest('.mech-user');
  if (!btn) return;
  mechDialog.close();
  const term = state.mechTerm?.trait ? '' : (state.mechTerm?.term || '');
  const line = btn.dataset.line;
  if (btn.dataset.slug === state.current?.slug) { scrollToId(btn.dataset.target, term, line); return; }
  state.pendingTarget = {id: btn.dataset.target, term, line};
  location.hash = '#/nhan-vat/' + encodeURIComponent(btn.dataset.slug);
});
$('d-traits-list').addEventListener('click', (e) => {
  const b = e.target.closest('.trait');
  if (b) openTrait(b.dataset.trait);
});
/* tabs, sliders, tree selection, goto buttons */
const TAB_ORDER = ['tree', 'skills', 'chain', 'mats'];
function setTab(name, focus = false) {
  if (!TAB_ORDER.includes(name) || $('tab-btn-' + name).hidden) name = 'skills';
  state.tab = name;
  for (const t of TAB_ORDER) {
    const on = t === name;
    const btn = $('tab-btn-' + t);
    btn.setAttribute('aria-selected', String(on));
    btn.tabIndex = on ? 0 : -1;
    $('tab-' + t).hidden = !on;
  }
  if (focus) $('tab-btn-' + name).focus();
}
$('d-tabs').addEventListener('click', (e) => {
  const b = e.target.closest('[data-tab]');
  if (!b) return;
  setTab(b.dataset.tab);
  const top = $('d-tabs').getBoundingClientRect().top + window.scrollY - 84;
  if (window.scrollY > top) window.scrollTo({top, behavior: 'instant'});
});
$('d-tabs').addEventListener('keydown', (e) => {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
  e.preventDefault();
  const visible = TAB_ORDER.filter((t) => !$('tab-btn-' + t).hidden);
  let i = visible.indexOf(state.tab);
  if (e.key === 'ArrowLeft') i = (i - 1 + visible.length) % visible.length;
  if (e.key === 'ArrowRight') i = (i + 1) % visible.length;
  if (e.key === 'Home') i = 0;
  if (e.key === 'End') i = visible.length - 1;
  setTab(visible[i], true);
});
detailView.addEventListener('input', (e) => {
  if (e.target.classList.contains('lv-range')) { state.level = Number(e.target.value); applyLevel(); }
  if (e.target.classList.contains('up-range')) updateUpgrade(e.target);
});
detailView.addEventListener('click', (e) => {
  const n = e.target.closest('.fn[data-sel]');
  if (n) {
    const key = n.dataset.sel;
    state.treeSel = {kind: 'skill', i: Number(key.slice(6))};
    $('d-tree').querySelectorAll('.fn').forEach((x) => x.classList.toggle('is-sel', x === n));
    renderTreeDetail();
    applyLevel();
    return;
  }
  const tg = e.target.closest('[data-tabgo]');
  if (tg) { setTab(tg.dataset.tabgo); return; }
  const go = e.target.closest('[data-goto]');
  if (go) scrollToId(go.dataset.goto);
});
// The dialog closes only via ✕, Esc, or a click that both starts and ends on the
// backdrop. Clicks inside the panel (padding, text, items, text selection) never close it.
const outsideDialog = (e) => {
  const r = mechDialog.getBoundingClientRect();
  return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
};
let pressedOnBackdrop = false;
mechDialog.addEventListener('pointerdown', (e) => {
  pressedOnBackdrop = e.target === mechDialog && outsideDialog(e);
});
mechDialog.addEventListener('click', (e) => {
  if (e.target === mechDialog && pressedOnBackdrop && outsideDialog(e)) {
    mechDialog.close();
    return;
  }
  const more = e.target.closest('.mech-more');
  if (more) {
    const item = more.closest('.mech-occ-item');
    const open = item.classList.toggle('expanded');
    more.textContent = open ? t('less') : t('more');
    more.setAttribute('aria-expanded', String(open));
    return;
  }
  const go = e.target.closest('.mech-go[data-target]');
  if (go) {
    mechDialog.close();
    scrollToId(go.dataset.target, go.dataset.term, go.dataset.line);
  }
});
mechDialog.addEventListener('close', () => { pressedOnBackdrop = false; });

/* Custom tooltip: replaces the slow native one for every [title]/[data-tip] on the page. */
const tip = document.createElement('div');
tip.className = 'tip';
tip.setAttribute('role', 'tooltip');
tip.hidden = true;
document.body.appendChild(tip);
let tipFor = null;      // element whose tooltip is shown
let tipPending = null;  // element waiting for its tooltip
let tipTimer = 0;
function tipTarget(node) {
  const el = node?.closest?.('[data-tip], [title]');
  if (!el || el === document.documentElement) return null;
  if (el.hasAttribute('title')) {  // take the text over so the native tooltip never shows
    const text = el.getAttribute('title');
    el.removeAttribute('title');
    if (text) el.dataset.tip = text;
  }
  return el.dataset.tip ? el : null;
}
function showTip(el) {
  tipFor = el;
  // inside a modal <dialog> the tooltip must live in the dialog's top layer
  const host = el.closest('dialog[open]') || document.body;
  if (tip.parentNode !== host) host.appendChild(tip);
  tip.textContent = el.dataset.tip;
  tip.hidden = false;
  tip.classList.remove('show');
  const r = el.getBoundingClientRect();
  const w = tip.offsetWidth, h = tip.offsetHeight, pad = 8;
  let top = r.top - h - 8;
  let below = false;
  if (top < pad) { top = r.bottom + 8; below = true; }
  const left = Math.min(Math.max(pad, r.left + r.width / 2 - w / 2), innerWidth - w - pad);
  tip.style.left = left + 'px';
  tip.style.top = top + 'px';
  tip.style.setProperty('--ax', (r.left + r.width / 2 - left) + 'px');
  tip.classList.toggle('below', below);
  requestAnimationFrame(() => tip.classList.add('show'));
}
function hideTip() {
  clearTimeout(tipTimer);
  tipFor = null;
  tipPending = null;
  tip.classList.remove('show');
  tip.hidden = true;
}
document.addEventListener('pointerover', (e) => {
  if (e.pointerType === 'touch') return;
  const el = tipTarget(e.target);
  if (el && (el === tipFor || el === tipPending)) return;  // moving between children of the same target
  hideTip();
  if (el) {
    tipPending = el;
    tipTimer = setTimeout(() => { tipPending = null; showTip(el); }, 60);
  }
});
document.addEventListener('pointerout', (e) => {
  const cur = tipFor || tipPending;
  if (cur && !cur.contains(e.relatedTarget)) hideTip();
});
document.addEventListener('focusin', (e) => { const el = tipTarget(e.target); if (el && e.target.matches(':focus-visible')) showTip(el); });
document.addEventListener('focusout', hideTip);
document.addEventListener('pointerdown', hideTip);
addEventListener('scroll', hideTip, {capture: true, passive: true});
addEventListener('keydown', (e) => { if (e.key === 'Escape') hideTip(); });

applyStaticI18n();
boot();

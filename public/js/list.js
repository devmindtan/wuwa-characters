// Language switch, filters, custom dropdowns and the Resonator list.
import {$, EL_VI, elColor, elDot, elIcon, elVi, empty, esc, fEl, fR, fWeap, grid, mechDialog, q, rarityMark, shown, stars, state, WEAP_VI, weapDot, weapIcon, weapVi} from './core.js';
import {renderDetail, setTab} from './detail.js';
import {t} from './i18n.js';
import {renderSkills} from './kit.js';

/* ---------- language ---------- */
export function applyStaticI18n() {
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
export function buildFilters() {
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

export function setLang(lang) {
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

export function fillSelect(sel, values, labelFn) {
  values.forEach((v) => {
    const o = document.createElement('option');
    o.value = v;
    o.textContent = labelFn(v);
    sel.appendChild(o);
  });
}

/* ---------- custom dropdown (enhances a native <select>) ---------- */
export let ddSeq = 0;
export const openDropdowns = new Set();

export function enhanceSelect(sel, decorate = () => '') {
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

export function cardHTML(c) {
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

export function apply() {
  const term = q.value.trim().toLowerCase();
  const el = fEl.value, w = fWeap.value, r = fR.value;
  const list = state.characters.filter((c) => {
    if (el && c.element !== el) return false;
    if (w && c.weapon !== w) return false;
    if (r && String(c.rarity) !== r) return false;
    if (term) {
      // names always; skill/chain text once /api/search has arrived
      const blob = [c.name, c.slug, c.element, elVi(c.element), c.weapon, weapVi(c.weapon)].join(' ').toLowerCase()
        + ' ' + (state.search?.[c.slug] || '');
      if (!blob.includes(term)) return false;
    }
    return true;
  }).sort((a, b) => (b.rarity - a.rarity) || a.name.localeCompare(b.name));
  grid.innerHTML = list.map(cardHTML).join('');
  shown.textContent = list.length;
  empty.style.display = list.length ? 'none' : 'block';
}

export function renderHero() {
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

export function renderMeta() {
  const m = state.meta;
  $('patch-label').innerHTML = `Patch ${esc(m.patch)}<span class="hide-sm"> · ${esc(m.characters)} Resonators</span>`;
  $('stat-count').textContent = m.characters;
  $('stat-elements').textContent = new Set(state.characters.map((c) => c.element).filter(Boolean)).size;
  $('stat-weapons').textContent = new Set(state.characters.map((c) => c.weapon).filter(Boolean)).size;
  $('total').textContent = m.characters;
  $('list-foot').innerHTML = t('list_foot_html', {p: esc(m.patch)});
  if (!state.current) document.title = t('title_list', {p: m.patch});
}

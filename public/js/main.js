// Entry point: loads the API data and wires page-level events.
import {$, backBtn, dChain, detailView, dSkills, errorBox, esc, fEl, fR, fWeap, grid, loading, mechDialog, q, state} from './core.js';
import {route, setTab, TAB_ORDER} from './detail.js';
import {t} from './i18n.js';
import {applyLevel, renderTreeDetail, updateUpgrade} from './kit.js';
import {openMove, scrollToId, scrollToSkill} from './links.js';
import {apply, applyStaticI18n, buildFilters, renderHero, renderMeta, setLang} from './list.js';
import {openMechanic} from './mechanics.js';
import {onWeaponClick, onWeaponInput} from './weapon.js';
import './tooltip.js';  // side effects only: installs the page-wide tooltip

async function boot() {
  try {
    const [charsRes, mechRes, indexRes] = await Promise.all([
      fetch('/api/summary'),  // list fields only; a profile loads /api/characters/{slug} when opened
      fetch('/api/mechanics'),
      fetch('/api/index'),
    ]);
    if (!charsRes.ok) throw new Error(`API /api/summary → HTTP ${charsRes.status}`);
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
    // Full-text search (skill and chain text, EN + VI) arrives in the background.
    fetch('/api/search').then((r) => (r.ok ? r.json() : null)).then((s) => {
      if (!s) return;
      state.search = s;
      if (q.value.trim()) apply();
    }).catch(() => {});
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
  onWeaponInput(e.target);
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
  if (onWeaponClick(e.target)) return;
  const tg = e.target.closest('[data-tabgo]');
  if (tg) { setTab(tg.dataset.tabgo); return; }
  const go = e.target.closest('[data-goto]');
  if (go) scrollToId(go.dataset.goto);
});

applyStaticI18n();
boot();

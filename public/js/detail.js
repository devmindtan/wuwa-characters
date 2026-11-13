// Routing and the Resonator detail page (render, open/close, tabs).
import {$, backBtn, detailView, elColor, elIcon, elVi, esc, listView, stars, state, weapIcon, weapVi} from './core.js';
import {t} from './i18n.js';
import {renderMaterials, renderReferences, renderSkills} from './kit.js';
import {scrollToId} from './links.js';
import {renderTraits} from './mechanics.js';

export function renderChanges(c) {
  const box = $('d-changes');
  const list = [...(c.changes || [])].reverse();
  $('d-changes-list').innerHTML = list.map((ch) =>
    `<li><b>Patch ${esc(ch.version)}</b> · ${esc(ch.date)} — ${esc(ch.note)}</li>`
  ).join('');
  box.style.display = list.length ? '' : 'none';
  box.open = list.length > 1;
}

// Full Resonator data is fetched when a profile opens (the list only has summaries) and kept.
const fullCache = new Map();
const routeSlug = () => {
  const m = location.hash.match(/^#\/nhan-vat\/(.+)$/);
  return m ? decodeURIComponent(m[1]) : null;
};

export async function openDetail(slug) {
  if (!state.bySlug.has(slug)) { location.hash = '#/'; return; }
  let c = fullCache.get(slug);
  if (!c) {
    try {
      const res = await fetch('/api/characters/' + encodeURIComponent(slug));
      if (!res.ok) throw new Error(`API /api/characters/${slug} → HTTP ${res.status}`);
      c = await res.json();
      fullCache.set(slug, c);
    } catch (err) {
      console.error(err);
      location.hash = '#/';
      return;
    }
    if (routeSlug() !== slug) return;  // the visitor moved on while it was loading
  }
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

function renderSignatureWeapon(c) {
  const box = $('d-sig-weapon');
  const sw = c.signature_weapon;
  if (!sw) { box.hidden = true; box.innerHTML = ''; return; }
  const meta = [sw.type, sw.stat_type].filter(Boolean).map(esc).join(' · ');
  const passive = sw.rank_name ? `<div class="sw-passive">${esc(sw.rank_name)}</div>` : '';
  const tip = sw.effect ? esc(sw.effect) : '';
  box.hidden = false;
  box.outerHTML; // keep element
  box.innerHTML = `<a href="${esc(sw.source || '#')}" target="_blank" rel="noopener noreferrer" class="sig-weapon-link" style="display:flex;align-items:center;gap:12px;color:inherit;text-decoration:none;width:100%"${tip ? ` data-tip="${tip.replace(/"/g, '&quot;')}"` : ''}>
    <span class="sw-icon">${sw.img ? `<img src="${esc(sw.img)}" alt="" loading="lazy">` : ''}</span>
    <span class="sw-body">
      <div class="sw-k">${esc(t('k_sig_weapon'))}</div>
      <div class="sw-name">${esc(sw.name)} <span class="r5">${'★'.repeat(sw.rarity || 5)}</span></div>
      <div class="sw-meta">${meta}</div>
      ${passive}
    </span>
  </a>`;
  box.className = 'sig-weapon';
}

// Everything on the profile that depends on the language, except the skill/tree/chain bodies.
export function renderDetail(c) {
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
  renderSignatureWeapon(c);
  renderTraits(c);
  renderMaterials(c);
  renderReferences(c);
  renderChanges(c);
  document.title = t('title_detail', {name: c.name, p: state.meta.patch});
}

export function closeDetail() {
  state.current = null;
  state.detailOpen = false;
  if (state.meta) document.title = t('title_list', {p: state.meta.patch});
  listView.style.display = '';
  detailView.classList.remove('open');
  window.scrollTo({top: state.savedScroll || 0, behavior: 'instant'});
}

export function route() {
  const m = location.hash.match(/^#\/nhan-vat\/(.+)$/);
  if (m) openDetail(decodeURIComponent(m[1]));
  else closeDetail();
}

/* tabs, sliders, tree selection, goto buttons */
export const TAB_ORDER = ['tree', 'skills', 'chain', 'mats'];
export function setTab(name, focus = false) {
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

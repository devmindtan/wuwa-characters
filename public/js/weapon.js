// Signature weapon: summary card under the stats and the "Vũ khí" tab (stats by level, R1-R5 effect, ascension).
import {$, esc, state, weapIcon, weapVi} from './core.js';
import {t} from './i18n.js';
import {matCards, sumSteps} from './kit.js';

const RANKS = [1, 2, 3, 4, 5];
const sw = () => state.current?.signature_weapon || null;

// "{N}" placeholders -> the value of the chosen rank, highlighted.
function effectHTML(line, ranks, rank) {
  return esc(line).replace(/\{(\d)\}(%?)/g, (_, n, pct) => {
    const vals = ranks[n] || [];
    const tip = vals.map((v, i) => `R${i + 1}: ${v}${pct}`).join(' · ');
    return `<b class="wv" data-n="${n}" data-pct="${pct}" data-tip="${esc(tip)}">${esc((vals[rank - 1] ?? '?') + pct)}</b>`;
  });
}

const lines = (en, vi) => (state.showEn || !vi?.length ? en : vi) || [];
const maxRow = (w) => w.stats[w.stats.length - 1];
const lvLabel = (row) => t('wp_level_html', {lv: esc(row.level), a: esc(row.ascension)});
const fill = (input, i, max) => input.style.setProperty('--p', `${(i / Math.max(max, 1)) * 100}%`);

export function renderWeaponCard(c) {
  const box = $('d-sig-weapon');
  const w = c.signature_weapon;
  box.hidden = !w;
  $('tab-btn-weapon').hidden = !w;
  if (!w) { box.innerHTML = ''; return; }
  const top = w.stats?.length ? maxRow(w) : null;
  box.innerHTML = `<button type="button" class="sw-card" data-tabgo="weapon">
    <span class="sw-icon">${w.img ? `<img src="${esc(w.img)}" alt="" loading="lazy" width="56" height="56">` : ''}</span>
    <span class="sw-body">
      <span class="sw-k">${esc(t('k_sig_weapon'))}</span>
      <span class="sw-name">${esc(w.name)} <span class="sw-stars" aria-label="${w.rarity}★">${'★'.repeat(w.rarity || 5)}</span></span>
      <span class="sw-meta">${weapIcon(w.type)}<span>${esc(w.type)}</span>${top
        ? `<span class="sw-dot" aria-hidden="true">·</span><span>ATK <b>${esc(top.atk)}</b></span><span class="sw-dot" aria-hidden="true">·</span><span>${esc(w.stat_type)} <b>${esc(top.sub)}</b></span>`
        : `<span class="sw-dot" aria-hidden="true">·</span><span>${esc(w.stat_type)}</span>`}</span>
    </span>
    <span class="sw-go">${esc(t('sw_open'))}<svg viewBox="0 0 16 16" aria-hidden="true" width="12" height="12"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
  </button>`;
}

export function renderWeapon() {
  const w = sw();
  const box = $('d-weapon-body');
  if (!w) { box.innerHTML = ''; return; }
  const rank = state.wRank;
  const desc = lines(w.description, w.description_vi);
  const effect = lines(w.passive, w.passive_vi);
  const stats = w.stats || [];
  const lv = Math.min(state.wLv ?? stats.length - 1, stats.length - 1);
  const steps = w.ascension || [];
  const asc = Math.min(state.wAsc ?? steps.length, steps.length);

  const hero = `<header class="wp-hero">
    <div class="wp-art">${w.img ? `<img src="${esc(w.img)}" alt="${esc(w.name)}" width="128" height="128">` : ''}</div>
    <div class="wp-id">
      <h3>${esc(w.name)}</h3>
      <p class="wp-tags"><span class="wp-stars">${'★'.repeat(w.rarity || 5)}</span>
        <span class="tag">${weapIcon(w.type)}${esc(w.type)}${state.showEn ? '' : ` · ${esc(weapVi(w.type))}`}</span>
        <span class="tag">${esc(t('wp_sub', {s: w.stat_type}))}</span></p>
    </div>
    ${desc.length ? `<blockquote class="wp-lore" lang="${state.showEn || !w.description_vi?.length ? 'en' : 'vi'}">${desc.map((l) => `<p>${esc(l)}</p>`).join('')}</blockquote>` : ''}
  </header>`;

  const statBlock = stats.length ? `<section class="wp-block">
    <header><h4>${esc(t('wp_stats'))}</h4><p>${esc(t('wp_stats_hint'))}</p></header>
    <div class="wp-stat-head wp-lv-label">${lvLabel(stats[lv])}</div>
    <input type="range" class="wp-lv" min="0" max="${stats.length - 1}" step="1" value="${lv}" style="--p:${(lv / (stats.length - 1)) * 100}%" aria-label="${esc(t('wp_lv_aria'))}">
    <div class="wp-stat-vals">
      <div class="stat"><div class="k">Base ATK</div><div class="v wp-atk">${esc(stats[lv].atk)}</div></div>
      <div class="stat"><div class="k">${esc(w.stat_type)}</div><div class="v wp-sub">${esc(stats[lv].sub)}</div></div>
    </div>
  </section>` : `<section class="wp-block"><header><h4>${esc(t('wp_stats'))}</h4></header><p class="wp-empty">${esc(t('wp_no_stats'))}</p></section>`;

  const effBlock = `<section class="wp-block wp-effect">
    <header><h4>${esc(w.rank_name || t('wp_effect'))}</h4><p>${esc(t('wp_effect_hint'))}</p></header>
    <div class="wp-ranks" role="group" aria-label="${esc(t('wp_rank_aria'))}">${RANKS.map((r) =>
      `<button type="button" data-wrank="${r}" aria-pressed="${r === rank}">R${r}</button>`).join('')}</div>
    <div class="wp-eff-text" lang="${state.showEn || !w.passive_vi?.length ? 'en' : 'vi'}">${effect.map((l) => l.startsWith('• ')
      ? `<p class="wp-li">${effectHTML(l.slice(2), w.ranks || {}, rank)}</p>`
      : `<p>${effectHTML(l, w.ranks || {}, rank)}</p>`).join('')}</div>
  </section>`;

  const ascBlock = steps.length ? `<section class="wp-block">
    <header><h4>${esc(t('wp_asc'))}</h4><p>${esc(t('wp_asc_hint'))}</p></header>
    <div class="wp-stat-head wp-asc-label">${t('wp_asc_to_html', {n: asc})}</div>
    <input type="range" class="wp-asc" min="1" max="${steps.length}" step="1" value="${asc}" style="--p:${((asc - 1) / Math.max(steps.length - 1, 1)) * 100}%" aria-label="${esc(t('wp_asc_aria'))}">
    <div class="wp-asc-mats">${matCards(sumSteps(steps, asc))}</div>
  </section>` : '';

  box.innerHTML = hero + `<div class="wp-grid">${effBlock}${statBlock}</div>` + ascBlock;
}

// Events (delegated from main.js). Sliders update in place so a drag is never interrupted.
export function onWeaponInput(el) {
  const w = sw();
  const box = $('d-weapon-body');
  if (!w) return false;
  if (el.classList.contains('wp-lv')) {
    const row = w.stats[state.wLv = Number(el.value)];
    box.querySelector('.wp-lv-label').innerHTML = lvLabel(row);
    box.querySelector('.wp-atk').textContent = row.atk;
    box.querySelector('.wp-sub').textContent = row.sub;
    fill(el, state.wLv, w.stats.length - 1);
    return true;
  }
  if (el.classList.contains('wp-asc')) {
    state.wAsc = Number(el.value);
    box.querySelector('.wp-asc-label').innerHTML = t('wp_asc_to_html', {n: state.wAsc});
    box.querySelector('.wp-asc-mats').innerHTML = matCards(sumSteps(w.ascension, state.wAsc));
    fill(el, state.wAsc - 1, w.ascension.length - 1);
    return true;
  }
  return false;
}

export function onWeaponClick(target) {
  const b = target.closest('[data-wrank]');
  const w = sw();
  if (!b || !w) return false;
  state.wRank = Number(b.dataset.wrank);
  const box = $('d-weapon-body');
  box.querySelectorAll('[data-wrank]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
  box.querySelectorAll('.wv').forEach((v) => { v.textContent = ((w.ranks[v.dataset.n] || [])[state.wRank - 1] ?? '?') + v.dataset.pct; });
  return true;
}

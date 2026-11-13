// "Combo" tab: rotation steps (prydwen.gg) with the kit lines each step activates (/api/combos/{slug}).
// The step -> line matching is built by scripts/build_combos.py; this module only renders it.
// Layout: the whole sequence as a strip of chips -> one selected step in detail -> totals grouped by source.
import {$, esc, state} from './core.js';
import {t} from './i18n.js';

const cache = new Map();  // slug -> combos payload (or null when the Resonator has none)
const KINDS = ['basic', 'heavy', 'skill', 'lib', 'intro', 'outro', 'echo', 'midair', 'dodge', 'move', 'other'];
const KIND_MONO = {basic: 'BA', heavy: 'HA', skill: 'RS', lib: 'RL', intro: 'IN', outro: 'OU', echo: 'EC', midair: 'MA',
  dodge: 'DC', move: '', other: ''};

async function load(slug) {
  if (cache.has(slug)) return cache.get(slug);
  let data = null;
  try {
    const res = await fetch('/api/combos/' + encodeURIComponent(slug));
    if (res.ok) data = await res.json();
  } catch (err) { console.error(err); }
  cache.set(slug, data);
  return data;
}

// A reference [target, line] -> what the step activates, in the current language.
function resolve(c, [target, li]) {
  const vi = !state.showEn;
  if (target === 'weapon') {
    const w = c.signature_weapon;
    if (!w) return null;
    const lines = vi && w.passive_vi?.length ? w.passive_vi : w.passive;
    const text = (lines[li] || '').replace(/\{(\d)\}/g, (_, n) => (w.ranks?.[n] || [])[(state.wRank || 1) - 1] ?? '?');
    return {target, li, text, source: w.name, tag: t('cb_src_weapon', {r: state.wRank || 1}), group: 'weapon', cond: 'weapon'};
  }
  const [kind, num] = target.split('-');
  if (kind === 'skill') {
    const s = c.skills?.[Number(num)];
    if (!s) return null;
    const text = (vi && s.desc_vi?.[li]) || s.desc?.[li] || '';
    return {target, li, text, source: s.name, tag: s.type, group: 'skill', cond: null};
  }
  const node = (c.resonance_chain || []).find((n) => n.node === Number(num));
  if (!node) return null;
  const text = (vi && node.desc_vi?.[li]) || node.desc?.[li] || '';
  return {target, li, text, source: node.name, tag: 'S' + node.node, group: 'chain', cond: Number(num)};
}

// Assumptions ("tình huống"): Resonance Chain owned up to S{n}, signature weapon equipped or not.
const allowed = (r) => r && !(typeof r.cond === 'number' && r.cond > state.comboS) && !(r.cond === 'weapon' && !state.comboWeapon);
const refKey = (r) => r.target + ':' + r.li;
const kindLabel = (kind) => t('cb_kind_' + kind);
const clean = (text) => text.replace(/^•\s*/, '');

// One card per source (skill entry, chain node, weapon) listing every line it contributes.
function sourceCards(items, withSteps) {
  const bySrc = new Map();
  items.forEach((a) => {
    if (!bySrc.has(a.r.target)) bySrc.set(a.r.target, []);
    bySrc.get(a.r.target).push(a);
  });
  return `<ul class="cb-cards">${[...bySrc.values()].map((list) => {
    const r0 = list[0].r;
    return `<li class="cb-card g-${r0.group}">
      <button type="button" class="cb-src" data-cb-target="${esc(r0.target)}" data-cb-line="${list[0].r.li}" data-tip="${esc(t('cb_go_tip'))}">
        <span class="cb-tag">${esc(r0.tag)}</span><span class="cb-src-name">${esc(r0.source)}</span>
        <svg viewBox="0 0 16 16" aria-hidden="true" width="11" height="11"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
      <ul class="cb-lines">${list.map((a) => `<li>
        <p>${esc(clean(a.r.text))}</p>
        ${withSteps && a.steps?.length ? `<div class="cb-at"><span>${esc(t('cb_at'))}</span>${a.steps.map((n) =>
          `<button type="button" class="cb-at-step" data-cb-step="${n - 1}">${n}</button>`).join('')}</div>` : ''}
      </li>`).join('')}</ul>
    </li>`;
  }).join('')}</ul>`;
}

function stepChip(st, i, sel, count) {
  const mono = KIND_MONO[st.kind];
  const label = st.label || st.text;
  const short = mono ? label.replace(/^(?:Hold\s+)?(?:Basic|Heavy|Skill|Ultimate|Intro|Outro|Echo|Mid-?Air)\s*:\s*/i, '') : label;
  return `<li class="cb-chip-wrap"><button type="button" class="cb-chip k-${st.kind}${i === sel ? ' is-sel' : ''}${count ? ' has-eff' : ''}"
      data-cb-step="${i}" aria-pressed="${i === sel}" data-tip="${esc(`${i + 1}. ${kindLabel(st.kind)} — ${label}`)}">
    <span class="cb-chip-no">${i + 1}</span>${mono ? `<span class="cb-chip-k">${mono}</span>` : ''}
    <span class="cb-chip-l">${esc(short)}</span>${st.n ? `<span class="cb-chip-n">×${st.n}</span>` : ''}
    ${count ? `<span class="cb-chip-c" aria-label="${esc(t('cb_eff_count', {n: count}))}">${count}</span>` : ''}
  </button></li>`;
}

function groupedList(items, withSteps) {
  const groups = [['skill', t('cb_group_skill')], ['chain', t('cb_group_chain')], ['weapon', t('cb_group_weapon')]];
  return groups.map(([g, title]) => {
    const list = items.filter((a) => a.r.group === g);
    if (!list.length) return '';
    return `<section class="cb-group g-${g}"><h5>${esc(title)} <small>${list.length}</small></h5>${sourceCards(list, withSteps)}</section>`;
  }).join('');
}

export async function renderCombo() {
  const c = state.current;
  const box = $('d-combo');
  if (!c || !box) return;
  const data = await load(c.slug);
  if (state.current !== c) return;  // the visitor opened another profile meanwhile
  const rots = data?.rotations || [];
  const src = data?.source || c.source;
  const srcLink = src ? `<a href="${esc(src)}" target="_blank" rel="noopener noreferrer">prydwen.gg</a>` : 'prydwen.gg';
  if (!rots.length) {
    box.innerHTML = `<p class="cb-empty">${t('cb_empty_html', {src: srcLink})}</p>`;
    return;
  }
  const ri = Math.min(state.comboRot, rots.length - 1);
  const rot = rots[ri];
  const maxS = (c.resonance_chain || []).length;
  const hasWeapon = !!c.signature_weapon;

  // Resolve every step once; a step activating exactly what an earlier one did points back to it.
  const firstSeen = new Map();
  const activated = new Map();  // refKey -> {r, steps[]}
  const rows = rot.steps.map((st, i) => {
    const refs = (st.refs || []).map((ref) => resolve(c, ref)).filter(allowed);
    const key = refs.map(refKey).join('|');
    let same = null;
    if (key) {
      if (firstSeen.has(key)) same = firstSeen.get(key);
      else firstSeen.set(key, i + 1);
    }
    refs.forEach((r) => {
      const k = refKey(r);
      if (!activated.has(k)) activated.set(k, {r, steps: []});
      const a = activated.get(k);
      if (!a.steps.includes(i + 1)) a.steps.push(i + 1);
    });
    return {st, refs, same};
  });
  // Default selection: the first step that activates something.
  if (state.comboStep == null || state.comboStep >= rows.length) {
    state.comboStep = Math.max(0, rows.findIndex((r) => r.refs.length));
  }
  const sel = state.comboStep;

  const counts = {};
  rot.steps.forEach((st) => { if (st.kind !== 'move' && st.kind !== 'other') counts[st.kind] = (counts[st.kind] || 0) + (st.n || 1); });
  const unused = (data.triggers || []).map((ref) => resolve(c, ref)).filter(allowed)
    .filter((r) => !activated.has(refKey(r))).map((r) => ({r, steps: []}));

  const toolbar = `<div class="cb-toolbar">
    ${rots.length > 1 ? `<div class="cb-rots" role="tablist" aria-label="${esc(t('cb_rot_aria'))}">${rots.map((r, i) =>
      `<button type="button" role="tab" data-cb-rot="${i}" aria-selected="${i === ri}">${esc((!state.showEn && r.title_vi) || r.title)}</button>`).join('')}</div>`
      : `<p class="cb-rot-one">${esc((!state.showEn && rot.title_vi) || rot.title)}</p>`}
    <div class="cb-assume">
      <span class="cb-assume-k">${esc(t('cb_assume'))}</span>
      ${maxS ? `<div class="cb-seg" role="group" aria-label="${esc(t('cb_chain_aria'))}">${Array.from({length: maxS + 1}, (_, s) =>
        `<button type="button" data-cb-s="${s}" aria-pressed="${s === state.comboS}">S${s}</button>`).join('')}</div>` : ''}
      ${hasWeapon ? `<label class="cb-check" data-tip="${esc(c.signature_weapon.name)}"><input type="checkbox" data-cb-weapon ${state.comboWeapon ? 'checked' : ''}><span>${esc(t('cb_weapon_short'))}</span></label>` : ''}
    </div>
  </div>`;

  const strip = `<section class="cb-strip-box">
    <header class="cb-strip-head"><h4>${esc(t('cb_seq_title', {n: rows.length}))}</h4>
      <div class="cb-counts">${KINDS.filter((k) => counts[k]).map((k) =>
        `<span class="cb-count k-${k}"><b>${counts[k]}</b>${esc(KIND_MONO[k] || kindLabel(k))}</span>`).join('')}</div></header>
    <ol class="cb-strip">${rows.map(({st, refs}, i) => stepChip(st, i, sel, refs.length)).join('')}</ol>
  </section>`;

  const cur = rows[sel];
  const st = cur.st;
  const hint = st.hint ? `<p class="cb-hint"${st.hint_vi && !state.showEn ? ` data-tip="${esc(st.hint)}"` : ''}>${esc((!state.showEn && st.hint_vi) || st.hint)}</p>` : '';
  let body;
  if (cur.same) {
    body = `<p class="cb-same">${esc(t('cb_same_as', {k: cur.same}))} <button type="button" class="cb-link" data-cb-step="${cur.same - 1}">${esc(t('cb_go_step', {k: cur.same}))}</button></p>`;
  } else if (cur.refs.length) {
    body = sourceCards(cur.refs.map((r) => ({r})), false);
  } else {
    body = `<p class="cb-none">${esc(t(st.kind === 'move' || st.kind === 'other' ? 'cb_step_move' : 'cb_step_none'))}</p>`;
  }
  const detail = `<section class="cb-detail k-${st.kind}" aria-live="polite">
    <header class="cb-detail-head">
      <span class="cb-detail-no">${sel + 1}<small>/${rows.length}</small></span>
      <div class="cb-detail-id">
        <span class="cb-kind">${esc(kindLabel(st.kind))}${st.cond ? ` · <em>${esc(st.cond)}</em>` : ''}</span>
        <h4>${esc(st.label || st.text)}${st.n ? ` <span class="cb-chip-n">×${st.n}</span>` : ''}</h4>
        ${hint}
      </div>
      <div class="cb-nav">
        <button type="button" data-cb-step="${sel - 1}" ${sel === 0 ? 'disabled' : ''} aria-label="${esc(t('cb_prev'))}"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M10 3 5 8l5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
        <button type="button" data-cb-step="${sel + 1}" ${sel === rows.length - 1 ? 'disabled' : ''} aria-label="${esc(t('cb_next'))}"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
      </div>
    </header>
    ${cur.refs.length && !cur.same ? `<p class="cb-detail-k">${esc(t('cb_step_activates', {n: cur.refs.length}))}</p>` : ''}
    ${body}
  </section>`;

  const total = `<details class="cb-fold" open>
    <summary><span>${esc(t('cb_sum_title'))}</span><small>${esc(t('cb_sum_count', {n: activated.size}))}</small></summary>
    <p class="cb-fold-hint">${esc(t('cb_sum_hint'))}</p>
    ${activated.size ? groupedList([...activated.values()], true) : `<p class="cb-none">${esc(t('cb_no_effects'))}</p>`}
  </details>`;
  const missed = unused.length ? `<details class="cb-fold">
    <summary><span>${esc(t('cb_unused_title'))}</span><small>${unused.length}</small></summary>
    <p class="cb-fold-hint">${esc(t('cb_unused_hint'))}</p>
    ${groupedList(unused, false)}
  </details>` : '';

  box.innerHTML = `${toolbar}${strip}${detail}${total}${missed}<p class="cb-note">${t('cb_note_html', {src: srcLink})}</p>`;
}

// Events (delegated from main.js). Returns true when handled.
export function onComboClick(target) {
  const step = target.closest('[data-cb-step]');
  if (step && !step.disabled) {
    const fromTotals = !!step.closest('.cb-fold, .cb-same');
    state.comboStep = Number(step.dataset.cbStep);
    renderCombo().then(() => {
      const box = $('d-combo');
      box.querySelector(`.cb-chip[data-cb-step="${state.comboStep}"]`)?.focus({preventScroll: true});
      if (fromTotals) box.querySelector('.cb-strip-box')?.scrollIntoView({behavior: 'smooth', block: 'start'});
    });
    return true;
  }
  const rot = target.closest('[data-cb-rot]');
  if (rot) { state.comboRot = Number(rot.dataset.cbRot); state.comboStep = null; renderCombo(); return true; }
  const s = target.closest('[data-cb-s]');
  if (s) { state.comboS = Number(s.dataset.cbS); renderCombo(); return true; }
  return false;
}

export function onComboInput(el) {
  if (!el.matches('[data-cb-weapon]')) return false;
  state.comboWeapon = el.checked;
  renderCombo();
  return true;
}

// Left/Right arrows move through the steps while the strip has focus.
export function onComboKey(e) {
  if (!e.target.closest?.('.cb-strip') || !['ArrowLeft', 'ArrowRight'].includes(e.key)) return false;
  const btn = $('d-combo').querySelector(`.cb-chip[data-cb-step="${state.comboStep + (e.key === 'ArrowRight' ? 1 : -1)}"]`);
  if (btn) { e.preventDefault(); btn.click(); }
  return true;
}

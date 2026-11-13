// "Combo" tab: rotation steps (prydwen.gg) with the kit lines each step activates (/api/combos/{slug}).
// The step -> line matching is built by scripts/build_combos.py; this module only renders it.
import {$, esc, state} from './core.js';
import {t} from './i18n.js';

const cache = new Map();  // slug -> combos payload (or null when the Resonator has none)
const KINDS = ['basic', 'heavy', 'skill', 'lib', 'intro', 'outro', 'echo', 'midair', 'dodge', 'move', 'other'];

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
    return {target, li, text, source: w.name, tag: t('cb_src_weapon', {r: state.wRank || 1}), cond: 'weapon'};
  }
  const [kind, num] = target.split('-');
  if (kind === 'skill') {
    const s = c.skills?.[Number(num)];
    if (!s) return null;
    const text = (vi && s.desc_vi?.[li]) || s.desc?.[li] || '';
    return {target, li, text, source: s.name, tag: s.type, cond: null};
  }
  const node = (c.resonance_chain || []).find((n) => n.node === Number(num));
  if (!node) return null;
  const text = (vi && node.desc_vi?.[li]) || node.desc?.[li] || '';
  return {target, li, text, source: node.name, tag: 'S' + node.node, cond: Number(num)};
}

// Assumptions ("tình huống"): Resonance Chain owned up to S{n}, signature weapon equipped or not.
const allowed = (r) => r && !(typeof r.cond === 'number' && r.cond > state.comboS) && !(r.cond === 'weapon' && !state.comboWeapon);
const refKey = (r) => r.target + ':' + r.li;

function effectHTML(r, steps) {
  const cls = r.cond === 'weapon' ? 'is-weapon' : typeof r.cond === 'number' ? 'is-chain' : '';
  const at = steps?.length ? `<span class="cb-at">${esc(t('cb_at_steps', {s: steps.join(', ')}))}</span>` : '';
  return `<li class="cb-eff ${cls}">
    <button type="button" class="cb-src" data-cb-target="${esc(r.target)}" data-cb-line="${r.li}" data-tip="${esc(t('cb_go_tip'))}">
      <span class="cb-tag">${esc(r.tag)}</span><span class="cb-src-name">${esc(r.source)}</span></button>
    <span class="cb-text">${esc(r.text.replace(/^•\s*/, ''))}</span>${at}
  </li>`;
}

function kindLabel(kind) { return t('cb_kind_' + kind); }

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

  // Resolve every step once, then mark repeats ("same as step k").
  const firstSeen = new Map();
  const activated = new Map();  // refKey -> {r, steps[]}
  const stepRows = rot.steps.map((st, i) => {
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

  const counts = {};
  rot.steps.forEach((st) => { if (st.kind !== 'move' && st.kind !== 'other') counts[st.kind] = (counts[st.kind] || 0) + (st.n || 1); });
  const unused = (data.triggers || []).map((ref) => resolve(c, ref)).filter(allowed).filter((r) => !activated.has(refKey(r)));

  const pick = rots.length > 1 ? `<div class="cb-rots" role="tablist" aria-label="${esc(t('cb_rot_aria'))}">${rots.map((r, i) =>
    `<button type="button" role="tab" data-cb-rot="${i}" aria-selected="${i === ri}">${esc((!state.showEn && r.title_vi) || r.title)}</button>`).join('')}</div>` : '';

  const assume = `<div class="cb-assume">
    <span class="cb-assume-k">${esc(t('cb_assume'))}</span>
    ${maxS ? `<div class="cb-seg" role="group" aria-label="${esc(t('cb_chain_aria'))}">${Array.from({length: maxS + 1}, (_, s) =>
      `<button type="button" data-cb-s="${s}" aria-pressed="${s === state.comboS}">S${s}</button>`).join('')}</div>` : ''}
    ${hasWeapon ? `<label class="cb-check"><input type="checkbox" data-cb-weapon ${state.comboWeapon ? 'checked' : ''}><span>${esc(t('cb_weapon', {w: c.signature_weapon.name}))}</span></label>` : ''}
  </div>`;

  const summary = `<section class="cb-sum">
    <header><h4>${esc(t('cb_sum_title'))}</h4><p>${esc(t('cb_sum_hint'))}</p></header>
    <div class="cb-counts">${KINDS.filter((k) => counts[k]).map((k) =>
      `<span class="cb-count k-${k}"><b>${counts[k]}×</b> ${esc(kindLabel(k))}</span>`).join('')}</div>
    ${activated.size ? `<ul class="cb-effs">${[...activated.values()].map((a) => effectHTML(a.r, a.steps)).join('')}</ul>` : `<p class="cb-none">${esc(t('cb_no_effects'))}</p>`}
  </section>`;

  const timeline = `<ol class="cb-steps">${stepRows.map(({st, refs, same}, i) => {
    const hint = st.hint ? `<span class="cb-hint"${st.hint_vi && !state.showEn ? ` data-tip="${esc(st.hint)}"` : ''}>${esc((!state.showEn && st.hint_vi) || st.hint)}</span>` : '';
    const cond = st.cond ? `<span class="cb-cond">${esc(st.cond)}</span>` : '';
    const n = st.n ? `<span class="cb-n">×${st.n}</span>` : '';
    let body = '';
    if (same) body = `<p class="cb-same">${esc(t('cb_same_as', {k: same}))}</p>`;
    else if (refs.length <= 2) body = `<ul class="cb-effs">${refs.map((r) => effectHTML(r)).join('')}</ul>`;
    else {
      body = `<ul class="cb-effs">${refs.slice(0, 2).map((r) => effectHTML(r)).join('')}</ul>
        <details class="cb-more"><summary>${esc(t('cb_more', {n: refs.length - 2}))}</summary>
        <ul class="cb-effs">${refs.slice(2).map((r) => effectHTML(r)).join('')}</ul></details>`;
    }
    return `<li class="cb-step k-${st.kind}">
      <div class="cb-step-head"><span class="cb-no">${i + 1}</span>
        <span class="cb-kind">${esc(kindLabel(st.kind))}</span>
        <b class="cb-label">${esc(st.label || st.text)}</b>${n}${cond}${hint}</div>
      ${body}
    </li>`;
  }).join('')}</ol>`;

  const missed = unused.length ? `<details class="cb-unused">
    <summary>${esc(t('cb_unused_title', {n: unused.length}))}</summary>
    <p>${esc(t('cb_unused_hint'))}</p>
    <ul class="cb-effs">${unused.map((r) => effectHTML(r)).join('')}</ul>
  </details>` : '';

  box.innerHTML = `${pick}${assume}
    <div class="cb-grid"><div class="cb-main">${timeline}</div><aside class="cb-side">${summary}${missed}</aside></div>
    <p class="cb-note">${t('cb_note_html', {src: srcLink})}</p>`;
}

// Events (delegated from main.js). Returns true when handled.
export function onComboClick(target) {
  const rot = target.closest('[data-cb-rot]');
  if (rot) { state.comboRot = Number(rot.dataset.cbRot); renderCombo(); return true; }
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

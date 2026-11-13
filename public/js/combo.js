// "Combo" tab, told as what the player does: "Basic 1 → 3 → Dash → ..." with the short result of each action.
// Actions and results are built by scripts/build_combos.py (/api/combos/{slug}); this module only renders them.
import {$, esc, state} from './core.js';
import {t} from './i18n.js';

const cache = new Map();  // slug -> combos payload (or null when the Resonator has none)

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

// Original kit line behind a result, shown as its tooltip.
function originalLine(c, [target, li]) {
  const vi = !state.showEn;
  if (target === 'weapon') {
    const w = c.signature_weapon;
    if (!w) return '';
    const lines = vi && w.passive_vi?.length ? w.passive_vi : w.passive;
    return `${w.name}: ` + (lines[li] || '').replace(/\{(\d)\}/g, (_, n) => (w.ranks?.[n] || [])[(state.wRank || 1) - 1] ?? '?');
  }
  const [kind, num] = target.split('-');
  if (kind === 'skill') {
    const s = c.skills?.[Number(num)];
    return s ? `${s.name}: ${(vi && s.desc_vi?.[li]) || s.desc?.[li] || ''}` : '';
  }
  const node = (c.resonance_chain || []).find((n) => n.node === Number(num));
  return node ? `S${node.node} ${node.name}: ${(vi && node.desc_vi?.[li]) || node.desc?.[li] || ''}` : '';
}

// Assumptions: Resonance Chain owned up to S{n}, signature weapon equipped or not.
const allowed = (o) => !(typeof o.cond === 'number' && o.cond > state.comboS) && !(o.cond === 'weapon' && !state.comboWeapon);

function resultHTML(c, o) {
  const badge = o.cond === 'weapon' ? `<i>${esc(t('cb_badge_weapon'))}</i>` : typeof o.cond === 'number' ? `<i>S${o.cond}</i>` : '';
  const cls = o.cond === 'weapon' ? ' is-weapon' : typeof o.cond === 'number' ? ' is-chain' : '';
  return `<button type="button" class="cb-res${cls}" data-cb-target="${esc(o.ref[0])}" data-cb-line="${o.ref[1]}"
    data-tip="${esc(originalLine(c, o.ref).replace(/^(.*?:\s)•\s*/, '$1'))}">${badge}${esc(state.showEn ? o.en : o.vi)}</button>`;
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
  const flow = rots[ri].flow;
  const en = state.showEn;
  const maxS = (c.resonance_chain || []).length;
  const title = (r) => (!en && r.title_vi) || r.title;

  const pick = rots.length > 1 ? `<div class="cb-rots" role="tablist" aria-label="${esc(t('cb_rot_aria'))}">${rots.map((r, i) =>
    `<button type="button" role="tab" data-cb-rot="${i}" aria-selected="${i === ri}">${esc(title(r))}</button>`).join('')}</div>` : '';

  const assume = `<div class="cb-assume">
    <span>${esc(t('cb_assume'))}</span>
    ${maxS ? `<div class="cb-seg" role="group" aria-label="${esc(t('cb_chain_aria'))}">${Array.from({length: maxS + 1}, (_, s) =>
      `<button type="button" data-cb-s="${s}" aria-pressed="${s === state.comboS}">S${s}</button>`).join('')}</div>` : ''}
    ${c.signature_weapon ? `<label class="cb-check"><input type="checkbox" data-cb-weapon ${state.comboWeapon ? 'checked' : ''}><span>${esc(c.signature_weapon.name)}</span></label>` : ''}
  </div>`;

  const formula = `<p class="cb-formula" aria-label="${esc(t('cb_formula'))}">${flow.map((a) =>
    `<span class="cb-tok k-${a.kind}">${esc(a.token)}${a.n ? `×${a.n}` : ''}</span>`).join('<span class="cb-arrow" aria-hidden="true">→</span>')}</p>`;

  const steps = `<ol class="cb-list">${flow.map((a, i) => {
    const res = a.out.filter(allowed);
    const hint = a.hint ? `<span class="cb-hint"${!en && a.hint_vi ? ` data-tip="${esc(a.hint)}"` : ''}>${esc((!en && a.hint_vi) || a.hint)}</span>` : '';
    let then = '';
    if (a.same != null) then = `<p class="cb-then cb-then-same">${esc(t('cb_same_as', {k: a.same + 1}))}</p>`;
    else if (res.length) then = `<p class="cb-then"><span class="cb-then-k">${esc(t('cb_then'))}</span>${res.map((o) => resultHTML(c, o)).join('')}</p>`;
    return `<li class="cb-act k-${a.kind}">
      <span class="cb-n">${i + 1}</span>
      <div class="cb-act-body">
        <p class="cb-say">${a.cond ? `<em>${esc(a.cond)}:</em> ` : ''}${esc(en ? a.say_en : a.say_vi)}${a.n ? ` <b>×${a.n}</b>` : ''}</p>
        ${hint}${then}
      </div>
    </li>`;
  }).join('')}</ol>`;

  box.innerHTML = `${pick}${formula}${assume}${steps}<p class="cb-note">${t('cb_note_html', {src: srcLink})}</p>`;
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

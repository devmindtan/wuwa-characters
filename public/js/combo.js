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

// The button a step is about: E / Q / R / Basic... (movement steps show their own word: Dash, Jump, Swap).
const capOf = (a) => (['move', 'other'].includes(a.kind) ? a.token : t('cb_cap_' + a.kind));

// Assumptions: Resonance Chain owned up to S{n}, signature weapon equipped or not.
const allowed = (o) => !(typeof o.cond === 'number' && o.cond > state.comboS) && !(o.cond === 'weapon' && !state.comboWeapon);

function resultHTML(c, o) {
  const badge = o.cond === 'weapon' ? `<i>${esc(t('cb_badge_weapon'))}</i>` : typeof o.cond === 'number' ? `<i>S${o.cond}</i>` : '';
  const cls = o.cond === 'weapon' ? ' is-weapon' : typeof o.cond === 'number' ? ' is-chain' : '';
  return `<button type="button" class="cb-res${cls}" data-cb-target="${esc(o.ref[0])}" data-cb-line="${o.ref[1]}"
    data-tip="${esc(originalLine(c, o.ref).replace(/^(.*?:\s)•\s*/, '$1'))}">${badge}${esc(state.showEn ? o.en : o.vi)}</button>`;
}

// "What this combo gives you", added up from the per-action results (already classified by the build).
function summaryHTML(c, flow) {
  const en = state.showEn;
  const presses = {};
  const states = [], status = new Map(), resources = new Map(), self = [], next = [], guard = [], control = [], extra = [];
  const energy = [], summons = [], spends = [], moves = [], damage = [];
  const push = (list, o) => { if (!list.some((x) => x.vi === o.vi)) list.push(o); };
  flow.forEach((a) => {
    if (!['move', 'other'].includes(a.kind)) presses[a.kind] = (presses[a.kind] || 0) + (a.times || 1);
    a.out.filter(allowed).forEach((o) => {
      const reps = a.n || 1;
      if (o.cat === 'state') { if (!states.includes(o.name)) states.push(o.name); }
      else if (o.cat === 'resource' || o.cat === 'status') {
        const map = o.cat === 'status' ? status : resources;
        const cur = map.get(o.name) || {qty: 0, o};
        cur.qty += (o.qty || 0) * reps;
        map.set(o.name, cur);
      } else if (o.cat === 'stat') push(a.kind === 'outro' ? next : self, o);
      else if (o.cat === 'defense' || o.cat === 'heal') push(guard, o);
      else if (o.cat === 'control') push(control, o);
      else if (o.cat === 'trigger') push(extra, o);
      else if (o.cat === 'energy') push(energy, o);
      else if (o.cat === 'summon') push(summons, o);
      else if (o.cat === 'consume') push(spends, o);
      else if (o.cat === 'unlock') push(moves, o);
      else if (o.cat === 'damage') push(damage, o);
    });
  });
  const fmt = (n) => (Number.isInteger(n) ? n : Number(n.toFixed(1))).toLocaleString(en ? 'en' : 'vi');
  const chips = (list) => list.map((o) => resultHTML(c, o)).join('');
  const sum = (map, word) => [...map.values()].map(({qty, o}) => resultHTML(c, {...o, vi: `${word.vi}${fmt(qty)} ${o.name}`, en: `${word.en}${fmt(qty)} ${o.name}`})).join('');
  const kinds = ['basic', 'heavy', 'skill', 'echo', 'lib', 'intro', 'outro', 'midair', 'dodge'].filter((k) => presses[k]);
  const rows = [
    [t('cb_sum_inputs'), kinds.map((k) => {
      const cap = t('cb_cap_' + k), name = t('cb_key_' + k);
      return `<span class="cb-keycount k-${k}"><kbd>${esc(cap)}</kbd><b>×${presses[k]}</b>${name !== cap ? `<small>${esc(name)}</small>` : ''}</span>`;
    }).join('')],
    states.length && [t('cb_sum_states'), `<span class="cb-sum-txt">${states.map(esc).join(' → ')}</span>`],
    moves.length && [t('cb_sum_moves'), chips(moves)],
    (resources.size || energy.length) && [t('cb_sum_gain'), sum(resources, {vi: '+', en: '+'}) + chips(energy)],
    spends.length && [t('cb_sum_spend'), chips(spends)],
    (status.size || control.length || damage.length) && [t('cb_sum_enemy'), chips(damage) + sum(status, {vi: 'Gây ', en: 'Inflict '}) + chips(control)],
    summons.length && [t('cb_sum_summon'), chips(summons)],
    self.length && [t('cb_sum_self'), chips(self)],
    guard.length && [t('cb_sum_guard'), chips(guard)],
    next.length && [t('cb_sum_next'), chips(next)],
    extra.length && [t('cb_sum_extra'), chips(extra)],
  ].filter(Boolean);
  return `<section class="cb-sum">
    <h4>${esc(t('cb_sum_title'))} <small>${esc(t('cb_sum_auto'))}</small></h4>
    <dl>${rows.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${v}</dd></div>`).join('')}</dl>
  </section>`;
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
    const same = a.same != null ? `<span class="cb-same-tag">${esc(t('cb_same_short', {k: a.same + 1}))}</span>` : '';
    if (a.same != null) then = '';
    else if (res.length) then = `<p class="cb-then"><span class="cb-then-k">${esc(t('cb_then'))}</span>${res.map((o) => resultHTML(c, o)).join('')}</p>`;
    return `<li class="cb-act k-${a.kind}${a.same != null ? ' is-same' : ''}">
      <span class="cb-n">${i + 1}</span>
      <div class="cb-act-body">
        <p class="cb-say"><kbd class="cb-cap k-${a.kind}">${esc(capOf(a))}</kbd><span>${a.cond ? `<em>${esc(a.cond)}:</em> ` : ''}${esc(en ? a.say_en : a.say_vi)}${a.n ? ` <b>×${a.n}</b>` : ''}${same}</span></p>
        ${hint}${then}
      </div>
    </li>`;
  }).join('')}</ol>`;

  const cancelHelp = flow.some((a) => a.hint) ? `<details class="cb-help"><summary>${esc(t('cb_cancel_q'))}</summary>
    <p>${esc(t('cb_cancel_a'))}</p></details>` : '';
  box.innerHTML = `${pick}${assume}${summaryHTML(c, flow)}${formula}${cancelHelp}${steps}<p class="cb-note">${t('cb_note_html', {src: srcLink})}</p>`;
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

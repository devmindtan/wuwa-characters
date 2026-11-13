// Mechanic dialog: explanations, quotes, kit traits, Resonators using it.
import {$, elIcon, esc, mechDialog, state} from './core.js';
import {I18N, t} from './i18n.js';
import {scrollToId} from './links.js';

// Same term can be a global mechanic or a kit term of several Resonators: prefer the one for this page.
export function findMechanic(term) {
  const slug = state.current?.slug;
  const list = state.mechanics.filter((x) => x.term === term);
  return list.find((x) => x.owners?.includes(slug)) || list.find((x) => !x.owners?.length) || list[0];
}

// "Definition.\n• point\n• point" -> paragraph + bullet list
export function summaryHTML(text) {
  const lines = String(text).split('\n').filter((l) => l.trim());
  const head = lines.filter((l) => !l.startsWith('• '));
  const items = lines.filter((l) => l.startsWith('• '));
  return head.map((l) => `<span class="ms-p">${esc(l)}</span>`).join('')
    + (items.length ? `<ul class="ms-list">${items.map((l) => `<li>${esc(l.slice(2))}</li>`).join('')}</ul>` : '');
}

export function autoQuote(m, cur) {
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

export function openMechanic(termOrObj) {
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
export const roleKeys = () => (state.index.rules?.roles || []).map((r) => r.key);
export const roleKeywords = (k) => (state.index.rules?.roles || []).find((r) => r.key === k)?.kw || '';
export const roleLabel = (k) => t('role_' + k);

export function mechUsers(m) {
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
export const STATUS_KEYS = new Set(['spectro_frazzle', 'aero_erosion', 'havoc_bane', 'fusion_burst', 'glacio_chafe', 'electro_flare']);
export const traitKeys = () => (state.index.rules?.traits || []).map((r) => r.key);
export const traitKeywords = (k) => (state.index.rules?.traits || []).find((r) => r.key === k)?.kw || '';
export const traitsOf = (c) => state.index.chars[c.slug]?.traits || {};
export const traitLabel = (k) => ('trait_' + k) in I18N.vi ? t('trait_' + k) : k.split('_').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ');

export const traitDesc = (k, full = false) => {
  if (('traitd_' + k) in I18N.vi) return t('traitd_' + k);
  const m = state.mechanics.find((x) => x.term === traitLabel(k) && !x.owners?.length);
  const sum = m && ((state.showEn ? m.summary_en : m.summary_vi) || m.summary_vi);
  if (!sum) return t('trait_status_desc', {name: traitLabel(k)});
  return full ? sum : sum.split('\n')[0];
};

export function renderTraits(c) {
  const tr = traitsOf(c);
  const keys = traitKeys().filter((k) => tr[k]);
  $('d-traits').hidden = !keys.length;
  $('d-traits-list').innerHTML = keys.map((k) =>
    `<button type="button" class="trait trait-${k}" data-trait="${k}" data-tip="${esc(traitDesc(k))}">${esc(traitLabel(k))}<small>${tr[k].length}</small></button>`).join('');
}

export function openTrait(key) {
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

export function renderMechUsers() {
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
// The dialog closes only via ✕, Esc, or a click that both starts and ends on the
// backdrop. Clicks inside the panel (padding, text, items, text selection) never close it.
export const outsideDialog = (e) => {
  const r = mechDialog.getBoundingClientRect();
  return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
};
export let pressedOnBackdrop = false;
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

// Shared state, DOM references, small helpers and game icons.
export const EL_VI = {Spectro:'Quang Phổ',Havoc:'Hỗn Độn',Aero:'Khí',Electro:'Lôi',Fusion:'Nhiệt',Glacio:'Băng'};
export const WEAP_VI = {Sword:'Kiếm',Broadblade:'Đại Kiếm',Pistols:'Súng Lục',Gauntlets:'Găng Tay',Rectifier:'Pháp Khí'};
// Official element text colors (in-game / Wuthering Waves Wiki dark theme).
export const COLOR_HEX = {Spectro:'#F8E56C',Havoc:'#E649A6',Aero:'#55FFB5',Electro:'#B46BFF',Fusion:'#F0744E',Glacio:'#41AEFB'};
// "<Element> DMG ..." phrases are coloured by element (colour only, no bold).
export const DMG_SUFFIXES = [' DMG Bonus', ' DMG Amplification', ' DMG RES', ' DMG', ' RES'];

export const state = {
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

export const $ = (id) => document.getElementById(id);
export const grid = $('grid');
export const empty = $('empty');
export const loading = $('loading');
export const errorBox = $('error');
export const shown = $('shown');
export const listView = $('listView');
export const detailView = $('detailView');
export const q = $('q');
export const fEl = $('f-el');
export const fWeap = $('f-weap');
export const fR = $('f-r');
export const backBtn = $('back');
export const dSkills = $('d-skills');
export const dChain = $('d-chain');
export const mechDialog = $('mechDialog');

export const esc = (s) => (s ?? '').toString().replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
export const stars = (r) => r ? '★'.repeat(r) : '';
export const elColor = (el) => COLOR_HEX[el] || '#d6c4a1';
export const regexEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export const elVi = (el) => EL_VI[el] || el || '';
export const weapVi = (w) => WEAP_VI[w] || w || '';

// Official in-game element/weapon icons, served from public/assets/icons/.
export const icon = (kind, v, cls = '') => v
  ? `<img class="ico ico-${kind} ${cls}" src="assets/icons/${kind}/${esc(v.toLowerCase())}.png" alt="" aria-hidden="true" width="18" height="18" decoding="async">`
  : '';
export const elIcon = (v, cls) => icon('element', v, cls);
export const weapIcon = (v, cls) => icon('weapon', v, cls);
export const elDot = (v) => elIcon(v, 'dd-ico');
export const weapDot = (v) => weapIcon(v, 'dd-ico');
export const rarityMark = (v) => v ? `<i class="dd-star r${v}">★</i>` : '';

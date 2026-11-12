const EL_VI = {Spectro:'Quang Phổ',Havoc:'Hỗn Độn',Aero:'Khí',Electro:'Lôi',Fusion:'Nhiệt',Glacio:'Băng'};
const WEAP_VI = {Sword:'Kiếm',Broadblade:'Đại Kiếm',Pistols:'Súng Lục',Gauntlets:'Găng Tay',Rectifier:'Pháp Khí'};
const KIND_VI = {system:'Cơ chế',resource:'Tài nguyên',status:'Negative Status',mode:'Trạng thái',skill:'Kỹ năng',summon:'Triệu hồi',stat:'Chỉ số'};
const COLOR_HEX = {Spectro:'#f4e6a4',Havoc:'#d38af0',Aero:'#7de8c0',Electro:'#b5a6ff',Fusion:'#ff9a7c',Glacio:'#9ed8ff'};

const state = {
  meta: null,
  characters: [],
  mechanics: [],
  bySlug: new Map(),
  current: null,
  showEn: false,
  savedScroll: 0,
  detailOpen: false,
};

const $ = (id) => document.getElementById(id);
const grid = $('grid');
const empty = $('empty');
const loading = $('loading');
const errorBox = $('error');
const shown = $('shown');
const listView = $('listView');
const detailView = $('detailView');
const q = $('q');
const fEl = $('f-el');
const fWeap = $('f-weap');
const fR = $('f-r');
const toggleEn = $('toggle-en');
const backBtn = $('back');
const dSkills = $('d-skills');
const mechDialog = $('mechDialog');

const esc = (s) => (s ?? '').toString().replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const stars = (r) => r ? '★'.repeat(r) : '';
const elColor = (el) => COLOR_HEX[el] || '#d6c4a1';
const regexEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const elVi = (el) => EL_VI[el] || el || '';
const weapVi = (w) => WEAP_VI[w] || w || '';

function fillSelect(sel, values, labelFn) {
  values.forEach((v) => {
    const o = document.createElement('option');
    o.value = v;
    o.textContent = labelFn(v);
    sel.appendChild(o);
  });
}

/* ---------- custom dropdown (enhances a native <select>) ---------- */
let ddSeq = 0;
const openDropdowns = new Set();

function enhanceSelect(sel, decorate = () => '') {
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

const elDot = (v) => v ? `<i class="dd-dot" style="--c:${elColor(v)}"></i>` : '';
const rarityMark = (v) => v ? `<i class="dd-star r${v}">★</i>` : '';

function cardHTML(c) {
  const col = elColor(c.element);
  return `<article class="card" data-slug="${esc(c.slug)}" tabindex="0" role="button" aria-label="Mở hồ sơ ${esc(c.name)}" style="--el:${col};--tint-soft:${col}22">
    <div class="card-media">
      <img src="${esc(c.img_card || c.img_icon)}" alt="${esc(c.name)}" loading="lazy" onerror="this.onerror=null;this.src='${esc(c.img_icon)}'">
      <span class="card-badge">${esc(c.element)}</span>
      <span class="card-rarity ${c.rarity===4?'r4':''}">${stars(c.rarity)}</span>
    </div>
    <div class="card-info">
      <h3>${esc(c.name)}</h3>
      <p><b>${esc(c.element)}</b> · ${esc(c.weapon)}</p>
    </div>
  </article>`;
}

function apply() {
  const term = q.value.trim().toLowerCase();
  const el = fEl.value, w = fWeap.value, r = fR.value;
  const list = state.characters.filter((c) => {
    if (el && c.element !== el) return false;
    if (w && c.weapon !== w) return false;
    if (r && String(c.rarity) !== r) return false;
    if (term) {
      const blob = [
        c.name, c.slug, c.element, elVi(c.element), c.weapon, weapVi(c.weapon),
        c.intro, c.intro_vi,
        (c.changes || []).map((ch) => ch.note).join(' '),
        (c.skills || []).map((s) => [s.name, (s.desc_vi || []).join(' '), (s.desc || []).join(' ')].join(' ')).join(' '),
      ].join(' ').toLowerCase();
      if (!blob.includes(term)) return false;
    }
    return true;
  }).sort((a, b) => (b.rarity - a.rarity) || a.name.localeCompare(b.name));
  grid.innerHTML = list.map(cardHTML).join('');
  shown.textContent = list.length;
  empty.style.display = list.length ? 'none' : 'block';
}

function renderHero() {
  const featured = state.bySlug.get('jinhsi') || state.characters[0];
  if (!featured) return;
  const img = $('hero-img');
  img.src = featured.img_full || featured.img_card || featured.img_icon;
  img.alt = featured.name;
  img.hidden = false;
  img.onerror = () => { img.onerror = null; img.src = featured.img_icon; };
  $('hero-name').textContent = featured.name;
  $('hero-tags').textContent = `${featured.element} · ${featured.weapon}`;
}

function renderMeta() {
  const m = state.meta;
  $('patch-label').textContent = `Patch ${m.patch} · ${m.characters} Resonators`;
  $('stat-count').textContent = m.characters;
  $('stat-elements').textContent = new Set(state.characters.map((c) => c.element).filter(Boolean)).size;
  $('stat-weapons').textContent = new Set(state.characters.map((c) => c.weapon).filter(Boolean)).size;
  $('total').textContent = m.characters;
  $('foot-patch').textContent = `bản game ${m.patch}`;
  document.title = `Wuthering Waves — Resonators Archive · Patch ${m.patch}`;
}

function lineHTML(line) {
  if (line.startsWith('• ')) return {li: true, text: line.slice(2)};
  const short = line.length < 72 && !/[.!?]$/.test(line);
  return {li: false, text: line, sub: short};
}

function renderSkills() {
  const c = state.current;
  if (!c) return;
  let out = '';
  (c.skills || []).forEach((s, i) => {
    const lines = (state.showEn ? s.desc : s.desc_vi) || [];
    let body = '', inList = false;
    for (const line of lines) {
      const l = lineHTML(line);
      if (l.li) {
        if (!inList) { body += '<ul>'; inList = true; }
        body += `<li>${esc(l.text)}</li>`;
      } else {
        if (inList) { body += '</ul>'; inList = false; }
        body += `<p${l.sub ? ' class="sub"' : ''}>${esc(l.text)}</p>`;
      }
    }
    if (inList) body += '</ul>';
    if (!body) body = '<p>Chưa có mô tả chi tiết cho kỹ năng này.</p>';
    out += `<section class="skill" id="skill-${i}" data-index="${i}" tabindex="-1">
      <div class="skill-head"><span class="skill-type">${esc(s.type)}</span><h3>${esc(s.name)}</h3></div>
      <div class="skill-body">${body}</div>
    </section>`;
  });
  dSkills.innerHTML = out;
  dSkills.lang = state.showEn ? 'en' : 'vi';
  renderIntro();
  linkifyAll();
}

function renderIntro() {
  const c = state.current;
  const introEl = $('d-intro');
  const text = state.showEn ? c.intro : c.intro_vi;
  introEl.textContent = text || '';
  introEl.hidden = !text;
  introEl.lang = state.showEn ? 'en' : 'vi';
}

function linkifyAll() {
  const c = state.current;
  if (!c) return;
  const byText = new Map();
  (c.skills || []).forEach((s, i) => {
    if (s.name && !byText.has(s.name)) byText.set(s.name, {type: 'skill', index: i, text: s.name});
  });
  for (const m of state.mechanics) {
    if (!byText.has(m.term)) byText.set(m.term, {type: 'mech', term: m.term, text: m.term});
  }
  const terms = [...byText.values()].sort((a, b) => b.text.length - a.text.length);
  if (!terms.length) return;
  const re = new RegExp('(?<![A-Za-z0-9])(' + terms.map((t) => regexEsc(t.text)).join('|') + ')(?![A-Za-z0-9])', 'g');

  dSkills.querySelectorAll('.skill-body').forEach((body) => {
    const section = body.closest('.skill');
    const ownIndex = Number(section?.dataset.index);
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        if (node.parentElement?.closest('a,button')) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const text = node.nodeValue;
      re.lastIndex = 0;
      let match, last = 0;
      const frag = document.createDocumentFragment();
      while ((match = re.exec(text))) {
        const matched = match[1];
        const term = byText.get(matched);
        if (!term) continue;
        if (term.type === 'skill' && term.index === ownIndex) continue;
        if (match.index > last) frag.appendChild(document.createTextNode(text.slice(last, match.index)));
        frag.appendChild(makeTermNode(term, matched));
        last = match.index + matched.length;
      }
      if (!last) continue;
      if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    }
  });
}

function makeTermNode(term, text) {
  if (term.type === 'skill') {
    const a = document.createElement('a');
    a.href = `#skill-${term.index}`;
    a.className = 'term-link skill-link';
    a.dataset.skill = String(term.index);
    a.textContent = text;
    return a;
  }
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'term-link mech-link';
  b.dataset.mech = term.term;
  b.textContent = text;
  return b;
}

function scrollToSkill(index) {
  const el = $('skill-' + index);
  if (!el) return;
  el.scrollIntoView({behavior: 'smooth', block: 'start'});
  el.classList.remove('flash');
  void el.offsetWidth;
  el.classList.add('flash');
  el.focus({preventScroll: true});
  setTimeout(() => el.classList.remove('flash'), 1900);
}

function renderChanges(c) {
  const box = $('d-changes');
  const list = [...(c.changes || [])].reverse();
  $('d-changes-list').innerHTML = list.map((ch) =>
    `<li><b>Patch ${esc(ch.version)}</b> · ${esc(ch.date)} — ${esc(ch.note)}</li>`
  ).join('');
  box.style.display = list.length ? '' : 'none';
  box.open = list.length > 1;
}

function openDetail(slug) {
  const c = state.bySlug.get(slug);
  if (!c) { location.hash = '#/'; return; }
  state.current = c;
  state.showEn = false;
  toggleEn.setAttribute('aria-pressed', 'false');
  toggleEn.textContent = 'Bản gốc EN';
  const col = elColor(c.element);
  $('d-frame').style.setProperty('--tint-soft', col + '22');
  const img = $('d-img');
  img.src = c.img_full || c.img_card || c.img_icon;
  img.alt = c.name;
  img.onerror = () => { img.onerror = null; img.src = c.img_icon; };
  $('d-name').textContent = c.name;
  $('d-element').textContent = `${c.element} · ${elVi(c.element)}`;
  $('d-weapon').textContent = `${c.weapon} · ${weapVi(c.weapon)}`;
  $('d-version').textContent = `Patch ${state.meta.patch}`;
  $('d-tags').innerHTML =
    `<span class="tag el" style="background:${col}">${esc(c.element)} · ${esc(elVi(c.element))}</span>
     <span class="tag">${esc(c.weapon)} · ${esc(weapVi(c.weapon))}</span>
     <span class="tag" style="color:${c.rarity===5?'var(--r5)':'var(--r4)'}">${stars(c.rarity)}</span>`;
  $('d-stats').innerHTML = `
    <div class="stat"><div class="k">Nguyên tố</div><div class="v" style="color:${col}">${esc(c.element)}<small>${esc(elVi(c.element))}</small></div></div>
    <div class="stat"><div class="k">Vũ khí</div><div class="v">${esc(c.weapon)}<small>${esc(weapVi(c.weapon))}</small></div></div>
    <div class="stat"><div class="k">Độ hiếm</div><div class="v" style="color:${c.rarity===5?'var(--r5)':'var(--r4)'}">${c.rarity ? c.rarity + '★' : '—'}</div></div>
    <div class="stat"><div class="k">Kỹ năng</div><div class="v">${(c.skills || []).length}<small>mục chính</small></div></div>`;
  $('d-source').innerHTML = `Nguồn tham khảo: <a href="${esc(c.source)}" target="_blank" rel="noopener noreferrer">${esc(c.source)}</a>`;
  renderChanges(c);
  renderSkills();
  document.title = `${c.name} — Resonators Archive · Patch ${state.meta.patch}`;
  if (!state.detailOpen) state.savedScroll = window.scrollY;
  state.detailOpen = true;
  listView.style.display = 'none';
  detailView.classList.add('open');
  window.scrollTo({top: 0, behavior: 'instant'});
  backBtn.focus({preventScroll: true});
}

function closeDetail() {
  state.current = null;
  state.detailOpen = false;
  if (state.meta) document.title = `Wuthering Waves — Resonators Archive · Patch ${state.meta.patch}`;
  listView.style.display = '';
  detailView.classList.remove('open');
  window.scrollTo({top: state.savedScroll || 0, behavior: 'instant'});
}

function route() {
  const m = location.hash.match(/^#\/nhan-vat\/(.+)$/);
  if (m) openDetail(decodeURIComponent(m[1]));
  else closeDetail();
}

function openMechanic(termName) {
  const m = state.mechanics.find((x) => x.term === termName);
  if (!m) return;
  $('mech-kind').textContent = KIND_VI[m.kind] || 'Cơ chế';
  $('mech-title').textContent = m.term;
  $('mech-summary').textContent = m.summary_vi;
  const c = state.current;
  const occurrences = [];
  const seen = new Set();
  (c?.skills || []).forEach((s, i) => {
    for (const line of ((state.showEn ? s.desc : s.desc_vi) || [])) {
      if (!line.includes(m.term)) continue;
      const key = i + '|' + line;
      if (seen.has(key)) continue;
      seen.add(key);
      occurrences.push({skill: s.name, index: i, line});
      if (occurrences.length >= 8) break;
    }
  });
  const occBox = $('mech-occ-list');
  if (occurrences.length) {
    occBox.innerHTML = occurrences.map((o) =>
      `<button type="button" class="mech-occ-item" data-skill="${o.index}"><b>${esc(o.skill)}</b><br>${esc(o.line.slice(0, 210))}${o.line.length > 210 ? '…' : ''}</button>`
    ).join('');
  } else {
    occBox.innerHTML = `<p class="mech-occ-item" style="cursor:default">${esc(m.sample_vi || 'Không có trong bộ kỹ năng hiện tại.')}</p>`;
  }
  mechDialog.showModal();
}

async function boot() {
  try {
    const [charsRes, mechRes] = await Promise.all([
      fetch('/api/characters'),
      fetch('/api/mechanics'),
    ]);
    if (!charsRes.ok) throw new Error(`API /api/characters trả về ${charsRes.status}`);
    const chars = await charsRes.json();
    state.meta = chars.meta;
    state.characters = chars.characters;
    state.bySlug = new Map(state.characters.map((c) => [c.slug, c]));
    if (mechRes.ok) {
      const mech = await mechRes.json();
      state.mechanics = mech.mechanics || [];
    }
    loading.style.display = 'none';
    renderMeta();
    renderHero();
    fillSelect(fEl, [...new Set(state.characters.map((c) => c.element).filter(Boolean))].sort(), (v) => `${v} · ${EL_VI[v] || ''}`);
    fillSelect(fWeap, [...new Set(state.characters.map((c) => c.weapon).filter(Boolean))].sort(), (v) => `${v} · ${WEAP_VI[v] || ''}`);
    enhanceSelect(fEl, elDot);
    enhanceSelect(fWeap);
    enhanceSelect(fR, rarityMark);
    apply();
    route();
  } catch (err) {
    loading.style.display = 'none';
    errorBox.style.display = 'block';
    errorBox.innerHTML = `Không tải được dữ liệu từ API.<br><small>${esc(err.message)}. Hãy chạy <code>./run.sh</code> rồi mở <code>http://127.0.0.1:8000</code>.</small>`;
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
toggleEn.addEventListener('click', () => {
  state.showEn = !state.showEn;
  toggleEn.setAttribute('aria-pressed', String(state.showEn));
  toggleEn.textContent = state.showEn ? 'Đang xem EN' : 'Bản gốc EN';
  renderSkills();
});
[q, fEl, fWeap, fR].forEach((el) => el.addEventListener('input', apply));
window.addEventListener('hashchange', route);
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && state.current && !mechDialog.open) location.hash = '#/';
});

dSkills.addEventListener('click', (e) => {
  const skill = e.target.closest('[data-skill]');
  if (skill) { e.preventDefault(); scrollToSkill(Number(skill.dataset.skill)); return; }
  const mech = e.target.closest('[data-mech]');
  if (mech) { e.preventDefault(); openMechanic(mech.dataset.mech); }
});

$('mech-close').addEventListener('click', () => mechDialog.close());
mechDialog.addEventListener('click', (e) => {
  if (e.target === mechDialog) {
    const r = mechDialog.getBoundingClientRect();
    const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
    if (!inside) { mechDialog.close(); return; }
  }
  const occ = e.target.closest('.mech-occ-item[data-skill]');
  if (occ) {
    mechDialog.close();
    scrollToSkill(Number(occ.dataset.skill));
  }
});

boot();

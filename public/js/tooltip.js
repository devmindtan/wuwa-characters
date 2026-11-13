// Custom tooltip for every [title]/[data-tip] (fast, also inside the dialog).

/* Custom tooltip: replaces the slow native one for every [title]/[data-tip] on the page. */
export const tip = document.createElement('div');
tip.className = 'tip';
tip.setAttribute('role', 'tooltip');
tip.hidden = true;
document.body.appendChild(tip);
export let tipFor = null;      // element whose tooltip is shown
export let tipPending = null;  // element waiting for its tooltip
export let tipTimer = 0;
export function tipTarget(node) {
  const el = node?.closest?.('[data-tip], [title]');
  if (!el || el === document.documentElement) return null;
  if (el.hasAttribute('title')) {  // take the text over so the native tooltip never shows
    const text = el.getAttribute('title');
    el.removeAttribute('title');
    if (text) el.dataset.tip = text;
  }
  return el.dataset.tip ? el : null;
}
export function showTip(el) {
  tipFor = el;
  // inside a modal <dialog> the tooltip must live in the dialog's top layer
  const host = el.closest('dialog[open]') || document.body;
  if (tip.parentNode !== host) host.appendChild(tip);
  tip.textContent = el.dataset.tip;
  tip.hidden = false;
  tip.classList.remove('show');
  const r = el.getBoundingClientRect();
  const w = tip.offsetWidth, h = tip.offsetHeight, pad = 8;
  let top = r.top - h - 8;
  let below = false;
  if (top < pad) { top = r.bottom + 8; below = true; }
  const left = Math.min(Math.max(pad, r.left + r.width / 2 - w / 2), innerWidth - w - pad);
  tip.style.left = left + 'px';
  tip.style.top = top + 'px';
  tip.style.setProperty('--ax', (r.left + r.width / 2 - left) + 'px');
  tip.classList.toggle('below', below);
  requestAnimationFrame(() => tip.classList.add('show'));
}
export function hideTip() {
  clearTimeout(tipTimer);
  tipFor = null;
  tipPending = null;
  tip.classList.remove('show');
  tip.hidden = true;
}
document.addEventListener('pointerover', (e) => {
  if (e.pointerType === 'touch') return;
  const el = tipTarget(e.target);
  if (el && (el === tipFor || el === tipPending)) return;  // moving between children of the same target
  hideTip();
  if (el) {
    tipPending = el;
    tipTimer = setTimeout(() => { tipPending = null; showTip(el); }, 60);
  }
});
document.addEventListener('pointerout', (e) => {
  const cur = tipFor || tipPending;
  if (cur && !cur.contains(e.relatedTarget)) hideTip();
});
document.addEventListener('focusin', (e) => { const el = tipTarget(e.target); if (el && e.target.matches(':focus-visible')) showTip(el); });
document.addEventListener('focusout', hideTip);
document.addEventListener('pointerdown', hideTip);
addEventListener('scroll', hideTip, {capture: true, passive: true});
addEventListener('keydown', (e) => { if (e.key === 'Escape') hideTip(); });

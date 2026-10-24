// Shared stage for the Claude Code sample films. One paused GSAP timeline; typing, counters and the hero dot are
// evaluated from time alone in __seek, so any seek order renders the same frame. Every audible event is registered as a
// cue next to the constant that moves the picture, and every stretch of the film as a section named by its purpose
// (intro, tease, build, groove, light, muffled, breath, stop, end, riser) for engine/compose.py.
// Contract for engine/render.mjs and cues.mjs: __duration, __seek(t), __ready, __cues, __sections, __bpm, __T.
const BPM = window.BPM || 100, B = 60 / BPM, BAR = 4 * B, beat = (n) => n * B, bar = (n) => n * BAR;
const tl = gsap.timeline({ paused: true });
const CUES = [], SECTIONS = [], TYPERS = [], COUNTERS = [], DOT = [];
const cue = (t, type, o = {}) => (CUES.push({ t: Math.round(t * 1000) / 1000, type, ...o }), t);
const section = (t0, t1, kind, o = {}) => SECTIONS.push({ t0: Math.round(t0 * 1000) / 1000, t1: Math.round(t1 * 1000) / 1000, kind, ...o });
const $ = (q) => document.querySelector(q);
function el(tag, cls, parent, html) {
  const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html;
  (parent || $('#stage')).appendChild(e); return e;
}
function scene(t0, t1, cls = '') {
  const d = el('div', `scene ${cls}`); d.style.display = 'none';
  tl.set(d, { display: 'block' }, t0); if (t1 != null) tl.set(d, { display: 'none' }, t1); return d;
}
function show(n, t0, t1) { tl.set(n, { visibility: 'visible' }, t0); if (t1 != null) tl.set(n, { visibility: 'hidden' }, t1); }
// a cut-in with a 2-frame punch (Apple's type: no fades, no blur)
function pop(n, t0, s = 1.06, t1 = null) { show(n, t0, t1); tl.fromTo(n, { scale: s }, { scale: 1, duration: 0.067, ease: 'power2.out', immediateRender: false }, t0); }
// words as separate spans, so each can pop on its own beat
function words(parent, text, cls = '') {
  return text.split(' ').map((w) => { const s = el('span', `w ${cls}`, parent, w); parent.appendChild(document.createTextNode(' ')); return s; });
}
function popWords(spans, t0, gap, type = 'word') { spans.forEach((s, i) => { pop(s, t0 + i * gap, 1.05); cue(t0 + i * gap, type, { i }); }); }
// typed text: one key cue per character (typing is the one place dense sounds are fine)
function typeText(node, text, t0, cps = 24) {
  TYPERS.push({ node, text, t0, cps });
  for (let i = 0; i < text.length; i++) if (text[i] !== ' ') cue(t0 + i / cps, 'key', { i });
  return t0 + text.length / cps;
}
function counter(node, from, to, t0, t1, fmt = (v) => String(Math.round(v))) { COUNTERS.push({ node, from, to, t0, t1, fmt }); }
// the hero dot: keyed positions (functions, measured after layout); it flies 0.3 s into each key (power2.inOut)
const dotAt = (t, at, r = 12) => DOT.push({ t, at, r });
const dotHide = (t) => DOT.push({ t, hide: true });
function centerOf(q) { return () => { const r = (typeof q === 'string' ? $(q) : q).getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }; }
function measure(node) {   // a node's box even while its scene is hidden
  const sc = node.closest('.scene'); const was = sc && sc.style.display; if (sc) sc.style.display = 'block';
  const r = node.getBoundingClientRect(); if (sc) sc.style.display = was; return r;
}
function fixedPoint(q) { let p = null; return () => (p ||= (() => { const r = measure(typeof q === 'string' ? $(q) : q); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()); }
// a terminal card: lines appear (or are typed) at their times
function terminal(parent, x, y, w, h, title = '~/reference-motion-video') {
  const card = el('div', 'term', parent); Object.assign(card.style, { left: `${x}px`, top: `${y}px`, width: `${w}px`, height: `${h}px` });
  el('div', 'bar', card, `<i></i><i></i><i></i><span>${title}</span>`);
  const body = el('div', 'body', card);
  return { card, body, line(html, t, cls = '', type = null, o = {}) { const l = el('div', `ln ${cls}`, body, html); show(l, t); if (type) cue(t, type, o); return l; } };
}
function applyAll(t) {
  for (const k of TYPERS) { const n = Math.max(0, Math.min(k.text.length, Math.floor((t - k.t0) * k.cps + 1e-6) + 1)); const s = t < k.t0 ? '' : k.text.slice(0, n); if (k.node.dataset.s !== s) { k.node.textContent = s; k.node.dataset.s = s; } }
  for (const c of COUNTERS) { const k = Math.max(0, Math.min(1, (t - c.t0) / (c.t1 - c.t0))); const e = 1 - Math.pow(1 - k, 3); c.node.textContent = c.fmt(c.from + (c.to - c.from) * e); }
  const dot = $('#dot'); let i = -1; for (let k = 0; k < DOT.length; k++) if (DOT[k].t <= t) i = k;
  if (i < 0 || DOT[i].hide) { dot.style.visibility = 'hidden'; return; }
  const a = DOT[i], nx = DOT[i + 1], pa = a.at(); let d = { ...pa, r: a.r };
  if (nx && !nx.hide) { const fly = Math.min(0.3, nx.t - a.t), s0 = nx.t - fly; if (t >= s0) { const k = gsap.parseEase('power2.inOut')((t - s0) / fly), pb = nx.at(); d = { x: pa.x + (pb.x - pa.x) * k, y: pa.y + (pb.y - pa.y) * k, r: a.r + (nx.r - a.r) * k }; } }
  Object.assign(dot.style, { visibility: 'visible', left: `${d.x - d.r}px`, top: `${d.y - d.r}px`, width: `${2 * d.r}px`, height: `${2 * d.r}px` });
}
function finish(T, total) {
  DOT.sort((a, b) => a.t - b.t); CUES.sort((a, b) => a.t - b.t);
  tl.set({}, {}, total);
  window.__cues = CUES; window.__sections = SECTIONS; window.__bpm = BPM; window.__T = T;
  tl.seek(0); applyAll(0);
  window.__duration = total;
  window.__seek = async (t) => { tl.seek(t, false); applyAll(t); };
  window.__ready = true;
}

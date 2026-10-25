// Noto Sans KR is served in unicode-range slices, and text inside a hidden scene never triggers its slice. Load the
// slices for every character the film shows (typed text included) before telling the renderer it is ready.
function koStart(build) {
  document.fonts.load('800 150px Inter').then(() => document.fonts.load('500 30px "JetBrains Mono"')).then(() => {
    build(); window.__ready = false;
    const txt = $('#stage').textContent + TYPERS.map((k) => k.text).join('');
    return Promise.all(['500', '700', '800'].map((w) => document.fonts.load(`${w} 64px "Noto Sans KR"`, txt)));
  }).then(() => document.fonts.ready).then(() => { window.__ready = true; });
}

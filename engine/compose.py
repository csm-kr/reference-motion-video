"""A score composed to the picture: the film's own cue list is the score, and its sections say what the music does.

usage: python compose.py cues.json out.wav --palette bright_demo [--samples DIR] [--narr narr.js --narr-root DIR] [--stems DIR]

cues.json (cues.mjs dumps it from window.__duration / __T / __cues / __sections) holds `duration`, `bpm`, `cues` and
`sections`. A section names what the picture is doing, by purpose, so the same film works with any palette:
  intro    the problem, before the product acts: no rhythm, a pad and the cue sounds only
  tease    the product wakes up, the first ask: a sparse groove (no backbeat, no top percussion, no melody)
  build    the moment before a result lands: a crescendo into the section's end (also the fill before a re-entry)
  groove   the product at work; `e` is the energy (0.5-1.2)
  light    under a dense sentence or a card full of text: the groove without its melodic figure
  muffled  a serious fact, a statistic, a problem: the groove low-passed, opening into the next section
  breath   one beat of near silence before the payoff: only the hero object's sound may ring
  stop     the product deliberately does not act (a safety stop, a limit): drums out, a held pad
  end      the end card: silence
  riser    (overlay) a riser that ends on the section's end
Cue types every palette answers: drop (the payoff), reentry, final (the logo; then a dead stop), break (a stop begins),
cut, tap, tapTouch, pop, word, chip, node, num, count, fill, bar, key (typing), dot (the hero object's own sound).
Bars are counted from the first `drop` cue, so put the drop on a downbeat. Voices ('voice'/'narr' cues with a clip in
--narr) get the v4 voice-first mix. The sync gate runs on the master: a cue without an audible onset within 33 ms gets
the palette's emphasis sound and the mix is redone (twice at most); the report says what was added.
"""
import argparse
import importlib
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audio  # noqa: E402

audio.set_rate(48000)
from audio import Mix, OneShot, Sampler, band, sweep  # noqa: E402
import bedmix  # noqa: E402
from palettes import kit  # noqa: E402
from synccheck import check as sync_check  # noqa: E402

SR = 48000
SKIP_CUES = {'voice', 'narr', 'breath'}
GROOVE_BUSES = ('drums', 'perc', 'music', 'keys', 'pad', 'horns')


class Ctx:
    """What a palette sees: the mix, the beat grid from the drop, humanizing helpers, voice spans, and its samples."""

    def __init__(self, data, bpm, samples, spans):
        self.dur = data['duration']
        self.cues = sorted(data['cues'], key=lambda c: c['t'])
        self.T = data.get('T', {})
        self.m = Mix(self.dur, tail=3.0)
        self.bpm, self.beat = bpm, 60 / bpm
        self.step, self.bar = self.beat / 4, 4 * self.beat
        drops = [c['t'] for c in self.cues if c['type'] == 'drop']
        self.origin = drops[0] if drops else 0.0
        self.off = self.origin % self.bar
        self.samples = samples
        self.spans = spans
        self.rng = np.random.default_rng(7)

    # grid
    def steps(self, a, b):
        """16th-note slots in [a, b) on the drop-based grid: (time, slot in bar 0-15, bar index)."""
        s0, s1 = int(np.ceil((a - self.off) / self.step - 1e-6)), int(np.ceil((b - self.off) / self.step - 1e-6))
        return [(self.off + s * self.step, s % 16, s // 16) for s in range(s0, s1)]

    def bar_of(self, t):
        return int(np.floor((t - self.off) / self.bar + 1e-6))

    def after_drop(self, t):
        return t >= self.origin - 1e-6

    # humanizing (never on cue-locked hits)
    def hum(self, t, ms=8):
        return t + self.rng.uniform(-ms, ms) / 1000

    def vel(self, v, spread=0.1):
        return v * self.rng.uniform(1 - spread, 1 + spread)

    # voices
    def under_narr(self, t):
        return any(a - 0.1 <= t <= b + 0.1 for a, b, r in self.spans if r == 'narr')

    def under_voice(self, t):
        return any(a - 0.1 <= t <= b + 0.1 for a, b, _ in self.spans)

    # mix
    def add(self, bus, t, sig, gain=1.0, pan=0.0, send=0.0):
        self.m.add(bus, t, sig, gain, pan, send)

    def hit(self, bus, t, shot, gain=1.0, semis=0.0, pan=0.0, send=0.0):
        self.m.hit(bus, t, shot, gain, semis, pan, send)

    def duck(self, t, depth=1.0):
        self.m.duck(t, depth)

    # samples (None when missing, so a palette can fall back to synthesis)
    def path(self, rel):
        p = os.path.join(self.samples or '', rel)
        return p if self.samples and os.path.exists(p) else None

    def oneshot(self, rel, gain=1.0):
        p = self.path(rel)
        return OneShot(p, gain) if p else None

    def sampler(self, rel, **kw):
        p = self.path(rel)
        if not p:
            return None
        try:
            return Sampler(p, **kw)
        except FileNotFoundError:
            return None


def _smooth(g, ms=50):
    k = int(ms / 1000 * SR)
    return np.convolve(np.pad(g, (k, k), mode='edge'), np.ones(2 * k + 1) / (2 * k + 1), 'valid')[: len(g)]


def arrange(pal, ctx, sections):
    lows, gates, ends = [], [], []
    for s in sorted(sections, key=lambda s: (s['t0'], s['kind'] == 'riser')):
        k, a, b, e = s['kind'], s['t0'], s['t1'], s.get('e', 1.0)
        if k == 'intro':
            pal.intro(ctx, a, b)
        elif k == 'tease':
            pal.groove(ctx, a, b, 0.62 * e, back=False, hats=False, keys=False)
        elif k == 'build':
            pal.build(ctx, a, b)
        elif k == 'groove':
            pal.groove(ctx, a, b, e)
        elif k == 'light':
            pal.groove(ctx, a, b, 0.85 * e, keys=False)
        elif k == 'muffled':
            pal.groove(ctx, a, b, 0.7 * e, back=False, keys=False)
            lows.append((a, b))
        elif k == 'stop':
            pal.stop(ctx, a, b)
        elif k == 'breath':
            gates.append((a, b))
        elif k == 'end':
            ends.append((a, b))
        elif k == 'riser':
            pal.riser(ctx, a, b)
        else:
            raise ValueError(f'unknown section kind {k!r}')
    for c in ctx.cues:
        if c['type'] in SKIP_CUES or c['t'] >= ctx.dur:
            continue
        if not pal.cue(ctx, c):
            default_cue(ctx, c)
    return lows, gates, ends


def default_cue(ctx, c):
    """A cue type the palette does not answer still gets a sound on its frame."""
    t = c['t']
    if c['type'] == 'dot':
        ctx.add('dot', t, kit.water_drop(1046.5 if not ctx.after_drop(t) else 1396.9), send=0.35)
    elif c['type'] == 'key':
        ctx.add('hits', t, kit.key_tick(0.14), pan=0.1)
    else:
        ctx.add('hits', t, kit.snap(0.25), send=0.1)


def shape(ctx, lows, gates, ends):
    """Section effects. Muffled windows are low-passed on the groove buses (in place). Returns two gain curves: one for
    every bus and the room (breaths 40 dB down, end cards and the time after the final hit's tail silent) and one for the
    hero object's bus, which keeps ringing through a breath."""
    m = ctx.m
    for a, b in lows:
        i0, i1 = int((a - 0.05) * SR), int((b + 0.05) * SR)
        L = i1 - i0
        k = np.linspace(0, 1, L)
        hi = 1000 + 7000 * np.clip((k - 0.9) / 0.1, 0, 1) ** 2   # opens over the last 10%
        xf = np.ones(L); n = int(0.03 * SR); xf[:n] = 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n); xf[-n:] = xf[:n][::-1]
        for name in GROOVE_BUSES:
            if name in m.buses:
                for ch in range(2):
                    dry = m.buses[name][ch, i0:i1].copy()
                    m.buses[name][ch, i0:i1] = dry * (1 - xf) + sweep(dry, np.full(L, 20.0), hi) * 1.1 * xf
    g_end = np.ones(m.N)
    for a, _ in ends:
        g_end[int(a * SR):] = 0.0
    finals = [c['t'] for c in ctx.cues if c['type'] == 'final']
    if finals:   # the dead stop: the final hit's own tail, then nothing
        tf = finals[-1]
        stop_at = min([a for a, _ in ends if a > tf] + [tf + 2.4])
        e0, e1 = int((tf + 1.2) * SR), int(stop_at * SR)
        if e1 > e0:
            g_end[e0:e1] = np.minimum(g_end[e0:e1], np.linspace(1, 0, e1 - e0) ** 2)
        g_end[e1:] = 0.0
    g = g_end.copy()
    for a, b in gates:   # the breath: 40 dB down with 50 ms edges
        g[int((a + 0.05) * SR):int((b - 0.04) * SR)] = 0.01
    return _smooth(g), _smooth(g_end)


def mixdown(ctx, g, g_dot, wet=0.3):
    """Buses to (bed, hits) stereo at the film length: the section gains, a seeded room (the same on every render, and
    gated with the buses so no tail rings through a breath or the end card) and the kick sidechain."""
    m = ctx.m
    N = m.N
    irng = np.random.default_rng(2026)
    L = int(1.6 * SR)
    ti = np.arange(L) / SR
    irs = []
    for _ in range(2):
        ir = irng.standard_normal(L) * np.exp(-ti / (1.6 / 4.5)); ir = band(ir, 180, 7500); ir[: int(0.022 * SR)] = 0
        irs.append(ir / np.sqrt((ir ** 2).sum()))
    size = 1 << int(np.ceil(np.log2(N + L)))
    room = np.stack([np.fft.irfft(np.fft.rfft(m.verb[ch], size) * np.fft.rfft(irs[ch], size), size)[:N] for ch in range(2)]) * wet * g
    kd = 1 - 0.15 * m.duck_src
    bed = room.copy()
    for name, bus in m.buses.items():
        if name in ('hits', 'voice'):
            continue
        f = (1 - 0.5 * m.duck_src) if name == 'pad' else kd if name in ('music', 'perc', 'keys', 'horns') else 1.0
        bed = bed + bus * f * (g_dot if name == 'dot' else g)
    n = int(round(ctx.dur * SR))
    hits = (m.buses['hits'] * g)[:, :n] if 'hits' in m.buses else np.zeros((2, n))
    return bed[:, :n], hits


def voice_mix(bed, hits, v, spans, dur):
    """The v4 voice-first rules (bedmix): floors -14/-10 dB, deeper until the voice is 8.5 dB over bed + hits, 1.5-5 kHz carve."""
    if not spans:
        return bed + hits, {}
    extra = {}
    vm = v.mean(0) if v.ndim == 2 else v   # the measurement wants mono; v arrives as the stereo voice bus
    for _ in range(3):
        g = bedmix.duck_gain(spans, dur, extra=extra)
        over = bedmix.voice_over_bed(vm, (bedmix.carve(bed * g, spans) + np.sqrt(g) * hits).mean(0), spans)
        short = {i: o - 9.0 for i, o in enumerate(over) if o < 8.5}
        if not short:
            break
        for i, s in short.items():
            extra[i] = extra.get(i, 0.0) + s
    return bedmix.carve(bed * g, spans) + np.sqrt(g) * hits + v, extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cues'); ap.add_argument('out'); ap.add_argument('--palette', required=True)
    ap.add_argument('--samples', default=os.path.join(HERE, '..', 'samples'))
    ap.add_argument('--narr'); ap.add_argument('--narr-root', default='.'); ap.add_argument('--stems'); ap.add_argument('--bpm', type=float)
    a = ap.parse_args()
    data = json.load(open(a.cues))
    pal = importlib.import_module(f'palettes.{a.palette}')
    bpm = a.bpm or data.get('bpm') or pal.BPM
    dur = data['duration']
    v, spans = np.zeros(int(round(dur * SR))), []
    if a.narr:
        narr = json.loads(open(a.narr).read().split('=', 1)[1].strip().rstrip(';'))
        v, spans = bedmix.voices(data['cues'], narr, a.narr_root, dur)
    ctx = Ctx(data, bpm, os.path.abspath(a.samples) if a.samples else None, spans)
    pal.setup(ctx)
    lows, gates, ends = arrange(pal, ctx, data.get('sections', []))
    added = []
    raw = {k: b.copy() for k, b in ctx.m.buses.items()}   # the arrangement before any section effect
    for attempt in range(3):
        ctx.m.buses = {k: b.copy() for k, b in raw.items()}
        g, g_dot = shape(ctx, lows, gates, ends)
        bed, hits = mixdown(ctx, g, g_dot)
        mix, extra = voice_mix(bed, hits, np.stack([v, v]), spans, dur)
        bedmix.master(mix, a.out)
        y = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', a.out, '-ac', '1', '-ar', '22050', '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)
        sync = sync_check(y, data['cues'], to=dur - 0.3)
        miss = [r for r in sync['rows'] if not r['ok']]
        if not miss or attempt == 2:
            break
        ctx.m.buses = raw   # the palette's emphasis goes into the raw arrangement, then shape and mix again
        for r in miss:
            if r['type'] == 'key':   # a typed key gets a louder key, never a clap (claps on typing sounded wrong in sample 3)
                ctx.add('hits', r['t'], kit.key_tick(0.14 * 1.6 ** (attempt + 1)), pan=0.1)
            else:
                pal.emphasis(ctx, r['t'], attempt + 1)
            added.append({'t': r['t'], 'type': r['type'], 'level': attempt + 1})
        raw = ctx.m.buses
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        bedmix._write(np.stack([v, v]), os.path.join(a.stems, 'voice.wav')); bedmix._write(mix - np.stack([v, v]), os.path.join(a.stems, 'bed.wav'))
    i, tp = bedmix.lufs_tp(a.out)
    print(json.dumps({'out': a.out, 'palette': a.palette, 'bpm': bpm, 'lufs': i, 'true_peak': tp,
                      'sync': {k: sync[k] for k in ('n', 'miss', 'chance')}, 'misses': [(r['t'], r['type'], r['dt_ms']) for r in miss],
                      'emphasis_added': added, 'extra_duck_db': {k: round(x, 1) for k, x in extra.items()}}))


if __name__ == '__main__':
    main()

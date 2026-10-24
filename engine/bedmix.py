"""Music path 1: a licensed library track as the bed, on the film's beat grid, under the voices, with a cue-locked hit layer.

usage: python bedmix.py --cues cues.json --narr narr.js --track track.mp3 --map beats.json --film-bpm 100
                        --anchor <track downbeat s> --at <film s> [--mute a,b ...] [--lowpass a,b,hz ...] [--to s] --out mix.wav
The track is time-stretched by film BPM / track BPM (rubberband, pitch kept; keep it within about 3%), then placed so that
one of its downbeats (`--anchor`, original track seconds, e.g. the first downbeat of its loudest section from beatmap.py)
lands on a film downbeat (`--at`, e.g. the title drop). Every later beat then sits on the film grid.
Mix (the v4 voice-first rules): voices at -17 dBFS speech RMS, no reverb; the bed at least 14 dB down under narration and
10 dB under other voices, deeper if the voice is not 8.5 dB over it; 1.5-5 kHz carved 7 dB under every voice; hits on their
own bus, ducked half as much; -14 LUFS integrated, true peak under -1 dBTP.
"""
import argparse
import json
import os
import re
import subprocess

import numpy as np
from scipy.signal import butter, sosfiltfilt

SR = 48000


def load(path, ch=2, af=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', path] + (['-af', af] if af else []) + ['-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-']
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()
    return x.reshape(-1, ch).T if ch > 1 else x


def stretch(path, ratio):
    """The track at ratio x its tempo, pitch kept (rubberband)."""
    return load(path, 2, f'rubberband=tempo={ratio:.6f}:pitch=1:transients=crisp:detector=percussive')


def _ramp_gain(n, windows, ramp=0.02, floor=0.0):
    g = np.ones(n, np.float32)
    k = int(ramp * SR)
    r = 0.5 + 0.5 * np.cos(np.pi * np.arange(k) / k)   # 1 -> 0
    for a, b in windows:
        i0, i1 = int(a * SR), int(b * SR)
        g[i0:i1] = floor
        g[i0:min(n, i0 + k)] = floor + (1 - floor) * r[: max(0, min(n, i0 + k) - i0)]
        g[max(0, i1 - k):i1] = floor + (1 - floor) * r[::-1][k - (i1 - max(0, i1 - k)):]
    return g


def place(track, ratio, anchor_src, anchor_film, dur, mutes=(), lowpass=()):
    """Film-timeline bed from an already-stretched track (mono or [ch, n]): the original track time anchor_src lands on
    film time anchor_film. mutes: [(a, b)] silent with 20 ms ramps inside the window. lowpass: [(a, b, hz)] low-passed
    from a to b, opening to the dry track over the last 0.6 s."""
    x = np.atleast_2d(np.asarray(track, np.float32))
    n = int(round(dur * SR))
    s0 = int(round((anchor_src / ratio - anchor_film) * SR))   # stretched-file sample at film time 0
    out = np.zeros((x.shape[0], n), np.float32)
    a, b = max(0, -s0), min(n, x.shape[1] - s0)
    if b > a:
        out[:, a:b] = x[:, s0 + a:s0 + b]
    for a_, b_, hz in lowpass:
        lp = sosfiltfilt(butter(4, hz, 'lowpass', fs=SR, output='sos'), out, axis=1).astype(np.float32)
        w = np.zeros(n, np.float32)
        i0, i1, k = int(a_ * SR), int(b_ * SR), int(0.6 * SR)
        w[i0:i1] = 1
        w[max(i0, i1 - k):i1] = np.linspace(1, 0, i1 - max(i0, i1 - k))
        out = out * (1 - w) + lp * w
    if mutes:
        out *= _ramp_gain(n, mutes)
    return out[0] if np.ndim(track) == 1 else out


def duck_gain(spans, dur, narr_db=-14.0, voice_db=-10.0, extra=None, pre=0.08, post=0.12, smooth=0.06):
    """Bed gain at SR: narr_db under narration spans, voice_db under other voices (extra[i] dB more for span i), 60 ms
    smoothing; the spans are (start, end, role)."""
    n = int(round(dur * SR))
    g = np.ones(n)
    for i, (a, b, role) in enumerate(spans):
        d = (narr_db if role == 'narr' else voice_db) + (extra or {}).get(i, 0.0)
        i0, i1 = max(0, int((a - pre) * SR)), min(n, int((b + post) * SR))
        g[i0:i1] = np.minimum(g[i0:i1], 10 ** (d / 20))
    k = int(smooth * SR)
    g = np.convolve(np.pad(g, (k, k), mode='edge'), np.ones(2 * k + 1) / (2 * k + 1), 'valid')[:n]
    # smoothing must not make a span shallower than asked: re-apply the floor inside each span's core
    for i, (a, b, role) in enumerate(spans):
        d = (narr_db if role == 'narr' else voice_db) + (extra or {}).get(i, 0.0)
        i0, i1 = max(0, int(a * SR)), min(n, int(b * SR))
        g[i0:i1] = np.minimum(g[i0:i1], 10 ** (d / 20))
    return g


def carve(bed, spans, db=-7.0, lo=1500, hi=5000):
    """While any voice plays, the bed's speech band is cut by db (split band, zero phase)."""
    n = bed.shape[-1]
    gate = np.zeros(n)
    for a, b, _ in spans:
        gate[max(0, int((a - 0.08) * SR)):int((b + 0.12) * SR)] = 1.0
    k = int(0.05 * SR)
    gate = np.convolve(np.pad(gate, (k, k), mode='edge'), np.ones(2 * k + 1) / (2 * k + 1), 'valid')[:n]
    mid = sosfiltfilt(butter(4, [lo, hi], 'bandpass', fs=SR, output='sos'), bed, axis=-1)
    return bed - (1 - 10 ** (db / 20)) * mid * gate


# ---------------------------------------------------------------- the hit layer: one short sound per cue, on its frame
def _t(sec):
    return np.arange(int(sec * SR)) / SR


def _env(t, a=0.001, d=0.08):
    return (1 - np.exp(-t / a)) * np.exp(-t / d)


def tick(f=3200, v=0.12, d=0.018):
    t = _t(0.08)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2.01 * f * t)) * _env(t, 0.0005, d) * v


def thump(v=0.5, f0=95, f1=45, d=0.16):
    t = _t(0.4)
    f = f1 + (f0 - f1) * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(t, 0.001, d) * v


def mallet(midi, v=0.18, d=0.35):
    f = 440 * 2 ** ((midi - 69) / 12)
    t = _t(d + 0.1)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t / (d * 0.45)) + 0.35 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t / 0.03)) * (1 - np.exp(-t / 0.0015)) * v


def snap(v=0.3, f=1900, d=0.025):
    """A finger-snap: a 1.8-7 kHz noise burst plus a short ping. A low thump alone was masked by the track's bass on
    off-beat cuts (synccheck missed 2 of 8 cuts in the first test mix)."""
    rng = np.random.default_rng(int(f))
    t = _t(0.12)
    noise = sosfiltfilt(butter(2, [1800, 7000], 'bandpass', fs=SR, output='sos'), rng.standard_normal(len(t)))
    return (noise / (np.abs(noise).max() + 1e-9) + 0.4 * np.sin(2 * np.pi * f * t)) * _env(t, 0.0008, d) * v


def water_drop(f0=880.0, v=0.22):
    t = _t(0.35)
    f = f0 * (1 + 0.55 * (1 - np.exp(-t / 0.014)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t / 0.085) + 0.25 * np.sin(2 * ph) * np.exp(-t / 0.04)) * (1 - np.exp(-t / 0.0015)) * v


def boom(v=0.8):
    rng = np.random.default_rng(7)
    t = _t(1.6)
    f = 32 + 58 * np.exp(-t / 0.12)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(t, 0.002, 0.55)
    air = sosfiltfilt(butter(2, [3000, 12000], 'bandpass', fs=SR, output='sos'), rng.standard_normal(len(t))) * np.exp(-t / 0.35) * 0.25
    return (body + air) * v


def layer(*sounds):
    out = np.zeros(max(len(s) for s in sounds))
    for s in sounds:
        out[:len(s)] += s
    return out


KIT = {   # cue type -> sound; a type not listed gets no sound (its frame is carried by the track's own beat)
    'tapTouch': lambda c: tick(2600 + 40 * (c.get('i', 0) % 6), 0.10),
    'tapTalk': lambda c: layer(tick(3400, 0.16), thump(0.18, 140, 70, 0.05)),
    'tapSoft': lambda c: tick(3000, 0.08),
    'cut': lambda c: layer(thump(0.55 if c.get('big') else 0.4), snap(0.34 if c.get('big') else 0.26)),
    'count': lambda c: mallet([72, 74, 76, 79, 81][c.get('n', 0) % 5] + 12),
    'dot': lambda c: water_drop(),
    'drop': lambda c: boom(),
    'pop': lambda c: layer(snap(0.18, 2400, 0.018), tick(4200, 0.08, 0.012)),
    'word': lambda c: layer(snap(0.18, 2400, 0.018), tick(4200, 0.08, 0.012)),
    'chip': lambda c: mallet(84, 0.10, 0.25),
    'node': lambda c: mallet(79, 0.10, 0.25),
    'num': lambda c: layer(thump(0.35), mallet(84, 0.12)),
    'fill': lambda c: mallet(88, 0.12, 0.3),
    'bar': lambda c: thump(0.25, 120, 60, 0.12),
    'final': lambda c: boom(0.9),
}


def hit_layer(cues, dur):
    out = np.zeros(int(round(dur * SR)) + SR)
    counts = {}
    for c in sorted(cues, key=lambda c: c['t']):
        f = KIT.get(c['type'])
        if not f or c['t'] >= dur:
            continue
        c = dict(c, n=counts.get(c['type'], 0)); counts[c['type']] = c['n'] + 1
        s = f(c)
        i = int(round(c['t'] * SR))
        out[i:i + len(s)] += s[: len(out) - i]
    return out[: int(round(dur * SR))]


# ---------------------------------------------------------------- loudness
def lufs_tp(path):
    s = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', s)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', s)[-1])


def _write(x, path, codec='pcm_f32le'):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', str(x.shape[0]), '-i', '-', '-c:a', codec, path],
                   input=np.ascontiguousarray(x.T, np.float32).tobytes(), check=True)


def master(mix, out, target=-14.0):
    """Linear gain to the target LUFS and a limiter run at 192 kHz (true peak), back to 48 kHz; repeated until on target."""
    mix = np.atleast_2d(mix).astype(np.float64)
    mix = sosfiltfilt(butter(2, 28, 'highpass', fs=SR, output='sos'), mix, axis=1)
    mix /= np.abs(mix).max() / 0.7
    raw = out + '.raw.wav'
    _write(mix, raw)
    gain = target - lufs_tp(raw)[0]
    for _ in range(4):
        af = (f'volume={gain:.3f}dB,aresample=192000:resampler=soxr:precision=28,alimiter=limit={10 ** (-2.0 / 20):.4f}'
              ':attack=3:release=80:level=disabled,aresample=48000:resampler=soxr:precision=28')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', af, '-c:a', 'pcm_s24le', out], check=True)
        i, _ = lufs_tp(out)
        if abs(i - target) < 0.1:
            break
        gain += target - i
    os.remove(raw)


# ---------------------------------------------------------------- the film mix
def voices(cues, narr, root, dur):
    """Every 'voice' / 'narr' cue's clip at its cue time, at -17 dBFS speech RMS (mono), and the spans it covers."""
    v = np.zeros(int(round(dur * SR)) + 20 * SR)
    spans = []
    for c in cues:
        if c['type'] not in ('voice', 'narr') or c['t'] >= dur:
            continue
        n = narr[c['id']]
        y = load(os.path.join(root, n['file']), 1, 'aresample=resampler=soxr:precision=28')
        sp = y[np.abs(y) > 0.01]
        y = y / (np.sqrt(np.mean(sp ** 2)) + 1e-9) * 10 ** (-17 / 20)
        i = int(round(c['t'] * SR))
        v[i:i + len(y)] += y
        spans.append((c['t'], c['t'] + len(y) / SR, n.get('role', 'voice')))
    return v[: int(round(dur * SR))], spans


def rms_db(x):
    x = x[np.abs(x) > 1e-4]
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12) if len(x) else -120.0


def voice_over_bed(v, bed, spans):
    """Per span: speech RMS minus bed RMS in dB, both measured only where the voice is active (1% of its peak)."""
    out = []
    for a, b, _ in spans:
        vs, bs = v[int(a * SR):int(b * SR)], bed[int(a * SR):int(b * SR)]
        act = np.abs(vs) > 0.01 * (np.abs(vs).max() + 1e-12)
        out.append(rms_db(vs[act]) - rms_db(bs[act]) if act.any() else 99.0)
    return out


def grid_offset(bed, film_bpm, at, beats_fn):
    """Median offset (s) of the bed's own beats from the film grid at + k * 60 / film_bpm, measured with beatmap."""
    y = np.atleast_2d(bed).mean(0)
    y22 = y[::2] if SR == 44100 else np.interp(np.arange(0, len(y), SR / 22050), np.arange(len(y)), y).astype(np.float32)
    b = np.array(beats_fn(y22))
    if not len(b):
        return 0.0
    P = 60 / film_bpm
    return float(np.median(b - (at + np.round((b - at) / P) * P)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cues', required=True); ap.add_argument('--narr', required=True); ap.add_argument('--narr-root', default='.')
    ap.add_argument('--track', required=True); ap.add_argument('--map', required=True); ap.add_argument('--film-bpm', type=float, required=True)
    ap.add_argument('--anchor', type=float, required=True); ap.add_argument('--at', type=float, required=True)
    ap.add_argument('--mute', action='append', default=[]); ap.add_argument('--lowpass', action='append', default=[])
    ap.add_argument('--bed-db', type=float, default=-19.0, help='bed RMS before ducking (voices sit at -17)')
    ap.add_argument('--carve-lo', type=float, default=1500, help='lowest Hz of the speech band cut under voices')
    ap.add_argument('--to', type=float); ap.add_argument('--out', required=True); ap.add_argument('--stems')
    a = ap.parse_args()
    d = json.load(open(a.cues))
    narr = json.loads(open(a.narr).read().split('=', 1)[1].strip().rstrip(';'))
    bm = json.load(open(a.map))
    dur = a.to or d['duration']
    ratio = a.film_bpm / bm['bpm']
    st = stretch(a.track, ratio)
    mutes, lps = [tuple(map(float, m.split(','))) for m in a.mute], [tuple(map(float, m.split(','))) for m in a.lowpass]
    # the stretch shifts the track by a few ms (rubberband latency: 8.6 ms in the first test); measure the placed bed's own
    # beats against the film grid and move the anchor by that offset
    from beatmap import beatmap
    off = grid_offset(place(st, ratio, a.anchor, a.at, dur), a.film_bpm, a.at, lambda y: beatmap(y, 22050)['beats'])
    anchor = a.anchor + off * ratio
    bed = place(st, ratio, anchor, a.at, dur, mutes=mutes, lowpass=lps)
    off_after = grid_offset(place(st, ratio, anchor, a.at, dur), a.film_bpm, a.at, lambda y: beatmap(y, 22050)['beats'])
    bed *= 10 ** ((a.bed_db - rms_db(bed.mean(0))) / 20)
    v, spans = voices(d['cues'], narr, a.narr_root, dur)
    hits = hit_layer(d['cues'], dur)
    # each span starts at its role's floor (-14 narration, -10 others) and goes deeper until the voice sits 8.5 dB over the
    # carved, ducked bed, measured where the voice is active (the first test left N1 at 7.6 dB over the track's drop)
    extra = {}
    for _ in range(3):
        g = duck_gain(spans, dur, extra=extra)
        over = voice_over_bed(v, (carve(bed * g, spans, lo=a.carve_lo) + np.sqrt(g) * hits).mean(0), spans)   # the hits count as bed
        short = {i: o - 9.0 for i, o in enumerate(over) if o < 8.5}
        if not short:
            break
        for i, s in short.items():
            extra[i] = extra.get(i, 0.0) + s
    bed = carve(bed * g, spans, lo=a.carve_lo)
    mix = bed + np.sqrt(g) * hits + v
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        _write(np.stack([v, v]), os.path.join(a.stems, 'voice.wav')); _write(bed + np.sqrt(g) * hits, os.path.join(a.stems, 'bed.wav'))
    fo = int(0.4 * SR); mix[:, -fo:] *= np.linspace(1, 0, fo) ** 2
    master(mix, a.out)
    i, tp = lufs_tp(a.out)
    print(json.dumps({'out': a.out, 'ratio': round(ratio, 5), 'lufs': i, 'true_peak': tp, 'grid_offset_ms': [round(off * 1000, 1), round(off_after * 1000, 1)],
                      'voice_over_bed_db': [round(o, 1) for o in voice_over_bed(v, (bed + np.sqrt(g) * hits).mean(0), spans)],
                      'spans': [(round(s, 2), round(e, 2), r) for s, e, r in spans], 'extra_duck_db': {k: round(x, 1) for k, x in extra.items()}}))


if __name__ == '__main__':
    main()

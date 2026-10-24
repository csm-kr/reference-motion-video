"""Beat map of a steady-tempo track: tempo, beat times, downbeats and energy sections (numpy only).

usage: python beatmap.py track.mp3 [--clicks check.wav] > beats.json
Library tracks are produced on a fixed grid, so the beats are fit as one line, t = phase + k * period, through the attack
of each beat (well under 5 ms on a quantized track). `fit_residual_ms` says how well the line fits; above about 10 ms
the track drifts (played live) and needs a beat tracker instead. `--clicks` writes the track with a high click on every
downbeat and a low one on every other beat: listen to it once before trusting the map.
"""
import json
import subprocess
import sys

import numpy as np

SR = 22050
NFFT, HOP = 512, 64            # onset frames: 23 ms window, 2.9 ms hop
CNFFT, CHOP = 4096, 1024       # chroma frames: enough pitch resolution for chords


def load(path, sr=SR):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def _mag(y, n, hop):
    fr = np.lib.stride_tricks.sliding_window_view(np.pad(y, (0, n)), n)[::hop]
    return np.abs(np.fft.rfft(fr * np.hanning(n).astype(np.float32), axis=1)).astype(np.float32)


def _flux(S, band):
    L = np.log1p(10 * S[:, band])
    return np.concatenate([[0.0], np.maximum(0, np.diff(L, axis=0)).sum(1)])


def _tempo(env, fps):
    e = env - np.convolve(env, np.ones(int(fps / 2)) / int(fps / 2), 'same')
    e = np.maximum(e, 0); e /= e.std() + 1e-9
    n = 1 << int(np.ceil(np.log2(2 * len(e))))
    ac = np.fft.irfft(np.abs(np.fft.rfft(e, n)) ** 2)[: len(e)]
    ac /= ac[0]
    bpms = np.arange(60, 200, 0.05)
    lag = 60 / bpms * fps
    at = lambda L: np.interp(L, np.arange(len(ac)), ac)  # noqa: E731
    prior = np.exp(-0.5 * (np.log2(bpms / 115) / 0.6) ** 2)   # resolves half and double tempo towards 80-150 BPM
    score = (at(lag) + 0.5 * at(2 * lag)) * prior
    return float(bpms[np.argmax(score)])


def _attack(y, sr, t, win=0.025):
    """Where the energy (1 ms smoothing) last crosses 20% of its rise before the loudest point within +-win of t, and the
    size of that rise. The steepest-rise point sat 4-5 ms late on a kick, whose energy builds over its first cycle."""
    i0, i1 = max(0, int((t - win) * sr)), min(len(y), int((t + win) * sr))
    if i1 - i0 < 8:
        return t, 0.0
    k = max(2, int(0.001 * sr))
    e = np.convolve(y[i0:i1].astype(np.float64) ** 2, np.ones(k) / k, 'same')
    j = int(np.argmax(e))
    pre = float(np.median(e[: max(1, j // 3)]))
    below = np.flatnonzero(e[: j + 1] < pre + 0.2 * (e[j] - pre))
    return (i0 + (below[-1] + 1 if len(below) else 0)) / sr, float(e[j] - pre)


def _grid(y, sr, env, fps, t_off, bpm):
    period = 60 / bpm * fps
    phases = np.arange(0, period, 0.25)
    ks = np.arange(int((len(env) - period) / period))
    comb = [np.interp(p + ks * period, np.arange(len(env)), env).sum() for p in phases]
    t0 = phases[int(np.argmax(comb))] / fps + t_off
    P = 60 / bpm
    dur = len(y) / sr
    k = np.arange(int(np.ceil(-t0 / P)), int((dur - t0) / P) + 1)
    # the line is fit through the onset-envelope peak nearest each grid beat (one consistent detector for every beat;
    # the waveform-energy attack wandered by 12-15 ms in dense mixes, where the loudest thing near a beat is not a drum)
    tt, w = np.zeros(len(k)), np.zeros(len(k))
    r = max(1, int(0.03 * fps))
    for j, kk in enumerate(k):
        c = int(round((t0 + kk * P - t_off) * fps))
        a, b = max(1, c - r), min(len(env) - 1, c + r)
        if b - a < 3:
            continue
        i = a + int(np.argmax(env[a:b]))
        y0, y1, y2 = env[i - 1], env[i], env[min(len(env) - 1, i + 1)]
        dd = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) < 0 else 0.0
        tt[j], w[j] = (i + dd) / fps + t_off, y1
    keep = w > 0.3 * np.median(w[w > 0])
    for _ in range(4):   # robust line fit: drop beats whose onset sits off the line
        A = np.stack([np.ones(keep.sum()), k[keep]], 1)
        (ph, P), *_ = np.linalg.lstsq(A, tt[keep], rcond=None)
        res = tt - (ph + P * k)
        mad = np.median(np.abs(res[keep])) + 1e-6
        keep = keep & (np.abs(res) < max(0.004, 4 * mad))
    # the envelope peak sits a few ms off the audible attack; move the whole line by the median attack offset
    att = np.array([_attack(y, sr, ph + P * kk)[0] for kk in k[keep]])
    ph += float(np.median(att - (ph + P * k[keep])))
    beats = ph + P * k
    a0, a1 = _active(y, sr)   # no beats in leading or trailing silence
    beats = beats[(beats >= max(0.0, a0 - P / 2)) & (beats < min(dur, a1 - P / 4))]   # a beat needs a quarter beat of sound after it
    return beats, float(P), float(np.sqrt(np.mean(res[keep] ** 2)) * 1000), tt, w


def _active(y, sr, floor_db=45):
    """First and last time the 50 ms RMS is within floor_db of the track's loudest window."""
    n = int(0.05 * sr)
    r = np.sqrt(np.mean(y[: len(y) // n * n].astype(np.float64).reshape(-1, n) ** 2, axis=1))
    db = 20 * np.log10(r + 1e-12)
    on = np.flatnonzero(db > db.max() - floor_db)
    return on[0] * n / sr, (on[-1] + 1) * n / sr


def _chroma(y, sr, beats):
    S = _mag(y, CNFFT, CHOP)
    f = np.fft.rfftfreq(CNFFT, 1 / sr)
    sel = (f > 65) & (f < 2000)
    pc = np.round(12 * np.log2(f[sel] / 261.63)).astype(int) % 12
    C = np.zeros((len(S), 12), np.float32)
    for p in range(12):
        C[:, p] = S[:, sel][:, pc == p].sum(1)
    tc = (np.arange(len(S)) * CHOP + CNFFT / 2) / sr
    edges = np.append(beats, beats[-1] + np.median(np.diff(beats)))
    out = np.zeros((len(beats), 12))
    for i in range(len(beats)):
        m = (tc >= edges[i]) & (tc < edges[i + 1])
        out[i] = C[m].mean(0) if m.any() else 0
    return out / (np.linalg.norm(out, axis=1, keepdims=True) + 1e-9)


def _downbeat_phase(y, sr, beats, low_env, fps, t_off):
    ch = _chroma(y, sr, beats)
    nov = np.concatenate([[0.0], 1 - (ch[1:] * ch[:-1]).sum(1)])
    idx = np.clip(np.round((beats - t_off) * fps).astype(int), 0, len(low_env) - 1)
    w = int(0.03 * fps)
    low = np.array([low_env[max(0, i - w):i + w + 1].max() for i in idx])
    s = [nov[m::4].mean() / (nov.mean() + 1e-9) + low[m::4].mean() / (low.mean() + 1e-9) for m in range(4)]
    return int(np.argmax(s))


def _sections(y, sr, downbeats, min_bars=4):
    S = _mag(y, NFFT, HOP * 8)
    tf = (np.arange(len(S)) * HOP * 8 + NFFT / 2) / sr
    f = np.fft.rfftfreq(NFFT, 1 / sr)
    bands = np.geomspace(40, sr / 2, 9)
    bars = []
    for i in range(len(downbeats)):
        a = downbeats[i]; b = downbeats[i + 1] if i + 1 < len(downbeats) else a + np.median(np.diff(downbeats))
        m = (tf >= a) & (tf < b)
        seg = y[int(a * sr):int(b * sr)]
        rms = 20 * np.log10(np.sqrt(np.mean(seg.astype(np.float64) ** 2)) + 1e-9) if len(seg) else -120.0
        be = [10 * np.log10((S[m][:, (f >= lo) & (f < hi)] ** 2).sum() / max(1, m.sum()) + 1e-12) for lo, hi in zip(bands[:-1], bands[1:])]
        bars.append([rms] + be)
    F = np.array(bars)
    F = F - F.mean(0)
    nb = len(F)
    B = min_bars
    d = np.zeros(nb)
    for b in range(1, nb):
        lo, hi = F[max(0, b - B):b], F[b:min(nb, b + B)]
        if len(lo) and len(hi):
            d[b] = np.linalg.norm(hi.mean(0) - lo.mean(0)) / np.sqrt(F.shape[1])
    # a section starts at a local peak of the block change that moves the bar features by >= 3 dB on average; a
    # spread-based threshold failed, because a change ramps the score up over the min_bars bars on either side
    peaks = [b for b in range(1, nb) if d[b] >= 3.0 and d[b] >= d[b - 1] and (b + 1 == nb or d[b] >= d[b + 1])]
    starts = [0]
    for b in sorted(peaks, key=lambda b: -d[b]):
        if all(abs(b - s) >= min_bars for s in starts):
            starts.append(int(b))
    starts.sort()
    out = []
    for j, s in enumerate(starts):
        e = starts[j + 1] if j + 1 < len(starts) else nb
        out.append({'t': round(float(downbeats[s]), 4), 'bar': s, 'bars': e - s, 'energy': round(float(np.mean([r[0] for r in bars[s:e]])), 1)})
    return out, [round(float(r[0]), 1) for r in bars]


def beatmap(y, sr=SR):
    y = np.asarray(y, np.float32)
    S = _mag(y, NFFT, HOP)
    f = np.fft.rfftfreq(NFFT, 1 / sr)
    fps = sr / HOP
    t_off = NFFT / 2 / sr
    env = _flux(S, slice(None))
    low_env = _flux(S, f < 150)
    bpm0 = _tempo(env, fps)
    beats, P, resid, _, _ = _grid(y, sr, env, fps, t_off, bpm0)
    m = _downbeat_phase(y, sr, beats, low_env, fps, t_off)
    downbeats = beats[m::4]
    sections, bar_energy = _sections(y, sr, downbeats)
    return {'bpm': round(60 / P, 3), 'period': round(P, 6), 'beats': [round(float(b), 4) for b in beats], 'downbeats': [round(float(b), 4) for b in downbeats],
            'sections': sections, 'bar_energy': bar_energy, 'fit_residual_ms': round(resid, 2), 'duration': round(len(y) / sr, 3)}


def click_check(path, m, out):
    sr = 44100
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy() * 0.6
    t = np.arange(int(0.03 * sr)) / sr
    down = set(m['downbeats'])
    for b in m['beats']:
        c = np.sin(2 * np.pi * (2000 if b in down else 1000) * t) * np.exp(-t / 0.008) * 0.5
        i = int(b * sr); x[i:i + len(c)] += c[: max(0, len(x) - i)]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(sr), '-ac', '1', '-i', '-', out], input=x.astype(np.float32).tobytes(), check=True)


if __name__ == '__main__':
    path = sys.argv[1]
    res = beatmap(load(path))
    if '--clicks' in sys.argv:
        click_check(path, res, sys.argv[sys.argv.index('--clicks') + 1])
    print(json.dumps(res))

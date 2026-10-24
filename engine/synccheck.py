"""Sync gate: the nearest audible onset to every picture cue must be within one frame (33 ms at 30 fps).

usage: python synccheck.py mix.wav cues.json [--to s] [--tol 0.033]
Voice cues are left out (a voice clip starts before its first word) and so is 'breath' (a silence). The chance baseline is
the share of random times that also have an onset within the tolerance: a pass means little if that share is high, so
read the two numbers together (KIBO v4.5: 148 cues, 0 outside one frame, chance 75%).
"""
import argparse
import json
import subprocess

import numpy as np

SR = 22050
HOP, WIN = 64, 512
SKIP = {'voice', 'narr', 'breath'}


def onsets(y):
    """Onsets that stand out: a spectral-flux peak at least 3 MADs over the median of the surrounding second and 10% of the
    file's strongest. v4's detector (log1p(50|X|), fixed 0.12) also counted noise and dense beds, so random times passed
    75% of the time."""
    fr = np.lib.stride_tricks.sliding_window_view(np.asarray(y, np.float32), WIN)[::HOP] * np.hanning(WIN)
    flux = np.maximum(0, np.diff(np.log1p(np.abs(np.fft.rfft(fr, axis=1))), axis=0)).sum(1)
    flux /= flux.max() + 1e-12
    times = (np.arange(len(flux)) + 1) * HOP / SR + WIN / 2 / SR
    w = int(SR / HOP / 2)
    pad = np.pad(flux, w, mode='edge')
    win = np.lib.stride_tricks.sliding_window_view(pad, 2 * w + 1)[::8]
    med = np.repeat(np.median(win, axis=1), 8)[: len(flux)]
    mad = np.repeat(np.median(np.abs(win - np.median(win, axis=1, keepdims=True)), axis=1), 8)[: len(flux)]
    thr = np.maximum(med + 3 * mad + 0.02, 0.10)
    pk = [i for i in range(1, len(flux) - 1) if flux[i] > thr[i] and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
    return times[pk]


RUN = 0.08   # keys closer than this blur into one typing texture (for the detector and the ear): check a run's first key


def check(y, cues, tol=0.033, to=None, seed=0):
    on = onsets(y)
    dur = len(y) / SR if to is None else to
    rows = []
    last_key = -9.0
    for c in sorted(cues, key=lambda c: c['t']):
        if c['type'] in SKIP or c['t'] >= dur:
            continue
        if c['type'] == 'key':
            inside_run = c['t'] - last_key < RUN
            last_key = c['t']
            if inside_run:
                continue
        dt = float(np.min(np.abs(on - c['t']))) if len(on) else 9.0
        rows.append({'t': c['t'], 'type': c['type'], 'dt_ms': round(dt * 1000, 1), 'ok': dt <= tol})
    rnd = np.random.default_rng(seed).uniform(0.5, max(0.6, dur - 0.5), 2000)
    chance = float(np.mean([np.min(np.abs(on - r)) <= tol for r in rnd])) if len(on) else 0.0
    return {'n': len(rows), 'miss': sum(not r['ok'] for r in rows), 'chance': round(chance, 3), 'rows': rows}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('mix'); ap.add_argument('cues'); ap.add_argument('--to', type=float); ap.add_argument('--tol', type=float, default=0.033)
    a = ap.parse_args()
    y = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', a.mix, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)
    r = check(y, json.load(open(a.cues))['cues'], a.tol, a.to)
    for x in r['rows']:
        if not x['ok']:
            print(f"MISS {x['type']:9s} {x['t']:7.3f}  nearest onset {x['dt_ms']} ms")
    print(json.dumps({k: r[k] for k in ('n', 'miss', 'chance')}))

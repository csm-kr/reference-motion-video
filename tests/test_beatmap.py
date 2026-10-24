"""beatmap: tempo, beat times, downbeats and sections of a steady-tempo track, checked on synthetic tracks with known answers."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))
from beatmap import beatmap  # noqa: E402

SR = 22050
NOTE = {'C': 261.63, 'F': 349.23, 'G': 392.0, 'A': 440.0}


def kick(n=0.18):
    t = np.arange(int(n * SR)) / SR
    f = 50 + 100 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.08)


def snare(rng, n=0.12):
    t = np.arange(int(n * SR)) / SR
    return rng.standard_normal(len(t)) * np.exp(-t / 0.04) * 0.5


def chord(root, dur):
    t = np.arange(int(dur * SR)) / SR
    f = NOTE[root]
    return sum(np.sin(2 * np.pi * f * k * t) for k in (1, 1.25, 1.5)) * 0.06 * np.minimum(1, t / 0.01)


def track(bpm, offset, bars, quiet_bars=0, seed=0):
    """Kick on beats 1 and 3, snare on 2 and 4, a new chord on every downbeat; the first quiet_bars bars are soft with no snare."""
    rng = np.random.default_rng(seed)
    p = 60 / bpm
    y = np.zeros(int((offset + bars * 4 * p + 2) * SR))
    beats = offset + p * np.arange(bars * 4)
    for k, t in enumerate(beats):
        i, quiet = int(round(t * SR)), k // 4 < quiet_bars
        g = 0.25 if quiet else 1.0
        if k % 2 == 0:
            s = kick(); y[i:i + len(s)] += g * s
        elif not quiet:
            s = snare(rng); y[i:i + len(s)] += s
        if k % 4 == 0:
            s = chord('CFGA'[(k // 4) % 4], 4 * p); y[i:i + len(s)] += g * s
    y += 0.002 * rng.standard_normal(len(y))
    return y.astype(np.float32), beats


@pytest.mark.parametrize('bpm', [100.0, 123.0, 87.5])
def test_tempo_and_beat_times(bpm):
    y, truth = track(bpm, 0.37, 16)
    m = beatmap(y, SR)
    assert abs(m['bpm'] - bpm) < 0.1
    b = np.array(m['beats'])
    err = [np.min(np.abs(b - t)) for t in truth]
    assert max(err) < 0.005


def test_downbeats_are_bar_starts():
    y, truth = track(100.0, 0.37, 16)
    m = beatmap(y, SR)
    d = np.array(m['downbeats'])
    want = truth[::4]
    assert max(np.min(np.abs(d - t)) for t in want) < 0.005
    assert not any(np.min(np.abs(d - t)) < 0.05 for t in truth[2::4])   # beat 3 also has a kick, but is not a bar start


def test_section_boundary_where_energy_rises():
    y, truth = track(100.0, 0.37, 16, quiet_bars=8)
    m = beatmap(y, SR)
    starts = np.array([s['t'] for s in m['sections']])
    assert np.min(np.abs(starts - truth[32])) < 0.6 / 2   # the loud part starts at bar 9
    loud = [s for s in m['sections'] if abs(s['t'] - truth[32]) < 0.3][0]
    first = m['sections'][0]
    assert loud['energy'] > first['energy']

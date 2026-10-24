"""bedmix: a library track placed on the film's beat grid, ducked under the voices, with cue hits on top, mastered."""
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))
from bedmix import KIT, SR, duck_gain, hit_layer, lufs_tp, master, place  # noqa: E402


def clicks(times, n):
    y = np.zeros(n, np.float32)
    for t in times:
        y[int(round(t * SR))] = 1.0
    return y


def test_place_puts_the_anchor_downbeat_on_the_film_time():
    # a downbeat at original track time 10.0 s; the track was stretched 2% faster, so the stretched file has it at 10.0 / 1.02;
    # anchored so that it lands on film 4.0 s
    track = clicks([10.0 / 1.02], int(20 * SR))
    bed = place(track, ratio=1.02, anchor_src=10.0, anchor_film=4.0, dur=8.0)
    peak = np.argmax(np.abs(bed)) / SR
    assert abs(peak - 4.0) < 0.001
    assert len(bed) == int(8.0 * SR)


def test_place_mutes_with_short_ramps():
    track = np.ones(int(20 * SR), np.float32) * 0.5
    bed = place(track, ratio=1.0, anchor_src=0.0, anchor_film=0.0, dur=10.0, mutes=[(4.0, 5.0)])
    assert np.max(np.abs(bed[int(4.05 * SR):int(4.95 * SR)])) < 0.5 * 10 ** (-40 / 20)
    assert abs(bed[int(3.9 * SR)] - 0.5) < 1e-3 and abs(bed[int(5.1 * SR)] - 0.5) < 1e-3
    assert np.max(np.abs(np.diff(bed))) < 0.05   # no step at the mute edges


def test_hit_layer_sounds_every_cue_type_on_its_time():
    for typ in KIT:
        y = hit_layer([{'t': 1.5, 'type': typ, 'big': 1}], 3.0)
        on = np.flatnonzero(np.abs(y) > 0.05 * np.abs(y).max())[0] / SR
        assert abs(on - 1.5) < 0.004, typ


def test_duck_gain_depth_under_voices():
    g = duck_gain([(2.0, 4.0, 'narr'), (6.0, 7.0, 'voice')], dur=10.0)
    db = lambda t: 20 * np.log10(g[int(t * SR)])  # noqa: E731
    assert db(3.0) <= -14 + 0.1
    assert db(6.5) <= -10 + 0.1
    assert db(5.0) > -0.5 and db(9.0) > -0.5


def test_master_hits_minus_14_lufs_under_minus_1_dbtp():
    rng = np.random.default_rng(1)
    t = np.arange(int(12 * SR)) / SR
    x = (0.3 * np.sin(2 * np.pi * 220 * t) * (1 + np.sin(2 * np.pi * 0.5 * t)) + 0.05 * rng.standard_normal(len(t))).astype(np.float32)
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'm.wav')
        master(np.stack([x, x]), out)
        i, tp = lufs_tp(out)
    assert abs(i + 14) < 0.3
    assert tp <= -1.0

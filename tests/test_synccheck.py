"""synccheck: every picture cue needs an audible onset within one frame (33 ms) in the final mix."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))
from synccheck import SR, check  # noqa: E402


def mix_with_hits(times, dur=6.0, seed=0):
    rng = np.random.default_rng(seed)
    y = 0.01 * rng.standard_normal(int(dur * SR))
    t = np.arange(int(0.05 * SR)) / SR
    for x in times:
        i = int(x * SR)
        y[i:i + len(t)] += np.sin(2 * np.pi * 1200 * t) * np.exp(-t / 0.01)
    return y.astype(np.float32)


def test_cues_with_hits_pass_and_a_late_hit_fails():
    cues = [{'t': 1.0, 'type': 'cut'}, {'t': 2.5, 'type': 'pop'}, {'t': 4.0, 'type': 'cut'}]
    ok = check(mix_with_hits([1.0, 2.5, 4.0]), cues)
    assert ok['miss'] == 0 and ok['n'] == 3
    late = check(mix_with_hits([1.0, 2.5, 4.06]), cues)
    assert late['miss'] == 1 and late['rows'][2]['dt_ms'] > 33


def test_fast_typing_is_checked_as_one_run():
    # 24 characters a second: keys 42 ms apart blur into one texture for the detector (and the ear); only the run's first
    # key must be heard. A run whose first key is silent still fails.
    keys = [{'t': 1.0 + k / 24, 'type': 'key'} for k in range(12)]
    ok = check(mix_with_hits([1.0]), keys)
    assert ok['n'] == 1 and ok['miss'] == 0
    late = check(mix_with_hits([1.3]), keys)
    assert late['miss'] == 1


def test_voice_and_breath_cues_are_not_picture_cues():
    cues = [{'t': 1.0, 'type': 'voice', 'id': 'S1'}, {'t': 2.0, 'type': 'breath'}, {'t': 3.0, 'type': 'cut'}]
    r = check(mix_with_hits([3.0]), cues)
    assert r['n'] == 1 and r['miss'] == 0

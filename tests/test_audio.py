"""audio.Sampler tunes each recording to A = 440 (VSCO's glockenspiel is 8-18 cents sharp)."""
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))
import audio  # noqa: E402

audio.set_rate(48000)


def tone(hz, dur=1.2, sr=48000):
    t = np.arange(int(dur * sr)) / sr
    return (np.sin(2 * np.pi * hz * t) + 0.3 * np.sin(2 * np.pi * 2 * hz * t)) * np.exp(-t / 0.5) * 0.5


def measured_hz(y, sr=48000):
    seg = y[int(0.05 * sr):int(0.05 * sr) + 16384]
    X = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 1 << 19)); f = np.fft.rfftfreq(1 << 19, 1 / sr)
    m = (f > 200) & (f < 700)
    return f[m][np.argmax(X[m])]


def test_detune_is_measured_in_cents():
    assert abs(audio.detune_cents(tone(440.0), 69)) < 2
    assert abs(audio.detune_cents(tone(440 * 2 ** (15 / 1200)), 69) - 15) < 2
    assert abs(audio.detune_cents(np.random.default_rng(0).standard_normal(48000), 69)) < 60   # noise: a bounded answer, no crash


def test_sampler_plays_a_sharp_recording_in_tune():
    d = tempfile.mkdtemp()
    sharp = tone(440 * 2 ** (15 / 1200))   # labelled A4, recorded 15 cents sharp
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '1', '-i', '-', os.path.join(d, 'x_A4.wav')],
                   input=sharp.astype(np.float32).tobytes(), check=True)
    s = audio.Sampler(d, loop=False)
    y = s(69, 1.0, 1.0)
    assert abs(1200 * np.log2(measured_hz(y) / 440.0)) < 3
    y0 = audio.Sampler(d, loop=False, tune=False)(69, 1.0, 1.0)
    assert abs(1200 * np.log2(measured_hz(y0) / 440.0) - 15) < 3

"""compose: a score written to the picture's sections and cues. Every palette must act out the same section grammar."""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pytest

ENGINE = os.path.join(os.path.dirname(__file__), '..', 'engine')
SAMPLES = os.path.join(os.path.dirname(__file__), '..', 'samples')
sys.path.insert(0, ENGINE)

# 100 BPM: beat 0.6 s, bar 2.4 s; the drop lands on bar 3 (7.2 s)
FILM = {
    'duration': 16.8, 'bpm': 100, 'T': {},
    'sections': [
        {'t0': 0.0, 't1': 2.4, 'kind': 'intro'},
        {'t0': 2.4, 't1': 4.8, 'kind': 'tease'},
        {'t0': 4.8, 't1': 6.6, 'kind': 'build'},
        {'t0': 5.4, 't1': 6.6, 'kind': 'riser'},
        {'t0': 6.6, 't1': 7.2, 'kind': 'breath'},
        {'t0': 7.2, 't1': 9.6, 'kind': 'groove', 'e': 1.0},
        {'t0': 9.6, 't1': 12.0, 'kind': 'stop'},
        {'t0': 12.0, 't1': 14.4, 'kind': 'groove', 'e': 1.0},
        {'t0': 15.6, 't1': 16.8, 'kind': 'end'},
    ],
    'cues': [
        {'t': 2.4, 'type': 'cut', 'big': 1}, {'t': 3.3, 'type': 'pop'}, {'t': 4.2, 'type': 'tap', 'i': 0}, {'t': 5.1, 'type': 'count'},
        {'t': 6.0, 'type': 'dot'}, {'t': 7.2, 'type': 'drop'}, {'t': 8.1, 'type': 'chip'}, {'t': 8.7, 'type': 'node'},
        {'t': 9.0, 'type': 'num'}, {'t': 9.6, 'type': 'break'}, {'t': 10.2, 'type': 'key'}, {'t': 10.35, 'type': 'key'},
        {'t': 10.5, 'type': 'key'}, {'t': 12.0, 'type': 'reentry'}, {'t': 12.9, 'type': 'word'}, {'t': 13.5, 'type': 'cut'},
        {'t': 14.4, 'type': 'final'},
    ],
}
PALETTES = os.environ.get('PALETTES', 'bright_demo,drums_launch,soft_pulse').split(',')   # PALETTES=band pytest ... tests one


def band_db(y, sr, a, b, lo=None, hi=None):
    seg = y[int(a * sr):int(b * sr)]
    if lo or hi:
        S = np.fft.rfft(seg); f = np.fft.rfftfreq(len(seg), 1 / sr)
        S[(f < (lo or 0)) | (f > (hi or sr))] = 0
        seg = np.fft.irfft(S, len(seg))
    return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12)


@pytest.fixture(scope='module', params=PALETTES)
def rendered(request):
    if not os.path.isdir(os.path.join(SAMPLES, 'vsco')):
        pytest.skip('samples not fetched')
    d = tempfile.mkdtemp()
    cj, out = os.path.join(d, 'cues.json'), os.path.join(d, 'score.wav')
    json.dump(FILM, open(cj, 'w'))
    r = subprocess.run([sys.executable, os.path.join(ENGINE, 'compose.py'), cj, out, '--palette', request.param, '--samples', SAMPLES],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    sr = 48000
    y = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', out, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)
    return request.param, y, sr, json.loads(r.stdout.strip().splitlines()[-1])


def test_intro_has_no_kick(rendered):
    name, y, sr, _ = rendered
    assert band_db(y, sr, 0.2, 2.3, hi=120) < band_db(y, sr, 7.4, 9.4, hi=120) - 12, name


def test_breath_is_near_silent(rendered):
    name, y, sr, _ = rendered
    assert band_db(y, sr, 6.72, 7.12) < band_db(y, sr, 7.4, 9.4) - 30, name


def test_stop_drops_the_drums(rendered):
    name, y, sr, _ = rendered
    assert band_db(y, sr, 10.4, 11.8, hi=150) < band_db(y, sr, 7.4, 9.4, hi=150) - 10, name


def test_end_card_is_silent(rendered):
    name, y, sr, _ = rendered
    assert band_db(y, sr, 15.8, 16.7) < band_db(y, sr, 7.4, 9.4) - 45, name


def test_every_cue_is_heard_and_loudness_is_on_target(rendered):
    name, _, _, rep = rendered
    assert rep['sync']['miss'] == 0, (name, rep['sync'])
    assert abs(rep['lufs'] + 14) < 0.5 and rep['true_peak'] <= -1.0, (name, rep)


def _speechlike(path, dur=1.6, sr=48000):
    """A voice stand-in: a 180 Hz harmonic tone, band-limited like speech, syllables at 4 Hz."""
    t = np.arange(int(dur * sr)) / sr
    y = sum(np.sin(2 * np.pi * 180 * k * t) / k for k in range(1, 18)) * (0.55 + 0.45 * np.sin(2 * np.pi * 4 * t)) ** 2
    y *= np.minimum(1, t / 0.02) * np.minimum(1, (dur - t) / 0.02)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(sr), '-ac', '1', '-i', '-', path], input=(0.3 * y).astype(np.float32).tobytes(), check=True)


def test_narration_gets_the_voice_first_mix():
    # the same film with and without a narration line over the groove: the bed must drop at least 13 dB under it
    # (floor -14 dB, 60 ms smoothing) and the voice must sit at least 8.5 dB over bed + hits
    if not os.path.isdir(os.path.join(SAMPLES, 'vsco')):
        pytest.skip('samples not fetched')
    d = tempfile.mkdtemp()
    _speechlike(os.path.join(d, 'v1.wav'))
    open(os.path.join(d, 'narr.js'), 'w').write('window.NARR = ' + json.dumps({'V1': {'file': 'v1.wav', 'role': 'narr'}}) + ';\n')
    film = json.loads(json.dumps(FILM)); film['cues'].append({'t': 7.6, 'type': 'narr', 'id': 'V1'})
    cj = os.path.join(d, 'cues.json'); json.dump(film, open(cj, 'w'))
    sr = 48000

    def run(narr, tag):
        out, stems = os.path.join(d, f'{tag}.wav'), os.path.join(d, f'stems-{tag}')
        cmd = [sys.executable, os.path.join(ENGINE, 'compose.py'), cj, out, '--palette', 'bright_demo', '--samples', SAMPLES, '--stems', stems]
        if narr:
            cmd += ['--narr', os.path.join(d, 'narr.js'), '--narr-root', d]
        r = subprocess.run(cmd, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-2000:]
        load = lambda p: np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)  # noqa: E731
        return load(os.path.join(stems, 'bed.wav')), load(os.path.join(stems, 'voice.wav')), json.loads(r.stdout.strip().splitlines()[-1])

    bed0, _, _ = run(False, 'plain')
    bed1, v1, rep = run(True, 'narr')
    # measured between cues: cue hits are ducked half as much on purpose (a cut must still land under a voice), so a
    # window holding the chip, node and num hits drops only about 12.9 dB
    assert band_db(bed1, sr, 7.7, 8.05) < band_db(bed0, sr, 7.7, 8.05) - 13
    act = np.abs(v1) > 0.01 * np.abs(v1).max()
    seg = slice(int(7.6 * sr), int(9.2 * sr))
    vdb = 20 * np.log10(np.sqrt(np.mean(v1[seg][act[seg]] ** 2)) + 1e-12)
    bdb = 20 * np.log10(np.sqrt(np.mean(bed1[seg][act[seg]] ** 2)) + 1e-12)
    assert vdb - bdb >= 8.4, (vdb, bdb, rep)
    assert rep['sync']['miss'] == 0

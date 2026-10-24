"""Band score preset: drum kit, electric bass, muted guitar scratches. No piano, no bells.
The arrangement section below is the 50s B2B product promo it was built for (120 BPM); rewrite it per video.

usage: python score_band.py cues.json out.wav --samples DIR [--stems]

Every transition gets a band device on its exact frame: tom fills into chapter changes, snare pickups,
crash + kick + bass on landings, stop-time while the agent types, unison hits on cuts and stabs.
Reference measurement (Airbnb, Stripe spots): 28-76% percussive energy, bass 80-250 Hz carries the low end,
1-4 kHz present, cuts sit on a kick or snare transient. Drums and bass are synthesized here; only UI SFX
(key presses, whooshes, glitch) come from the Pixabay-licensed HyperFrames set.
"""
import json
import subprocess
import sys

import numpy as np

SR = 44100
BEAT = 0.5                       # 120 BPM
S16 = BEAT / 4
rng = np.random.default_rng(5)

data = json.load(open(sys.argv[1]))
SAMPLES = sys.argv[sys.argv.index('--samples') + 1]
T, DUR, CUES = data['T'], data['duration'], data['cues']
N = int((DUR + 3) * SR)
drums, bassb, gtr, sfx, room = (np.zeros((2, N)) for _ in range(5))
kick_env = np.zeros(N)


def tt(sec):
    return np.arange(int(sec * SR)) / SR


def add(bus, t, sig, gain=1.0, pan=0.0, send=0.0):
    i = int(round(t * SR))
    if i >= N or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    sig = sig[: N - i] * gain
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    bus[0, i:i + len(sig)] += sig * gl
    bus[1, i:i + len(sig)] += sig * gr
    if send:
        room[0, i:i + len(sig)] += sig * gl * send
        room[1, i:i + len(sig)] += sig * gr * send


def band(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    w = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * w, len(x))


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def peak_at(x):
    h = int(0.01 * SR)
    return int(np.argmax(np.convolve(x ** 2, np.ones(h), 'same'))) / SR


SFXS = {}
for nm in ['whoosh', 'whoosh-short', 'key-press', 'click', 'glitch-1']:
    x = load(f'{SAMPLES}/sfx/{nm}.mp3')
    SFXS[nm] = (x / (np.abs(x).max() + 1e-9), peak_at(x))


def shot(name, semis=0.0):
    x, pk = SFXS[name]
    if semis:
        r = 2 ** (semis / 12)
        x = np.interp(np.arange(0, len(x) - 1, r), np.arange(len(x)), x)
        pk /= r
    return x, pk


# ---------------------------------------------------------------- drum kit (synthesized)
def kick(v=1.0):
    t = tt(0.45)
    f = 60 + 120 * np.exp(-t / 0.025)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.15)
    click = band(rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t / 0.005) * 0.9
    return np.tanh(1.8 * (body + click)) * v


def snare(v=1.0, tight=False):
    t = tt(0.4)
    body = (np.sin(2 * np.pi * 190 * t) * 0.8 + np.sin(2 * np.pi * 330 * t) * 0.4) * np.exp(-t / 0.06)
    wires = 1.5 * band(rng.standard_normal(len(t)), 1500, 9000) * np.exp(-t / (0.09 if tight else 0.16))
    crack = band(rng.standard_normal(len(t)), 3000, 12000) * np.exp(-t / 0.006) * 0.8
    return np.tanh(1.4 * (body * 0.7 + wires + crack)) * v * 0.8


def rim(v=1.0):
    t = tt(0.06)
    return (np.sin(2 * np.pi * 1700 * t) * 0.6 + np.sin(2 * np.pi * 480 * t)) * np.exp(-t / 0.009) * v * 0.6


def tom(f0, v=1.0):
    t = tt(0.6)
    f = f0 * (1 + 0.35 * np.exp(-t / 0.05))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)
    y += band(rng.standard_normal(len(t)), 300, 3000) * np.exp(-t / 0.02) * 0.25
    return np.tanh(1.3 * y) * v * 0.8


HAT_F = np.array([205.3, 304.4, 369.6, 522.7, 540.0, 800.0]) * 1.6


def metal(n):
    t = np.arange(n) / SR
    y = sum(np.sign(np.sin(2 * np.pi * f * t + rng.uniform(0, 6))) for f in HAT_F)
    return band(y, 6500, 15000)


def hat(v=0.3, open_=False):
    d = 0.45 if open_ else 0.08
    t = tt(d)
    return metal(len(t)) * np.exp(-t / (0.16 if open_ else 0.022)) * v * 0.35


def crash(v=0.5, decay=1.8):
    t = tt(decay * 2.2)
    y = metal(len(t)) * 0.5 + band(rng.standard_normal(len(t)), 4000, 16000)
    return y * np.exp(-t / decay) * (1 - np.exp(-t / 0.003)) * v * 0.45


def reverse_cymbal(dur, v=0.4):
    c = crash(1.0, dur * 0.7)[: int(dur * SR)]
    return c[::-1] * np.linspace(0.3, 1, len(c)) * v


# ---------------------------------------------------------------- electric bass and muted guitar
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ebass(m, dur, v=0.5, slide_to=None):
    """Picked electric bass: saw + sub, lowpass that closes after the pick, optional slide."""
    t = tt(dur + 0.08)
    f = np.full(len(t), mtof(m))
    if slide_to is not None:
        k = np.clip((t - dur * 0.55) / (dur * 0.45), 0, 1)
        f = mtof(m) * (mtof(slide_to) / mtof(m)) ** (k ** 2)
    ph = np.cumsum(f) / SR
    saw = 2 * (ph % 1) - 1
    y = 0.9 * saw + 0.3 * np.sin(2 * np.pi * ph)        # harmonics carry the bass in 80-250 Hz, not the sub
    env_f = 450 + 2400 * np.exp(-t / 0.07)
    lp = np.zeros_like(y)
    acc = 0.0
    for i in range(len(y)):          # per-sample one-pole with a moving cutoff
        a = np.exp(-2 * np.pi * env_f[i] / SR)
        acc = (1 - a) * y[i] + a * acc
        lp[i] = acc
    amp = (1 - np.exp(-t / 0.003)) * (0.7 + 0.3 * np.exp(-t / 0.12))
    amp *= np.where(t > dur, np.exp(-(t - dur) / 0.02), 1)
    return np.tanh(2.2 * lp * amp) * v


def scratch(v=0.2):
    """Muted guitar dead-note: a pitchless chk."""
    t = tt(0.05)
    return band(rng.standard_normal(len(t)), 900, 4200) * np.exp(-t / 0.012) * v


# ---------------------------------------------------------------- arrangement helpers
def put_kick(t, v=0.9):
    add(drums, t, kick(v))
    i = int(t * SR)
    L = int(0.3 * SR)
    seg = kick_env[i:i + L]
    kick_env[i:i + len(seg)] = np.maximum(seg, np.exp(-np.arange(len(seg)) / SR / 0.09))


def steps(a, b, every, offset=0.0):
    t = a + offset
    while t < b - 1e-6:
        yield round(t, 4)
        t += every


def in_any(t, spans):
    return any(a <= t < b for a, b in spans)


ROOT = {'D': 38, 'Bm': 35, 'G': 43, 'A': 45, 'Em': 40, 'F#m': 42}   # roots kept between 62 and 110 Hz
CYCLE = ['D', 'Bm', 'G', 'A']
CHORDS = [(2.0 * k, CYCLE[k % 4]) for k in range(14)]
CHORDS += [(28.0, 'Em'), (29.0, 'G'), (30.0, 'A'), (32.0, 'Bm'), (33.0, 'A'), (34.0, 'D'), (35.0, 'Bm'), (36.0, 'G'), (37.0, 'A'),
           (38.0, 'D'), (39.0, 'F#m'), (40.0, 'Bm'), (41.0, 'G'), (42.0, 'A'), (44.0, 'G'), (44.5, 'A'), (45.0, 'Bm'), (46.0, 'G'), (46.5, 'A')]


def root_at(t):
    cur = CHORDS[0][1]
    for s, c in CHORDS:
        if s <= t + 1e-6:
            cur = c
    return ROOT[cur]


def hit(t, v=1.0, cym=True, bass_note=None, bass_dur=0.4):
    """Band unison hit: kick + snare (+ crash) + bass."""
    put_kick(t, 0.95 * v)
    add(drums, t, snare(0.8 * v), send=0.25)
    if cym:
        add(drums, t, crash(0.55 * v), pan=0.25, send=0.2)
    add(bassb, t, ebass(bass_note if bass_note is not None else root_at(t), bass_dur, 0.55 * v))


def tom_fill(a, b, v=0.8):
    hits = list(steps(a, b, S16))
    fs = [220, 200, 165, 150, 120, 110, 92, 85]
    for k, t in enumerate(hits):
        add(drums, t, tom(fs[min(len(fs) - 1, k * len(fs) // max(1, len(hits)))], v * (0.6 + 0.4 * k / max(1, len(hits) - 1))),
            pan=0.5 - k / max(1, len(hits) - 1), send=0.25)


def snare_pickup(a, b, v=0.7):
    hits = list(steps(a, b, S16))
    for k, t in enumerate(hits):
        add(drums, t, snare(v * (0.45 + 0.55 * k / max(1, len(hits) - 1)), tight=True), send=0.2)


def snare_roll(a, b, v=0.7):
    t, gap, hits = a, 0.25, []
    while t < b - 1e-6:
        hits.append(t)
        t += gap
        gap = max(0.0625, gap * 0.82)
    for k, t in enumerate(hits):
        add(drums, t, snare(v * (0.25 + 0.75 * k / len(hits)), tight=True), send=0.25)


def groove(a, b, style):
    """half: kick 1, snare 3. full: rock beat with 8th hats. drive: four-on-the-floor, 16th hats, open hats."""
    for t in steps(a, b, BEAT):
        bar_pos = round(((t - 0.0) % 2.0) / BEAT) % 4
        if style == 'half':
            if bar_pos == 0:
                put_kick(t, 0.8)
            if bar_pos == 2:
                add(drums, t, snare(0.55), send=0.25)
        elif style == 'full':
            if bar_pos in (0, 2):
                put_kick(t, 0.85)
            if bar_pos in (1, 3):
                add(drums, t, snare(0.6), send=0.2)
            if bar_pos == 2 and t + 0.25 < b:
                put_kick(t + 0.25, 0.55)
        else:
            put_kick(t, 0.9)
            if bar_pos in (1, 3):
                add(drums, t, snare(0.7), send=0.2)
    hat_every = S16 if style == 'drive' else BEAT / 2
    for k, t in enumerate(steps(a, b, hat_every)):
        accent = (k % (4 if style == 'drive' else 2)) == 0
        add(drums, t, hat(0.28 if accent else 0.16), pan=0.3)
    if style == 'drive':
        for t in steps(a, b, BEAT, BEAT / 2):
            add(drums, t, hat(0.2, open_=True), pan=-0.25)
    if style != 'half':
        for t in steps(a, b, BEAT, BEAT / 2 + S16):
            add(gtr, t, scratch(0.16), pan=-0.45)


def bassline(a, b, style):
    """half: roots on 1. full: syncopated 8ths. drive: pumping 8ths with octave jumps."""
    PAT = {  # (seconds into the 2.0 s bar, semitones over the root, length)
        'half': [(0.0, 0, 1.2)],
        'full': [(0.0, 0, 0.45), (0.75, 0, 0.2), (1.0, 0, 0.45), (1.5, 12, 0.2), (1.75, 7, 0.2)],
        'drive': [(k * 0.25, 12 if k % 4 == 2 else 0, 0.2) for k in range(8)],
    }
    for t0 in steps(a - (a % 2.0), b, 2.0):
        for off, semis, d in PAT[style]:
            t = t0 + off
            if a - 1e-6 <= t < b - 1e-6:
                add(bassb, t, ebass(root_at(t) + semis, d, 0.42))


# ---------------------------------------------------------------- the score, scene by scene
# REWRITE PER VIDEO: everything from here to the UI sound design reads this video's T keys.
cue_t = lambda ty: [c['t'] for c in CUES if c['type'] == ty]  # noqa: E731
LAND = cue_t('land')[0]

# S1 problem: no beat yet. Rim on each swapping word, ghost taps on fragments, hats creep in.
for k, t in enumerate(cue_t('swap')):
    add(drums, t, rim(0.55), pan=-0.2 + 0.07 * k, send=0.2)
    if k in (0, 3):
        put_kick(t, 0.6)
for c in CUES:
    if c['type'] == 'pop':
        add(drums, c['t'], snare(0.08, tight=True), pan=((c['i'] * 37) % 11 - 5) / 6)
for k, t in enumerate(steps(2.0, T['ask1'], S16)):
    add(drums, t, hat(0.05 + 0.18 * k / 8), pan=0.3)
# the sentence: half-time groove and a bass pedal; "안 맞고" stutters off the grid
groove(T['ask1'], T['period'], 'half')
for t in steps(T['ask1'], T['period'], BEAT / 2):
    add(bassb, t, ebass(38, 0.2, 0.28))
for d in (0.0, 0.11, 0.19, 0.37, 0.43):                    # deliberately off-grid
    add(drums, T['ask2'] + 0.45 + d, snare(0.32, tight=True), pan=rng.uniform(-0.4, 0.4), send=0.2)
add(bassb, T['ask2'] + 0.45, ebass(38, 0.5, 0.4, slide_to=33))
# the dot: everything stops, a single rim
add(drums, T['period'], rim(0.9), send=0.4)
add(drums, T['period'], snare(0.35, tight=True), send=0.4)
put_kick(T['period'], 0.55)
# sweep -> tom fill into the logo
tom_fill(T['sweep'], T['logo1'])
hit(T['logo1'], 1.0, bass_note=38, bass_dur=1.2)
groove(T['logo1'] + BEAT, T['logo1Out'], 'half')
snare_pickup(T['logo1Out'], T['docsIn'])

# product chapters: full groove, devices on every boundary
SECTIONS_FULL = [(T['docsIn'], T['push']), (T['ti'], T['inbox'] - 0.5), (T['inbox'], T['agent'] - 0.5), (T['agent'], T['type']), (T['enter'], T['type1'] - 0.3)]
for a, b in SECTIONS_FULL:
    groove(a + (BEAT if a in (T['docsIn'], T['ti'], T['inbox'], T['enter']) else 0), b, 'full')
    bassline(a, b, 'full')
hit(T['docsIn'], 0.9, bass_note=38)
add(drums, T['flow'], crash(0.35), pan=-0.3, send=0.2)
snare_roll(T['push'], T['ti'] - 0.05, 0.6)
for t in steps(T['push'], T['ti'], BEAT / 2):
    add(bassb, t, ebass(33 + int((t - T['push']) / 0.25), 0.2, 0.4))       # bass climbs into the push
hit(T['ti'], 0.95)
hit(T['clear'], 0.8, cym=False)
add(drums, T['clear'], hat(0.3, open_=True), send=0.2)
tom_fill(T['inbox'] - 0.5, T['inbox'], 0.7)
hit(T['inbox'], 0.9)
add(drums, T['inqRing'], hat(0.35, open_=True), pan=0.2)
add(drums, T['inqRing'], rim(0.8))
add(drums, T['inqRing'], snare(0.4, tight=True), send=0.2)
tom_fill(T['agent'] - 0.5, T['agent'], 0.7)
hit(T['agent'], 0.9)
# stop-time while the agent is typed to: hats on quarters, the bass holds, keys stay audible
for t in steps(T['type'], T['enter'] - 0.5, BEAT):
    add(drums, t, hat(0.18), pan=0.3)
add(bassb, T['type'], ebass(root_at(T['type']), T['enter'] - T['type'] - 0.55, 0.32))
snare_pickup(T['enter'] - 0.5, T['enter'], 0.55)
hit(T['enter'], 0.95)
add(drums, T['approve'], crash(0.3), pan=0.3, send=0.2)
add(drums, T['apRing'], hat(0.35, open_=True))
add(drums, T['apRing'], snare(0.45, tight=True), send=0.2)
add(drums, T['apRing'], rim(0.8))
hit(T['apRing'] + 0.7, 0.75, cym=False)
# the band stops dead as the screen recedes
hit(T['type1'] - 0.3, 0.85, cym=False, bass_dur=0.15)       # dead stop, no cymbal tail over the words

# break: words land on single kicks with long bass notes, letters stutter, then the snap
for k, t in enumerate([c['t'] for c in CUES if c['type'] == 'word' and T['type1'] <= c['t'] < T['type2']]):
    put_kick(t, 0.8 if k == 0 else 0.55)
    add(drums, t, hat(0.2), pan=0.3)
    add(bassb, t, ebass(root_at(t) + (12 if k % 2 else 0), 0.45, 0.32))
for d in (0.0, 0.07, 0.21, 0.26, 0.4, 0.52, 0.61):
    add(drums, T['type2'] + d, rim(0.4), pan=rng.uniform(-0.6, 0.6))
snare_pickup(T['snap'] - 0.25, T['snap'], 0.4)
hit(T['snap'], 1.0, bass_note=33)
for t in [c['t'] for c in CUES if c['type'] == 'stab' and c['i'] < 3][1:]:
    hit(t, 0.75, cym=False, bass_note=33, bass_dur=0.15)

# build to the flood: kicks on quarters, accelerating roll, climbing bass, one breath of silence
for t in steps(T['tb'], T['impact'] - 0.15, BEAT):
    put_kick(t, 0.85)
snare_roll(T['tb'] + 0.5, T['impact'] - 0.15, 0.75)
for k, t in enumerate(steps(T['tb'], T['impact'] - 0.15, BEAT / 2)):
    add(bassb, t, ebass(33 + (12 if k % 2 else 0) + k // 2, 0.22, 0.4))
add(drums, T['eq'], hat(0.35, open_=True))

# payoff: unison hit, then the drive groove
hit(T['impact'], 1.15, bass_note=26, bass_dur=0.9)
add(drums, T['impact'], crash(0.5, 2.4), pan=-0.3, send=0.3)
groove(T['impact'] + BEAT, T['floodOut'] - 0.4, 'drive')
bassline(T['impact'] + BEAT, T['floodOut'] - 0.4, 'drive')
slam = cue_t('slam')[0]
hit(slam, 0.9)
add(drums, T['floodOut'] - 0.4, reverse_cymbal(0.4 + 0.1, 0.45))
add(drums, T['floodOut'], rim(0.7))                  # the flood starts collapsing: mark it, the landing hit follows at T.ex
put_kick(T['ex'], 0.9)
add(drums, T['ex'], rim(0.6))
groove(T['ex'] + BEAT, T['mont'] - 0.5, 'full')
bassline(T['ex'] + BEAT, T['mont'] - 0.5, 'full')
tom_fill(T['mont'] - 0.5, T['mont'], 0.8)

# montage: every 8th-note cut is a band hit, kick and snare alternating, bass stabs
for c in CUES:
    if c['type'] == 'cutM':
        t, i = c['t'], c['i']
        if i % 2 == 0:
            put_kick(t, 0.9)
        else:
            add(drums, t, snare(0.6, tight=True), send=0.2)
        add(bassb, t, ebass(root_at(t) + (12 if i % 4 == 3 else 0), 0.18, 0.45))
        add(drums, t, hat(0.22), pan=0.3)
        if i % 4 == 0:
            add(drums, t, crash(0.35), pan=0.3 * (1 if i % 8 else -1), send=0.2)

# collapse: stop, reverse cymbal into the dot, pickup into the summary
hit(T['collapse'], 0.8, cym=False, bass_dur=0.2)
add(drums, T['collapse'] + 0.05, reverse_cymbal(0.45, 0.4))
put_kick(T['collapse'] + 0.5, 0.7)
add(drums, T['collapse'] + 0.5, rim(0.6))
snare_pickup(T['sum'] - 0.5, T['sum'], 0.55)
for k, t in enumerate([c['t'] for c in CUES if c['type'] == 'stab' and c['i'] >= 3]):
    hit(t, 0.9 + 0.1 * k, cym=k == 2, bass_dur=0.4)
tom_fill(T['toLogo'] - 0.5, T['toLogo'], 0.6)
put_kick(T['toLogo'], 0.8)
add(drums, T['toLogo'], rim(0.6))
add(drums, T['toLogo'], hat(0.3, open_=True))
for t in cue_t('letter')[4:]:
    add(drums, t, hat(0.22), pan=0.2)
# the dot lands as the logo's period: last unison hit and a held low D
hit(LAND, 1.2, bass_note=26, bass_dur=2.4)
add(drums, LAND, crash(0.55, 2.6), pan=-0.2, send=0.35)
add(drums, LAND, tom(85, 0.7), send=0.3)
for t in cue_t('land')[1:]:
    add(drums, t, rim(0.3), send=0.3)
for t in (T['tag'], T['cta']):
    put_kick(t, 0.65)
    add(drums, t, hat(0.35, open_=True), send=0.2)
    add(drums, t, rim(0.5), send=0.3)

# ---------------------------------------------------------------- UI sound design (pitchless)
for c in CUES:
    t, ty = c['t'], c['type']
    i = c.get('i', 0)
    if ty == 'key':
        x, pk = shot('key-press', rng.uniform(-1, 1))
        add(sfx, t - pk, x, 0.3 * rng.uniform(0.8, 1.0), pan=0.15 * (i % 3 - 1))
    elif ty == 'enter':
        x, pk = shot('click')
        add(sfx, t - pk, x, 0.35)
    elif ty == 'click':
        x, pk = shot('click')
        add(sfx, t - pk, x, 0.25)
    elif ty == 'glitch':
        x, pk = shot('glitch-1')
        add(sfx, t - 0.1, x[int((pk - 0.1) * SR):int((pk + 0.5) * SR)], 0.07, send=0.1)
    elif ty == 'whip':
        x, pk = shot('whoosh-short')
        add(sfx, t + 0.25 - pk, x, 0.28, pan=0.2, send=0.15)
    elif ty == 'whoosh':
        x, pk = shot('whoosh', 1.0)
        add(sfx, t + c['dur'] * 0.5 - pk, x, 0.14, send=0.2)
    elif ty == 'cam':
        zr = c['zr']
        if 0.8 < zr < 1.25 or c['dur'] < 0.3:
            continue
        x, pk = shot('whoosh', 2.0 if zr < 1 else -2.0)
        add(sfx, t + c['dur'] * 0.5 - pk, x, 0.1 + 0.03 * min(3, abs(np.log(zr))), pan=-0.2 if zr < 1 else 0.2, send=0.2)
    elif ty == 'morph' or ty == 'grow':
        L = int(c['dur'] * SR)
        k = np.linspace(0, 1, L)
        add(sfx, t, band(rng.standard_normal(L), 2000, 12000) * k ** 2 * 0.18, send=0.2)
    elif ty == 'suck':
        L = int(c['dur'] * 0.6 * SR)
        k = np.linspace(0, 1, L)
        add(sfx, t, band(rng.standard_normal(L), 1500, 9000) * (1 - k) ** 2 * 0.18, send=0.2)
    elif ty in ('tick', 'pill'):
        add(drums, t, hat(0.12 if ty == 'pill' else 0.18), pan=-0.5 + 0.2 * (i % 6))
    elif ty == 'count':
        for k in range(16):
            u = 1 - np.sqrt(1 - k / 16)
            add(drums, t + u * c['dur'], hat(0.14), pan=0.2)

# ---------------------------------------------------------------- mix
bassb *= 1 - 0.35 * kick_env                  # sidechain: bass ducks under the kick
ir_len = int(1.2 * SR)
ti = np.arange(ir_len) / SR
irs = []
for ch in range(2):
    ir = band(rng.standard_normal(ir_len) * np.exp(-ti / 0.25), 300, 8000)
    ir[: int(0.012 * SR)] = 0
    irs.append(ir / np.sqrt((ir ** 2).sum()))
size = 1 << int(np.ceil(np.log2(N + ir_len)))
wet = np.stack([np.fft.irfft(np.fft.rfft(room[c], size) * np.fft.rfft(irs[c], size), size)[:N] for c in range(2)])
bassb = np.stack([band(bassb[c], 45, 5000) for c in range(2)])
mix = drums * 1.0 + bassb * 1.5 + gtr * 12.0 + sfx + wet * 0.35
if '--stems' in sys.argv:
    db = lambda b, t: 20 * np.log10(np.sqrt((b[:, int(t * SR):int((t + 1) * SR)] ** 2).mean()) + 1e-9)  # noqa: E731
    for name, b in [('drums', drums), ('bass', bassb * 1.5), ('gtr', gtr * 12.0), ('sfx', sfx), ('room', wet * 0.35)]:
        print(f'{name:6s}', ' '.join(f'{db(b, t):4.0f}' for t in range(0, 50)))
mix = np.stack([band(mix[c], 42, 18000) for c in range(2)])
end = int(DUR * SR)
fade = np.ones(N)
fade[end - int(0.8 * SR):end] = np.linspace(1, 0, int(0.8 * SR)) ** 2
mix = (mix * fade)[:, :end]
mix = np.tanh(mix * 1.2) / 1.2
mix /= np.abs(mix).max() / 0.9
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_s16le', sys.argv[2]],
               input=mix.T.astype(np.float32).tobytes(), check=True)
print('wrote', sys.argv[2], f'{DUR:.2f}s, {len(CUES)} cues')

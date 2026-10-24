"""drums_launch: a live, drum-driven groove for feature launches and ads (the Moments 50 s drum ad its owner picked over
orchestral and solo violin, after Apple's "The new MacBook Air with M5").

D minor Afrobeat-flavoured kit at 100 BPM: VSCO kick and snare with ghost notes, eighth hats, shaker, congas, cowbell,
a syncopated bass, a Karplus-Strong muted-guitar skank, and trumpet + horn stabs at the top energy. Big reveals get the
biggest hits; the stop drops the kick for real and a fill lands the re-entry. Needs samples/vsco (Percussion, Brass) and
samples/sfx; missing samples fall back to synthesized drums.
"""
import numpy as np

import audio
from . import kit

NAME = 'drums_launch'
PURPOSE = 'feature launch film or ad; product reveal; music-led, little or no voice-over'
BPM = 100

D_MIN = [62, 65, 69, 72]
G_NIN = [59, 62, 65, 69]
BASS1 = [(0, 38, 2), (3, 50, 1), (6, 48, 1), (7, 45, 1), (10, 38, 2), (13, 41, 1), (14, 43, 1)]
BASS2 = [(0, 43, 2), (3, 50, 1), (6, 41, 1), (8, 43, 2), (11, 45, 1), (13, 48, 1), (14, 45, 1)]
KICK1 = [(0, 1.0), (3, 0.7), (6, 0.85), (10, 0.9), (13, 0.65)]
KICK2 = [(0, 1.0), (6, 0.8), (8, 0.75), (11, 0.85), (14, 0.6)]
CONGA = [(2, 'conga', .45), (3, 'conga_t', .3), (5, 'tumba', .5), (7, 'quinto', .4), (10, 'conga', .45), (11, 'conga_t', .3), (13, 'tumba', .5), (15, 'quinto', .35)]
BELL = [0, 3, 6, 10, 12]
FILES = {
    'bd': 'vsco/Percussion/BDrumNewhit_v6_rr1_Sum.wav', 'bd_big': 'vsco/Percussion/BDrumNewhit_v7_rr1_Sum.wav',
    'sn': 'vsco/Percussion/Snare2-HitSN_v7_rr1_Sum.wav', 'sn_soft': 'vsco/Percussion/Snare2-HitSN_v5_rr1_Sum.wav',
    'ghost': 'vsco/Percussion/afro/Snare2-taps_v2_rr1_Sum.wav', 'crash': 'vsco/Percussion/cymbal-crash1_ff_rr1.wav',
    'crash_mf': 'vsco/Percussion/cymbal-crash1_mf_rr1.wav', 'conga': 'vsco/Percussion/afro/Conga-HitN_v2_rr1_Sum.wav',
    'conga_t': 'vsco/Percussion/afro/Conga-Tap1_v1_rr1_Sum.wav', 'quinto': 'vsco/Percussion/afro/Quinto-HitN_v2_rr1_Sum.wav',
    'tumba': 'vsco/Percussion/afro/Tumba-HitN_v2_rr1_Sum.wav', 'bell': 'vsco/Percussion/afro/Cowbell1_Hit_v2_rr1_Sum.wav',
    'shk': 'vsco/Percussion/afro/Tamb1-Shake_v1_rr1_Sum.wav', 'impact': 'sfx/impact-bass-1.mp3', 'whoosh': 'sfx/whoosh-short.mp3',
    'riser': 'sfx/riser.mp3', 'key': 'sfx/key-press.mp3', 'click': 'sfx/click-soft.mp3', 'pop': 'sfx/pop.mp3',
}
SYNTH = {'bd': lambda: kit.punch_kick(1.0), 'bd_big': lambda: kit.punch_kick(1.0), 'sn': lambda: kit.clap(1.0), 'sn_soft': lambda: kit.clap(0.7),
         'ghost': lambda: kit.rim(0.6), 'crash': lambda: kit.splash(1.0, 1.2), 'crash_mf': lambda: kit.splash(0.8, 0.9),
         'conga': lambda: kit.tom(220, 1.0, 0.12), 'conga_t': lambda: kit.tom(260, 0.7, 0.08), 'quinto': lambda: kit.tom(300, 0.9, 0.1),
         'tumba': lambda: kit.tom(170, 1.0, 0.15), 'bell': lambda: kit.mallet(88, 1.0, 0.15), 'shk': lambda: kit.shaker(1.0),
         'impact': lambda: kit.boom(1.0), 'whoosh': lambda: kit.riser(0.3, 1.0), 'riser': lambda: kit.riser(2.0, 1.0),
         'key': lambda: kit.key_tick(1.0), 'click': lambda: kit.key_tick(0.8), 'pop': lambda: kit.snap(1.0, 2400)}


class _Synth:
    """A synthesized stand-in with the OneShot interface (peak-aligned)."""

    def __init__(self, x):
        self.x = x / (np.abs(x).max() + 1e-9)
        self.pk = int(np.argmax(np.abs(self.x))) / audio.SR

    def at(self, semis=0.0):
        return (audio.repitch(self.x, semis), self.pk / 2 ** (semis / 12)) if semis else (self.x, self.pk)


def setup(ctx):
    ctx.S = {k: ctx.oneshot(p) or _Synth(SYNTH[k]()) for k, p in FILES.items()}
    ctx.tp = ctx.sampler('vsco/Brass/Trumpet/sus', layer=r'_v3', octave=1)
    ctx.hn = ctx.sampler('vsco/Brass/F_Horn/sus', layer=r'_v2', octave=1)
    ctx.glock = ctx.sampler('vsco/Percussion/Glock', loop=False, octave=1)
    ctx.plucks = {}


def glock(ctx, midi, dur, v):
    return ctx.glock(midi, dur, v) if ctx.glock else kit.mallet(midi, v * 0.6, dur)


def pluck(ctx, midi, v):
    if midi not in ctx.plucks:
        ctx.plucks[midi] = kit.pluck(midi, 1.0)
    return ctx.plucks[midi] * v


def stab(ctx, t, v=0.6, chord=D_MIN, long=False):
    d = 0.5 if long else 0.16
    if ctx.tp and ctx.hn:
        for midi in chord[:3]:
            ctx.add('horns', ctx.hum(t, 3), ctx.tp(midi, d, 0.32 * v, release=0.12), pan=0.15, send=0.18)
        ctx.add('horns', ctx.hum(t, 3), ctx.hn(chord[0] - 12, d, 0.4 * v, release=0.15), pan=-0.15, send=0.18)
    else:
        ctx.add('horns', t, kit.airy_pad(chord[:3], d, 0.5 * v), send=0.18)


def tight(ctx, key, pre=0.04):
    """A one-shot trimmed to `pre` s before its peak (an impact's long build-up would play early otherwise)."""
    x, pk = ctx.S[key].at()
    i = max(0, int((pk - pre) * audio.SR))
    y = x[i:].copy()
    n = int(pre * audio.SR)
    y[:n] *= np.linspace(0, 1, n) ** 2
    return y, pre


def intro(ctx, a, b):
    ctx.add('pad', a, kit.airy_pad([50, 57, 62, 65], b - a - 0.1, 0.045), send=0.45)


def groove(ctx, a, b, e=1.0, back=True, hats=True, keys=True):
    S = ctx.S
    for t, s, bi in ctx.steps(a, b):
        alt = bi % 2
        kick = dict(KICK2 if alt else KICK1)
        if s in kick:
            v = kick[s]
            ctx.hit('drums', ctx.hum(t), S['bd'], 0.55 * ctx.vel(v) * e)
            ctx.add('drums', ctx.hum(t, 2), kit.kick_sub(0.5 * v * e))
            ctx.duck(t, 0.8 * v)
        if back and s in (4, 12):
            ctx.hit('drums', ctx.hum(t), S['sn'], 0.5 * ctx.vel(1) * e, pan=0.05, send=0.12)
        if back and s in (7, 9, 15):
            ctx.hit('drums', ctx.hum(t, 12), S['ghost'], 0.18 * ctx.vel(1, .3) * e, pan=0.1)
        if hats and s % 2 == 0:
            ctx.add('drums', ctx.hum(t, 5), kit.hat(0.22 * (1.0 if s % 4 == 0 else 0.7) * e, s == 14 and alt), pan=0.35)
        ctx.hit('drums', ctx.hum(t, 6), S['shk'], 0.07 * (1.4 if s % 2 else 1.0) * e, pan=-0.4)
        if hats:
            for s_, k, v in CONGA:
                if s == s_:
                    ctx.hit('perc', ctx.hum(t, 10), S[k], v * 0.8 * ctx.vel(1, .2) * e, pan=0.45 if 'quinto' in k else -0.3, send=0.1)
        if keys and e >= 1.0 and s in BELL:
            ctx.hit('perc', ctx.hum(t, 4), S['bell'], 0.16 * e, pan=0.55)
        for s_, midi, ln in (BASS2 if alt else BASS1):
            if s == s_:
                ctx.add('music', ctx.hum(t, 4), kit.bass(midi, ln * ctx.step * 0.85, 0.32 * e))
        chord = G_NIN if alt else D_MIN
        if keys and s in (2, 3, 6, 10, 11, 14) and not ctx.under_narr(t):
            for j, midi in enumerate(chord[1:3] if s % 2 else chord[:3]):
                ctx.add('music', ctx.hum(t, 3), pluck(ctx, midi, 0.12 * e), pan=0.3 - 0.15 * j, send=0.08)
        if keys and e >= 1.1 and s in (0, 3, 6, 10):
            stab(ctx, t, 0.5 * e, chord)


def build(ctx, a, b):
    """A fill that lands on b: snare and hand drums in 16ths, rising, the last beat with stabs."""
    st = ctx.steps(a, b)
    n = len(st)
    for k, (t, _, _) in enumerate(st):
        g = 0.25 + 0.6 * k / max(1, n)
        kind = ['sn_soft', 'tumba', 'conga', 'quinto'][k % 4] if k < n - 4 else 'sn'
        ctx.hit('drums' if kind.startswith('sn') else 'perc', ctx.hum(t, 5), ctx.S[kind], g * (0.6 if kind.startswith('sn') else 0.8), pan=0.4 * np.sin(k), send=0.15)
        if k >= n - 4:
            stab(ctx, t, 0.5 + 0.2 * (k - n + 4), D_MIN)


def stop(ctx, a, b):
    """One hit, then the kick is gone; only the shaker keeps time."""
    ctx.hit('drums', a, ctx.S['crash_mf'], 0.22, send=0.15)
    stab(ctx, a, 1.0, D_MIN)
    ctx.add('pad', a, kit.airy_pad([62, 65, 69], b - a - 0.1, 0.04), send=0.5)
    for t, s, _ in ctx.steps(a + 0.6, b):
        ctx.hit('perc', ctx.hum(t, 6), ctx.S['shk'], 0.05, pan=-0.4)


def riser(ctx, a, b):
    x, pk = ctx.S['riser'].at()
    L = int((b - a) * audio.SR)
    p = int(pk * audio.SR)
    seg = x[max(0, p - L):p] * np.linspace(0.3, 1, min(L, p)) ** 1.5
    ctx.add('sfx', b - 0.1 - len(seg) / audio.SR, seg * np.linspace(1, 0.6, len(seg)), 0.16, send=0.3)


def cue(ctx, c):
    S, t, k, i = ctx.S, c['t'], c['type'], c.get('i', 0)
    if k == 'drop':
        y, pre = tight(ctx, 'impact'); ctx.add('sfx', t - pre, y, 0.38, send=0.2)
        ctx.hit('hits', t, S['crash'], 0.45, send=0.2); ctx.hit('hits', t, S['bd_big'], 0.6); stab(ctx, t, 1.0, D_MIN, long=True)
    elif k == 'reentry':
        ctx.hit('hits', t, S['crash'], 0.5, send=0.3); ctx.hit('hits', t, S['bd_big'], 0.6); ctx.hit('sfx', t, S['impact'], 0.3)
        stab(ctx, t, 1.0, D_MIN, long=True)
    elif k == 'final':
        ctx.hit('hits', t, S['crash'], 0.45, send=0.3); ctx.hit('hits', t, S['bd_big'], 0.65)
        y, pre = tight(ctx, 'impact'); ctx.add('sfx', t - pre, y, 0.3, send=0.2); stab(ctx, t, 1.0, D_MIN, long=True)
    elif k == 'break':
        ctx.hit('hits', t, S['bd_big'], 0.6); ctx.add('music', t, kit.bass(38, 0.3, 0.35))
    elif k == 'cut':
        if c.get('big'):
            ctx.hit('hits', t, S['crash_mf'], 0.32, send=0.2); ctx.hit('hits', t, S['bd_big'], 0.5); stab(ctx, t, 0.8, D_MIN)
        else:
            ctx.hit('hits', t, S['sn'], 0.42, send=0.12)
    elif k in ('num', 'bar', 'fill'):
        ctx.hit('hits', t, S['crash_mf'], 0.3, send=0.2); ctx.hit('hits', t, S['sn'], 0.4); stab(ctx, t, 0.8, G_NIN if k == 'num' else D_MIN)
    elif k == 'word':
        ctx.hit('hits', t, S['sn'], 0.5, send=0.2); stab(ctx, t, 0.7, G_NIN)
    elif k == 'pop':
        ctx.hit('hits', t, S['pop'], 0.2, semis=(i % 5) * 1.5 - 2, pan=0.1)
    elif k == 'key':
        ctx.hit('hits', t, S['key'], 0.3 * ctx.vel(1, .15), semis=ctx.rng.uniform(-1, 1), pan=0.1)
    elif k in ('tap', 'tapTalk', 'tapTouch', 'tapSoft'):
        ctx.hit('hits', t, S['click'], 0.35, semis=-2, pan=0.2); ctx.hit('perc', t, S['conga_t'], 0.3)
    elif k in ('chip', 'count'):
        ctx.add('hits', t, glock(ctx, 86 if k == 'chip' else 84, 0.4, 0.3), send=0.4)
    elif k == 'node':
        ctx.add('hits', t, glock(ctx, 81 + 2 * (i % 4), 0.4, 0.28), send=0.4); ctx.hit('perc', t, S['conga'], 0.35)
    elif k == 'whip':
        ctx.hit('sfx', t + 0.06, S['whoosh'], 0.35, pan=-0.2, send=0.15); ctx.hit('hits', t, S['crash_mf'], 0.25, send=0.2)
    elif k == 'dot':
        ctx.add('dot', t, glock(ctx, 86, 0.6, 0.22), send=0.5)
    else:
        return False
    return True


def emphasis(ctx, t, level=1):
    ctx.hit('hits', t, ctx.S['sn'], 0.35 * 1.4 ** level); ctx.add('hits', t, kit.snap(0.2 * 1.4 ** level))

"""bright_demo: friendly, bright pop for product demos and walkthroughs (KIBO v4.5's A2-bright, picked by its owner).

F major I-vi-IV-V at 100 BPM: punchy kick, clap and snap backbeat, shaker and tambourine, marimba stabs (VSCO marimba
when the samples are there, synthesized otherwise), plucky bass, an airy pad that ducks under the kick, tuned toms on big
cuts, and a water-drop pluck for the hero object only. Humanized (+-8 ms, +-10% velocity, off 16ths 10 ms late) except
the hits locked to cues. No marimba figure and no tambourine under narration.
"""
import numpy as np

from . import kit

NAME = 'bright_demo'
PURPOSE = 'product demo or walkthrough; friendly consumer or SaaS app; voice-led'
BPM = 100

CH = [[65, 69, 72, 76], [62, 65, 69, 72], [58, 62, 65, 69], [60, 64, 67, 72]]   # F, Dm7, Bbmaj7, C
RT = [41, 38, 34, 36]
KA = {0: 1.0, 6: 0.7, 8: 0.9, 11: 0.6}
KB = {0: 1.0, 3: 0.55, 8: 0.9, 14: 0.65}
BL = {0: 0, 3: 12, 6: 0, 8: 7, 11: 0, 14: 12}
SCALE = [65, 67, 69, 70, 72, 74, 76, 77]
SW = 0.010
DOTF = (1046.5, 1396.9)   # the hero object's pitch before and after the drop


def setup(ctx):
    ctx.marimba = ctx.sampler('vsco/Percussion/Marimba', loop=False, octave=1)
    ctx.tamb = ctx.oneshot('vsco/Percussion/afro/Tamb1-Hit_v1_rr1_Sum.wav')
    ctx.clav = ctx.oneshot('vsco/Percussion/afro/Claves1_Hit_v2_rr1_Sum.wav')
    if ctx.marimba:   # match the sampled bar's peak to the synthesized one, so levels stay as approved
        ctx.mar_k = np.abs(kit.mallet(72, 1.0)).max() / (np.abs(ctx.marimba(72, 0.4, 1.0)).max() + 1e-9)


def mallet(ctx, midi, v=0.25, dec=0.45):
    if ctx.marimba:
        return ctx.marimba(midi, dec, v * ctx.mar_k, release=0.25)
    return kit.mallet(midi, v, dec)


def gstep(t, s):
    return t + (SW if s % 2 else 0.0)


def intro(ctx, a, b):
    ctx.add('pad', a, kit.airy_pad([53, 60, 65, 69], b - a - 0.1, 0.05), send=0.5)


def groove(ctx, a, b, e=1.0, back=True, hats=True, keys=True):
    for t, s, bi in ctx.steps(a, b):
        ch, rt = CH[bi % 4], RT[bi % 4]
        K = KB if bi % 2 else KA
        tg = ctx.hum(gstep(t, s))
        if s in K:
            ctx.add('drums', tg, kit.punch_kick(0.6 * ctx.vel(K[s]) * e)); ctx.duck(t, 0.8 * K[s])
        if back and s in (4, 12):
            ctx.add('drums', tg, kit.clap(0.42 * ctx.vel(1) * e), send=0.2); ctx.add('perc', tg + 0.006, kit.snap(0.25 * e), pan=0.3, send=0.15)
        ctx.add('perc', tg, kit.shaker(0.07 * (1.3 if s % 2 else 1.0) * e), pan=-0.35)
        if hats and s % 4 == 2 and not ctx.under_narr(t):
            if ctx.tamb:
                ctx.hit('perc', tg, ctx.tamb, 0.16 * ctx.vel(1) * e, pan=0.4)
            else:
                ctx.add('perc', tg, kit.hat(0.12 * e), pan=0.4)
        if s in BL:
            ctx.add('music', tg, kit.pluck_bass(rt + BL[s], ctx.step * 1.6, 0.36 * e))
        if s == 0:
            ctx.add('pad', t, kit.airy_pad(ch, min(ctx.bar - 0.1, b - t - 0.05), 0.06 * e), send=0.4)
        if keys and s in (2, 7, 10) and not ctx.under_narr(t):
            ctx.add('keys', tg, mallet(ctx, ch[(s // 3) % 4] + 12, 0.1 * e), pan=0.25, send=0.15)


def build(ctx, a, b):
    steps = ctx.steps(a, b)
    for k, (t, _, _) in enumerate(steps):
        ctx.add('drums', t, kit.clap(0.1 + 0.25 * k / max(1, len(steps) - 1)), send=0.15)


def stop(ctx, a, b):
    for t, s, bi in ctx.steps(a, b):
        if s == 0:
            ctx.add('pad', t, kit.airy_pad(CH[bi % 4], min(ctx.bar - 0.1, b - t - 0.05), 0.05), send=0.5)
        if s in (0, 8):
            ctx.add('music', t, kit.sub_pulse(RT[bi % 4], 0.5, 0.18))


def riser(ctx, a, b):
    ctx.add('sfx', a, kit.riser(b - a, 0.07), send=0.3)


def accent(ctx, t, v=1.0, ch=None, big=False):
    ch = ch or CH[ctx.bar_of(t) % 4]
    for j, midi in enumerate(ch[:3]):
        ctx.add('keys', t, mallet(ctx, midi + 12, 0.22 * v), pan=-0.2 + 0.2 * j, send=0.2)
    if big:   # cut hits stay on the lightly ducked hits bus, so they still land under a voice
        ctx.add('hits', t, kit.tom(98, 0.55 * v)); ctx.add('hits', t + 0.004, kit.tom(73, 0.45 * v))
        ctx.add('hits', t, kit.clap(0.5 * v), send=0.25); ctx.add('hits', t, kit.snap(0.3 * v), pan=0.2)
        ctx.add('sfx', t, kit.splash(0.12 * v), send=0.3)


def cue(ctx, c):
    t, k, i = c['t'], c['type'], c.get('i', 0)
    if k == 'tapTouch':   # taps before the product helps: claves stepping up the scale
        if ctx.clav:
            ctx.hit('perc', t, ctx.clav, 0.22, semis=(i % 8) * 0.5, pan=-0.2)
        ctx.add('keys', t, mallet(ctx, SCALE[i % 8] + 12, 0.07, 0.25), pan=-0.2, send=0.1)
    elif k in ('tap', 'tapTalk'):
        ctx.add('keys', t, mallet(ctx, [72, 74, 76, 77, 79][i % 5] + 12, 0.24), pan=0.2, send=0.2); ctx.add('hits', t, kit.clap(0.3), send=0.15)
    elif k == 'tapSoft':
        if ctx.clav:
            ctx.hit('hits', t, ctx.clav, 0.24, semis=2, pan=0.2)
        else:
            ctx.add('hits', t, kit.rim(0.2), pan=0.2)
    elif k == 'cut':
        if c.get('big'):
            accent(ctx, t, 0.9, big=True)
        elif c.get('quiet'):
            ctx.add('hits', t, kit.tom(86, 0.35)); ctx.add('hits', t, kit.clap(0.25), send=0.2); accent(ctx, t, 0.5)
        else:
            ctx.add('hits', t, kit.tom(120, 0.32)); ctx.add('hits', t, kit.clap(0.28), send=0.2)
    elif k == 'fill':
        if c.get('small'):
            accent(ctx, t, 0.7)
        else:
            accent(ctx, t, 1.0, CH[0], big=True); ctx.add('drums', t, kit.punch_kick(0.7))
    elif k == 'count':
        ctx.add('keys', t, mallet(ctx, 84, 0.12, 0.25), pan=0.3, send=0.15)
    elif k == 'pop':   # chord tones of the bar (v4's 84 + 2i stepped onto F#, which clashes in F major once pops are many)
        ctx.add('hits', t, mallet(ctx, CH[ctx.bar_of(t) % 4][i % 4] + 24, 0.17, 0.2), pan=0.2); ctx.add('hits', t, kit.snap(0.18, 2100), pan=-0.15)
    elif k == 'chip':
        accent(ctx, t, 0.6); ctx.add('perc', t, kit.snap(0.25), pan=0.25)
    elif k == 'node':
        ctx.add('hits', t, kit.tom(110, 0.3)); ctx.add('keys', t, mallet(ctx, CH[ctx.bar_of(t) % 4][0] + 24, 0.12, 0.3), send=0.2)
    elif k in ('num', 'bar'):
        accent(ctx, t, 0.9 if k == 'num' else 0.85, CH[i % 4] if k == 'bar' else None, big=True)
    elif k == 'drop':
        accent(ctx, t, 1.1, CH[0], big=True); ctx.add('drums', t, kit.punch_kick(0.75)); ctx.add('music', t, kit.pluck_bass(29, 0.6, 0.4))
    elif k == 'word':
        ctx.add('drums', t, kit.clap(0.45), send=0.25); accent(ctx, t, 0.7)
    elif k == 'break':
        ctx.add('drums', t, kit.tom(70, 0.5, 0.5)); ctx.add('sfx', t, kit.splash(0.08, 0.8), send=0.5)
    elif k == 'reentry':
        accent(ctx, t, 1.1, CH[0], big=True); ctx.add('drums', t, kit.punch_kick(0.8))
    elif k == 'final':
        accent(ctx, t, 1.2, CH[0], big=True); ctx.add('drums', t, kit.punch_kick(0.85))
        ctx.add('pad', t, kit.airy_pad([53, 60, 65, 69, 72], 1.6, 0.07), send=0.5); ctx.add('music', t, kit.pluck_bass(41, 0.5, 0.4))
    elif k == 'key':
        ctx.add('hits', ctx.hum(t, 2), kit.key_tick(0.14), pan=0.1)
    elif k == 'dot':
        ctx.add('dot', t, kit.water_drop(DOTF[1] if ctx.after_drop(t) else DOTF[0], 0.3), send=0.35)
    else:
        return False
    return True


def emphasis(ctx, t, level=1):
    ctx.add('hits', t, kit.snap(0.22 * 1.4 ** level), pan=0.1); ctx.add('hits', t, kit.clap(0.2 * 1.4 ** level))

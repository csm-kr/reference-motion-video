"""soft_pulse: calm, warm and clear for concept explainers and how-it-works films; sits under narration.

C major I-vi-IV-V at 96 BPM on real instruments: Salamander grand piano chords and broken-chord figures, VSCO marimba
(tuned to A = 440) for the cue sounds, a plucky bass, an airy pad, and a soft kit from bright_demo's family. Layers
enter with the energy, so each step of an explanation adds one: piano and pad always; bass from e 0.5; the piano figure
from e 0.6; a soft kick on 1 and 3 from e 0.7; a soft clap on 2 and 4 from e 0.8; a shaker from e 0.95. Every pitched cue
plays chord tones of its bar, so a diagram building node by node plays a rising line in key.
The first version (synthesized felt piano, glockenspiel arpeggios and pings, snaps on every cue) was rejected by the
owner: the cue sounds were as loud as the whole bed and the glockenspiel sat 8-18 cents sharp.
"""
from . import kit

NAME = 'soft_pulse'
PURPOSE = 'concept explainer, how-it-works, diagrams building step by step; calm and clear; narration-friendly'
BPM = 96

CH = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]   # C, Am, F, G
RT = [36, 45, 41, 43]


def setup(ctx):
    ctx.piano = ctx.sampler('piano', loop=False)
    ctx.marimba = ctx.sampler('vsco/Percussion/Marimba', loop=False, octave=1)
    ctx.glock = ctx.sampler('vsco/Percussion/Glock', loop=False, octave=1)
    ctx.node_i = 0


def piano(ctx, midi, dur, v):
    return ctx.piano(midi, dur, v, release=0.6) if ctx.piano else kit.felt(midi, dur, v * 0.8)


def mar(ctx, midi, v=0.2, dur=0.4):
    return ctx.marimba(midi, dur, v, release=0.25) if ctx.marimba else kit.mallet(midi, v, dur)


def chord(ctx, t, ch, dur, v, pan=0.0, send=0.3):
    for j, midi in enumerate(ch):
        ctx.add('keys', ctx.hum(t + 0.008 * j, 2), piano(ctx, midi, dur, v * (0.8 if j else 1.0)), pan=pan - 0.15 + 0.1 * j, send=send)


def intro(ctx, a, b):
    ctx.add('pad', a, kit.airy_pad([60, 64, 67], b - a - 0.1, 0.04), send=0.5)
    for t, s, bi in ctx.steps(a, b):
        if s in (0, 8):
            ctx.add('keys', ctx.hum(t, 6), piano(ctx, CH[bi % 4][1 + (s // 8)] + 12, 1.2, 0.09), send=0.4)


def groove(ctx, a, b, e=1.0, back=True, hats=True, keys=True):
    for t, s, bi in ctx.steps(a, b):
        ch, rt = CH[bi % 4], RT[bi % 4]
        if s == 0:
            ctx.add('pad', t, kit.airy_pad(ch[:3], min(ctx.bar - 0.1, b - t - 0.05), 0.035 * e), send=0.45)
            chord(ctx, t, ch[:3], min(ctx.bar * 0.9, b - t), 0.07 * e)
        if e >= 0.5 and s in (0, 6, 8):
            ctx.add('music', ctx.hum(t, 3), kit.pluck_bass(rt + (12 if s == 6 else 0), ctx.step * 1.8, 0.3 * e))
        if keys and e >= 0.6 and s % 4 == 2 and not ctx.under_narr(t):   # a broken chord on the off-beats
            ctx.add('keys', ctx.hum(t, 4), piano(ctx, ch[(s // 4) % 4] + 12, 0.5, 0.05 * e), pan=0.25, send=0.35)
        if e >= 0.7 and s in (0, 8):
            ctx.add('drums', ctx.hum(t, 3), kit.punch_kick(0.4 * e)); ctx.duck(t, 0.6)
        if back and e >= 0.8 and s in (4, 12):
            ctx.add('drums', ctx.hum(t, 5), kit.clap(0.2 * e), pan=0.1, send=0.2)
        if hats and e >= 0.95 and s % 2 == 1:
            ctx.add('perc', ctx.hum(t, 5), kit.shaker(0.035 * e), pan=-0.3)


def build(ctx, a, b):
    st = ctx.steps(a, b)
    n = max(1, len(st) - 1)
    for k, (t, s, bi) in enumerate(st):
        ctx.add('keys', t, mar(ctx, CH[bi % 4][k % 4] + 12, 0.06 + 0.12 * k / n, 0.3), pan=0.25 * ((k % 2) * 2 - 1), send=0.25)
        if k % 2 == 0:
            ctx.add('drums', t, kit.clap(0.05 + 0.15 * k / n), send=0.15)


def stop(ctx, a, b):
    ctx.add('pad', a, kit.airy_pad([64, 67, 72], b - a - 0.1, 0.035), send=0.55)
    for midi in (64, 67, 72):
        ctx.add('keys', a, piano(ctx, midi, b - a, 0.06), send=0.5)


def riser(ctx, a, b):
    ctx.add('sfx', a, kit.riser(b - a, 0.04), send=0.4)


def cue(ctx, c):
    t, k, i = c['t'], c['type'], c.get('i', 0)
    ch = CH[ctx.bar_of(t) % 4]
    tones = ch + [x + 12 for x in ch]
    if k in ('node', 'chip'):   # a diagram building up plays a rising line of chord tones
        ctx.add('hits', t, mar(ctx, tones[ctx.node_i % 8] + 12, 0.22, 0.5), send=0.3)
        ctx.node_i += 1
    elif k in ('num', 'fill', 'bar', 'count'):
        ctx.add('hits', t, mar(ctx, ch[0] + 24, 0.2, 0.5), send=0.3); ctx.add('hits', t, mar(ctx, ch[2] + 12, 0.16, 0.5), send=0.3)
        chord(ctx, t, ch[:3], 1.2, 0.06)
    elif k == 'cut':
        ctx.add('hits', t, kit.tom(120 if not c.get('big') else 96, 0.28)); ctx.add('hits', t, kit.clap(0.14), send=0.15)
    elif k in ('pop', 'word'):
        ctx.add('hits', t, mar(ctx, ch[1 + i % 3] + 24, 0.13, 0.25), send=0.2)
    elif k == 'key':
        ctx.add('hits', ctx.hum(t, 2), kit.key_tick(0.13), pan=0.1)
    elif k in ('tap', 'tapTalk', 'tapTouch', 'tapSoft'):
        ctx.add('hits', t, mar(ctx, ch[i % 4] + 24, 0.15, 0.2)); ctx.add('hits', t, kit.rim(0.08))
    elif k == 'dot':   # the hero object: a short, high, in-tune glockenspiel note on the bar's root
        ctx.add('dot', t, ctx.glock(ch[0] + 24, 0.35, 0.16) if ctx.glock else kit.water_drop(1046.5, 0.25), send=0.45)
    elif k == 'drop':
        ctx.add('drums', t, kit.punch_kick(0.6)); ctx.add('music', t, kit.pluck_bass(RT[ctx.bar_of(t) % 4], 0.6, 0.38))
        chord(ctx, t, [x - 12 for x in ch[:3]] + [ch[0]], 2.0, 0.1)
        ctx.add('hits', t, mar(ctx, ch[0] + 24, 0.24, 0.8), send=0.35); ctx.add('hits', t, kit.clap(0.2), send=0.2)
    elif k == 'break':
        ctx.add('hits', t, piano(ctx, RT[ctx.bar_of(t) % 4] + 12, 1.5, 0.16), send=0.4); ctx.add('sfx', t, kit.splash(0.04, 0.8), send=0.5)
    elif k == 'reentry':
        ctx.add('drums', t, kit.punch_kick(0.55)); chord(ctx, t, ch[:3], 1.6, 0.09)
        ctx.add('hits', t, mar(ctx, ch[0] + 24, 0.22, 0.6), send=0.35); ctx.add('hits', t, kit.clap(0.18), send=0.2)
    elif k == 'final':
        ctx.add('drums', t, kit.punch_kick(0.6)); ctx.add('music', t, kit.pluck_bass(36, 0.6, 0.38))
        chord(ctx, t, [48, 55, 60, 64, 67], 2.2, 0.1, send=0.45); ctx.add('hits', t, mar(ctx, 84, 0.22, 1.0), send=0.45)
    else:
        return False
    return True


def emphasis(ctx, t, level=1):
    ch = CH[ctx.bar_of(t) % 4]
    ctx.add('hits', t, mar(ctx, ch[0] + 24, 0.2 * 1.4 ** level, 0.3)); ctx.add('hits', t, kit.clap(0.12 * 1.4 ** level))

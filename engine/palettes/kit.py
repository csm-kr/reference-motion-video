"""Synthesized voices shared by the palettes (numpy). Each returns a mono signal at audio.SR, read when called.

Ported from the scores that won with their owners: the KIBO v4 A2-bright score (punch kick, clap, snap, shaker, pluck bass,
airy pad, marimba-ish mallet, toms, water drop) and the Moments drum ad (hat, sub kick, bass, Karplus-Strong skank).
"""
import numpy as np

import audio
from audio import band, sweep

rng = np.random.default_rng(2026)


def tt(sec):
    return np.arange(int(sec * audio.SR)) / audio.SR


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def punch_kick(v=1.0):
    t = tt(0.3)
    f = 52 + 110 * np.exp(-t / 0.018)
    body = np.sin(2 * np.pi * np.cumsum(f) / audio.SR) * np.exp(-t / 0.13)
    knock = band(rng.standard_normal(len(t)), 250, 2400) * np.exp(-t / 0.006) * 0.25
    return np.tanh(1.4 * (body + knock)) * v


def kick_sub(v=1.0):
    t = tt(0.4)
    f = 48 + 80 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / audio.SR) * np.exp(-t / 0.22) * v


def clap(v=0.5):
    t = tt(0.25)
    n = band(rng.standard_normal(len(t)), 900, 3200)
    env = np.zeros(len(t))
    for k, d in enumerate((0.0, 0.009, 0.018)):
        env += np.where(t >= d, np.exp(-(t - d) / 0.006), 0) * (0.8 if k < 2 else 1.0)
    env += np.where(t >= 0.018, 0.45 * np.exp(-(t - 0.018) / 0.07), 0)
    return n * env * v


def snap(v=0.4, f=1900):
    t = tt(0.08)
    n = band(rng.standard_normal(len(t)), 2200, 7000) * np.exp(-t / 0.011)
    return (0.9 * n + 0.5 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.008)) * v


def hat(v=0.3, open_=False):
    t = tt(0.3 if open_ else 0.06)
    return band(rng.standard_normal(len(t)), 7000, 15000) * np.exp(-t / (0.11 if open_ else 0.018)) * v


def shaker(v=0.08):
    t = tt(0.07)
    return band(rng.standard_normal(len(t)), 4500, 11000) * np.sin(np.pi * np.minimum(1, t / 0.05)) ** 2 * v


def rim(v=0.4):
    t = tt(0.06)
    ring = np.sin(2 * np.pi * 1650 * t) * np.exp(-t / 0.012) + 0.6 * np.sin(2 * np.pi * 480 * t) * np.exp(-t / 0.02)
    return (ring + band(rng.standard_normal(len(t)), 800, 2600) * np.exp(-t / 0.008) * 0.4) * v


def tom(f0=96, v=0.6, dec=0.32):
    t = tt(dec + 0.15)
    f = f0 * (1 + 0.5 * np.exp(-t / 0.03))
    body = np.sin(2 * np.pi * np.cumsum(f) / audio.SR) * np.exp(-t / dec * 2.2)
    return (body + band(rng.standard_normal(len(t)), 150, 1800) * np.exp(-t / 0.02) * 0.35) * v


def splash(v=0.15, dec=0.5):
    t = tt(dec + 0.2)
    return band(rng.standard_normal(len(t)), 3000, 12000) * np.exp(-t / (dec * 0.35)) * (1 - np.exp(-t / 0.004)) * v


def riser(dur, v=0.06):
    L = int(dur * audio.SR)
    k = np.linspace(0, 1, L)
    n = sweep(rng.standard_normal(L), 400 + 1600 * k, 2500 + 9000 * k) * k ** 2.5
    tone = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (2 * k)) / audio.SR) * k ** 3 * 0.3
    return (n + tone) * v


def mallet(midi, v=0.25, dec=0.45, bright=3.93):
    """Marimba-ish bar (synthesized): the fundamental plus its 4th mode, quick decay."""
    f = hz(midi)
    t = tt(dec + 0.1)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / (dec * 0.45)) + 0.35 * np.sin(2 * np.pi * bright * f * t) * np.exp(-t / 0.03)
    return y * (1 - np.exp(-t / 0.0015)) * v


def pluck_bass(midi, dur, v=0.4):
    f = hz(midi)
    t = tt(dur + 0.05)
    y = np.tanh(1.6 * sum(np.sin(2 * np.pi * k * f * t) / k for k in range(1, 9)))
    env = (1 - np.exp(-t / 0.003)) * np.exp(-t / 0.16) * np.where(t > dur, np.exp(-(t - dur) / 0.02), 1)
    return (band(y, 30, 600) + band(y, 600, 2400) * np.exp(-t / 0.02) * 0.35) * env * v


def bass(midi, dur, v=0.5):
    f = hz(midi)
    t = tt(dur + 0.06)
    y = np.tanh(2.2 * (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) + 0.2 * np.sin(2 * np.pi * 3 * f * t)))
    env = (1 - np.exp(-t / 0.004)) * (0.6 + 0.4 * np.exp(-t / 0.09)) * np.where(t > dur, np.exp(-(t - dur) / 0.02), 1)
    return band(y * env, 30, 2400) * v


def sub_pulse(midi, dur=0.22, v=0.35):
    t = tt(dur + 0.05)
    return np.sin(2 * np.pi * hz(midi) * t) * (1 - np.exp(-t / 0.006)) * np.exp(-t / (dur * 0.6)) * v


def airy_pad(chord, dur, v=0.05):
    t = tt(dur + 0.6)
    y = np.zeros(len(t))
    for midi in chord:
        for det in (-0.12, 0.0, 0.11):
            ff = hz(midi) * 2 ** (det / 12)
            y += sum(np.sin(2 * np.pi * k * ff * t + rng.uniform(0, 6.28)) / k for k in range(1, 6))
    env = np.minimum(1, t / 0.35) * np.where(t > dur, np.exp(-(t - dur) / 0.25), 1)
    return band(y * env, 200, 2600) * v / len(chord)


def felt(midi, dur=1.6, v=0.25):
    """Soft felt piano: a few inharmonic partials, a muted hammer thump, low-passed."""
    f0 = hz(midi)
    t = tt(dur + 0.4)
    y = sum(np.sin(2 * np.pi * k * f0 * np.sqrt(1 + 0.0004 * k * k) * t) / k ** 1.6 * np.exp(-t / (1.4 / k ** 0.6)) for k in range(1, 7))
    env = (1 - np.exp(-t / 0.007)) * np.where(t > dur, np.exp(-(t - dur) / 0.12), 1)
    return band(y * env + band(rng.standard_normal(len(t)), 80, 900) * np.exp(-t / 0.012) * 0.15, 40, 2200) * v


def pluck(midi, v=0.3, decay=0.996):
    """Karplus-Strong muted guitar skank."""
    p = int(audio.SR / hz(midi))
    n = int(0.22 * audio.SR)
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = decay * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return band(out * np.exp(-np.arange(n) / audio.SR / 0.05), 300, 5000) * v


def water_drop(f0=880.0, v=0.3):
    """A pitched water-drop pluck: the hero object's own sound (KIBO's dot)."""
    t = tt(0.35)
    f = f0 * (1 + 0.55 * (1 - np.exp(-t / 0.014)))
    ph = 2 * np.pi * np.cumsum(f) / audio.SR
    return (np.sin(ph) * np.exp(-t / 0.085) + 0.25 * np.sin(2 * ph) * np.exp(-t / 0.04)) * (1 - np.exp(-t / 0.0015)) * v


def boom(v=0.8):
    t = tt(1.6)
    f = 32 + 58 * np.exp(-t / 0.12)
    body = np.sin(2 * np.pi * np.cumsum(f) / audio.SR) * (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.55)
    return (body + band(rng.standard_normal(len(t)), 3000, 12000) * np.exp(-t / 0.35) * 0.25) * v


def key_tick(v=0.12):
    """A keyboard key: a short thock and a click (for typed text), both noise so it has no pitch. A 320 Hz sine thock
    sat a quarter tone under E4 and, repeated 40 times in a typed prompt, made a bright F major score sound out of tune."""
    t = tt(0.05)
    thock = band(rng.standard_normal(len(t)), 250, 900) * np.exp(-t / 0.008)
    thock /= np.abs(thock).max() + 1e-9
    click = band(rng.standard_normal(len(t)), 2500, 8000) * np.exp(-t / 0.003)
    return (0.7 * thock + 0.6 * click / (np.abs(click).max() + 1e-9)) * v

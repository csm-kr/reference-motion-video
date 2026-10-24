"""Measure a reference video's music and cuts: tempo, HPSS percussive share, energy per band, and whether
scene cuts land on a low (<150 Hz) or high (>2 kHz) transient.

usage: python ref-analyze.py video.mp4 [from_sec] [to_sec]   (needs librosa, numpy; ffmpeg for scene cuts)
"""
import subprocess, sys, json
import numpy as np, librosa

def cuts(path):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-vf', "select='gt(scene,0.32)',showinfo", '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return [float(l.split('pts_time:')[1].split()[0]) for l in out.splitlines() if 'pts_time:' in l]

def analyze(path, t0=0, t1=None):
    y, sr = librosa.load(path, sr=22050, mono=True, offset=t0, duration=None if t1 is None else t1 - t0)
    H, P = librosa.effects.hpss(y)
    eh, ep = float((H ** 2).sum()), float((P ** 2).sum())
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512)) ** 2
    f = librosa.fft_frequencies(sr=sr, n_fft=2048)
    bands = {'sub<80': (0, 80), 'bass80-250': (80, 250), 'lowmid250-1k': (250, 1000), 'mid1-4k': (1000, 4000), 'high>4k': (4000, 11025)}
    tot = S.sum()
    share = {k: round(float(S[(f >= a) & (f < b)].sum() / tot) * 100, 1) for k, (a, b) in bands.items()}
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
    # band-limited onset envelopes: low (kick/bass) vs high (snare/hat)
    times = librosa.times_like(S[0], sr=sr, hop_length=512)
    lo = np.maximum(0, np.diff(np.log1p(S[(f < 150)].sum(0)), prepend=0))
    hi = np.maximum(0, np.diff(np.log1p(S[(f > 2000)].sum(0)), prepend=0))
    on = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    rms = librosa.feature.rms(y=y, hop_length=sr)[0]
    return dict(tempo=float(np.atleast_1d(tempo)[0]), perc_share=round(ep / (eh + ep) * 100, 1), bands=share,
                onsets_per_s=round(len(on) / (len(y) / sr), 2), beats=beats.tolist(), times=times, lo=lo, hi=hi,
                loud=[round(20 * np.log10(r + 1e-9), 1) for r in rms])

def cut_hits(a, cs, t0=0):
    rows = []
    for c in cs:
        c -= t0
        if c < 0.3: continue
        i = np.searchsorted(a['times'], c)
        w = slice(max(0, i - 4), i + 5)   # ±90ms
        lo, hi = float(a['lo'][w].max()), float(a['hi'][w].max())
        lo_med, hi_med = float(np.median(a['lo'][a['lo'] > 0]) + 1e-9), float(np.median(a['hi'][a['hi'] > 0]) + 1e-9)
        db = min((abs(c - b) for b in a['beats']), default=9)
        rows.append((round(c, 2), round(db, 3), round(lo / lo_med, 1), round(hi / hi_med, 1)))
    return rows

if __name__ == '__main__':
    path = sys.argv[1]; t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0; t1 = float(sys.argv[3]) if len(sys.argv) > 3 else None
    cs = [c for c in cuts(path) if c >= t0 and (t1 is None or c <= t1)]
    a = analyze(path, t0, t1)
    rows = cut_hits(a, cs, t0)
    on_beat = sum(1 for r in rows if r[1] <= 0.07)
    lo_hit = sum(1 for r in rows if r[2] >= 3); hi_hit = sum(1 for r in rows if r[3] >= 3)
    print(json.dumps(dict(file=path.split('/')[-1], tempo=round(a['tempo'], 1), perc_share=a['perc_share'], bands=a['bands'], onsets_per_s=a['onsets_per_s'],
        cuts=len(rows), cuts_on_beat=on_beat, cuts_with_low_hit=lo_hit, cuts_with_high_hit=hi_hit), ensure_ascii=False))
    print('  loud/s:', ' '.join(str(int(x)) for x in a['loud']))
    print('  cuts (t, beat_dist, low_hit_x, high_hit_x):', rows[:30])

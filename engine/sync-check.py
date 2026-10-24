"""Check that every transition has a hit: a top-25% low (<200 Hz) or high (>2 kHz) onset within ±45 ms.

usage: python sync-check.py score.wav cues.json key1,key2,...   (keys of window.__T that are transitions)
"""
import json, sys
import numpy as np, librosa
y, sr = librosa.load(sys.argv[1], sr=22050)
T = json.load(open(sys.argv[2]))['T']
keys = sys.argv[3].split(',')
S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256)) ** 2
f = librosa.fft_frequencies(sr=sr, n_fft=1024); tm = librosa.times_like(S[0], sr=sr, hop_length=256)
lo = np.maximum(0, np.diff(np.log1p(S[f < 200].sum(0)), prepend=0)); hi = np.maximum(0, np.diff(np.log1p(S[f > 2000].sum(0)), prepend=0))
lm, hm = np.percentile(lo[lo > 0], 75), np.percentile(hi[hi > 0], 75)
miss = 0
for k in keys:
    t = T[k]; i = np.searchsorted(tm, t); w = slice(max(0, i - 4), i + 5)
    l, h = lo[w].max() / lm, hi[w].max() / hm
    ok = l >= 1 or h >= 1
    miss += not ok
    print(f'{k:9s} {t:6.2f}  low {l:4.1f}  high {h:4.1f}  {"OK" if ok else "MISS"}')
print('miss', miss, '/', len(keys))

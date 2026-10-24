#!/usr/bin/env bash
# Fetch the samples the palettes use into ../samples (git-ignored). Palettes synthesize anything missing.
# usage: bash engine/fetch_samples.sh [core|orchestra|piano|all]   (default core)
#   core       VSCO-2-CE (CC0) mallets, kit and hand percussion, brass; HyperFrames SFX (Pixabay licence). ~60 MB
#   orchestra  VSCO-2-CE string sections (one dynamic layer each), solo violin, harp, timpani. ~190 MB
#   piano      Salamander Grand Piano by Alexander Holm (CC-BY 3.0: credit it in the description). ~2 MB
set -euo pipefail
cd "$(dirname "$0")/.."
V=https://raw.githubusercontent.com/sgossner/VSCO-2-CE/master
X=https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/audio/assets/sfx
WHAT=${1:-core}
want() { [ "$WHAT" = all ] || [ "$WHAT" = "$1" ]; }
get() { mkdir -p "$(dirname "$2")"; [ -s "$2" ] || curl -sfL -o "$2" "$1" || echo "missing: $1"; }
enc() { python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$1"; }

TREE=""
tree_get() {   # tree_get <upstream folder> <regex on the file stem>: every matching .wav, spaces in folder names -> _
  [ -n "$TREE" ] || TREE=$(curl -sf "https://api.github.com/repos/sgossner/VSCO-2-CE/git/trees/HEAD?recursive=1")
  echo "$TREE" | python3 -c '
import json, re, sys
pre, pat = sys.argv[1], sys.argv[2]
for x in json.load(sys.stdin)["tree"]:
    p = x["path"]
    if x["type"] == "blob" and p.startswith(pre + "/") and p.endswith(".wav") and re.search(pat, p.rsplit("/", 1)[1][:-4]):
        print(p)' "$1" "$2" | while read -r p; do get "$V/$(enc "$p")" "samples/vsco/${p// /_}"; done
}

if want core; then
  for n in B2 B4 C2 C4 C6 F1 F3 F5 G2 G4; do get "$V/Percussion/Marimba/Marimba_hit_Outrigger_${n}_loud_01.wav" "samples/vsco/Percussion/Marimba/Marimba_hit_Outrigger_${n}_loud_01.wav"; done
  for n in C5 C6 C7 G4 G5 G6; do get "$V/Percussion/Glock/glock_medium_${n}.wav" "samples/vsco/Percussion/Glock/glock_medium_${n}.wav"; done
  for n in C4 C5 C6 C7 G3 G4 G5 G6; do get "$V/Percussion/Xylo/Xylo_Medium_${n}_ff_01_far.wav" "samples/vsco/Percussion/Xylo/Xylo_Medium_${n}_ff_01_far.wav"; done

  # kit and hand percussion: all directly under Percussion/ upstream; the hand drums go to afro/ here
  for f in BDrumNewhit_v6_rr1_Sum BDrumNewhit_v7_rr1_Sum Snare2-HitSN_v5_rr1_Sum Snare2-HitSN_v7_rr1_Sum cymbal-crash1_ff_rr1 cymbal-crash1_mf_rr1; do
    get "$V/Percussion/$f.wav" "samples/vsco/Percussion/$f.wav"
  done
  for f in Snare2-taps_v2_rr1_Sum Conga-HitN_v2_rr1_Sum Conga-Tap1_v1_rr1_Sum Quinto-HitN_v2_rr1_Sum Tumba-HitN_v2_rr1_Sum \
           Cowbell1_Hit_v2_rr1_Sum Claves1_Hit_v2_rr1_Sum Tamb1-Hit_v1_rr1_Sum Tamb1-Shake_v1_rr1_Sum; do
    get "$V/Percussion/$f.wav" "samples/vsco/Percussion/afro/$f.wav"
  done
  tree_get "Brass/Trumpet/sus" "_v3_"   # brass sustains for the drum palette's stabs
  tree_get "Brass/F Horn/sus" "_v2_"
  for f in impact-bass-1 whoosh-short whoosh riser key-press click-soft click pop glitch-1 chime sparkle; do get "$X/$f.mp3" "samples/sfx/$f.mp3"; done
  get "$X/CREDITS.md" "samples/sfx/CREDITS.md"
fi

if want orchestra; then
  tree_get "Strings/Cello Section/susvib" "_v1_"
  tree_get "Strings/Cello Section/spic" "_v2_RR1"
  tree_get "Strings/Solo Contrabass/SusVib" "_v1_"
  tree_get "Strings/Viola Section/susvib" "_v1_"
  tree_get "Strings/Violin Section/susVib" "_v2"
  tree_get "Strings/Violin Section/Spic" "_v2_rr1"
  tree_get "Strings/Solo Violin/Arco Vib" "_f$"
  tree_get "Strings/Harp" "."
  tree_get "Percussion/Timpani" "Hit_v[13]_rr1"
fi

if want piano; then
  for o in 1 2 3 4 5 6 7; do for n in C Ds Fs A; do get "https://tonejs.github.io/audio/salamander/$n$o.mp3" "samples/piano/$n$o.mp3"; done; done
fi

echo "samples: $(du -sh samples | cut -f1)"
echo "check upstream paths if any 'missing:' line printed; palettes synthesize what is not there"

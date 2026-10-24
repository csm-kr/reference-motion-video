#!/usr/bin/env bash
# two-pass loudnorm to -16 LUFS, peak-limited; single-pass loudnorm overshot to -12.7 LUFS / 0 dBFS
set -euo pipefail
in=$1; out=$2
J=$(ffmpeg -v info -i "$in" -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | python3 -c "import sys,json;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -v error -y -i "$in" -af "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,alimiter=limit=0.84:level=false" -ar 44100 "$out"

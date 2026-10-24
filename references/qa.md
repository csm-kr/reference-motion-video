# Gates: what to check before showing a cut

Run relevant checks on the final files, not stems alone, and keep every result as an evidence file next to the report. Sync and audio checks use the bundled engine; STT, OCR, QR decoding and artifact detectors need tools supplied by the environment. Apply those checks only when the film contains the relevant feature, and report anything not run.

| gate | how | pass |
|---|---|---|
| sync | `python engine/synccheck.py out/film.mp4 cues.json` (compose.py already runs it on the master) | every picture cue within 33 ms of an onset; typing runs (keys under 80 ms apart) checked by their first key; read with the chance baseline (random times that pass: 75% with the old detector, 22-38% now) |
| loudness | `ffmpeg -i film.mp4 -af ebur128=peak=true -f null -` | -14 LUFS ±0.5 integrated, true peak ≤ -1 dBTP |
| clicks | listen to the final AAC; use an available impulse / flat-top / burst / jump detector when needed (none is bundled) | no audible clicks or clipped bursts; inspect detector flags before changing speech consonants |
| voice | STT on each voice line cut from the final mix, word accuracy against the script | every line at the clean clip's own accuracy (a line the clean clip already fails is the take, not the mix) |
| stills | `node engine/stills.mjs index.html out/stills <times>` at every section boundary, before rendering | nothing overlaps the caption slot, nothing cut off, readable at phone size |
| contact sheet | one frame every 4 s of the final cut | the approved structure, no blank or white frames |
| drafts | OCR one frame a second | no DRAFT marks in a final |
| captions | OCR at each caption's time against the `.srt` | every caption present at its time, never two at once |
| QR / URL | decode at 1920×1080 and at 640×360 | decodes to the intended URL |
| change control | PSNR between the previous and the new version | only the intended span differs |
| blind listen | two or three loudness-matched versions, shuffled, answer kept hidden | the person picks; the pick wins over every metric |
| comprehension (optional) | with the user's choice of a cloud video service, ask a fresh session with no brief what the product is, for whom, and what the viewer should do | matches the brief's one sentence and call to action |

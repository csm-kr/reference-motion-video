# Music: compose to the picture

## Why composing is the default

A generated or licensed track has its own clock and its own story; the picture's events only roughly meet it. Composing from the film's cue list puts every sound on the frame that caused it and lets the music act out the sections. The owner's blind A/B on the KIBO v4.5 hook (2026-10-18, 30 s, same picture, both at -14 LUFS) settled it:

| | composed (v4.5, A2-bright) | stock track (Mixkit "Forbidden Apple", beat-matched) |
|---|---|---|
| cues heard within 33 ms (strict gate) | 45 / 47 | 47 / 47 |
| voice over bed, 5 lines | 8.0-12.9 dB | 8.5-14.1 dB |
| STT word accuracy | same | same |
| owner's blind pick | **this one** ("무조건 나은데") | "doesn't fit": wrong mood for the product, does not follow the picture |

So: machine metrics cannot pick music. Fit decides, and fit means the product's mood plus the picture's flow.

## How compose.py works

1. **Cues and sections in** (`cues.json` from the composition): every visible event is a cue; every stretch a section named by its purpose (`SKILL.md`, "Sections, by purpose").
2. **Grid:** bars counted from the first `drop` cue; 16th-note slots. Choose a BPM whose beat is a whole number of frames at 30 fps: 100 BPM = 18 frames, 120 = 15, 96 = 18.75 (fine at 30 fps for sections that start on bars; prefer 100 when frames matter).
3. **Arrangement:** for each section the palette plays `intro`, `groove` (with `back`, `hats`, `keys` switched off for `tease`, `light`, `muffled`), `build`, `stop` or `riser`; then one sound per cue (`cue()`), with compose's defaults for any type the palette does not answer.
4. **Section effects:** `muffled` windows low-passed on the groove buses and opening over their last 10%; `breath` 40 dB down with 50 ms edges (the hero object's bus keeps ringing); `end` silent; after `final`, the hit's own tail for 1.2 s, then a dead stop. The room (reverb) is gated with the buses, so no tail rings through a breath.
5. **Mixdown:** a seeded room (the same on every render, so adding a cue never changes the space), the kick sidechain on music, percussion, keys and horns, the pad ducked deeper.
6. **Voices** (if `--narr`): the v4 voice-first rules below.
7. **Master:** -14 LUFS integrated, a limiter at 192 kHz so the true peak stays under -1 dBTP (measured -2.0).
8. **Sync gate:** on the master, every non-voice cue needs an onset within 33 ms. A miss gets the palette's `emphasis` at +3 dB per round and the mix is redone (two rounds at most). The report lists every emphasis added; more than a few means the palette's own sound for that cue type is too weak, so fix the palette.

## Audition, then choose

Never start from the previous film's score: a reused palette silently carries its sound into a film it does not fit. Render the same 15-30 s stretch (the hook or the busiest scene) with two or three palettes that fit the brief's purpose, loudness-matched, and ask the person to pick blind (shuffle the files, keep the answer in a hidden file, reveal after the pick). KIBO v4 auditioned four (A, A2-bright, A3-deep, B-minimal); the owner picked A2-bright, which became `bright_demo`.

## Writing a palette

Follow `engine/palettes/__init__.py`. What made the approved scores work:
- One clear groove per palette, two kick patterns alternating by bar, a bass line on the roots, a pad on the bar.
- Humanize the groove (timing ±8 ms, velocity ±10%, a light swing of the off 16ths), never the hits locked to cues.
- The hero object has its own sound and nothing else uses it (KIBO's water-drop pluck, Moments' glockenspiel, the explainer's high glockenspiel ping).
- Cut hits go to the `hits` bus, which ducks half as much under voices, so a cut still lands under a line.
- Place one-shots by their loudest moment (`ctx.hit`), and trim long pre-rolls (an impact that peaks 2 s in plays its build-up early otherwise).
- No melodic figure and no tambourine under narration.
- Samples: VSCO-2-CE (CC0) names notes one octave low for the mallets and brass used here (a file named C4 sounds C5): pass `octave=1`, and check any new library with an f0 estimate before trusting its names.
- Prove it: add the palette to `tests/test_compose.py`.

## Mix rules (voice first, from KIBO v4)

- Voices: each clip at -17 dBFS speech RMS, centred, no reverb.
- The bed under a voice: at least 14 dB down under narration, 10 dB under other voices, and deeper until the voice is 8.5 dB over bed plus hits, measured where the voice is active.
- While any voice plays, the bed's 1.5-5 kHz band is cut 7 dB (split band, zero phase).
- A phrase the final STT still misses gets the bed further down under that phrase only (v4: "with Vertex AI as backup").
- 5 ms edges on every placed sound; a click checker on the final AAC (`qa.md`).

## The library-track path (only when the user picks a track)

`beatmap.py` maps the track (tempo, beats within 1-2 ms on quantized tracks, downbeats, sections by energy); `bedmix.py` time-stretches it by film BPM / track BPM with rubberband (keep it within about 3%), places one of its downbeats (usually its loudest section's first bar) on a film downbeat (the title drop), measures the placed bed's own beats against the film grid and removes the offset (rubberband added 8.3 ms), mutes the breath, low-passes the intro, adds the cue hits and mixes voice-first. Its sync was perfect and it still lost on fit, so use it when the track itself is the brief ("use this song").
- Licences: YouTube Audio Library says its tracks will not be claimed on YouTube (use outside YouTube is unclear). Mixkit's Free License allows online ads and YouTube with no credit; check each track's licence field. Some Pixabay tracks are registered with Content ID and get claims.
- Match the track's tags to the product before measuring tempo; the losing track was tagged "Powerful, Positive, Bass, Drums, City, Fashion" for a kiosk-accessibility product.

## Cost notes (2026-10)

Google Lyria was ruled out as too expensive. ChatGPT and Claude subscriptions include no music generation. Open models that run on Apple Silicon: ACE-Step 1.5 (MIT, outputs usable commercially, 7-10 GB, BPM/key/length control), Stable Audio 3 Small (community licence, about 3.5 GB). MusicGen and YuE2 weights are non-commercial. Composing costs nothing.

## Sound-design rules

- A whoosh peaks at the camera's top speed (the middle of an inOut move); a riser ends 0.15 s before the hit, then one breath, then the impact.
- At most about 3 SFX per 0.5 s, typing excepted. Drop the drums in the quiet chapter so the music acts out the copy.
- The final hit lands on the frame where the hero object becomes part of the logo; the end card is silent.

## Measured product spots (ref-analyze.py, 2026-10-16)

"perc" is the HPSS percussive share; bands are shares of spectral energy; "cut hits" counts scene cuts with a low (<150 Hz) or high (>2 kHz) onset at least 3× the median within ±90 ms.

| video | BPM | perc | <80 Hz | 80-250 | 250-1k | 1-4k | >4k | cut hits low / high of cuts |
|---|---|---|---|---|---|---|---|---|
| Airbnb, Welcome to the World of Experiences (yZc1D68BkfU) | 144 | 11% | 77% | 6% | 7% | 8% | 3% | 11 / 18 of 25 |
| Airbnb, Things to do that stay with you (nJM6bltqMBk) | 99 | 28% | 2% | 45% | 42% | 7% | 4% | 20 / 14 of 40 |
| Airbnb, Introducing Experience Hosting (MLMzSYzAjZQ) | 129 | 38% | 11% | 36% | 24% | 25% | 4% | 9 / 7 of 13 |
| Airbnb 2022 Summer Release, first 75 s (doczmXmQcP4) | 108 | 76% | 1% | 25% | 45% | 25% | 4% | 4 / 8 of 22 |
| Stripe, Introducing Reader S700 (9oieNo53aNY) | 123 | 52% | 14% | 21% | 46% | 16% | 2% | 23 / 12 of 40 |
| Apple, iPhone 17 Scratch Resistant (PBrYMBacnyM) | 123 | 34% | 25% | 38% | 19% | 12% | 6% | one cut |

What the product spots share: 100-145 BPM, the low end in 80-250 Hz (bass harmonics, not sub), 1-4 kHz present, most cuts on a kick or snare. In a dense groove almost any time has an onset nearby (Apple's M5 film: 87%), so "every cut is on a beat" means little; what matters is the biggest reveal on the biggest hit, cuts on the beat and words off it, and no cuts in the break.

---
name: reference-motion-video
description: Plan and build product launch films, explainers, demo walkthroughs, and teasers from references and real product screens. Use HTML and GSAP with the bundled frame renderer and music composed to the picture's cues.
---

# Reference motion video

**The film is HTML, and its cue list is the score.** Every visible event registers a cue next to the constant that moves the picture; every stretch of the film is a section named by its purpose. A palette turns those into music that hits each frame and acts out the story: no rhythm while the problem is stated, a groove when the product works, a breath before the payoff, drums out when the product deliberately stops, a dead stop on the logo.

Worked examples: `examples/claude-code/` (runnable launch, explainer and demo films on a shared stage, each with a different palette), `examples/moments-v2.html` (36 s continuous-shot ad), `examples/ads/` (Moments ads: drums, orchestral, violin). The Moments compositions need product assets and path adjustments; they are references, not ready-to-render demos.

## Rules that decided past films

1. **Fit first.** The music must match the product's mood and act out the picture's flow. In a blind A/B (KIBO v4.5, 30 s, same picture, same loudness) the owner picked the score composed to the picture over a free stock electropop track that was beat-matched and better on every machine metric: "the second one doesn't fit". Composing is the default; a library track only when the user picks the track (`references/music.md`).
2. **A sound on every cue, on its frame.** Cuts land on the beat, words pop on the off-beat, the biggest reveal gets the biggest hit.
3. **Real footage and real output only.** Motion graphics frame and explain; they never fake a feature. Label speed-ups and waiting cuts on screen ("Live app · 1×", "⋯ waiting cut", "▶▶ sped up"), tag synthetic voices, put a source under every number.
4. **Voice first.** When there is narration or dialogue, the bed gets out of its way (`references/music.md`, "Mix").
5. **Machine gates are necessary, not sufficient.** Sync, loudness and STT can all pass on music that does not fit. The person decides by blind listening.
6. **Ask, then decide.** Ask only what the request and the repo cannot answer, with a recommended answer first; decide the rest and say so.

## Workflow

### 0. Setup check (before anything else)

Report each line as ok or missing, with the fix; never print a key's value.
- Google Chrome (the renderer drives the installed Chrome: the bundled Chromium cannot decode H.264), ffmpeg (with `rubberband`), Node ≥ 20 with `npm ci --prefix engine --ignore-scripts` from the skill directory.
- Python 3.12 with numpy, scipy, soundfile, pytest (`uv venv --python 3.12 .venv`, then `uv pip install --python .venv/bin/python -r requirements.txt` from the skill directory).
- Samples: run `bash engine/fetch_samples.sh core` (VSCO-2-CE CC0 percussion, brass, mallets; Pixabay-licensed SFX), then `bash engine/fetch_samples.sh piano` for `soft_pulse` (Salamander Grand Piano, CC-BY 3.0; credit it when used). Palettes fall back to synthesis when a sample is missing, but the piano fallback can fail the section-balance check; use both sets for the full test suite.
- A narration provider and its credentials only if narration is requested (`references/voice.md`). No API key is needed for the three runnable samples. Narration, transcription and app capture clients are not bundled; use available tools and verify the chosen provider's current documentation when needed.
- Free disk: renders pipe frames (no PNG dumps), but sample libraries and takes need a few GB.

### 1. Intake interview → one-page brief (approved before planning)

Ask only for context that the request and repository do not supply. Use the environment's question tool, or plain chat if none is available; group related questions, put the recommended option first, and reuse answers already given:
1. **Purpose:** what kind of film (launch, concept explainer, demo walkthrough, use-case vignette, manifesto), who watches it, where it goes (YouTube, a contest, social), what they should do after it, the deadline and any judging criteria.
2. **Message and proof:** the one sentence to remember, three proofs with their sources, what must not be said.
3. **Form and sound:** length and formats (16:9, 9:16, cutdowns), languages for screen, captions and voice; music reference links or a mood (offer the palettes in the table below that fit the purpose, plus "I have reference links"); narration or not, and which voice.
4. **Sources and rules:** can the real app be recorded (URL, login, demo data, two devices), will people appear, brand assets, contest rules, third-party IP.
Read the brief back and get a yes. Write it to `video/BRIEF.md`.

### 2. Genre and references

Pick the genre's beat template and measured targets in `references/genres.md` (16 official references across five genres, with shot lengths, words per card, voice-over pace, when the product and logo appear). Watch the chosen references with `/watch`; measure their music with `engine/ref-analyze.py`. For a continuous-shot ad, read `references/transitions.md` and `references/youtube-analysis.md`.

### 3. Plan → `video/PLAN.md` (approved before building)

A beat sheet on the BPM grid (100 BPM = 0.6 s a beat, 18 frames at 30 fps; put the drop on a downbeat): `time | bars | scene | on-screen text | footage | section kind | cues | voice`. Name the **hero object** (one element from the product that travels through the film and lands in the logo), the persistent frame, and every claim with its evidence file.

### 4. Capture real screens

`references/capture.md`: when the product needs it, two-device live takes from the real app (CDP screencast frames with wall-clock stamps, a synthetic customer voice played into the phone's mic, the AI's reply tapped from the page), converted to constant-frame-rate MP4 on one clock, then played in the film through a time map (`[[film t, take t], ...]`: equal steps are 1×, a flat run is a hold, two points 1 ms apart are a cut). Use the browser tool available in the environment; `references/aside-capture.md` gives an Aside-specific implementation. Terminal or tool output: re-typeset the real output (the Claude Code samples), never invent it.

### 5. Narration (optional)

`references/voice.md`: use the chosen TTS provider or supplied recordings, audition takes, pick by word accuracy and pace (155-170 wpm is a starting point for an English demo), and fit the wording or pauses before stretching speech. Clean at the source and write each line to a word budget for its slot.

### 6. Build the composition

- One fixed 1920×1080 `#stage`; **all motion from ONE paused GSAP timeline**; typing, counters, the hero dot and video takes evaluated from time alone in `__seek(t)`. Never CSS animations, `setTimeout` or `requestAnimationFrame` for motion. `fromTo` needs `immediateRender: false`.
- Contract for the engine: `window.__duration`, `__seek(t)`, `__ready`, `__cues`, `__sections`, `__bpm`, `__T`. Start from `examples/claude-code/stage.js` (cues, sections, word pops, typing, counters, terminal cards, the hero dot) or `examples/moments-v2.html` (virtual camera over real screens).
- Register a cue next to every constant that makes something visible; mark every stretch with a section by purpose (table below).
- Captions: reserve a readable slot for spoken lines and keep other content clear of it; identify synthetic speakers and their provider, add translations when the brief requires them, and write the `.srt` from the same caption list.
- Check stills before any full render: `node engine/stills.mjs index.html out/stills 1.7 3.6 ...`.

### 7. Music: compose to the picture

```bash
node engine/cues.mjs > cues.json                      # duration, bpm, T, cues, sections
python engine/compose.py cues.json score.wav --palette bright_demo [--narr narr.js --narr-root .]
```
`compose.py` writes the score, mixes the voices voice-first, masters to -14 LUFS (true peak under -1 dBTP) and runs the sync gate itself: a cue with no audible onset within 33 ms gets the palette's emphasis sound and the mix is redone (twice at most); the report lists what it added. **Audition before choosing:** render the same 15-30 s stretch with two or three fitting palettes and let the person pick blind. Details, mix rules and the library-track path: `references/music.md`.

### 8. Render

`node engine/render.mjs index.html out/film.mp4 --fps 30 --audio score.wav` (JPEG q95 frames piped to x264: about 10× faster than PNG; YouTube flags: High profile, GOP of half the frame rate, BT.709 tags, AAC 48 kHz 384 kbps). Short ranges for drafts: `--from 10 --to 16`. Chrome loads about 18 distinct videos in one page; use stills for takes that do not move.

### 9. Gates (all on the final files)

`references/qa.md`. Check sync on the final MP4 (`python engine/synccheck.py out/film.mp4 cues.json`: every cue within 33 ms, read with its chance baseline), loudness, true peak, stills, transitions, and the person's listening judgement. Apply voice, caption, QR, and revision checks only when those features exist, using tools available in the environment; do not report unrun checks as passed. A cloud comprehension test is optional and requires the user's choice to send the film to that service.

### 10. Deliver

Deliver the brief's length and format, normally H.264 MP4, an `.srt` sidecar when captions are present, and a thumbnail or cutdowns if requested. The built-in stage and renderer are 1920×1080; another aspect ratio requires explicit adaptation, not a renderer flag. Report checks actually run and their evidence. Publishing is a separate action unless the user has already requested it.

## Sections, by purpose

| kind | use it where the picture... | the music |
|---|---|---|
| `intro` | states the problem, before the product acts | no rhythm: a pad, the cue sounds only |
| `tease` | wakes the product up, the first ask | a sparse groove (no backbeat, top percussion or melody) |
| `build` | is about to land a result; the fill before a re-entry | a crescendo into the section's end |
| `groove` | shows the product at work (`e` 0.5-1.2) | the full groove at energy `e` |
| `light` | carries a dense line or a card full of text | the groove without its melodic figure |
| `muffled` | states a serious fact, a statistic, a problem | the groove low-passed, opening into the next section |
| `breath` | holds for one beat before the payoff | near silence; only the hero object's sound rings |
| `stop` | shows the product deliberately not acting (a safety stop, a limit) | drums out, a held pad |
| `end` | is the end card | silence |
| `riser` (overlay) | rises into a landing | a riser that ends on the section's end |

Cue types every palette answers: `drop` (the payoff), `reentry`, `final` (the logo, then a dead stop), `break` (a stop begins), `cut` (`big` for a chapter), `tap`, `tapTouch`, `pop`, `word`, `chip`, `node`, `num`, `count`, `fill`, `bar`, `key` (typing), `dot` (the hero object's own sound).

## Palettes (`engine/palettes/`)

| palette | fits | sound | origin |
|---|---|---|---|
| `bright_demo` | demo walkthroughs, friendly consumer or SaaS apps, voice-led | F major pop at 100 BPM: punchy kick, clap and snap, shaker and tambourine, marimba (VSCO samples or synthesized), plucky bass, airy pad, water-drop hero sound | KIBO v4.5 (A2-bright), owner's pick; won the blind A/B |
| `drums_launch` | launch films and ads, product reveals, music-led | D minor live kit at 100 BPM: VSCO kick, snare and ghosts, hats, congas, cowbell, syncopated bass, muted-guitar skank, trumpet and horn stabs | Moments 50 s drum ad (after Apple's MacBook Air M5 film), owner's favourite style |
| `soft_pulse` | concept explainers, diagrams, narration-heavy films | C major at 96 BPM: sampled piano, tuned marimba cue sounds, a soft kit, bass and pad; layers enter with the energy and cue notes climb as a diagram builds | for `examples/claude-code/explainer` |

Still as stand-alone scripts, to be ported to the palette interface: piano and bells (`engine/score.py`, Moments v2), band (`engine/score_band.py`, a B2B promo), orchestral and solo violin (`examples/ads/orch`, `examples/ads/violin`). To add a palette, follow `engine/palettes/__init__.py` and add its name to `tests/test_compose.py`: the tests prove it acts out the section grammar (no kick in the intro, a silent breath and end card, drums out in the stop, every cue heard, -14 LUFS).

## Files

- `engine/`: `render.mjs`, `cues.mjs`, `stills.mjs`, `compose.py` + `palettes/`, `audio.py` (buses, sampler, room), `synccheck.py`, `beatmap.py` and `bedmix.py` (the library-track path), `ref-analyze.py`, `music-analyze.py`, `fetch_samples.sh`.
- `references/`: `genres.md`, `music.md`, `voice.md`, `capture.md`, `qa.md`, `transitions.md`, `youtube-analysis.md`, `aside-capture.md`, `ads/`.
- `tests/`: `python -m pytest -q tests/` (beat map, library mix, sync gate, section grammar on every palette).

## Brief and submission constraints

- Use the requested duration, languages, aspect ratio and destination. For a contest, read its actual rules and verify the duration with `ffprobe`; do not inherit a past contest's limits.
- Show real product footage or real output for feature claims, and respect the user's brand and asset permissions. Identify unofficial samples about another product, as the Claude Code samples do.
- Prepare local deliverables first. Upload only when the user has authorized the destination and visibility.

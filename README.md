# reference-motion-video

A skill for Claude Code and Codex that plans and builds product videos from references, real product screens, kinetic typography, and music composed to the picture. Author the film as HTML on one paused GSAP timeline, then render each frame to H.264 MP4 with the bundled engine.

## What it does

1. Check the setup and ask for the purpose, audience, message, proof, references, format, and sound.
2. Write a brief and a scene plan before building.
3. Capture real product screens or use real tool output. Connect scenes through a recurring object, camera moves, and typography that acts out its meaning.
4. Register picture events as sound cues and mark sections by purpose: problem, build, groove, breath, stop, ending.
5. Compose a score, mix narration when supplied, render the film, and check timing, loudness, readability, and transitions.

See `examples/claude-code/` for runnable launch, explainer, and demo films, with `drums_launch`, `soft_pulse`, and `bright_demo` music palettes.

## Install

Choose one destination.

**Codex:**

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/csm-kr/reference-motion-video.git ~/.codex/skills/reference-motion-video
cd ~/.codex/skills/reference-motion-video
```

**Claude Code**, from your project directory:

```bash
mkdir -p .claude/skills
git clone https://github.com/csm-kr/reference-motion-video.git .claude/skills/reference-motion-video
cd .claude/skills/reference-motion-video
```

Then, from the skill directory:

```bash
npm ci --prefix engine --ignore-scripts
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
bash engine/fetch_samples.sh core
bash engine/fetch_samples.sh piano
.venv/bin/python -m pytest -q tests/
```

Requires Node 20+, Python 3.12, `uv`, installed Google Chrome, and ffmpeg/ffprobe with the `rubberband` filter. Set `CHROME_PATH` if Chrome is elsewhere. Samples are downloaded separately and are not committed. Fetch both `core` and `piano`: the sampled piano is used by `soft_pulse`. Composition tests skip when the VSCO samples have not been fetched; fetching only `core` leaves the piano fallback active and can fail a section-balance check.

Music-reference measurement is optional and additionally needs `librosa` and `yt-dlp`:

```bash
uv pip install --python .venv/bin/python librosa yt-dlp
```

## Use with an agent

In Codex, invoke `$reference-motion-video`; in Claude Code, invoke `/reference-motion-video`, or ask in plain language:

> Make a 30-second launch film for this app. Use these references, show the real product, and compose music to its transitions.

The skill collects missing context, writes `video/BRIEF.md` and `video/PLAN.md`, confirms the direction, and builds the film. Narration and multi-device capture are optional; their references describe workflows, not bundled TTS or recording clients. Use the browser and media tools available in your environment.

## Run a sample by hand

From the skill directory:

```bash
mkdir -p out/launch
node engine/cues.mjs examples/claude-code/launch/index.html > out/launch/cues.json
.venv/bin/python engine/compose.py out/launch/cues.json out/launch/score.wav --palette drums_launch
node engine/render.mjs examples/claude-code/launch/index.html out/launch/film.mp4 --fps 30 --audio out/launch/score.wav
.venv/bin/python engine/synccheck.py out/launch/film.mp4 out/launch/cues.json
```

Use `node engine/stills.mjs examples/claude-code/launch/index.html out/stills 1.5 4.0 10.0` to inspect frames before rendering. For the other runnable samples, use `explainer` with `soft_pulse`, or `demo` with `bright_demo`.

To make your own film, start with the closest sample, keep its engine and shared-stage paths valid, and edit the scenes, timing constants, cues, and sections. All motion must be derived from the requested time in `__seek(t)`; wall-clock animations do not render correctly.

## References and assets

- `SKILL.md`: the agent workflow and engine contract.
- `references/`: genres, transitions, capture, sound, narration, and review methods.
- `examples/moments-v2.html` and `examples/ads/`: worked compositions for study. Product captures and photos are not bundled; adapt their asset and script paths before rendering.
- `engine/`: frame renderer, cue extraction, three music palettes, audio mixing, and sync checks. The composer targets -14 LUFS and true peak at or below -1 dBTP; inspect the report and final MP4.

Instrument samples: VSCO-2-CE by Versilian Studios (CC0). SFX: HeyGen HyperFrames under the Pixabay Content License; preserve the downloaded credits. `soft_pulse` and the older piano preset use Salamander Grand Piano by Alexander Holm (CC-BY 3.0; attribution required when used). Check the applicable terms for any assets you add.

The Claude Code sample films are unofficial demonstrations and are not affiliated with or endorsed by Anthropic.

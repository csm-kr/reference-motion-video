# reference-motion-video

A skill for Claude Code and Codex that plans and builds product videos from references, real product screens, kinetic typography, and music composed to the picture. Author the film as HTML on one paused GSAP timeline, then render each frame to H.264 MP4 with the bundled engine.

Based on [`csm-kr/motion-demo-video` at `5ab050d`](https://github.com/csm-kr/motion-demo-video/tree/5ab050dc456cfd64e30ef28931802171f7296d14), **October 18, 2026**, before the ten-style collection and the later three.js stage. This repository starts with one initial commit. The engine and Python tests are preserved from that snapshot; the skill name, public instructions, and installation guide have been adapted.

## What it does

1. Check the setup and ask for the purpose, audience, message, proof, references, format, and sound.
2. Write a brief and a scene plan before building.
3. Capture real product screens or use real tool output. Connect scenes through a recurring object, camera moves, and typography that acts out its meaning.
4. Register picture events as sound cues and mark sections by purpose: problem, build, groove, breath, stop, ending.
5. Compose a score, mix narration when supplied, render the film, and check timing, loudness, readability, and transitions.

Three runnable sample films live in `examples/claude-code/`: an 18-second launch, a 30-second explainer, and a 23-second demo. Their music palettes are `drums_launch`, `soft_pulse`, and `bright_demo`.

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
- `examples/moments-v2.html` and `examples/ads/`: earlier worked compositions for study. Product captures and photos are not bundled; adapt their asset and script paths before rendering.
- `engine/`: frame renderer, cue extraction, three music palettes, audio mixing, and sync checks. The composer targets -14 LUFS and true peak at or below -1 dBTP; inspect the report and final MP4.

Instrument samples: VSCO-2-CE by Versilian Studios (CC0). SFX: HeyGen HyperFrames under the Pixabay Content License; preserve the downloaded credits. `soft_pulse` and the older piano preset use Salamander Grand Piano by Alexander Holm (CC-BY 3.0; attribution required when used). Check the applicable terms for any assets you add.

The Claude Code sample films are unofficial demonstrations and are not affiliated with or endorsed by Anthropic.

## 한국어

10개 스타일과 3D 무대가 추가되기 전인 **2026년 10월 18일 버전**을 별도 스킬로 정리했습니다. 레퍼런스 분석 → 브리프와 장면표 작성 → 실제 제품 화면과 타이포 모션 제작 → 화면의 큐에 맞춘 작곡 → MP4 렌더와 검수 순서로 진행합니다.

출시 영상·설명 영상·제품 데모 예제 3개와 음악 팔레트 3종을 포함합니다. Codex에서는 `$reference-motion-video`, Claude Code에서는 `/reference-motion-video`로 사용합니다. 영상 길이·언어·화면비·게시 위치는 사용자의 브리프에 맞춰 정하며, 특정 해커톤의 제출 규칙을 기본값으로 강제하지 않습니다.

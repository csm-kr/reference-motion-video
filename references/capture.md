# Capture: real screens, real time

The KIBO v4 method (2026-10), for apps with more than one device or a live AI. Nothing in the app is mocked or restyled.

## Two devices on one clock

- Record the **production** app with Playwright driving installed Chrome. Each page gets a CDP screencast (`Page.startScreencast`: JPEG frames at device pixels, each with its wall-clock timestamp), so pages recorded at once stay in sync. KIBO: the kiosk at 1080×1920 @2x and a phone at 390×844 @2x that opens the kiosk's claim link (what a QR scan does).
- A live voice AI: the phone's microphone is a stream you play TTS customer lines into, each only after the app has shown "listening" for 2.5 s; the AI's spoken replies are tapped from the page's own audio output (a MediaRecorder on its AudioContext), stamped with the same clock.
- Log everything with wall-clock times: taps, Live input and output transcripts, tool calls, server command results, the session stream. The on-screen chips in the film are built from this log ("tool call → command ok 1,243 ms").
- Convert each stream to constant 30 fps H.264 whose time 0 is the take's start (`ffconcat` with per-frame durations, `-g 6` so seeking is fast); fix a clock step if the Mac's clock jumped.

## Playing takes in the film: the time map

Each device in the composition plays its take through `[[film t, take t], ...]`: equal steps are 1×, a flat run is a hold, two points 1 ms apart are a cut. Speed-ups and waiting cuts are labelled on screen, on the device's own label ("Live app · 1×", "Live app · 1× · ⋯ waiting cut", "▶▶ Sped up · automated taps"). Rings and tap ripples are placed by fractions of the capture measured on the takes. A take's blank lead must never show: enter the device after it (v4.5 moved the phone in on the slot's second beat).

## Limits

- Chrome loads about 18 distinct videos in one page (the 19th stalled); use stills for a device that does not move.
- Seek videos by awaiting `seeked` in `__seek`.
- Real accounts carry real names and faces: say so before the film leaves the machine. Use demo data where the product has it.

## Other sources

- Logged-in web apps with Aside: `aside-capture.md` (a screenshot per keystroke for typing, measured rects in the same call).
- Terminal or tool output (the Claude Code samples): re-typeset the real output in an HTML terminal; never invent a command or a result.
- Live action: your own phone, hands only, locked off, 4K60 if possible, with a release from anyone in frame; Pexels for generic b-roll.

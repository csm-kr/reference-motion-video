# Voice: narration and synthetic lines

Narration methods from the October 18, 2026 workflow. Narration is optional and no TTS API client is bundled.

## Engine

- Use the user's supplied recordings or chosen TTS provider. The earlier KIBO film used Gemini TTS and auditioned voices; that is an example, not a dependency.
- Before making API calls, check the provider's current official documentation for its model IDs, voices, output format, pricing, data handling and commercial rights. Do not infer current capabilities or terms from this dated snapshot.
- Keep voice direction short and consistent. Use pacing controls, pronunciation tools and pause syntax only when the chosen provider supports them.

## Takes: generate many, pick by measurement

1. Write each line to a word budget for its slot: English about 160 wpm for a demo (30 s ≈ 80 words); explainers 140-160, energetic ads 165-180; Korean news reads about 344 syllables a minute, Japanese about 400 characters.
2. Audition a short line first, then generate enough takes to resolve pronunciation or pacing problems within the user's budget.
3. Transcribe each take with word times and score word accuracy against the script (`wacc` rules: numbers to digits, "%" to "percent", the product name's mis-hearings mapped to it). Pick by accuracy first, then by pace closest to the target. KIBO v4: 20 of 21 lines at 100%; a line a voice cannot say clearly ("hears" heard as "Here's") gets reworded, not forced.
4. Fit a line by rewording, adjusting the provider's supported pacing controls, or moving pauses before time-stretching speech.

## Clean at the source

Decode the provider's actual output format, check for clipped runs, and trim to the speech (a starting point: 10 ms RMS above -48 dBFS, 40 ms before and 120 ms after). If resampling is needed, use a proper band-limited resampler and soften the edges. For RIFF/WAV output, respect chunk lengths rather than treating headers as audio. Optional: shorten pauses with crossfades inside the silence.

## Voice chain and mix

High-pass at 80 Hz, +2.5 dB at 3.5 kHz, 2.5:1 compression; no reverb on any voice. In the film: -17 dBFS speech RMS per clip and the bed rules in `music.md` (14 dB under narration, 10 under other voices, 8.5 dB over bed plus hits, the 1.5-5 kHz carve). Captions: chunks of up to about 100 characters timed from the STT word times of the chosen take.

## Synthetic customer and AI lines

Customer lines played into a device's mic for a live take are TTS too: label them on screen ("Customer · synthetic voice (Gemini TTS)") and never present them as testimonials. The AI's spoken replies are the product's own output, captured from the page.

## Local transcription for the checks

Use an available speech-to-text tool with word timestamps and support for the film's language. For a known script, a forced aligner can supply word timing. Neither is bundled; verify the selected tool's current installation and licence before adding it. Use a cloud service only within the user's authorized scope.

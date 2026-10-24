# Transitions, camera and craft rules

From the frame-by-frame study of the winning results in the source video (`youtube-analysis.md`) and the Moments films. These rules carry the short ad mode (one continuous shot, a hero object through every chapter). Long demo and explainer films with real takes use beat-locked cuts with a hit on each (`../SKILL.md`, "Cuts and continuity"); both keep the rules on kinetic type, proof shots and zooms.

## Craft rules (what separated the winning results in the source video)

- **Continuous transitions across chapters.** An object from one scene becomes the next (see the vocabulary below). **Never blink, flash, or cut to black between chapters.** This was the deciding factor in the first test: the losing showreel had beautiful scenes joined by blinks and fades.
- **Story continuity beats per-scene polish.** Each scene hands off to the next; the whole should feel like one shot.
- **Kinetic typography acts out the meaning.** "guess" jitters, "spin" rotates, "consistency" letters snap into alignment, "instantly" snaps in. Do this with intent, not decoration.
- **Purpose over art.** For demo and education videos, the viewer must get the point immediately. A clear and direct cut beats a beautiful and vague one.
- **Open with the viewer's own problem** (empathy words) before showing the product.
- **Alternate typography and product footage:** each claim in text is immediately *proven* by a product shot.
- **Zoom in** on the exact UI moment that matters, then zoom out for context.
- Music starts calm, **builds** to the payoff, and resolves on logo + CTA. Cut on beats.

## Transition vocabulary (pick one per chapter boundary)

| technique | what happens | seen in |
|---|---|---|
| **Object becomes background** | the hero dot scales up until its color is the next scene's background | showreel 2:45, dot → orange field |
| **Object becomes UI** | the dot stretches into a real UI shape (focus ring, button, chip), then real footage fades in under it | Moments v2: period → search focus ring |
| **Shape morph** | a grid or object keeps its position and only changes shape (circle → square → star) | showreel grid |
| **Collapse → burst** | everything shrinks into one point, which explodes into particles that regroup as the next word | showreel 2:50 |
| **Gather / merge** | particles gather into a word; blobs merge into one sphere (metaball) | showreel 2:51, 2:55 |
| **Macro zoom continuity** | camera sits on the typed text, then pulls back to the whole screen without a cut | ChatGPT Work, Flowdeck input |
| **Push-in + dim** | camera dives into the one control that matters, focus ring draws, the rest dims | Flowdeck NOW button |
| **Shared element** | the same photo/card flies from a list into its detail view and back | Moments v2: result tile → lightbox → moment tile |
| **Dot match cut** | zoom into a small brand mark, swap it for a vector copy, grow it into a flood, shrink it onto the same mark on another screen | Moments v2: title period → flood → greeting period |
| **Color flood** | the background fills with the accent while the camera pulls out; use once, at the payoff | Flowdeck purple, kinetic-type green |
| **Fixed frame, swapped content** | the frame stays still; only what is inside it changes (light board → dark board, keyword → keyword) | Flowdeck ending, "People Ops. → Everyone." |
| **Motion-blur whip** | words or screens slide out sideways with blur while the next slides in | ChatGPT Work, showreel copy |

Hard cuts are allowed only (a) inside a montage of ≤0.3s shots, or (b) on a downbeat where the cut itself is the accent. Crossfades are allowed only *under* a covering object (fade the screen in beneath the ring or flying photo), never as the transition itself.

Where to find the hero object: a dot or period in the logo, the brand accent on one UI element, a recurring control (a Save button that appears in every scene), the product's main card. If the product has nothing like this, a single colored dot still works, but say in the memo why it fits.

## Virtual camera over real screens

- Put every captured screen at its native pixel size (e.g. 2880×1800) inside one `#cam` layer. The camera is `{cx, cy, z}`: the screen point at stage center, and how many screen pixels span the 1920px stage width.
- Evaluate the camera **from time alone** (a list of moves, each starting where the previous ended) instead of stateful tweens, so any seek order renders the same frame. Interpolate `z` in log space so zooms feel even. See `camTo` / `camAt` in `examples/moments-v2.html`.
- A full-screen view of a 16:10 capture is `z ≈ 3240` for 2880px, which leaves a margin so the screen reads as a floating card.
- Macro zooms need a 2× capture. Past about 1.5× of the capture's own pixels text goes soft; that is where you swap to a vector copy (the dot match cut).
- Keep camera framing clear of the caption pill. If the target sits at the screen edge, let the camera go past the screen; the card edge and empty background are fine.

## Beat grid

- Choose the BPM before timing anything (100 BPM = 0.6s per beat). Put scene boundaries, word swaps, and landings on beats, and start each transition so it **lands** on the downbeat (start = beat − duration).
- Speed-up swaps (task words, titles) shorten their gaps by about 20% each step.
- When the music arrives, measure its real beat times and snap the constants to them.

---
name: historical-animation
description: >
  Plan and animate a silent, subtitled military-history film from a user prompt and script.
  Use when the user gives a battle, an empire, a war, a script, commander portraits, a historical map,
  territory changes, or army movements. Use for Chandragupta, Seleucus, and any other campaign.
  The war's details change with the prompt. Never add audio. Subtitles are required.
---

# Historical animation

## Overview

Turn a prompt and a script into a silent schematic battle film. You plan the shots, place maps, portraits, and armies, burn the script in as subtitles, and render. The names and the geography come from this request. Do not reuse another war's layout.

No speech, music, or effects. Subtitles are part of the picture.

## When to use

- The user names a battle, a campaign, a treaty, or two empires.
- The user pastes a script, subtitle lines, or a shot list.
- The user supplies an SVG map or square portraits.

Do not use this skill for a film that needs a soundtrack.

## Before any shot

1. Read `docs/house-rules.md`.
2. Read the prompt and the script. The script lines are the subtitles.
3. Read `docs/placement.md` before you choose a coordinate.
4. Read `skills/silent-subtitles/SKILL.md`, `skills/battle-map/SKILL.md`, `skills/army-symbols/SKILL.md`, and `skills/commander-portraits/SKILL.md` as you reach that step.

## Procedure

1. Write a one-page plan before drawing. One row per scene: start, end, subtitle (the user's line), what is on the map, what moves, which regions change color. Four to six scenes, about 8 to 14 seconds each, is the usual shape. The first scene starts at 0.
2. List every claim the picture will make. Cite it, or drop it. Estimates stay estimates. A debated border stays debated.
3. Build the plate with the battle-map skill. User SVG first. Original schematic otherwise.
4. Place both armies with the army-symbols skill. In the clash scene both boxes move forward and stop short of a gap.
5. Place commanders with the commander-portraits skill. Circles sit beside their army, on the home side. Crop the user's square image. If they gave no image, use initials.
6. Apply the silent-subtitles skill. Each script line is a scene subtitle.
7. Extend `hde/` from `docs/scene-contract.md` if the shot needs circles, moving boxes, unit symbols, or a territory fill. Then render from `docs/renderer.md`.
8. Read a still from each scene. Fix collisions. Render the preview, then the 720p file. Stop when the log prints `result: OK` and `OUTPUT_PATH=`.

## Common rationalizations

| Thought | Why it is wrong |
| --- | --- |
| "A placeholder voice will do for now." | This library does not add audio. Subtitles carry the script. |
| "I already know where the armies stood from the last film." | Positions change with the war. Read this prompt. |
| "A generated face is close enough." | No portrait file means initials, not a face. |
| "The whole frontier changed hands, so color the whole map." | Recolor only regions a source you cite actually cedes. |
| "The dots already move because an arrow is there." | An arrow is a line. When the plan says the armies advance, the boxes themselves move. |
| "I'll render and call it done without opening a still." | Colliding labels are the usual failure. Look at one frame per scene. |

## Red flags

- A flite log line, a music bed, or an `audio_file` path.
- One army moving while the other sits still in a scene described as a battle.
- A portrait circle with no image and no "portrait not supplied" label.
- A commander circle covering the unit icons.
- Subtitles missing, or rewritten instead of using the user's lines.
- A territory fill with no source note.
- `result: OK` not in the render log.

## Verification

- Every script line is visible as a subtitle in the scene that speaks it.
- The render log says silence, not `flite`.
- Stills show the map, the circular ruler, both army boxes, both commander circles, and the subtitle band clear of icons.
- `python3 -m unittest tests.test_engine -v` passes.
- The report names the MP4 path from the log, what is illustrative, and any portrait the user has not supplied yet.

## See also

- `docs/placement.md`
- `docs/scene-contract.md`
- `docs/renderer.md`
- `skills/historical-animation/examples.md`

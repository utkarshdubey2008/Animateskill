# AGENTS.md

Guidance for coding agents working in this repository.

## What this is

A skill library for silent, subtitled military-history animation. Skills are the workflows. `hde/` is the renderer they drive. The war on screen comes from the user's prompt and script.

## Rules

- If a task matches a skill, follow that skill.
- Skills live at `skills/<name>/SKILL.md`.
- Read `docs/house-rules.md` before drawing. It is the source for silence, subtitles, and honesty.
- Read `docs/placement.md` before choosing a coordinate.
- Do not add narration, music, or effects. Do not pass `--no-silence`.

## Intent

| The user wants | Skill |
| --- | --- |
| A battle film, a script, a campaign | `historical-animation` |
| A map, borders, the ruler | `battle-map` |
| Armies, units, an advance | `army-symbols` |
| A king, a general, a portrait | `commander-portraits` |
| Subtitles or a render | `silent-subtitles` |

A full film runs `historical-animation`, which calls the others in order.

## Execution

1. Load the matching `SKILL.md`.
2. Finish its steps, including stills and validation, before you call the film done.
3. Extend `hde/` only for a field in `docs/scene-contract.md` that this film uses. Keep the existing tests passing.

## Do not skip the skill

These thoughts are wrong: "This war is too small for a skill." "I already know the layout." "A voiceover is easier than subtitles."

## New skills

```
skills/<name>/SKILL.md
```

Front matter needs `name` and `description`. Put long samples in `examples.md`. Point at `docs/` instead of copying a rule into a second file.

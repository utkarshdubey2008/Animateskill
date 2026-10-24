# House rules

These rules win over habit. Every skill in this repo starts from here.

## The film is silent, and it has subtitles

- Burn the user's script onto the picture as subtitles.
- Do not synthesize speech. Do not attach a narration file. Do not add music or sound effects.
- The encoder still muxes a silent AAC track, because the validator expects an audio stream. That track stays silent.
- Render with the default, which is silence. Do not pass `--no-silence`.

## The war changes

Names, borders, armies, and dates come from the prompt and the script for this film. Plassey, the Mauryan war, and any other battle are examples of method. Copy the method. Do not copy their coordinates onto a different war.

## What the user supplies

- A prompt: the war, the length, and any shot notes.
- A script: the subtitle lines. Use those words. One scene per line unless the user grouped lines into a scene.
- Optional SVG maps, and optional square portraits.

If a map or a portrait is missing, draw an original schematic or a labeled empty circle. Do not invent a face. Do not trace a published map.

## Pictures stay honest

- A filled marker is an area the sources locate. A hollow marker is approximate.
- A moving army and a dashed arrow are illustrative unless a source describes that route. The label starts with `Illustrative`.
- A portrait is a coin, a sculpture, or a clearly labeled artistic reconstruction. The on-screen detail says which.
- A territory change uses only regions a cited source hands over. Disputed lists stay described as disputed.
- A later treaty is not drawn on the day of the battle. Give it its own scene and its own year.

## Coordinates

`x` runs west to east, 0 to 1. `y` runs north to south, 0 to 1. North is up. The plate is 1600×900 (16:9). `zoom` is the fraction of map width on screen. At `zoom` 1 the whole plate is visible and the center has no effect.

The bottom 20 percent of the frame is the subtitle band. The top-left holds the title and the legend. Keep labels, portraits, and the circular ruler out of both.

---
name: battle-map
description: >
  Build the historical map plate for a silent battle film: user SVG or an original schematic,
  rivers, mountains, cities, coastlines, empire colors, changing borders, and the circular ruler.
  Use when placing geography or territory. Never add audio.
---

# Battle map

## Overview

The plate is the ground under the armies. It is an original diagram, or an SVG the user supplied. North is up. Empire colors are flat and consistent. Borders change only where a cited source says land changed hands.

## When to use

Use after the scene plan exists and before armies are placed.

## Steps

1. Read `docs/house-rules.md` and `docs/placement.md`.
2. If the user supplied an SVG map, use that file as the plate. Do not redraw a published atlas into it.
3. If they did not, create `assets/maps/<slug>.svg` at 1600×900. Include a `<desc>` that says the drawing is original, north is up, and movement is added by the scene file.
4. Draw coast, rivers, mountains, and cities that the scene plan mentions. Skip landmarks the script never uses.
5. Fill each empire with one color. Reuse that hex on the army box and the portrait ring.
6. Give every region path a stable id. List which ids change fill, in which scene, in the plan.
7. Place `skills/battle-map/assets/circular-ruler.svg` on the plate in the corner from `docs/placement.md`.
8. When a scene changes a fill, implement `layers` from `docs/scene-contract.md` before rendering. The stock renderer uses one raster for the whole film.

## Checks

- Place names are short and outside the subtitle band and the title corner.
- The ruler is a compass, not a fake mileage scale.
- Every recolored region has a source note that names it.
- No troop icons are baked into the plate.

## See also

- `docs/placement.md`
- `docs/scene-contract.md`

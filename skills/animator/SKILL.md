---
name: animator
description: >
  Unified military history animation skill: plan and render silent, subtitled schematic
  documentaries and tactical battle maps from prompts, scripts, commander portraits, and SVG
  battlefield plates. Encapsulates tactical cartography (no macro country maps for battles),
  pre-gunpowder melee mechanics (no bombing in antiquity/medieval), moving formation boxes with
  period flags (no arrows), pre-deployed defensive lines, dynamic camera pans, casualty tracking,
  and burned subtitles with silent AAC validation.
---

# Animator — Unified Historical Battle Animation Skill

## 1. Overview & Operational Architecture

`animator` is the master animation and documentary framework for rendering historical military documentaries and tactical battle maps. It consolidates all sub-disciplines into an automated, reproducible pipeline:

1. **Choreography & Camera Dynamics**: Scene timing, camera windows (`start`/`end` with `cx`, `cy`, `zoom`), easing curves, and dissolve transitions. When forces march directionally (e.g., southward/downward), the camera frame tracks dynamically downward to follow the march while fitting the awaiting defenders.
2. **Tactical Battlefield Cartography (No Macro Country Maps)**: For specific battles, render true **tactical battlefield plates** rather than generic country borders. Maps must feature local terrain: rivers, fords, tidal marshes, elevation ridges, earthworks, citadels, and approach routes.
3. **Formation Boxes & Troop Advances (No Arrows)**: Rectangular army boxes with unit symbols (infantry, cavalry, archer, chariot, elephant). Troop movement is conveyed strictly via animated formation boxes (`motions`) with dashed path trails, **never** directional arrows.
4. **Historical Flags**: Period-accurate flag rendering mounted with flagstaffs directly on army formation boxes (`assets/flags/<side>.png`).
5. **Period-Appropriate Combat (No Bombing in Antiquity/Medieval)**:
   - **Gunpowder Era (16th c. onwards)**: Use `type: "artillery"` for siege batteries, wall breaches, and cannon fire.
   - **Pre-Gunpowder Antiquity & Medieval Warfare**: **Never** draw artillery fireballs, smoke rings, or bomb blasts. Use `type: "clash"` for tactical melee sparks, dust pulses, and crossing blade flashes representing cavalry, infantry, and elephant collisions.
6. **Pre-Deployed Defending Armies**: When the viewport shifts or pans to a defense sector, defending forces must **already be on screen and ready in battle array** (e.g. elephant lines screening the center, cavalry on the wings, infantry entrenched). Defending armies never pop in from nowhere.
7. **Army Sizes, Leadership & Casualty Accountability**: Explicitly display commanders, troop numbers, and casualty tolls (who led, who fell, and how much each side suffered) in labels, narration, and cards.
8. **Disappearing Routed Armies**: When an army is crushed, its formation box executes an alpha dissolve (`alpha: 0.0`) and is purged entirely from subsequent scenes.
9. **Mandatory Burned Subtitles**: Subtitles are **strictly required** on every scene, burned into the lower 20% viewport band. Zero placeholder UI badges like `"CAPTIONS ONLY"`.

---

## 2. Battlefield Cartography vs Macro Country Maps

- **Specific Battles Require Battlefield Plates**: Do not substitute a tactical engagement with a continental or country border map.
- **Topographical Elements**:
  - Waterways: Multi-tier blue styling (`#102a45` deep bed, `#25689e` main channel, `#4ea2de` flow core).
  - Obstacles: Marshes, tidal mudflats, river fords, elevation contours.
  - Fortifications: Citadel polygons, bastion towers, defense earthworks, palisades.
  - Scale: Include a dedicated tactical scale bar (e.g., 0 to 3.0 km) and compass rose.

---

## 3. Dynamic Camera & Pre-Deployed Formations

- **Tracking Directional Advances**: When an invading host advances across long distances (e.g. marching southwards from northern staging grounds):
  ```json
  "camera": {
    "start": {"cx": 0.50, "cy": 0.28, "zoom": 0.70},
    "end": {"cx": 0.50, "cy": 0.44, "zoom": 0.75}
  }
  ```
- **Defenders Pre-Deployed**: The defending army must be listed in `"show"` and placed in its entrenched coordinates before the enemy arrives.

---

## 4. Pre-Gunpowder Melee vs Gunpowder Sieges

- **Strict Historical Era Separation**:
  ```json
  "effects": [
    {
      "type": "clash",
      "marker": "navsari_ford",
      "t0": 0.15,
      "t1": 0.85,
      "intensity": 0.95
    }
  ]
  ```
- `type: "clash"` generates a tactical gold/amber melee engagement ring and crossing spark flash. It omits black smoke, fireballs, and artillery craters.

---

## 5. Force Counts, Leadership & Casualty Accountability

- **Formation Detail Tags**:
  - Winner: `"detail": "~35,000 | Victorious (~6,000 casualties)"`
  - Loser: `"detail": "~45,000 | Annihilated (~25,000+ casualties)"`
- **Fallen Commanders**: When a commander is killed or routed:
  ```json
  "overrides": {
    "enemy_general": {
      "keys": [
        {"t": 0.40, "mark": "killed", "detail": "killed in action (~25,000+ casualties)"}
      ]
    },
    "enemy_army": {
      "keys": [
        {"t": 0.0, "alpha": 1.0},
        {"t": 0.45, "alpha": 1.0},
        {"t": 0.75, "alpha": 0.0}
      ]
    }
  }
  ```

---

## 6. Render & Validation Pipeline

1. **Smoke Preview**:
   ```bash
   python3 -m hde render documentaries/<id>.json --preview
   ```
2. **Production 720p Render**:
   ```bash
   python3 -m hde render documentaries/<id>.json
   ```
3. **Conformance Validation**:
   ```bash
   python3 -m hde validate output/<id>_720p.mp4 --width 1280 --height 720 --fps 24 --duration <sec>
   ```

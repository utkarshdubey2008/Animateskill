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

## 6. Multi-Box Formations & Vanguard Screening

- **Monarch / General Rear Command Position**: The monarch or supreme commander is rendered as a circular portrait figure (`role: "person"`, circular portrait) positioned in the rear tactical reserve or headquarters line. Both opposing commanders must remain fully within the active screen viewport across all scenes.
- **3 Rectangular Plain Boxes Ahead**: Deploy exactly 3 rectangular plain formation boxes ahead of the monarch's position to represent tactical echelons (e.g. Left Flank, Center Shock Line, Right Flank).
  - **Sizing**: Compact and proportional (`~46x24` px at 720p), never oversized.
  - **Plain Styling**: No flags, banners, unit icons, or text labels on the army boxes.
  - **Bold / Gradient Color**: Rich vertical linear gradient with luminous edge bevel and crisp saturated border matching the faction palette.
- **Advancing Formation Waves**: Animate movement using scene `motions` interpolating positions across keyframes, moving formation boxes forward into combat contact while both leaders stay in-frame.

---

## 7. Box Destruction: Fragmentation & Vaporization

- **Loss Mechanics Without Anachronistic Gunpowder Blasts**: In ancient and medieval warfare, defeating an army unit must not use cannonballs or explosives. Instead, unit destruction is visualized via structural disintegration:
- **Destruction Marks**: Set `"mark": "shattered"`, `"destroyed"`, or `"vaporized"` in unit keyframes.
- **Visual Rendering**:
  - The rectangular formation box splits into 4 angular polygonal shards flying outward along expansion vectors.
  - Fracture seams (jagged white/amber fracture lines) cut through the unit boundary.
  - A cloud of high-velocity dispersing ember and dust particles radiates outward from the unit centroid.
  - Box opacity fades out as fragments expand, cleanly dissolving the defeated division from the field.

---

## 8. Horizontal Tactical Forces & Casualty HUD

- **Scoreboard Box Layout**: Positioned on the left side of the screen (`x: 24`, `y: 82`), horizontal, sleek, and compact (`width: ~500px`, `height: ~54px`), leaving the central battlefield open.
- **Side-by-Side Party Columns**: Rather than stacking parties vertically, place combatant cards side-by-side separated by a vertical divider line.
- **Top-Level Documentary Schema**:
  ```json
  "parties": [
    {
      "name": "Chalukya-Lata (Pulakeshin)",
      "side": "chalukya",
      "army_size": "~35,000",
      "killed": "~6,000"
    },
    {
      "name": "Umayyad Caliphate (Al-Hakam)",
      "side": "umayyad",
      "army_size": "~45,000",
      "killed": "~25,000+ (ANNIHILATED)"
    }
  ]
  ```
- **HUD Components**:
  - Translucent glass HUD card (`rgba(8, 12, 16, 0.85)` with subtle steel blue border).
  - Gold accent tag with `"FORCES & CASUALTIES"`.
  - Mini flag thumbnails mounted beside party names.
  - Force size and casualty metrics on each horizontal column.

---

## 9. Silent Video & Custom Audio Decoupling

- When custom audio is added separately by the user:
  - Set `"audio_file": null` in documentary narration config.
  - The render pipeline creates a pristine silent AAC audio stream conforming to strict MP4 container validation without placeholder badges.

---

## 9. Commander Elimination (Regicide Execution)

- **Victorious Advance Overrun**: After the forward 3–5 enemy formation boxes are shattered and vaporized, the victorious division boxes advance directly into the enemy rear command position.
- **Leader Termination**: The opposing commander circle is stamped with `"mark": "killed"`, drawing a heavy crimson saltire cross (`X`) with glowing red perimeter, updating the status label to `"killed in action"`.

---

## 10. Render & Validation Pipeline

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

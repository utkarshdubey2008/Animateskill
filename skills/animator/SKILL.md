---
name: animator
description: >
  Unified military history animation skill: plan and render silent, subtitled schematic
  documentaries and battle maps from prompts, scripts, commander portraits, and SVG territory
  plates. Encapsulates scene choreography, map plate generation, moving tactical army boxes
  with historical flags (without directional arrows), multi-stage artillery bombardments,
  casualty cross markers, and burned subtitles with silent AAC validation.
---

# Animator — Unified Historical Battle Animation Skill

## 1. Overview & Architecture

`animator` is the master animation and documentary framework for rendering silent, subtitled historical military documentaries and tactical battle maps. It consolidates all sub-disciplines into an automated, reproducible pipeline:

1. **Choreography & Camera**: Scene timing, camera windows (`start`/`end` with `cx`, `cy`, `zoom`), easing curves, and dissolve transitions. Supports dynamic panning or locked static tactical views.
2. **Cartography & Waterways**: High-contrast 1600×900 SVG plates, territory fills, geographic features, and prominent multi-tier blue river channels (`#25689e`, `#12304d`, `#4899d9`).
3. **Tactical Formations & Advances (No Arrows)**: Rectangular army boxes with unit symbols (infantry, cavalry, archer, chariot, elephant). Troop movement is conveyed strictly via animated formation boxes (`motions`) with dashed path trails, **never** directional arrows.
4. **Historical Flags**: Period-accurate flag rendering mounted with flagstaffs directly on army formation boxes (`assets/flags/<side>.png`).
5. **Artillery Bombardments**: Multi-stage explosive bursts with shockwaves, smoke rings, fiery flame cores, and jitter.
6. **Casualty Indicators**: Red diagonal cross (`mark: "killed"`) rendered over fallen commanders or routed units.
7. **Silent Subtitles (Burned)**: Subtitles are **strictly mandatory**. The user's script is burned directly onto the lower 20% of the screen. Zero synthesized voice, zero music, zero sound effects. No placeholder UI badges like `"CAPTIONS ONLY"`.

---

## 2. Mandatory Burned Subtitles & Audio Architecture

- **Subtitles are strictly required**: Every scene must have a burned-in subtitle drawn from the user's narration script. Subtitles carry the entire storyline.
- **Silent Audio**: The final video container muxes a silent stereo AAC track (`-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100`). No synthetic TTS (`flite`), no music, no audio sound effects.
- **Screen Placement**: Subtitles are rendered in the lower 20% viewport band (`y > 0.80`), left-aligned or centered, using high-contrast bold white type with a dark drop-shadow. An optional one-line disclaimer (e.g. `Schematic, not a survey.`) sits beneath.
- **Clean UI**: Never draw placeholder badges, watermarks, or `"CAPTIONS ONLY"` badges in the corner. The screen remains clean and cinematic.

---

## 3. Troop Movements: Moving Boxes Over Arrows

- **Never use directional movement arrows for troop advance**: Arrows clutter the tactical view and obscure terrain. 
- **Advance Mechanics**: Use moving formation boxes defined under `motions`:
  ```json
  "motions": {
    "british_army": {
      "confidence": "illustrative",
      "keys": [
        {"t": 0.10, "x": 0.14, "y": 0.46},
        {"t": 0.80, "x": 0.28, "y": 0.47}
      ]
    }
  }
  ```
- **Path Trails**: The rendering engine automatically draws dashed trajectory lines (`Illustrative advance`) tracking the formation from origin to destination as `t` advances. Both opposing armies move forward into engagement during clash scenes.

---

## 4. Historical Flags

- **Period-Accurate Flags**: Stored as PNG assets in `assets/flags/<side>.png` (e.g., `british.png` for 1707–1800 King's Colours, `mysore.png` for the green/gold Khudadad State flag).
- **Mounting**: When `marker.role == "army"`, the engine automatically mounts the side's flag on a clean white/silver flagstaff above the upper edge of the formation box:
  - Width: ~34px scaled.
  - Height: ~22px scaled.
  - Position: Attached above the anchor edge, waving slightly or crisply displayed.

---

## 5. Artillery Bombardments & Explosions

- **Multi-Stage Fire & Shockwave**: Bombardments are declared in scene `effects`:
  ```json
  "effects": [
    {
      "type": "artillery",
      "marker": "the_breach",
      "t0": 0.05,
      "t1": 0.95,
      "intensity": 1.0
    }
  ]
  ```
- **Visual Breakdown**:
  1. **Shockwave Ring**: Outer expanding translucent blast circle (radius up to 45px).
  2. **Smoke / Debris Ring**: Mid-tier dark charcoal particulate ring.
  3. **Fireball Core**: Fiery orange-red expanding explosion (`#ff5500` / `#ff7722`) with random frame-to-frame blast jitter.
  4. **Hot Ignition Core**: Bright incandescent yellow-white center burst (`#ffee88`).

---

## 6. Casualty & Killed Indicators

- **Casualty Cross**: When a commander is killed or a unit eliminated, specify `mark: "killed"` in marker overrides or motion keyframes:
  ```json
  "overrides": {
    "tipu": {
      "keys": [
        {"t": 0.45, "mark": "killed", "detail": "killed in action"}
      ]
    }
  }
  ```
- **Visual Presentation**: A bold, blood-red diagonal cross `X` (`#e02424`) with a dark border is rendered directly across the commander's circular portrait or army formation box, immediately indicating fatal casualties.

---

## 7. Cartography & Waterway Styling

- **Tactical Plates vs Imperial Maps**:
  - For broad territorial campaigns: Use colored SVG region fills (e.g., Mauryan red vs Seleucid blue).
  - For tactical battles and sieges: Use uncolored slate plates (`#1a1f26`) with crisp rampart outlines to keep focus on formations.
- **Water Channels**: Rivers (like the Cauvery) must never blend into the terrain. Render with multi-tiered blue styling:
  - Deep riverbed: `#12304d` (thick base stroke).
  - Main channel: `#25689e` (vibrant blue stroke).
  - Flow highlights: `#4899d9` (fine interior lines).

---

## 8. Camera Controls: Dynamic Pan vs Static Lock

- **Dynamic Panning**: Set differing `start` and `end` camera windows to follow advances across wide battlefields.
- **Static Lock**: For compact siege operations or localized breach assaults, lock the camera to prevent disorienting pans:
  ```json
  "camera": {
    "start": {"cx": 0.36, "cy": 0.46, "zoom": 0.65},
    "end": {"cx": 0.36, "cy": 0.46, "zoom": 0.65}
  }
  ```

---

## 9. Render & Validation Pipeline

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
   Requires: H.264 stream, AAC audio stream (silent), exact frame count, and exit code 0.

# Scene contract

The checked-in loader accepts the fields in `docs/renderer.md`. The shots in this skill library need the optional fields below. Add them to `hde/model.py` and `hde/frame.py` when a film uses them. Unknown fields other than these still fail the load. Old films that omit them must still load. Keep `python3 -m unittest tests.test_engine -v` passing.

## Marker fields to add

| Field | Meaning |
| --- | --- |
| `role` | `person` or `army`. A person is a circle. An army is a square box. |
| `image` | Path to a square portrait, or `null`. Persons only. |
| `symbol` | `infantry`, `cavalry`, `archer`, `chariot`, or `elephant`. Repeat the marker, or pass a list, for each arm in that box. Armies only. |
| `attach` | An army marker id. A person with `attach` follows that army. |
| `offset` | `[dx, dy]` in map units. The person's place is the army's place plus this offset. Use about `[0, 0.045]` or `[0, -0.045]` so the circle sits on the home side of the box. |

`x` and `y` on the marker are the resting place. Override keys still cannot carry `x` or `y`. Movement is the `motions` block.

## Motions

```json
"motions": {
  "northern-army": {
    "confidence": "illustrative",
    "keys": [
      {"t": 0.12, "x": 0.50, "y": 0.36},
      {"t": 0.82, "x": 0.50, "y": 0.46}
    ]
  }
}
```

`t` is the fraction of that scene. Before the first key, the marker is at the first key. After the last key, it stays at the last key. Two keys are a straight move. A bend is another key. An attached person does not get a separate motion.

Draw a dashed trail from the first key to the current point when `confidence` is `illustrative`.

The next scene that shows the unit begins with a key at `t` 0 at the previous scene's end point.

## Territory layers

```json
"layers": [
  {"id": "region-example", "t": 0.40, "fill": "#c4a46a"}
]
```

`id` matches the SVG path id. At that scene-local `t`, the fill changes. The renderer today rasterizes one SVG for the whole film, so this field has to be implemented before a border can change on screen.

## Subtitles

`narration` is the burned subtitle and uses the user's spelling. `speech` stays a non-empty ASCII string because the loader requires it. Nothing reads `speech` aloud under the default silence render.

# Renderer

The silent renderer lives in `hde/`. Run it from the repository root.

```bash
python3 -m hde render documentaries/<slug>.json --stills-only --stills 4,14,28
python3 -m hde render documentaries/<slug>.json --preview
python3 -m hde render documentaries/<slug>.json
python3 -m hde validate output/<slug>_720p.mp4 --width 1280 --height 720 --fps 24 --duration <seconds>
```

Silence is the default. Subtitles still burn from each scene's `narration`. `--preview` writes `output/<slug>_preview.mp4` at 640×360, 12 fps. A full render uses the JSON size, normally 1280×720 at 24 fps, CRF 18, preset `veryfast`, two encoder threads.

The log prints `result: OK` and `OUTPUT_PATH=...` when the file is valid. Report that path only after both lines appear. The log must not say `flite`.

## What a documentary file contains today

`schema_version` 1. Unknown fields raise. The id is a lowercase slug. Width and height are even. `fps` is an integer from 1 to 60.

Scenes start at 0, meet exactly, and the last ends at `duration_s`. For a dissolve, scene N `camera.end` equals scene N+1 `camera.start`.

Markers are points. `attested_area` is a filled dot. `approximate` is a hollow dot. Anchors are `n`, `s`, `e`, `w`. Overrides may change `detail`, `mark` (`killed` only), and `alpha`. They may not change `x` or `y`.

Arrows are the motion the current code draws. `illustrative` arrows are dashed. The label starts with `Illustrative `. `t0` and `t1` are scene fractions.

Effects are `rain` and `artillery`. Overlays are `card`. `sources` is a non-empty list of `{id, text, refs}`.

The map is one SVG, rasterized once per film to `output/cache/<id>_2400x1350.png` for a 720p film. A newer SVG mtime rebuilds it.

Circle portraits, army boxes, unit symbols, attached commanders, moving boxes, and territory fill changes are specified in `docs/scene-contract.md`. Implement them in `hde/` when the film uses them. Do not remove the silence default to do that.

`documentaries/plassey.json` is a finished silent-capable example of the current loader. Its tests lock the 55 second cut. A new war is a new JSON and a new SVG.

"""Render a documentary JSON file to stills or an H.264 MP4."""

from __future__ import annotations

import gc
import os
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from hde.audio import prepare_audio
from hde.encode import encode_mp4
from hde.fonts import load_font_paths
from hde.frame import FrameContext, compose_scene, make_scrim
from hde.geom import smoothstep
from hde.model import Documentary, frame_count, load_documentary, local_t, scene_index_at
from hde.model import assign_ranges
from hde.raster import rasterize_svg
from hde.validate import validate_mp4

PREVIEW_SIZE = (640, 360)
PREVIEW_FPS = 12


@dataclass
class RenderSettings:
    width: int
    height: int
    fps: int
    crf: int
    preset: str
    output: Path | None = None
    preview: bool = False
    max_frames: int | None = None
    stills: tuple[float, ...] = ()
    stills_only: bool = False
    silence: bool = False
    threads: int = 2


def render_documentary(doc_path: Path, settings: RenderSettings) -> Path | None:
    try:
        os.nice(5)
    except OSError:
        pass
    doc = load_documentary(doc_path)
    width, height, fps = settings.width, settings.height, settings.fps
    nframes = frame_count(doc.duration_s, fps)
    if settings.max_frames is not None:
        if settings.max_frames < 1:
            raise ValueError("max_frames must be at least 1")
        nframes = min(nframes, settings.max_frames)
    ranges = assign_ranges(doc.scenes, fps, frame_count(doc.duration_s, fps))
    raster_w, raster_h = (2400, 1350) if height >= 720 else (1280, 720)
    cache_png = doc.root / "output" / "cache" / f"{doc.id}_{raster_w}x{raster_h}.png"
    print(f"documentary: {doc.id}")
    print(f"frame: {width}x{height} @ {fps} fps, {nframes} frames, {nframes / fps:.3f}s")
    print(f"map raster: {raster_w}x{raster_h}")
    base = rasterize_svg(doc.map_svg, raster_w, raster_h, cache_png)
    ctx = FrameContext(
        doc=doc,
        base=base,
        width=width,
        height=height,
        fps=fps,
        fonts=load_font_paths(),
        scrim=make_scrim(width, height),
        black=Image.new("RGB", (width, height), (0, 0, 0)),
        storm=Image.new("RGB", (width, height), (26, 38, 48)),
        badge=None,
    )
    if settings.stills_only:
        ctx.badge = "CAPTIONS ONLY" if settings.silence else "PLACEHOLDER VOICE"
        _write_stills(ctx, doc, ranges, fps, settings.stills)
        return None

    duration_s = nframes / fps
    audio = prepare_audio(doc, duration_s, settings.silence, doc.root / "output" / "cache" / "audio")
    ctx.badge = audio.badge
    print(f"audio: {audio.description}")
    output = settings.output or _default_output(doc, settings.preview)
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"encoding: {output}")
    started = time.monotonic()
    cache: dict = {}

    def frames():
        for frame_i in range(nframes):
            image = produce_frame(ctx, doc, frame_i, ranges, cache)
            if frame_i in still_frames:
                _save_still(doc, image, frame_i / fps)
            if frame_i % fps == 0 or frame_i == nframes - 1:
                scene = doc.scenes[scene_index_at(ranges, frame_i)]
                print(f"frame {frame_i + 1}/{nframes}  {scene.id}", flush=True)
            if frame_i % 120 == 0:
                gc.collect()
            yield image

    still_frames = {min(nframes - 1, max(0, round(second * fps))) for second in settings.stills}
    try:
        encode_mp4(
            frames(),
            nframes,
            audio.path,
            width,
            height,
            fps,
            output,
            settings.crf,
            settings.preset,
            settings.threads,
        )
    except Exception:
        if output.exists():
            output.unlink()
        raise
    elapsed = time.monotonic() - started
    print(f"rendered {nframes} frames in {elapsed:.1f}s ({nframes / max(elapsed, 0.001):.1f} fps)")
    if nframes < fps:
        min_bytes = 500
    elif height >= 720 and nframes >= fps * 10:
        min_bytes = 150_000
    else:
        min_bytes = 8_000
    report = validate_mp4(
        output,
        width=width,
        height=height,
        fps=fps,
        duration=duration_s,
        min_bytes=min_bytes,
    )
    print(report.text())
    if not report.ok:
        raise RuntimeError(f"validation failed for {output}")
    print(f"OUTPUT_PATH={output}")
    return output


def produce_frame(ctx: FrameContext, doc: Documentary, frame_i: int, ranges, cache: dict) -> Image.Image:
    index = scene_index_at(ranges, frame_i)
    start, end = ranges[index]
    scene = doc.scenes[index]
    image = compose_scene(ctx, scene, local_t(frame_i, start, end), frame_i)
    transition_frames = int(round(scene.transition_s * ctx.fps))
    age = frame_i - start
    if scene.transition_in == "cut" or transition_frames <= 0 or age >= transition_frames or age < 0:
        return image
    weight = 1.0 - smoothstep(age / transition_frames)
    if weight <= 0:
        return image
    if scene.transition_in == "dissolve" and index > 0:
        previous = _scene_end(ctx, doc, ranges, index - 1, cache)
        return Image.blend(image, previous, weight)
    return Image.blend(image, ctx.black, weight)


def _scene_end(ctx: FrameContext, doc: Documentary, ranges, index: int, cache: dict) -> Image.Image:
    if cache.get("idx") == index:
        return cache["img"]
    start, end = ranges[index]
    frame_i = end - 1
    image = compose_scene(ctx, doc.scenes[index], local_t(frame_i, start, end), frame_i)
    cache["idx"] = index
    cache["img"] = image
    return image


def _write_stills(ctx, doc, ranges, fps: int, stills: tuple[float, ...]) -> None:
    if not stills:
        raise ValueError("stills-only render needs at least one timestamp")
    total = frame_count(doc.duration_s, fps)
    cache: dict = {}
    for second in stills:
        frame_i = min(total - 1, max(0, round(second * fps)))
        image = produce_frame(ctx, doc, frame_i, ranges, cache)
        _save_still(doc, image, second)


def _save_still(doc: Documentary, image: Image.Image, second: float) -> Path:
    directory = doc.root / "output" / "stills"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{doc.id}_{second:.1f}s.png"
    image.save(path, format="PNG")
    print(f"still: {path}")
    return path


def _default_output(doc: Documentary, preview: bool) -> Path:
    kind = "preview" if preview else "720p"
    return doc.root / "output" / f"{doc.id}_{kind}.mp4"

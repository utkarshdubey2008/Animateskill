"""Command line for the historical documentary renderer."""

from __future__ import annotations

import argparse
from pathlib import Path

from hde.render import PREVIEW_FPS, PREVIEW_SIZE, RenderSettings, render_documentary
from hde.validate import validate_mp4


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hde",
        description="Render a schematic historical documentary to an H.264 MP4.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render", help="render a documentary JSON file")
    render.add_argument("documentary", type=Path)
    render.add_argument("-o", "--output", type=Path)
    render.add_argument("--preview", action="store_true", help="640x360 at 12 fps")
    render.add_argument("--stills", default="", help="comma-separated timestamps in seconds")
    render.add_argument("--stills-only", action="store_true", help="write PNG stills and skip the MP4")
    render.add_argument("--max-frames", type=int, help="stop after this many frames")
    render.add_argument(
        "--silence",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="omit speech, music, and effects (default). Subtitles still burn in.",
    )
    render.add_argument("--crf", type=int)
    render.add_argument("--preset")

    check = sub.add_parser("validate", help="check an MP4 with ffprobe")
    check.add_argument("file", type=Path)
    check.add_argument("--width", type=int)
    check.add_argument("--height", type=int)
    check.add_argument("--fps", type=float)
    check.add_argument("--duration", type=float)
    check.add_argument("--tolerance", type=float, default=0.25)
    check.add_argument("--min-bytes", type=int, default=1000)

    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            return _render(args)
        return _validate(args)
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}")
        return 1


def _render(args) -> int:
    if args.preview:
        width, height = PREVIEW_SIZE
        fps = PREVIEW_FPS
        crf = args.crf if args.crf is not None else 28
        preset = args.preset or "ultrafast"
    else:
        # Canonical size lives in the JSON. These are overwritten after a peek
        # only when the caller did not ask for the preview preset.
        width, height, fps = 1280, 720, 24
        crf = args.crf if args.crf is not None else 18
        preset = args.preset or "veryfast"
    if not args.preview:
        from hde.model import load_documentary

        doc = load_documentary(args.documentary)
        width, height, fps = doc.width, doc.height, doc.fps
    stills = tuple(float(part) for part in args.stills.split(",") if part.strip())
    settings = RenderSettings(
        width=width,
        height=height,
        fps=fps,
        crf=crf,
        preset=preset,
        output=args.output,
        preview=args.preview,
        max_frames=args.max_frames,
        stills=stills,
        stills_only=args.stills_only,
        silence=args.silence,
    )
    render_documentary(args.documentary, settings)
    return 0


def _validate(args) -> int:
    report = validate_mp4(
        args.file,
        width=args.width,
        height=args.height,
        fps=args.fps,
        duration=args.duration,
        tolerance=args.tolerance,
        min_bytes=args.min_bytes,
    )
    print(report.text())
    return 0 if report.ok else 1

"""Rasterize a traceable SVG plate once and reuse it for every frame."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image


def rasterize_svg(svg: Path, width: int, height: int, cache_path: Path) -> Image.Image:
    if shutil.which("rsvg-convert") is None:
        raise RuntimeError(
            "rsvg-convert is required to rasterize map SVG assets. Install librsvg2-bin."
        )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    fresh = cache_path.is_file() and cache_path.stat().st_mtime >= svg.stat().st_mtime
    if not fresh:
        subprocess.run(
            [
                "rsvg-convert",
                "-w",
                str(width),
                "-h",
                str(height),
                "-o",
                str(cache_path),
                str(svg),
            ],
            check=True,
        )
    image = Image.open(cache_path).convert("RGB")
    if image.size != (width, height):
        raise RuntimeError(f"raster {image.size} does not match requested {(width, height)}")
    return image

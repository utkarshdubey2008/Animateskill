"""Crop a square portrait into a circle with a clean border.

The user supplies a square image. This keeps the center, masks it to a circle,
and strokes a ring in the empire color.

Usage:
  python3 skills/commander-portraits/scripts/circular_crop.py IN.png OUT.png --border "#c4a46a" --size 256
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def circular_crop(source: Path, dest: Path, size: int = 256, border: str = "#f4efe4", border_px: int = 8) -> None:
    if size < 32 or size % 2:
        raise ValueError("size must be an even integer of at least 32")
    if border_px < 1 or border_px >= size // 2:
        raise ValueError("border_px must fit inside the circle")
    image = Image.open(source).convert("RGBA")
    side = min(image.size)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    image.putalpha(mask)
    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ring)
    color = _hex(border)
    draw.ellipse((0, 0, size - 1, size - 1), outline=color + (255,), width=border_px)
    image.alpha_composite(ring)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)


def _hex(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6 or any(char not in "0123456789abcdefABCDEF" for char in text):
        raise ValueError("border must be a #RRGGBB color")
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop a square portrait into a bordered circle.")
    parser.add_argument("source", type=Path)
    parser.add_argument("dest", type=Path)
    parser.add_argument("--border", default="#f4efe4")
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument("--border-px", type=int, default=8)
    args = parser.parse_args()
    circular_crop(args.source, args.dest, args.size, args.border, args.border_px)


if __name__ == "__main__":
    main()

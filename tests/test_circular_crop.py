"""The portrait crop keeps a centered circle and a solid ring."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "commander-portraits" / "scripts" / "circular_crop.py"


def _load():
    spec = importlib.util.spec_from_file_location("circular_crop", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CircularCropTests(unittest.TestCase):
    def test_center_pixel_survives_and_corner_is_clear(self):
        module = _load()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "square.png"
            dest = Path(tmp) / "circle.png"
            image = Image.new("RGBA", (80, 120), (10, 20, 30, 255))
            image.putpixel((40, 60), (200, 10, 10, 255))
            image.save(source)
            module.circular_crop(source, dest, size=64, border="#e2b15a", border_px=4)
            cropped = Image.open(dest).convert("RGBA")
            self.assertEqual(cropped.size, (64, 64))
            self.assertEqual(cropped.getpixel((0, 0))[3], 0)
            self.assertGreater(cropped.getpixel((32, 32))[3], 200)
            edge = cropped.getpixel((32, 2))
            self.assertGreater(edge[3], 200)
            self.assertGreater(edge[0], 180)

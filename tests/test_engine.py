"""Schema, confidence rules, camera math, and a four-frame encode."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hde.geom import camera_window, crop_box, project, pulse, smoothstep
from hde.model import assign_ranges, frame_count, load_documentary
from hde.render import RenderSettings, render_documentary
from hde.validate import validate_mp4

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "documentaries" / "plassey.json"


class GeometryTests(unittest.TestCase):
    def test_full_frame_centers_the_map(self):
        map_w, map_h = 1600, 900
        out_w, out_h = 1280, 720
        window = camera_window(0.5, 0.5, 1.0, map_w, map_h, out_w / out_h)
        box = crop_box(window, map_w, map_h)
        sx, sy = project(0.5, 0.5, box, out_w, out_h, map_w, map_h)
        self.assertAlmostEqual(sx, 640, delta=2)
        self.assertAlmostEqual(sy, 360, delta=2)

    def test_camera_clamps_to_the_plate(self):
        left, top, view_w, view_h = camera_window(0.0, 0.5, 0.5, 1600, 900, 16 / 9)
        self.assertEqual(left, 0)
        self.assertGreater(view_w, 0)
        self.assertGreater(view_h, 0)
        self.assertLessEqual(top + view_h, 900)

    def test_easing_endpoints(self):
        self.assertEqual(smoothstep(0), 0)
        self.assertEqual(smoothstep(1), 1)
        self.assertEqual(pulse(0.5, 0.2, 0.8), 1)
        self.assertEqual(pulse(0.0, 0.2, 0.8), 0)


class PlasseyDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_documentary(DOC)

    def test_five_beats_cover_fifty_five_seconds(self):
        doc = self.doc
        self.assertEqual(doc.duration_s, 55)
        self.assertEqual(doc.width, 1280)
        self.assertEqual(doc.height, 720)
        self.assertEqual(doc.fps, 24)
        self.assertEqual(
            [scene.id for scene in doc.scenes],
            ["assemble", "battle", "rain", "withdrawal", "consequences"],
        )
        nframes = frame_count(doc.duration_s, 24)
        ranges = assign_ranges(doc.scenes, 24, nframes)
        self.assertEqual(nframes, 1320)
        self.assertEqual(ranges[0][0], 0)
        self.assertEqual(ranges[-1][1], 1320)
        for earlier, later in zip(ranges, ranges[1:]):
            self.assertEqual(earlier[1], later[0])
            self.assertGreater(earlier[1], earlier[0])
        preview = assign_ranges(doc.scenes, 12, frame_count(55, 12))
        self.assertEqual(preview[-1][1], 660)

    def test_cameras_meet_so_dissolves_do_not_jump(self):
        for earlier, later in zip(self.doc.scenes, self.doc.scenes[1:]):
            self.assertAlmostEqual(earlier.camera_end.cx, later.camera_start.cx)
            self.assertAlmostEqual(earlier.camera_end.cy, later.camera_start.cy)
            self.assertAlmostEqual(earlier.camera_end.zoom, later.camera_start.zoom)

    def test_movement_is_only_illustrative_arrows(self):
        arrows = [arrow for scene in self.doc.scenes for arrow in scene.arrows]
        self.assertGreaterEqual(len(arrows), 2)
        ids = {arrow.id for arrow in arrows}
        self.assertIn("advance", ids)
        self.assertIn("withdrawal", ids)
        for arrow in arrows:
            self.assertEqual(arrow.confidence, "illustrative")
            self.assertTrue(arrow.label.lower().startswith("illustrative"))
        # Marker positions are single points. Overrides cannot smuggle coordinates.
        self.assertTrue(all(marker.confidence in {"attested_area", "approximate"} for marker in self.doc.markers.values()))

    def test_sources_and_plate_are_traceable(self):
        ids = {note.id for note in self.doc.sources}
        self.assertTrue({"geography", "strengths", "conspiracy", "rain", "casualties", "aftermath"} <= ids)
        self.assertIn("Original schematic", self.doc.map_attribution)
        self.assertTrue(self.doc.map_svg.is_file())
        description = self.doc.map_svg.read_text(encoding="utf-8")
        self.assertIn("Original schematic", description)
        self.assertIn("illustrative", description)

    def test_rejects_a_gap_and_a_moving_override(self):
        raw = json.loads(DOC.read_text(encoding="utf-8"))
        raw["scenes"][1]["start_s"] = 13
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(raw, handle)
            broken = Path(handle.name)
        try:
            with self.assertRaises(ValueError):
                load_documentary(broken)
        finally:
            broken.unlink()
        raw = json.loads(DOC.read_text(encoding="utf-8"))
        raw["scenes"][1]["overrides"] = {"clive": {"x": 0.1, "keys": [{"t": 0, "alpha": 1}]}}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(raw, handle)
            moved = Path(handle.name)
        try:
            with self.assertRaises(ValueError):
                load_documentary(moved)
        finally:
            moved.unlink()


class SmokeRenderTests(unittest.TestCase):
    def test_four_frames_encode_to_h264(self):
        dest = ROOT / "output" / "cache" / "smoke.mp4"
        if dest.exists():
            dest.unlink()
        settings = RenderSettings(
            width=320,
            height=180,
            fps=8,
            crf=32,
            preset="ultrafast",
            output=dest,
            max_frames=4,
            silence=True,
        )
        path = render_documentary(DOC, settings)
        self.assertEqual(path, dest)
        report = validate_mp4(dest, width=320, height=180, fps=8, duration=0.5, min_bytes=500)
        self.assertTrue(report.ok, report.text())
        dest.unlink()


if __name__ == "__main__":
    unittest.main()

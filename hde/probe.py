"""Small ffprobe wrapper used by audio fitting and MP4 validation."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def require_ffmpeg() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise RuntimeError("required program not found: " + ", ".join(missing))


def ffprobe(path: Path) -> dict:
    require_ffmpeg()
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def media_duration(path: Path) -> float:
    payload = ffprobe(path)
    return float(payload["format"]["duration"])


def parse_rate(value: str) -> float:
    if not value or value == "0/0":
        return 0.0
    num, den = value.split("/")
    denominator = float(den)
    if denominator == 0:
        return 0.0
    return float(num) / denominator

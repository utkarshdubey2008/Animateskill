"""Check that a rendered MP4 matches the documentary contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from hde.probe import ffprobe, parse_rate


@dataclass
class ValidationReport:
    ok: bool
    lines: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def text(self) -> str:
        body = "\n".join(self.lines)
        if self.errors:
            body += "\n" + "\n".join(f"error: {item}" for item in self.errors)
        body += "\nresult: " + ("OK" if self.ok else "FAIL")
        return body


def validate_mp4(
    path: Path,
    width: int | None = None,
    height: int | None = None,
    fps: float | None = None,
    duration: float | None = None,
    tolerance: float = 0.25,
    min_bytes: int = 1000,
) -> ValidationReport:
    report = ValidationReport(ok=True)
    path = Path(path)
    if not path.is_file():
        return _fail(report, [f"file not found: {path}"])
    size = path.stat().st_size
    report.lines.append(f"path: {path}")
    report.lines.append(f"size: {size} bytes")
    if size < min_bytes:
        report.errors.append(f"file is smaller than {min_bytes} bytes")
    try:
        payload = ffprobe(path)
    except Exception as exc:  # ffprobe already explains a broken file
        report.errors.append(f"ffprobe failed: {exc}")
        report.ok = False
        return report

    format_name = payload.get("format", {}).get("format_name", "")
    report.lines.append(f"container: {format_name}")
    if "mp4" not in format_name and "mov" not in format_name:
        report.errors.append(f"container is {format_name or 'unknown'}, expected mp4")

    video = _stream(payload, "video")
    audio = _stream(payload, "audio")
    if video is None:
        report.errors.append("no video stream")
    else:
        codec = video.get("codec_name")
        pix = video.get("pix_fmt")
        got_w = int(video.get("width", 0))
        got_h = int(video.get("height", 0))
        rate = parse_rate(str(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/0"))
        report.lines.append(f"video: {codec} {got_w}x{got_h} {rate:.3f} fps {pix}")
        if codec != "h264":
            report.errors.append(f"video codec is {codec}, expected h264")
        if pix != "yuv420p":
            report.errors.append(f"pixel format is {pix}, expected yuv420p")
        if width is not None and got_w != width:
            report.errors.append(f"width is {got_w}, expected {width}")
        if height is not None and got_h != height:
            report.errors.append(f"height is {got_h}, expected {height}")
        if fps is not None and abs(rate - fps) > 0.05:
            report.errors.append(f"fps is {rate:.3f}, expected {fps:.3f}")
    if audio is None:
        report.errors.append("no audio stream")
    else:
        report.lines.append(
            f"audio: {audio.get('codec_name')} {audio.get('sample_rate')} Hz "
            f"{audio.get('channels')} ch"
        )
        if audio.get("codec_name") != "aac":
            report.errors.append(f"audio codec is {audio.get('codec_name')}, expected aac")

    got_duration = float(payload.get("format", {}).get("duration", 0) or 0)
    report.lines.append(f"duration: {got_duration:.3f} s")
    if duration is not None and abs(got_duration - duration) > tolerance:
        report.errors.append(
            f"duration is {got_duration:.3f}s, expected {duration:.3f}s ± {tolerance:.2f}s"
        )
    report.ok = not report.errors
    return report


def _stream(payload: dict, kind: str) -> dict | None:
    for stream in payload.get("streams", []):
        if stream.get("codec_type") == kind:
            return stream
    return None


def _fail(report: ValidationReport, errors: list[str]) -> ValidationReport:
    report.errors.extend(errors)
    report.ok = False
    return report

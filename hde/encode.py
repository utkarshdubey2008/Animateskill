"""Stream raw frames to FFmpeg. One frame is resident in Python at a time."""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image

from hde.probe import require_ffmpeg


def encode_mp4(
    frames,
    nframes: int,
    audio: Path,
    width: int,
    height: int,
    fps: int,
    output: Path,
    crf: int,
    preset: str,
    threads: int,
) -> None:
    require_ffmpeg()
    output.parent.mkdir(parents=True, exist_ok=True)
    log_path = output.with_suffix(".ffmpeg.log")
    duration = nframes / fps
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "warning",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "pipe:0",
        "-i",
        str(audio),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-threads",
        str(threads),
        "-g",
        str(max(1, fps * 2)),
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-t",
        f"{duration:.6f}",
        "-movflags",
        "+faststart",
        str(output),
    ]
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=log,
        )
        assert proc.stdin is not None
        try:
            written = 0
            for image in frames:
                if not isinstance(image, Image.Image):
                    raise RuntimeError("encoder expected a Pillow image")
                if image.mode != "RGB" or image.size != (width, height):
                    raise RuntimeError(f"frame is {image.mode} {image.size}, expected RGB {width}x{height}")
                proc.stdin.write(image.tobytes())
                written += 1
            if written != nframes:
                raise RuntimeError(f"wrote {written} frames, expected {nframes}")
            proc.stdin.close()
            code = proc.wait()
        except BrokenPipeError as exc:
            proc.wait(timeout=30)
            raise RuntimeError(_tail(log_path)) from exc
        finally:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
        if code != 0:
            raise RuntimeError(f"ffmpeg exited {code}\n{_tail(log_path)}")


def _tail(path: Path, lines: int = 40) -> str:
    if not path.is_file():
        return "ffmpeg produced no log"
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(text[-lines:])

"""Narration track. A recorded file replaces the placeholder voice."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

from hde.model import Documentary, Scene
from hde.probe import media_duration, require_ffmpeg

RATE = 44100
LEAD_S = 0.25
# Bump when the placeholder processing changes so the cache rebuilds.
AUDIO_REV = "v1"
MAX_ATEMPO = 1.15


@dataclass
class AudioTrack:
    path: Path
    badge: str | None
    description: str


def prepare_audio(doc: Documentary, duration_s: float, silence: bool, cache_dir: Path) -> AudioTrack:
    """Build a WAV that is exactly `duration_s` long."""
    require_ffmpeg()
    cache_dir.mkdir(parents=True, exist_ok=True)
    if doc.audio_file is not None:
        mode, badge, description = "file", None, f"file {doc.audio_file}"
    elif silence:
        mode, badge, description = "silence", None, "silence"
    else:
        mode, badge, description = "voice", "PLACEHOLDER VOICE", f"flite voice {doc.voice}"
    dest = cache_dir / f"{doc.id}-{mode}-{duration_s:.3f}.wav"
    if _reusable(dest, duration_s):
        return AudioTrack(dest, badge, description)
    if doc.audio_file is not None:
        _fit_external(doc.audio_file, dest, duration_s)
    elif silence:
        _write_silence(dest, duration_s)
    else:
        scene_paths = [_scene_speech(doc, scene, cache_dir) for scene in doc.scenes]
        _concat(scene_paths, dest)
        actual = media_duration(dest)
        if abs(actual - duration_s) > 0.08:
            raise RuntimeError(
                f"narration duration {actual:.3f}s does not match {duration_s:.3f}s"
            )
    return AudioTrack(dest, badge, description)


def _reusable(path: Path, duration_s: float) -> bool:
    if not path.is_file() or path.stat().st_size < 44:
        return False
    try:
        return abs(media_duration(path) - duration_s) < 0.08
    except (subprocess.CalledProcessError, KeyError, ValueError):
        return False


def _scene_speech(doc: Documentary, scene: Scene, cache_dir: Path) -> Path:
    slot = scene.end_s - scene.start_s
    try:
        scene.speech.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(
            f"{scene.id}.speech must be ASCII so the placeholder voice can read it"
        ) from exc
    key = hashlib.sha256(
        f"{AUDIO_REV}|{doc.voice}|{slot:.3f}|{LEAD_S:.3f}|{scene.speech}".encode("ascii")
    ).hexdigest()[:20]
    dest = cache_dir / f"{scene.id}-{key}.wav"
    if dest.is_file():
        return dest
    raw = cache_dir / f"{scene.id}-{key}-raw.wav"
    text_path = cache_dir / f"{scene.id}-{key}.txt"
    text_path.write_text(scene.speech.strip() + "\n", encoding="ascii")
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"flite=textfile={text_path}:voice={doc.voice}",
            "-af",
            "volume=2.2",
            "-ar",
            str(RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(raw),
        ]
    )
    speech_dur = media_duration(raw)
    target = slot - LEAD_S - 0.08
    spoken = raw
    if speech_dur > target:
        ratio = speech_dur / target
        if ratio > MAX_ATEMPO:
            raise RuntimeError(
                f"{scene.id} narration is {speech_dur:.2f}s in a {slot:.2f}s scene "
                f"(would need atempo {ratio:.2f}; shorten the speech)"
            )
        sped = cache_dir / f"{scene.id}-{key}-sped.wav"
        _run_ffmpeg(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(raw),
                "-af",
                f"atempo={ratio:.5f}",
                "-ar",
                str(RATE),
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(sped),
            ]
        )
        print(f"audio {scene.id}: sped x{ratio:.3f} to fit {slot:.2f}s")
        spoken = sped
        speech_dur = media_duration(spoken)
    _fit_wav(spoken, dest, slot, LEAD_S)
    print(f"audio {scene.id}: speech {speech_dur:.2f}s in slot {slot:.2f}s")
    return dest


def _fit_wav(source: Path, dest: Path, slot_s: float, lead_s: float) -> None:
    with wave.open(str(source), "rb") as handle:
        if handle.getframerate() != RATE or handle.getnchannels() != 1 or handle.getsampwidth() != 2:
            raise RuntimeError(f"{source} is not {RATE} Hz mono s16")
        frames = handle.readframes(handle.getnframes())
    lead_n = int(round(lead_s * RATE))
    slot_n = int(round(slot_s * RATE))
    speech_n = len(frames) // 2
    if lead_n + speech_n > slot_n:
        raise RuntimeError(f"speech still exceeds the scene slot after fitting ({source})")
    tail_n = slot_n - lead_n - speech_n
    payload = (b"\x00" * (lead_n * 2)) + frames + (b"\x00" * (tail_n * 2))
    with wave.open(str(dest), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(payload)


def _fit_external(source: Path, dest: Path, duration_s: float) -> None:
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-af",
            f"apad=pad_dur={duration_s + 1:.3f},atrim=0:{duration_s:.3f}",
            "-ar",
            str(RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )


def _concat(parts: list[Path], dest: Path) -> None:
    listing = dest.with_suffix(".txt")
    lines = []
    for part in parts:
        escaped = str(part).replace("'", r"'\''")
        lines.append(f"file '{escaped}'")
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c",
            "copy",
            str(dest),
        ]
    )


def _write_silence(dest: Path, duration_s: float) -> None:
    count = int(round(duration_s * RATE))
    with wave.open(str(dest), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(b"\x00" * (count * 2))


def _run_ffmpeg(command: list[str]) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required")
    subprocess.run(command, check=True)

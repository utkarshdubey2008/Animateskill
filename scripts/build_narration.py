#!/usr/bin/env python3
import asyncio
import io
import subprocess
import wave
from pathlib import Path

import edge_tts

ROOT = Path("/root/historical-documentary-engine")
AUDIO_DIR = ROOT / "assets" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
FINAL_WAV = AUDIO_DIR / "seringapatam_narration.wav"

RATE = 44100
SCENE_DUR = 12.0
LEAD_S = 0.45

SCENES = [
    (
        "scene1",
        "In April 1799, British and allied forces under General George Harris converged on the island fortress of Seringapatam, the stronghold of Tipu Sultan, Ruler of Mysore.",
    ),
    (
        "scene2",
        "British siege batteries opened heavy fire on the western ramparts across the Cauvery River. By early May, artillery had battered a practicable breach in the fortress wall.",
    ),
    (
        "scene3",
        "At one o'clock on May fourth, Major General David Baird led the assault columns across the rocky riverbed under fire, rushing up the rubble into the breach.",
    ),
    (
        "scene4",
        "Tipu Sultan fought fiercely in the melee near the northern rampart. Trapped under the low archway of the Water Gate, the Tiger of Mysore was shot and killed in action.",
    ),
    (
        "scene5",
        "With Tipu Sultan killed, Seringapatam fell to the British. Tipu's body was recovered beneath a mound of the fallen, ending four decades of Mysorean resistance to British rule.",
    ),
]


async def generate_scene_wav(text: str, index: int) -> bytes:
    mp3_path = AUDIO_DIR / f"temp_{index}.mp3"
    wav_path = AUDIO_DIR / f"temp_{index}.wav"
    # Christopher is a classic authoritative American documentary voice
    comm = edge_tts.Communicate(text, voice="en-US-ChristopherNeural", rate="+6%")
    await comm.save(str(mp3_path))

    # Convert mp3 to 44.1kHz mono s16le wav
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(mp3_path),
            "-ar",
            str(RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(wav_path),
        ],
        check=True,
    )

    with wave.open(str(wav_path), "rb") as wf:
        nframes = wf.getnframes()
        frames = wf.readframes(nframes)

    speech_dur = nframes / RATE
    print(f"Scene {index + 1} speech duration: {speech_dur:.2f}s")

    # Fit into 12.0s slot with lead-in and trailing silence
    lead_frames = int(round(LEAD_S * RATE))
    slot_frames = int(round(SCENE_DUR * RATE))
    speech_frames = len(frames) // 2

    if lead_frames + speech_frames > slot_frames:
        raise RuntimeError(f"Scene {index + 1} speech exceeds slot: {lead_frames + speech_frames} > {slot_frames}")

    tail_frames = slot_frames - lead_frames - speech_frames
    fitted_bytes = (b"\x00" * (lead_frames * 2)) + frames + (b"\x00" * (tail_frames * 2))

    mp3_path.unlink(missing_ok=True)
    wav_path.unlink(missing_ok=True)

    return fitted_bytes


async def main():
    total_payload = b""
    for idx, (_, text) in enumerate(SCENES):
        scene_bytes = await generate_scene_wav(text, idx)
        total_payload += scene_bytes

    total_frames = len(total_payload) // 2
    total_duration = total_frames / RATE
    print(f"Total narration duration: {total_duration:.3f}s")

    with wave.open(str(FINAL_WAV), "wb") as out_wf:
        out_wf.setnchannels(1)
        out_wf.setsampwidth(2)
        out_wf.setframerate(RATE)
        out_wf.writeframes(total_payload)

    print(f"Successfully wrote {FINAL_WAV} ({FINAL_WAV.stat().st_size} bytes)")


if __name__ == "__main__":
    asyncio.run(main())

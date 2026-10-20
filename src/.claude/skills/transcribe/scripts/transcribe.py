#!/usr/bin/env python3
"""Local audio/video transcription with faster-whisper. Runs inside the skill's .venv.

Do not run this directly: ``launch.py`` prepares the environment and sets
TRANSCRIBE_DEVICE. Usage: transcribe.cmd <input_path> [output_dir]

Writes ``<stem>.txt`` (readable paragraphs) and ``<stem>.srt`` (timestamped).
"""

from __future__ import annotations

import math
import os
import shutil
import sys
import sysconfig
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
MODEL_DIR = SKILL / "models" / "whisper-large-v3-turbo-ct2"
MODEL_ALIAS = (
    "large-v3-turbo"  # faster-whisper -> mobiuslabsgmbh/faster-whisper-large-v3-turbo
)
MODEL_NAME = "whisper-large-v3-turbo"


def say(msg: str) -> None:
    print(msg, flush=True)


def model_present() -> bool:
    return (MODEL_DIR / "model.bin").exists() and (MODEL_DIR / "config.json").exists()


def ensure_model() -> None:
    """Download the weights once; every later run is offline."""
    if model_present():
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        return
    say("First use: downloading the whisper-large-v3-turbo model (~1.6 GB, once)...")
    from faster_whisper.utils import download_model

    # Into a scratch folder first, so an interrupted download is never mistaken
    # for a finished model.
    partial = MODEL_DIR.with_name(MODEL_DIR.name + ".partial")
    if partial.exists():
        shutil.rmtree(partial)
    partial.mkdir(parents=True)
    download_model(MODEL_ALIAS, output_dir=str(partial))
    if MODEL_DIR.exists():
        shutil.rmtree(MODEL_DIR)
    partial.rename(MODEL_DIR)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    say("Model downloaded. Later runs make no network calls.")


def expose_cuda_libs() -> None:
    """Make the CUDA wheels in this venv findable by ctranslate2."""
    nvidia = Path(sysconfig.get_paths()["purelib"]) / "nvidia"
    if not nvidia.is_dir():
        return
    if sys.platform == "win32":
        for bin_dir in nvidia.glob("*/bin"):
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    else:
        import ctypes

        for lib in sorted(nvidia.glob("cublas/lib/*.so*")) + sorted(
            nvidia.glob("cudnn/lib/*.so*")
        ):
            try:
                ctypes.CDLL(str(lib), mode=ctypes.RTLD_GLOBAL)
            except OSError:
                pass


def format_srt_time(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def segments_to_txt(segments) -> str:
    """Join segments into paragraphs, breaking on pauses longer than 3 seconds."""
    paragraphs: list[str] = []
    current: list[str] = []
    prev_end = None
    for seg in segments:
        if prev_end is not None and (seg.start - prev_end) > 3.0 and current:
            paragraphs.append(" ".join(current))
            current = []
        current.append(seg.text.strip())
        prev_end = seg.end
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


def segments_to_srt(segments) -> str:
    blocks = []
    for i, seg in enumerate(segments, start=1):
        blocks.append(
            f"{i}\n{format_srt_time(seg.start)} --> {format_srt_time(seg.end)}\n"
            f"{seg.text.strip()}\n"
        )
    return "\n".join(blocks)


def load_faster_whisper_cuda():
    """Return (model, device_used, compute_type), or None if the GPU won't load."""
    from faster_whisper import WhisperModel

    expose_cuda_libs()
    for compute in ("float16", "int8_float16"):
        try:
            say(f"Loading {MODEL_NAME} on cuda ({compute})...")
            return (
                WhisperModel(str(MODEL_DIR), device="cuda", compute_type=compute),
                "cuda",
                compute,
            )
        except Exception as exc:  # CUDA libs missing, out of memory, ...
            say(f"cuda {compute} failed: {exc}")
    return None


def load_faster_whisper_cpu():
    from faster_whisper import WhisperModel

    say(f"Loading {MODEL_NAME} on cpu (int8)...")
    return (
        WhisperModel(str(MODEL_DIR), device="cpu", compute_type="int8"),
        "cpu",
        "int8",
    )


# The engine seam. An engine is a loader returning (model, device_used,
# compute_type) -- or None if it cannot start -- where model.transcribe(path, ...)
# yields (segments, info) like faster-whisper's. A new engine (e.g. whisper.cpp
# on Vulkan for AMD/Intel GPUs) is one more entry here plus a branch in
# pick_engine(); nothing else changes.
ENGINES = {
    "faster-whisper-cuda": load_faster_whisper_cuda,
    "faster-whisper-cpu": load_faster_whisper_cpu,
}


def pick_engine(device: str) -> list[str]:
    """Engine names to try, in order, for the device the launcher chose."""
    if device == "cuda":
        return ["faster-whisper-cuda", "faster-whisper-cpu"]
    return ["faster-whisper-cpu"]


def load_model(device: str):
    for name in pick_engine(device):
        loaded = ENGINES[name]()
        if loaded:
            return loaded
        say("GPU unavailable; continuing on the CPU with the same model.")
    raise RuntimeError("no transcription engine could start")


def transcribe(input_path: str, output_dir: str | None) -> int:
    started = time.time()
    src = Path(input_path).resolve()
    if not src.is_file():
        print(f"ERROR: input file not found: {src}", file=sys.stderr)
        return 1
    out_dir = Path(output_dir).resolve() if output_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    txt_path = out_dir / f"{src.stem}.txt"
    srt_path = out_dir / f"{src.stem}.srt"

    ensure_model()
    model, device_used, compute_type = load_model(
        os.environ.get("TRANSCRIBE_DEVICE", "cpu")
    )

    say(f"Transcribing: {src}")
    segments_iter, info = model.transcribe(
        str(src),
        beam_size=5,
        language=None,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    segments = []
    next_report = 0.1
    for seg in segments_iter:
        segments.append(seg)
        if info.duration and seg.end / info.duration >= next_report:
            say(f"  {math.floor(seg.end / info.duration * 100)}%")
            next_report = math.floor(seg.end / info.duration * 10) / 10 + 0.1

    txt = segments_to_txt(segments)
    txt_path.write_text(txt, encoding="utf-8")
    srt_path.write_text(segments_to_srt(segments), encoding="utf-8")

    say("=" * 60)
    say("TRANSCRIPTION COMPLETE")
    say(f"Device:         {device_used} ({compute_type})")
    say(f"Model:          {MODEL_NAME}")
    say(f"Language:       {info.language} (p={info.language_probability:.2f})")
    say(f"Audio duration: {info.duration:.1f}s ({info.duration / 60:.1f} min)")
    say(f"Segments:       {len(segments)}")
    say(f"Word count:     {len(txt.split())}")
    say(f"Wall-clock:     {time.time() - started:.1f}s")
    say(f"Text:           {txt_path}")
    say(f"Subtitles:      {srt_path}")
    say("=" * 60)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    raise SystemExit(
        transcribe(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    )

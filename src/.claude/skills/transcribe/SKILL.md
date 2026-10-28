---
name: transcribe
description: Transcribe a local audio or video file (a call, meeting, interview, voice note) to text and subtitles, fully offline on this machine. Use when the owner asks to transcribe, or get the words out of, a recording. The audio never leaves the machine.
---

# Transcribe

Turns a recording on your disk into a readable `.txt` and a timestamped `.srt`.

**Your audio never leaves this machine.** Nothing is uploaded, no cloud service
is called, and after the one-time model download below the skill makes no network
call at all. It is safe for confidential recordings.

## Run

Let `DIR` be this skill's own directory — the folder containing this `SKILL.md`.

```text
DIR\scripts\transcribe.cmd "<path to the audio or video file>" ["<output folder>"]
```

On Linux use `DIR/scripts/transcribe.sh` with the same arguments.

- Writes `<name>.txt` (paragraphs) and `<name>.srt` (timestamps) next to the
  recording, or into the output folder if you give one.
- Any common audio or video format works (mp3, wav, m4a, mp4, mkv, ...). No
  ffmpeg is needed.
- A long recording takes a while. On an NVIDIA GPU expect far faster than real
  time; on a CPU expect roughly real time or slower.

When the run ends it prints the device used, the model, the audio duration and
the word count. Read the `.txt` back and check it is real, connected text before
you rely on it — a clean exit alone does not prove that.

## First use

The first run sets itself up, once, without touching anything outside this brain:

1. Uses the brain's one Python environment, `.claude/.venv` (the one synaptra
   runs in), with the brain's own `uv` from `.claude/`. No Python on your PATH
   is used or needed, and no second environment is created.
2. Installs faster-whisper into it.
3. If an NVIDIA GPU is present (`nvidia-smi` works), also installs the CUDA 12
   runtime (cuBLAS and cuDNN) there and transcribes on the GPU.
4. Downloads the `whisper-large-v3-turbo` model (about 1.6 GB) into `DIR/models/`.

Expect several minutes and a few GB of disk the first time. Every later run
starts immediately and works offline.

## Hardware

| Machine | What runs |
|---------|-----------|
| NVIDIA GPU | GPU, float16 (falls back to int8_float16, then to the CPU) |
| No NVIDIA GPU | CPU, int8 — the same model, just slower |

Set `TRANSCRIBE_DEVICE=cpu` to force the CPU even when a GPU is present.

AMD and Intel GPUs currently run on the CPU path. The engine choice sits behind
one function, `pick_engine()` in `scripts/transcribe.py`, so a GPU engine for
them (whisper.cpp on Vulkan) can be added later as one more entry without
touching the rest.

## If it fails

| Message | Do |
|---------|----|
| `no Python under ...\.python` / `uv was not found` | Run `/init-brain`; it installs the brain's Python and `uv`. |
| `.claude/.venv is missing or unusable` | Restart the brain (a moved brain repairs it on `/session-start`) or run `/init-brain`. The skill never builds an environment of its own. |
| `conflicts with the brain's synaptra environment` | The install was undone and your memory environment is exactly as it was. Nothing to repair; report the named conflict. |
| Download or install error on first use | Check the network and re-run. Only first use needs the network. |
| A GPU line says `cuda ... failed` | The run continues on the CPU with the same model. Update the GPU driver to use the GPU. |

Before each install the skill takes a list of the brain's installed packages and,
if synaptra no longer imports at the same version afterwards, puts that list
back. If `.claude/.venv` is ever rebuilt (an update, a move repair), the next
run installs faster-whisper again by itself.

After a move or rename of the brain folder, the brain's own repair rebuilds
`.claude/.venv`; the next transcribe then reinstalls what it needs. To free disk
space, delete `DIR/models/`; it is downloaded again on next use.

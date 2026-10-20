# Cycle 1 — #65 transcribe skill (2026-10-20)

Criteria held: **12 of 12**.

## Receipts (clean extract of `git archive HEAD:src`, 4fa8e0d; uv.exe + .python copied in as the /init-brain stand-in)

| Test | Result |
|------|--------|
| 7a first run, RTX 3060, venv + CUDA wheels + model download | `cuda (float16)`, 16.2 s audio, 37 words, real connected text |
| 7b `TRANSCRIBE_DEVICE=cpu` on a fresh brain | `cpu (int8)`, same 37 words; venv has no `nvidia/` dir; no CUDA wheels installed |
| 7c folder renamed after first use | `cuda (float16)`, same output, 5.6 s |
| builder `check_forbidden` on HEAD:src | OK; no `.venv`, `models` in the archive |

HF repo behind faster-whisper's `large-v3-turbo` alias: `mobiuslabsgmbh/faster-whisper-large-v3-turbo`.

## Found and fixed
- `av` 19 removed `metadata_errors`, which faster-whisper 1.2.1 passes → pinned `av>=17,<19`.

## Accepted, not fixed
- uv writes `activate*` scripts into `.venv/Scripts` that embed the venv's absolute path. Never executed by the skill, never shipped (the venv is not in the release).
- Only Windows was run. `launch.py` and `expose_cuda_libs()` have POSIX branches; untested.
- The first-run time is dominated by downloads (cuDNN 700 MB + cuBLAS 530 MB + model 1.6 GB): 5–10 min on this link.

## For Kaushik
- The release zip does not need a VERSION bump to carry the skill, but the skill is new behaviour: bump in the release branch as usual.
- Windows-only tested. If Alex is not on Windows the skill is unproven for him.

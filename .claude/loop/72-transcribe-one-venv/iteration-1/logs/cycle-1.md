# Cycle 1 — #72 Owner transcribes inside the brain's one Python environment

**Result: 11 of 11 criteria hold.**

| AC | Evidence |
|----|----------|
| 1 | `checks/transcribe-one-venv/check_one_venv.py` on a provisioned brain: faster-whisper in `.claude/.venv`, no `skills/transcribe/.venv`. Fresh GPU brain and fresh CPU brain both ended with no skill venv. |
| 2 | GPU brain: cuBLAS, cuDNN and nvrtc installed into `.claude/.venv`, run on `cuda (float16)`, 37 words of real text. CPU brain with `TRANSCRIBE_DEVICE=cpu`: `cpu (int8)`, 37 words, no `nvidia` packages in the venv. |
| 3 | The skill-venv code, repointing, gitignore line and docs are removed; grep of `src/` for a skill-owned environment finds nothing. |
| 4 | Model fetched into `skills/transcribe/models/` on the GPU brain's first run; the CPU brain, given a copy of that folder, ran offline. |
| 5 | `update_brain.py` run on a brain with faster-whisper installed: 60 files copied, then transcribe ran with no reinstall (37 words). |
| 6 | Check: synaptra 2.1.1 before and after the install. |
| 7 | Check: a test-only `pydantic==1.10.13` made `synaptra.server` unimportable; the launcher restored the package set exactly (`uv pip freeze` identical), synaptra imported at 2.1.1, no marker was kept, the message named the conflict. |
| 8 | `checks/transcribe-one-venv/mcp_probe.py` against the GPU brain after the install: `initialize`, `tools/list` (18 tools) and `memory_health` answered. |
| 9 | Venv deleted and recreated (as `/init-brain` does): the next transcribe reinstalled faster-whisper and transcribed (37 words). Also checked by deleting the package and marker. |
| 10 | Venv deleted: launcher exits 2 with "missing or unusable ... does not create an environment of its own"; no venv created. |
| 11 | Brain folder renamed after first use: `.claude/.venv` is unusable (launcher stops with the AC 10 message). After the brain's own repair step (delete, recreate, reinstall synaptra) transcribe reinstalled and ran, 37 words. |

**Found and fixed in this cycle:** the guard first probed only `import synaptra`.
With pydantic 1 installed that still passed while the MCP server could not load.
The guard now imports `synaptra.server`.

**Accepted rather than fixed**

- Windows only. The POSIX branches (`bin/python`, `bin/synaptra`) are untested.
- The move repair was emulated by its steps (delete `.claude/.venv`, `uv venv`, `uv pip install synaptra==...`), not by running `/session-start`.
- The rollback needs the network if a restored package is not already on disk, because the install uses `--no-cache`.
- The CPU brain was given a copy of the model rather than downloading it again.
- The first GPU run was killed once by the harness for low memory, after the CUDA wheels installed; it was resumed on the same brain, not restarted from scratch.

**For Kaushik**

- A renamed brain cannot transcribe until `/session-start` has rebuilt `.claude/.venv`; that rebuild now also removes faster-whisper and the CUDA wheels (about 1.3 GB re-download on the next transcribe on a GPU machine, because installs bypass the cache to keep wheels inside the brain).
- Installing faster-whisper into synaptra's venv adds `av`, `ctranslate2`, `onnxruntime`, `flatbuffers` and `protobuf`. A later synaptra release that pins one of those differently would be caught by the guard only at the next install, not at `/update`.

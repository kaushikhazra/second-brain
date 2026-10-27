# Cycle 1 — #79

**Reproduced on 1.6.1.** A listing of two older memories (null source / null rater): both reported as
violations.

**Fix.** `verify_memory.py`: `judge()` skips an active memory whose `rater` is present and null, and one
created before `.claude/conformance-baseline.json`'s `since`; it prints how many it did not judge and
why. A memory with a rater and no `create-memory:` source is still reported; a listing with no `rater`
key (synaptra 2.0.0) is judged by source. `update_brain.py`: `keep_conformance_baseline` writes the
file, dated now, when the brain has none (never overwrites); `--restore` and auto-rollback remove one the
update added. File is machine-local (MACHINE_LOCAL, `.gitignore`). session-end SKILL.md says to report the
"not judged" line.

**Criteria held: 8 of 8** (`checks/session-end/check_conformance_baseline.py`); 8 removals each fail their
named AC. Regression: check_verify_memory 12/12, check_defect_fixes 15/15, check_r2_r3_r4_r5_r8 10/10.
`check_conformance_scan.py` needs a live server and was not run.

**Deviation from the approved default (said to Velasari).** `rater` is not a replacement signal for the
source prefix: it is stamped on every store, including a direct one. It marks legacy only.

**Accepted, not fixed.** A brain that updates gets a baseline at update time, so a direct store made
between its install and the update is not judged. `memory_list` returning `rater`/`created_at` is read
from synaptra's source, not exercised against a live 2.1.1 server.

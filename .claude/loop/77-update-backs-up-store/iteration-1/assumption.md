# Assumptions — #77

- The store is `.claude/synaptra-data`, already an OWNER_DIR: the release never overwrites it.
- A synaptra process holds the store open; it is copied only after stop_synaptra.
- Not tested live: a real synaptra 2.0.0 -> 2.1.1 install (needs network and a real venv).
- Fail-safe deadline: one cycle.

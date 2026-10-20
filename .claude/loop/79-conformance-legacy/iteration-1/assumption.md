# Assumptions — #79

- Synaptra 2.1.1 stamps a `rater` on every write (`auto:heuristic` when none is passed); null means
  written before rater tracking. memory_list returns `rater` and `created_at` (model_dump).
- A synaptra 2.0.0 listing has no `rater` key.
- Velasari approved: rater field, source-prefix fallback, created-after baseline.
- Fail-safe deadline: one cycle.

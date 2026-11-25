# Observe — #106

`python checks/update/check_torch_cleanup.py` — real scratch venvs, real uv, hand-built wheels.
Done is every line PASS, including the four `mutation:` lines (each criterion also fails on a broken
copy of the module). Existing checks must keep passing: `check_r1_declaration.py`,
`check_r2_r3_r4_r5_r8.py`, `check_store_backup.py`.

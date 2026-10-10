# Brain-run window — 2026-10-09 20:29–20:54 +0530 (#43)

Kaushik lifted build-only for one window to run the behaviour-pending checks with
`claude -p`. Four chains were started in parallel at ~20:30–20:33 before the message
"one at a time" reached the session; at ~20:35 three were stopped and their children
killed, one kept (the ac3 demo), and every run after that was sequential.

## Results (skill text as of commit 4cae2d9)

```
check_method.py --all   (one run, sequential, 8 turns)
  detect  AC1 PASS   alpha_method_named=True beta_says_none=True
  follow  AC2 PASS   spec_before_code=True no_loop_folder=True
          AC4 PASS   main_unmoved=True origin_main_unmoved=True merges=[]
  work    AC3 PASS   loop_folders=['1-delete-note-by-number'] goal_holds_criteria=True brain_loop_empty=True
          AC4 (beta) PASS   main_unmoved=True merges=[]
          AC5 PASS   criteria=2 comments_added=1 n_of_n_comment=True proof_lines=2
demo ac3  AC3 FAIL when cut (loop_folders=[] brain_loop_empty=False) — as it should
```

Earlier removal demos, all failing when the behaviour is cut: ac1 (cycle 1), ac2 (cycle 2),
ac5 (cycle 3, `comments_added=0`). ac4 failed when reversed in cycle 2 on the older skill
text; its re-run on the current text was **interrupted** (stopped at turn 5 of 6 by the
sequential-only order) and has not been repeated.

## Numbers

- **Criteria met, fresh: 5/5** (AC1–AC5 on the final skill text). Every criterion has a
  removal demo that fails; **AC4's demo on the current text is the one still owed.**
- AC3 and AC5 were the behaviour-pending ones: both now proven by a brain.
- **Regression of #38–#42 on this text: not run** (the window ended). #43 is therefore
  not closed on GitHub; the issue stays open.

## For Kaushik

- The AC5 comment is a real comment on `sb-sandbox-beta` #1; the check saves it and
  deletes it (checked: none left). The brain also pushed `feature/1-delete-note` and
  `feature/1-delete-note-by-number` to beta's remote; the branch guard hook blocks
  deleting them from here.
- The interrupted ac4 demo and the interrupted first `check_method --all` left no state
  in the sandboxes beyond those branches (alpha's remote is unchanged, main untouched).

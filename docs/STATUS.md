# Status

## Current Phase

Post-release hardening. A multi-dimension code review produced a ranked optimization plan, and the accepted items are implemented on the feature branch `fix/silent-completion-and-resilience` (commit `23f7300`). The branch is **not pushed and not merged**; `main` is unchanged and still matches `origin/main`.

## Current Focus

This repository contains only the course-watching workflow. The active local clone moved to `D:\dev\active\chaoxing_course_watcher` during a D-drive reorganisation and still tracks `git@github.com:O-right/chaoxing-course-watcher.git`. Do not confuse it with `D:\dev\active\course_rpa_node\chaoxing_course_watcher`, which is the older combined-workspace archive (2012-line `main.py`, remote `course-rpa-node.git`).

The current work fixes defects that let a run report success without actually watching the content, hardens unattended multi-hour runs, cuts avoidable wall-clock time, and closes the gap between `CONFIG` and `.env.example`. Everything is validated offline only. The next milestone is a bounded authorized live run to confirm the two highest-severity fixes against the real Chaoxing DOM.

## Review Findings Behind This Work

A six-dimension review (correctness, robustness, security, architecture, performance, testing) ran each finding through an adversarial verification pass. Findings that survived were ranked by run impact over effort and grouped A/B/C/D; group D was explicitly rejected as not worth the effort for a solo tool. The full report is not tracked in Git.

Two findings were reproduced independently before implementation:
- `current_video_locator` falling back to the first `<video>` was confirmed by reading the call chain `wait_until_video_finished` -> `read_video_state` -> completion check.
- The stall-threshold defect was confirmed with a standalone simulation showing a healthy video trips the stall counter whenever `poll x rate <= progress_stall_epsilon_seconds`, exhausting all 18 recovery attempts and failing the run.

## Recent Evidence

- `python -m unittest discover -s tests -t .` passes with 44 tests (was 14).
- `python -m py_compile main.py tests\test_closed_page_guards.py tests\test_course_matching.py tests\test_env_documented.py tests\test_video_progress.py` passes.
- `ruff check --select F821,F811,E9 main.py tests` reports `All checks passed` (run from a scratch virtualenv; `pipx` is not installed locally).
- `python main.py --help` and `.\run_chaoxing.ps1 --help` exit 0.
- `git diff --check` is clean; `.env`, `logs/`, screenshots, and storage-state paths were confirmed absent from the staged set.
- Config-path smoke checks pass: `--max-chapters 0` and `CX_MAX_CHAPTERS=0` are rejected, `CX_MAX_CHAPTERS=1OO` warns instead of silently defaulting, a too-dense poll interval warns, and `--headless`/`--headed` remain mutually exclusive.
- Mutation testing confirmed the new regression tests have force: reverting the `current_video_locator` fix fails 1 test, reverting the stall-threshold fix fails 8, and reverting the fail-closed completion scan fails 1. The completion-scan case failed to fail on the first attempt, so a direct test for `incomplete_learning_signals` returning `None` was added.
- `main.py` line endings are unchanged (LF in both `HEAD` and the working copy); the `core.autocrlf` warning during `git add` is pre-existing noise.

## Next Steps

- Review `git diff main` on `fix/silent-completion-and-resilience`, then push and let CI confirm the new ruff step on a GitHub-hosted runner (`pipx` was never exercised in real CI).
- Run a bounded authorized live session to validate the two fixes that offline tests cannot reach:
  - a task point with **multiple videos**, to confirm the second and later videos are no longer skipped;
  - a catalog whose active item is the **last visible entry**, to confirm the run no longer declares the course complete early.
- Confirm the `--fast-actions` timing changes on a real course before relying on them.
- Review Dependabot PR #2 (`actions/setup-python 6.3.0`), PR #3 (`actions/checkout 7.0.0`), and PR #4 (`playwright 1.61.0`); all three are still open and unreviewed.
- Keep local `.env` outside Git and do not print or commit private course URLs.

## Blockers And Cautions

- **No live run has validated any of this work.** All evidence above is offline. Do not claim live completion without a fresh configured run.
- The exit-code contract changed: reaching `CX_MAX_CHAPTERS` now returns `False` (exit code 1) instead of `True`. Any wrapper, scheduled task, or script that treated exit 0 as "course finished" must be re-checked.
- `CX_STORAGE_STATE_PATH` is off by default. When enabled, the file contains login cookies and is equivalent to credentials; `.gitignore` covers `storage_state*` but the file is better kept outside the repository.
- `CX_SELECTOR_VIDEO_PLAY_CONTROL` now uses `;` to separate priority groups and `,` within a group. A pre-existing comma-only override still works but collapses into a single group and loses intra-group priority.
- The `login_success_marker` selector defaults to empty, so login verification currently relies on "did we leave the passport page". Setting `CX_SELECTOR_LOGIN_SUCCESS_MARKER` makes it stricter.
- The owner accepts that existing Git history exposes a non-noreply author email and named course evidence.
- The latest CI passes, but GitHub annotates the pinned Actions for Node.js 20 deprecation; Dependabot PR #2 and #3 are the pending upgrade path.
- The removed tutai deployment is not a viable runner until its Chaoxing network block is resolved.

## Active Files

- `main.py`
- `run_chaoxing.ps1`
- `requirements.txt`
- `README.md`
- `LICENSE`
- `.env.example`
- `.gitignore`
- `SECURITY.md`
- `security_best_practices_report.md`
- `.github/workflows/ci.yml`
- `.github/dependabot.yml`
- `AGENTS.md`
- `tests/__init__.py`
- `tests/test_closed_page_guards.py`
- `tests/test_course_matching.py`
- `tests/test_env_documented.py`
- `tests/test_video_progress.py`
- `docs/`

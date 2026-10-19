# Project Status

## Snapshot

- Phase: Post-release hardening, live-validated on a real course except the multi-video path.
- Current focus: the branch is ready to push and open a PR; the multi-video live check is deferred by the owner.
- Branch: `fix/silent-completion-and-resilience`, local only (not pushed). Based on `23fa1b2`; `origin/main` is 2 commits ahead (Dependabot PR #8, `python-dotenv 1.2.3`, no overlap with this branch).

## Completed Recently

- 2026-10-19 bounded live validation passed on an authorized 6-task-point course: the 4 remaining units were watched and the platform shows 6/6 (100%). The last-catalog-entry fix was exercised for real. Record: `docs/runs/2026-10-19-live-course-validation.md`.
- `a8c91ae`: the live run exposed two defects in this branch's own changes, both fixed with regression tests. The post-login check raced the redirect, and the first fix polled a stale cached URL. An unlinked course-title wrapper made one course ambiguous with itself. Suite 44 -> 52.
- `23f7300` (2026-07-27): silent-false-completion fixes, unattended-run resilience, latency trims, configurable selectors; rationale in `docs/DECISIONS.md` (2026-07-27 entries).

## In Progress

- None.

## Next Up

- Merge `origin/main` into the branch, push, open a PR, and confirm CI. The `pipx`-based ruff step has never run on a hosted runner.
- Decide whether to merge to `main`. The only fix without live evidence is the multi-video path.
- Deferred by owner: a live run on a task point with **multiple videos** (and ideally multiple resource cards).
- After the merge, let Dependabot PR #5 (`setup-python 7.0.0`) and #6 (`checkout 7.0.1`) rebase, since both touch `ci.yml`. Review #9 (`playwright 1.63.0`) with the DOM-fixture tests, and #10 (`python-dotenv 1.2.4`).

## Blockers

- None. The multi-video check needs a course that actually has such a task point.

## Active Files

- `main.py` — the whole workflow; this round changed `wait_until_left_login_page` and the candidate JS in `course_candidate_details`.
- `tests/test_login_check.py`, `tests/test_course_card_dom.py`, `tests/test_course_matching.py` — regression coverage for the live-run fixes.
- `.github/workflows/ci.yml` — ruff step and compile list; expect conflicts with Dependabot #5/#6.
- `.env.example` — must document every `CX_*` read (enforced by `tests/test_env_documented.py`).
- `docs/runs/2026-10-19-live-course-validation.md` — live evidence and open follow-ups.

## Validation

- Ran (2026-10-19/20):
  - Unit suite: 52 tests OK; the 3 DOM-fixture tests ran against system Chrome.
  - `py_compile` on `main.py` and every test file.
  - ruff 0.17.1 `--select F821,F811,E9` from a scratch venv: all checks passed.
  - `python main.py --help` and `.\run_chaoxing.ps1 --help`: exit 0.
  - `git diff --check`: clean.
  - Mutation checks: reverting each live-run fix makes its new test fail.
  - Live run #5: exit 0, plus a platform-side 6/6 check.
- Not run:
  - GitHub CI for this branch (not pushed).
  - Live run on a multi-video or multi-card task point.
  - `--fast-actions` timing on a real course.
  - Headed mode, manual verification wait, or `CX_STORAGE_STATE_PATH` in a live run.

## Notes For Next Session

- The active clone is `D:\dev\active\chaoxing_course_watcher` (remote `O-right/chaoxing-course-watcher`). `D:\dev\active\course_rpa_node\chaoxing_course_watcher` is the old combined-workspace archive.
- Exit-code contract: reaching `CX_MAX_CHAPTERS` exits 1. Re-check any wrapper that treated exit 0 as "finished".
- On the new chapter-detail layout, every single-video unit triggers the "资源卡片条为空" warning and a screenshot. That is harmless there; the right behavior for multi-card units is still undecided.
- Course keywords must be close to the real title (match gate 0.68); otherwise use `--course-url`.
- `CX_SELECTOR_LOGIN_SUCCESS_MARKER` defaults to empty, so a login counts as successful once the page leaves the passport host.
- In sync Playwright loops, wait with `page.wait_for_timeout`, not `time.sleep`, when polling cached state such as `page.url` (see DECISIONS 2026-10-19).
- `CX_STORAGE_STATE_PATH` (off by default) stores login cookies; keep it outside the repo. `CX_SELECTOR_VIDEO_PLAY_CONTROL` uses `;` between priority groups.
- The owner accepts the existing Git history metadata exposure. tutai is not a viable runner until its Chaoxing network block is resolved.
- Logs, screenshots, `.env`, and storage state stay untracked. Live logs and screenshots show the account display name and school.

_Last sync: 2026-10-20 · Claude Code_

# Project Status

## Snapshot

- Phase: Post-release hardening (PR #11) and the desktop UI (PR #12) are on `main`. The workflow is live-validated on a real course except the multi-video path. The UI has not driven a real run yet.
- Current focus: one real course run started from the UI. The multi-video live check is deferred by the owner.
- Branch: `main`. `feat/desktop-ui` was merged via PR #12 and deleted.

## Completed Recently

- 2026-10-20 Dependabot #5 (`setup-python 7.0.0`), #9 (`playwright 1.64.0`), #6 (`checkout 7.0.1`), and #10 (`python-dotenv 1.2.4`) were merged in that order, each with green CI. The local environment was upgraded to the same pins, and the suite passed on them. The checkout pin's stale `# v4` comment now reads `# v7.0.1`; both action SHAs were checked against their release tags.
- 2026-10-20 desktop UI, merged via PR #12: `gui.py` (Tkinter, no new dependencies) runs `main.py` as a subprocess and shows status, video progress, and colored logs. Also `start_ui.bat`, `python gui.py --create-shortcuts` (Desktop and Start Menu shortcuts that share the window's AppUserModelID), and `CX_FAST_ACTIONS` as the env form of `--fast-actions`. Suite 52 -> 81. Rationale in `docs/DECISIONS.md` (2026-10-20).
- 2026-10-20 PR #11 merged to `main`. CI passed on Python 3.10 and 3.11: ruff (the `pipx` step's first hosted run), 52 tests with none skipped (the DOM fixtures ran against the runner's Chrome), compile, and CLI help.
- 2026-10-19 bounded live validation passed on an authorized 6-task-point course: the 4 remaining units were watched and the platform shows 6/6 (100%). The last-catalog-entry fix was exercised for real. Record: `docs/runs/2026-10-19-live-course-validation.md`.
- `a8c91ae`: the live run exposed two defects in this branch's own changes, both fixed with regression tests. The post-login check raced the redirect, and the first fix polled a stale cached URL. An unlinked course-title wrapper made one course ambiguous with itself. Suite 44 -> 52.
- `23f7300` (2026-07-27): silent-false-completion fixes, unattended-run resilience, latency trims, configurable selectors; rationale in `docs/DECISIONS.md` (2026-07-27 entries).

## In Progress

- None.

## Next Up

- Run one real course from the UI with the browser visible, to confirm the UI path end to end.
- The bundled Chromium for `playwright 1.64.0` is not installed locally, and it was not installed before either. Runs use system Chrome. Run `python -m playwright install chromium` before choosing 「内置 Chromium」 in the UI.
- Deferred by owner: a live run on a task point with **multiple videos** (and ideally multiple resource cards).
- Decide how the card-tabs warning should behave on the new chapter-detail layout (see TASKS).

## Blockers

- None. The multi-video check needs a course that actually has such a task point.

## Active Files

- `gui.py` — the desktop UI: form <-> `.env` <-> child environment, log parsing, process runner, icon, and shortcuts.
- `tests/test_gui.py` — 26 tests for the UI's non-window logic, including a hermetic run of `main.py` and a real shortcut read back through the Windows Shell.
- `main.py` — the whole workflow; this round only added `CX_FAST_ACTIONS`.
- `start_ui.bat` — double-click launcher (`pythonw`, falls back to `python`).
- `.github/workflows/ci.yml` — ruff and compile include `gui.py` and the new tests; actions pinned to `checkout v7.0.1` and `setup-python v7.0.0`.
- `.env.example` — must document every `CX_*` read (enforced by `tests/test_env_documented.py`).

## Validation

- Ran for the desktop UI (2026-10-20):
  - Unit suite: 81 tests OK, none skipped.
  - ruff 0.17.1 `--select F821,F811,E9 main.py gui.py tests` and full `F` on the new files: passed.
  - `py_compile` on every file; `python main.py --help`; `python gui.py --help`; `git diff --check`: clean.
  - Mutation checks: dropping the explicit empty env values or the trailing-backslash guard makes a test fail.
  - Screenshots with a fake `main.py` covered the idle, running, cap-reached, and failed states.
  - `--create-shortcuts` created the owner's Desktop and Start Menu shortcuts, and the Shell read back the AppUserModelID. Launching from the Desktop shortcut opened the window under `pythonw` with no console window.
  - Real `.env` untouched.
  - GitHub CI on PR #12 (Python 3.10 and 3.11): 81 tests, none skipped. The first run failed only in the shortcut test, because `WScript.Shell` cannot open a `.lnk` whose path falls outside the ANSI code page (Chinese on the English runner). The test now reads back through `Shell.Application`.
  - After the Dependabot merges: 81 tests OK locally on `playwright 1.64.0` and `python-dotenv 1.2.4`, DOM fixtures included.
- Not run for the desktop UI:
  - A real Chaoxing run started from the UI.
  - Pinning to the taskbar (Windows only allows this by hand).
- Ran (2026-10-19/20):
  - Unit suite: 52 tests OK; the 3 DOM-fixture tests ran against system Chrome.
  - `py_compile` on `main.py` and every test file.
  - ruff 0.17.1 `--select F821,F811,E9` from a scratch venv: all checks passed.
  - `python main.py --help` and `.\run_chaoxing.ps1 --help`: exit 0.
  - `git diff --check`: clean.
  - Mutation checks: reverting each live-run fix makes its new test fail.
  - Live run #5: exit 0, plus a platform-side 6/6 check.
  - GitHub CI on PR #11 (Python 3.10 and 3.11): every step passed.
- Not run:
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
- With 「记住设置」 checked, the UI writes its managed `CX_*` keys (password included) into `.env` and leaves every other line alone. The owner's `.env` also holds unrelated secrets, so never rewrite it wholesale. Values python-dotenv cannot round-trip (`${`, a trailing backslash, newlines) are skipped and logged.
- UI run logs go to `logs/ui/`. The shortcut icon `app.ico` is generated and gitignored. Shortcuts store absolute paths to this clone and to the current Python, so re-run `python gui.py --create-shortcuts` after moving either.
- In Claude Code, `! python gui.py` blocks the session until the window closes; use the Desktop shortcut or `start_ui.bat`.
- The `gh` token lacks the `workflow` scope, so GitHub refuses a merge whose result writes new content into `.github/workflows/`. Bring the PR branch up to date with `main` first, so the merge result matches a pushed commit. Pushing over SSH is not affected.

_Last sync: 2026-10-20 (desktop UI) · Claude Code_

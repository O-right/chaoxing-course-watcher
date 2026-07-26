# Architecture

## System Shape

This repository is a single-workflow Python + Playwright project for Chaoxing course watching. It is one of two split repositories created from the former combined workspace.

## Components

- `main.py`
  - Main course-watcher entrypoint.
  - Defines configuration, CLI parsing, browser lifecycle, login, course lookup, chapter/task processing, video playback, recovery, screenshots, and exit-code behavior.
  - Module level, before the class: env coercion helpers (`env_flag` / `env_int` / `env_float`, which warn instead of silently defaulting on a bad value), log redaction (`redact_url_for_log` / `redact_urls_in_text`), the `CONFIG` dict, and four pure decision functions extracted so the highest-risk logic is directly testable without a browser:
    - `video_is_complete(state, completion_margin)` — is this video actually finished.
    - `stall_epsilon_for(sleep_seconds, playback_rate, configured_epsilon)` — how far a healthy video must advance in one iteration.
    - `next_poll_seconds(state, poll, min_poll, margin)` — adaptive progress-poll interval.
    - `classify_completion_scan(signals)` — maps a completion scan to `unreadable` / `incomplete` / `clear`.
  - `CourseAutoTester` holds the browser-bound workflow. `build_config_from_args` layers CLI flags over `CONFIG` and then calls `validate_config`, which rejects settings that would make a run a no-op.
- `run_chaoxing.ps1`
  - PowerShell launcher.
  - Loads local `.env` values when present and forwards CLI arguments to `main.py`.
- `requirements.txt`
  - Pins the locally verified Playwright and `python-dotenv` versions.
- `.github/`
  - Runs offline Python 3.10/3.11 checks on Windows and schedules dependency updates.
- `docs/`
  - Current status, tasks, architecture, decisions, and product scope for handoff.

## Runtime Flow

1. Build configuration from defaults, `.env`, `CX_*` environment variables, and CLI flags.
2. Launch Playwright Chromium or a configured installed browser channel.
3. Log in with configurable selectors.
4. Locate and open the course by keyword.
5. Optionally scroll to and open a chapter keyword.
6. Process the current learning task page:
   - skip if the active catalog item is explicitly completed;
   - iterate visible resource cards;
   - process every detected video;
   - handle non-video courseware quickly.
7. Keep playback moving with real player clicks, playback-rate best effort, stall recovery, iframe re-location, and alternate playback routes for true no-source states.
8. Wait for a real completion state before advancing.
9. Click next task only when the control is visible and enabled, and confirm advancement by URL or content changes.
10. On no-next paths, verify no unfinished markers remain before returning success.

## Configuration And Secrets

- Local `.env` and runtime environment variables hold private configuration.
- Course targets must be configured explicitly; no course is selected by default.
- URL paths, query values, and fragments are redacted from terminal diagnostics.
- Automatic commitment confirmation is disabled by default.
- Every selector in `CONFIG["selectors"]` can be overridden with `CX_SELECTOR_<KEY>`, so a Chaoxing front-end change does not require a source edit. `CX_SELECTOR_VIDEO_PLAY_CONTROL` uses `;` between priority groups and `,` within a group.
- `tests/test_env_documented.py` fails the build if a `CX_*` variable read by `main.py` is missing from `.env.example`, or if `.env.example` documents a variable the code no longer reads.
- Session persistence (`CX_STORAGE_STATE_PATH`) is off by default; the file holds login cookies and is equivalent to credentials.
- `.env`, logs, screenshots, browser profiles, cookies, tokens, storage state, and private URLs must remain untracked.
- This repository's remote is `git@github.com:O-right/chaoxing-course-watcher.git`. The active local clone is `D:\dev\active\chaoxing_course_watcher`.

## Failure Semantics

- Unresolvable or unreadable state fails closed rather than reporting success. See `DECISIONS.md` (2026-07-27) for the rationale.
- A failed learning unit is retried up to `CX_UNIT_RETRIES` times and then fails the run; it is never skipped.
- Re-entering the same catalog item more than `CX_MAX_UNIT_REVISITS` times is treated as stuck.
- Reaching `CX_MAX_CHAPTERS` exits non-zero. Giving up at the cap is not completion.

## Validation

- Baseline: `python -m py_compile main.py`.
- CLI smoke: `python main.py --help`.
- Unit suite: `python -m unittest discover -s tests -t .`.
- Lint (undefined names / redefinitions only): `pipx run ruff check --select F821,F811,E9 main.py tests`.
- PowerShell forwarding smoke: `.\run_chaoxing.ps1 --help`.
- Use local/offline Playwright fixtures for selector and recovery changes when practical.
- Use bounded live Chaoxing runs only when authorized and configured.

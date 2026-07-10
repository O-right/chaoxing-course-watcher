# Architecture

## System Shape

This repository is a single-workflow Python + Playwright project for Chaoxing course watching. It is one of two split repositories created from the former combined workspace.

## Components

- `main.py`
  - Main course-watcher entrypoint.
  - Defines configuration, CLI parsing, browser lifecycle, login, course lookup, chapter/task processing, video playback, recovery, screenshots, and exit-code behavior.
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
- `.env`, logs, screenshots, browser profiles, cookies, tokens, and private URLs must remain untracked.
- This repository's remote is `git@github.com:O-right/chaoxing-course-watcher.git`.

## Validation

- Baseline: `python -m py_compile main.py`.
- CLI smoke: `python main.py --help`.
- Unit suite: `python -m unittest discover -s tests`.
- PowerShell forwarding smoke: `.\run_chaoxing.ps1 --help`.
- Use local/offline Playwright fixtures for selector and recovery changes when practical.
- Use bounded live Chaoxing runs only when authorized and configured.

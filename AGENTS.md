# Project Agent Rules

## Project Context

- This repository is the standalone Chaoxing course watcher.
- The workflow logs in, opens an authorized course, enters learning task points, processes resource cards, plays videos, and advances until a configured cap or verified completion.
- Runtime URLs, credentials, course names, selectors, browser options, and timing settings must stay configurable through `.env`, environment variables, or CLI flags.

## Commands

- Install dependencies: `python -m pip install -r requirements.txt`
- Install browser: `python -m playwright install chromium`
- Run launcher: `.\run_chaoxing.ps1 --course "课程名称关键词" --headless --fast-actions --browser-channel chrome`
- Run directly: `python main.py --course "课程名称关键词" --max-chapters 200 --headless --fast-actions --browser-channel chrome`
- Syntax check: `python -m py_compile main.py`
- CLI help: `python main.py --help`

## MUST DO

- Read `docs/STATUS.md`, `docs/TASKS.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and `docs/PRD.md` before non-trivial changes.
- Keep selectors, credentials, course names, timing, and browser settings configurable.
- Preserve randomized action delays and basic exception handling around page operations.
- Save useful failure evidence for login, course selection, chapter/task processing, video playback, and next-task navigation failures.
- Validate with deterministic local checks first; only claim live Chaoxing completion when a configured real run actually passed.

## MUST NEVER

- Never commit real passwords, tokens, cookies, private course URLs, `.env`, logs, screenshots, or browser profiles.
- Never bypass access controls, payment controls, CAPTCHA, MFA, SMS login, or site terms.
- Never claim an end-to-end course flow is verified unless it ran against the real configured course and passed.

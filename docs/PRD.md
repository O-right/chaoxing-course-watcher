# PRD: Chaoxing Course Watcher

## Goal

Maintain a Python + Playwright course-watching automation that can operate on authorized Chaoxing courses: log in, open a target course, process learning task pages, watch required videos, handle courseware/resource cards, and stop only at a configured cap or verified completion.

## Requirements

- Load credentials, selectors, course names, browser choices, timing, screenshots, and recovery settings from `.env`, `CX_*` environment variables, and CLI flags.
- Support headed/headless runs and installed browser channels such as Chrome or Edge.
- Locate Chaoxing course cards by keyword, preferring real course-card links.
- Optionally start at a requested chapter keyword.
- Process all visible learning resource cards in a chapter, including mixed `课件` and `视频` cards.
- Detect nested video iframes and process all `<video>` elements on the current task page.
- Use playback-rate control when allowed, while tolerating platform-limited playback.
- Recover from paused, stalled, iframe-recreated, or true no-source videos when possible.
- Wait for a real ended or near-end-paused state before advancing.
- Skip only task points that the active catalog item explicitly marks complete.
- Advance only with observable URL or page-content evidence.
- Treat no-next as completion only after checking for unfinished markers, and treat an unreadable check as "not verified" rather than complete.
- Never report success for content that was not actually watched: when progress cannot be positively confirmed, fail loudly instead of advancing or exiting zero.
- Retry a failed task point a bounded number of times, but never skip past one that did not complete.
- Save failure screenshots and return non-zero on failed paths, including when the configured chapter cap is reached.
- Allow every selector to be overridden through `CX_SELECTOR_<KEY>` so a platform front-end change does not require editing source.

## Acceptance Criteria

- `python -m py_compile main.py` passes.
- `python -m unittest discover -s tests -t .` passes.
- `ruff check --select F821,F811,E9 main.py tests` passes.
- `python main.py --help` works.
- Launcher argument forwarding works through `run_chaoxing.ps1`.
- Every `CX_*` variable read by `main.py` is documented in `.env.example`, enforced by test.
- Real course completion is documented only when the exact configured run passed.
- `.env`, logs, screenshots, browser profiles, cookies, tokens, and private URLs remain untracked.

## Out Of Scope

- CAPTCHA solving.
- MFA or SMS automation.
- Scraping unrelated private data.
- Circumventing access controls or site restrictions.
- CI against a private live Chaoxing course.

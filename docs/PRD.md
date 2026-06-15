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
- Treat no-next as completion only after checking for unfinished markers.
- Save failure screenshots and return non-zero on failed paths.

## Acceptance Criteria

- `python -m py_compile main.py` passes.
- `python main.py --help` works.
- Launcher argument forwarding works through `run_chaoxing.ps1`.
- Real course completion is documented only when the exact configured run passed.
- `.env`, logs, screenshots, browser profiles, cookies, tokens, and private URLs remain untracked.

## Out Of Scope

- CAPTCHA solving.
- MFA or SMS automation.
- Scraping unrelated private data.
- Circumventing access controls or site restrictions.
- CI against a private live Chaoxing course.

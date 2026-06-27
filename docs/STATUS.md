# Status

## Current Phase

Standalone course-watcher repository created and synced from the former combined workspace.

## Current Focus

This repository now contains only the course-watching workflow. The active local clone is `D:\chaoxing_course_watcher`, tracking `git@github.com:O-right/chaoxing-course-watcher.git`. The old combined workspace at `D:\course_rpa_node` should be treated as a handoff/archive location, not the normal place for course-watcher commits.

Current local work adds closed-page guards for the video progress path and improves course selection so course-name lookup scores all visible candidates before clicking. Ambiguous short keywords now fail with candidate diagnostics instead of clicking the first partial match. `CX_COURSE_URL` / `--course-url` can bypass name matching when an exact authorized course URL is available.

## Recent Evidence

- `2026春-线性代数` full-course completion was previously verified from the combined workspace.
- `道德与法治` final fresh-session audit previously reported no unfinished task points.
- `2025-2026(2) 物理学` mixed `1课件 / 2视频` resource-card handling was previously verified on `5.1 物质的微观模型`.
- The split repository clone was created locally at `D:\chaoxing_course_watcher`.
- `python -m py_compile main.py` passed in this standalone clone.
- `python main.py --help` passed in this standalone clone.
- `git diff --check` passed after adding handoff docs.
- Added closed-page guards around video detection, progress reads, and debug screenshots so an externally closed/crashed page stops cleanly instead of reusing stale video locators.
- Added `tests/test_closed_page_guards.py` for closed-page screenshot, locator lookup, and stale-video progress-read paths.
- `python -m unittest discover -s tests` passed after the guard change.
- `python -m py_compile main.py tests\test_closed_page_guards.py` passed after the guard change.
- `python main.py --help` passed after the guard change.
- `git diff --check` passed after the guard change.
- Course lookup now expands quoted/suffixed keywords, scores collected course candidates, rejects close ambiguous matches, and supports direct course URLs.
- Added `tests/test_course_matching.py` for keyword expansion, exact-match priority, suffix variants, ambiguity handling, and low-similarity rejection.
- `python -m unittest discover -s tests` passed after the course-matching change.
- `python -m py_compile main.py tests\test_closed_page_guards.py tests\test_course_matching.py` passed after the course-matching change.
- `python main.py --help` passed after the course-matching change and shows `--course-url`.
- `git diff --check` passed after the course-matching change, with only LF/CRLF conversion warnings.
- Bounded live course-opening smoke passed with system Chrome: keyword `中国现代史纲要` matched `中国近现代史纲要` via similarity score `0.820` and opened that course page. This did not enter chapters or process videos.
- Local `.env` was copied from the former combined workspace and is ignored by Git.
- Local Git status was clean before adding these handoff docs.

## Next Steps

- Use this repository for future course-watcher changes and commits.
- Keep local `.env` outside Git; recreate it only if the file is deleted or credentials change.
- Re-run the target course in a bounded live session to confirm the closed-page guard behavior in the real Chaoxing flow.
- Use headed mode with manual verification wait if the platform presents a visible verification or the browser closes during a headless run.
- Run `python main.py --help` and a bounded course smoke before claiming any new live behavior.

## Blockers And Cautions

- `.env` exists locally for this clone but is intentionally ignored and must not be committed or printed.
- Do not claim new live completion without a fresh configured run.
- The reported closed-page failure has local guard coverage, but the exact live Chaoxing course path has not been re-run after the fix.
- The course-matching optimization has deterministic unit coverage and one bounded live course-opening smoke, but not full course-flow validation.
- The removed tutai deployment is not a viable current runner until its Chaoxing network block is resolved.

## Active Files

- `main.py`
- `run_chaoxing.ps1`
- `requirements.txt`
- `README.md`
- `AGENTS.md`
- `tests/test_closed_page_guards.py`
- `tests/test_course_matching.py`
- `docs/`

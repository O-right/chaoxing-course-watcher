# Status

## Current Phase

Feature branch prepared for review after integrating the latest `main` open-source hardening.

## Current Focus

This repository now contains only the course-watching workflow. The active local clone is `D:\chaoxing_course_watcher`, tracking `git@github.com:O-right/chaoxing-course-watcher.git`. The old combined workspace at `D:\course_rpa_node` should be treated as a handoff/archive location, not the normal place for course-watcher commits.

The `codex/course-matching-guards` branch combines closed-page guards and scored course selection with the latest `main` privacy and open-source documentation changes. Ambiguous short keywords fail with candidate diagnostics instead of clicking the first partial match, while `CX_COURSE_URL` / `--course-url` provides an exact authorized entry path. The safe environment template, ignore rules, README, and security guidance now document this path without exposing private values.

## Recent Evidence

- `2026春-线性代数` full-course completion was previously verified from the combined workspace.
- `道德与法治` final fresh-session audit previously reported no unfinished task points.
- `2025-2026(2) 物理学` mixed `1课件 / 2视频` resource-card handling was previously verified on `5.1 物质的微观模型`.
- The standalone clone is active at `D:\chaoxing_course_watcher` and tracks `git@github.com:O-right/chaoxing-course-watcher.git`.
- Closed-page guards cover video detection, progress reads, and debug screenshots; scored course selection covers exact, suffix, similarity, ambiguity, and rejection paths.
- Latest `origin/main` open-source hardening was integrated into the feature branch; the only textual merge conflict was resolved in `README.md`.
- `.env.example` now documents `CX_COURSE_URL` with an empty value, `.env` remains ignored, and no private template values are populated.
- `python -m unittest discover -s tests` passed with 9 tests after the integration.
- `python -m py_compile main.py tests\test_closed_page_guards.py tests\test_course_matching.py` passed after the integration.
- `python main.py --help` passed after the integration and shows `--course-url`.
- `git diff --cached --check` passed after conflict resolution.
- Bounded live course-opening smoke passed with system Chrome: keyword `中国现代史纲要` matched `中国近现代史纲要` via similarity score `0.820` and opened that course page. This did not enter chapters or process videos.

## Next Steps

- Confirm PR #1 remains conflict-free after branch updates, then review it before merging to `main`.
- Re-run the target course in a bounded live session to confirm the closed-page guard behavior in the real Chaoxing flow.
- Use headed mode with manual verification wait if the platform presents a visible verification or the browser closes during a headless run.
- Keep local `.env` outside Git and do not print or commit private course URLs.

## Blockers And Cautions

- `.env` exists locally for this clone but is intentionally ignored and must not be committed or printed.
- Do not claim new live completion without a fresh configured run.
- The reported closed-page failure has local guard coverage, but the exact live Chaoxing course path has not been re-run after the fix.
- The course-matching optimization has deterministic unit coverage and one bounded live course-opening smoke, but not full course-flow validation.
- PR #1 has no recorded CI checks, so local deterministic validation is currently the primary merge evidence.
- The removed tutai deployment is not a viable current runner until its Chaoxing network block is resolved.

## Active Files

- `main.py`
- `run_chaoxing.ps1`
- `requirements.txt`
- `README.md`
- `.env.example`
- `.gitignore`
- `SECURITY.md`
- `AGENTS.md`
- `tests/test_closed_page_guards.py`
- `tests/test_course_matching.py`
- `docs/`

# Status

## Current Phase

Standalone course-watcher repository created and synced from the former combined workspace.

## Current Focus

This repository now contains only the course-watching workflow. The active local clone is `D:\chaoxing_course_watcher`, tracking `git@github.com:O-right/chaoxing-course-watcher.git`. The old combined workspace at `D:\course_rpa_node` should be treated as a handoff/archive location, not the normal place for course-watcher commits.

## Recent Evidence

- `2026春-线性代数` full-course completion was previously verified from the combined workspace.
- `道德与法治` final fresh-session audit previously reported no unfinished task points.
- `2025-2026(2) 物理学` mixed `1课件 / 2视频` resource-card handling was previously verified on `5.1 物质的微观模型`.
- The split repository clone was created locally at `D:\chaoxing_course_watcher`.
- `python -m py_compile main.py` passed in this standalone clone.
- `python main.py --help` passed in this standalone clone.
- `git diff --check` passed after adding handoff docs.
- Local `.env` was copied from the former combined workspace and is ignored by Git.
- Local Git status was clean before adding these handoff docs.

## Next Steps

- Use this repository for future course-watcher changes and commits.
- Keep local `.env` outside Git; recreate it only if the file is deleted or credentials change.
- Run `python main.py --help` and a bounded course smoke before claiming any new live behavior.

## Blockers And Cautions

- `.env` exists locally for this clone but is intentionally ignored and must not be committed or printed.
- Do not claim new live completion without a fresh configured run.
- The removed tutai deployment is not a viable current runner until its Chaoxing network block is resolved.

## Active Files

- `main.py`
- `run_chaoxing.ps1`
- `requirements.txt`
- `README.md`
- `AGENTS.md`
- `docs/`

# Tasks

## Setup

- [x] Create standalone GitHub repository `O-right/chaoxing-course-watcher`.
- [x] Clone standalone local repository at `D:\chaoxing_course_watcher`.
- [x] Include `main.py`, `run_chaoxing.ps1`, `requirements.txt`, `.gitignore`, and README.
- [x] Add project handoff docs and repo rules.

## Validation

- [x] Verify repository tracks `git@github.com:O-right/chaoxing-course-watcher.git`.
- [x] Verify local branch tracks `origin/main`.
- [x] Run `python -m py_compile main.py`.
- [x] Run `python main.py --help` after doc sync.
- [ ] Run a bounded live course smoke only when credentials and authorization are available.

## Future Work

- [ ] Add structured logging if long-run diagnostics need cleaner output.
- [ ] Add selector profiles only if another course platform becomes a real requirement.
- [ ] Re-evaluate tutai or another remote runner only after a viable Chaoxing network path is available.

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
- [x] Add regression coverage for closed-page video progress and screenshot guards.
- [x] Run `python -m unittest discover -s tests` after the closed-page guard change.
- [x] Run `python -m py_compile main.py tests\test_closed_page_guards.py` after the closed-page guard change.
- [x] Run `python main.py --help` after the closed-page guard change.
- [x] Add deterministic coverage for course keyword expansion, candidate scoring, ambiguity handling, and low-similarity rejection.
- [x] Run `python -m unittest discover -s tests` after the course-matching change.
- [x] Run `python -m py_compile main.py tests\test_closed_page_guards.py tests\test_course_matching.py` after the course-matching change.
- [x] Run `python main.py --help` after adding `--course-url`.
- [x] Run bounded live course-opening smoke for `中国现代史纲要` matching `中国近现代史纲要` without entering chapters or watching videos.
- [ ] Run a bounded live course smoke only when credentials and authorization are available.

## Future Work

- [ ] Add structured logging if long-run diagnostics need cleaner output.
- [ ] Add selector profiles only if another course platform becomes a real requirement.
- [ ] Re-evaluate tutai or another remote runner only after a viable Chaoxing network path is available.

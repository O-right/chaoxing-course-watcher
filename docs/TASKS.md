# Tasks

## Setup

- [x] Create standalone GitHub repository `O-right/chaoxing-course-watcher`.
- [x] Clone standalone local repository at `D:\chaoxing_course_watcher`.
- [x] Include `main.py`, `run_chaoxing.ps1`, `requirements.txt`, `.gitignore`, and README.
- [x] Add project handoff docs and repo rules.

## Validation

- [x] Verify repository tracks `git@github.com:O-right/chaoxing-course-watcher.git`.
- [x] Verify the local feature branch tracks `origin/codex/course-matching-guards`.
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
- [x] Run a bounded authorized course-opening smoke without entering chapters or watching videos.
- [x] Integrate latest `origin/main` open-source hardening into the feature branch and resolve the README conflict.
- [x] Preserve `--course-url` documentation and add `CX_COURSE_URL` to the safe environment template.
- [x] Re-run 9 unit tests, Python compilation, CLI help, ignore/template checks, and staged diff checks after integration.
- [x] Review and merge PR #1 after GitHub confirms the synchronized branch is conflict-free.
- [ ] Run a bounded live course smoke only when credentials and authorization are available.

## Open Source Preparation

- [x] Rewrite README in Chinese with project purpose, setup, usage, limits, privacy guidance, and Star request.
- [x] Redact private URL details from page, candidate, navigation, and exception logs.
- [x] Require explicit course configuration and use conservative playback/commitment defaults.
- [x] Pin verified Python dependency versions.
- [x] Add read-only offline GitHub Actions checks and weekly Dependabot updates.
- [x] Scan the current tree and all Git commits with custom sensitive-path and credential rules.
- [x] Add `security_best_practices_report.md`.
- [x] Run 14 unit tests, compilation, direct/launcher CLI help, dependency, README, CI, ignore, secret-pattern, and diff checks.
- [x] Add standard MIT `LICENSE` for `O-right`.
- [x] Confirm existing author-email and course metadata in Git history is acceptable; do not rewrite history.
- [x] Verify official gitleaks checksum and pass Git-history plus working-directory scans.
- [x] Run pip-audit, upgrade vulnerable `python-dotenv` from `1.2.1` to `1.2.2`, and confirm zero known vulnerabilities.
- [x] Push the branch and confirm Python 3.10/3.11 GitHub Actions passes.
- [x] Owner reviews and approves the final Chinese README and repository publication.
- [x] Review and merge PR #1 before changing repository visibility.
- [x] Set the GitHub description to `学习通自动刷课脚本` and publish the repository.

## Future Work

- [ ] Add structured logging if long-run diagnostics need cleaner output.
- [ ] Add selector profiles only if another course platform becomes a real requirement.
- [ ] Re-evaluate tutai or another remote runner only after a viable Chaoxing network path is available.

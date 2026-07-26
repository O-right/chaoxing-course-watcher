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

## Post-Release Hardening (branch `fix/silent-completion-and-resilience`)

### Silent false-completion fixes

- [x] Stop `current_video_locator` falling back to the page's first `<video>` when an explicit index cannot be resolved.
- [x] Add `scanned_after_active` so a catalog whose active item is last returns `not_found` instead of `completed`.
- [x] Replace the dead `visited_urls` guard with `unit_visit_counts` re-entry counting (`CX_MAX_UNIT_REVISITS`).
- [x] Return `False` when the `CX_MAX_CHAPTERS` cap is reached.
- [x] Make `incomplete_learning_signals` return `Optional` and fail closed when nothing could be read.
- [x] Warn and screenshot when the resource-card selector matches nothing on a page that has video/iframe content.
- [x] Verify login actually succeeded and run the blocking-verification handler on the login step.

### Unattended-run resilience

- [x] Add bounded per-unit retries (`CX_UNIT_RETRIES`) that retry without skipping.
- [x] Move the randomized delay outside the `expect_popup` window and reclaim orphaned tabs.
- [x] Scale the stall threshold by `sleep x playback rate`.
- [x] Add `CX_MAX_UNKNOWN_DURATION_POLLS` for streams that never report a duration.
- [x] Add opt-in session persistence (`CX_STORAGE_STATE_PATH`) with skip-form-when-restored handling.

### Latency

- [x] Remove the duplicate main-frame probe and budget per-candidate timeouts in `find_locator_in_page_or_frames`.
- [x] Collapse the 14 sequential play-control probes into 3 priority groups.
- [x] Bound the `networkidle` wait with `CX_SETTLE_TIMEOUT_MS` after `domcontentloaded`.
- [x] Shorten the video wait on pages with no `<video>` at all.
- [x] Extend `--fast-actions` to the remaining fixed waits without changing defaults.

### Configuration and tooling

- [x] Support `CX_SELECTOR_<KEY>` overrides for all selectors; move the two inlined selectors into `CONFIG`.
- [x] Document all 45 `CX_*` variables in `.env.example` and add a drift test.
- [x] Remove the 15 duplicated `.get(key, literal)` defaults.
- [x] Add `validate_config` and warn on unparseable env values.
- [x] Group course candidates by `href` before the ambiguity check.
- [x] Anchor `run_chaoxing.ps1` paths with `$PSScriptRoot`.
- [x] Add `persist-credentials: false` and a ruff step to CI; switch tests to `-t .`.

### Verification

- [x] Extract pure decision functions and cover them; suite grew from 14 to 44 tests.
- [x] Mutation-test the new regression tests to confirm they fail when the fixes are reverted.
- [x] Run compile, unit tests, ruff, CLI help, launcher help, and `git diff --check`.
- [ ] Run a bounded authorized live session against a task point with **multiple videos**.
- [ ] Run a bounded authorized live session against a catalog whose active item is the **last visible entry**.
- [ ] Push the branch and confirm the new ruff CI step passes on a GitHub-hosted runner.
- [ ] Decide whether to merge to `main` after live evidence exists.

## Future Work

- [ ] Review and merge Dependabot PR #2 (`actions/setup-python 6.3.0`) after its diff and CI pass review.
- [ ] Review and merge Dependabot PR #3 (`actions/checkout 7.0.0`) after its diff and CI pass review.
- [ ] Review Dependabot PR #4 (`playwright 1.61.0`) independently and verify tests before merging.
- [ ] Add structured logging if long-run diagnostics need cleaner output.
- [ ] Add selector profiles only if another course platform becomes a real requirement.
- [ ] Re-evaluate tutai or another remote runner only after a viable Chaoxing network path is available.

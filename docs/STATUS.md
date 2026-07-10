# Status

## Current Phase

Open-source preparation is in progress on the feature branch; the GitHub repository remains private.

## Current Focus

This repository now contains only the course-watching workflow. The active local clone is `D:\chaoxing_course_watcher`, tracking `git@github.com:O-right/chaoxing-course-watcher.git`. The old combined workspace at `D:\course_rpa_node` should be treated as a handoff/archive location, not the normal place for course-watcher commits.

The `codex/course-matching-guards` branch now combines course-matching and closed-page guards with a Chinese public README, privacy-safe logging, explicit course configuration, conservative public defaults, pinned dependencies, offline CI, Dependabot, and an open-source readiness report. The repository must not be made public until the owner selects a license and decides whether existing author-email and course-validation metadata in Git history is acceptable.

## Recent Evidence

- Previous authorized live runs from the combined workspace covered full-course completion, a no-unfinished audit, and mixed courseware/video resource handling.
- The standalone clone is active at `D:\chaoxing_course_watcher` and tracks `git@github.com:O-right/chaoxing-course-watcher.git`.
- Closed-page guards cover video detection, progress reads, and debug screenshots; scored course selection covers exact, suffix, similarity, ambiguity, and rejection paths.
- Latest `origin/main` open-source hardening was integrated into the feature branch; the only textual merge conflict was resolved in `README.md`.
- `.env.example` now documents `CX_COURSE_URL` with an empty value, `.env` remains ignored, and no private template values are populated.
- `python -m unittest discover -s tests` passed with 14 tests after open-source hardening.
- `python -m py_compile main.py tests\test_closed_page_guards.py tests\test_course_matching.py` passed after the integration.
- `python main.py --help` and `.\run_chaoxing.ps1 --help` passed and show `--course-url`.
- Pinned dependencies resolved locally and `python -m pip check` passed.
- README structure, CI permissions, full-SHA Action pins, Dependabot configuration, secret-pattern checks, ignore checks, and `git diff --check` passed.
- A custom scan of all 10 Git commits found no sensitive-path files, high-confidence credentials, course-ID URL parameters, or mobile-number patterns.
- A bounded authorized course-opening smoke previously verified similarity matching without entering chapters or processing videos.

## Next Steps

- Select and add an open-source license.
- Decide whether to accept or rewrite the existing author-email and named-course metadata in Git history.
- Run dedicated `gitleaks` and `pip-audit` checks; the temporary `pip-audit` attempt timed out.
- Push the open-source preparation changes, confirm GitHub Actions, and review PR #1 before merging to `main`.
- Re-run the target course in a bounded live session to confirm the closed-page guard behavior in the real Chaoxing flow.
- Use headed mode with manual verification wait if the platform presents a visible verification or the browser closes during a headless run.
- Keep local `.env` outside Git and do not print or commit private course URLs.

## Blockers And Cautions

- `.env` exists locally for this clone but is intentionally ignored and must not be committed or printed.
- No `LICENSE` exists yet, so the repository is not ready to become public.
- Git history contains a non-noreply author email and named course evidence; history rewriting requires an explicit owner decision.
- Dedicated secret scanning is not installed, and the temporary dependency vulnerability audit timed out.
- The new GitHub Actions workflow has not run remotely yet.
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
- `security_best_practices_report.md`
- `.github/workflows/ci.yml`
- `.github/dependabot.yml`
- `AGENTS.md`
- `tests/test_closed_page_guards.py`
- `tests/test_course_matching.py`
- `docs/`

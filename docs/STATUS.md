# Status

## Current Phase

Open-source preparation is in progress on the feature branch; the GitHub repository remains private.

## Current Focus

This repository now contains only the course-watching workflow. The active local clone is `D:\chaoxing_course_watcher`, tracking `git@github.com:O-right/chaoxing-course-watcher.git`. The old combined workspace at `D:\course_rpa_node` should be treated as a handoff/archive location, not the normal place for course-watcher commits.

The `codex/course-matching-guards` branch now combines course-matching and closed-page guards with a Chinese public README, privacy-safe logging, explicit course configuration, conservative public defaults, pinned dependencies, offline CI, Dependabot, an MIT license, and an open-source readiness report. The owner accepts the existing author-email and course-validation metadata in Git history. Automated release checks are complete; the repository remains private while the owner reviews the README.

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
- A custom scan of the complete reachable Git history found no sensitive-path files, high-confidence credentials, course-ID URL parameters, or mobile-number patterns.
- GitHub Actions run `29083118433` passed Python 3.10 and 3.11 dependency installation, 14 tests, compilation, and Chinese CLI help on Windows.
- Added standard MIT license with `Copyright (c) 2026 O-right`.
- Verified gitleaks `8.30.1` official archive SHA256; Git-history and working-directory scans both reported no leaks.
- pip-audit `2.10.1` found `CVE-2026-28684` in `python-dotenv==1.2.1`; upgrading to `1.2.2` cleared the audit to zero known vulnerabilities.
- A bounded authorized course-opening smoke previously verified similarity matching without entering chapters or processing videos.

## Next Steps

- Owner reviews the final Chinese README.
- Review the clean, mergeable Draft PR #1 before merging to `main`.
- Keep repository visibility private until the README and PR are approved.
- Re-run the target course in a bounded live session to confirm the closed-page guard behavior in the real Chaoxing flow.
- Use headed mode with manual verification wait if the platform presents a visible verification or the browser closes during a headless run.
- Keep local `.env` outside Git and do not print or commit private course URLs.

## Blockers And Cautions

- `.env` exists locally for this clone but is intentionally ignored and must not be committed or printed.
- The owner accepts that existing Git history exposes a non-noreply author email and named course evidence.
- Do not claim new live completion without a fresh configured run.
- The reported closed-page failure has local guard coverage, but the exact live Chaoxing course path has not been re-run after the fix.
- The course-matching optimization has deterministic unit coverage and one bounded live course-opening smoke, but not full course-flow validation.
- PR #1 is clean and mergeable, and its Python 3.10/3.11 GitHub Actions checks pass; it remains a Draft.
- The removed tutai deployment is not a viable current runner until its Chaoxing network block is resolved.

## Active Files

- `main.py`
- `run_chaoxing.ps1`
- `requirements.txt`
- `README.md`
- `LICENSE`
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

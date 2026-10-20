# Decisions

## 2026-06-15: Course Watcher Is A Standalone Repository

Decision: Use `O-right/chaoxing-course-watcher` as the canonical GitHub repository and `D:\chaoxing_course_watcher` as the active local clone for course-watching work.

Reason: The former combined workspace was split into workflow-specific repositories. Course watching and assignment automation have different commands, dependencies, risk profiles, and handoff needs.

## 2026-06-15: Keep Runtime Secrets Out Of Git

Decision: Keep `.env`, logs, screenshots, browser profiles, cookies, tokens, credentials, and private course URLs untracked.

Reason: The course watcher requires private account and course configuration for live runs, but source control should contain only reusable automation code and public documentation.

## 2026-06-15: Completion Requires Observable Evidence

Decision: Continue requiring real video end states, checked no-next completion paths, and bounded live evidence before claiming course completion.

Reason: Previous Chaoxing runs showed false-completion risks from no-next pages, early near-end advancement, true no-source videos, and mixed courseware/video resource cards.

## 2026-06-27: Course Selection Uses Scored Candidates

Decision: Course-name lookup should collect visible course candidates, score normalized title/text variants, and reject close ambiguous matches instead of clicking the first partial text match. `CX_COURSE_URL` / `--course-url` is the exact-entry fallback when keyword matching is uncertain.

Reason: Short keywords such as a subject name can match multiple course cards. Failing with candidate diagnostics is safer than opening the wrong course, while direct URLs preserve a deterministic path for authorized known courses.

## 2026-07-10: Public Release Uses Privacy-Safe Explicit Defaults

Decision: Public builds require explicit course configuration, redact URL paths and query data from logs, default playback to `1.0`, keep automatic commitment confirmation disabled, pin verified dependencies, and require license plus Git-history privacy review before changing repository visibility to public.

Reason: A reusable public repository should not target a specific course, disclose private course identifiers in diagnostics, silently accept learning commitments, or publish without clear reuse terms and an explicit decision about historical personal metadata.

Release choice: Use the MIT License with `Copyright (c) 2026 O-right`. The owner accepts the existing non-noreply author email and named course evidence in Git history, so the repository will not rewrite existing commits before publication.

## 2026-07-27: Ambiguous Or Unreadable State Must Fail Closed, Never Report Success

Decision: Any path that cannot positively confirm progress must fail loudly rather than fall through to a success verdict. Concretely: `incomplete_learning_signals` returns `None` when no container could be read and the caller treats that as unreadable rather than complete; `click_unfinished_chapter_from_catalog` returns `not_found` when it scanned nothing instead of `completed`; `current_video_locator` refuses to substitute the page's first `<video>` when an explicit index cannot be resolved; and reaching `CX_MAX_CHAPTERS` returns `False`.

Reason: The tool's only real product is "this content was actually watched". Every one of these paths previously converted a detection failure into an exit code of 0, which is the worst possible outcome because it is silent and indistinguishable from real completion. A noisy failure costs a restart; a false success costs the course.

Consequence: The exit-code contract changed. Hitting the chapter cap is now exit 1. Any wrapper that treated exit 0 as "finished" must be revisited.

## 2026-07-27: Retry Failed Task Points, But Never Skip Them

Decision: `process_unit_with_retries` retries a failed learning unit up to `CX_UNIT_RETRIES` times and then fails the whole run. It does not advance past a unit it could not complete.

Reason: A single transient failure ending a multi-hour run is a real cost, so bounded retries are worth it. But the obvious "skip and continue" variant would silently leave unwatched task points behind and report success, which is exactly the failure class this round was fixing. Requiring a human restart is an acceptable price; silent gaps are not.

## 2026-07-27: Speed Work Must Not Trade Away Completion Credit

Decision: Latency fixes target wasted waiting only — duplicate frame probes, per-candidate timeouts that ignored the caller's budget, `networkidle` waits that can never settle, and waiting for a `<video>` on a page that has none. Deliberate waits that exist so the platform can record progress keep their defaults; `video_completion_settle_seconds` and `learning_card_switch_wait_seconds` are shortened only under the explicit `--fast-actions` opt-in.

Reason: Shortening the post-completion settle window trades a possible loss of completion credit for about 1.5 seconds per video. That is the wrong side of the trade for this tool, and it should never happen implicitly.

## 2026-07-27: Stall Detection Is Relative, Not Absolute

Decision: The stall threshold is computed from the previous iteration's actual sleep and the observed playback rate, bounded by `CX_PROGRESS_STALL_EPSILON_SECONDS`, rather than comparing against that absolute value directly. `validate_config` additionally warns when `poll x rate` is close to the configured epsilon.

Reason: The expected per-iteration advance is `sleep x rate`, not a constant. With the absolute comparison, a healthy video trips the stall counter whenever `poll x rate <= epsilon` — reachable through the documented `--progress-poll-seconds 0.5`, and reachable at a 1.0s poll whenever the platform throttles playback to 0.5x. The counter then burns all 18 recovery attempts and fails the run. Defaults were never affected, which is why this went unnoticed.

## 2026-07-27: Selectors Are Configuration, Enforced By A Drift Test

Decision: Every entry in `CONFIG["selectors"]` accepts a `CX_SELECTOR_<KEY>` override, the two selectors previously inlined in method bodies moved into `CONFIG`, and `tests/test_env_documented.py` fails the build when a `CX_*` read has no counterpart in `.env.example`.

Reason: `AGENTS.md` already required selectors to stay configurable, but all twelve were hardcoded with no override path, so a Chaoxing front-end change meant editing source. Documentation of tunables had also drifted to 22 of 45 variables. A test is the only thing that keeps this from silently rotting again — it caught two omissions during this round's own implementation.

Note: `video_play_control` now uses `;` between priority groups and `,` within a group, so a single query serves each group. Grouping is required because a merged query returns `.first` in DOM order, which would let a generic text selector outrank a player-specific button.

## 2026-07-27: Add Ruff, Do Not Add A Type Checker

Decision: CI runs `ruff check --select F821,F811,E9`. No mypy or pyright.

Reason: The realistic defect in a 2342-line single file with 69 methods is a mistyped name or a duplicated method sitting on a branch the tests never reach, where the sole `except Exception` at the top of `run()` turns it into a generic message and exit 1 with no traceback. F821/F811 catch exactly that for about three seconds per CI run. A type checker, by contrast, would mostly report `Any` flowing out of `Locator.evaluate()` and `page.evaluate()`, which no annotation can narrow — hundreds of complaints, no real defects.

## 2026-07-27: Keep The Single Class; Extract Only What Needs Testing

Decision: `CourseAutoTester` stays as one class. The only extractions are module-level pure functions for the decisions that most need coverage: `video_is_complete`, `stall_epsilon_for`, `next_poll_seconds`, and `classify_completion_scan`.

Reason: The highest-risk logic was untestable because it was inline arithmetic inside a `while` loop that also called seven collaborators and slept. Extracting those four made it directly assertable and took the suite from 14 to 44 tests. A broader decomposition of the class would be a large refactor with no defect behind it, on a personal single-purpose tool that is explicitly not a framework.

## 2026-07-27: Session Persistence Is Opt-In

Decision: `CX_STORAGE_STATE_PATH` defaults to empty. When set, the login session is saved after a successful login and reused on the next start, and `login()` skips the form when a restored session already left the passport page.

Reason: Reusing a session avoids replaying the login step, which is where verification challenges appear. But the file holds login cookies and is equivalent to stored credentials, so writing it must be a deliberate choice rather than a default side effect of running the tool.

## 2026-07-10: Use A Chinese Public Display Name And Stable Repository Slug

Decision: Present the project as `学习通自动刷课脚本` in the README heading and GitHub repository description, while retaining the existing `chaoxing-course-watcher` repository slug.

Reason: The Chinese display name states the project's purpose directly. Keeping the existing slug avoids breaking clone commands, links, and the already-open pull request immediately before publication.

## 2026-10-19: Poll Browser State With Playwright Waits, Not `time.sleep`

Decision: A loop that waits for browser-side state by re-reading cached sync-API properties (`page.url`, `page.frames`) must pause with `page.wait_for_timeout(...)` or another Playwright call, never with `time.sleep`.

Reason: In the sync API those properties change only when Playwright processes driver events, and that happens during Playwright calls. In the 2026-10-19 live run, `page.url` stayed on the passport host for 20 seconds after a successful login while the loop slept. The same loop using `wait_for_timeout` saw the redirect at 0.8 seconds. Loops that already call `evaluate`, `wait_for`, or `count` every iteration are unaffected, which is why only the new login check hit this.

Alternatives: Keeping `time.sleep` with a dummy `evaluate` works but hides why it is needed. `page.wait_for_url(predicate)` would also work, but the explicit polling loop matches the rest of the file and re-runs the closed-page guard every iteration.

## 2026-10-19: An Unlinked Course Candidate Inherits A Card Link Only When It Is Unambiguous

Decision: The live course list wraps `a.color1` in `h3.inlineBlock`. When a matched element is not inside a link, `course_candidate_details` walks up from the element to the first level that contains links. It adopts the href only if that level has exactly one distinct non-`javascript:` link; otherwise href stays empty. Python-side ranking never merges candidates by text.

Reason: Without an href, the title wrapper could not be grouped with its own link, so the course was rejected as ambiguous against itself. Merging by text instead would also merge two genuinely different courses with the same title. The live list contains such a pair, and merging them would open one at random.

Consequence: An unlinked title in a card with several distinct links still fails as ambiguous. `--course-url` remains the exact fallback.

## 2026-10-20: The Desktop UI Is A Thin Tkinter Shell Over `main.py`

Decision: `gui.py` uses Tkinter from the standard library and runs `main.py` as a subprocess, passing settings as `CX_*` environment variables. It does not import or reimplement any workflow logic. When asked to remember settings, it updates only its managed keys in `.env`.

Reason: The owner asked for a simple, polished UI with only useful features. Tkinter adds no dependency. A local web UI would need a server that accepts the account password over HTTP and would add a framework. A hosted page cannot start local processes at all. A subprocess keeps `main.py` the single source of truth for completion, failure, and exit codes, and a crash in the workflow cannot take the window down. The owner's `.env` also holds unrelated secrets, so rewriting the whole file was never an option.

Consequence: The UI learns progress by parsing log lines, so `tests/test_gui.py` asserts that the parsed markers still exist in `main.py`. Values python-dotenv cannot round-trip are not saved. Shortcuts must carry the window's AppUserModelID for taskbar pinning to work, which needs `IPropertyStore`; `WScript.Shell` cannot set it.

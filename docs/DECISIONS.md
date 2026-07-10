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

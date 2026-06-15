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

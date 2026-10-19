# 2026-10-19 — Bounded live validation on an authorized course

## Command

```
# Git Bash, repo root; credentials from local .env; default timing (no --fast-actions)
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python -u main.py --course "<exact course title>" --max-chapters 200 --headless --browser-channel chrome > logs/live_run_20261019_<n>.log 2>&1
```

## Inputs

- Branch `fix/silent-completion-and-resilience`: `7c60c3f` for attempts #1-#2, then working-tree fixes that were committed as `a8c91ae`.
- One authorized course on the owner's account: 6 task points, 2 already complete, 4 single-video task points remaining (videos from about 2.5 to 17 minutes; completion rule "watch time >= 90%, no seeking"). The course title is deliberately not recorded in this public repo.
- Python 3.11.9, Playwright 1.58.0, system Chrome 155 (`--browser-channel chrome`), Windows 11.

## Outputs

- `logs/live_run_20261019_1.log` ... `logs/live_run_20261019_5.log` and `logs/screenshots/20261019_*.png` — local only, gitignored; they show the account display name and school.

## Numbers

- Attempts: 5. Passed: 1 (#5). Failed: 4, all exit 1, none reported false success.
- #1: keyword differed from the real title (similarity about 0.67, below the 0.68 gate) -> `no_match`. Correct by design; re-ran with the exact title.
- #2: login actually succeeded, but the single post-click URL read raced the redirect -> "still on passport".
- #3: first fix polled `page.url` with `time.sleep`; the sync API never processed the navigation event, so the cached URL stayed on passport for the whole 8 s budget. A diagnostic with `page.wait_for_timeout` saw the redirect at 0.8 s.
- #4: login OK; course match `ambiguous` — the card's `h3.inlineBlock` (no href) tied 1.000 with its own `a.color1`.
- #5 (with `a8c91ae`): login OK, exact match, 4 task points each played to the end at 1.0x, then catalog scan `not_found` -> completion scan clear -> no next control -> completed, exit 0. Wall clock about 31 minutes.

## Validation

- Platform side: a separate read-only login after #5 showed the course at 6/6 task points, 100%. A mid-run screenshot already showed the first three units checked off, so credit was recorded per unit, not only at the end.
- Last-catalog-entry fix exercised for real: after the final unit the catalog scan logged "章节目录中没有找到可靠的未完成任务点" (`not_found`) instead of declaring completion, and completion was only reported after the incomplete-marker scan and the missing next control.
- Not exercised: a task point with multiple videos (every remaining unit had one video), multi-card task points, `--fast-actions` timing, headed mode, manual verification wait, `CX_STORAGE_STATE_PATH`.

## Risks / Follow-ups

- `warn_if_card_tabs_missing` fired on all 4 units: the new "章节详情" layout shows no resource-card tab bar for single-video units, so the warning is a false positive here and saves one screenshot per unit. Whether multi-card units in this layout still expose `#prev_tab` / `.prev_list` is unknown, so the warning cannot simply be removed.
- Non-course links such as "添加课程" scored 0.847 because their container text includes the whole course list. Harmless while the real card scores higher, but scoring leans on container text.
- A `no_match` result does not print the closest candidates; a near-miss keyword can only be diagnosed from the screenshot.

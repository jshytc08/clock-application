# Graph Report - clock-application  (2026-09-09)

## Corpus Check
- 15 files · ~6,499 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 119 nodes · 177 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ab3fa62a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- package.json
- main.js
- core.mjs
- .prettierrc.json
- check.py
- test_api.py
- test_browser.py
- get_all_timezones
- AGENTS.md
- README.md

## God Nodes (most connected - your core abstractions)
1. `tick()` - 13 edges
2. `get_all_timezones()` - 8 edges
3. `open_app()` - 8 edges
4. `toggleFavorite()` - 7 edges
5. `formatDuration()` - 6 edges
6. `createCard()` - 6 edges
7. `zoneName()` - 5 edges
8. `restoreState()` - 5 edges
9. `save()` - 5 edges
10. `make()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `toggleFavorite()` --calls--> `validZone()`  [EXTRACTED]
  app/static/js/main.js → app/static/js/core.mjs
- `tick()` --calls--> `formatDuration()`  [EXTRACTED]
  app/static/js/main.js → app/static/js/core.mjs
- `alarmPreview()` --calls--> `nextAlarm()`  [EXTRACTED]
  app/static/js/main.js → app/static/js/core.mjs
- `createCard()` --calls--> `zoneName()`  [EXTRACTED]
  app/static/js/main.js → app/static/js/core.mjs
- `toggleFavorite()` --calls--> `zoneName()`  [EXTRACTED]
  app/static/js/main.js → app/static/js/core.mjs

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "package.json"
Cohesion: 0.14
Nodes (13): devDependencies, prettier, engines, node, name, private, scripts, format (+5 more)

### Community 1 - "main.js"
Cohesion: 0.17
Nodes (23): zoneName(), alarmDate(), alarmPreview(), alertUser(), catalog, chime(), clockNow(), createCard() (+15 more)

### Community 2 - "core.mjs"
Cohesion: 0.35
Nodes (9): defaultState(), durationSeconds(), formatDuration(), nextAlarm(), restoreState(), validZone(), previewTimer(), renderTimer() (+1 more)

### Community 3 - ".prettierrc.json"
Cohesion: 0.50
Nodes (3): endOfLine, printWidth, singleQuote

### Community 10 - "test_api.py"
Cohesion: 0.13
Nodes (6): health(), get, read_root(), security_headers(), middleware, Request

### Community 13 - "test_browser.py"
Cohesion: 0.20
Nodes (13): fixture, base_url(), browser(), open_app(), page(), Real browser regression checks; each test gets isolated browser storage., test_alarms_validation_duplicate_limit_safe_labels_and_due_delivery(), test_blocked_storage_and_failed_sync_remain_usable() (+5 more)

### Community 18 - "get_all_timezones"
Cohesion: 0.22
Nodes (12): get_all_timezones(), get_server_time(), get_time(), get, Read-only time API with bounded, deterministic catalog queries., TimezonePage, BaseModel, ge (+4 more)

### Community 46 - "README.md"
Cohesion: 0.17
Nodes (10): Alert behavior and privacy, Read-only API, Release status, Run locally, Verify before committing, What it does, Before opening the production URL to users, Development (+2 more)

## Knowledge Gaps
- **28 isolated node(s):** `singleQuote`, `printWidth`, `endOfLine`, `catalog`, `epochAnchor` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `singleQuote`, `printWidth`, `endOfLine` to the rest of the system?**
  _28 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `test_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._
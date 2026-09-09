# Graph Report - clock-application  (2026-09-09)

## Corpus Check
- 18 files · ~7,559 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 134 nodes · 203 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0f528276`
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
7. `loadCatalog()` - 6 edges
8. `build_pages()` - 6 edges
9. `zoneName()` - 5 edges
10. `restoreState()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `test_static_export_contains_only_public_web_assets()` --calls--> `build_pages()`  [EXTRACTED]
  tests/test_pages.py → scripts/build_pages.py
- `base_url()` --calls--> `build_pages()`  [EXTRACTED]
  tests/test_browser.py → scripts/build_pages.py
- `loadCatalog()` --calls--> `fetchCatalogPage()`  [EXTRACTED]
  app/static/js/main.js → app/static/js/catalog.mjs
- `toggleFavorite()` --calls--> `validZone()`  [EXTRACTED]
  app/static/js/main.js → app/static/js/core.mjs
- `previewTimer()` --calls--> `durationSeconds()`  [EXTRACTED]
  app/static/js/main.js → app/static/js/core.mjs

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "package.json"
Cohesion: 0.14
Nodes (13): devDependencies, prettier, engines, node, name, private, scripts, format (+5 more)

### Community 1 - "main.js"
Cohesion: 0.14
Nodes (28): formatDuration(), MAX_ALARMS, zoneName(), alarmDate(), alarmPreview(), alertUser(), catalog, chime() (+20 more)

### Community 2 - "core.mjs"
Cohesion: 0.24
Nodes (10): fetchCatalogPage(), paginateCatalog(), defaultState(), durationSeconds(), MAX_DURATION, MAX_FAVORITES, nextAlarm(), restoreState() (+2 more)

### Community 3 - ".prettierrc.json"
Cohesion: 0.50
Nodes (3): endOfLine, printWidth, singleQuote

### Community 10 - "test_api.py"
Cohesion: 0.13
Nodes (6): health(), get, read_root(), security_headers(), middleware, Request

### Community 13 - "test_browser.py"
Cohesion: 0.15
Nodes (17): fixture, Path, build_pages(), Export only public web assets for static hosting, including project subpaths., base_url(), browser(), open_app(), page() (+9 more)

### Community 18 - "get_all_timezones"
Cohesion: 0.22
Nodes (12): get_all_timezones(), get_server_time(), get_time(), get, Read-only time API with bounded, deterministic catalog queries., TimezonePage, BaseModel, ge (+4 more)

### Community 46 - "README.md"
Cohesion: 0.14
Nodes (12): Alert behavior and privacy, GitHub Pages, Read-only API, Release status, Run locally, Verify before committing, What it does, Before opening the production URL to users (+4 more)

## Knowledge Gaps
- **31 isolated node(s):** `singleQuote`, `printWidth`, `endOfLine`, `MAX_DURATION`, `catalog` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `singleQuote`, `printWidth`, `endOfLine` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `main.js` be split into smaller, more focused modules?**
  _Cohesion score 0.14482758620689656 - nodes in this community are weakly interconnected._
- **Should `test_api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._
- **Should `test_browser.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1471861471861472 - nodes in this community are weakly interconnected._
- **Should `README.md` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
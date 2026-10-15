# Feature: Calc Data tab redesign (Tabbed Office)

- **Locator:** `product/odd/tasks/calc-data-redesign.md`
- **Engram mirror:** `odd/calc-data-redesign/tasks`
- **Repo / branch:** `/mnt/games/libreoffice/core`, `feature/calc-data-redesign` (from 99aa23f56, the tip of `feature/calc-home-redesign`)
- **SDD workspace:** `/mnt/games/libreoffice/core/.superpowers/sdd/2026-10-12-calc-data-redesign/` (briefs, reports, review packages, ledger)

## Objective

Give the Tabbed Office Data tab Excel's layout: every button of the user's Excel 2016 Data tab, in Excel's 7 sections plus Analyze (Statistics). Buttons whose feature LibreOffice lacks are placeholders: a labelled, iconed command with no implementation, shown greyed out.

## Problem and why

The user's words: "arrancamos con la pestaña data. Este seria el resultado final" (Excel 2016 Data tab screenshot), then "vamos con todo ahora, y lo que no haya no funciona. Queda para despues la implementacion en codigo".

The Data tab is still LibreOffice's upstream page (5 sections, one toolbox per button, LO grouping). Home is done; Data is the next slice of the same redesign.

## Sources

- **Approved layout:** `product/docs/design/calc-data-tab-layout.txt` (approved 2026-10-12).
- **Command map:** exploration recorded in the SDD ledger (Excel item -> `.uno:` command, missing icons).
- **Tooling reference:** `product/docs/calc-home-redesign.md` in the repo.

## Scope

**In scope:**
- The Data page of `sc/uiconfig/scalc/ui/notebookbar_office.ui`, generated from `product/ui/calc_data.json`.
- Config-only menus: Other Sources, What-If, Refresh, Group, Ungroup (popups); Statistics as a ribbon dropdown.
- 9 placeholder commands (labels + tooltips, no implementation): From Database, Recent Sources, Connections, Properties, Reapply, Flash Fill, Relationships, Manage Data Model, Forecast Sheet.
- Split buttons with dedicated Calc slots (Merge & Center recipe): Refresh, Group, Ungroup.
- Fluent-based icons for every Data button.
- Docs and validation screenshots.

**Out of scope (later features):** implementing the 9 placeholders (From Database with PostgreSQL first: enable LibreOffice's existing postgresql SDBC driver in the build), other tabs, Writer/Impress, translations.

## Constraints

- Same as Home: build only through `product/dev/lo-make.sh`; no class-layout changes in public `include/` headers without a full rebuild; existing upstream variants (`notebookbar.ui` etc.) untouched; the office `.ui` stays "upstream + generated pages"; Conventional Commits (subject <= 79 chars), no AI attribution; never commit `.superpowers/`.
- Controller registrations are per command + module: a split or dropdown must use a dedicated command, never an existing one used by other toolbars.
- Every new state-bearing slot must be invalidated wherever its original command is (lesson from Merge & Center).

## Acceptance criteria

- Data tab shows the 8 sections and every button of the approved layout, placeholders greyed out.
- Split buttons act on body click and open their menu on the arrow.
- Unit tests, gla11y/lint, UITests pass; light/dark screenshots approved by the user.

## TDD

- **Mode:** strict.
- **Runners:** `python3 -I -m unittest discover -s product/tests -t .`; `product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.<test>`; `product/dev/check-ui.sh <ui>`.
- Rendering-only checks use measured screenshots (`product/dev/shot.sh`).

## Delivery

- **Forecast:** about 800 authored lines (layout JSON, generator, xcu labels and menus, 3 slots, icon manifest, tests, docs); generated `.ui`/`suppr` excluded.
- **Strategy:** ask-on-risk. No product remote exists, so no pull request can be opened; the chain question (stacked-to-main or feature-branch-chain) is asked when the user decides to push. One work-unit commit (or more) per task, recorded below.
- **RDD:** on (default). Boundary for this feature: 99aa23f56. After each task commit: `gentle-ai review assess --committed-only`.

## Tasks

| ID | Task | Route | Status | Commits | RDD |
|----|------|-------|--------|---------|-----|
| D1 | Data page from `calc_data.json`: generator multi-page support, all existing-command buttons, config-only dropdowns (Other Sources, What-If, Statistics), 9 placeholder commands, Refresh/Group/Ungroup as plain buttons for now; remove the old `Menu Data` and compact block; tests | delegated (Sonnet) | [x] 73 unit tests, 8 UITests, gla11y 0 new; task review Approved | da39e4c55 | medium: user granted, but START refused (lens_context_budget_exceeded: generated .ui too large to review as one candidate); boundary moved to da39e4c55 |
| D2 | Split buttons Refresh, Group, Ungroup: dedicated slots + controllers + popup menus + invalidations + UITests; plus always-disabled slots for the 9 placeholders (sfx2 force-enables slot-less items) | delegated (Sonnet) | [x] 81 unit tests, 10 UITests (status-listener IsEnabled), placeholders greyed; task review Approved | e00d2feb3 | medium: user granted; 1-lens review approved + acknowledged (advisory: stale-state UITest, invalidation regex) |
| D3 | Icons for every Data button (placeholders included), coverage test | delegated (Sonnet) | [x] 36 icons light/dark, 82 unit tests; task review Approved (minors -> D4) | d8c8cf945 | medium: under budget (slice from e00d2feb3) |
| D4 | Fit 8 sections at 1920 px (sort buttons icon-only first), icon polish (Reapply, Consolidate), state-freshness UITest (one listener across changes), `product/docs/calc-data-redesign.md`, final screenshots, user gate | delegated (Sonnet) | [x] all 8 sections at 1920 px; 84 unit tests, 12 UITests; task review Approved (2 minors fixed by controller); user gate pending | 3f65bb51a, 1ae7c4ffc, e4baee882, f629c100c | D3+D4 medium slice: user declined |

| D5 | Final-review follow-ups: placeholder slots ReadOnlyDoc=FALSE and hidden from Customize, moved to fork block SID_NEW_SLOTS+380.., robust placeholder test, InsertSheetFromFile image flag + image-flag test, Show/Hide Details unfilled, docs (recipe, PostgreSQL prerequisites, Streams, width caveat) | delegated (Sonnet) | [x] 86 unit tests, 12 UITests; review Approved | 5f441f438, 53e663964, 4d851cbce, d2f8c0d6e | medium: under budget (slice from f629c100c) |
| D6 | Split buttons: menu arrow unusable when the body command is disabled (VCL ignores clicks on disabled items). Options: Excel-like (Refresh All always enabled; Ungroup enabled when the sheet has an outline) / dropdown-only / leave | pending user decision | [ ] | | |

## Progress / evidence

- 2026-10-12: layout approved; branch `feature/calc-data-redesign` created from 99aa23f56.

- 2026-10-13: D1-D4 complete; whole-branch final review (Opus) dispatched; user visual gate pending (screenshots in the session scratchpad d4/).

- 2026-10-13: D5 (final-review follow-ups) complete; D6 waiting for the user's decision.

- 2026-10-15: project docs and ODD task files moved into this repo under `product/` (single repo; the separate office-boost workspace is retired).

## Next step

D6 decision (split-button arrow), then the user's visual approval of the Data tab. Later: implement the 9 placeholders one by one (From Database first: enable the postgresql SDBC driver in the build).

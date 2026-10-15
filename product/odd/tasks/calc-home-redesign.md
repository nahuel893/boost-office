# Feature: Calc Home tab redesign (stage A)

- **Locator:** `product/odd/tasks/calc-home-redesign.md`
- **Engram mirror:** `odd/calc-home-redesign/tasks`

## Objective

Add a Calc ribbon variant, "Tabbed Office", whose Home tab has Excel's 8 sections. It uses Fluent-based icons (light and dark) and neutral color schemes. Existing variants do not change.

## Problem and why

The user's words: "antes de agregar cosas, hay que hacer un redising de la UI".

The UI looks dated, disordered and cluttered. Calc's Home tab lacks Excel's section structure, which the user called "clave". This slice validates the visual language before every tab gets redesigned.

## Sources

- **Spec:** `product/docs/superpowers/specs/2026-10-12-calc-home-redesign-design.md`. Annexes are in `product/docs/design/calc-home-*.txt`.
- **Plan:** `product/docs/superpowers/plans/2026-10-12-calc-home-redesign.md`, 10 tasks.

## Scope

**In scope (stage A, declarative only):**
- `sc/uiconfig/scalc/ui/notebookbar_office.ui` and its registration.
- Product tooling under `product/` in `/mnt/games/libreoffice/core`, on branch `feature/calc-home-redesign`.

**Out of scope:**
- Stage B C++ items.
- Other tabs and apps.
- Branding and shipped defaults.
- The paused feature `product/odd/tasks/calc-formulas-tab.md`.

## Constraints

See the plan's Global Constraints. The main ones:
- Builds are memory-capped.
- No edits to existing `notebookbar*.ui` files.
- An isolated dev profile.
- Conventional commits, with no AI attribution.

## Acceptance criteria

These come from spec §1. The user approves the before/after screenshots in light and dark, and every automatic check passes:
- unit tests
- gla11y and lint
- UITests
- the isolation diff

## TDD

- **Mode:** strict, from the session config.
- **Runners:**
  - product unit tests: `python3 -I -m unittest discover -s product/tests -t .`
  - LibreOffice UITest: `product/dev/uitest.sh <module.Class.test>`

## Delivery

- **Forecast:** about 2000 authored lines (tooling, tests, layout JSON, manifest). The generated and copied `.ui` and `suppr` lines are excluded.
- **Strategy:** ask-on-risk.
- **Ruling:**
  - No product remote exists, so no pull request can be opened yet.
  - The chain-strategy question (stacked-to-main or feature-branch-chain) is asked when the user decides to push.
  - Slice boundaries: one work-unit commit per task, recorded below.
- **RDD:** on (default). After each task commit, `gentle-ai review assess --committed-only`.

## Tasks

Execution follows superpowers:subagent-driven-development. Every task is delegated: one implementer and one reviewer per task. Their outputs live in `/mnt/games/libreoffice/core/.superpowers/sdd/2026-10-12-calc-home-redesign/`.

| ID | Task | Route | Status | Commits | RDD |
|----|------|-------|--------|---------|-----|
| T1 | Dev harness + baseline screenshots | delegated (Sonnet) | [x] | 60b188762, 02aacbf01 | high: declined (with T2) |
| T2 | Tabbed Office skeleton (spike 0e = YES) | delegated (Sonnet) | [x] | 1e6895881 | high: declined (with T1) |
| T3 | Spike 0a dropdown menus (user clicked; P3) | delegated (Sonnet) | [x] | 58bd7e65b | passive |
| T4 | Spikes 0b-0d (0c NO, 0d YES; user checks skipped by ruling) | delegated (Sonnet) | [x] | 3aaa937f8 | passive |
| T5 | Ribbon page generator | delegated (Haiku) | [x] | a4593e5d6 | high: declined |
| T6 | Home layout (P4 labelled menus, Excel 365 alignments) | delegated (Sonnet) | [x] | 6f81bdd89, 70f2938c3, 6213acce3 | medium: part 2 approved+acknowledged; part 1 declined |
| T7 | Icon builder + DIRECT icons (fills, crisp 16 px, trim guard) | delegated (Sonnet) | [x] | c0684fa3a, ea6f42cd4 | high: declined (with T6b) |
| T6b | Grow/Shrink to Font row 2 (user request) | delegated (Sonnet) | [x] | b385b5964 | with T7 |
| T8 | COMPOSE icons (badges, highlights) | delegated (Sonnet) | [x] | 66eddd4df | with T9 |
| T9 | Color scheme extension (Boost Light green, Boost Dark) | delegated (Sonnet) | [x] | 8aee18222 | high: 4-lens review approved + acknowledged (T8+T9) |
| T6c | Tabbed Office in the UI picker dialog, Calc only (cui C++) | delegated (Sonnet) | [x] | 8eb8a1dbc, 904266ebd | medium under budget |
| L | One-step launcher product/dev/calc.sh (user request) | inline (controller) | [x] | f5d8d9c63 | |
| T9b | Calc-green cell selector (CalcCellFocus) + launcher reinstalls changed schemes | delegated (Sonnet) | [x] | b83472cc0 | |
| T9c | Thin borders on themed entries/combo boxes (vcl C++) | delegated (Sonnet) | [x] | 5ecf17ffd | |
| T9d | Selected tab: white/#454545 + green underline (vcl C++) | delegated (Sonnet) | [x] | 59a2c7636 | |
| T9e | Gray ribbon separators (SeparatorColor) | delegated (Sonnet) | [x] | 74469ab16 | review approved |
| D | Documentation product/docs/calc-home-redesign.md (user request) | inline (controller) | [x] | 60b290784 | |
| T6d | Cell style list at the bottom of Styles, same height (user request; generator "row"/"valign") | inline (controller; 4 small files, design given by user) | [x] 48 unit tests OK, sc.build, dark screenshot | 0e3d8c44d | high: declined (user: "es leve") |
| T9f | Compact notebookbar rows: ToolBox::SetCompactHeight (private flag) on NotebookbarToolBox; ribbon 27 px shorter, rows 39->30 px; combo rows stay ~35 px | delegated (Sonnet; explorer first) | [x] review Approved after 1 fix round (ABI) | 7c1dd97c5, 8d85e0aae, f9c155c0d | medium: under budget (pending in slice from 0e3d8c44d) |
| T6e | Merge & Center split button: slot .uno:HomeMergeCenter (FID_MERGE_TOGGLE path), Controller.xcu Value=.uno:HomeMergeMenu, invalidations mirrored | delegated (Sonnet; explorer first) | [x] RED/GREEN unit + UITest; review Approved after 1 fix round (stale state) | 45eb3b382, 7f94c7d8a | medium: under budget (slice from 0e3d8c44d) |
| T6f | Cell style combo below Conditional/Table Styles: generator "footer" + "medium" (24 px) style; ribbon +7 px vs before | delegated (Sonnet) | [x] 60 unit tests, gla11y 0 new, UITest OK; review Approved (minors parked) | f9ed0f195, c10f31972 | slice 0e3d8c44d..c10f31972 high: declined by user |
| T9g | Scrollbar sliders visible at rest: ShadowColor, 10 px thick (axis-scoped, 40 px along axis kept, overlay indicators excluded) | delegated (Sonnet; explorer first) | [x] 60 tests, pixel evidence; review Changes requested -> fix round 1 -> controller re-review OK | 140710dc8, 99aa23f56 | medium: under budget (slice from c10f31972) |
| T10 | Validation (steps 1-3) + user review gate | delegated (Sonnet) | [x] steps 1-3; user gate: changes requested and applied (T9b-T9e) | 691a58788 | |

## Progress / evidence

- **2026-10-12:** the plan's code was dry-run in a scratch copy: 33 unit tests OK; gla11y reported 0 new fatals; lint-ui OK.

## Design changes accepted during execution (2026-10-12)
- Number uses the original 0.0 button; Undo section kept; Strikeout, Format as Table, Excel-like Editing (from the user's Excel 365 screenshot).
- Menus via dedicated dropdown commands .uno:Home*Menu (labels need .uno: keys).
- Icons: Office-like soft color fills (Fluent filled silhouette under the outline, a touch of white stays); 16 px slots use the trimmed 20 px design.
- Light theme surfaces soft green (#E4F2E8 family).
- Add Tabbed Office to the UI picker dialog after T6 (C++ cui, extra task).

## Queued user requests (2026-10-12, after T6d)
- T9f: compress the whole ribbon height (user chose "option 2": smaller GTK/VCL padding, rows 39 px apart today; other tabs float centered because the tab control takes the tallest page, vcl/source/control/tabctrl.cxx:2055-2075). Exploring which knob is ribbon-only.
  Route: delegated (Sonnet), dispatched; scope ruling: every notebookbar toolbox, no global CSS.
- T6e: Merge & Center must be an instant split button (body = merge & center, arrow = menu), like Excel. Plan after exploration: new Calc slot `.uno:HomeMergeCenter` (small C++ in sc), Controller.xcu `Value=.uno:HomeMergeMenu`, label, layout cmd. Queued after T9f.
- T9g: scrollbar sliders barely visible unless hovered; user wants white or gray. Queued after T6e.
- T6f (reopens T6d intent): the cell style combo must be BELOW Conditional/Table Styles, not to their right. Plan: generator section "footer" row spanning all columns; large buttons span the rows above. Queued right after T6e (same files).
- Font: user wants an Office-like font (UI and cells). Candidates: Selawik (Microsoft's OFL fallback for Segoe UI), Carlito (Calibri metrics, bundled in instdir), Akasia (young OFL project with Aptos metrics, unverified). Awaiting the user's choice.

## Next step
After context compaction (user request): redesign the **Data** tab of Tabbed Office with the same
tools (gen_ribbon.py layout JSON, icon manifest, schemes). Start with brainstorming the Data tab
layout against Excel 365's Data tab. Pending manual checks from the Home gate: body click on the
new menu buttons, menu/hover/pressed colors. Stage B list: product/docs/stage-a-findings.md and
product/docs/calc-home-redesign.md section 6.

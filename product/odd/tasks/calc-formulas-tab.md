# Feature: Excel-like formula tools in Calc's tabbed UI

Locator: `product/odd/tasks/calc-formulas-tab.md`. Engram mirror: `odd/calc-formulas-tab/tasks`.

## Objective

Give Calc's tabbed NotebookBar the formula features of Excel's "Formulas" tab: Function Library, Defined Names, Formula Auditing, Calculation.

## Problem (corrected 2026-10-12 after T2)

The first premise ("Calc has no Formulas tab") was **wrong**. Master already has a **"Functions" tab** between Data and Review in `sc/uiconfig/scalc/ui/notebookbar.ui`. It is `phbFunctions` at L6671, with tab label `FunctionsLabel1`, and has three groups:

- `gdFunctionsGoalSeeker`: GoalSeek, Solver, ShowInvalid, ShowErrors.
- `gdFunctionsDetective`: AuditingFillMode, ShowPrecedents, ShowDependents, ClearArrowPrecedents, ClearArrowDependents.
- `gdFunctionsStatistics`: statistics dialogs.

The 26.8 build has the same tab. Compared with Excel's Formulas tab, it is missing:

- FunctionDialog and AutoSum.
- Named ranges (AddName, DefineName, InsertName).
- Calculate and CalculateHard.
- ClearArrows (remove all) and ToggleFormula (show formulas).

## Why

This is the first step toward an Office-like UI. It is declarative (XML only, no C++) and upstreamable.

## Decision pending (user)

- **A. Extend the existing Functions tab** with Excel's missing groups. Recommended: no duplication, no tab renumbering, more likely accepted upstream.
- **B. Add a separate Formulas tab.** It duplicates the auditing buttons, requires renumbering the `position` of every later tab (7 to 15), and is less likely accepted upstream.

## Command map (from T2, cited in the T2 report)

- **Labels:** `.uno:AddName` is "Define Name...". `.uno:DefineName` is "Manage Names...". `.uno:InsertName` is "Insert Named Range or Expression...".
- **Commands that do not exist:** `.uno:AutoCalculate`, `.uno:ManageNames`. AutoCalculate is dropped from scope.
- **No colibre icon:** `CalculateHard`, `InsertName`. The fallback rendering is unverified.
- **AutoSum:** `.uno:AutoSum` (`SID_AUTO_SUM`) is exec-only (cellsh.sdi:282). Its label is "Sum" (GenericCommands.xcu).

## Implementation notes

- **Group pattern:** `gdFunctionsGoalSeeker` (L6682-6829) is a GtkGrid with `sfxlo-NotebookbarToolBox` buttons, a vertical separator, and an italic caption label wired with a11y labelled-by/label-for. Ids follow `btn<Tab><Command>` and `bx<Tab><Command>`.
- **Suppressions (build-breaking):** every new `GtkToolButton` needs a `button-no-label` line in `solenv/sanitizers/ui/modules/scalc.suppr`.
- **No C++ dependencies:** no C++ code or uitest depends on tab ids or indexes.

## Scope

- **In scope:** the change in `sc/uiconfig/scalc/ui/notebookbar.ui` plus `solenv/sanitizers/ui/modules/scalc.suppr`, on `master`, branch `feature/calc-formulas-tab`.
- **Out of scope:**
  - Per-category function dropdowns, which need C++.
  - Other notebookbar variants: `notebookbar_compact.ui`, `notebookbar_groups.ui`, `notebookbar_groupedbar_*.ui`.
  - Writer and Impress.
  - Removing buttons from other tabs.
  - AutoCalculate (no command exists).

## Acceptance criteria

1. The formula tools are reachable from Calc's Tabbed UI, grouped the Excel way, according to the chosen option (A or B).
2. Every button dispatches an existing command and shows its standard label. Missing icons are handled explicitly.
3. The gla11y build check reports 0 new fatals. `bin/lint-ui.py` passes.
4. The existing tabs and groups are unchanged, except for the agreed extension.

## Checks

- **gla11y (the build's check):** `python3 -I bin/gla11y -P ./ -s solenv/sanitizers/ui/modules/scalc.suppr --widgets-suffixignored +ValueSet,HBox,VBox,ToolBox,Preview,PreviewWin,PreviewWindow,PrevWindow --widgets-button +svtlo-ManagedMenuButton --fatal-all --not-fatal-type duplicate-mnemonic --not-fatal-type labelled-by-and-mnemonic --not-fatal-type orphan-label sc/uiconfig/scalc/ui/notebookbar.ui`
- **Lint:** `python3 -I bin/lint-ui.py sc/uiconfig/scalc/ui/notebookbar.ui`
- **Baseline:** both pass, 0 new fatals (T2).

## TDD

- **Mode:** strict, enabled from the session configuration.
- **Runner:** LibreOffice UITest, which needs the local build. The build (`make build gb_SUPPRESS_TESTS=1`) started 2026-10-12, with its log at `/mnt/games/libreoffice/build.log`. The first attempt used `make build-nocheck`, a target that does not exist in this version, and failed immediately. RED/GREEN runs once the build is done.

## Delivery

- **Forecast:** 300 to 500 authored XML lines.
- **Strategy:** `ask-on-risk`.
- **RDD:** on by default.

## Tasks

| ID | Task | Route | Status |
|---|---|---|---|
| T1 | Prototype env: relocatable copy of the installed build at `/mnt/games/libreoffice/proto` plus an isolated profile | inline | [x] headless convert OK |
| T2 | Map commands, labels, icons and the tab template | delegated, Sonnet (4+ files) | [x] done; premise corrected |
| T3 | Implement the chosen option, first in the prototype (visual), then in master | delegated, Sonnet writer | [ ] blocked on the A/B decision |
| T4 | Cross-family review of the diff | Pi `wA:p6` (gpt-6-luna), read-only | [ ] |
| T5 | Build plus a UITest asserting the buttons/commands (RED, then GREEN) | inline plus build | [~] build OK (2026-10-12); UITest pending |
| T6 | Work-unit commit, then prepare the Gerrit submission | inline | [ ] |

## Progress / Evidence

- **T1:** the proto headless convert succeeded.
- **T2:** the agent's report was spot-checked: `phbFunctions` at L6671, `FunctionsLabel1` reads "~Functions", groups at 6682/6832/7000.
- **T5:**
  - Dependencies installed: perl-archive-zip, nasm, ccache. ccache uses `cache_dir=/mnt/games/libreoffice/ccache` with `max_size` 15G.
  - `autogen.input`: gtk3 only, no Java, help, dicts, firebird or postgresql. `./autogen.sh` exit 0.
  - `make build gb_SUPPRESS_TESTS=1` is running in the background; it is downloading external tarballs.
  - The first run at -j10 froze the PC (14 GB RAM) and left truncated .o files after the hard reboot.
  - Rerun under a cgroup cap: `systemd-run --user --scope -p MemoryHigh=6G -p MemoryMax=7G -p MemorySwapMax=1G nice -n 10 make build gb_SUPPRESS_TESTS=1 PARALLELISM=6`. Peak memory was 4.8G.
  - Build OK at 14:05. `instdir/program/soffice --version` reports LibreOfficeDev 27.2.0.0.alpha0 62abc2329664.
  - Headless csv to ods conversion OK, with the profile at `/mnt/games/libreoffice/dev-profile`.

## Next step

**On hold (2026-10-12):** the user decided to redesign the UI first (icons, button layout, visual quality) before adding features. Resume after that redesign lands. The A/B decision is still open. The build (T5) keeps running because the redesign needs it too.

# Feature: Writer ribbon tabs like Word (Tabbed Office)

- **Status:** planned 2026-10-20. Open questions answered (see "Answers and rulings").
- **Locator:** `product/odd/tasks/writer-ribbon-tabs.md`
- **Engram mirror:** `odd/writer-ribbon-tabs/tasks`
- **Repo / branch:** `/mnt/games/libreoffice/core`, `feature/writer-ribbon-tabs`, from the product tip the controller
  names when the feature starts.
- **Design:** `product/docs/writer-ribbon-tabs.md`.
  Section and decision numbers below refer to it.
- **SDD workspace:** `/mnt/games/libreoffice/core/.superpowers/sdd/2026-10-20-writer-impress-ribbons/` (briefs,
  research, map, reports; never committed)

## Objective

Make the Tabbed Office Writer ribbon look like Word for Microsoft 365: same tabs, same order, same sections and
controls in the same places, built the way Calc's was. Controls whose feature LibreOffice lacks are greyed
placeholders. Implementing those features comes later.

## Problem and why

The user's words (2026-10-20): "hacelo igual que con Calc"; "si faltan features que están en LibreOffice, las
listás como hiciste con Calc".

Writer has no Tabbed Office mode yet: the mode is Calc-only in cui (`cui/source/dialogs/uitabpage.cxx:67-69`,
`:94-98`), in the mode table (`ToolbarMode.xcu:17-296` has no TabbedOffice node for Writer) and in the generator
(`product/ui/gen_ribbon.py:39-43`, `:446-450`). Writer's stock Tabbed ribbon is LibreOffice's layout, not Word's.

## Rulings (binding, from the brief; design section 4 holds the rest)

- **Reference:** Word for Microsoft 365, Windows, Current Channel, 2024+ look, at 1920 px. Same as Calc.
- **Tabs:** File, Home, Insert, Design, Layout, References, Mailings, Review, View, Help. Extension and Tools stay
  with their content, as in Calc.
- **Not in this feature:** Word's Draw (ink) tab, the File backstage, contextual tabs. Writer's stock contextual tabs
  (Table, Image, Draw, Object, Media, Print, Form) stay exactly as they are.
- **Missing features** are greyed placeholders on family slots. Cloud or account controls are omitted and listed
  (design decision 5).
- **Every LibreOffice button the Word layout drops** is listed per tab, stays reachable in the menu bar, and a test
  asserts it (design section 2).
- **The Boost look applies as is:** Inter UI font, Boost icons, Boost color schemes; Light is white.
- **Accent:** Word's blue for Writer. The narrowest way needs C++ and **waits for the user's OK** (design 3.4); the
  fallback needs none.
- **T9 and T10 stay pending.** The layout keeps Word's labels in `office_label`, and nothing depends on T10 (design
  decisions 29-30).

## Scope

**In scope:**
- Pages of `sw/uiconfig/swriter/ui/notebookbar_office.ui` generated from `product/ui/writer_<tab>.json`: Home,
  Insert, Design, Layout, References, Mailings, Review, View, Help; tab operations in `product/ui/writer_tabs.json`.
- The generator, test tooling and dev scripts for two apps, with Calc's output byte-identical.
- The Writer Tabbed Office mode: ToolbarMode node, cui whitelist and preview picture, profile, launcher,
  screenshots, UITest scaffold.
- Dropdowns, placeholder commands and slots, labels, icons, tests, docs.

**Out of scope:** implementing placeholder features; Word's Draw tab, File backstage and contextual tabs; Impress;
translations; T9 and T10 (pending decisions); the accent C++ until the user approves it.

## Constraints

- Build only through `product/dev/lo-make.sh`; run UITests only through `product/dev/uitest.sh`.
- The stock `notebookbar.ui` and the other Writer variants stay untouched; the office `.ui` stays "stock + tab
  operations + generated pages".
- Calc stays byte-identical: every task that touches shared code (generator, test tooling, dev scripts, cui)
  proves the sha256 of `sc/uiconfig/scalc/ui/notebookbar_office.ui`, `solenv/sanitizers/ui/modules/scalc.suppr` and
  `scalc.false` unchanged, and the Calc tests stay green.
- A split or dropdown needs a dedicated command; never put a new controller on a command that other toolbars use.
- `product/icons/` and `product/tests/test_icons.py` belong to another worker until that work lands: read them, never
  write them. The b tasks start after it lands.
- Never touch the user's profile `/mnt/games/libreoffice/try-profile`. Kill only your own soffice, by PID.
- Commits are Conventional, subject <= 79 characters, no AI attribution. Never commit `.superpowers/`.
- Artifacts in English.

## Acceptance criteria

- Each tab shows Word's sections and controls in Word's order (design section 1), placeholders greyed and inert,
  omitted controls absent.
- The tabs appear in Word's order with Word's names; the contextual tab objects equal the stock ones.
- Every command that leaves a tab is reachable as design section 2 records, and a test asserts it.
- Calc's generated files are byte-identical to before the feature.
- Tabbed Office can be chosen in Writer's User Interface dialog, with a Writer preview picture.
- Unit tests, gla11y/lint (`check-ui.sh`) and UITests pass. Light and dark screenshots of every tab at 1920 px
  exist, and the user approves them visually.

## TDD

- **Mode:** strict.
- **Runners:**
  - `python3 -I -m unittest discover -s product/tests -t .`
  - `product/dev/uitest.sh --app writer notebookbarOffice.NotebookbarOffice.<test>` (W0b adds `--app`; without it
    the script runs Calc's target, as today)
  - `product/dev/check-ui.sh sw/uiconfig/swriter/ui/notebookbar_office.ui`
- Layout tests compare each generated page with a DESIGN table copied by hand into its test module
  (`product/tests/test_writer_<tab>_ui.py`), as Calc does (`product/docs/calc-ribbon-tabs.md:170-176`).
- RED first wherever a deterministic test exists. Exceptions: the 1920 px fit is measured by screenshots
  (`product/dev/shot-tab.sh`), the docs task is passive (structural readback), and the visual gate has no RED.
- A UITest goes through `UITest_writer_tests8`, which rebuilds what changed first, so a RED UITest run already uses
  the new sources (Calc's experience, `calc-ribbon-tabs.md:327-330`).

## Delivery

- **Forecast:** about 7000 authored changed lines (range 6000-9000), generated `.ui`, `.suppr` and `.false`
  excluded. Basis: Calc's ribbon-tabs slice (map-M1 section 7.1) scaled to 193 controls, 30 dropdowns and 24
  slots; the biggest parts are tests (about 1900), XCU labels and controllers (about 1500), docs (about 800),
  UITests (about 900) and slot declarations (about 500).
- **Strategy:** controller ruling, 2026-10-20 (the user can overturn it). The feature branch takes one
  work-unit commit per task. At the end of each slice, `dev` is fast-forwarded and pushed to GitHub
  (nahuel893/boost-office) only when the user asks, as with Calc and the look work. There are no pull
  requests; each slice below is the review candidate.
- **Slices** (one pull request each, about 650-1000 lines):

| Slice | Tasks | Forecast |
|---|---|---|
| S1 infrastructure | W0a, W0b | 730 |
| S2 placeholder slots | W1 | 750 |
| S3 Home | W2a, W2b | 670 |
| S4 Insert | W3a, W3b | 720 |
| S5 Design and Layout | W4a, W4b | 820 |
| S6 References and Mailings | W5a, W5b, W6a, W6b | 960 |
| S7 Review | W7a, W7b | 650 |
| S8 View, Help, polish | W8a, W8b, W9 | 900 (+150 with the accent) |
| S9 docs and gate | W10, W11 | 820 |

- **RDD:** user-owned switch. After each work-unit commit, run `gentle-ai review assess --cwd <repo> --agent
  claude-code --base-ref <last reviewed boundary> --committed-only --json` and follow `review_due`. A due review
  needs the user's consent per candidate; while the user is away it is recorded as "consent pending". Calc's
  reviews of the whole slice were refused (`lens_context_budget_exceeded`, `product/odd/tasks/calc-ribbon-tabs.md:70`),
  so the review candidate is always one work-unit commit or one slice, never the branch.

## Tasks

| ID | Task | Route | Status | Commits | RDD |
|----|------|-------|--------|---------|-----|
| W0a | Generator and test tooling for two apps; Writer office `.ui` = stock + tab operations; registration; suppressions | delegated (opus: shared code, Calc byte-identical) | [x] | 12d483db7 (generated), 348ecf587 (code) | high; granted, approved, acknowledged (348ecf587 only) |
| W0b | Writer Tabbed Office mode end to end: ToolbarMode node, cui whitelist and per-app preview lookup, profile, launcher, shot-tab, uitest.sh, UITest scaffold | delegated (opus: cui C++ and shared scripts) | [ ] | | |
| W1 | All 24 placeholder slots in one sw rebuild, with the registry and the slot test | delegated (opus: C++ and `.sdi`) | [ ] | | |
| W2a / W2b | Home: a = layout, labels, popups, placeholder labels, unit tests, UITests; b = icons, 1920 fit, screenshots | a: delegated (sonnet); b: delegated (sonnet), after the icon worker | [ ] | | |
| W3a / W3b | Insert | as W2 | [ ] | | |
| W4a / W4b | Design (new page) and Layout | as W2 | [ ] | | |
| W5a / W5b | References | as W2 | [ ] | | |
| W6a / W6b | Mailings (new page) | as W2 | [ ] | | |
| W7a / W7b | Review | as W2 | [ ] | | |
| W8a / W8b | View and Help (new page) | as W2 | [ ] | | |
| W9 | Polish across tabs: caption baseline, collapse order at 1600/1366, parked minors; the per-app accent (approved) | delegated (opus: accent C++ in vcl and sfx2) | [ ] | | |
| W10 | Docs: `product/docs/writer-ribbon-tabs.md` from the draft and the results | delegated (sonnet) | [ ] | | passive (docs) |
| W11 | Visual gate: contact sheets, Writer preview picture, user gate | delegated (sonnet) | [ ] | | |
| T9w | Word labels for existing commands (follows Calc's T9 answer) | pending user decision | [ ] | | |
| T10w | Greyed disabled popup entries (follows Calc's T10 answer) | pending user decision | [ ] | | |
| A1 | The accent: answered 2026-10-20, one accent per app, built in W9 | answered | [x] | | |

Why this shape: the brief's shape, with W0 split in two (about 730 lines in one task would mix the shared
generator with C++ and dev scripts) and Design paired with Layout and Help with View (Design has 10 controls and
no dropdowns; Help has 5). W1 exceeds the 400-line heuristic on purpose: 24 slot declarations in one sw rebuild,
as Calc's T1 did.

### W0a: generator and test tooling for two apps

- **Files:** `product/ui/gen_ribbon.py` (app table instead of the Calc constants `:39-43`, glob `:446-450`, `regenerate_all_files` and
  `main` `:484-525`; `.false` sync for Writer); `product/ui/writer_tabs.json` (new: `valign` of "Home Tab" and
  "Layout Tab"; no new pages yet); `product/tests/office.py`, `commands.py`, `placeholders.py` (per-app access, Calc
  names kept); `product/tests/test_gen_ribbon.py`; `product/tests/test_writer_tabs.py` (new);
  `sw/uiconfig/swriter/ui/notebookbar_office.ui` (generated); `sw/UIConfig_swriter.mk` (one line);
  `solenv/sanitizers/ui/modules/swriter.suppr` and `swriter.false` (seeded office copies, generated);
  `product/dev/check-ui.sh` (files by app).
- **Checks:** unit tests; the three Calc sha256 values recorded before the change match after `gen_ribbon.py --all`;
  `product/dev/check-ui.sh sw/uiconfig/swriter/ui/notebookbar_office.ui` (no new warnings or fatals);
  `product/dev/check-ui.sh sc/uiconfig/scalc/ui/notebookbar_office.ui` (unchanged); `product/dev/lo-make.sh sw.build`.
- **RED:** `test_writer_tabs.py` expects `office.expected_office_ui("writer")` to equal the committed Writer office
  `.ui` and the Writer suppressions to mirror every stock line with the office path; it fails before the app table
  exists. `test_gen_ribbon.py` gains "`--all` writes both apps" and "an unknown `--app` is an error".

### W0b: Writer Tabbed Office mode end to end

- **Files:** `officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu` (Writer `TabbedOffice`, MenuPosition
  9, copied from `:409-436`); `cui/source/dialogs/uitabpage.cxx` (`:67-69`, `:94-98`, `UpdateImage` `:171-183` prefers
  `notebookbar_office_<app>.png`); `cui/source/dialogs/uipickerdlg.cxx` (`:90-105`, through the same helper);
  `product/dev/profile.py` (`app` parameter) and `product/tests/test_profile.py`; `product/dev/office.sh` (new),
  `product/dev/calc.sh` (wrapper) and `product/tests/test_calc_launcher.py` (parametrized by app);
  `product/dev/shot-tab.sh` (app option, Writer tab list, measured `x0`); `product/dev/uitest.sh` (`--app`);
  `sw/qa/uitest/writer_tests8/notebookbarOffice.py` (new).
- **Checks:** unit tests; `product/dev/lo-make.sh cui.build officecfg.build postprocess.build`;
  `product/dev/uitest.sh --app writer notebookbarOffice.NotebookbarOffice.test_tabbed_office_loads` and
  `...test_tab_order`; `product/dev/uitest.sh` with a Calc test still passes; one Writer screenshot through
  `product/dev/shot-tab.sh` with the new app option; Calc sha256 check.
- **RED:** the Writer case of `test_profile.py`; an XCU test that Writer has `TabbedOffice` at MenuPosition 9 with
  CommandArg `notebookbar_office.ui`; a source test that the cui helper lists Writer; the UITest
  `test_tabbed_office_loads` fails before the ToolbarMode node exists.

### W1: placeholder slots

- **Files:** `sw/inc/cmdid.h` (`FN_BOOST = SID_SW_START + 5900` after `:55`, `FN_BOOST_*` +0..+23);
  `sw/sdi/swriter.sdi` (24 declarations in the format of `:5973-5988`); `sw/sdi/viewsh.sdi` (`TextEditView`, state
  method only, as `:21-25`); `sw/source/uibase/uiview/viewstat.cxx` (one `DisableItem` case group in
  `SwView::GetState`, `:63`); `product/tests/placeholders_writer.json` (new; slots, offsets, URL variants; labels come
  with the tab tasks); `product/tests/test_writer_slots.py` (new, after `test_calc_slots.py:33-114`).
- **Checks:** unit tests; `product/dev/lo-make.sh sw.build`; `product/dev/uitest.sh --app writer
  notebookbarOffice.NotebookbarOffice.test_placeholder_slots_disabled` (every registry URL dispatched in a Writer
  document is disabled and changes nothing).
- **RED:** `test_writer_slots.py` (each slot in the fork block, declared, listed with no execute method, in the
  disabled group, no other source mentions it, no gaps or duplicates, no other define in 25900-25999) and the
  UITest, both before the sources change.

### W2a-W8a: one tab (or tab pair), layout and behaviour

Common to every a task:

- **Files:** `product/ui/writer_<tab>.json`; `product/ui/writer_tabs.json` when the tab is new (Design in W4a,
  Mailings in W6a, Help in W8a: `add_pages` and `positions`); popup files in `sw/uiconfig/swriter/popupmenu/` and
  their lines in `sw/UIConfig_swriter.mk:17-34`; labels in `WriterCommands.xcu` (menus, placeholder variants, the
  missing label nodes); `Controller.xcu` Popup and ToolBox nodes (Module `com.sun.star.text.TextDocument`, node
  names with a `Writer` suffix where Calc owns the name); `product/tests/placeholders_writer.json` (labels);
  `product/tests/test_writer_<tab>_ui.py` (new); `sw/qa/uitest/writer_tests8/notebookbarOffice.py`; the generated
  `.ui` and suppressions.
- **Checks:** unit tests; `product/dev/lo-make.sh sw.build officecfg.build postprocess.build`; `check-ui.sh` on the
  Writer office `.ui`; the tab's UITests one by one; Calc sha256 check.
- **RED:** the DESIGN table test of the page, the label/controller/popup checks of every command, the
  `LEFT_THE_TAB` test (exact menu-bar id for class a, the equivalent id for class b, the quick access bar for
  `Menubar`, the ruling for class c), and the tab's UITests (tab visible in the text, table, image and print-preview
  contexts; dropdown contents built through the real controllers; placeholders disabled and inert).

Per tab (counts from design section 1; dropdown names from its tables):

| Task | Pages | Dropdowns (popup file or controller) | New labels | Leave-list rows | Forecast |
|---|---|---|---|---|---|
| W2a Home | Home Tab | 4: HomeChangeCaseMenu, HomeTextEffectsMenu, HomeFindMenu, HomeSelectMenu | 4 menus, 6 placeholder items | 32 | 550 |
| W3a Insert | Insert Tab | 7: InsertShapesMenu, InsertHeaderMenu (HeaderMenuController), InsertFooterMenu (FooterMenuController), InsertPageNumberMenu, InsertTextBoxMenu, InsertQuickPartsMenu, InsertObjectMenu | 7 menus, 4 placeholders | 13 | 600 |
| W4a Design, Layout | new Design Tab; Layout Tab | 7: LayoutBreaksMenu, LayoutWrapTextMenu, PageLayoutBringForwardMenu, PageLayoutSendBackwardMenu, PageLayoutAlignMenu, PageLayoutGroupMenu, PageLayoutRotateMenu | 7 menus, 6 placeholders, 5 label nodes (PageAreaDialog, LeftParaMargin, RightParaMargin, AboveSpacing, BelowSpacing) | 5 | 700 |
| W5a References | References Tab | 3: ReferencesTocMenu, ReferencesAddTextMenu, ReferencesNextFootnoteMenu | 3 menus, 4 placeholders | 8 | 400 |
| W6a Mailings | new Mailings Tab | 2: MailingsSelectRecipientsMenu, MailingsFinishMenu | 2 menus, 8 placeholders | 0 | 400 |
| W7a Review | Review Tab | 5: ReviewLanguageMenu, ReviewDeleteCommentMenu, ReviewAcceptMenu, ReviewRejectMenu, ReviewCompareMenu | 5 menus, 8 placeholders | 5 | 550 |
| W8a View, Help | View Tab; new Help Tab | 2: ViewSwitchWindowsMenu (WindowListMenuController), ViewMacrosMenu | 2 menus, 12 placeholders | 12 | 500 |

Tab-specific checks:

- W2a: the Find menu's first item is the find toolbar URL `vnd.sun.star.findbar:FocusToFindbar`
  (`GenericCommands.xcu:1855`); Home fits or the Styles gallery shrinks first (measured in W2b).
- W3a: the Header and Footer dropdowns list the document's page styles; the Shapes submenus open.
- W4a: the Design tab shows in the table and image contexts; the four spin fields render (stock pattern
  `notebookbar.ui:5443-5447`); the Arrange menus list their items with a shape selected.
- W5a: the duplicate `InsertMultiIndex` and `UpdateCurIndex` buttons have distinct widget ids (design decision 11).
- W6a: the record buttons are disabled outside a mail merge.
- W7a: the Language submenus come from their controllers (`Controller.xcu:146-174`).
- W8a: Switch Windows lists two open windows (Calc's T6b check); Help is the last tab.
- W2a checks which module names load the office `.ui` (master documents, Writer/Web; design section 6).

### W2b-W8b: icons, 1920 fit, screenshots

- **Route:** delegated (sonnet), each after its a task and after the icon worker's work lands.
- **Files:** `product/icons/manifest.json` and vendored Fluent SVGs (excluded from the forecast);
  `product/tests/test_writer_icons.py` (new; folded into `test_icons.py` later by agreement with its owner).
- **Checks:** unit tests; `python3 -I product/icons/build_theme.py install --instdir instdir`; light and dark
  screenshots of the tab at 1920, 1600 and 1366 px through `product/dev/shot-tab.sh`, outside the repository.
- **RED:** the icon coverage test for the tab's commands in both themes fails before the manifest entries exist.

### W9: polish

- **Files:** depends on findings: layout files (collapse priorities), `writer_tabs.json` (caption baseline, as Calc's
  T8a), and with the user's OK the accent: `include/vcl/tabctrl.hxx`, `vcl/source/control/tabctrl.cxx`,
  `sfx2/source/notebookbar/NotebookbarTabControl.cxx`,
  `officecfg/registry/schema/org/openoffice/Office/UI/ToolbarMode.xcs`, `product/themes/palette.json`,
  `product/themes/build_schemes.py`, `product/tests/test_schemes.py`. Without the OK: only the palette fallback, and
  only if the user picks it.
- **Checks:** unit tests; `product/dev/lo-make.sh vcl.build sfx2.build officecfg.build postprocess.build` (accent);
  screenshots of every tab; a pixel check that the selected tab's underline is the app's color in Writer and still
  green in Calc.
- **RED:** a caption-baseline test across Writer tabs; with the accent, a scheme test that `accent.writer` reaches
  the ToolbarMode values and the pixel check, both failing first.

### W10: docs

- **Files:** `product/docs/writer-ribbon-tabs.md` (from the design draft, with the build results, counts and test
  totals), `product/odd/tasks/writer-ribbon-tabs.md` (this file).
- **Checks:** structural readback; every path:line in the doc still resolves (`rg` spot checks).
- **RED:** none (passive documentation).

### W11: visual gate

- **Files:** `vcl/Package_toolbarmode.mk` (one line, `notebookbar_office_writer.png`), the picture itself;
  contact sheets outside the repository: `/mnt/games/libreoffice/assets/previews/writer-ribbon-tabs-light.png` and
  `...-dark.png`.
- **Checks:** `product/dev/lo-make.sh vcl.build`; the User Interface dialog shows the Writer picture for Tabbed Office;
  the user approves the contact sheets.
- **RED:** none (visual gate).

## Checks

Every task, before its work-unit commit:

1. `python3 -I -m unittest discover -s product/tests -t .` (all product tests, Calc's included).
2. The Calc byte-identity check (sha256 of the three Calc generated files) when shared code changed.
3. `product/dev/check-ui.sh sw/uiconfig/swriter/ui/notebookbar_office.ui` when the Writer `.ui` changed.
4. The builds the task needs, only through `product/dev/lo-make.sh`: `sw.build`, `cui.build`,
   `officecfg.build` then `postprocess.build`, and `vcl.build`/`sfx2.build` for the accent.
5. The task's UITests one at a time: `product/dev/uitest.sh --app writer notebookbarOffice.NotebookbarOffice.<test>`
   (target `UITest_writer_tests8`, log `workdir/UITest/writer_tests8/done.log`). No new gbuild target is needed: the
   target adds the whole `sw/qa/uitest/writer_tests8/` directory (`sw/UITest_writer_tests8.mk`).
6. Screenshots for the b tasks, W9 and W11, through `product/dev/shot-tab.sh`, outside the repository.

## Answers and rulings (2026-10-20)

The controller's rulings can be overturned by the user.

1. **Accent:** the user chose one accent per app ("Uno por app"). Writer gets Word blue and Calc keeps its
   green. Impress will get PowerPoint orange later. This is the C++ route of design section 3.4, done in W9.
2. **`.uno:ArrowsToolbox` and `.uno:InsertDraw`:** controller ruling, following Calc's precedent (decisions
   19-20): they stay reachable through View > Toolbars, and the menu-bar test lists that path.
3. **Word splits that LibreOffice lacks:** controller ruling: they are built as dropdowns for now, the same
   state as Calc's pending D6 (split arrows). Real split bodies can come later, one mirror slot each.
4. **Approximate mappings:** controller ruling: kept, and each one is listed in decision 20. A mapping
   becomes a placeholder only if a UITest shows it does not do the Word job.
5. **Undo on Home:** controller ruling: kept on Home, for Calc parity (calc-home-redesign); it also stays in
   the quick access bar.

## Progress / evidence

- 2026-10-20: design and plan drafted (D1) and committed by the controller with the answers. Research and code map: `research-word365-ribbon.md`, `map-M1.md` in the
  SDD workspace.
- 2026-10-20, W0a (route: delegated, opus; trigger: shared generator and 2+ non-trivial files). Writer's first
  commit was 51a072cd5. The controller split it into 12d483db7 and 348ecf587; the tree is unchanged.
  - Evidence (report: `task-W0a-report.md`):
    - unit tests 318 -> 333, all pass (RED observed first);
    - the Calc sha256 values of `notebookbar_office.ui`, `scalc.suppr` and `scalc.false` are the same before
      and after `gen_ribbon.py --all`;
    - `check-ui.sh`: Writer has 0 new warnings and 0 new fatals; Calc's output is identical;
    - `lo-make.sh sw.build` exits 0, and `git show --check` is clean.
  - Controller spot check: after `gen_ribbon.py --all` the tracked tree is clean, and 333 tests pass.
  - Why the split:
    - the review of the whole commit stopped with `lens_context_budget_exceeded`, because the generated `.ui`
      has 15261 lines;
    - 12d483db7 holds only the generated output and its 6-line input, `writer_tabs.json`. Its bytes are
      checked by `test_writer_tabs.py` (generator output == committed file), by `check-ui.sh` and by the
      sw build;
    - 348ecf587 holds the authored code, and the native review covered it (high risk, 4 lenses).
  - The LibreOffice pre-commit hook has a bug: its `.ui` exemption never matches (`-z` input), so a commit
    whose first added file is the 840 KB `.ui` is refused. The `writer_tabs.json` file in 12d483db7 sorts
    first.
  - Review (lineage review-932185ac1739a545): approved and acknowledged, with no blockers.
  - Parked advisory findings:
    - WARNING `check-ui.sh:16-22`: the shared temp report is not cleared between gla11y runs, so a failed run
      reprints the previous file's report. Fix it in W0b, which touches `check-ui.sh` again.
    - WARNING `sw/UIConfig_swriter.mk:254`: "Writer files not in the manifest". This is a false positive: they
      are in the base commit 12d483db7.
    - SUGGESTIONS:
      - `gen_ribbon.py` writes each app's files one by one, not all at once (`:520-524`);
      - an ignored return value (`:542-545`);
      - the app record is built from positional fields (`:54-60`);
      - `:49`;
      - `check-ui.sh:11-15`;
      - the alias in `commands.py:19` has no explanation;
      - duplicated literals in `test_writer_tabs.py:21-23`.
  - Worker concerns:
    - `swriter.false` keeps 277 office lines, not 713: 436 stock lines name widgets that are gone. Design
      section 3.1 is corrected.
    - 20 office lines in `swriter.suppr` show as unused, because gla11y checks `.false` first. This is not
      fatal. A fix would change the shared `sync_suppr`. Parked.
    - `placeholders.registry("writer")` points to a file that W1 creates.

## Next step

W0b: the Writer Tabbed Office mode end to end (delegated, opus). Carry the `check-ui.sh` report fix.

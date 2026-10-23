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
- **Accent:** Word's blue for Writer, through the C++ route of design 3.4. The user approved it ("Uno por app"); it
  is done in W9.
- **T9 is answered; T10 stays pending.** The layout keeps Word's labels in `office_label`; task T9w puts them on
  the ribbon (see "Answers and rulings", item 6). Nothing depends on T10 (design decisions 29-30).

## Scope

**In scope:**
- Pages of `sw/uiconfig/swriter/ui/notebookbar_office.ui` generated from `product/ui/writer_<tab>.json`: Home,
  Insert, Design, Layout, References, Mailings, Review, View, Help; tab operations in `product/ui/writer_tabs.json`.
- The generator, test tooling and dev scripts for two apps, with Calc's output byte-identical.
- The Writer Tabbed Office mode: ToolbarMode node, cui whitelist and preview picture, profile, launcher,
  screenshots, UITest scaffold.
- Dropdowns, placeholder commands and slots, labels, icons, tests, docs.

**Out of scope:** implementing placeholder features; Word's Draw tab, File backstage and contextual tabs; Impress;
translations; T10 (a pending decision).

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
| W0b | Writer Tabbed Office mode end to end: ToolbarMode node, cui whitelist and per-app preview lookup, profile, launcher, shot-tab, uitest.sh, UITest scaffold | delegated (opus: cui C++ and shared scripts) | [x] | 6bfb5aae4, c0a315dd2 (Calc UITest fix) | high; declined; independent verifier (FAIL -> fixed); fix: medium, under budget |
| W1 | All 24 placeholder slots in one sw rebuild, with the registry and the slot test | delegated (opus: C++ and `.sdi`) | [x] | 2f510a14f | slice 6bfb5aae4..2f510a14f: medium, budget reached; declined (writer self-check + controller spot check) |
| W2a / W2b | Home: a = layout, labels, popups, placeholder labels, unit tests, UITests; b = icons, 1920 fit, screenshots | a: delegated (sonnet); b: delegated (sonnet), after the icon worker | a [x], b [x] | a: 38c1b440e (layout + generated), ee9c5bafd (code); b: 1ff462bc9 | a: medium, budget reached; declined (writer self-check + controller spot check); b: pending in slice |
| W2c | Home Styles gallery as wide as Word's (it is 70 px and clips the style names) | delegated (opus: svx sizing, shared control) | [x] | 117239dbd (generator `expand`), 786925aaf (Home JSON + `.ui` + tests) | slice 89785d255..786925aaf (W2b + W2c): high; granted, approved, acknowledged |
| W3a / W3b | Insert | as W2 | a [x], b [x] | a: 016dd7aff (layout + generated), ff8ce7436 (code), d677b1cc9 (Header/Footer fix); b: 3bffe89ad, 2b97b23ff | a: medium, budget reached; granted, approved, acknowledged; b: medium, under budget (pending in slice from b2b3346bd) |
| W4a / W4b | Design (new page) and Layout | as W2 | a [x], b [x] | a: 2bb1f6dbf (layout + generated), 404294f79 (code); b: 2ef03d924, ebd26872f (Style Set fix, controller) | a: medium, budget reached; reviewed from 2bb1f6dbf (W3b's two small commits fall before the generated commit and stay unreviewed); granted, approved, acknowledged; b: medium, under budget (pending in slice from 404294f79) |
| W5a / W5b | References | as W2 | a [x], b [x] | a: b4c7dbfe7 (layout + generated), 26fa4a6d0 (code); b: 6bed2991d | a: the slice from c293641c5 (2279 lines) exceeded the lens budget at START; reviewed 26fa4a6d0 alone: medium, granted, approved, acknowledged. T9w-fit (a0c9e3c2d) stays unreviewed |
| W6a / W6b | Mailings (new page) | as W2 | a [x], b [x] | a: 7e4cf361b (layout + generated), 604c02701 (code); b: 2e760bcaf | a: reviewed 604c02701 alone (623 lines): medium, granted, approved, acknowledged |
| W7a / W7b | Review | as W2 | a [x], b [x] | a: 820baee29 (layout + generated), 6f24be2b0 (code); b: a22437b09, e0108c293 (fit), 3942ac2b9 (test fix, controller) | a: reviewed 6f24be2b0 alone (880 lines): medium, granted, approved, acknowledged; b: medium, under budget (pending in slice from 6f24be2b0) |
| W8a / W8b | View and Help (new page) | as W2 | a [x], b [ ] | a: 027e8f459 (layout + generated), ff29c3f19 (code) | a: ff29c3f19 alone (992 lines): medium; declined by the user (writer self-check + controller spot check) |
| W9 | Polish across tabs: caption baseline, collapse order at 1600/1366, parked minors; the per-app accent (approved) | delegated (opus: accent C++ in vcl and sfx2) | [ ] | | |
| W10 | Docs: `product/docs/writer-ribbon-tabs.md` from the draft and the results | delegated (sonnet) | [ ] | | passive (docs) |
| W11 | Visual gate: contact sheets, Writer preview picture, user gate | delegated (sonnet) | [ ] | | |
| T9w | Office labels on the ribbon, for Writer and Calc together: the generator shows `office_label`; menus, help and tooltips keep LibreOffice's labels | delegated (opus: shared generator, vcl C++; Calc's output changes on purpose) | [x] | 9871de25c (data + generated), 22e203a66 (vcl), c293641c5 (generator + tests) | high (gen_ribbon.py starts processes). First review (9871de25c..c293641c5): false BLOCKER, abandoned with the user's authorization. Second review (a91cd6f15..c293641c5): granted, approved, acknowledged |
| T9w-fit | Calc Formulas and Data fit at 1920 px again: the longer Excel labels pushed Calculation and Analyze behind `>>` | delegated (sonnet) | [x] | a0c9e3c2d | medium, under budget (pending in slice from c293641c5) |
| IC1 | Plain grey line icons for Writer and Calc (ruling 8): no `fill` in the manifest; the icon test pins it | delegated (sonnet), inside W8b | [ ] | | |
| T10w | Greyed disabled popup entries, for Calc and Writer together (Calc's T10: LibreOffice's `DontHideDisabledEntry` hides them by default) | controller ruling under ruling 9: show them greyed, as Office does, in every menu; built in W9 | [ ] | | |
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
6. **T9, Office labels (2026-10-21):** the user chose "Los de Office". The Tabbed Office ribbons of Calc and
   Writer show Word's and Excel's labels (`office_label`: Cover Page, WordArt, Equation...). Menus, help and
   tooltips keep LibreOffice's labels. So it is the ribbon-only route, not label overrides in the app's
   `Commands.xcu`, which would also rename the menus. Task T9w does both apps in one generator change. Calc's
   generated `.ui` changes on purpose, so for that task the byte-identity check becomes an expected-diff check:
   only labels change. Impress follows the same rule.
7. **T9w route (2026-10-21):** the spike showed that the VCL builder ignores a `.ui` label on a tool button that
   has a command (`vcl/source/window/builder.cxx:1655-1658`). The user chose "Arreglo chico en C++": the builder
   uses the `.ui` label as the item text, and the tooltip stays the command's. The other route would have been a
   URL variant per command, with its own `Commands.xcu` node and icon. Side effect: 8 existing buttons that
   already set a label in their `.ui` now show it (five in the bibliography toolbar, and "Shapes" in the three
   `notebookbar_groups.ui`).
8. **Icon style (2026-10-22):** the user rejected the icon look ("tienen que ser otros más sencillos y
   minimalistas. No pegan con el tema de iconos de calc") and chose "Línea gris, acento mínimo": every Boost icon,
   in Writer and Calc, is a grey line icon with no pastel fill. Color stays only as a small badge that means
   something (green plus or check, red cross, the conditional-format bars). The controller showed a spike
   (`assets/previews/icon-minimal/before-after.png`: 24 icons, before and after) and the user approved it. 246 of
   the 356 manifest entries lose their `fill`. The renderer keeps its fill support, unused.
9. **Working mode (2026-10-23):** the user asked to finish the whole request without stopping to ask. The
   controller rules on open decisions itself and records them here; review consent is still relayed, but work
   continues while it waits.

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

- 2026-10-20, W0b (route: delegated, opus; trigger: cui C++ and shared scripts, 2+ non-trivial files). Commit
  6bfb5aae4.
  - Evidence (report: `task-W0b-report.md`):
    - unit tests 333 -> 365, all pass (RED observed first);
    - Calc sha256 values unchanged;
    - `lo-make.sh cui.build officecfg.build postprocess.build` exits 0;
    - the Writer UITests `test_tabbed_office_loads` and `test_tab_order` pass, and one Calc UITest passes;
    - Writer screenshot at 1920 px light: `/mnt/games/libreoffice/assets/previews/writer-ribbon-tabs/w0b/`.
      Measured Writer tab-bar `x0` = 217.
  - Controller spot check: 365 OK; the tree is clean after `gen_ribbon.py --all`; the screenshot shows the
    Boost look on Writer, with the green (Calc) accent until W9.
  - RDD: high, and the user chose "Saltear esta vez", so the off path applied: an independent verifier
    (sonnet), report `task-W0b-verify-report.md`.
    - FAIL, one BLOCKER: the Calc UITest `test_ui_picker_hides_office_variant_in_writer` still expected
      Tabbed Office to be hidden in Writer.
    - Controller fix in c0a315dd2: the test now expects the option in Writer; `test_writer_mode.py` covers
      Impress and Draw. It passes in 20 s.
    - A version that also opened an Impress document passed, but left soffice hanging on shutdown, twice
      (stopped by PID).
    - The verifier's other checks passed:
      - `calc.sh` parity across 48 dry-run combinations;
      - the Writer launcher's profile;
      - the cui helper;
      - the XCU node;
      - the shell guards;
      - the `check-ui.sh` report fix.
    - The fix commit assessed medium, under budget: it stays pending in the slice.
  - Parked:
    - SUGGESTION `cui/source/dialogs/welcomedlg.cxx:139` sets `ActiveCalc` without `GetModeForApp`;
    - `UpdateImage` tries a per-app picture for every mode;
    - `test_tab_order` reads labels through the temporary `XAccessible` window property;
    - the light GTK config folder is shared by Calc and Writer;
    - clang-format 5.0.0 is missing, so the hook skipped it.
  - Design note: `office.sh <app> <mode>`; the mode is one of light, dark, tabbed, tabbed-light or compact,
    not a theme.

- 2026-10-21, W1 (route: delegated, opus; trigger: C++, `.sdi` and 2+ non-trivial files). Commit 2f510a14f.
  - Evidence (report: `task-W1-report.md`):
    - unit tests 365 -> 376, all pass. RED was observed first: the slot test had 8 of 11 failing, and the
      UITest failed with "no dispatch";
    - `lo-make.sh sw.build` exits 0;
    - `test_placeholder_slots_disabled` and `test_tabbed_office_loads` pass, with no soffice left behind;
    - Calc sha256 values unchanged.
  - Controller spot check: unit tests OK; the tree is clean after `gen_ribbon.py --all`; no soffice is running.
  - RDD for the slice 6bfb5aae4..2f510a14f (it includes the W0b UITest fix): medium, budget reached. The
    user chose "Saltear esta vez". Medium tier with an opus writer: the writer's self-verification and the
    controller spot check, with no separate verifier.
  - Rulings:
    - all 24 slots declare `SfxVoidItem X SLOT ()` with no argument, as Calc's 42 do, because sfx2 ignores
      an undeclared argument. The brief's "declare the string argument" was wrong;
    - the registry keeps labels (`label` or `variant_labels`) from design section 5, which differs from
      Calc's T1. The tab tasks still add the WriterCommands.xcu label nodes.
  - Notes:
    - 10 base command names are the same as Calc's (harmless: slot pools and `*Commands.xcu` are per
      module);
    - "FN_BOOST+0..+23" appears in comments in four sw files and is not tested;
    - design 3.3 is confirmed: 737 ids in 20000-25999, the highest 22610;
    - the new case group is at `viewstat.cxx:130-157`.

- 2026-10-21, W2a (route: delegated, sonnet; trigger: 2+ non-trivial files). Commits:
  - 38c1b440e: `writer_home.json` and the generated output;
  - ee9c5bafd: the popups, the WriterCommands/Controller.xcu nodes, `test_writer_home_ui.py` and the
    UITests.
  - Evidence (report: `task-W2a-report.md`):
    - unit tests 376 -> 398, all pass;
    - the 7 new Home UITests pass, plus `test_tabbed_office_loads`, `test_tab_order` and
      `test_placeholder_slots_disabled`;
    - `sw.build officecfg.build postprocess.build` exit 0;
    - `check-ui.sh` reports 0 new warnings and fatals;
    - Calc sha256 values unchanged.
  - Controller spot check: 398 OK; the tree is clean after `gen_ribbon.py --all`; no soffice or make left
    running.
  - RDD for ee9c5bafd: medium, budget reached; the user chose "Saltear esta vez".
  - Notes:
    - 3 of the 7 UITests were green before the work (context visibility, inert placeholders, enabled real
      commands), so they are regression guards;
    - the placeholder items in the Text Effects and Select menus are hidden in a real menu while disabled.
      That is T10, pending as in Calc;
    - only `com.sun.star.text.TextDocument` loads the office `.ui`. Writer/Web and master documents keep
      the stock ribbon. This comes from reading the code (`SfxNotebookBar` handles neither enum value), not
      from a UITest;
    - the Styles gallery does not expand horizontally; the fit is measured in W2b.

- 2026-10-21, W2b (route: delegated, sonnet). Commit 1ff462bc9: the Home icons, plus
  `product/tests/test_writer_icons.py`.
  - Evidence (report: `task-W2b-report.md`):
    - RED: 1 failure, 42 missing icon members across 21 commands;
    - GREEN: 400 tests OK;
    - the icon build and install exit 0;
    - `writer_home.json` is unchanged, so there is no layout commit.
  - Fit: the tab is about 1125 px wide, so it fits at 1920, 1600 and 1366 with nothing collapsing. The
    collapse order is never exercised.
  - Screenshots: `/mnt/games/libreoffice/assets/previews/writer-ribbon-tabs/w2b/`, light and dark at 1920,
    1600 and 1366.
  - Controller check of light-1920: the groups are Undo, Clipboard, Font, Paragraph, Styles, Editing and
    Editor, with thin Boost icons. Defect: the Styles gallery is 70 px wide and clips the names.
  - New task W2c, ruled by the controller:
    - the gallery's width is `width-request` 70 in `svx/uiconfig/ui/stylespreview.ui:37`;
    - Word shows a wide gallery that shrinks first;
    - it is fixed now, because Home is the first tab the user judges.

- 2026-10-21, W2c (route: delegated, opus). Commits:
  - 117239dbd: a generator option, `"expand": true` on a toolbox, and its tests;
  - 786925aaf: the Home JSON, the regenerated `.ui`, `test_writer_home_ui.py` and the UITest. The generator
    commit came first, because the JSON depends on the option (ruling: accepted).
  - Root cause:
    - the generator never set the gallery to expand, so the toolbox item kept the 70 px from
      `stylespreview.ui:32,37`, set before the style list fills;
    - VCL never passes `hexpand` up to parent containers;
    - the stock `notebookbar.ui` sets the expand flags (`:3835`, `:3873`, `:3883`).
  - Widths, before -> after: 1920 px 70 -> 853; 1600 px 70 -> 533; 1366 px 70 -> 299. The gallery absorbs the
    width the window loses, and every group still shows at 1366.
  - Evidence:
    - unit tests 400 -> 404 (RED first);
    - the new UITest failed first at 70 px against the required 500, then passed;
    - `check-ui.sh` reports 0 new warnings and fatals;
    - `sw.build` exits 0;
    - Calc is byte-identical, and no svx file changed.
  - Screenshots: `/mnt/games/libreoffice/assets/previews/writer-ribbon-tabs/w2c/`. Controller check of
    light-1920: about 10 style tiles, like Word.
  - Review for the slice 89785d255..786925aaf (W2b + W2c): high; the user granted it. Approved and
    acknowledged, with no blockers (lineage review-1b13c416bb897d58).
  - Parked for W9:
    - svx draws each style preview as a fixed 100x24 image (`StylesPreviewWindow.cxx:546`), so long names
      are clipped and Title loses the bottom of its letters (stock has the same problem);
    - in dark mode the previews are white tiles;
    - about 90 px of the gallery are unused at 1366;
    - below 1366 nothing is measured;
    - review WARNING `notebookbarOffice.py:396-405`: the fit UITest never reads back the window width;
    - review SUGGESTIONS in `test_writer_icons.py`:
      - the magic `icon_size` value 5 (`:52`);
      - `test_the_home_page_has_buttons` counts all objects (`:67-68`);
      - the theme zips are reparsed per button, and `links.txt` is split on whitespace (`:36-45`);
    - the review's task-log WARNING is answered by this entry.
  - For later tabs: a gallery that should flex (for example Design > Style Set) uses `"expand": true`.

- 2026-10-21, W3a (route: delegated, sonnet). Commits:
  - 016dd7aff: `writer_insert.json` and the generated output;
  - ff8ce7436: 7 dropdowns, labels, `test_writer_insert_ui.py` and the UITests.
  - Evidence (report: `task-W3a-report.md`):
    - unit tests 404 -> 429;
    - the 9 new UITests pass;
    - `sw.build officecfg.build postprocess.build` exit 0;
    - `check-ui.sh` is clean;
    - Calc is byte-identical.
  - Design correction:
    - `HeaderMenuController` and `FooterMenuController` stay empty under a new command name, because they
      read their document from the status of `.uno:InsertPageHeader` and `.uno:InsertPageFooter`;
    - W3a's workaround (a `Value` on the ToolBox node) made split buttons whose body did nothing;
    - controller ruling, without C++: static popups `insert_header.xml` and `insert_footer.xml` hold the
      `.uno:InsertPageHeader` / `.uno:InsertPageFooter` item, which the registered controller turns into the
      page-style submenu, as the menu bar does (`menubar.xml:365`).
  - Fix d677b1cc9 (W3a-fix, delegated, sonnet; report `task-W3a-fix-report.md`): 429 tests OK, the build
    exits 0, and the Header/Footer UITest passes. That UITest uses UNO only: it builds the popup through
    ResourceMenuController and the page-style controller.
  - The layout kind `"split"` means the toolbox item has an arrow, in both Calc and Writer. The controller
    decides between dropdown-only and a split body.
  - Controller check: a live GTK click on the Insert tab through `shot-tab.sh` works. Screenshot:
    `assets/previews/writer-ribbon-tabs/w3a-check/insert-light-1920.png`. It shows Word's groups in order,
    with the placeholders greyed; several icons are missing until W3b.
  - Crash, parked for W9:
    - a UITest `executeAction("CLICK")` on the Insert tab aborted soffice on the headless (svp) backend;
    - coredump of PID 1742359, 2026-10-21 12:35:55: `Scheduler::CallbackTaskScheduling` -> abort, an
      exception escaping a scheduled task;
    - not reproduced with a GTK click.
  - Review of the slice 016dd7aff..d677b1cc9: medium; the user granted it. One lens (reliability); approved
    and acknowledged (lineage review-b448768d9a3da881).
  - Parked:
    - WARNING: the tests depend on artifacts the candidate does not change (`test_writer_insert_ui.py:19`);
    - WARNING: names and comments say "split" for Header/Footer and "not split" in a later test
      (`:72-73`, `:318`). No functional bug;
    - SUGGESTION: `controller_nodes()` filters Writer nodes by name suffix only (`commands.py:52-66`).

- 2026-10-21, W3b (route: delegated, sonnet). Commits:
  - 3bffe89ad: the Insert icons, and the icon test extended through a shared mixin;
  - 2b97b23ff: an explicit Drop Caps icon in `writer_insert.json`. The manifest entry alone showed no icon;
    the root cause is unknown.
  - Evidence (report: `task-W3b-report.md`):
    - RED: 66 missing icon members across 15 commands;
    - GREEN: 431 tests OK;
    - the build, `check-ui.sh` and the Insert UITest pass;
    - Calc is byte-identical.
  - Fit: the tab is about 1228 px, so nothing collapses at 1920, 1600 or 1366.
  - Live check: a GTK click on the Header button body opens the menu, and its submenu lists the page styles.
    Screenshots `light-1920-header-menu.png` and `-submenu.png` in `assets/previews/writer-ribbon-tabs/w3b/`;
    the controller looked at the submenu shot.
  - Labels: the ribbon shows LibreOffice's labels (Title Page, Insert Fontwork, Date (fixed), Formula
    Object), not Word's `office_label`. This is T9, a pending user decision. Blank Page is greyed because
    it is a placeholder (design section 5).
  - RDD for b2b3346bd..2b97b23ff: medium, under budget. It stays pending in the slice.

- 2026-10-21, W4a (route: delegated, sonnet). Commits:
  - 2bb1f6dbf: `writer_design.json`, `writer_layout.json`, `writer_tabs.json` (Design at position 3; Layout to
    Tools shift to 4..16), the regenerated `.ui` and suppressions;
  - 404294f79: 7 popup files, Controller.xcu (7 Popup and 7 ToolBox nodes), WriterCommands.xcu (7 menu labels,
    6 Design placeholder variants, 5 label nodes), unit tests and UITests.
  - Evidence (report: `task-W4a-report.md`):
    - RED: the two new unit modules failed on the missing JSON (20 + 23 tests); 13 UITests failed before any
      source change (`test_tab_order` '17' != '16', missing sections, spin fields and controllers);
    - GREEN: 431 -> 474 unit tests OK; the 12 new UITests, `test_tab_order` and `test_tabbed_office_loads`
      pass;
    - the build, `check-ui.sh` and `git show --check` are clean; Calc is byte-identical.
  - Controller spot check: 474 tests OK, `gen_ribbon.py --all` leaves the tree clean, no soffice left.
  - Behaviour found by the UITests:
    - `.uno:TextWrap` is enabled only after the draw shell takes over on idle, so the test retries;
    - with one shape, exactly one of foreground and background is enabled;
    - Rotate Left and Right are disabled for a shape, as the design says.
  - Labels for the new nodes use LibreOffice wording ("Page Area...", "Before Text Indent", "After Text
    Indent", "Above Paragraph Spacing", "Below Paragraph Spacing"); Word's label stays in `office_label` for
    T9w.
  - Open for W4b: icons for the six Design placeholders and the new menus; the fit at 1920; a visual check of
    the spin-field widths (the UITest only asserts at least 60 px). The Style Set placeholder is a wide greyed
    button, not Word's gallery.
  - Later tabs: W6a and W8a add Mailings and Help, and must shift the positions after them again.
  - Review of 2bb1f6dbf..404294f79: medium; the user granted it. One lens (reliability); approved and
    acknowledged (lineage review-8d8fa0abdde8db94). W3b's commits (3bffe89ad, 2b97b23ff) lie before the generated
    commit, so no reviewable slice holds them; they stay unreviewed (icons, a test, one JSON line).
  - Parked for W9 (test quality):
    - WARNING: `test_writer_design_ui.py:151` asserts exactly 6 placeholders after `drop_implemented`, so
      implementing one breaks the test;
    - WARNING: the UITests depend on generated files outside the reviewed commit
      (`notebookbarOffice.py:38-39`). This is the split by design;
    - SUGGESTION: the `NEW_LABELS` comment says five label nodes, the dict holds four
      (`test_writer_layout_ui.py:97-99`); PageAreaDialog is asserted by the Design test.

- 2026-10-21, W4b (route: delegated, sonnet; the fix inline). Commits:
  - 2ef03d924: the Design and Layout icons, and the icon test extended to both tabs;
  - ebd26872f (controller, inline): the Style Set placeholder loses `expand`. At 1920 the expanded greyed box
    left an empty gap mid-group and pushed Colors, Fonts and Page Background to the far right. Screenshot
    after: `assets/previews/writer-ribbon-tabs/w4b-fix/light-design-1920.png`.
  - Evidence (report: `task-W4b-report.md`):
    - RED: 50 missing icon members on Design and 64 on Layout; GREEN: 478 tests OK;
    - the Style Set fix: RED on the renamed expand test, then 478 OK; `check-ui.sh` and `lo-make.sh sw.build`
      exit 0;
    - Calc is byte-identical; `check-ui.sh`, the build and the Layout UITest pass.
  - Explicit icons: the six Design placeholders need an `"icon"` in the JSON, because their URLs carry a `?`
    argument. Large controls must point at `cmd/32/...`; a `cmd/sc_` name renders 16 px in a large slot.
  - Glyphs without a Fluent match: Hyphenation uses `text_align_justify`, Position `layout_cell_four`.
  - Fit: both tabs fit at 1920. Design never collapses. On Layout, at 1600 and 1366, the whole Arrange group
    moves behind `>>`: it is the rightmost group, as in Word, but LibreOffice cannot collapse inside a group.
  - Breaks: a click on the button body opens the menu (`w4b/light-layout-1920-breaks-menu.png`).
  - Spin fields: readable, 191 and 199 px wide, about 2.7 times Word's. Parked for W9.
  - Controller look at light Design and Layout 1920: icons and sections are right; labels are LibreOffice's
    ("Theme", "Page Area", "Anchor Menu", "Navigator"), which T9w fixes.
  - RDD for 404294f79..ebd26872f: medium, under budget. It stays pending in the slice.

- 2026-10-21/22, T9w (route: delegated, opus). Commits:
  - 9871de25c: `office_label` for 51 Calc items, plus the regenerated Calc and Writer `.ui` and suppressions;
  - 22e203a66: `vcl/source/window/builder.cxx`. In the frame branch, a `.ui` label becomes the item text after
    `InsertItem(command, frame)`; the tooltip stays the command's. New `CppunitTest_vcl_builder`;
  - c293641c5: the generator puts `office_label` on the ribbon, unless it equals LibreOffice's label. Plus the
    unit tests, the Calc label pins and one UITest per app.
  - Spike first: a `.ui` label on a commanded tool button never showed. This is ruling 7; the user chose the
    vcl fix.
  - Evidence (report: `task-T9w-report.md`):
    - RED first for the CppUnit test, the generator tests, the Calc pins and both UITests;
    - GREEN: 478 -> 495 unit tests OK; `CppunitTest_vcl_builder`, both new UITests and one existing UITest per
      app pass;
    - `check-ui.sh` and `lo-make.sh sc.build sw.build` exit 0;
    - the Calc expected-diff check finds only 51 added item labels;
    - `gen_ribbon.py --all` leaves the tree clean.
  - Controller spot check: 495 OK, the tree is clean after `gen_ribbon.py --all`, no process left.
  - Controller look at `t9w/writer-insert-light-1920.png`: the buttons read Cover Page, WordArt, Drop Cap,
    Equation and Date & Time.
  - Menus keep LibreOffice's labels: Format > Title Page..., Insert > Fontwork.... Tooltips stay LibreOffice's.
  - Side effect: Shapes in the Groups notebookbars of Calc, Impress and Writer now reads "Shapes" (its `.ui`
    label) instead of "Basic Shapes". The bibliography toolbar is built without a frame and does not change.
  - Fit regression: at 1920, Calc Formulas hides Calculation and Calc Data hides Analyze behind `>>`. The base
    screenshots show both groups. Follow-up task T9w-fit.
  - Parked:
    - 96 suppressions are now unused (51 Calc, 45 Writer). The product tests still require a `button-no-label`
      suppression per ribbon button, so they stay;
    - commit 9871de25c alone is not reproducible by its own generator. This follows from the generated-first
      commit order;
    - some Excel labels sit on approximate Calc commands (Show Training, Contact Support, Show Queries, From
      Table, Workbook Statistics), from the design rows;
    - withheld labels: ShareDocument, and Gridlines and Headings on Page Layout;
    - clang-format 5.0.0 is not installed, so the new C++ test was not format-checked.
  - First review, of 9871de25c..c293641c5 (only the authored commits): the user granted it, and four lenses ran.
    - Reliability raised a deterministic BLOCKER: "the generated `.ui` were not regenerated". It was false. The
      base tree, 9871de25c, already holds the labels (`Cover Page` at line 3763 of the Writer `.ui`), and 495
      tests pass at HEAD. The split commit hid the generated files from the reviewer.
    - A deterministic finding gets no refuter, so the user authorized `gentle-ai review abandon` (lineage
      review-09327ba64d72dc2f, reason `operator_disposition`).
    - Lesson: split generated output only when it is too large for the lens budget. This generated diff was 164
      lines.
  - Second review, of a91cd6f15..c293641c5 (all three commits; W4b's commits fall before it and stay
    unreviewed): the user granted it. Four lenses ran; approved and acknowledged (lineage
    review-13157995130e1de7).
  - Parked review advisories (W9, test quality):
    - WARNING: the builder now honours a `.ui` label on any frame-built tool button, not only on the ribbon.
      Known scope: 8 buttons (ruling 7);
    - WARNING: the UITest thresholds (`> 50` in Calc, `> 40` in Writer) are unexplained;
    - WARNING: Writer's UITest `settle` was flagged as missing. It is false: it is defined at
      `notebookbarOffice.py:395`;
    - SUGGESTION: `settle` returns an unsettled value on timeout, silently;
    - SUGGESTION: a menu opened through accessibility may stay open if its popup is late;
    - SUGGESTION: the office-label test is copied into eight Calc modules, and the UITest helpers are duplicated
      across apps;
    - SUGGESTION: `CppunitTest_vcl_builder` loads a Writer document, so the vcl test depends on sw.

- 2026-10-22, T9w-fit (route: delegated, sonnet). Commit a0c9e3c2d:
  - Formulas: Financial, Logical and Text became one column of small buttons with labels. This is Excel's
    narrow-window look; Excel at 1920 shows them large.
  - Data: From Other Sources and Existing Connections became one column of small buttons with labels.
  - No label, group or control changed; `test_calc_formulas_ui.py` was updated for the new sizes.
  - Evidence (report: `task-T9w-fit-report.md`): 495 tests OK; `check-ui.sh` and `lo-make.sh sc.build` are
    clean; the Formulas and Data UITests pass; Writer's generated files are unchanged.
  - Fit at 1920: Formulas ends at x=1754 and still fits at 1840 px wide. Data ends at x=1791; it fits at
    1880 px and folds Analyze at 1840 px.
  - Collapse: Data matches the design at 1600 and 1366, and Formulas at 1600. At 1366, Formulas keeps Defined
    Names visible, which the design does not list. The design row is out of date (W10).
  - The other Calc tabs show no fold and no clipped label at 1920. View is the tightest, ending at x=1806.
  - Controller check: 495 OK, the tree is clean after `gen_ribbon.py --all`, no process left. Looked at the light
    1920 shots of Formulas and Data: every group shows, and the captions sit on one line.
  - RDD for c293641c5..a0c9e3c2d: medium, under budget. It stays pending in the slice.

- 2026-10-22, W5a (route: delegated, sonnet). Commits:
  - b4c7dbfe7: `writer_references.json` and the regenerated `.ui` and suppressions (+974/-518);
  - 26fa4a6d0: 3 popup files, Controller.xcu and WriterCommands.xcu nodes (3 menus, 4 placeholder variants),
    `test_writer_references_ui.py`, and 7 UITests. The `.ui` also loses 5 labels: once the new label nodes exist,
    Word's label equals LibreOffice's and the generator drops it.
  - Evidence (report: `task-W5a-report.md`):
    - RED: the unit tests errored before the layout file existed. The tab-visible and placeholders-inert UITests
      already passed, because References is a stock page;
    - GREEN: 495 -> 519 unit tests OK; the 7 new UITests, `test_tabbed_office_loads`, `test_tab_order` and the
      T9w labels UITest pass;
    - the build and `check-ui.sh` are clean; Calc is unchanged.
  - Controller spot check: 519 OK, the tree is clean after `gen_ribbon.py --all`, no process left.
  - Menu labels are the worker's wording: "Table of Contents", "Add Text to Contents", "Go to Footnote". The
    ribbon shows Word's text.
  - Behaviour: Edit and Remove Table of Contents are listed but disabled outside an index. Insert Caption is
    disabled in plain text, as LibreOffice does.
  - Review:
    - the whole slice from c293641c5 (T9w-fit and W5a, 2279 lines) hit `lens_context_budget_exceeded` at START
      after the user granted it. No authority was created;
    - the authored commit 26fa4a6d0 alone (633 lines): the user granted it. One lens (reliability); approved and
      acknowledged (lineage review-9d02af84e02caa1b). T9w-fit stays unreviewed.
  - Parked for W9 (test quality):
    - WARNING: the dropdown UITests build the popup through the controller directly. No test drives the ribbon
      button, and the three dropdown commands have no slot. W5b's click on the Table of Contents button covers
      it visually;
    - SUGGESTION: the Add Text UITest sets "Heading" but never applies an entry or checks the outline level.

- 2026-10-22, W5b (route: delegated, sonnet). Commit 6bed2991d: the References icons, the icon test extended, and
  explicit icons in `writer_references.json` with the regenerated `.ui`.
  - Evidence (report: `task-W5b-report.md`): RED, 92 missing icon members; GREEN, 521 tests OK; build, install,
    `check-ui.sh`, `sw.build` and one References UITest pass; Calc unchanged.
  - Explicit icons: the three placeholders (URL arguments), and Show Notes (`JumpToFootnoteOrAnchor`). Its PNG is in
    the installed zip, yet the icon rendered blank without an explicit `"icon"`. That is the second plain command
    after Drop Caps (W3b); the root cause is open for W9.
  - Bibliography, Insert Table of Figures and Insert Index share one icon, because all three are
    `.uno:InsertMultiIndex`.
  - Fit: the tab ends at x=1444, a margin of 476 px. Nothing collapses at 1600. At 1366, Table of Authorities
    goes behind `>>`, as the design says.
  - A click on the Table of Contents button body opens its menu (`w5b/light-references-1920-toc-menu.png`). This
    covers the W5a review warning visually.
  - Controller check: 521 OK, the tree is clean after `gen_ribbon.py --all`, no process left. Looked at
    `w5b/light-references-1920.png`: Word's groups and labels, with the placeholders greyed.
  - RDD for 26fa4a6d0..6bed2991d: medium, under budget. It stays pending in the slice.

- 2026-10-22, W6a (route: delegated, sonnet). Commits:
  - 7e4cf361b: `writer_mailings.json`, `writer_tabs.json` (Mailings at position 6; Review to Tools shift to
    7..17), the regenerated `.ui` (966 lines) and `swriter.suppr`. It also holds the one-line fix to
    `test_writer_design_ui.py`, which pins the tab positions. The controller added that file to the surface
    after the worker stopped with NEEDS_CONTEXT;
  - 604c02701: 2 popup files, Controller.xcu and WriterCommands.xcu nodes (2 menus, 8 placeholder variants),
    `test_writer_mailings_ui.py`, and 8 UITests.
  - Tab label `M~ailings` (access key A): `~M` would clash with the contextual Media tab. This was the worker's
    choice, accepted by the controller, and it differs from the design's `~Mailings`.
  - Evidence (report: `task-W6a-report.md`):
    - RED: 13 of 25 new unit tests failed; `test_tab_order` failed with '18' != '17'; the dropdown test failed on
      the missing controller;
    - GREEN: 521 -> 546 unit tests OK; 12 UITests pass, one at a time;
    - the build and `check-ui.sh` are clean; Calc is unchanged.
  - Controller spot check: 546 OK, the tree is clean after `gen_ribbon.py --all`, no process left.
  - Record box: outside a mail merge, First, Previous, Next and Last are disabled. The record box item stays
    enabled, and its controller greys only the entry field. Design section 1 calls it greyed, which is true of the
    field only (W10).
  - Review of 604c02701 (623 lines): medium; the user granted it. One lens (reliability); approved and
    acknowledged (lineage review-da58bf2532a0970e). W5b (6bed2991d) and 7e4cf361b stay unreviewed.
  - Parked for W9 (test quality):
    - WARNING: the record-button UITest reads Enabled right after switching to the office UI, without `settle`.
      It can be flaky;
    - SUGGESTION: `test_writer_mailings_ui.py:88` filters placeholders with `drop_implemented`, then asserts
      exactly 8 (the same pattern as Design);
    - SUGGESTION: no runtime test drives the ribbon dropdown arrows through GenericPopupToolbarController. W6b's
      click covers it visually.

- 2026-10-22, W6b (route: delegated, sonnet). Commit 2e760bcaf: the Mailings icons, the icon test extended, and
  explicit icons in `writer_mailings.json` with the regenerated `.ui`.
  - Evidence (report: `task-W6b-report.md`): RED, the Mailings icon test failed on `cmd/sc_insertenvelope.png`;
    GREEN, 548 tests OK; build, install, `check-ui.sh`, `sw.build` and one Mailings UITest pass; Calc unchanged.
  - Labels (`InsertLabels`) rendered blank until it got an explicit `"icon"`. That is the third plain command,
    after Drop Caps and Show Notes; the root cause is open for W9.
  - Check for Errors: the red fill hid the "!" when greyed, so its manifest entry is line-only.
  - Fit: the tab ends at x=1443, a margin of 477 px. Nothing collapses at 1600. At 1366, Finish and then Preview
    Results go behind `>>`, right to left, as the design says.
  - A click on the Finish & Merge button body opens its menu (`w6b/light-mailings-1920-finish-menu.png`).
  - Controller look at `w6b/light-mailings-1920.png`: Word's groups and labels. Defect found, for W9: the
    Mailings ribbon is about 9 px taller than the other tabs. The ruler is at y=190, not 181, and the captions at
    y=156, not 147, so the document jumps when the tab changes. The record box (an entry field) is the likely
    cause.
  - The record box showed "-1" after the Finish menu click (W9).
  - Controller check: 548 OK, the tree is clean after `gen_ribbon.py --all`, no process left.
  - RDD for 604c02701..2e760bcaf: medium, under budget. It stays pending in the slice.

- 2026-10-22, W7a (route: delegated, sonnet). Commits:
  - 820baee29: `writer_review.json` (10 sections, 24 controls) and the regenerated `.ui` (1940 lines),
    `swriter.suppr` and `swriter.false`;
  - 6f24be2b0: 5 popup files, Controller.xcu nodes (5 Popup and 5 ToolBox; Calc owns none of the names, so no
    `Writer` suffix), WriterCommands.xcu labels (5 menus, 8 placeholder variants), `test_writer_review_ui.py`
    (29 tests), and 9 UITests. The new label nodes trim 7 lines of the `.ui`.
  - Evidence (report: `task-W7a-report.md`):
    - RED: 11 unit tests failed and 2 errored with only the JSON in place; the UITests failed on the missing
      sections and controllers;
    - GREEN: 548 -> 577 unit tests OK (commit 1 alone: 548 OK); 9 new UITests, `test_tabbed_office_loads`,
      `test_tab_order` and the T9w labels UITest pass, one at a time;
    - the build and `check-ui.sh` are clean; Calc is unchanged.
  - Controller spot check: 577 OK, the tree is clean after `gen_ribbon.py --all`, no process left.
  - `placeholders_writer.json`: the Comments placeholder labels are now "Previous Comment" and "Next Comment"
    (Calc's wording), so the menu and tooltip text is unambiguous. The ribbon still shows "Previous" and "Next"
    through `office_label`.
  - Design notes for W10:
    - section 1 calls the Accept/Reject/Previous/Next group "Tracking"; Word 365 calls it "Changes". The worker
      followed section 1;
    - section 1 lists Check Accessibility as `.uno:AccessibilityCheck`, an alias with no dispatch of its own; its
      state comes from `SidebarDeck.A11yCheckDeck`.
  - Concerns:
    - the Language submenus are filled by MenuBarManager only when the menu opens. The UITest builds each
      `SetLanguage*Menu` controller directly; the real click is W7b's screenshot;
    - Thesaurus, Hangul/Chinese conversion and Show Comments are not asserted enabled, because they depend on the
      environment (a thesaurus, Asian support, a comment);
    - `controller_nodes()` in `commands.py` keys by node name, so the stock `cNN` language nodes collide; the new
      test reads them by command (W9);
    - widget ids repeat the prefix for the new commands (`btnReviewReviewAcceptMenu`), as on Mailings.
  - Review of 6f24be2b0 (880 lines): medium; the user granted it. One lens (reliability); approved and
    acknowledged (lineage review-76fe1839059d2644). One SUGGESTION, R3-001, on the dropdown popup UITest
    (`notebookbarOffice.py:1011-1027`), with no text attached; parked for W9. W6b (2e760bcaf), the docs commits and
    820baee29 stay unreviewed.

- 2026-10-22, W7b (route: delegated, sonnet; the test fix inline, controller). Commits:
  - a22437b09: the Review icons (20 new Fluent entries, none custom; Spelling, Thesaurus, New Comment and Show
    Comments reused), the icon test extended, and explicit icons for the 4 placeholder controls;
  - e0108c293: the 1920 px fit. Protect and Ink were behind `>>`. Thesaurus with Word Count, and Previous, Next and
    Show Comments, are now stacked small-label buttons, as Word narrows those groups;
  - 3942ac2b9: `test_writer_review_ui.py` pins the fitted sizes. The worker's fit commit left 2 tests red, because
    that file was outside its surface; it stopped with NEEDS_CONTEXT, and the controller fixed the test inline.
    e0108c293 alone fails those 2 tests.
  - Evidence (report: `task-W7b-report.md`): RED, 98 missing icon members; GREEN, 579 unit tests OK after
    3942ac2b9; build, install, `check-ui.sh`, `sw.build` and one Review UITest pass; Calc unchanged.
  - No plain command rendered blank on Review; the Drop Caps, Show Notes and Labels root cause is still open (W9).
  - Fit: the tab ends at x=1788, a margin of 132 px. At 1600, Ink, Protect and Compare go behind `>>`; at 1366,
    Tracking too. Whole groups, right to left, as the design says.
  - Ribbon height matches Home: captions at y=157, ruler at y=191.
  - Language: a click on the button body opens its menu, and moving across "Language for Selection" opens the
    submenu with the document languages (`w7b/light-review-1920-language-submenu.png`). This is the real-click
    evidence W7a could not get from a UITest.
  - Controller check: 579 OK, the tree is clean after `gen_ribbon.py --all`, no process left. Looked at
    `w7b/light-review-1920.png` and the submenu shot: Word's groups and labels, the placeholders greyed.
  - For W9: a two-button small-label column (Proofing, and Tracking's Previous/Next) spreads its buttons to the
    top and lower rows (y=62 and y=111), while a three-button column uses all three rows. Compare with Word's
    alignment of two small buttons.
  - For W10: design section 1 lists Thesaurus, Word Count, Previous, Next and Show Comments as L; after the fit
    they are S.
  - RDD for 6f24be2b0..3942ac2b9: medium, under budget (236 lines). It stays pending in the slice.

- 2026-10-22, W8a (route: delegated, sonnet). Commits:
  - 027e8f459: `writer_view.json`, `writer_help.json`, `writer_tabs.json` (the Help page through `add_pages`, last,
    at position 18), the regenerated `.ui` (2207 lines), `swriter.suppr` and `swriter.false`, and the one-line
    `test_writer_mailings_ui.py` edit (Help joins the tab order);
  - ff29c3f19: `view_macros.xml`, Controller.xcu nodes (`ViewSwitchWindowsMenuWriter` on WindowListMenuController
    with no popup file, as Calc; `ViewMacrosMenuWriter` on ResourceMenuController), WriterCommands.xcu (2 menus,
    12 placeholder variants, the Help tab label), `test_writer_view_ui.py` (28 tests), `test_writer_help_ui.py`
    (19 tests), and 15 UITests. The label nodes trim 14 lines of the `.ui`.
  - The worker first stopped with NEEDS_CONTEXT and no commits: the Mailings tab-order test was outside its
    surface. The controller added that file for the one-line edit (Amendment 1), and the worker made both commits.
  - Help tab label `H~elp` (access key E): the design's `Hel~p` clashes with the contextual Print tab, L with
    Layout and H with Home. A unit test checks that E is unique. The worker's choice, accepted by the controller.
  - Evidence (report: `task-W8a-report.md`):
    - RED: the Switch Windows and Macros controllers were missing, and the section tests failed on the missing
      JSON;
    - GREEN: 579 OK at commit 1 (new test files aside), 626 OK at commit 2; 17 UITests pass one at a time,
      including Switch Windows with two Writer documents, `test_tab_order` with Help last, and the T9w labels test;
    - the build and `check-ui.sh` are clean (unused suppressions 653 -> 663, the known class); Calc is unchanged.
  - Controller spot check: 626 OK, the tree is clean after `gen_ribbon.py --all`, no process left.
  - Macro Manager: hidden in the Macros popup unless experimental mode is on, as in Calc (`IsExperimental` in
    GenericCommands.xcu).
  - For W9/W10: Multiple Pages (`.uno:ShowMultiplePages`) is greyed while editing, because only the print-preview
    shell handles it. The design keeps it on View > Zoom; Word's Multiple Pages works in the editing view.
  - RDD for ff29c3f19 (992 lines): medium, budget reached. The user declined it (candidate-scoped); medium tier
    off-path: the writer's self-verification and the controller spot check. A machine restart cleared the
    scratchpad before the answer was applied, so the controller took a fresh consent envelope for the same
    target and ran its decline invocation.

## Next step

W8b: View and Help, icons, 1920 fit and screenshots (delegated, sonnet). Brief: `task-W8b-brief.md`.

# Feature: Impress ribbon tabs like PowerPoint (Tabbed Office)

- **Status:** planned, 2026-10-23 (written in task ID1, accepted by the controller). Started 2026-10-23, after Writer
  closed (design decision 38, ruling 13).
- **Locator:** `product/odd/tasks/impress-ribbon-tabs.md`
- **Engram mirror:** `odd/impress-ribbon-tabs/tasks`
- **Repo / branch:** `/mnt/games/libreoffice/core`, `feature/impress-ribbon-tabs`, branched from the tip of
  `feature/writer-ribbon-tabs` once W11 lands (ruling 13).
- **Design:** `product/docs/impress-ribbon-tabs.md`. Section and decision numbers below refer to it.
- **SDD workspace:** `/mnt/games/libreoffice/core/.superpowers/sdd/2026-10-20-writer-impress-ribbons/` (briefs,
  research, map, reports; never committed)

## Objective

Make the Tabbed Office Impress ribbon look like PowerPoint for Microsoft 365: same tabs, same order, same sections
and controls in the same places, built the way Calc's and Writer's were. Controls whose feature LibreOffice lacks are
greyed placeholders; cloud controls are omitted. Implementing the missing features comes later.

## Problem and why

The request (task ID1 brief, 2026-10-23): Calc looks like Excel 365 and Writer like Word 365; "Impress is next: its
ribbon must look like PowerPoint 365, built the same way, with greyed placeholders for features LibreOffice lacks,
cloud features omitted, and the LibreOffice-only buttons listed per tab and kept reachable in the menu bar, with a
test."

Impress has no Tabbed Office mode yet: cui allows it only for Calc and Writer
(`cui/source/dialogs/uitabpage.cxx:93-96`), the Impress mode table has no TabbedOffice node
(`officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu:602-856`), and the generator knows two apps
(`product/ui/gen_ribbon.py:72-79`). Impress's stock Tabbed ribbon is LibreOffice's layout, not PowerPoint's: it has
a Layout tab of slide-management buttons and no Transitions, Animations or Help tab (design section 1).

## Rulings (binding; design section 4 holds the rest)

- **Reference:** PowerPoint for Microsoft 365, Windows, Current Channel, 2024+ look, at 1920 px. Same as Calc and
  Writer.
- **Tabs:** File, Home, Insert, Design, Transitions, Animations, Slide Show, Review, View, Help. Extension and Tools
  stay with their content; Help is last.
- **Not in this feature:** PowerPoint's Draw (ink) and Record tabs (design decisions 4-5), the File backstage,
  PowerPoint's contextual tabs. Impress's stock contextual tabs (Table, Image, Draw, Object, Media, Form, Master,
  Outline, 3D) stay exactly as they are.
- **Missing features** are greyed placeholders on family slots; cloud or account controls are omitted and listed
  (design decision 29). Translate is a placeholder, as in Calc and Writer (design decision 30).
- **Every LibreOffice button the PowerPoint layout drops** is listed per tab, stays reachable in the menu bar, and a
  test asserts it (design section 2).
- **Labels (ruling T9):** the ribbon shows PowerPoint's labels (`office_label`); menus, help and tooltips keep
  LibreOffice's.
- **Accent (ruling 1):** PowerPoint orange, `#C43E1C` light and `#FF8F6B` dark (design 3.4; the hex is inferred).
- **Icons (ruling 8):** plain grey line icons; color only as a small badge that means something.
- **Greyed menu entries (T10w):** disabled popup entries show greyed, through W9c.
- **Working mode (ruling 9, ruling 12):** the controller rules on open decisions and records them, without asking;
  receipt-driven review is off for this clone (the user's decision, 2026-10-23).

## Scope

**In scope:**
- Pages of `sd/uiconfig/simpress/ui/notebookbar_office.ui` generated from `product/ui/impress_<tab>.json`: Home,
  Insert, Design, Transitions (the stock Layout page), Animations, Slide Show, Review, View, Help; tab operations in
  `product/ui/impress_tabs.json`.
- The generator, test tooling and dev scripts for three apps, with Calc's and Writer's output byte-identical.
- The Impress Tabbed Office mode: ToolbarMode node, cui whitelist and preview picture, profile, launcher,
  screenshots, UITest scaffold.
- Dropdowns, placeholder commands and slots, labels, icons, the accent, tests, docs.

**Out of scope:** implementing placeholder features; inline transition and animation controls (design decision 25);
PowerPoint's Draw and Record tabs, File backstage and contextual tabs; Draw's ribbon; translations.

## Constraints

- Build only through `product/dev/lo-make.sh`; run UITests only through `product/dev/uitest.sh`.
- The stock `sd/uiconfig/simpress/ui/notebookbar*.ui` and Draw's files stay untouched; the office `.ui` stays "stock
  + tab operations + generated pages".
- Calc and Writer stay byte-identical: every task that touches shared code (generator, test tooling, dev scripts,
  cui) proves the sha256 of `sc/uiconfig/scalc/ui/notebookbar_office.ui`, `solenv/sanitizers/ui/modules/scalc.suppr`,
  `scalc.false`, `sw/uiconfig/swriter/ui/notebookbar_office.ui`, `swriter.suppr` and `swriter.false` unchanged, and the Calc and
  Writer tests stay green.
- A split or dropdown needs a dedicated command; never put a new controller on a command that other toolbars use. A
  popup controller works only under its original command (Writer's header/footer lesson).
- `DrawImpressCommands.xcu` is shared with Draw: add nodes, never change an existing one.
- Never touch the user's profiles (`/mnt/games/libreoffice/try-profile`, `try-profile-writer`); the Impress dev
  profile is `/mnt/games/libreoffice/try-profile-impress`. Kill only your own soffice, by PID.
- UITests: no tab CLICK on the headless backend (`executeAction("SELECT", {"POS": ...})`), `settle` before reading
  state, open only Impress documents, close the template dialog.
- Commits are Conventional, subject <= 79 characters, no AI attribution. Never commit `.superpowers/`.
- Artifacts in English.

## Acceptance criteria

- Each tab shows PowerPoint's sections and controls in PowerPoint's order (design section 1), placeholders greyed
  and inert, omitted controls absent.
- The tabs appear in PowerPoint's order with PowerPoint's names and unique new mnemonics (N, A, P); the contextual
  tab objects equal the stock ones.
- Every command that leaves a tab is reachable as design section 2 records, and a test asserts it.
- Calc's and Writer's generated files are byte-identical to before the feature.
- Tabbed Office can be chosen in Impress's User Interface dialog, with an Impress preview picture; Draw is unchanged.
- The selected tab's underline is PowerPoint orange in Impress, and still green and blue in Calc and Writer.
- Unit tests, gla11y/lint (`check-ui.sh`) and UITests pass. Light and dark screenshots of every tab at 1920 px
  exist, and the user approves them visually.

## TDD

- **Mode:** strict.
- **Runners:**
  - `python3 -I -m unittest discover -s product/tests -t .`
  - `product/dev/uitest.sh --app impress notebookbarOffice.NotebookbarOffice.<test>` (I0b adds `impress`)
  - `product/dev/check-ui.sh sd/uiconfig/simpress/ui/notebookbar_office.ui`
- Layout tests compare each generated page with a DESIGN table copied by hand into its test module
  (`product/tests/test_impress_<tab>_ui.py`), as Calc and Writer do.
- RED first wherever a deterministic test exists. Exceptions: the 1920 px fit is measured by screenshots
  (`product/dev/shot-tab.sh`), the docs task is passive (structural readback), and the visual gate has no RED.
- A UITest goes through `UITest_impress_tests2`, which rebuilds what changed first, so a RED UITest run already uses
  the new sources.

## Delivery

- **Forecast:** about 7800 authored changed lines (range 6500-9000), generated `.ui` and `.suppr` excluded. Basis:
  the per-task estimates below (171 controls, 19 new menus, 24 slots, 70 leave-list rows); Writer's 7000 for 193
  controls, 30 dropdowns and 24 slots is the check. The biggest parts are tests (about 2000), XCU labels and
  controllers (about 1300), UITests (about 1000), docs (about 800) and slot declarations (about 500).
- **Strategy:** Writer's (controller ruling, the user can overturn it): one work-unit commit per task, plus a
  separate generated commit where the generated diff is too big for the review lens budget (Writer lesson: split it
  only then; W0a's 15261-line `.ui` needed it, T9w's 164 lines did not). `dev` is fast-forwarded and pushed only when
  the user asks. No pull requests; each slice below is the review candidate.
- **Slices** (about 700-1100 lines each):

| Slice | Tasks | Forecast |
|---|---|---|
| S1 infrastructure | I0a, I0b | 700 |
| S2 placeholder slots | I1 | 740 |
| S3 Home, part 1 | I2a | 700 |
| S4 Home, part 2 and icons | I2c, I2b | 900 |
| S5 Insert and Design | I3a, I3b, I4a, I4b | 1000 |
| S6 Transitions and Animations | I5a, I5b | 900 |
| S7 Slide Show and Review | I6a, I6b, I7a, I7b | 1080 |
| S8 View, Help, polish | I8a, I8b, I9 | 970 |
| S9 docs and gate | I10, I11 | 850 |

- **RDD:** off for this clone (`gentle-ai review mode status`: off, decided by clone_local; the user's decision,
  2026-10-23). No review starts and no consent is asked. The gate per task is the writer's own verification plus the
  parent's spot check: the unit suite, `gen_ribbon.py --all` leaving the tree clean, the Calc and Writer sha256
  check when shared code changed, and a look at the screenshots. If the user turns RDD back on, the review candidate
  is one work-unit commit or one slice, never the branch (Writer: the 2279-line slice from c293641c5 hit
  `lens_context_budget_exceeded` at START; single commits up to 992 lines passed).

## Tasks

| ID | Task | Route | Status | Commits | RDD |
|----|------|-------|--------|---------|-----|
| I0a | Generator and test tooling for three apps; Impress office `.ui` = stock + tab operations; registration; suppressions; unique-id test | delegated (opus: shared code, Calc and Writer byte-identical) | [ ] | | |
| I0b | Impress Tabbed Office mode end to end: ToolbarMode node, cui whitelist, profile (template dialog off), launcher, shot-tab, uitest.sh, UITest scaffold | delegated (opus: cui C++ and shared scripts) | [ ] | | |
| I1 | All 24 placeholder slots in one sd rebuild, with the registry and the slot test | delegated (opus: C++ and `.sdi`) | [ ] | | |
| I2a | Home, part 1: Undo, Clipboard, Slides, Font, Paragraph (5 menus); layout, labels, popups, placeholder labels, unit tests, UITests | delegated (sonnet) | [ ] | | |
| I2c | Home, part 2: Drawing (shape gallery, Arrange, Shape Effects) and Editing (6 menus) | delegated (sonnet) | [ ] | | |
| I2b | Home icons, 1920 fit (through control sizes), screenshots | delegated (sonnet), after I2c | [ ] | | |
| I3a / I3b | Insert | as I2a / I2b | [ ] | | |
| I4a / I4b | Design (moved before Transitions) | as I2a / I2b | [ ] | | |
| I5a / I5b | Transitions (the stock Layout page, relabelled) and Animations (new page) | as I2a / I2b | [ ] | | |
| I6a / I6b | Slide Show | as I2a / I2b | [ ] | | |
| I7a / I7b | Review | as I2a / I2b | [ ] | | |
| I8a / I8b | View and Help (new page) | as I2a / I2b | [ ] | | |
| I9 | Polish: fit and caption baseline across tabs, other views, the accent (data only: W9a's mechanism already maps Impress, design 3.4) | delegated (sonnet) | [ ] | | |
| I10 | Docs: `product/docs/impress-ribbon-tabs.md` from the draft and the results | delegated (sonnet) | [ ] | | passive (docs) |
| I11 | Visual gate: contact sheets, Impress preview picture, user gate | delegated (sonnet) | [ ] | | |

Route evidence: every task touches two or more non-trivial files, so each is delegated to one writer (writer
trigger); the parent keeps the spot checks.

Why this shape: Writer's shape, with Home split in two (I2a and I2c, about 700 lines each: Home has 64 controls and
11 menus, more than one task should carry) and Transitions paired with Animations (both open the same kind of deck
and neither has a menu). Help goes with View, as in Writer. I1 exceeds the 400-line heuristic on purpose: 24 slot
declarations in one sd rebuild, as Writer's W1 did.

### I0a: generator and test tooling for three apps

- **Files:** `product/ui/gen_ribbon.py` (the `impress` entry in `APPS` `:72-79`, design 3.1);
  `product/ui/impress_tabs.json` (new: only the two `valign` properties; pages and labels come with their tasks);
  `product/tests/office.py`, `commands.py` (`LOOKUP_ORDERS` `:15-18`, `controller_nodes` `:55-70` with the `Impress`
  suffix), `placeholders.py` (`REGISTRIES` `:22`); `product/tests/test_gen_ribbon.py`;
  `product/tests/test_impress_tabs.py` (new); `sd/uiconfig/simpress/ui/notebookbar_office.ui` (generated);
  `sd/UIConfig_simpress.mk` (one line after `:153`); `solenv/sanitizers/ui/modules/simpress.suppr` (the 639 stock
  lines seeded with the office path, then generated).
- **Checks:** unit tests; the six Calc and Writer sha256 values recorded before the change match after
  `gen_ribbon.py --all`; `product/dev/check-ui.sh sd/uiconfig/simpress/ui/notebookbar_office.ui` (no new warnings or
  fatals); `check-ui.sh` on the Calc and Writer office `.ui` (unchanged); `product/dev/lo-make.sh sd.build`; Draw's
  `sd/uiconfig/sdraw/` unchanged (`git status`).
- **RED:** `test_impress_tabs.py` expects `office.expected_office_ui("impress")` to equal the committed Impress office
  `.ui`, the Impress suppressions to mirror every stock line with the office path, and every object id in the
  office `.ui` to be unique; it fails before the app entry exists. `test_gen_ribbon.py` gains "`--all` writes three
  apps".
- **Commits:** the generated `.ui` (about 14700 lines) and `impress_tabs.json` in one commit, the code in another
  (Writer W0a's split).

### I0b: Impress Tabbed Office mode end to end

- **Files:** `ToolbarMode.xcu` (Impress `TabbedOffice`, MenuPosition 9, copied from Calc's `:437-464` into the
  Impress node `:602`); `cui/source/dialogs/uitabpage.cxx` (`HasTabbedOffice` `:93-96`); `product/dev/profile.py`
  (`APPS` `:18`, `build_items` `:38`: Impress and `NewDoc/AutoPilot` = false) and `product/tests/test_profile.py`;
  `product/dev/office.sh` (`impress` case, `:27-28`) and `product/tests/test_calc_launcher.py`;
  `product/dev/shot-tab.sh` (`:24-26`, `:45`, `:50`, `:61-66`: app option, tab list, measured `x0`);
  `product/dev/uitest.sh` (`impress` -> `impress_tests2`, `:4-25`) and `product/tests/test_uitest_script.py`;
  `product/tests/test_writer_mode.py` (`:52-70`, `:84`: Impress now has TabbedOffice) or a new
  `test_impress_mode.py`; `sd/qa/uitest/impress_tests2/notebookbarOffice.py` (new).
- **Checks:** unit tests; `product/dev/lo-make.sh cui.build officecfg.build postprocess.build`;
  `product/dev/uitest.sh --app impress notebookbarOffice.NotebookbarOffice.test_tabbed_office_loads` and
  `...test_tab_order`; one Calc and one Writer UITest still pass; one Impress screenshot through
  `product/dev/shot-tab.sh --app impress`; Calc and Writer sha256 check.
- **RED:** the Impress case of `test_profile.py` (including AutoPilot false); an XCU test that Impress has
  `TabbedOffice` at MenuPosition 9 with CommandArg `notebookbar_office.ui`; a source test that the cui helper lists
  Impress and not Draw; the UITest `test_tabbed_office_loads` fails before the ToolbarMode node exists.
- **Notes:** the three tests that use `impress` as the invalid app (`test_profile.py:99`,
  `test_calc_launcher.py:145`, `test_uitest_script.py:70`) switch to `draw`. The scaffold's open helper creates an
  Impress document and closes the template dialog through "close" (`tdf130440.py:16-19`); every Impress UITest uses
  it.

### I1: placeholder slots

- **Files:** `sd/inc/app.hrc` (`SID_BOOST = SID_SD_START + 900` after `:437`, `SID_BOOST_*` +0..+23); `sd/sdi/sdraw.sdi`
  (24 declarations in the format of `:4269-4285`); `sd/sdi/ViewShellBase.sdi` (`ViewShellBaseView` `:19`, state method
  only); `sd/source/ui/view/ViewShellBase.cxx` (one `DisableItem` group at the start of `ViewShellBase::GetState`,
  `:706-711`); `product/tests/placeholders_impress.json` (new; slots, offsets, URL variants; labels come with the tab
  tasks); `product/tests/test_impress_slots.py` (new, after `test_writer_slots.py`).
- **Checks:** unit tests; `product/dev/lo-make.sh sd.build`; `product/dev/uitest.sh --app impress
  notebookbarOffice.NotebookbarOffice.test_placeholder_slots_disabled` (every registry URL dispatched in an Impress
  document is disabled and changes nothing, in Normal and Slide Sorter view).
- **RED:** `test_impress_slots.py` (each slot in the fork block, declared, listed in `ViewShellBaseView` with no
  execute method, in the disabled group, no other source mentions it, no gaps or duplicates, no other define in
  27900-27999) and the UITest, both before the sources change.

### I2a-I8a: one tab (or tab pair), layout and behaviour

Common to every a task:

- **Files:** `product/ui/impress_<tab>.json`; `product/ui/impress_tabs.json` when the task changes tabs (I4a: `move`
  and positions of Design and Layout; I5a: `relabel` of `LayoutLabel` and `add_pages` Animations, positions after
  it; I8a: `add_pages` Help); popup files in `sd/uiconfig/simpress/popupmenu/` and their lines in
  `sd/UIConfig_simpress.mk:16-...`; labels in `DrawImpressCommands.xcu` (menus, placeholder variants, URL
  variants); `Controller.xcu` Popup and ToolBox nodes (Module `com.sun.star.presentation.PresentationDocument`,
  node names with an `Impress` suffix); `product/tests/placeholders_impress.json` (labels);
  `product/tests/test_impress_<tab>_ui.py` (new); every test that pins tab positions or order
  (`test_impress_tabs.py` and the earlier `test_impress_<tab>_ui.py` files: Writer's W8a stopped once because a
  tab-order test was outside its surface); `sd/qa/uitest/impress_tests2/notebookbarOffice.py`; the generated `.ui`
  and suppressions.
- **Checks:** unit tests; `product/dev/lo-make.sh sd.build officecfg.build postprocess.build`; `check-ui.sh` on the
  Impress office `.ui`; the tab's UITests one by one; Calc and Writer sha256 check.
- **RED:** the DESIGN table test of the page, the label/controller/popup checks of every command, the
  `LEFT_THE_TAB` test (exact menu-bar id for class a, the equivalent id for class b, the quick access bar for
  `Menubar`, View > Toolbars for class c), and the tab's UITests (tab visible with a shape, a table, an image and
  text selected; dropdown contents built through the real controllers; placeholders disabled and inert).

Per tab (counts from design section 1; dropdown names from its tables):

| Task | Pages | Dropdowns (popup file or controller) | New labels | Leave-list rows | Forecast |
|---|---|---|---|---|---|
| I2a Home, part 1 | Home Tab: Undo, Clipboard, Slides, Font, Paragraph | 5: HomeSectionMenu, HomeChangeCaseMenu, HomeColumnsMenu, HomeTextDirectionMenu, HomeAlignTextMenu | 5 menus, 4 placeholder entries, 3 TextColumnsNumber variants, the Reset variant | 23 | 700 |
| I2c Home, part 2 | Home Tab: Drawing, Editing | 6: InsertShapesMenu, HomeArrangeMenu, HomeShapeEffectsMenu, HomeFindMenu, HomeReplaceMenu, HomeSelectMenu | 6 menus, 5 placeholder entries | 0 | 700 |
| I3a Insert | Insert | 2: InsertZoomMenu, InsertTextBoxMenu (InsertShapesMenu from I2c) | 2 menus, 6 placeholder entries | 9 | 500 |
| I4a Design | Design, moved | 1: DesignVariantsMenu | 1 menu, 3 placeholder entries | 0 | 300 |
| I5a Transitions, Animations | Layout, relabelled; new Animations | 0 | 3 placeholder entries | 15 | 750 |
| I6a Slide Show | SlideShow | 0 | 3 placeholder entries | 2 | 350 |
| I7a Review | Review | 2: ReviewLanguageMenu, ReviewDeleteCommentMenu | 2 menus, 10 placeholder entries | 3 | 550 |
| I8a View, Help | View; new Help | 3: ViewColorGrayscaleMenu, ViewSwitchWindowsMenu (WindowListMenuController), ViewMacrosMenu | 3 menus, 5 placeholder entries | 18 | 550 |

Tab-specific checks:

- I2a: New Slide's popup is the layout gallery plus Duplicate Slide, and Layout's is the gallery plus Reset Slide
  Layout (design decision 19); Reset puts a moved title placeholder back (decision 13); Two Columns gives a text box
  two columns (decision 14). Each gate falls back as its decision says.
- I2c: the shape sub-toolbar cells open their stock popups; the Find menu's first item is the find toolbar URL; the
  Arrange menu lists its items with a shape selected.
- I3a: Video and Audio have distinct widget ids (decision 16); the Shapes submenus open.
- I4a: Design shows before Transitions; the theme colors box (`.uno:ThemeSelectorPanel`) still renders.
- I5a: the tab reads Transitions with mnemonic N and Animations with A; every deck control opens its deck and a
  second press keeps it open (decision 25); Animation Pane toggles the Animation deck.
- I6a: Hide Slide toggles the current slide's hidden state from Normal view (decision 28); the three Set Up
  controls open the Set Up Slide Show dialog.
- I7a: the Language submenu comes from its controller (`Controller.xcu:155`); Previous and Next move between
  comments.
- I8a: Switch Windows lists two open Impress windows; Help is the last tab, mnemonic P; the view buttons switch
  views and back.

### I2b-I8b: icons, 1920 fit, screenshots

- **Route:** delegated (sonnet), each after its a task.
- **Files:** `product/icons/manifest.json` and vendored Fluent SVGs (excluded from the forecast); the layout files
  for explicit icons (the deck controls of I5a share one URL, so each needs its own `icon`; every `?` variant needs
  one); `product/tests/test_impress_icons.py` (new; folded into `test_icons.py` later by agreement with its owner).
- **Checks:** unit tests; `python3 -I product/icons/build_theme.py install --instdir instdir`; light and dark
  screenshots of the tab at 1920, 1600 and 1366 px through `product/dev/shot-tab.sh --app impress`, outside the
  repository.
- **RED:** the icon coverage test for the tab's commands in both themes fails before the manifest entries exist.

### I9: polish

- **Files:** depends on findings: layout files (control sizes), `impress_tabs.json` (caption baseline); the accent:
  `product/themes/palette.json` (`accent.impress`, `tab_accents`), `product/tests/test_schemes.py`. No C++: W9a's
  `lcl_getTabAccentColor` already maps Impress (`sfx2/source/notebookbar/NotebookbarTabControl.cxx:164`).
- **Checks:** unit tests; the scheme build (`product/themes/build_schemes.py`); screenshots of every tab, Slide
  Sorter included; a pixel check that the selected tab's underline is orange in Impress and still green in Calc and
  blue in Writer.
- **RED:** a caption-baseline test across Impress tabs; a scheme test that `accent.impress` reaches Impress's
  ToolbarMode values, and the pixel check, both failing first.

### I10: docs

- **Files:** `product/docs/impress-ribbon-tabs.md` (from the design draft, with the build results, counts and test
  totals), `product/odd/tasks/impress-ribbon-tabs.md` (this file).
- **Checks:** structural readback; every path:line in the doc still resolves (`rg` spot checks).
- **RED:** none (passive documentation).

### I11: visual gate

- **Files:** `vcl/Package_toolbarmode.mk` (one line, `notebookbar_office_impress.png`), the picture itself; contact
  sheets outside the repository: `/mnt/games/libreoffice/assets/previews/impress-ribbon-tabs-light.png` and
  `...-dark.png`.
- **Checks:** `product/dev/lo-make.sh vcl.build`; the User Interface dialog shows the Impress picture for Tabbed
  Office; the user approves the contact sheets and the accent.
- **RED:** none (visual gate).

## Checks

Every task, before its work-unit commit:

1. `python3 -I -m unittest discover -s product/tests -t .` (all product tests, Calc's and Writer's included).
2. The Calc and Writer byte-identity check (sha256 of the six files of the Constraints) when shared code changed.
3. `product/dev/check-ui.sh sd/uiconfig/simpress/ui/notebookbar_office.ui` when the Impress `.ui` changed.
4. The builds the task needs, only through `product/dev/lo-make.sh`: `sd.build`, `cui.build`, `officecfg.build` then
   `postprocess.build`, and `vcl.build` for the preview picture.
5. The task's UITests one at a time: `product/dev/uitest.sh --app impress
   notebookbarOffice.NotebookbarOffice.<test>` (target `UITest_impress_tests2`; the target adds the whole
   `sd/qa/uitest/impress_tests2/` directory, `sd/UITest_impress_tests2.mk:10-11`, so no new gbuild target).
6. Screenshots for the b tasks, I9 and I11, through `product/dev/shot-tab.sh --app impress`, outside the repository.

## Answers and rulings (2026-10-23)

Inherited from Writer (`product/odd/tasks/writer-ribbon-tabs.md`, "Answers and rulings"), binding here:

1. **Accent** (Writer ruling 1): one per app; Impress gets PowerPoint orange (design 3.4).
2. **Splits LibreOffice lacks are dropdowns** (Writer ruling 3), **approximate mappings are kept** (ruling 4),
   **Undo stays on Home** (ruling 5).
3. **Office labels on the ribbon only** (Writer rulings 6-7, T9w): already in the generator and the VCL builder.
4. **Grey line icons** (Writer ruling 8) and **greyed disabled menu entries** (T10w).
5. **Working mode** (Writer ruling 9).

Designer rulings (task ID1; the controller can overturn them; design section 4 has the reasons):

6. PowerPoint's Record and Draw tabs are out (decisions 4-5).
7. Transitions reuses the stock Layout page; Animations and Help are new pages (decisions 6-7).
8. Transitions and Animations controls open their sidebar decks; Animation Pane is the exact toggle (decision 25).
9. Translate is a placeholder and Contact Support is real, as in Calc and Writer (decision 30).
10. Slots are `SID_BOOST` = `SID_SD_START + 900`, disabled in `ViewShellBase` (decisions 22-23).
11. The feature starts after Writer's W9 (decision 38).

Controller rulings (2026-10-23):

12. **No questions, no review prompts.** The user: "termina lo que te pedi por favor. Basta de preguntar y frenar el
    trabajo", "basta ya de pedir revisiones". RDD is off for the clone; the controller rules on every open decision
    and records it here; the gate is the writer's verification plus the parent's spot check. Push stays the user's
    decision.
13. **Branch:** `feature/impress-ribbon-tabs` starts from the tip of `feature/writer-ribbon-tabs` after Writer's
    W11, so the generator, accent and greyed-entry changes are already there and no merge is needed.
14. **Designer rulings 6-11 are accepted as written.** The approximate mappings (deck and dialog controls,
    Reset, Columns, InsertSlideController, Hide Slide) keep their UITest gates and fallbacks; the visual gate (I11)
    decides whether the deck controls feel close enough.
15. **Fit is through control sizes**, as in Calc and Writer: the generator has no collapse-priority key, so I2b and
    I9 change sizes, never add a priority mechanism.

## Progress / evidence

- 2026-10-23, ID1: the design and this plan were drafted (read-only; report
  `.superpowers/sdd/2026-10-20-writer-impress-ribbons/task-ID1-report.md`). Counts: 9 tabs built (21 on the
  ribbon), 43 sections, 171 controls (145 real, 32 of them approximate), 26 placeholder controls and 13 placeholder
  menu items on 24 slots, 20 dropdowns on 19 new menus, 70 leave-list rows. The controller accepted both, corrected
  the accent mechanism (W9a landed in d8c601d40 and already maps Impress), the fit lever (sizes, not priorities)
  and the RDD lines (off), and added rulings 12-15.

- 2026-10-23, start: Writer closed at d33ae2337 (W0a-W12, 666 unit tests OK); this branch starts there
  (ruling 13). Writer's W12 already gives every stock page plain captions in `apply_tabs`, for every app.

## Next step

I0a (delegated, opus; brief `.superpowers/sdd/2026-10-20-writer-impress-ribbons/task-I0a-brief.md`): record the six
Calc and Writer sha256 values first, then add the `impress` app to the generator and the test tooling.

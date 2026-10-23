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
| I0a | Generator and test tooling for three apps; Impress office `.ui` = stock + tab operations; registration; suppressions; unique-id test | delegated (opus: shared code, Calc and Writer byte-identical) | [x] | 987d57ed7 (generated), 57a17c72f (code) | off (ruling 12): controller spot check |
| I0b | Impress Tabbed Office mode end to end: ToolbarMode node, cui whitelist, profile (template dialog off), launcher, shot-tab, uitest.sh, UITest scaffold | delegated (opus: cui C++ and shared scripts); shot-tab and the office.sh fix inline (controller) | [x] | 880e4cd87, 085cab01e, ee1b573e9 | off (ruling 12): controller spot check |
| I1 | All 24 placeholder slots in one sd rebuild, with the registry and the slot test | delegated (opus: C++ and `.sdi`) | [x] | f7c63b9f6 | off (ruling 12): controller spot check |
| I2a | Home, part 1: Undo, Clipboard, Slides, Font, Paragraph (5 menus); layout, labels, popups, placeholder labels, unit tests, UITests | delegated (sonnet) | [x] (Columns: fallback, ruling 19) | e7d5a89ce (layout + generated), 64b7a1062 (code) | off (ruling 12): controller spot check |
| I2c | Home, part 2: Drawing (shape gallery, Arrange, Shape Effects) and Editing (6 menus) | delegated (sonnet) | [x] | 70dbfd32e, 057581424 | 741 unit tests OK; UITests pass |
| I2b | Home icons, 1920 fit (through control sizes), screenshots | delegated (sonnet), after I2c | [x] | d04c730e5 | 745 unit tests OK; fits at 1920 |
| I3a | Insert, layout and behaviour | delegated (sonnet) | [x] | 24b68da34, 2c339b20a | 774 unit tests OK; UITests pass |
| I3b | Insert icons, 1920 fit, screenshots | delegated (sonnet), after I3a | [x] | 108404dd7 | 779 unit tests OK; fits at 1920 |
| I4a | Design (moved before Transitions), layout and behaviour | delegated (sonnet) | [x] | 8a94a9d48, 1d6710d99 | 806 unit tests OK; UITests pass |
| I4b | Design icons, 1920 fit, screenshots; the theme colors box shown whole (svx) | delegated (sonnet), after I4a | [x] | d76206f30, 374cf2422, 584d6a44a | 812 unit tests OK; fits at every width |
| I4c | Disabled popup entries greyed on the gtk3 backend (toolkit; all three apps) | delegated (opus) | [x] | b4d6c4849 | 813 unit tests OK; gtk3 screenshots |
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
- I5a: remove the `pmhbLayout` `valign` operation from `impress_tabs.json` in the same change that generates the
  Layout page as Transitions (the box id disappears and `set_property` raises "object not found"; I0a report).
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
16. **Placeholder slots stay out of Tools > Customize** (I1): AccelConfig, MenuConfig and ToolBoxConfig FALSE, as
    every Calc and Writer placeholder, not the TRUE the I1 brief copied from `AddSlideSection`.
17. **The disable group runs last in `ViewShellBase::GetState`** (I1): `Implementation::GetSlotState` puts a state
    for every slot it is asked about (`ViewShellBase.cxx:1552`), which replaces an earlier disable, so design 3.3
    and decision 23 ("first") are corrected in I10. Draw's `GraphicViewShellBase` inherits `ViewShellBase`'s slot
    table, so in Draw the 24 commands answer as known and disabled, like the existing Impress-only
    `.uno:LeftPaneImpress`; nothing visible changes in Draw.
18. **Builds yield to the user's machine (2026-10-23):** the user plays games on this machine while the feature
    runs (available memory about 3.8 GB, swap in use). Every worker builds with `PARALLELISM=2` and starts a build,
    UITest or screenshot only with at least 2500 MB available, waiting otherwise.
19. **Columns falls back to Text Attributes (I2a):** decision 14's gate failed: `SDRATTR_TEXTCOLUMNS_NUMBER` has slot
    id 0 (`svx/source/svdraw/svdattr.cxx:440`), so `.uno:TextColumnsNumber` with an argument never reaches the
    shape. The Columns menu holds only `.uno:TextAttributes` ("Text Attributes..."), the three column variants are
    gone, and a UITest pins the failure so it flags if the slot ever gets a mapping. One, Two and Three Columns as
    real commands are later C++ work (a slot mapping in svx), outside this feature.
20. **The theme colors box is fixed in svx (I4b):** the stock `svx/uiconfig/ui/themeselectorpanel.ui` clips its
    swatches in every notebookbar (it requests a height of 65 for taller items). I4b changes that file only, in its own
    `fix(svx)` commit, keeping the ribbon band at its height; the fix also helps LibreOffice's stock Design tab.
21. **Greyed popup entries on gtk3 (I4c):** the I2b and I4b screenshots show ribbon dropdowns without their disabled
    entries on the gtk3 backend (the real app and shot-tab), although W9d's headless UITest passes: gtk3 native
    popups hide disabled entries unless the menu has `MenuFlags::AlwaysShowDisabledEntries`
    (`vcl/unx/gtk3/gtksalmenu.cxx:385-399`), and W9d only stopped adding `HideDisabledEntries`
    (`toolkit/source/awt/vclxmenu.cxx:518-521`). I4c (opus) sets the always-show flag in `VCLXMenu::execute` when
    `DontHideDisabledEntry` is true, proves it with gtk3 screenshots in Impress, Writer and Calc, and comes before
    I5a because it affects the finished apps too.

## Progress / evidence

- 2026-10-23, ID1: the design and this plan were drafted (read-only; report
  `.superpowers/sdd/2026-10-20-writer-impress-ribbons/task-ID1-report.md`). Counts: 9 tabs built (21 on the
  ribbon), 43 sections, 171 controls (145 real, 32 of them approximate), 26 placeholder controls and 13 placeholder
  menu items on 24 slots, 20 dropdowns on 19 new menus, 70 leave-list rows. The controller accepted both, corrected
  the accent mechanism (W9a landed in d8c601d40 and already maps Impress), the fit lever (sizes, not priorities)
  and the RDD lines (off), and added rulings 12-15.

- 2026-10-23, start: Writer closed at d33ae2337 (W0a-W12, 666 unit tests OK); this branch starts there
  (ruling 13). Writer's W12 already gives every stock page plain captions in `apply_tabs`, for every app.

- 2026-10-23, I0a (route: delegated, opus). Commits 987d57ed7 (the generated office `.ui`, 14637 lines; 639 office
  lines in `simpress.suppr`; `impress_tabs.json`) and 57a17c72f (the `impress` app in `gen_ribbon.py`, per-app
  test tooling, `sd/UIConfig_simpress.mk`, `test_impress_tabs.py` with 13 tests).
  - `impress_tabs.json` holds 21 `valign` operations, not the design's 2: W12's shared test (no stock page centres
    its section box) runs for every app, and all 19 of Impress's stock `pmhb*` boxes are centred. Design 3.1 is
    corrected in I10. I5a must drop the `pmhbLayout` operation (see the I5a check).
  - `controller_nodes(app=...)` now filters suffixed nodes both ways: each app sees only its own (Writer's or
    Impress's), Calc neither. No result changes today.
  - `placeholders.registry("impress")` names `placeholders_impress.json`, which I1 creates.
  - Evidence (report: `task-I0a-report.md`): RED `KeyError: 'impress'` plus 1 FAIL and 1 ERROR in
    `test_gen_ribbon.py`; 666 -> 679 OK (the generated commit alone 666 OK); `check-ui.sh` 0 new warnings or fatals
    (Calc and Writer output identical); `sd.build` exit 0; the six Calc and Writer sha256 values unchanged; Draw's
    files untouched; `git show --check` clean.
  - Controller check: 679 unit tests OK; the tree clean after `gen_ribbon.py --all`; no `.superpowers` file tracked.

- 2026-10-23, I0b (route: delegated, opus; the last part inline, controller). Commits:
  - 880e4cd87: Impress `TabbedOffice` (MenuPosition 9) in `ToolbarMode.xcu`; `HasTabbedOffice` lists Impress, not
    Draw; `profile.py` writes Impress's keys and `NewDoc/AutoPilot` = false (no template dialog); `office.sh impress`
    with the profile `/mnt/games/libreoffice/try-profile-impress`; `uitest.sh --app impress`
    (`UITest_impress_tests2`); the scaffold `sd/qa/uitest/impress_tests2/notebookbarOffice.py` with
    `test_tabbed_office_loads` and `test_tab_order`; the tests that used `impress` as the invalid app use `draw`.
    UITest RED: `'notebookbar_office.ui' != 'notebookbar.ui'` at `ActiveImpress`.
  - 085cab01e (controller, from the worker's patch): `shot-tab.sh --app impress`. It was outside the commit because
    `test_ui_font.py:115` also used `impress` as the unknown app; the controller switched it to `draw`. Impress's tab
    list comes from the installed `.ui` in its own order, without the contextual tabs (a label filter would hit the
    stock Layout tab when asked for Design).
  - ee1b573e9 (controller): `office.sh`'s running-instance check anchors the profile path, so a running Writer or
    Impress (`try-profile-writer`, `try-profile-impress`) no longer blocks `office.sh calc` (`try-profile`).
  - Evidence (report: `task-I0b-report.md`): 679 -> 695 -> 697 OK; `cui.build officecfg.build postprocess.build`
    exit 0; both Impress UITests and one Calc and one Writer UITest pass; the six Calc and Writer sha256 values and
    their profile and launcher outputs unchanged; screenshot `impress-ribbon-tabs/i0b/impress-light-1920-design.png`:
    File, Home, Insert, Layout, Design, Slide Show, Review, View, Extension, Tools; a blank presentation, no template
    dialog; `x0` = 217, as Writer.
  - For I10: design 3.2 should state the `.ui`-order rule of shot-tab's Impress tab list; the plan missed
    `test_ui_font.py:115` and `test_shot_tab.py:60` among the tests that used `impress` as the invalid app. The stock
    Design page's color gallery is clipped at the top (I4a rebuilds the page). Impress shows the shared preview
    picture until I11.
  - Controller check: 697 unit tests OK; the tree clean after `gen_ribbon.py --all`.

- 2026-10-23, I1 (route: delegated, opus). Commit f7c63b9f6 (7 files, 1047 lines): `SID_BOOST` =
  `SID_SD_START + 900` and `SID_BOOST_*` +0..+23 in `sd/inc/app.hrc` (27900-27923; the sd range used up to 27458);
  24 declarations in `sdraw.sdi`; the slots in `ViewShellBaseView` with `GetState` only; one disable group at the
  end of `ViewShellBase::GetState` (ruling 17); `product/tests/placeholders_impress.json` (no labels yet; the tab
  tasks add them); `test_impress_slots.py` (13 tests); the UITest `test_placeholder_slots_disabled`.
  - Evidence (report: `task-I1-report.md`): RED for the unit tests and the UITest (with the group first:
    `True is not false : HomeSection?Action:string=removeall`); 697 -> 710 OK; `sd.build` exit 0; the three Impress
    UITests pass; Draw's files and generated `sdgslots.hxx` have no Boost slots; `git show --check` clean.
  - Rulings 16-17 record the two deviations from the brief and the design.
  - Controller check: 710 unit tests OK; the tree clean after `gen_ribbon.py --all`.

- 2026-10-23, I2a (route: delegated, sonnet). Commits e7d5a89ce (`impress_home.json`, 111 lines, and the
  regenerated `.ui` and suppressions: 3 files, +1128/-1117) and 64b7a1062 (5 popups `home_*.xml`, 10 Controller.xcu
  nodes, labels in `DrawImpressCommands.xcu`, `test_impress_home_ui.py`, 10 UITests).
  - Gates: decision 13 (Reset) passes (a moved title placeholder goes back; the `?Reset` URL gets no controller; it
    passed at RED too, since the stock `.uno:AssignLayout` re-applies the layout); decision 19 passes (New Slide's
    popup has Duplicate, Layout's has Reset Slide Layout, read through the accessible "Toggle Popup" action);
    decision 14 fails: ruling 19.
  - Outside the surface, accepted: `product/tests/test_commands.py` counts all Controller.xcu nodes against
    `controller_nodes(app="writer")`; it now leaves out Impress-suffixed nodes (332 != 322 otherwise).
  - Until I2c the Home page shows five sections, so the stock Search, Find bar and Start from First Slide buttons are
    off it for now. Reset reuses the Layout icon and Convert to SmartArt has none: I2b.
  - Evidence (report: `task-I2a-report.md`): 710 -> 710 (commit 1) -> 738 OK; 13 UITests pass one at a time (two
    RED runs overlapped by mistake, the GREEN runs were single); `sd.build officecfg.build postprocess.build` exit 0;
    `check-ui.sh` 0 new warnings or fatals; the six Calc and Writer sha256 values unchanged; `git show --check` clean.
  - Controller check: 738 unit tests OK; the tree clean after `gen_ribbon.py --all`; no soffice
    left; no `.superpowers` file tracked.

- 2026-10-23, I2c (route: delegated, sonnet). Commits 70dbfd32e (`impress_home.json` Drawing and Editing, and the
  regenerated `.ui` and suppressions: 3 files, +691/-5) and 057581424 (the 6 popups, among them
  `home_shapes.xml` for `InsertShapesMenu`, which I3a reuses; Controller.xcu nodes; labels; tests: 12 files,
  +577/-25).
  - Choices, accepted: Quick Styles is a plain button (a deck opener has no dropdown controller; the design says
    "dd"); Shape Fill and Shape Outline are split buttons with their existing color controllers; the Find menu's first
    item is the find toolbar URL, so the label-known test exempts `vnd.sun.star.findbar:` URLs.
  - Commit 1 alone fails 16 tests and 1 error (the generated `.ui` needs the label nodes of commit 2); commit 2 makes
    the suite green. Accepted as in Writer.
  - The headless UITest window clips the ribbon after Font, so the shape-cell test builds each stock popup through its
    `ToolbarAsMenuController` instead of pressing the cell. Fit and icons: I2b.
  - Evidence (report: `task-I2c-report.md`): 738 -> 741 OK; the UITests pass one at a time;
    `sd.build officecfg.build postprocess.build` exit 0; `check-ui.sh` 0 new warnings or fatals; the six Calc and
    Writer sha256 values unchanged; `git show --check` clean.
  - Controller check: 741 unit tests OK; the tree clean after `gen_ribbon.py --all`; no soffice left; no
    `.superpowers` file tracked.

- 2026-10-23, I2b (route: delegated, sonnet). Commit d04c730e5 (102 files, mostly vendored Fluent SVGs; +259/-5):
  Boost icons for every Home command in both themes, `product/tests/test_impress_icons.py` (4 tests; coverage and
  the button count from the layout JSON). No fit commit: Home fits at 1920 unchanged.
  - Fit: at 1920 the last separator is at x=1767 (153 px margin, still fits at about 1880); at 1600 and 1366 Editing
    collapses first, then Drawing, behind `>>`. The ribbon height equals the stock tabs'.
  - Icon notes: Reset has its own icon; Convert to SmartArt shares `insertsmartart` through the manifest `aliases`
    key; Quick Styles has an explicit icon (no `DrawImpressCommands.xcu` change). New entries `cube`, `line`, `text`,
    `connector` and the popup sub-command names (`linearrowend`, `freeline_unfilled`, ...) also theme the stock
    drawing toolbars of every app; no existing zip member changed (sha1 of all 871 members per theme compared).
  - Evidence (report: `task-I2b-report.md`): 741 -> 745 OK; `build_theme.py build`/`install` exit 0; `sd.build`
    exit 0; `test_tabbed_office_loads` passes; `check-ui.sh` 0 new fatals; screenshots light and dark at 1920, 1600
    and 1366 plus the open Arrange menu in `assets/previews/impress-ribbon-tabs/i2b/`.
  - For I9: the default shape cells (diamond, smiley, block arrow, flowchart, callout, star) still draw Colibre's
    icons (about 6 manifest entries); the stock Drawing toolbar shows under the ribbon in Tabbed Office, which
    PowerPoint does not have; the tab underline is still green (the accent is I9's).
  - Controller check: 745 unit tests OK; the tree clean after `gen_ribbon.py --all`; no soffice left; no
    `.superpowers` file tracked; the 1920 light screenshot looked at.

- 2026-10-23, I3a (route: delegated, sonnet). Commits 24b68da34 (`impress_insert.json`, 146 lines, and the
  regenerated `.ui` and suppressions: 3 files, +1281/-941) and 2c339b20a (the `InsertZoomMenu` and
  `InsertTextBoxMenu` popups, Controller.xcu nodes, labels, `test_impress_insert_ui.py`, 9 UITests: 9 files,
  +715/-15). `InsertShapesMenu` is reused from I2c.
  - Choices, accepted: Photo Album, Link, Equation, Video, Audio and WordArt are plain buttons (no LibreOffice menu,
    decision 9); Table, Symbol and New Slide are splits. Summary Zoom is Summary Slide, enabled only once the slide
    has a title (`sd/source/ui/view/drviews7.cxx:451-471`); the UITest sets one first. Symbol's enabled state is not
    asserted (it needs text edit mode).
  - Deviations, accepted: no separate RED run of the UITests (the unit RED, 14 failing checks, stands for it); the
    suite was not run on commit 1 alone (the new test file is in commit 2).
  - Evidence (report: `task-I3a-report.md`): 745 -> 774 OK; the 9 new UITests and the load, tab-order,
    placeholder and Home visibility UITests pass; the build exit 0; `check-ui.sh` 0 new warnings or fatals; the six
    Calc and Writer sha256 values unchanged; `git show --check` clean.
  - Controller check: 774 unit tests OK; the tree clean after `gen_ribbon.py --all`; no soffice left; no
    `.superpowers` file tracked.

- 2026-10-23, I3b (route: delegated, sonnet). Commit 108404dd7: 10 new Fluent manifest entries (no custom glyphs),
  among them `insertvideo` and `insertaudio`, which Video and Audio name through explicit icons since both run
  `.uno:InsertAVMedia`; `large` added to the existing `insertshapesmenu` and `gallery` entries; the Insert class in
  `test_impress_icons.py` (RED: 58 missing icon members). No fit commit.
  - Fit: at 1920 the tab ends at x=1517 (403 px margin); at 1600 nothing collapses; at 1366 Media, then Symbols,
    collapse behind `>>`. The ribbon height equals Home's.
  - Evidence (report: `task-I3b-report.md`): 774 -> 779 OK; `test_tabbed_office_loads` passes; `check-ui.sh` 0 new
    warnings or fatals; Calc and Writer theme members byte-identical; screenshots light and dark at 1920, 1600 and
    1366 plus the open Shapes menu in `assets/previews/impress-ribbon-tabs/i3b/`.
  - Controller check: 779 unit tests OK; the tree clean after `gen_ribbon.py --all`; no soffice left; no
    `.superpowers` file tracked; the 1920 light screenshot looked at.

- 2026-10-23, I4a (route: delegated, sonnet). Commits 8a94a9d48 (`impress_design.json`, the `move` of Design
  before Layout with positions Design 3 and Layout 4 in `impress_tabs.json`, and the regenerated `.ui` and
  suppressions: 4 files, +466/-114) and 1d6710d99 (the `DesignVariantsMenu` popup, Controller.xcu nodes, labels,
  `test_impress_design_ui.py`, 10 UITests, the shot-tab fake-list test).
  - Choices, accepted: Slide Size is a plain button (the design lists no menu); its UITest reads the TargetURL and
    opens the dialog through `.uno:PageSetup`.
  - Finding: the theme colors box is clipped at the top by about 10 px, as on the stock page:
    `svx/uiconfig/ui/themeselectorpanel.ui:22-23` requests a height of 65 for taller items. Controller ruling 20:
    I4b fixes it in that file (its surface grows by that one file), in its own commit.
  - Commit 1 alone would fail the new design-test checks (the test file and nodes are in commit 2); not run alone.
  - Evidence (report: `task-I4a-report.md`): 779 -> 806 OK; the 10 new UITests, the load and tab-order UITests
    pass; the build exit 0; `check-ui.sh` 0 new warnings or fatals; the six Calc and Writer sha256 values unchanged;
    `git show --check` clean; screenshot `assets/previews/impress-ribbon-tabs/i4a/design-light-1920.png`.
  - Controller check: 806 unit tests OK; the tree clean after `gen_ribbon.py --all`; no soffice left; no
    `.superpowers` file tracked; the screenshot looked at (Design between Insert and Layout; Themes, Format Background
    and More without icons until I4b).

- 2026-10-23, I4b (route: delegated, sonnet). Commits d76206f30 (Design icons, the Design class in
  `test_impress_icons.py`), 374cf2422 (`fix(svx)`: `themeselectorpanel.ui` height-request 65 -> 80, iconview
  margin 0, item padding 0, row spacing 5; ruling 20) and 584d6a44a (icons for the Variants menu items through
  manifest `aliases`). No fit commit.
  - Fit: the tab ends at about x=765; nothing collapses at 1920, 1600 or 1366. The theme colors box shows whole and
    is about 433 px wide (was 361); the slide pane starts at y=224 on Design and on Home, so the band height holds.
  - Finding: the Variants menu screenshot shows only "Theme...", and I2b's Arrange menu also lacks its disabled
    entries: ruling 21, task I4c.
  - Evidence (report: `task-I4b-report.md`): 806 -> 812 OK (RED first for the Design icon tests); screenshots light
    and dark at 1920, 1600 and 1366 plus the open Variants menu in `assets/previews/impress-ribbon-tabs/i4b/`.
  - Controller check: 812 unit tests OK; the tree clean after `gen_ribbon.py --all`; no soffice left; no
    `.superpowers` file tracked; the Variants menu screenshot looked at.

- 2026-10-23, I4c (route: delegated, opus). Commit b4d6c4849 (2 files, +30/-2): `VCLXMenu::execute` adds
  `MenuFlags::AlwaysShowDisabledEntries` when `DontHideDisabledEntry` is true and the controller did not ask to
  hide disabled entries; a source test in `MenuDefaultsTest` pins it (RED first).
  - Evidence (report: `task-I4c-report.md`): 812 -> 813 OK; `toolkit.build` exit 0; Writer
    `test_ribbon_popups_show_disabled_entries_greyed` and Impress `test_tabbed_office_loads` pass; gtk3 screenshots
    in `assets/previews/impress-ribbon-tabs/i4c/`: before, the Variants menu shows only Theme...; after, Fonts,
    Effects and Background Styles show greyed; Impress Arrange shows its 15 disabled entries greyed; Writer's Text
    Effects menu shows its five placeholders greyed; Calc Review's Notes menu shows its disabled entries greyed.
  - For I9 (follow-ups, accepted as known): gtk3 submenus still hide disabled entries (gtk3 reads each submenu's
    own flags, `gtksalmenu.cxx:397`; the fix belongs in `framework/source/uielement/menubarmanager.cxx:612-617` and
    the popup controllers); greyed entries show a faint rounded outline from the upstream rule `menu
    menuitem:disabled` (`vcl/unx/gtk3/custom-theme.cxx:216-221`, left and right borders); a popup reused after the
    setting changes at runtime keeps its flags until it is recreated.
  - Controller check: 813 unit tests OK; the tree clean after `gen_ribbon.py --all`; no soffice left; no
    `.superpowers` file tracked; the after Variants screenshot looked at.

## Next step

I5a (delegated, sonnet; brief `task-I5a-brief.md`): the Transitions and Animations tabs. Then I5b, I6a, ... I8b; the a
briefs bind `task-Ia-common.md` from I6a on, the b briefs bind `task-Ib-common.md`.

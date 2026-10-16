# Calc ribbon tabs like Excel (Tabbed Office)

Status: implemented on branch `feature/calc-ribbon-tabs` (2026-10-16), waiting for the user's visual
review. Third slice of the "Tabbed Office" ribbon, built with the tools of the Home and Data slices
(`product/docs/calc-home-redesign.md`, `product/docs/calc-data-redesign.md`; read the Data doc first
for the placeholder and split recipes). This document is the reference for what the six new tabs
look like, how they are built, what was decided while the user was away, and what is still open.

Design sources: `product/docs/design/calc-ribbon-tabs-overview.txt` and one
`product/docs/design/calc-<tab>-tab-layout.txt` per tab. Excel reference research:
`product/docs/research/`. Feature document with every task and its evidence:
`product/odd/tasks/calc-ribbon-tabs.md`.

## 1. What the user sees

### Tab order and labels

File, Home, Insert, **Page Layout**, **Formulas**, Data, Review, View, (contextual tabs), Extension,
Tools, **Help**. LibreOffice's Layout tab is now Page Layout and its Functions tab is now Formulas,
placed before Data. Help is a new tab, last, after Tools (Excel puts "(Developer), Help" there).
Page ids do not change (`phbLayout`, `phbFunctions`). No "~" shows on the tab bar: it is the
mnemonic marker of the `.ui` labels.

Reference: Excel for Microsoft 365, Windows desktop, at full width. Every button is an Excel
button. Where LibreOffice has the feature, the button runs it. Where it does not, the button is a
**placeholder**: greyed out, tooltip "<Label> (not available yet)", no action. Placeholders are
marked **[P]** below and listed in section 8. Dropdown buttons are marked **(menu)**.

### Insert (10 sections)

| Section | Content |
|---|---|
| Tables | Pivot Table, Recommended PivotTables [P], Table |
| Illustrations | Pictures (menu: Place in Cell [P], Image...), Shapes (menu: Line, Basic Shapes, Block Arrows, Flowchart, Stars and Banners, Callout Shapes, Symbol Shapes, Connectors, each a submenu), Gallery (LibreOffice's Gallery sidebar; Excel's Icons), 3D Models [P], SmartArt [P], Screenshot [P] |
| Controls | Checkbox [P] |
| Charts | Chart (LibreOffice's chart wizard), nine chart-type buttons [P] (Column or Bar, Line or Area, Pie or Doughnut, Hierarchy, Statistic, Scatter or Bubble, Waterfall/Funnel/Stock/Surface/Radar, Combo, Maps), PivotChart [P] |
| Sparklines | Line, Column, Win/Loss (small buttons with labels; they run LibreOffice's sparkline dialog) |
| Filters | Slicer [P], Timeline [P] (small buttons with labels) |
| Links | Hyperlink |
| Comments | Comment |
| Text | Text Box, Headers and Footers, Fontwork (Excel's WordArt), Signature Line, Object |
| Symbols | Equation (Formula Object), Symbol |

### Page Layout (5 sections)

| Section | Content |
|---|---|
| Themes | Spreadsheet Theme, Theme..., Fonts [P], Effects [P] |
| Page Setup | Margins (menu: Normal, Wide, Narrow presets), Orientation (menu: Portrait, Landscape), Size (menu: 12 paper sizes and Page Style...), Print Area (menu: Set, Clear, Add, Edit), Breaks (menu: Insert Page Break with Row Break and Column Break, Remove Page Break with its submenu, Reset All), Background [P], Print Titles |
| Scale to Fit | Width [P], Height [P], Scale [P] |
| Sheet Options | Sheet Right-to-Left, View Grid Lines, Print Gridlines [P], View Headers, Print Headings [P] |
| Arrange | Bring Forward (menu), Send Backward (menu), Navigator (Excel's Selection Pane), Align (menu), Group (menu), Rotate (menu) |

### Formulas (5 sections)

| Section | Content |
|---|---|
| Function Library | Function, AutoSum (split: body inserts SUM, menu: Sum, Average, Count Numbers, Max, Min, Function...), Recently Used, Financial, Logical, Text, Date & Time, Lookup & Reference, Math & Trig, More Functions (all eight are menus listing the functions of the category; More Functions has five submenus: Statistical, Engineering, Information, Database, Array) |
| Python | Insert Python [P], Reset [P], Editor [P], Initialization [P] |
| Defined Names | Manage Names, Define Name, Use in Formula (menu), Create Names |
| Formula Auditing | Trace Precedents, Trace Dependents, Remove Arrows (menu: all, precedents, dependents), Show Formulas, Error Checking (menu: Error Checking [P], Trace Error), Evaluate Formula [P], Watch Window [P] |
| Calculation | Calculation Options (menu: Automatic, Manual, with a check mark on the current mode), Recalculate, Calculate Sheet [P] |

### Review (7 sections, all large buttons)

| Section | Content |
|---|---|
| Proofing | Spelling, Thesaurus, Properties (document properties) |
| Accessibility | Check Accessibility (menu: Check Accessibility [P], Alt Text, Table Styles, Unmerge Cells) |
| Language | Translate [P] |
| Comments | Comment, Delete Comment, Previous Comment [P], Next Comment [P], Show Comments |
| Notes | Notes (menu: Insert Comment, Edit, Previous [P], Next [P], Show/Hide, Show All, Hide All, Delete All) |
| Protect | Protect Sheet, Protect Spreadsheet Structure, Allow Edit Ranges [P], Share Spreadsheet |
| Ink | Hide Ink [P] |

### View (7 sections)

| Section | Content |
|---|---|
| Sheet View | Default, Keep, Exit, New, Options: all [P]. Excel's reduced form: one button for the combo, four icon-only buttons under it |
| Workbook Views | Normal View, Page Break, Page Layout [P], Custom Views [P] |
| Dark Mode | Dark Mode |
| Show | Navigator, Ruler [P], View Grid Lines, Formula Bar, View Headers, Column/Row Highlighting (Excel's Focus Cell) |
| Zoom | Zoom, 100%, Optimal |
| Window | New Window, Arrange All [P], Freeze Panes (menu: Freeze Panes, First Row, First Column), Split Window, Hide [P], Unhide [P], View Side by Side [P], Synchronous Scrolling [P], Reset Window Position [P], Switch Windows (menu: the open windows, the active one marked) |
| Macros | Macros (menu: Macro Manager, Record Macro, Run Macro, Edit Macros) |

### Help (2 sections, all large buttons)

| Section | Content |
|---|---|
| Help | LibreOffice Help, Get Help Online, Feedback [P], User Guides, What's New |
| Community | Get Involved, Blog [P] |

### Width behaviour (measured on screenshots, en-US labels)

Narrower windows fold sections from the right into ">>"; Excel folds group by group into dropdown
buttons instead.

| Tab | 1920 px | 1600 px | 1366 px |
|---|---|---|---|
| Insert | all 10 sections (last edge x = 1782) | Tables to Comments (x = 1098); Text and Symbols folded | same as 1600 |
| Page Layout | all 5 (Arrange ends at x = 1648) | Themes to Sheet Options (x = 1178); Arrange folded | same as 1600 |
| Formulas | all 5 (Calculation ends at x = 1773) | Function Library to Defined Names (x = 1322); Formula Auditing and Calculation folded | Function Library and Python (x = 1081) |
| Data | all 8 | first 5 (to Data Tools); Forecast, Outline and Analyze folded | first 4 (to Sort & Filter) |
| Review | all 7 (Ink ends at x = 1601) | Proofing to Protect (x = 1531); Ink folded | Proofing to Notes (x = 1016); Protect and Ink folded |
| View | all 7 (Macros ends at x = 1806) | Sheet View to Zoom (x = 1080); Window and Macros folded | same as 1600 |
| Help | both sections (ends at x = 611) | not measured; nothing folds by arithmetic | not measured; nothing folds by arithmetic |

At 1920 px the usable width stops near 1830 px, so Insert (about 50 px spare) and View (about 25 px)
are the tightest. Insert only fits because Filters and Sparklines are small-label columns. Translated
labels may push the last sections behind ">>".

Home is unchanged by this slice, except that section captions now sit on one baseline on every tab (section 6.11).

### Icons

Boost and boost_dark icons for every button (Fluent glyphs with soft fills, the same style as Home and
Data): 35 for Insert, 25 Page Layout, 28 Formulas, 15 Review, 27 View and 7 Help, in both themes.
Glyph substitutes, where Fluent 1.1.344 has no glyph at 24 px: four on Formulas (see T4b) and two on
View (see T6b).

## 2. How to try it

```
product/dev/calc.sh dark      # Tabbed Office, dark; then open any tab
product/dev/calc.sh light
product/dev/shot-tab.sh THEME TAB OUT.png [WIDTH]    # headless screenshot of one tab, see section 6.5
```

Close Calc before switching modes. After a build that changed the icon themes, run
`python3 -I product/icons/build_theme.py install --instdir instdir` so the installed icons match.
Screenshots and Excel reference images stay outside the repository.

## 3. How it is built

- One layout file per tab: `product/ui/calc_<tab>.json` (insert, pagelayout, formulas, review, view, help;
  same schema as `calc_home.json`). `product/ui/gen_ribbon.py` splices each page between its
  `product:<Tab>-begin/end` markers of `sc/uiconfig/scalc/ui/notebookbar_office.ui` and removes the
  upstream overflow menu object where there was one. The file stays "upstream + generated pages";
  `product/ui/calc_tabs.json` holds the tab operations (relabel, move, positions, add_pages, properties).
  Regenerate as shown in section 6.1.
- **Dropdowns**, **splits**, **placeholders** and **URL variants** follow the Data recipe
  (`calc-data-redesign.md`): a command with `Popup` and `ToolBox` nodes in `Controller.xcu` and a label in
  `CalcCommands.xcu`; a split body has its own slot that mirrors the original's state and execute code;
  a placeholder is a real slot whose state always disables it. New in this slice: a **family slot**
  serves several buttons through URL variants (`.uno:InsertChartType?Type:string=map`), and the placeholder
  slots live in the fork block `SID_NEW_SLOTS+380..+421` of `sc/inc/sc.hrc` (spare +422..+424;
  +424 is the last Calc slot id). The functional slots `FID_FORMULAS_AUTOSUM` (+15) and
  `FID_PAGELAYOUT_PRINT_TITLES` (+16) use two unused ids next to Data's +12..+14.
- **To implement a placeholder**: follow the recipe in the Data doc, section 3, and remove its entry from
  `product/tests/placeholders.json`.
- **Shared code touched** (not Calc-only; see section 7): `sfx2/source/sidebar/ControllerFactory.cxx` (T1b),
  `sfx2/source/control/unoctitm.cxx` (T1c, T8a), `framework/source/uielement/menubarmanager.cxx` (T3c, T8a),
  the export of `svt::PopupMenuControllerBase` in `include/svtools/popupmenucontrollerbase.hxx` (T4c), `vcl/source/bitmap/BitmapDisabledImageFilter.cxx`,
  `vcl/source/image/{Image,ImplImage}.cxx` and `vcl/inc/image.h` (T8b). Calc code: `sc/source/ui/unoobj/funcmenucontroller.cxx` (the function-category
  menus), the slots in `sc/sdi` and `sc/source/ui/view`.
- **Building**: only through `product/dev/lo-make.sh`. A task that adds a UNO component must run
  `product/dev/lo-make.sh Rdb_services` after `postprocess.build` (section 6.1, T1).

## 4. Tests and checks

Counts at the end of the slice: 279 product unit tests, 71 UITests in
`sc/qa/uitest/calc_tests/notebookbarOffice.py` (all tabs together), 7 VCL CppUnit tests for the
disabled-image filter (`CppunitTest_vcl_bitmapprocessor_test`).

- `python3 -I -m unittest discover -s product/tests -t .`: each generated page against its design file,
  "office .ui == upstream + tab operations + every generated page" (`product/tests/office.py`), labels,
  controllers and popup files of every command, the placeholder registry against `sc.hrc`, the `.sdi`
  files and `cellsh.cxx` (`test_calc_slots.py`), the split mirrors, icon coverage of every button in
  both themes (`test_icons.py`), duplicate widget ids over the whole `.ui`, the caption rule, suppr entries.
- `product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.<test>` (full names, one at a time): tab order,
  every placeholder disabled and inert and drawn disabled (62 buttons), dropdown contents built through the
  real menu controllers, AutoSum and Print Titles against their originals, the function menus, state
  listeners on URL variants.
- `product/dev/check-ui.sh sc/uiconfig/scalc/ui/notebookbar_office.ui`: gla11y and lint, no new warnings
  or fatals.
- Width, alignment and menus in a real window are checked by screenshot (`product/dev/shot-tab.sh`), not by
  a unit test.
- Final screenshots of the user gate (light and dark, 1920 px, every tab) are contact sheets outside the
  repository: `/mnt/games/libreoffice/assets/previews/calc-ribbon-tabs-light.png` and `...-dark.png`.

## 5. Decisions and rulings

Made while the user was away (2026-10-15 and 16), each worded so the user can overturn it. Source: the
feature document. Ask for a change and the matching task is reopened.

**Scope and reference**

1. **Reference**: Excel for Microsoft 365, Windows desktop, at 1920 px. The Data tab was built from the user's
   Excel 2016 screenshot; research R1 records how the 365 Data tab differs. Changing Data is a separate decision.
2. **Tab set and order**: File, Home, Insert, Page Layout, Formulas, Data, Review, View, Help. Functions becomes
   Formulas, before Data; Layout becomes Page Layout.
3. **Help goes last**, after Tools, as in Excel's "(Developer), Help".
4. **Not in this slice**: contextual tabs (Picture Format, Shape Format, Developer and others), Excel's Draw
   (ink) and Automate tabs, the File backstage.
5. **Screenshots of Microsoft's UI** are references only; they live in `/mnt/games/libreoffice/assets/excel-ref/`
   and are never committed.
6. **Supersedes** `product/odd/tasks/calc-formulas-tab.md`, which proposed editing the upstream `notebookbar.ui`.
7. **Omitted**: Insert > Tours, Add-ins (moved to Home in 2024), Forms; Review > Insights (Smart Lookup was retired
   in 2025), Changes, Performance; the Automate tab; anything that needs a Microsoft cloud (Power BI, Stock Images,
   Online Pictures, Signature Services, Data Type Icons).
8. **Kept as placeholders** when LibreOffice lacks the feature: Insert > Checkbox, Formulas > Python (four
   buttons), Review > Translate, View > Sheet View.
9. **Sheet Right-to-Left, Dark Mode** (existing LibreOffice features) are kept; **Translate** is a placeholder.

**Slots and structure**

10. **Family slots**: one slot serves several placeholder buttons through URL variants (53 ids would be needed
    otherwise; the Calc range ends at +424).
11. **Functional slots +15 and +16** go in the upstream gap next to Data's +12..+14 (upstream appends at the top
    and rarely refills old holes).
12. **Print Titles** is an alias slot that mirrors `SID_OPENDLG_EDIT_PRINTAREA` (same Execute and GetState), declared in the `Tables` interface of
    `tabvwsh.sdi` and disabled in drawing modes by its own `GetState`, because the files that disable the
    original were outside that task's edit surface.
13. **Formulas function menus**: static menus shipped first (T4a); the C++ category popup controller replaced
    them (T4c).
14. **AutoSum split** body mirrors `SID_AUTO_SUM`; nothing invalidates the original, so the mirror has no
    invalidation either.
15. **Python buttons never execute**, and the AutoSum body ignores an undeclared argument (R3).

**Content calls**

16. **Comments and Notes both drive LibreOffice's single comment type.** The Comments group has Comment,
    Delete, Previous, Next, Show Comments; the Notes menu holds the note-style actions; Convert to Comments
    is left out.
17. **Gallery** is Excel's Icons. **PivotTable** is a plain button (no menu).
18. **View > Sheet View** is built as Excel's reduced form (one "Default" button plus four icon-only buttons),
    as placeholders on one family slot (+421). It is the first group of Excel's View tab.
19. **Review loses LibreOffice-only buttons**: Automatic Spell Checking, Hyphenation, Track Changes, Compare,
    Merge Document and Redact have no Review button; each stays in the menu bar (a test asserts it).
20. **View loses LibreOffice-only buttons**: Entire Page, Page Width, Full Screen, Value Highlighting, Hidden
    Row/Column Indicator, Manage Styles, Sidebar and Status Bar stay in the menu bar. Images and Charts
    (`.uno:ShowGraphics`) was only in the removed View menu and is now reachable from Tools > Options only.
21. **Calculation Options** is Excel's Automatic/Manual with radio marks (T3c), not a single toggle.
22. **Orientation shows no check mark**; `docsh4.cxx` is left alone because the sidebar shares that state (T3c).
23. **Blog** (not "Microsoft Blog") and **Feedback** are the Help placeholders; the label must not carry
    Microsoft's product name.
24. **Icons**: a Fluent glyph with the closest meaning where Fluent has none at 24 px (six cases, listed in
    T4b and T6b). Menu-only items (Portrait, paper sizes, margin presets) have no icon.
25. **Popup entries shown disabled** in Excel are hidden here (LibreOffice default). Reversing this is T10
    (section 7).

**Process**

26. **RDD**: a due native review is recorded as "consent pending" per task and offered when the user returns;
    no review was run while the user was away.
27. **Changes to shared code were made where the root cause was** (T1b, T1c, T3c, T4c, T8a, T8b), not worked
    around in Calc. Each has a regression test. They are candidates for upstream (section 7).
28. **Delivery strategy** is ask-on-risk: no product remote exists yet, and publishing waits for the user's answer.

## 6. Reference by task

The sections below keep the per-task notes (what was built, the spikes, the measurements) in the order the
work was done: T1 groundwork, T2 Insert, T3 Page Layout, T1b and T1c bugfixes, T4 Formulas, T5 Review, T6 View,
T7 Help, T8a polish, T8b dark disabled icons. T-numbers refer to the feature document.

### 6.1 Tab order and labels (T1)

Visible tabs: File, Home, Insert, **Page Layout**, **Formulas**, Data, Review, View, (contextual tabs),
Extension, Tools, **Help**. Page ids do not change (`phbLayout`, `phbFunctions`).

The edits are data, not hand edits: `product/ui/calc_tabs.json` is applied by
`product/ui/gen_ribbon.py` (`apply_tabs`) to the upstream `notebookbar.ui`, before the generated
pages are spliced in. Operations: `relabel` (id, from, to; refuses an unexpected old text),
`move` (a page and its tab label in front of another page), `positions` (packing positions) and
`add_pages` (a new, empty generated page with its Help-style `product:<Tab>-begin/end` markers
and a tab label). Each operation can be applied twice, so re-running is safe.

The tests rebuild the office `.ui` as upstream + tab operations + every generated page
(`product/tests/office.py`) and compare it with the committed file.

```
python3 -I product/ui/gen_ribbon.py --layout product/ui/calc_home.json --tabs product/ui/calc_tabs.json \
    --ui sc/uiconfig/scalc/ui/notebookbar_office.ui --suppr solenv/sanitizers/ui/modules/scalc.suppr
```

The Help page holds one empty `sfxlo-PriorityMergedHBox` (`pmhbHelp`) until T7 gives it a layout
(`calc_help.json`, `id_prefix` Help, page `phbHelp`).

### 6.2 Placeholder slots (T1)

All placeholder slots of the slice exist already: `SID_NEW_SLOTS+380..+421` (Data +380..+388,
the other tabs +389..+420, View > Sheet View +421). Spare: +422..+424; +424 is the last Calc slot
id. Each slot follows the Data recipe: `sc/inc/sc.hrc` define, `scalc.sdi` entry (ReadOnlyDoc
FALSE; Menu, ToolBox and Accel config FALSE), `cellsh.sdi` StateMethod without ExecMethod, and a
case in the always-`DisableItem` list of `cellsh.cxx`. Labels and tooltips come with the tab tasks.

A **family slot** serves several buttons through URL variants, for example
`.uno:InsertChartType?Type:string=map`. The slot is disabled for every variant, and sfx2 ignores an
argument the slot does not declare.

### 6.3 Test tooling (T1)

- `product/tests/placeholders.json` is the one registry: slot, offset, base command, optional URL
  variants (`Arg:type=value`) and, once a button is on a page, its label. `placeholders.py` loads it;
  the UITests read the same file. Implementing a placeholder removes its entry.
- `gen_ribbon.item_url(item)` is the full command URL of a layout item (its `action`, else
  `.uno:<cmd>`); `item_command(item)` is the base command. Slot checks use the base command, label
  and icon checks the full URL.
- `test_calc_slots.py` proves, for every registered slot: defined in the fork block of `sc.hrc`,
  scalc.sdi and cellsh.sdi entries, in the always-disabled list, no execute path, no other source
  mentions it; and that the slot ids have no gaps or duplicates.
- UITests (`sc/qa/uitest/calc_tests/notebookbarOffice.py`): tab order (each position selected
  and its page checked visible; tab texts are not exposed to UITests, so the names are checked
  only by the unit tests against the .ui), every placeholder URL disabled and inert, one family
  variant URL.
- **Building**: a task that adds a UNO component (a `.component` entry) must run `product/dev/lo-make.sh Rdb_services`
  after `postprocess.build`: a module build of postprocess has no component list and leaves `services.rdb` as it
  was, so the new implementation cannot be created (T4c). `product/dev/uitest.sh` goes through the `UITest_calc_tests`
  target, which first rebuilds whatever changed, so a RED UITest run already uses the new sources.

### 6.4 Insert tab (T2a)

`product/ui/calc_insert.json` (page `phbInsert`, prefix `Insert`) replaces the upstream Insert page
between the generated `product:Insert-begin/end` markers and removes the `Menu Insert` overflow menu.
Ten sections in Excel's order: Tables, Illustrations, Controls, Charts, Sparklines, Filters, Links,
Comments, Text, Symbols (verbatim spec: `product/docs/design/calc-insert-tab-layout.txt`).

- **Dropdowns** `.uno:InsertPicturesMenu` and `.uno:InsertShapesMenu`: config only (label, a
  `ResourceMenuController` Popup node, a `GenericPopupToolbarController` ToolBox node, and
  `popupmenu/insert_pictures.xml` / `insert_shapes.xml` registered in `UIConfig_scalc.mk`). They have
  no slot, so they cannot be dispatched; the UITests build their popup through the menu controller.
- **URL variants** (`.uno:InsertSparkline?Type:string=line|column|stacked`, the nine
  `.uno:InsertChartType?Type:string=...` placeholders): one CalcCommands.xcu node per full URL, "&"
  escaped; the layout item has a short `cmd` id (`SparklineLine`, `ChartMap`, ...) and the URL in
  `action`. Placeholder tooltips read "<Label> (not available yet)".
- **Registry**: every Insert placeholder entry in `product/tests/placeholders.json` now carries its
  `label` (family slot: `variant_labels`, one per variant); `placeholders.labels_by_url()` flattens them.
- **Icons (T2b)**: 35 boost/boost_dark manifest entries, one per Insert control (Fluent glyphs, soft fills,
  same style as Home and Data): `datadatapilotrun`, `insertrecommendedpivottables`, `insertcalctable`,
  `insertpicturesmenu`, `insertshapesmenu`, `gallery`, `insert3dmodels`, `insertsmartart`,
  `insertscreenshot`, `insertcellcheckbox`, `insertobjectchart`, `insertpivotchart`, `insertslicer`,
  `inserttimeline`, `hyperlinkdialog`, `insertannotation`, `drawtext`, `editheaderandfooter`,
  `fontworkgalleryfloater`, `insertsignatureline`, `insertobject`, `insertobjectstarmath`,
  `charmapcontrol`, plus the URL variants `insertcharttype_<type>` (nine) and `insertsparkline_<type>`
  (three). Commands resolve their icon by name; each URL variant has an explicit `icon` key in
  `calc_insert.json` (`cmd/sc_<name>.png` for small, `cmd/32/<name>.png` for large buttons), which avoids
  the escaped `%3f` file names. Fluent has no 24 px `cube_add`, so 3D Models uses `cube_multiple`.
  Every Insert command with no `icon` key already had the image flag (`Properties` = 1), so the xcu is
  unchanged. `test_icons.py` checks every Insert button (RED before the manifest entries, 182 missing
  files) and the variant icon names and sizes.
- **Fit at 1920 px (measured on screenshots, Spanish-free English labels)**: the design's base layout
  put the Symbols section behind ">>" (Text ended at x = 1715, Symbols needs about 173 px, the usable
  width stops near 1830). The fallback ladder F1 (Filters) and F2 (Sparklines) as one column of small
  labelled buttons saves about 109 px: all ten sections are visible, the last one ends at x = 1782,
  no ">>". At 1600 and 1366 px (dark) Tables, Illustrations, Controls, Charts, Sparklines, Filters,
  Links and Comments stay visible (last edge x = 1098); Text and Symbols fold behind ">>".
- **Tab labels**: no literal "~" shows; the tab bar reads File, Home, Insert, Page Layout, Formulas,
  Data, Review, View, Extension, Tools, Help (the "~" in the .ui labels is the mnemonic marker).
  `calc_tabs.json` needed no change.
- **R6 in a real window**: the Shapes arrow opens a popup with Line, Basic Shapes, Block Arrows,
  Flowchart, Stars and Banners, Callout Shapes, Symbol Shapes, Connectors, each with a submenu arrow.
  Hovering Basic Shapes opens the nested submenu (Rectangle ... Sinusoid, 30 entries in five groups
  separated by lines). The entries show an empty check box and no shape glyph. That settles R6 for
  nested submenus opening from a ribbon dropdown; whether a click on an entry draws the shape was
  not exercised in the window.

Risks: R3 (`InsertSparkline?Type:string=...` stays enabled and opens the Sparkline dialog; sfx2 ignores
the undeclared argument) and R12 (no duplicate widget id in the whole office `.ui`) are proven by
UITests in `notebookbarOffice.py`. R6 is only half proven by those: they build the Shapes popup
through the menu controller, which shows its items exist, not that a real window opens nested
submenus from the ribbon button. The real-window check above (T2b) is what shows they open.

### 6.5 Screenshot tool (`product/dev/shot-tab.sh`)

```
product/dev/shot-tab.sh THEME TAB OUT.png [WIDTH]     # light|dark, e.g. dark Insert /tmp/x.png 1600
```

Starts a private headless sway (`WLR_BACKENDS=headless`, one output of 1920x1080, 1600x900 or
1366x768, its own Wayland and IPC sockets), the dev build in the dev profile with calc.sh's light or
dark settings, clicks the tab and grabs the output with grim. The headless seat has no input device,
so a small embedded Wayland client creates a `zwlr_virtual_pointer_v1` and clicks through a FIFO.
The tab label is found by its ink on the tab bar and its position in the tab order (no OCR: this
machine has no tesseract language data); `TAB` `-` keeps the tab Calc opens with. Only its own PIDs
are killed, the whole run is under `timeout` (180 s), and it refuses to start while the dev profile is
in use. `SHOT_AFTER='echo "click X Y" > "$SHOT_PTR"; sleep 2'` runs extra pointer commands (`move`,
`click`, `press`, `release`, `wait`) before the capture, which is how the Shapes popup was captured;
`SHOT_KEEP=1` leaves sway running. Screenshots belong outside the repository.

### 6.6 Page Layout tab (T3a)

`product/ui/calc_pagelayout.json` (page `phbLayout`, prefix `PageLayout`) replaces the upstream Layout page
and removes `Menu Page`. Five sections in Excel's order: Themes, Page Setup, Scale to Fit, Sheet Options,
Arrange (verbatim spec: `product/docs/design/calc-pagelayout-tab-layout.txt`). Icons, the 1920 px fit and
screenshots are T3b.

- **Ten dropdowns** (`.uno:PageLayout{Margins,Orientation,Size,PrintArea,Breaks,BringForward,SendBackward,
  Align,Group,Rotate}Menu`): config only, as on Data (label, `ResourceMenuController` + `GenericPopupToolbarController`
  nodes, `popupmenu/pagelayout_*.xml` in `UIConfig_scalc.mk`). The Breaks popup reuses the menu bar's
  `.uno:InsertBreakMenu` / `.uno:DelBreakMenu` submenus; R6 is now proven for them by a UITest.
- **URL variants in menus** (config only, label nodes in `CalcCommands.xcu`): `Orientation?isLandscape:bool=`
  (2), `CalcPageSize?PaperFormat:short=` (12), `CalcPageMargin?Page.LeftMargin:long=..` (3 presets).
- **Placeholders**: Fonts, Effects (+399), Background (+400), Width, Height, Scale (+401), Print Gridlines,
  Print Headings (+402) have labels, "(not available yet)" tooltips and registry labels
  (`variant_labels` in `placeholders.json`). Variant buttons carry the icon key `cmd/sc_<base>_<value>.png`.
- **Print Titles alias** `.uno:PageLayoutPrintTitles` = `FID_PAGELAYOUT_PRINT_TITLES` = `SID_NEW_SLOTS+16`
  (was unused). Mirrors `SID_OPENDLG_EDIT_PRINTAREA`: same `Execute`/`GetState` (`tabvwsh3.cxx`, `tabvwsha.cxx`),
  ReadOnlyDoc FALSE. The original is declared in `TableSelection` (docsh.sdi) and disabled in drawing modes by
  drawsh.sdi/drtxtob.sdi; those files were outside T3a's edit surface, so the alias is declared in the sibling
  interface `Tables` of the same shell (`tabvwsh.sdi`) and its `GetState` disables it when `bActiveDrawSh` or
  `bActiveDrawTextSh` is set (same effect, one UITest compares it with the original). Nothing invalidates the
  original (checked with rg), so there is no invalidation mirror; `PrintTitlesAliasTest` scans `sc/source` and
  fails if one appears without its mirror.
- **Spikes**
  - R4 margin presets: they work through URL arguments, but the design's member names were wrong. The
    `SvxULSpaceItem` members are `TopMargin` / `BottomMargin` (svxitems.sdi), not `UpperMargin` / `LowerMargin`.
    The three presets stay (no slot spent); values are 1/100 mm and the page style reads them back unchanged
    (UITest).
  - R8: `.uno:Orientation` is never a ribbon item; unit test over every page layout and the office `.ui`.
  - R9: the Orientation menu items (two variants of one boolean state) are not both checked (UITest, the
    popup is built by the real menu controller). No check marks are part of the design.
- Menu item texts of an awt popup built by the controller are empty until the menu is shown; the UITests resolve
  labels through `theUICommandDescription` instead.

#### Page Layout icons and fit (T3b)

- **Icons**: 25 boost/boost_dark manifest entries, one per control (Fluent glyphs, soft fills, same style as
  Home, Data and Insert): `choosedesign` (paint_brush), `themedialog` (color), `pagelayoutthemepart_{fonts,effects}`
  (text_font, text_effects), `pagelayout{margins,orientation,size,printarea,breaks}menu` (document_margins,
  orientation, document_one_page, print, document_page_break), `pagelayoutbackground` (image),
  `pagelayoutprinttitles` (table_bottom_row), `pagelayoutscaletofit_{width,height,scale}`
  (arrow_autofit_width, arrow_autofit_height, scale_fit), `sheetrighttoleft` (text_direction_horizontal_right),
  `togglesheetgrid` (grid), `viewrowcolumnheaders` (table_simple), `pagelayoutprintoption_{gridlines,headings}`
  (print, print_add), `pagelayout{bringforward,sendbackward,align,group,rotate}menu` (position_forward,
  position_backward, align_left, group, arrow_rotate_clockwise) and `navigator` (panel_left). Menu-only
  variants (Portrait, paper sizes, margin presets) have no icon, as designed. The variant buttons use the
  json `icon` key (`cmd/sc_pagelayoutscaletofit_width.png`, ...). The xcu needed no change: the image flag
  was already on every command without an `icon` key (existing test). `test_icons.py` now covers every Page
  Layout button and the variant icon names (RED before: 116 missing files).
- **Fit at 1920 px (measured on screenshots)**: all five sections are visible with no ">>" and no fallback
  was needed. Themes ends at x = 214, Page Setup at 737, Scale to Fit at 817, Sheet Options at 1178, Arrange
  at 1648 (usable width stops near 1830, so about 180 px spare, as the design estimated). At 1600 and 1366 px
  (dark) Themes, Page Setup, Scale to Fit and Sheet Options stay visible (last edge x = 1178); Arrange folds
  behind ">>".
- **Real-window menu check**: the Size dropdown lists the twelve paper sizes plus a separator and "Page
  Style...". The Breaks dropdown, opened with the cell cursor below row 1, shows only "Insert Page
  Break" and its submenu (Row Break, Column Break). With the cursor on A1 the popup reads "[No selection
  possible]": the popup hides disabled entries, and in a fresh sheet every Breaks entry is disabled (row
  break at row 1, no breaks to delete). Excel would show them greyed. Known behavior of this popup, not fixed.
- **Placeholder look**: of a placeholder family only the first variant (Fonts, Width, Print Gridlines) was drawn
  greyed; the others (Effects, Height, Scale, Print Headings) were drawn like enabled buttons although their
  slot is disabled (same on Insert's chart placeholders). Not caused by icons; fixed in T1b (below).

#### Placeholder buttons drawn disabled (T1b)

- **Cause** (sfx2, so upstream has it too): `ControllerFactory::CreateToolBoxController` (the VCL `ToolBox` path of
  notebookbar and sidebar toolboxes) called `EnableItem` after the controller's `update()`, which overwrote the
  disabled state the dispatch had just reported. A button only recovered when the bindings later pushed a state:
  the first push of a new slot cache, or a change. That push reaches only listeners on the URL that first bound
  the slot's shared dispatch (`SfxDispatchController_Impl::StateChanged` sends to `aDispatchURL.Main` and
  `.Complete`), so the other URL variants of a family never got it. A ribbon built again in the same window
  (Office, Compact, Office) gets no first push: a probe showed all 34 placeholders drawn enabled, and the item
  dumps of that case showed, besides the 12 variants, only Undo, Redo and Paste flipped in Calc (in Writer's Tabbed
  ribbon: Cut, Copy, Paste, Decrease spacing, three Borders, four table insert and three table align items).
- **Fix**: the forced `EnableItem` now runs only for an item that is disabled after `update()` and whose command
  has no dispatch (asked as `ToolboxController::bindListener` asks, alias included) or is a master command
  (`.uno:X.y`, e.g. `.uno:BasicShapes.rectangle`), whose dispatch is not bound to a state cache and pushes no later
  state. That keeps dropdowns with no slot (`.uno:InsertPicturesMenu`, `.uno:PageLayout*Menu`, upstream popup
  commands) enabled, which `PopupMenuToolbarController::statusChanged` would otherwise disable for lack of a
  dispatch, and master commands as they were.
- **Tests**: `test_every_placeholder_button_is_drawn_disabled` reads the toolbox items' own `Enabled` state
  (`toolboxitem-N` of each `bx<Prefix><Box>`), not a status listener, for all 34 placeholder buttons on the Data,
  Insert and Page Layout pages; it failed before the fix with 12 buttons drawn enabled.
  `test_placeholder_buttons_stay_disabled_when_the_ribbon_is_built_again` does the same check again after a rebuild.
- **Not fixed here** (fixed in T1c, below): a URL argument variant (`.uno:X?A:t=v`) did not hear later state
  changes of its slot when another URL bound the slot first (probe: a listener on
  `.uno:DataUngroup?Probe:string=x` heard `[False]` while one on `.uno:DataUngroup` heard
  `[False, True, False]`). With the T1b fix alone such a variant that is disabled when its button is built stays
  greyed until the ribbon is built again, where before it stayed enabled. Placeholders never change state, so
  they are not affected; real variant buttons (the Sparkline types) are.

#### Argument-variant URLs hear later state changes (T1c)

- **Cause** (sfx2, upstream too): `SfxBindings::GetDispatch` keeps one `SfxOfficeDispatch` per slot, made for the
  URL that asked first, and every URL of that command shares it (`.uno:InsertSparkline`, `...?Type:string=line`,
  `...=column`, `...=stacked`). Each listener is registered under its own URL, but
  `SfxDispatchController_Impl::StateChanged` sent a pushed state only to the listeners under the first URL's
  `Main` and `Complete`, and always with the first URL as `FeatureURL`. So in the Office ribbon (Line binds the
  slot) Column and Win/Loss only ever got their first state, and a listener on the plain `.uno:InsertSparkline`
  got events addressed to `...?Type:string=line`, which controllers that compare `FeatureURL.Complete` with
  their own command ignore.
- **Fix** (`sfx2/source/control/unoctitm.cxx`, `StateChanged`): the first URL's listeners get the same event as
  before; listeners on any other URL with the same `Main` (the same command, other arguments) get the same state
  with `FeatureURL` set to the URL they registered. Other URLs, and master commands (`.uno:X.y`, their own
  unbound dispatch), are untouched. The LibreOfficeKit state callback (`InterceptLOKStateChangeEvent`) is called
  once per change with the first URL's event, as before.
- **Effect seen** (item dumps, before/after): nothing changes in a fresh Calc Office, Writer Tabbed, Writer Compact
  or Impress `notebookbar_groupedbar_full` window, nor in Writer Compact with a read-only document. After Edit
  Document, the seven `.uno:StyleApply?...` buttons of Writer Compact (Default Paragraph, Heading 1-4, Emphasis,
  Strong Emphasis), which stayed greyed before, are enabled like in a fresh window.
- **Tests**: `test_argument_variant_listener_hears_later_state_changes` (Default UI, plain URL binds first) and
  `test_main_url_listener_hears_its_own_url_when_a_variant_bound_the_slot` (Office UI, Line binds first) keep a
  listener on `.uno:InsertSparkline` and one on `...?Type:string=column`, select a shape (no cell shell: the slot
  is disabled) and a cell again; each listener must hear exactly `[False, True]`, every event with its own URL.
  `test_sparkline_buttons_follow_their_slot_state` reads the three Sparkline buttons' drawn `Enabled` state through
  the same steps. Before the fix: Column was never told; Column and Win/Loss stayed drawn enabled with a shape
  selected; the plain URL's listener got `...?Type:string=line` as `FeatureURL`.
- **Not covered**: a probe saw no push at all, even on the plain URL's listener, after protecting the sheet
  through the API (`XProtectable.protect`, also followed by a cell selection) or after a multi-range selection:
  Calc does not invalidate `SID_INSERT_SPARKLINE` for them, so the button keeps its old state there (an sc
  matter, not this defect). The tests therefore use the shape selection, which changes the shell.

### 6.7 Formulas tab (T4a)

`product/ui/calc_formulas.json` (page `phbFunctions`, prefix `Formulas`) replaces the upstream Functions page
children between generated `product:Formulas-begin/end` markers. That page had no overflow menu object, so
`remove_objects` is empty. Five sections in Excel's order: Function Library, Python, Defined Names, Formula
Auditing, Calculation (verbatim spec: `product/docs/design/calc-formulas-tab-layout.txt`). Icons, the 1920 px
fit and screenshots are T4b; the eight function-category menus are T4c (below).

- **Category menus**: `.uno:Formulas{RecentlyUsed,Financial,Logical,Text,DateTime,Lookup,Math,MoreFunctions}Menu`
  are dropdowns without a slot (Popup + ToolBox nodes in `Controller.xcu`). T4a gave them static popups ("Function..."
  and "Function List"); T4c replaced those by one C++ controller that lists the functions of each category.
- **Other dropdowns**: Use in Formula (Paste Names), Remove Arrows (all traces, precedents, dependents), Error
  Checking (placeholder item "Error Checking" `FID_FORMULAS_ERROR_CHECKING`, then Trace Error), Calculation Options.
- **AutoSum split**: `.uno:FormulasAutoSum` = `FID_FORMULAS_AUTOSUM` = `SID_NEW_SLOTS+15` (was unused). The body
  shares `ExecuteEdit` and the `case` of `SID_AUTO_SUM` (`cellsh1.cxx`) and sits in the same sdi interface
  (`cellsh.sdi`, `CellSelection`). `SID_AUTO_SUM` has no state method and no `Invalidate()` call anywhere, so the
  mirror has none of either: the dispatcher alone decides its state from the shells that declare the slot, and both
  slots are declared only by `ScCellShell`. The arrow opens `.uno:FormulasAutoSumMenu` (Sum, Average, Count
  Numbers, Max, Min as `.uno:AutoSum` variants, then "Function..."), wired like Home's Merge & Center.
  `AutoSumSplitTest` fails if any source mentions the original in a `case` or `Invalidate` call without the body.
- **Placeholders**: Insert Python, Reset, Editor, Initialization (family `FID_FORMULAS_PYTHON`, +403), Evaluate
  Formula (+405), Watch Window (+406), Calculate Sheet (+407) are ribbon buttons; Error Checking (+404) is a menu
  item. Labels, "(not available yet)" tooltips and registry labels (`variant_labels` for Python) as on Page Layout.
- `.uno:CreateNames` had no image flag (`Properties` = 1), so no icon could ever show; added.
- **Spikes**
  - **R9 (settled)**: `.uno:AutomaticCalculation?AutomaticCalculation:bool=true|false` as "Automatic"/"Manual"
    both showed a check mark in automatic mode (T4a had fallen back to one AutoCalculate toggle). Cause: every
    listener of the slot, whatever its URL, is told the slot's boolean (true = automatic), and
    `MenuBarManager::statusChanged` (`framework/source/uielement/menubarmanager.cxx`) checked an item with that
    boolean. T3c rule (`getSingleBoolArgument`): an item whose command URL has exactly one argument, of type bool, is
    checked only when the slot's boolean state equals that argument; every other URL behaves as before. The slot honours
    the argument (`docsh4.cxx` FID_AUTO_CALC), so picking the current mode leaves it unchanged. Calculation Options is
    Excel's Automatic/Manual again with radio-like marks (screenshots: only the current mode checked); the
    `.uno:AutomaticCalculation` command keeps its "AutoCalculate" label. The popup an awt test builds has no
    `MenuBarManager` until a real menu activation, so a UITest cannot read the marks; they are verified by screenshot.
  - **Orientation shows no check mark (accepted)**: its slot state is not a boolean. `ScDocShell::GetState` for
    `SID_ATTR_PAGE_ORIENTATION` puts the page style's `SvxPageItem`, which the sidebar page panel and its Orientation
    control also expect (the case is shared with the margin and size slots), so the state item type is left alone.
    Listeners get no boolean, so the rule marks neither Portrait nor Landscape, in portrait or landscape: not
    misleading, only unmarked.
  - **R3 (settled)**: the only variants with an argument the slot does not declare would be the AutoSum body itself
    (`FormulasAutoSum` declares none). `.uno:FormulasAutoSum?Function:string=average` stays enabled and runs the plain
    sum: sfx2 ignores the undeclared argument. The other variants (`AutoSum?Function`, `AutomaticCalculation`) use
    declared arguments, and the Python family never executes.
  - **VCL split arrow**: a disabled toolbox item is dead in its arrow too (`ToolBox` mouse handling skips items
    with `mbEnabled` false, and `PopupMenuToolbarController::statusChanged` follows the body's state). The body is
    disabled exactly when the cell shell is absent (a drawing object, graphic, OLE or chart is selected); then every
    AutoSum menu item, including "Function...", is disabled as well (UITest), so no usable menu is hidden behind a
    disabled body. In cell edit mode both stay enabled like the original.
- **Tests**: `test_calc_formulas_ui.py` (layout vs design, controllers, popup files, labels, image flags, suppr,
  registry, reproducibility, the AutoSum mirror) and 13 UITests (`test_formulas_*`): page groups and toolboxes, every
  Formulas placeholder disabled and inert, AutoSum body inserting the same formula as `.uno:AutoSum` (and the four
  variants), state equal to the original for cell, range, shape, image, OLE and edit mode, a status listener on each
  hearing the same changes, the ribbon button drawn like its state, one real command per dropdown enabled, every
  popup listing its items, the Calculation Options toggle. The placeholder-button UITest now covers 41 buttons.

#### Formulas icons and fit (T4b)

- **Icons**: 27 new boost/boost_dark manifest entries (Fluent glyphs, soft fills, same style as Home, Data, Insert and
  Page Layout), one per control, plus the alias `formulasautosum` on the existing `autosum` entry. Large: `functiondialog`
  (math_formula), `formulasrecentlyusedmenu` (history), `formulasfinancialmenu` (money), `formulaslogicalmenu`
  (question_circle), `formulastextmenu` (text_t), `formulasdatetimemenu` (calendar_clock), `formulaslookupmenu`
  (book_search), `formulasmathmenu` (math_symbols), `formulasmorefunctionsmenu` (more_horizontal),
  `formulaspython_insert` (code_block), `definename` (tag_multiple, Manage Names), `formulaswatchwindow` (glasses),
  `formulascalcoptionsmenu` (calculator). Small: `formulaspython_{reset,editor,init}` (arrow_reset, code_block_edit,
  settings), `addname` (tag_add), `formulasuseinformulamenu` (tag), `createnames` (tag_edit), `showprecedents`
  (arrow_import), `showdependents` (arrow_export), `formulasremovearrowsmenu` (dismiss), `toggleformula`
  (math_format_linear), `formulaserrorcheckingmenu` (warning), `formulasevaluateformula` (math_format_professional),
  `calculate` (calculator_arrow_clockwise), `formulascalculatesheet` (calculator_multiple). Four glyphs differ from
  the design because Fluent 1.1.344 lacks them at 24 px or at all: `code_py` -> `code_block`, `code_text_edit` ->
  `code_block_edit`, `arrow_enter` -> `arrow_import`, `table_calculator` -> `calculator_multiple`.
- The four Python buttons are URL variants: json `icon` keys `cmd/32/formulaspython_insert.png` (large) and
  `cmd/sc_formulaspython_{reset,editor,init}.png`. T4a had given the large button a `cmd/sc_` key; it is `cmd/32/` now
  (the icon test checks the size prefix against the button size). Regenerating `notebookbar_office.ui` changes only
  that line. The image flag was already on every Formulas command (T4a, `CreateNames` included), so the xcu is unchanged.
- `test_icons.py`: every Formulas button resolves its icon in both themes (RED before: 130 missing files), and the
  URL-variant icon names and sizes.
- **Fit at 1920 px (measured on screenshots)**: all five sections are visible with no ">>" and no fallback step was
  needed (the design's two icon-only columns are already in the layout). Function Library ends at x = 882, Python 1081,
  Defined Names 1322, Formula Auditing 1602, Calculation 1773 (usable width stops near 1830). At 1600 px (dark)
  Function Library, Python and Defined Names stay visible (last edge x = 1322); Formula Auditing and Calculation fold
  behind ">>". At 1366 px Function Library and Python stay (last edge x = 1081); Defined Names, Formula Auditing and
  Calculation fold.
- **Real-window menus**: the AutoSum arrow lists Sum, Average, Count Numbers, Max, Min, a separator and Function...;
  Calculation Options lists Automatic (checked) and Manual (unchecked) with check boxes.

#### Function-category menus (T4c)

- **One controller**: `sc/source/ui/unoobj/funcmenucontroller.cxx`, a `svt::PopupMenuControllerBase`
  (implementation `com.sun.star.comp.Calc.FunctionMenuController`, constructor
  `Calc_FunctionMenuController_get_implementation` in `sc/util/sc.component`, built into `libsclo`). The eight Popup
  nodes of `Controller.xcu` name it and carry no `Value`; the ToolBox nodes (`GenericPopupToolbarController`) are
  unchanged. The eight static `popupmenu/formulas_*.xml` files and their `UIConfig_scalc.mk` lines are gone (nothing
  else used them).
- **Category from the command** (`CATEGORY_MENUS`, ids of `sc/inc/scfuncs.hxx`): Financial 3, Logical 5, Text 10,
  Date & Time 2, Lookup & Reference = Spreadsheet 9, Math & Trig = Mathematical 6; Recently Used reads the LRU list of
  `ScAppOptions` (`ScFunctionMgr::fillLastRecentlyUsedFunctions`). More Functions has five submenus whose items carry
  the commands `.uno:Formulas{Statistical,Engineering,Information,Database,Array}Menu` (labels in `CalcCommands.xcu`;
  Engineering is LibreOffice's Add-in category 11), categories 8, 11, 4, 1, 7. These five commands have no slot and no
  controller node: they only name a category and a label.
- **Built when the menu opens**: `PopupMenuToolbarController` calls `updatePopupMenu()` on every open, and the controller
  fills the menu then from `ScGlobal::GetStarCalcFunctionMgr()` (sorted by name, upper-case names in the language of
  the formulas, hidden functions left out as in the Function Wizard). `VCLXMenu::clear()` keeps every submenu it was
  given, so More Functions makes its five submenus once and refills only their items.
- **Items**: each function dispatches `.uno:InsertFunction?FunctionName:string=<NAME>&FunctionCategory:short=0`
  (`SID_INS_FUNCTION` finds the name among all functions, starts input mode and inserts `=NAME(` with the argument
  names, like the Functions sidebar) and, like the sidebar, puts the function at the top of the recently used list.
  Typing a formula updates that list too (`ScViewFunc::EnterData`). Every menu ends with a separator and
  "Function..." (`.uno:FunctionDialog`). The tooltip (`setTipHelpText`) is the signature and the short description
  of the Function Wizard (no new strings); add-in functions read from the configuration get the description only.
- **Selection**: VCL tells only the menu that holds the item, so the controller also listens to each submenu and reads
  the command from the event's `Source`. It dispatches through `PopupMenuControllerBase::dispatchCommand`
  (asynchronous). There is no `MenuBarManager` to follow states, so each build asks for the state of
  `.uno:InsertFunction` once (a status listener added and removed, as `PopupMenuControllerBase::updateCommand` does)
  and enables the function items by it: with a drawing object selected they are disabled, cannot be picked and so
  never reach the recently used list. "Function..." is left enabled (its own slot decides when it is dispatched).
- **Export**: `svt::PopupMenuControllerBase` was exported only without mergelibs (`UNLESS_MERGELIBS(SVT_DLLPUBLIC)`).
  Release configurations enable mergelibs (`distro-configs/LibreOfficeLinux.conf`, Win, macOS) and svt is merged while
  sc is not, so libsclo could not link there; the class is now `SVT_DLLPUBLIC` unconditionally (visibility only). The
  dev build has mergelibs off, so that link is not exercised here; a unit test pins the export.
- **Real window (gtk3, headless sway, 1920 px light)**: Financial opens a native menu of its functions (ACCRINT ...
  NPV ..., including the Analysis add-in's `_ADD` variants, which are LibreOffice's Financial category too); it is
  taller than the screen, so GTK places it from the top edge with a scroll arrow. Logical lists AND ... XOR, a separator
  and Function...; a click on IF leaves A1 in edit mode with `=IF(Test` and "Test" selected. More Functions lists the five
  submenus and Function...; hovering Information opens CELL ... TYPE to the right, and a click on ISBLANK there inserts
  `=ISBLANK(Value)` (the submenu listener path). Recently Used then lists the picked function first (AND, SUM, AVERAGE,
  MIN, MAX, IF). The tooltips do not show in the GTK native menus: `GtkSalMenu` implements no `SetItemTooltip` and
  blocks tooltips while a native popup runs; the text is set on the VCL menu (UITest) for the other VCL plugins.
- **Tests**: `FunctionMenuControllerTest` in `test_calc_formulas_ui.py` (Popup nodes, component registration, the
  category table against the design, submenu order and labels, the item URL, the removed popups, the unconditional
  export of the base class) and six UITests:
  each single-category menu lists exactly the functions `com.sun.star.sheet.FunctionDescriptions` gives for its
  category and ends with Function...; Financial (PMT, NPV, tooltip) and Lookup & Reference (VLOOKUP, INDEX);
  More Functions' five submenus; a SUM item, selected through the controller, starts input mode with `=SUM(`; Recently
  Used lists a typed function and then a function picked from a menu, first; with a drawing object selected (grid
  `SELECT OBJECT`) the function items are disabled, and enabled again with a cell. They build the popup through
  `PopupMenuControllerFactory` without a `Value` and select an item by calling the controller's `itemSelected`.

### 6.8 Review tab (T5a)

`product/ui/calc_review.json` (page `phbReview`, prefix `Review`) replaces the upstream Review page children
between generated `product:Review-begin/end` markers and removes the overflow menu object `Menu Review`. Seven
sections in Excel's order: Proofing, Accessibility, Language, Comments, Notes, Protect, Ink (spec:
`product/docs/design/calc-review-tab-layout.txt`). Every control is a large button. Icons, the 1920 px fit and
screenshots are T5b. No C++ and no new slot: slots +408..+412 already existed.

- **Dropdowns** (no slot): `.uno:ReviewAccessibilityMenu` ("Check Accessibility": placeholder item, Alt Text,
  AutoFormat, Unmerge Cells) and `.uno:ReviewNotesMenu` ("Notes"). Popup files `review_accessibility.xml` and
  `review_notes.xml`, `Controller.xcu` Popup + ToolBox nodes, registered in `UIConfig_scalc.mk`.
- **Placeholders** (registry labels, tooltip "<Label> (not available yet)"): Check Accessibility (menu item only),
  Translate, Previous/Next Comment (family `.uno:ReviewGoToComment?Direction:string=previous|next`, buttons in the
  Comments group and the same two URLs as Notes menu items), Allow Edit Ranges, Hide Ink.
- **R12 (duplicate ids)**: every generated id carries the page prefix (`btnReviewInsertAnnotation` vs
  `btnInsertInsertAnnotation`), so a command on two pages (Comment on Insert and Review) is two widgets; the
  whole-UI duplicate-id test and a shared-command test cover it. Navigator is not on this page.
- **R14 (buttons that leave the tab)**: Automatic Spell Checking, Hyphenation, Track Changes (Record, Manage),
  Compare/Merge Document and Redact have no Review button any more; `test_the_menu_bar_keeps_every_command_that_left_the_tab`
  asserts each stays in `menubar.xml` (Tools, Edit > Track Changes, File). Edit/Show All/Hide All/Delete All Comments
  moved into the Notes menu (Edit and Delete All also remain in the menu bar).
- **Comments vs Notes**: LibreOffice has one comment type (it behaves like Excel's notes). The Comments group has
  Comment (`InsertAnnotation`), Delete Comment (`DeleteNote`), Previous/Next, Show Comments (`ShowAnnotations`); the
  Notes menu has the note-style actions. Both drive the same comments; Convert to Comments is omitted.
- **UITests**: `test_review_*` (sections and toolboxes, placeholders disabled and inert, dropdown commands enabled
  once a comment/range exists, popup contents, placeholder labels). The drawn-disabled count is now 46 buttons.
- `.uno:AutoFormat` in the Check Accessibility menu keeps LibreOffice's label "Table Styles" instead of the design's
  "AutoFormat Styles..." (no such string exists; changing the shared label would rename other menus).

#### Review icons and fit (T5b)

- **Icons**: 15 new boost/boost_dark manifest entries (Fluent glyphs, soft fills, same style as the other tabs), all
  large: `spelldialog` (text_proofing_tools; the design's `text_proofing_tools_abc` does not exist in Fluent 1.1.344),
  `thesaurusdialog` (book_open), `setdocumentproperties` (data_usage), `reviewaccessibilitymenu`
  (accessibility_checkmark), `reviewtranslate` (translate), `deletenote` (comment_dismiss), `showannotations`
  (comment_multiple), `reviewnotesmenu` (comment_note), `protect` (lock_closed), `toolprotectiondocument`
  (shield_lock), `reviewalloweditranges` (lock_open), `sharedocument` (people_swap), `reviewhideink` (ink_stroke),
  and the URL variants `reviewgotocomment_previous` / `_next` (comment_arrow_left / comment_arrow_right). Comment
  reuses `insertannotation` from Insert.
- The two Previous/Next Comment buttons are URL variants: json `icon` keys `cmd/32/reviewgotocomment_{previous,next}.png`
  (T5a had `cmd/sc_`; the icon test checks the size prefix against the button size). The image flag was already on every
  Review command, so the xcu is unchanged.
- `test_icons.py`: every Review button resolves its icon in both themes (RED before: missing icons) and the
  URL-variant icon names and sizes.
- **Fit at 1920 px (measured on screenshots)**: all seven sections are visible with no ">>" and no fallback step was
  needed. Section right edges: Proofing 218, Accessibility 358, Language 434, Comments 948, Notes 1016, Protect 1530,
  Ink 1601 (design estimate 1564 px wide; usable width stops near 1830). At 1600 px (dark) Proofing to Protect stay
  (last edge x = 1531) and Ink folds behind ">>". At 1366 px Proofing to Notes stay (last edge x = 1016); Protect and
  Ink fold.
- **Real-window menus**: the popup menus list only enabled items. On an empty cell the Notes menu shows just
  "Insert Comment" and the Check Accessibility menu shows "[No selection possible]" (its four items need an object, a
  range or a merged cell). The full item lists are covered by the UITests, not by a screenshot.

### 6.9 View tab (T6a)

`product/ui/calc_view.json` (page `phbView`, prefix `View`) replaces the upstream View page children between
generated `product:View-begin/end` markers and removes the overflow menu object `Menu View`. Seven sections:
Sheet View, Workbook Views, Dark Mode, Show, Zoom, Window, Macros (spec:
`product/docs/design/calc-view-tab-layout.txt` plus the Sheet View group below). Icons, the 1920 px fit and
screenshots are T6b (the variant buttons already carry their icon names). No C++ and no new slot: slots
+413..+418 and +421 already existed; this task gives them labels and variants.

- **Sheet View group** (controller ruling, first group like Excel's). Excel's group is a "Switch Sheet View"
  combo with Keep, Exit, New and Options under it (research reference section 5, `view-msqa-1.png`: with a
  local file all of it is greyed). gen_ribbon only makes tool buttons, so the built form is Excel's reduced
  form: a "Default" button in the top row (stands for the combo and shows its default text) and the four
  buttons Keep, Exit, New, Options in one icon-only toolbox under it. All five are URL variants of the family
  slot `.uno:ViewSheetView` (`?Action:string=switch|keep|exit|new|options`), labelled "Default", "Keep",
  "Exit", "New", "Options" (tooltip "<Label> (not available yet)"). The width is about 170 px.
- **Dropdowns** (no slot): `.uno:ViewFreezePanesMenu` ("Freeze Panes": Freeze Panes, Freeze First Row, Freeze
  First Column; `view_freezepanes.xml`), `.uno:ViewMacrosMenu` ("Macros": Macro Manager, Record Macro,
  separator, Run Macro, Edit Macros; `view_macros.xml`) and `.uno:ViewSwitchWindowsMenu` ("Switch Windows").
  Controller.xcu Popup + ToolBox nodes, popup files registered in `UIConfig_scalc.mk`.
- **Placeholders** (registry labels): Page Layout, Custom Views, Ruler, Arrange All, Hide/Unhide
  (`.uno:ViewWindowVisibility?Action:string=hide|unhide`), View Side by Side / Synchronous Scrolling / Reset
  Window Position (`.uno:ViewSideBySide?Action:string=toggle|sync|reset`) and the five Sheet View variants.
- **R7 (Switch Windows)**: works. `WindowListMenuController` is registered under the new command with no
  `Value` and no popup file; its `itemActivated` fills the popup with the open windows (ids 4600..4699, the
  active one checked), as the UITest shows by building the popup through `PopupMenuControllerFactory` and
  activating it. The static-popup fallback was not needed.
- **R12 (duplicate ids)**: every generated id carries the page prefix, so Navigator, View Grid Lines and View
  Headers are `btnViewNavigator` here and `btnPageLayoutNavigator` on Page Layout; the whole-UI duplicate-id
  test and a shared-command test cover the three.
- **R14 (buttons that leave the tab)**: Entire Page, Page Width, Full Screen, Value Highlighting, Hidden
  Row/Column Indicator, Styles (Manage Styles), Sidebar and Status Bar stay in the menu bar (`menubar.xml`);
  the Menubar toggle is the quick access bar's first button (`notebookbarshortcuts.xml`); Show Formulas is on the
  Formulas tab. Images and Charts (`.uno:ShowGraphics`) was only in the removed `Menu View`: it is reachable
  from Tools > Options > LibreOffice Calc > View > Objects (the design's ruling).
- **Macro Manager is experimental**: `.uno:MacroManager` has `IsExperimental`, so the framework hides it from
  the Macros menu (as from the menu bar) unless experimental mode is on; Record Macro, Run Macro and Edit
  Macros always show.
- **UITests**: `test_view_*` (sections and toolboxes, placeholders disabled and inert, enabled commands, popup
  contents, Switch Windows fill, labels of every variant). The drawn-disabled count is now 60 buttons and the
  slice-wide placeholder count 65.

#### View icons and fit (T6b)

- **Icons**: 27 new boost/boost_dark manifest entries (Fluent glyphs, soft fills, same style as the other tabs).
  Large: `normalviewmode` (grid), `pagebreakmode` (document_page_break), `viewpagelayout` (document_one_page),
  `viewcustomviews` (eye), `changetheme` (weather_moon), `zoom` (zoom_in), `zoom100percent` (ratio_one_to_one),
  `zoomoptimal` (zoom_fit), `newwindow` (window_new), `viewarrangeall` (window_multiple), `viewfreezepanesmenu`
  (table_freeze_column_and_row), `viewswitchwindowsmenu` (tab_desktop_multiple; `window_multiple_swap` has no
  24 px source), `viewmacrosmenu` (code). Small: `viewruler` (ruler), `inputlinevisible` (text_field;
  `window_header_horizontal` has only a 20 px source), `viewcolumnrowhighlighting` (table_cursor), `splitwindow`
  (split_horizontal) and the URL variants `viewsheetview_{switch,keep,exit,new,options}` (eye_lines, save, eye_off,
  eye, text_bullet_list, after Excel's Sheet View icons), `viewwindowvisibility_{hide,unhide}` (eye_off, eye),
  `viewsidebyside_{toggle,sync,reset}` (split_vertical, arrow_sync, arrow_reset). Navigator, View Grid Lines and
  View Headers reuse the Page Layout icons.
- All URL variants are small buttons, so the json `icon` keys keep the `cmd/sc_<base>_<value>.png` form; no json,
  .ui or xcu change was needed (every View command already had the image flag).
- `test_icons.py`: every View button resolves its icon in both themes (RED before: 58 missing members) and the
  URL-variant icon names and sizes.
- **Fit at 1920 px (measured on screenshots)**: all seven sections are visible with no ">>" and no fallback step was
  needed. Section right edges: Sheet View 118, Workbook Views 465, Dark Mode 551, Show 921, Zoom 1080, Window 1729,
  Macros 1806. At 1600 px (dark) Sheet View to Zoom stay (last edge x = 1080) and Window and Macros fold behind
  ">>". At 1366 px the same: Sheet View to Zoom stay, Window and Macros fold.
- **Real-window menu**: with New Window clicked once (two windows of one document), Switch Windows lists
  "Untitled 1" (selected, radio mark) and "Untitled 1 : 2", so the framework WindowListMenuController fills a popup
  opened from the ribbon button.

### 6.10 Help tab (T7)

`product/ui/calc_help.json` (page `phbHelp`, prefix `Help`, no `remove_objects`) fills the empty `pmhbHelp` box
between the `product:Help-begin/end` markers. Two sections, all large buttons, no menus, no launchers
(verbatim spec: `product/docs/design/calc-help-tab-layout.txt`):

- **Help**: `.uno:HelpIndex` (shows "%PRODUCTNAME Help", so "LibreOffice Help"), `.uno:QuestionAnswers` ("Get Help
  Online"), `.uno:HelpFeedback` (placeholder +419), `.uno:Documentation` ("User Guides"), `.uno:WhatsNew`.
- **Community**: `.uno:GetInvolved`, `.uno:HelpBlog` (placeholder +420, labelled "Blog": the label must not carry
  Microsoft's product name).
- Labels: `Feedback` and `Blog` nodes in `CalcCommands.xcu` with the "(not available yet)" tooltips and the image
  flag; the registry (`placeholders.json`) carries both labels. The five existing commands already had labels and
  the image flag. No dropdown, so no Controller.xcu or popup file.
- **Icons**: 7 boost/boost_dark manifest entries, all large: `helpindex` (question_circle), `questionanswers`
  (person_support), `helpfeedback` (person_feedback), `documentation` (hat_graduation), `whatsnew` (sparkle),
  `getinvolved` (people_community), `helpblog` (news).
- **Fit at 1920 px**: the page ends at x = 611 of about 1875 px; nothing to reduce.
- Tests: `test_calc_help_ui.py` (layout, labels, registry, ids, suppr, reproducibility), `test_icons.py` (every Help
  button resolves its icon) and the `test_help_*` UITests (sections and toolboxes, both placeholders disabled and
  inert and drawn disabled while the other five buttons are drawn enabled, labels). The drawn-disabled count is now
  62 buttons.

### 6.11 Cross-tab polish (T8a)

#### Section captions on one baseline

- **Cause**: the tab control is as tall as its tallest page (Home), and each generated page box was `valign center`,
  so a page whose sections hold only large buttons (Review, Help: 80 px of sections) sat centered in it with its
  captions about 16 px higher than Home's. Page Layout's upstream page itself was `valign center` (3 px lower than
  the others once filled). Within a page, VclGrid splits extra height evenly between expanding rows and drops the
  remainder, so a caption under several expanding rows (a large button spans rows 0-2, the caption row expanded too)
  ended up to 3 px above its neighbours (Home: Clipboard and Editing against Font).
- **Fix** (`gen_ribbon.py`): the page box fills the tab page (`valign fill`), and each section grid `gd<P><Name>` now
  has two rows: the toolboxes' grid `gc<P><Name>` (new id, row 0, the only child with `vexpand`), the caption under
  it (row 1, no `vexpand`) and the separator spanning both. The extra height all goes to the toolboxes' grid, so every
  caption ends on its section's bottom edge. The toolboxes keep their columns, rows, spans and `valign`. A new
  `properties` operation of `calc_tabs.json` sets `phbLayout`'s own `valign` from `center` to `fill` (re-runnable,
  refuses an unexpected value). Requisitions are unchanged, so the ribbon height is too.
- **Measured** (1920 px light screenshots, before -> after): name box top (the ribbon's bottom edge) y = 181 on every
  tab, before and after. Section separators and caption baselines:

  | Tab | Separators before | Baselines before | Separators after | Baseline after |
  |---|---|---|---|---|
  | Home | 51-159 .. 51-162 | 156, 158, 159 | 51-162 | 159 |
  | Insert, Data, View | 54-158 | 155 | 51-162 | 159 |
  | Page Layout, Formulas | 54-157 .. 54-158 | 154, 155 | 51-162 | 159 |
  | Review, Help | 66-146 | 143 | 51-162 | 159 |

  Large buttons stay centered in the area above the caption, which is now the same on every tab: their icons start
  at y = 70-71 everywhere (Review and Help unchanged, Insert 6 px lower, Home's Paste 2 px lower). On Home the Cells
  buttons (Insert, Delete, Format) moved 8 px lower and line up with Sort & Filter and Find & Select (labels at
  y = 110-119 in both).
- **Tests**: `CaptionBaselineTest` (every generated page and its tab page fill the page height; every section grid of
  every page follows the two-row rule) and fixture tests in `test_gen_ribbon.py`; `test_calc_tabs.py` checks the
  Page Layout property change and the `properties` operation.

#### Disabled icons in dark (fixed in VCL by T8b, 6.12)

- Disabled icon-only buttons (View > Sheet View, Hide/Unhide; Review > Hide Ink) look almost as bright as enabled
  ones in Boost Dark. VCL draws a disabled image through `BitmapDisabledImageFilter`
  (`vcl/source/bitmap/BitmapDisabledImageFilter.cxx`, cached by `ImplImage::getBitmap`): every pixel becomes grey
  `luminance / 4 + 160` (160..224) with its alpha kept, whatever the background. Measured on the View screenshots: the
  disabled Sheet View icons are pure grey, at most 213 (the dark outline #D6D6D6) on #2B2B2B, contrast 6.3:1, above
  the enabled Column/Row Highlighting icon (3.6:1); in light they are at least 176 (#424242 outline) on #E4F2E8, 1.5:1.
- No product-side lever: the filter reads neither the color scheme nor the icon theme, and an icon's alpha dims its
  enabled form too. A fix belongs in VCL (filter range or alpha from the face color, with the cache keyed by it).

#### Parked review minors

- **sfx2** (`SfxDispatchController_Impl::StateChanged`, T1c): one event copy before the loop with only `FeatureURL`
  set per listener URL; the plain command of the bound variant takes `aDispatchURL` without its arguments instead of
  being parsed; a URL whose `parseStrict` fails is skipped. The variant-listener UITest helper waits until no listener
  has heard an event for one second (the bindings push from a 300 ms timer) instead of a fixed `sleep(1)`.
- **framework** (`getSingleBoolArgument`, T3c): the type is what `Name:type=value` has between the first `:` and the
  first `=` (as `SfxDispatchController_Impl::addParametersToArgs` reads it), so a string whose value contains
  `:bool=true` is not a boolean variant. `test_framework_menu_rule_reads_the_bool_type_from_the_arguments_type_segment`
  compiles the function out of the source with the system C++ compiler and runs it on 12 URLs (RED before: the two
  string URLs were read as booleans).
- **sc** (`FunctionMenuController::updateFunctionsEnabled`, T4c): `queryDispatch` on a frame disposed before the
  controller threw `DisposedException` out of `updatePopupMenu`; it is caught and the function items are built
  disabled. UITest `test_formulas_function_menu_of_a_closed_window_is_built_with_its_items_disabled` (RED before:
  `DisposedException: Frame disposed`).

### 6.12 Disabled icons in dark themes (T8b)

- **Cause** (6.11): `BitmapDisabledImageFilter` mapped every pixel to grey `luminance / 4 + 160` whatever the
  background, so on a dark face a disabled icon was a light grey brighter than many enabled icons.
- **Fix** (`vcl/source/bitmap/BitmapDisabledImageFilter.cxx`): the filter takes the face color it is drawn on. A light
  face (`!IsDark()`) keeps `luminance / 4 + 160`, byte for byte. On a dark face a pixel of luminance L becomes the grey
  whose WCAG contrast against the face is `1 + L / 255`: as light as the face for black, at most 2:1 for white
  (#2B2B2B: 43..88; #000000: 0..63; #454545: 69..114). The band is set in contrast, not in sRGB levels: the first
  version (`face + L * 3 / 16`, a fixed 48-level band) dimmed alike from #1F1F1F up but nearly vanished on black
  (1.28:1 simulated, high contrast black), because the same sRGB step is less contrast near black. Simulated on the
  Boost Dark icons (mean ink contrast, as in 6.11), the contrast band gives 1.51:1 on #000000, 1.61:1 on
  #1A1A1A, 1.63:1 on #2B2B2B to #5A5A5A (light today: 1.55:1). `Image::Draw` passes the output device's
  `StyleSettings::GetFaceColor()` (the color VCL already uses to pick a dark or light toolbox arrow); `ImplImage`
  keys its cached disabled bitmap by that face color too, so a theme switch at runtime makes it again.
- **Intended**: a control that sets its own face color gets the band of that face. In a light theme, a disabled image
  on a button with a dark background gets the dark band: `PushButton` draws with the face set to its control
  background (vcl/source/control/button.cxx), and toolkit's `setButtonLikeFaceColor` sets the face of button-like
  controls from their UNO background color (toolkit/source/awt/vclxwindows.cxx).
- **Limitation**: the band follows the face color, not the surface actually painted under the image. A theme that
  mixes a dark face with light menus or fields (`MenuColor`, `FieldColor`) would draw dark-on-light disabled icons
  there.
- **Measured** (1920 px screenshots, every icon that changed, WCAG contrast of its mean ink against the background,
  as in 6.11; "dark after" is the first version of the band, Calc View re-measured with the contrast band:
  1.59:1, range 1.47-1.81):

  | Screen | Light (before = after) | Dark before | Dark after |
  |---|---|---|---|
  | Calc View (16 disabled icons) | 1.53:1 | 6.14:1 | 1.56:1 |
  | Calc Review (10) | 1.56:1 | 6.82:1 | 1.63:1 |
  | Writer standard toolbar (7: Cut, Copy, Paste, Undo, Redo, ...) | 1.60:1 | 6.23:1 | 1.60:1 |
  | Impress toolbars (14) | 1.60:1 | 6.91:1 | 1.66:1 |

  Light screenshots are pixel-identical before and after. Enabled icons are unchanged (Calc View Column/Row
  Highlighting: 2.33:1 light, 3.63:1 dark).
- **Runtime switch**: one Calc process with system GTK colors (Adwaita), toggled light -> dark -> light by
  `.uno:ChangeTheme`: the disabled Ruler and Page Layout icons go from grey 176..255 on white to 45..93 on #2D2D2D
  (1.63:1, 1.75:1; 7.19:1 and 7.99:1 without the fix; measured with the first version of the band) and back to the
  same light pixels. (With a LibreOffice color
  scheme such as Boost, a scheme change asks for a restart, so it is not a runtime switch.)
- **Tests**: `vcl/qa/cppunit/BitmapProcessorTest.cxx` (`CppunitTest_vcl_bitmapprocessor_test`): on #2B2B2B,
  #454545, #1A1A1A and #000000 every disabled pixel is a grey at contrast `1 + L / 255` (within 0.02) against the face;
  light faces give exactly today's output; alpha is kept; an image drawn disabled on a light, a dark and again a light
  face gives the light, dark and light grey (the cache follows the face color).

## 7. Known limitations and next steps

- **Orientation menu has no check mark.** Its slot state is an `SvxPageItem`, not a boolean, so neither Portrait
  nor Landscape is marked (6.3, T3c; ruling 22). Calculation Options does show its mode.
- **Images and Charts (`.uno:ShowGraphics`) is reachable only through Tools > Options > LibreOffice Calc > View >
  Objects.** It was only in the removed View menu.
- **Macro Manager is hidden unless experimental mode is on** (`IsExperimental`, framework rule). Record Macro,
  Run Macro and Edit Macros always show. Data > Other Sources > Streams has the same limit.
- **gtk3 menus show no item tooltips.** `GtkSalMenu` implements no `SetItemTooltip`. The function menus set the
  signature as tooltip text anyway (UITest); other VCL plugins show it.
- **Popups hide disabled entries** (pending decision **T10**). LibreOffice's `DontHideDisabledEntry` defaults to
  hiding them; Excel shows them greyed. So the Breaks menu on cell A1 reads "[No selection possible]", the Notes
  menu on an empty cell shows only Insert Comment, and the Check Accessibility menu on an empty cell is empty.
  Changing the default affects every context menu. If chosen, the screenshots of the populated menus can be taken.
- **Some labels are LibreOffice's, not Excel's** (pending decision **T9**): for example Fontwork for WordArt,
  Headers and Footers, Object for the OLE button, Formula Object for Equation, Table Styles (the AutoFormat
  entry of the accessibility menu), "Chart..." for the chart wizard. Two ways: Calc-only label overrides in
  `CalcCommands.xcu`, which also rename the menus, or ribbon-only URL label variants.
- **Labels are en-US only.** About 115 new `CalcCommands.xcu` nodes, the three tab labels and the new
  popup menus need translations before shipping. Translated labels may also push the last sections behind ">>"
  at 1920 px.
- **Width**: sections fold into ">>" at 1600 and 1366 px (section 1); Excel folds group by group into dropdowns.
- **After adding a UNO component** (a `.component` entry, as for the function menus) run
  `product/dev/lo-make.sh Rdb_services` after `postprocess.build`, or the new service cannot be created.
- **Shared code changed in this slice** (candidates for upstream; each has a regression test):
  - **T1b** `sfx2/source/sidebar/ControllerFactory.cxx`: a toolbox button whose slot is disabled was forced
    enabled after `update()`.
  - **T1c** `sfx2/source/control/unoctitm.cxx`: a URL variant of a slot did not hear later state changes. The
    T8a refactor keeps one event copy per push. Side effect: seven Writer Compact `StyleApply` buttons that stayed
    greyed after Edit Document are now enabled.
  - **T3c** `framework/source/uielement/menubarmanager.cxx`: a menu item whose URL has exactly one boolean
    argument is checked only when the slot's state equals the argument. Only our Orientation and Calculation
    Options items use it in the whole tree.
  - **T4c** `include/svtools/popupmenucontrollerbase.hxx`: the class is exported unconditionally (visibility only);
    release builds enable mergelibs and the dev build does not, so that link is not exercised here.
  - **T8b** VCL: `BitmapDisabledImageFilter` draws disabled images by the face colour, so they look disabled in
    dark themes. Light output is byte-identical. The band follows the face colour, not the surface under the
    image; a theme that mixes a dark face with light menus or fields would draw dark-on-light disabled icons there.
- **Pre-existing bug, not fixed**: after a runtime theme switch (Adwaita light to dark with `.uno:ChangeTheme`)
  the View > Sheet View buttons lose their icons. With a LibreOffice colour scheme such as Boost a scheme change
  asks for a restart, so the normal path is not affected.
- **Not exercised in a real window**: clicking a Shapes entry to draw a shape; the mergelibs link of the
  function-menu controller. Calc does not invalidate `SID_INSERT_SPARKLINE` after the sheet is protected through
  the API or after a multi-range selection, so the Sparkline buttons keep their old state there (an sc matter).
- **Glyph substitutes** (Fluent 1.1.344 lacks the glyph at 24 px): four on Formulas and two on View (details in
  6.7 T4b and 6.9 T6b). Near-identical small icons remain (tags, the e^x pair,
  Calculate Now and Calculate Sheet).
- **Function menus**: the Financial menu is taller than the screen (GTK scrolls it); "Function..." stays enabled with
  a shape selected.
- **Next steps**: decide T9 and T10; the user reviews the screenshots; contextual tabs, Draw and Automate and the
  File backstage are separate slices; then implement placeholders one by one (section 8), starting with those
  that need no new infrastructure: Hide/Unhide, View Side by Side, Previous/Next Comment, Print Gridlines and
  Print Headings, Scale to Fit.

## 8. Placeholders

The "features to program later". 65 buttons and menu items on 42 slots (`product/tests/placeholders.json`,
`sc/inc/sc.hrc`): 9 on Data, 53 on the six new tabs' ribbons, 3 menu items. A family slot serves several
rows. Previous and Next Comment are also items of the Notes menu. All are greyed, with the tooltip
"<Label> (not available yet)", and do nothing. To implement one, follow the Data doc's recipe and delete
its registry entry.

| Tab | Label | Command | Slot |
|---|---|---|---|
| Data, Get External Data | From Database | `.uno:DataFromDatabase` | `FID_DATA_FROM_DATABASE` (+380) |
| Data, Get & Transform | Recent Sources | `.uno:DataRecentSources` | `FID_DATA_RECENT_SOURCES` (+381) |
| Data, Connections | Connections | `.uno:DataConnections` | `FID_DATA_CONNECTIONS` (+382) |
| Data, Connections | Properties | `.uno:DataConnectionProperties` | `FID_DATA_CONN_PROPS` (+383) |
| Data, Sort & Filter | Reapply | `.uno:DataFilterReapply` | `FID_DATA_FILTER_REAPPLY` (+384) |
| Data, Data Tools | Flash Fill | `.uno:DataFlashFill` | `FID_DATA_FLASH_FILL` (+385) |
| Data, Data Tools | Relationships | `.uno:DataRelationships` | `FID_DATA_RELATIONSHIPS` (+386) |
| Data, Data Tools | Manage Data Model | `.uno:DataManageModel` | `FID_DATA_MANAGE_MODEL` (+387) |
| Data, Forecast | Forecast Sheet | `.uno:DataForecastSheet` | `FID_DATA_FORECAST_SHEET` (+388) |
| Insert, Tables | Recommended PivotTables | `.uno:InsertRecommendedPivotTables` | `FID_INSERT_RECOMMENDED_PIVOT` (+389) |
| Insert, Pictures menu (menu item) | Place in Cell | `.uno:InsertPictureInCell` | `FID_INSERT_PICTURE_IN_CELL` (+390) |
| Insert, Illustrations | 3D Models | `.uno:Insert3DModels` | `FID_INSERT_3D_MODELS` (+391) |
| Insert, Illustrations | SmartArt | `.uno:InsertSmartArt` | `FID_INSERT_SMARTART` (+392) |
| Insert, Illustrations | Screenshot | `.uno:InsertScreenshot` | `FID_INSERT_SCREENSHOT` (+393) |
| Insert, Controls | Checkbox | `.uno:InsertCellCheckbox` | `FID_INSERT_CELL_CHECKBOX` (+394) |
| Insert, Charts | Insert Column or Bar Chart | `.uno:InsertChartType?Type:string=columnbar` | `FID_INSERT_CHART_TYPE` (+395) |
| Insert, Charts | Insert Line or Area Chart | `.uno:InsertChartType?Type:string=linearea` | `FID_INSERT_CHART_TYPE` (+395) |
| Insert, Charts | Insert Pie or Doughnut Chart | `.uno:InsertChartType?Type:string=piedoughnut` | `FID_INSERT_CHART_TYPE` (+395) |
| Insert, Charts | Insert Hierarchy Chart | `.uno:InsertChartType?Type:string=hierarchy` | `FID_INSERT_CHART_TYPE` (+395) |
| Insert, Charts | Insert Statistic Chart | `.uno:InsertChartType?Type:string=statistic` | `FID_INSERT_CHART_TYPE` (+395) |
| Insert, Charts | Insert Scatter (X, Y) or Bubble Chart | `.uno:InsertChartType?Type:string=scatterbubble` | `FID_INSERT_CHART_TYPE` (+395) |
| Insert, Charts | Insert Waterfall, Funnel, Stock, Surface or Radar Chart | `.uno:InsertChartType?Type:string=waterfall` | `FID_INSERT_CHART_TYPE` (+395) |
| Insert, Charts | Insert Combo Chart | `.uno:InsertChartType?Type:string=combo` | `FID_INSERT_CHART_TYPE` (+395) |
| Insert, Charts | Maps | `.uno:InsertChartType?Type:string=map` | `FID_INSERT_CHART_TYPE` (+395) |
| Insert, Charts | PivotChart | `.uno:InsertPivotChart` | `FID_INSERT_PIVOT_CHART` (+396) |
| Insert, Filters | Slicer | `.uno:InsertSlicer` | `FID_INSERT_SLICER` (+397) |
| Insert, Filters | Timeline | `.uno:InsertTimeline` | `FID_INSERT_TIMELINE` (+398) |
| Page Layout, Themes | Fonts | `.uno:PageLayoutThemePart?Part:string=fonts` | `FID_PAGELAYOUT_THEME_PART` (+399) |
| Page Layout, Themes | Effects | `.uno:PageLayoutThemePart?Part:string=effects` | `FID_PAGELAYOUT_THEME_PART` (+399) |
| Page Layout, Page Setup | Background | `.uno:PageLayoutBackground` | `FID_PAGELAYOUT_BACKGROUND` (+400) |
| Page Layout, Scale to Fit | Width | `.uno:PageLayoutScaleToFit?Dimension:string=width` | `FID_PAGELAYOUT_SCALE_TO_FIT` (+401) |
| Page Layout, Scale to Fit | Height | `.uno:PageLayoutScaleToFit?Dimension:string=height` | `FID_PAGELAYOUT_SCALE_TO_FIT` (+401) |
| Page Layout, Scale to Fit | Scale | `.uno:PageLayoutScaleToFit?Dimension:string=scale` | `FID_PAGELAYOUT_SCALE_TO_FIT` (+401) |
| Page Layout, Sheet Options | Print Gridlines | `.uno:PageLayoutPrintOption?Option:string=gridlines` | `FID_PAGELAYOUT_PRINT_OPTION` (+402) |
| Page Layout, Sheet Options | Print Headings | `.uno:PageLayoutPrintOption?Option:string=headings` | `FID_PAGELAYOUT_PRINT_OPTION` (+402) |
| Formulas, Python | Insert Python | `.uno:FormulasPython?Action:string=insert` | `FID_FORMULAS_PYTHON` (+403) |
| Formulas, Python | Reset | `.uno:FormulasPython?Action:string=reset` | `FID_FORMULAS_PYTHON` (+403) |
| Formulas, Python | Editor | `.uno:FormulasPython?Action:string=editor` | `FID_FORMULAS_PYTHON` (+403) |
| Formulas, Python | Initialization | `.uno:FormulasPython?Action:string=init` | `FID_FORMULAS_PYTHON` (+403) |
| Formulas, Error Checking menu (menu item) | Error Checking | `.uno:FormulasErrorChecking` | `FID_FORMULAS_ERROR_CHECKING` (+404) |
| Formulas, Formula Auditing | Evaluate Formula | `.uno:FormulasEvaluateFormula` | `FID_FORMULAS_EVALUATE_FORMULA` (+405) |
| Formulas, Formula Auditing | Watch Window | `.uno:FormulasWatchWindow` | `FID_FORMULAS_WATCH_WINDOW` (+406) |
| Formulas, Calculation | Calculate Sheet | `.uno:FormulasCalculateSheet` | `FID_FORMULAS_CALCULATE_SHEET` (+407) |
| Review, Check Accessibility menu (menu item) | Check Accessibility | `.uno:ReviewCheckAccessibility` | `FID_REVIEW_CHECK_ACCESSIBILITY` (+408) |
| Review, Language | Translate | `.uno:ReviewTranslate` | `FID_REVIEW_TRANSLATE` (+409) |
| Review, Comments | Previous Comment | `.uno:ReviewGoToComment?Direction:string=previous` | `FID_REVIEW_GOTO_COMMENT` (+410) |
| Review, Comments | Next Comment | `.uno:ReviewGoToComment?Direction:string=next` | `FID_REVIEW_GOTO_COMMENT` (+410) |
| Review, Protect | Allow Edit Ranges | `.uno:ReviewAllowEditRanges` | `FID_REVIEW_ALLOW_EDIT_RANGES` (+411) |
| Review, Ink | Hide Ink | `.uno:ReviewHideInk` | `FID_REVIEW_HIDE_INK` (+412) |
| View, Workbook Views | Page Layout | `.uno:ViewPageLayout` | `FID_VIEW_PAGE_LAYOUT` (+413) |
| View, Workbook Views | Custom Views | `.uno:ViewCustomViews` | `FID_VIEW_CUSTOM_VIEWS` (+414) |
| View, Show | Ruler | `.uno:ViewRuler` | `FID_VIEW_RULER` (+415) |
| View, Window | Arrange All | `.uno:ViewArrangeAll` | `FID_VIEW_ARRANGE_ALL` (+416) |
| View, Window | Hide | `.uno:ViewWindowVisibility?Action:string=hide` | `FID_VIEW_WINDOW_VISIBILITY` (+417) |
| View, Window | Unhide | `.uno:ViewWindowVisibility?Action:string=unhide` | `FID_VIEW_WINDOW_VISIBILITY` (+417) |
| View, Window | View Side by Side | `.uno:ViewSideBySide?Action:string=toggle` | `FID_VIEW_SIDE_BY_SIDE` (+418) |
| View, Window | Synchronous Scrolling | `.uno:ViewSideBySide?Action:string=sync` | `FID_VIEW_SIDE_BY_SIDE` (+418) |
| View, Window | Reset Window Position | `.uno:ViewSideBySide?Action:string=reset` | `FID_VIEW_SIDE_BY_SIDE` (+418) |
| View, Sheet View | Default | `.uno:ViewSheetView?Action:string=switch` | `FID_VIEW_SHEET_VIEW` (+421) |
| View, Sheet View | Keep | `.uno:ViewSheetView?Action:string=keep` | `FID_VIEW_SHEET_VIEW` (+421) |
| View, Sheet View | Exit | `.uno:ViewSheetView?Action:string=exit` | `FID_VIEW_SHEET_VIEW` (+421) |
| View, Sheet View | New | `.uno:ViewSheetView?Action:string=new` | `FID_VIEW_SHEET_VIEW` (+421) |
| View, Sheet View | Options | `.uno:ViewSheetView?Action:string=options` | `FID_VIEW_SHEET_VIEW` (+421) |
| Help, Help | Feedback | `.uno:HelpFeedback` | `FID_HELP_FEEDBACK` (+419) |
| Help, Community | Blog | `.uno:HelpBlog` | `FID_HELP_BLOG` (+420) |

# Calc ribbon tabs like Excel (Tabbed Office)

Status: in progress on branch `feature/calc-ribbon-tabs`. This document grows with the tab tasks;
T1 (below) is the shared groundwork. Design: `product/docs/design/calc-ribbon-tabs-overview.txt`,
rulings: `product/odd/tasks/calc-ribbon-tabs.md`. Read `calc-data-redesign.md` first for the
placeholder and split recipes.

## 1. Tab order and labels (T1)

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

## 2. Placeholder slots (T1)

All placeholder slots of the slice exist already: `SID_NEW_SLOTS+380..+421` (Data +380..+388,
the other tabs +389..+420, View > Sheet View +421). Spare: +422..+424; +424 is the last Calc slot
id. Each slot follows the Data recipe: `sc/inc/sc.hrc` define, `scalc.sdi` entry (ReadOnlyDoc
FALSE; Menu, ToolBox and Accel config FALSE), `cellsh.sdi` StateMethod without ExecMethod, and a
case in the always-`DisableItem` list of `cellsh.cxx`. Labels and tooltips come with the tab tasks.

A **family slot** serves several buttons through URL variants, for example
`.uno:InsertChartType?Type:string=map`. The slot is disabled for every variant, and sfx2 ignores an
argument the slot does not declare.

## 3. Test tooling (T1)

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

## 4. Insert tab (T2a)

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

## 5. Screenshot tool (`product/dev/shot-tab.sh`)

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

## 6. Page Layout tab (T3a)

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

### Page Layout icons and fit (T3b)

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

### Placeholder buttons drawn disabled (T1b)

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

### Argument-variant URLs hear later state changes (T1c)

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

## 7. Formulas tab (T4a)

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

### Formulas icons and fit (T4b)

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

### Function-category menus (T4c)

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

## 8. Review tab (T5a)

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

### Review icons and fit (T5b)

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

## 9. View tab (T6a)

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

### View icons and fit (T6b)

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

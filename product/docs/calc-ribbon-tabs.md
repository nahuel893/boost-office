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

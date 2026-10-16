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
- Icons, the 1920 px fit check and screenshots belong to T2b: the layout items have no `icon` yet.

Risks settled in T2a: R6 (the Shapes popup builds its Line submenu and the seven toolbar-submenu
entries from a ribbon dropdown), R3 (`InsertSparkline?Type:string=...` stays enabled and opens the
Sparkline dialog; sfx2 ignores the undeclared argument) and R12 (no duplicate widget id in the
whole office `.ui`). The UITests that prove them are in `notebookbarOffice.py`.

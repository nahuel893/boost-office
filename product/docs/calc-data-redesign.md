# Calc Data tab redesign

Status: implemented on branch `feature/calc-data-redesign` (2026-10-13). Second slice of the
"Tabbed Office" ribbon, built with the tools of the Home slice (`product/docs/calc-home-redesign.md`,
read that first for the variant, the themes and the shared tooling). This document is the reference
for what the Data tab looks like, how it is built, and what is still open.

Design source (outside the repo): `/home/nh/office-boost/docs/design/calc-data-tab-layout.txt`.

## 1. What the user sees

### Data tab: 8 sections, in Excel's order

| Section | Content |
|---|---|
| Get External Data | From Database (placeholder), External Links, Insert Sheet from File (small, with label); **Other Sources v** (large, split: menu); Data Sources (large) |
| Get & Transform | Data Provider (large); Select Range, Define Range, Recent Sources (placeholder) |
| Connections | **Refresh** (large, split); Connections (placeholder), Properties (placeholder), Edit Links (icon only) |
| Sort & Filter | Sort A-Z, Sort Z-A, Shuffle (icon only); Sort (large); AutoFilter (large); Reset Filter, Reapply (placeholder), Advanced Filter |
| Data Tools | Text to Columns (large); Flash Fill (placeholder), Duplicates, Validity; Consolidate, Relationships (placeholder), Manage Data Model (placeholder) |
| Forecast | **What-If Analysis v** (large, split: menu); Forecast Sheet (large, placeholder) |
| Outline | **Group** and **Ungroup** (split), Subtotals; Show Detail, Hide Detail (icon only) |
| Analyze | **Statistics v** (large, menu) |

- Every button is an Excel button. Where LibreOffice has the feature, the button runs it; where it
  does not, the button is a **placeholder**. The nine placeholders are From Database, Recent Sources,
  Connections, Properties, Reapply, Flash Fill, Relationships, Manage Data Model and Forecast Sheet.
  They are greyed out, and their tooltip reads "<Label> (not available yet)". They do nothing.
- Sort A-Z, Sort Z-A, Shuffle, Edit Links, Show Detail and Hide Detail are icon-only (their tooltips
  keep the names), like Excel's A-Z / Z-A buttons.
- Split buttons (body runs the main action, the arrow opens a menu):
  - **Refresh**: body refreshes the selected database range; menu: Refresh Range, Refresh Data
    Provider, Refresh Pivot Table, Recalculate Hard.
  - **Group**: body groups the selected rows or columns; menu: Group, AutoOutline.
  - **Ungroup**: body ungroups; menu: Ungroup, Remove Outline.
- Dropdown-only menus:
  - **Other Sources**: XML Source, Streams.
  - **What-If Analysis**: Scenarios, Goal Seek, Multiple Operations, Solver.
  - **Statistics**: LibreOffice's statistics menu (13 entries).
- **Standard Filter** left the tab (Excel has no such button); it is still in the menu bar under
  Data. "Advanced Filter" on the tab runs LibreOffice's Advanced Filter (`.uno:DataFilterSpecialFilter`);
  it only shares its icon with Standard Filter.
- The old compact "Data" overflow menu of the upstream page is gone; its items are reachable from
  the new sections and the menu bar.
- All 8 sections are visible at 1920 px. Narrower windows collapse sections from the right into ">>"
  (see section 6).

### Icons

Boost and boost_dark icons for every button (Fluent glyphs, same style as Home; see the Home doc).
Reset Filter is a filter with a red x, Reapply the Fluent `filter_sync` glyph (a filter with sync
arrows), Consolidate a table with an arrow joining a row (`table_move_below`; `merge` was dropped
because it read as the ">>" overflow chevron).

## 2. How to try it

```
product/dev/calc.sh dark      # Tabbed Office, dark; then open the Data tab
product/dev/calc.sh light
```

Close Calc before switching modes. Details of the launcher are in the Home doc.

## 3. How it is built

- `product/ui/calc_data.json` is the layout of the Data page (same schema as `calc_home.json`).
  `product/ui/gen_ribbon.py` is multi-page: `--layout` selects the page, and its generated children
  are spliced between `<!-- product:Data-begin/end -->` markers of `notebookbar_office.ui`. Home and
  Data both live in the file, and regenerating either one leaves the other and `scalc.suppr` unchanged
  (unit-tested). Regenerate with:

  ```
  python3 -I product/ui/gen_ribbon.py --layout product/ui/calc_data.json --ui sc/uiconfig/scalc/ui/notebookbar_office.ui --suppr solenv/sanitizers/ui/modules/scalc.suppr
  product/dev/lo-make.sh sc.build
  ```

- **Dropdown pattern** (Other Sources, What-If, Statistics): a `.uno:` command with a `Popup`
  node (`ResourceMenuController` on a `sc/uiconfig/scalc/popupmenu/*.xml`) and a `ToolBox` node
  (`GenericPopupToolbarController`) in `Controller.xcu`, plus a label in `CalcCommands.xcu`. The
  .ui `label` property is ignored when a command is set, so the label must be in the xcu.
- **Split recipe** (Refresh, Group, Ungroup): the body needs its own command, because a toolbar
  controller on the original command would change every other toolbar. So each split has a new
  Data-only slot (`FID_DATA_REFRESH`, `FID_DATA_GROUP`, `FID_DATA_UNGROUP`, in `sc.hrc` after
  `FID_HOME_MERGE_CENTER`) that reuses the original's state and execute code (`cellsh.sdi`,
  `cellsh.cxx`, `cellsh1.cxx`, `cellsh2.cxx`), and a popup command (`...Menu`) opened by the arrow.
  **Invalidation rule**: every place that invalidates the original slot must also invalidate the
  new slot, or the button keeps a stale enabled/disabled state. The mirrors are
  `tabview3.cxx` (Refresh, Ungroup) and `olinefun.cxx` (Ungroup). A unit test scans `sc/source` for
  every `Invalidate(<original>)` and requires the mirror in the same file.
- **Placeholder slots** = always-disabled state: each placeholder is a real slot (`sc.hrc`,
  `cellsh.sdi`) with a state method that always calls `DisableItem` and no execute method, so the
  toolbar greys it out. (Without a slot, the toolbar would re-enable the button: see
  `sfx2/source/sidebar/ControllerFactory.cxx`.) This is also the scaffold of each future feature:
  to implement one, follow the recipe below. Placeholder slot ids live in the fork-reserved block
  `SID_NEW_SLOTS+380..+399` (ceiling +424), not in the ids upstream hands out next.
- **How to implement a placeholder**:
  1. In `sc/sdi/scalc.sdi`, flip `MenuConfig`, `ToolBoxConfig` and `AccelConfig` back to `TRUE` (they
     are `FALSE` while the command does nothing; `ReadOnlyDoc` is already `FALSE`).
  2. In `sc/sdi/cellsh.sdi`, give the row an `ExecMethod` (Data commands usually live in
     `cellsh2.cxx` `ExecuteDB`) and a real `StateMethod` (`GetDBState` where it fits).
  3. Remove the slot from the always-`DisableItem` case list in `cellsh.cxx` and implement Execute.
     Import data through `ScDBDocFunc::DoImport` so that Refresh can re-import the range later.
  4. In `CalcCommands.xcu`, remove "(not available yet)" from the command's `TooltipLabel`.
  5. Remove the slot from `PLACEHOLDERS` / `PLACEHOLDER_SLOTS` in
     `product/tests/test_calc_data_ui.py` and from the placeholder list in the UITest
     `sc/qa/uitest/calc_tests/notebookbarOffice.py`; add tests for the new behavior.
- **From Database prerequisites**: `autogen.input` has `--disable-postgresql-sdbc`, `--without-java`
  and `--disable-firebird-sdbc`. Enabling PostgreSQL means a reconfigure and a large rebuild. The
  MariaDB/MySQL connector is already built.
- **Icons**: `product/icons/manifest.json` entries named after the lowercased command (resolved
  from the boost theme by command name, no icon key in the layout). A command is only in the image
  list when its `*Commands.xcu` entry has `Properties` = 1 (the image flag); a unit test checks this
  for every command on the Data and Home pages.

Other upstream files touched: `Controller.xcu`, `CalcCommands.xcu`, `sc/UIConfig_scalc.mk`
(popup menus), `sc/inc/sc.hrc`, `sc/sdi/{cellsh,scalc}.sdi`, `sc/source/ui/view/{cellsh,cellsh1,cellsh2,tabview3}.cxx`,
`sc/source/ui/docshell/olinefun.cxx`, `scalc.suppr`.

## 4. Tests and checks

Counts after the Data slice: 84 product unit tests, 12 UITests in
`sc/qa/uitest/calc_tests/notebookbarOffice.py` (Home and Data together).

- `python3 -I -m unittest discover -s product/tests -t .`: layout vs design (sections, captions,
  width savers), "office .ui == upstream + Home + Data", labels and controllers of every command,
  split recipe (menus, slots, invalidation mirrors), placeholders (label, tooltip, disabled slot with no
  execute path), suppr entries, and icon coverage of every Data button.
- `product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.<test>` (names must be full, one at
  a time): all sections and toolboxes present; placeholders have a slot that is always disabled and
  does nothing when dispatched; Group/Ungroup follow the selection and really group; Refresh without a
  database range does nothing; a single status listener kept on `.uno:DataUngroup` is told that Group
  enabled it (olinefun path) and that a selection change disabled it (tabview3 path); the same for
  `.uno:HomeMergeCenter` across a selection change.
- `product/dev/check-ui.sh sc/uiconfig/scalc/ui/notebookbar_office.ui`: gla11y and lint, 0 new
  warnings or fatals.
- Width is checked by screenshot (1920, 1600, 1366 px, dark and light), not by a unit test.

## 5. Decisions made with the user during the work

- All of Excel's Data buttons, even those LibreOffice cannot do yet; those stay as greyed
  placeholders instead of being left out.
- Standard Filter leaves the tab (Excel has none), Statistics gets its own section (Analyze).
- "From Database" instead of Excel's "From Access": the future implementation targets PostgreSQL.
- "Tabbed Office" stays a separate variant; the original Tabbed is not replaced.
- Placeholders are greyed through real always-disabled slots (a small, deliberate C++ cost) rather
  than changing the shared toolbar code.
- To fit 1920 px, Sort A-Z, Sort Z-A, Shuffle and Edit Links are icon-only (Excel's Sort buttons are).

## 6. Known limitations and next steps

- **Width**: all 8 sections fit at 1920 px (about 100 px to spare, measured with en-US labels; translated labels may push Outline and Analyze
  behind ">>"). At 1600 px the first five sections
  (up to Data Tools) are visible and Forecast, Outline and Analyze are behind ">>". At 1366 px only
  Get External Data, Get & Transform, Connections and Sort & Filter are visible. Excel instead folds
  group by group into dropdown buttons. If more width is ever needed, Insert Sheet from File can go
  icon-only (its label is the widest in its column).
- `InsertSheetFromFile` used to need an explicit icon key. Root cause: its `CalcCommands.xcu` entry
  lacked the image flag (`Properties` = 1), so `framework/source/uiconfiguration/uicommanddescription.cxx`
  left it out of the image list. Fixed by adding the flag; the explicit key is gone.
- Group's state: `SID_OUTLINE_MAKE` is never invalidated by upstream code that we found, and the
  mirrored `FID_DATA_GROUP` inherits that. Known: the listener test saw a push after a selection
  change, so the button does refresh then, by some other invalidation. Not known: which one, and
  whether every selection change that should enable Group triggers it.
- Other Sources > Streams only appears in experimental mode.
- The status-listener UITests prove that the frame pushes fresh states to a long-lived listener
  after a group or selection change. They cannot attribute a push to a single `Invalidate()` mirror:
  in a control run a listener on `.uno:DataGroup` (which has no mirror) also received a push after a
  selection change, so some other invalidation exists too.
- Labels are en-US only; the new strings need Spanish translations before shipping.
- Next steps: implement the placeholders one by one, replacing the always-disabled state with real
  behavior. **From Database** first, by enabling LibreOffice's PostgreSQL SDBC driver in the build,
  then Recent Sources and Connections (both can reuse the database range and link lists), Flash Fill,
  Reapply (re-run the last filter), Relationships and Manage Data Model, Forecast Sheet.

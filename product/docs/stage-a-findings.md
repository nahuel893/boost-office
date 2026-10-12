# Stage A spike findings

Each section records the question, what was tried, the observed result and the decision.
Spec: /home/nh/office-boost/docs/superpowers/specs/2026-10-12-calc-home-redesign-design.md §6.

## 0a Declarative dropdown menus

Decision: P3

Question: can a ribbon button open a dropdown menu without C++ or a new .uno: slot?

Tried: in notebookbar_office.ui, set `btnHomeRowOperations` (GtkMenuToolButton) `action-name` to
`private:resource/popupmenu/row_operations`, with label "Rows" and icon `cmd/lc_insertrowsbefore.png`.
Built sc, checked in the GUI (Tabbed Office, isolated profile). P2 was not needed and not probed.

Observed (human click test):
- (a) Icon shows (third icon of the Cells group top row, with an arrow). The label "Rows" is not
  visible because that toolbox is icon-only; the label could not be observed there. Task 6 places
  these buttons in "large" and "small-label" toolboxes and verifies the label by screenshot.
- (b) Enabled (renders normal, unlike the greyed neighbour "Merge and Center Cells").
- (c) Clicking the button or its arrow opens the Rows menu.
- (d) "Insert Rows Above" inserts a row.

Screenshot: /mnt/games/libreoffice/assets/previews/spike-0a-p3.png

Probe edits were reverted before commit.

## 0b Theme engine reach under gtk3

## 0c Custom scheme switching with the system

## 0d Runtime packaging (icon zip drop-in, configuration-only extension)

## 0e UITest access to notebookbar widgets

Question: can a UITest reach widgets of a notebookbar by id after `.uno:ToolbarMode`?

Tried: switch with `.uno:ToolbarMode?Mode:string=notebookbar_office.ui`, then
`getTopFocusWindow().getChild("phbHome")` and check state `Visible`.

Result: YES.
- Before the variant existed (RED): `getChild("phbHome")` raised "Could not find child
  with id: phbHome" (children listed were only the sidebar/grid/input bar), so no
  fallback notebookbar was loaded and the test was not a false pass.
- After adding the variant (GREEN): `notebookbarOffice.NotebookbarOffice.test_office_variant_loads`
  PASS and `test_switch_back_to_compact` PASS (`NewDocSection`, unique to
  notebookbar_compact.ui, is reachable after switching back).

Decision: later tasks may assert notebookbar content through `getChild` by widget id.
Note: on failure, the UITest log ends with an unrelated Python 3.14 traceback-cleaning
error from UNO exceptions; the real cause is the `Could not find child` line above it.

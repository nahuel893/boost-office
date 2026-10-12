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

Probe: scheme "Boost Probe" (one loud color per ThemeColors role), tint 255, Tabbed Office,
dark appearance, gtk3. Screenshot: /mnt/games/libreoffice/assets/previews/spike-0b-probe-dark.png
(colors sampled from pixels).

| Ribbon part | Probe color | Role |
|-------------|-------------|------|
| Ribbon background | magenta | Window |
| Tab strip background | magenta | Window |
| Active tab | cyan (0,255,255) | Base |
| Inactive tab text, group captions, plain button labels | dark navy | WindowText (not fully certain vs ButtonText) |
| Font name / size combo field | cyan (0,255,255) | Base, not Field (light cyan) |
| Combo dropdown-arrow part, Number format combo | yellow | Button |
| Combo text ("General") | maroon | ButtonText |
| Separators between sections | cyan | Base |
| Formula bar, sheet tab | cyan | Base |
| Status bar | magenta | Window |
| Row/column header (selected) | orange | Accent |
| Menu bar | not present in Tabbed Office | n/a |

Gaps for stage B (the scheme alone cannot style these):
- Field is not used by the ribbon combos; they follow Base, so a field-vs-ribbon contrast cannot be set separately.
- Separators follow Base, not Separator.
- Inactive-tab text and captions cannot be told apart from ButtonText by role.
- Toolbox buttons stay transparent over Window; there is no Face-colored button background.

Menu, hover and pressed states: not checked in stage A spikes (no human check); to be verified on the Boost scheme screenshots in Tasks 9-10.

## 0c Custom scheme switching with the system

Probe: ApplicationAppearance=0 (follow the system), scheme "Boost Probe", run under
LO_GTK_THEME=adw-gtk3 (light) and adw-gtk3-dark (dark).
Screenshots: /mnt/games/libreoffice/assets/previews/spike-0c-system-light.png and
/mnt/games/libreoffice/assets/previews/spike-0c-system-dark.png

Result: NO, the custom scheme does not follow the system light/dark switch. Ribbon
colors are identical in both shots (magenta Window, cyan Base, yellow Button); only
font metrics differ. Explicitly set colors do not follow the OS
(svtools/source/config/colorcfg.cxx:628-641). Decision: Task 10 must ship separate
light and dark schemes and choose by appearance, not rely on auto-switching.

## 0d Runtime packaging (icon zip drop-in, configuration-only extension)

Probe: images_probe.zip (red cmd/sc_bold.png 16px, cmd/lc_paste.png 24px, cmd/32/paste.png)
dropped into instdir/share/config/, selected with SymbolStyle=probe; probe-scheme.oxt
(configuration-data only, ColorSchemes.xcu) installed with unopkg into the dev profile.
Screenshot: /mnt/games/libreoffice/assets/previews/spike-0b-probe-dark.png

Result: both work.
- Icon zip: YES. Bold shows a red 16 px square and Paste a red 24 px square (icon_size 3 = 24 px).
- Fallback: YES. All other icons still render from Colibre (dark).
- Extension: YES. `unopkg add -f` exits 0, `unopkg list` shows org.boost.probe-scheme, and the
  "Boost Probe" scheme applies when selected by name.

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

## Validation

Branch feature/calc-home-redesign at 904266ebd. Tabbed Office variant, Boost Light / Boost Dark
schemes, boost / boost_dark icon themes.

### Automatic checks (Step 1)

- `python3 -I -m unittest discover -s product/tests -t .`: 36 tests, OK.
- `product/dev/check-ui.sh sc/uiconfig/scalc/ui/notebookbar_office.ui`: exit 0.
- UITests (module notebookbarOffice.NotebookbarOffice), all PASS:
  test_office_variant_loads, test_switch_back_to_compact, test_home_sections_and_toolboxes,
  test_ui_picker_lists_office_variant, test_ui_picker_hides_office_variant_in_writer.
- `git diff --stat 62abc2329664 -- 'sc/uiconfig/scalc/ui/notebookbar*.ui'` lists only
  notebookbar_office.ui (new file); no other notebookbar*.ui changed.

### Screenshots

Directory: /mnt/games/libreoffice/assets/previews/
- Width test, dark: final-dark-1920.png, final-dark-1366.png, final-dark-1024.png
- Width test, light: final-light-1920.png, final-light-1366.png, final-light-1024.png
- Icons sheet: step3-icons-sheet.png (contact sheet; dryrun-icons-sheet.png is the earlier dry run)
- Colors: step4-colors-dark.png, step4-colors-light.png, step4-colors-both.png
- Baselines: baseline-tabbed-dark.png, baseline-tabbed-light.png, baseline-compact-dark.png,
  baseline-compact-light.png

### Width result

Collapse: YES. Sections collapse into the ">>" overflow instead of clipping.

| Shot | All 8 sections | In ">>" overflow | Overlap / cut |
|------|----------------|------------------|---------------|
| dark 1920 | yes | none | none in the ribbon (a dark frame outline surrounds the top ~550 px of the window, probably a screenshot/window artifact; not investigated) |
| dark 1366 | no | Styles, Cells, Editing | none |
| dark 1024 | no | Styles, Cells, Editing | none |
| light 1920 | yes | none | none |
| light 1366 | no | Styles, Cells, Editing | none |
| light 1024 | no | Styles, Cells, Editing, and Number (wider light font metrics) | the capture caught the overflow popup open; it covers the ribbon's lower part and shows the Number section cut at its left edge; behind it Alignment's third row is hidden by the popup |

Visible at 1366 and 1024: Undo, Clipboard, Font, Alignment, Number (Number moves into the
overflow in light 1024). No button is cut mid-glyph in the resting ribbon.

### Stage B / follow-up list

From spec section 8:
- Office-like flat tabs with an accent underline, scoped to the ribbon.
- Caption color `text.secondary` (VCL label attributes support no color).
- Automatic light/dark switching of the scheme and the icon theme.
- The "~" menus, if still wanted.
- The ">>" collapse for the full Tabbed layout: works in stage A (see width result).

From "## 0b" (areas the scheme cannot style):
- Field role is not used by the ribbon combos (they follow Base).
- Separators follow Base, not Separator.
- Inactive-tab text and captions cannot be told apart from ButtonText by role.
- Toolbox buttons stay transparent over Window; no Face-colored button background.

Gaps found during stage A review and validation:
- Ribbon section separators are painted with BaseColor (SeparatorColor is ignored under gtk3),
  so they are faint on the Boost Light green.
- Custom schemes do not follow the system light/dark switch (see "## 0c").
- The Excel-style dark-green tab band needs C++.
- Table Styles (.uno:AutoFormat) is disabled without a cell range selected.
- Split-button main-half click (clicking the body of Insert/Delete/... instead of the arrow) is
  unverified.
- Menus, hover and pressed colors still need a human check.
- Translations for the new labels are pending.
- A stale notebookbar_office.ui stored for non-Calc apps is only remapped in the UI picker.
- Unexplained dark frame outline in final-dark-1920.png and an overflow popup caught open in
  final-light-1024.png: confirm they are capture artifacts.

### Known limitation

The dev build is en-US only (no `--with-lang`), so long translated labels are not checked yet.

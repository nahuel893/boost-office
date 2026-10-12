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

# Calc Home tab redesign (stage A + first stage B items)

Status: implemented on branch `feature/calc-home-redesign` (2026-10-12), validated with the user
screen by screen. This document is the reference for what changed, how it is built, and what is
still open. The next slice is the Data tab, built with the same tools.

Design sources (outside the repo, `/home/nh/office-boost/docs/`):
`superpowers/specs/2026-10-12-calc-home-redesign-design.md` (spec) and the annexes
`design/calc-home-{tab-layout,icons,palette,prototype}.txt`. Spike results and the validation
record are in `product/docs/stage-a-findings.md`.

## 1. What the user sees

### A new ribbon variant, "Tabbed Office" (Calc only)

- File: `sc/uiconfig/scalc/ui/notebookbar_office.ui`, a copy of the upstream Tabbed
  `notebookbar.ui` whose Home page is generated (section 3). All other tabs are still upstream.
- Registered as Calc mode `TabbedOffice` (`ToolbarMode.xcu`), listed in View > User Interface
  and in the User Interface picker dialog (Calc only; other apps map it to "Tabbed").
- LibreOffice's own "Tabbed" and every other variant are unchanged.

### Home tab: 5 sections become Excel's 8

| Section | Content |
|---|---|
| Undo (new) | Undo, Redo (also kept in the quick access bar, by user decision) |
| Clipboard | Paste (large, split), Cut, Copy, Clone Formatting |
| Font | Row 1: font name, size. Row 2: B, I, U v, S, Grow, Shrink, Borders v, Fill v, Color v |
| Alignment | Top/Middle/Bottom, Left/Center/Right, indent -/+, Wrap Text, **Merge & Center** (split: body merges and centers, arrow opens the menu) |
| Number | Number format list, Currency v, %, 0.0 (thousands + 2 decimals), +/- decimals |
| Styles (new) | Conditional Formatting (medium 24 px, split), **Format as Table** (`.uno:AutoFormat`, medium 24 px), cell style list (a full-width "footer" row below the two buttons) |
| Cells | **Insert v**, **Delete v**, **Format v** (large) |
| Editing (new) | AutoSum, **Fill v**, **Clear v**, **Sort & Filter v** (large), **Find & Select v** (large) |

- Eight new dropdown menus (`.uno:HomeMergeMenu`, `HomeInsertMenu`, `HomeDeleteMenu`,
  `HomeFormatMenu`, `HomeFillMenu`, `HomeClearMenu`, `HomeSortFilterMenu`,
  `HomeFindSelectMenu`). They only group commands LibreOffice already had; menu contents are in
  `sc/uiconfig/scalc/popupmenu/home_*.xml`.
  Merge & Center is a split button: its body runs the Home-only slot `.uno:HomeMergeCenter`
  (same code path as `.uno:ToggleMergeCells`, so other toolbars are unchanged), and only the
  arrow opens `.uno:HomeMergeMenu` (Controller `Value`). The other seven menus are dropdown-only.
- Removed from Home (still in Format Cells): Subscript, Superscript, Spacing, Justify,
  Left-to-right / Right-to-left. The old "Home" overflow menu is gone (its items live in Editing).
- Large buttons use 32 px icons; section captions are plain (no italic), 90% size.
- Narrow windows: sections collapse from the right into a ">>" button (VclOptionalBox +
  priority classes).
- No new spreadsheet functionality: every button dispatches an existing LibreOffice command.

### Icons: "boost" and "boost_dark" themes

- 63 icons covering the Home tab, built from Microsoft's Fluent UI System Icons 1.1.344 (MIT,
  vendored in `product/icons/fluent/` with its LICENSE).
- Style: gray outline (#424242 / #D6D6D6) over a soft color fill (the Fluent "filled"
  silhouette, a touch of white stays) — yellow clipboard/format, blue copy/search/filter, light
  blue cells, red erase, green currency; badges carry one accent (green +, red x, amber bars,
  blue arrows).
- 16 px icons use the 20 px design with its empty padding trimmed (crisp, fills the slot); the
  custom "000" glyph has a hand-drawn 16 px version.
- Icons not in the themes fall back to Colibre (other tabs keep LibreOffice icons for now).

### Colors: "Boost Light" and "Boost Dark" schemes

- Shipped as a configuration-only extension (`org.boost.colorschemes`) with all 27 UI roles.
- Light: soft green surfaces (#E4F2E8, hover #D3E8DA, pressed #C3DECB), white fields and active
  tab. Dark: neutral gray (#2B2B2B). Every text pair meets WCAG AA (unit-tested).
- LibreOffice's green tint on Calc's ribbon is removed (`NotebookbarColorTransparency=255`).
- Cell selector (cursor frame, active header highlight, fill handle) uses the Calc green
  (`CalcCellFocus`: #1B7A3E light, #5CC27E dark).

### First stage B (C++) changes

- Thin border (ShadowColor role, #828282 / #7A7A7A) around themed entries and combo boxes, so
  drop-down lists read as such (applies to every themed gtk3 field, dialogs included).
- Selected tab stands out: white fill (light) / #454545 (dark) plus a 3 px Calc-green underline,
  kept on hover (every themed gtk3 notebook).
- Ribbon section separators painted with the SeparatorColor role (was BaseColor, invisible):
  gray #9E9E9E (light) / #6A6A6A (dark). The same gray now also draws menu and inactive borders.
- Compact ribbon rows (`vcl/source/window/toolbox.cxx`, `sfx2/source/sidebar/SidebarToolBox.cxx`): new opt-in
  `ToolBox::SetCompactHeight()`, enabled by every notebookbar toolbox (all apps and variants; not the sidebar,
  standard toolbars or dialogs), stops the line height from growing to the native combo/list/spin box height.
  Small icon rows on Home go from a 39 px to a 30 px pitch. Rows that hold a real combo box (font, number
  format, cell style) stay as tall as the combo itself (~35 px, set by the GTK theme).
- Scrollbar sliders visible at rest: ShadeColor (ShadowColor role, #828282 / #7A7A7A, about 3.9:1
  against the trough) instead of the surface color; 10 px painted thumb (was 8 px) with a 2 px
  transparent border. Hover/active stay WindowTextColor. Every themed gtk3 scrollbar is affected
  (dialogs, sidebar); overlay scrolling is untouched.

Light palette as shipped: surface #E4F2E8, hover #D3E8DA, pressed #C3DECB, separator #9E9E9E,
field border #828282, fields/menus/active tab white. Dark: surface #2B2B2B, separator #6A6A6A,
field border #7A7A7A, active tab #454545.

## 2. How to try it

```
product/dev/calc.sh light     # Tabbed Office, light (soft green)
product/dev/calc.sh dark      # Tabbed Office, dark
product/dev/calc.sh tabbed    # LibreOffice's original Tabbed, for comparison
```

The launcher (profile `/mnt/games/libreoffice/try-profile`, change with `--profile`) builds and
installs missing icon zips, (re)installs the scheme extension when it changed, writes the
profile, and starts Calc detached. Close Calc before switching modes.

## 3. How it is built (product tooling, `product/`)

| Tool | Purpose |
|---|---|
| `product/ui/gen_ribbon.py` + `product/ui/calc_home.json` | Generates the Home page XML from a JSON layout (sections, columns, toolboxes, items), splices it between `<!-- product:Home-begin/end -->` markers, and syncs `scalc.suppr`. Every other line of the .ui stays byte-identical to upstream. |
| `product/icons/build_theme.py` + `manifest.json` | Vendors Fluent glyphs, composes layers (fills, badges, highlights, knockouts, color-stripe clipping), renders 16/24/32 px light/dark PNGs, writes `links.txt`, zips and installs `images_boost*.zip`. |
| `product/themes/build_schemes.py` + `palette.json` | Tokens -> 27 UI roles + document colors -> `ColorSchemes.xcu` -> `boost-schemes.oxt`. |
| `product/dev/lo-make.sh` | gbuild under a cgroup memory cap (MemoryMax=7G, PARALLELISM=6); a full -j10 build froze the 14 GB machine. |
| `product/dev/profile.py`, `shot.sh`, `uitest.sh`, `check-ui.sh`, `calc.sh` | Isolated profiles, Sway/Hyprland screenshots (light uses a private GTK config), UITests by name, gla11y + lint, one-step launcher. |

To change the Home layout: edit `calc_home.json`, run
`python3 -I product/ui/gen_ribbon.py --layout product/ui/calc_home.json --ui sc/uiconfig/scalc/ui/notebookbar_office.ui --suppr solenv/sanitizers/ui/modules/scalc.suppr`,
then `product/dev/lo-make.sh sc.build`.

Other upstream files touched: `ToolbarMode.xcu` (mode), `Controller.xcu` + `CalcCommands.xcu`
(the eight menu commands), `sc/UIConfig_scalc.mk` (new .ui and popup menus), `scalc.suppr`,
`cui/inc/uimode.hrc`, `cui/source/dialogs/{uitabpage,uipickerdlg,welcomedlg}.cxx`,
`cui/uiconfig/ui/uitabpage.ui`, `extras/source/toolbarmode/notebookbar_office.png`,
`vcl/Package_toolbarmode.mk`, `vcl/unx/gtk3/custom-theme.cxx`.

## 4. Tests and checks

- `python3 -I -m unittest discover -s product/tests -t .` — 60 tests: profile writer, ribbon
  generator, "office .ui == upstream + layout", icon themes (coverage of every Home button, color
  stripe band empty, no light-theme gray in dark, crisp 16 px, trim never clips ink, fills,
  badges), color schemes (27 roles, WCAG AA, xcu/extension layout, cell cursor), launcher.
- `product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.<test>` — 6 UITests: variant loads,
  switching back to Tabbed Compact, every Home section/toolbox present, picker lists the variant
  in Calc, picker hides it in Writer, `.uno:HomeMergeCenter` merges and centers A1:B2.
- `product/dev/check-ui.sh sc/uiconfig/scalc/ui/notebookbar_office.ui` — the build's gla11y
  check (0 new warnings/fatals) and lint.

## 5. Decisions made with the user during the work

- Undo section kept on Home although Undo/Redo are in the quick access bar (Office familiarity).
- Number uses the original "0.0" button (it already formats with thousands separator).
- Layout aligned with Excel 365's Home: Strikeout kept, Format as Table added, AutoSum stacked
  with Fill and Clear; Grow/Shrink moved to the second Font row to save width.
- Dropdown menus need dedicated `.uno:` commands so their labels show (the .ui `label`
  property is ignored when a command is set).
- Icons with soft color fills (not monochrome), with a touch of white; bigger 16 px icons.
- Light theme in soft green; green cell selector; thin borders on drop-down fields.

## 6. Known limitations and next steps

- Other Calc tabs, Writer/Impress/Draw, dialogs and the status bar are not redesigned yet.
  Next: the Data tab, reusing `gen_ribbon.py`, the icon builder and the schemes.
- Translations: the dev build is en-US only; new labels need Spanish strings (and a
  `--with-lang` build) before shipping.
- Custom schemes do not follow the system light/dark switch (two schemes, chosen per profile).
- An Excel-style dark green tab band, and separate colors for the cell frame and the header
  highlight (dark text on dark green today), need more C++.
- Table Styles is disabled until a cell range is selected (LibreOffice behavior).
- The ">>" collapse folds Styles, Cells and Editing together at 1366 px; Excel folds group by
  group into dropdown buttons.
- Not yet checked by hand: clicking the body (not the arrow) of the new menu buttons; menu,
  hover and pressed colors.
- Product defaults (enable theme, select schemes/icons) are applied per profile today; shipping
  them belongs to the packaging work.

# Excel for Microsoft 365 (Windows) ribbon reference: Insert, Page Layout, Formulas, Review, View, Help (+ Data diff, brief tabs)

Date: 2026-10-15. Task R1 of `2026-10-15-calc-ribbon-tabs`. Research only; no code touched.

Target: Excel for Microsoft 365, Windows desktop, Current Channel, 2024+ "visual refresh" look
(rounded ribbon card, Fluent icons), window 1920 px wide.

## How to read this document

### Conventions

| Code | Meaning |
|---|---|
| **L** | Large: icon above label (label may wrap to 2 lines). |
| **S** | Small with label: 16 px icon left of label, stacked in a column of 3 (or 2). |
| **I** | Small icon-only (no label), stacked in a column. |
| **btn** | Plain button. |
| **tgl** | Toggle button (stays pressed). |
| **split** | Split button: body runs the default command, arrow opens a menu. In **L** size the body is the icon and the arrow sits under the label. |
| **dd** | Dropdown: whole control opens a menu/gallery (chevron after or under the label). |
| **gal** | In-ribbon gallery (inline items + scroll arrows + "more" arrow). |
| **chk** | Checkbox. |
| **combo** / **spin** | Combo box / spin box. |
| **launcher** | Dialog launcher (small arrow, group bottom-right). |

"Tooltip" = the bold title of the ScreenTip. When a tooltip was not verified it is written `= label`
(Excel normally uses the label, plus the shortcut in parentheses where one exists).

### Evidence keys (full URLs in the Appendix)

| Key | What it is | Version it shows |
|---|---|---|
| **[MSID]** | Microsoft "Office Fluent UI Command Identifiers", `Microsoft 365/Current Channel/excelcontrols.xlsx` (control IDs, types, group membership, ribbon order). | 365 Current Channel 2402 (commit 2024-03-18). Superset: contains variant groups that are never all shown at once. |
| **[BS]** | BetterSolutions.com tab pages and per-group crops. | 365 Windows, 2024+ refresh look; pages (c) 2026, mention 2024/2025 changes. Crops are at roughly 120% DPI scale and show the largest group layout. |
| **[ED]** | ExcelDemy "Excel Ribbon" guide, full-tab screenshots. | 365 Windows, 2023 (pre-refresh look), narrow window (~800-1080 px), so groups are reduced. |
| **[QA-INS]** | Microsoft Q&A thread 5811236, full Insert tab screenshot, 1912 px wide. | 365 Windows, 2026 refresh look, at ~1912 px. Best single reference for the 1920 px target. |
| **[MS-...]** | Microsoft Support / Tech Community / Insider pages and their screenshots. | 365 (dated per item). |

### Global facts

- **Tab order (365 Windows, default):** File, Home, Insert, Draw, Page Layout, Formulas, Data, Review, View,
  Automate, (Developer, only when enabled), Help. Verified by screenshot [QA-INS] (2026) and the Focus Cell
  screenshot [MS-FOCUS], order consistent with [MSID]. Draw appears by default on 365 (touch or not, see [ED]).
  Automate appears only when Office Scripts are enabled for the account (business/enterprise).
- **Add-ins moved to Home (2024):** the Insert > Add-ins group was replaced by a Home > Add-ins button
  ([MS-ADDINS], [BS] Insert page). Do not build an Insert > Add-ins group.
- **1920 px fit (estimate):** per-tab widths below were estimated from [BS] crop widths divided by 1.2.
  Insert verified at 1912 px [QA-INS]: every group at its largest layout. Page Layout and Help fit.
  Formulas (with Python), Review and View are at or above ~1920 px, so Excel probably reduces one or two
  groups at 1920 px; the reduced forms observed in [ED] / [MS] screenshots are recorded under each tab.

---

## 1. Insert

Groups, left to right (2026, [QA-INS] screenshot): **Tables | Illustrations | Controls | (Add-ins, see note) |
Charts | Tours (conditional, see note) | Sparklines | Filters | Links | Comments | Text | Symbols**.

### Tables

| Col | Control | Tooltip | Size | Kind | Menu (top level, in order) |
|---|---|---|---|---|---|
| 1 | PivotTable | = label | L | split | From Table/Range; From External Data Source; From Data Model; From Power BI (Microsoft) [org name may be shown] |
| 2 | Recommended PivotTables | = label | L | btn | - |
| 3 | Table | Table (Ctrl+T) | L | btn | - |
| 4 | Forms (conditional) | = label | L | dd | New Form (further items Preview/Edit/Send/Delete exist in [MSID], labels unverified) |

- No dialog launcher.
- Forms: shown for work/school accounts, Current Channel 2410+, workbook on OneDrive for work or school [MS-FORMS].
  Visible in [QA-INS]; absent in [BS] crop and [ED].
- Evidence: PivotTable menu from [MS-PIV] screenshot (`insert-mssupport-2.png`).

### Illustrations

| Col | Control | Tooltip | Size | Kind | Menu |
|---|---|---|---|---|---|
| 1 | Pictures | = label | L | dd | Place in Cell >; Place over Cells >. Each submenu: This Device...; Stock Images...; Online Pictures... ([MS-PIC]). A "Mobile Device" item exists in [MSID] (conditional, unverified). |
| 2 | Shapes | = label | L | dd (gallery) | Recently Used Shapes; Lines; Rectangles; Basic Shapes; Block Arrows; Equation Shapes; Flowchart; Stars and Banners; Callouts |
| 3 | Icons | = label | L | btn | - (opens the stock images/icons dialog) |
| 4, row 1 | 3D Models | = label | S | split ([MSID] `splitButton`; arrow drawn apart from label in [QA-INS]) | From a File...; From Online Sources... ([MS-3D]; newer builds may say "This Device..." / "Stock 3D Models...", unverified) |
| 4, row 2 | SmartArt | = label | S | btn | - |
| 4, row 3 | Screenshot | = label | S | dd | Available Windows (gallery); Screen Clipping |

- No dialog launcher.
- Reduced form ([MS-CHK] 2024 screenshot): Pictures, Shapes, Icons become S in a column of 3, next to the 3D Models/SmartArt/Screenshot column.

### Controls

| Col | Control | Tooltip | Size | Kind |
|---|---|---|---|---|
| 1 | Checkbox | = label | L | btn (formats the selected cells as in-cell checkboxes) |

- Group was first called "Cell Controls", renamed "Controls" in 2024 [BS]. Position (after Illustrations) verified
  by Microsoft's screenshot [MS-CHK] and [QA-INS]. Current Channel 2408+.

### Add-ins (do not build)

- Moved to Home in 2024 [BS][MS-ADDINS]. [QA-INS] still shows an empty, near-zero-width group captioned
  "A..." between Controls and Charts; this looks like a residual empty container (`GroupOfficeExtension` in
  [MSID]). Recommendation: omit it.

### Charts

| Col | Control | Tooltip | Size | Kind | Menu |
|---|---|---|---|---|---|
| 1 | Recommended Charts | = label | L | btn | - |
| 2, row 1 | (Column/Bar icon) | Insert Column or Bar Chart | I | dd (icon + chevron) | 2-D Column; 3-D Column; 2-D Bar; 3-D Bar; More Column Charts... |
| 2, row 2 | (Line/Area icon) | Insert Line or Area Chart | I | dd | 2-D Line; 3-D Line; 2-D Area; 3-D Area; More Line Charts... |
| 2, row 3 | (Pie/Doughnut icon) | Insert Pie or Doughnut Chart | I | dd | 2-D Pie; 3-D Pie; Doughnut; More Pie Charts... |
| 3, row 1 | (Hierarchy icon) | Insert Hierarchy Chart | I | dd | Treemap; Sunburst; More Hierarchy Charts... |
| 3, row 2 | (Statistic icon) | Insert Statistic Chart | I | dd | Histogram (Histogram, Pareto); Box and Whisker; More Statistical Charts... |
| 3, row 3 | (Scatter icon) | Insert Scatter (X, Y) or Bubble Chart | I | dd | Scatter; Bubble; More Scatter Charts... |
| 4, row 1 | (Waterfall icon) | Insert Waterfall, Funnel, Stock, Surface or Radar Chart | I | dd | Waterfall; Funnel; Stock; Surface; Radar; More Stock Charts... |
| 4, row 2 | (Combo icon) | Insert Combo Chart | I | dd | Clustered Column - Line; Clustered Column - Line on Secondary Axis; Stacked Area - Clustered Column; Create Custom Combo Chart... |
| 4, row 3 | (empty) | | | | |
| 5 | Maps | = label | L | dd | Filled Map; More Map Charts... ([BS] says "More Map Options") |
| 6 | PivotChart | = label | L | split | PivotChart; PivotChart & PivotTable |

- **Dialog launcher: yes** (opens Insert Chart > All Charts; "Change Chart Type" if a chart is active) [BS], visible in [QA-INS].
- The 8 chart-type controls are icon-only (no label) in a 3-column grid (3 + 3 + 2). Verified in [BS] and [QA-INS].
- Tooltip sources: "Insert Statistic Chart" [MS-BOX], "Insert Hierarchy Chart" [MS-TREE], "Insert Waterfall, Funnel,
  Stock, Surface or Radar chart" [MS-FUNNEL], "Insert Column or Bar Chart" [MS-COL]; Line/Area, Pie/Doughnut,
  Scatter (X, Y) or Bubble from [DUM] (Excel 2016 text); "Insert Combo Chart" is from memory, unverified.
- Sub-menu item lists from [BS] text; "Pareto" and the exact Combo item spelling are from memory, unverified.

### Tours (conditional)

| Col | Control | Tooltip | Size | Kind | Menu |
|---|---|---|---|---|---|
| 1 | 3D Map | = label | L | split | Open 3D Maps; Add Selected Data to 3D Maps (labels unverified; [BS] gives the old "Launch Power Map / Add Selected Data to PowerMap") |

- Microsoft: "You'll find the 3D Map button in the Tours group, on the Insert tab ..., next to the Charts group" [MS-3DMAP].
  Present in [ED] (2023) and [BS]. **Absent in [QA-INS] (2026, business account)**; 3D Maps is suspended in China
  [MS-CHINA]. Treat as present by default but low-confidence for the 2026 build.

### Sparklines

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Line | L | btn |
| 2 | Column | L | btn |
| 3 | Win/Loss | L | btn (label wraps "Win/" / "Loss") |

### Filters

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Slicer | L | btn |
| 2 | Timeline | L | btn |

### Links

| Col | Control | Tooltip | Size | Kind | Menu |
|---|---|---|---|---|---|
| 1 | Link | Link (Ctrl+K) (shortcut from [BS]) | L | split | recent files/locations list; Insert Link... |

### Comments

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Comment | L | btn (new threaded comment) |

### Text

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Text Box | L | tgl (no arrow in [BS] or [QA-INS]; a horizontal/vertical split variant exists in [MSID], probably East Asian languages only) | - |
| 2 | Header & Footer | L | btn | - |
| 3 | WordArt | L | dd (gallery) | WordArt styles gallery |
| 4 | Signature Line | L | split | Microsoft Office Signature Line...; Add Signature Services... |
| 5 | Object | L | btn | - |

- Reduced form ([ED]): whole group collapses to a single "Text" dropdown.

### Symbols

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Equation | L | split (arrow under label in [BS]/[QA-INS]; body/arrow split not verified) | built-in equations gallery (Area of Circle, Binomial Theorem, Expansion of a Sum, Fourier Series, ...); Insert New Equation; Ink Equation |
| 2 | Symbol | L | btn | - |

**Sources (Insert):** [BS-INS], [MSID], [QA-INS], [MS-CHK], [MS-PIV], [MS-PIC], [MS-3D], [MS-3DMAP], [MS-FORMS],
[MS-ADDINS], [MS-BOX], [MS-TREE], [MS-FUNNEL], [MS-COL], [DUM], [ED]. Images: `insert/insert-msqa-2.png` (full tab, 1912 px, 2026),
`insert/insert-msqa-1.png` (1542 px, reduced), `insert/insert-bettersolutions-1..11.png` (one per group),
`insert/insert-mstechcommunity-1.png` (Controls group, Microsoft), `insert/insert-mssupport-1.png`, `insert/insert-mssupport-2.png`
(PivotTable split menu, Microsoft), `insert/insert-exceldemy-1.png` (2023, narrow).

**Confidence (Insert):** group order, sizes and stacking verified by a 1912 px 365 screenshot. Uncertain: Tours
presence in current builds; 3D Models and 3D Map menu labels; Equation split vs dropdown; Forms menu items beyond
"New Form"; most tooltips (`= label`).

---

## 2. Page Layout

Groups: **Themes | Page Setup | Scale to Fit | Sheet Options | Arrange**. Estimated full width ~1615 px: fits at 1920 px.

### Themes

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Themes | L | dd (gallery) | Office / built-in themes gallery; Browse for Themes...; Save Current Theme... |
| 2, row 1 | Colors | S | dd | built-in color sets; Customize Colors... |
| 2, row 2 | Fonts | S | dd | built-in font pairs; Customize Fonts... |
| 2, row 3 | Effects | S | dd | effect presets (Office, Office 2007-2010, Subtle Solids, ...) |

- No launcher. Reduced form ([ED]): Colors/Fonts/Effects become icon-only (I) with chevrons.

### Page Setup

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Margins | L | dd | Normal; Wide; Narrow; (Last Custom Setting when set); Custom Margins... |
| 2 | Orientation | L | dd | Portrait; Landscape |
| 3 | Size | L | dd | paper sizes; More Paper Sizes... |
| 4 | Print Area | L | dd | Set Print Area; Clear Print Area (Add to Print Area appears when a print area exists, per [MSID]) |
| 5 | Breaks | L | dd | Insert Page Break; Remove Page Break; Reset All Page Breaks |
| 6 | Background | L | btn (caption becomes "Delete Background" when a sheet background is set) | - |
| 7 | Print Titles | L | btn | - |

- **Launcher: yes** -> Page Setup dialog, Page tab.
- Reduced form ([ED]): Margins L, then two S columns of 3: (Orientation, Size, Print Area) and (Breaks, Background, Print Titles).

### Scale to Fit

| Row | Control | Kind | Values |
|---|---|---|---|
| 1 | Width: | label + combo | Automatic; 1 page ... 9 pages; More Pages... |
| 2 | Height: | label + combo | Automatic; 1 page ... 9 pages; More Pages... |
| 3 | Scale: | label + spin | 100% (steps of 5%) |

- Each row has a small icon left of its label. **Launcher: yes** -> Page Setup, Page tab.

### Sheet Options

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 (conditional) | Sheet Right-to-Left | L | tgl |
| 2 | "Gridlines" (column header label), then View, Print | S | label + 2 chk (View checked by default) |
| 3 | "Headings" (column header label), then View, Print | S | label + 2 chk (View checked by default) |

- **Launcher: yes** -> Page Setup, Sheet tab.
- Sheet Right-to-Left: shown in [BS] (labelled "Added in 365"), absent in [ED] (en-US). Likely shown only when a
  right-to-left editing language is enabled (older Microsoft/ExcelDemy statements); unverified for 365.

### Arrange

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Bring Forward | L | split | Bring Forward; Bring to Front |
| 2 | Send Backward | L | split | Send Backward; Send to Back |
| 3 | Selection Pane | L | tgl | - |
| 4 | Align | L | dd | Align Left; Align Center; Align Right; Align Top; Align Middle; Align Bottom; Distribute Horizontally; Distribute Vertically; Snap to Grid; Snap to Shape; View Gridlines |
| 5 | Group | L | dd | Group; Regroup; Ungroup |
| 6 | Rotate | L | dd | Rotate Right 90 deg; Rotate Left 90 deg; Flip Vertical; Flip Horizontal; More Rotation Options... |

- No launcher. Disabled unless a drawing object is selected. Reduced form ([ED]): one "Arrange" dropdown.

**Sources (Page Layout):** [BS-PL], [MSID], [ED]. Images: `page-layout/page-layout-bettersolutions-1..5.png` (one per group),
`page-layout/page-layout-exceldemy-1.png` (2023, narrow, reduced).

**Confidence (Page Layout):** verified by screenshot (per-group [BS] crops + [ED] full tab). Uncertain: Sheet
Right-to-Left visibility rule; Margins "Last Custom Setting" item; exact Rotate item text (degree sign).

---

## 3. Formulas

Groups: **Function Library | Python (conditional) | Defined Names | Formula Auditing | Calculation | Solutions (add-in only)**.
Estimated full width ~1920 px with Python, ~1715 px without: with Python, Excel probably reduces one group at 1920 px.

### Function Library

| Col | Control | Tooltip | Size | Kind | Menu |
|---|---|---|---|---|---|
| 1 | Insert Function | Insert Function (Shift+F3) | L | btn | - |
| (separator) | | | | | |
| 2 | AutoSum | = label | L | split | Sum; Average; Count Numbers; Max; Min; More Functions... |
| 3 | Recently Used | = label | L | dd | last 10 functions; Insert Function... |
| 4 | Financial | = label | L | dd | functions of the category; Insert Function... |
| 5 | Logical | = label | L | dd | same pattern |
| 6 | Text | = label | L | dd | same pattern |
| 7 | Date & Time | = label | L | dd | same pattern |
| 8 | Lookup & Reference | = label | L | dd | same pattern |
| 9 | Math & Trig | = label | L | dd | same pattern |
| 10 | More Functions | = label | L | dd | Statistical >; Engineering >; Cube >; Information >; Compatibility >; Web > |

- No launcher. A vertical separator follows Insert Function [BS crop].
- Reduced form ([ED], 2023): Insert Function L; then S columns of 3: (AutoSum, Recently Used, Financial),
  (Logical, Text, Date & Time), and an icon-only column (Lookup & Reference, Math & Trig, More Functions).
- [MSID] also lists an "Azure" category gallery under More Functions (not shown in [BS]); treat as conditional.

### Python (conditional)

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Insert Python | L | btn in [BS] crop (no arrow); [MSID] has it as a split with "Python in Excel options" / "Try Python samples" | - |
| 2, row 1 | Reset | S | split | Reset; Reset Runtime |
| 2, row 2 | Editor | S | btn | - |
| 2, row 3 | Initialization | S | btn | - |

- Group added Jan 2025 [BS]. Availability [MS-PY]: Enterprise/Business on Windows (Current Channel 2408+,
  Monthly Enterprise 2408+, Semi-Annual 2502+); Family/Personal preview only; not on perpetual or free licences.

### Defined Names

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Name Manager | L | btn | - |
| 2, row 1 | Define Name | S | split | Define Name...; Apply Names... |
| 2, row 2 | Use in Formula | S | dd | defined names list; Paste Names... |
| 2, row 3 | Create from Selection | S | btn | - |

### Formula Auditing

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1, row 1 | Trace Precedents | S | btn | - |
| 1, row 2 | Trace Dependents | S | btn | - |
| 1, row 3 | Remove Arrows | S | split | Remove Arrows; Remove Precedent Arrows; Remove Dependent Arrows |
| 2, row 1 | Show Formulas | S | tgl (Ctrl+`) | - |
| 2, row 2 | Error Checking | S | split | Error Checking...; Trace Error; Circular References > |
| 2, row 3 | Evaluate Formula | S | btn | - |
| 3 | Watch Window | L | tgl | - |

- Reduced form ([ED]): column 2 becomes icon-only.

### Calculation

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Calculation Options | L | dd | Automatic; Partial; Manual; (separator) Format Stale Values (toggle) |
| 2, row 1 | Calculate Now | S | btn (F9) | - |
| 2, row 2 | Calculate Sheet | S | btn (Shift+F9) | - |

- "Partial" is the renamed "Automatic Except for Data Tables" (also pauses Python) [MS-STALE][SPP]; "Format Stale Values"
  is on this menu [MS-STALE]. Older docs ([BS]) still say "Automatic except for Data Tables". Item order from [MSID].
- Reduced form ([ED]): Calculate Now / Calculate Sheet icon-only.

### Solutions (do not build)

- Only when the Euro Currency Tools add-in is loaded: Euro Conversion, Euro Formatting (S) and a conversion combo [BS].

**Sources (Formulas):** [BS-FOR], [MSID], [MS-PY], [MS-STALE], [SPP], [ED]. Images: `formulas/formulas-bettersolutions-1..6.png`
(one per group), `formulas/formulas-exceldemy-1.png` (2023, narrow).

**Confidence (Formulas):** verified by screenshot for all groups. Uncertain: Insert Python button kind (button vs split);
the exact Calculation Options item text "Partial" (text sources only, no screenshot); exact layout at exactly 1920 px.

---

## 4. Review

Groups ([MSID] order, confirmed by [ED] and [MS-PERF] screenshot): **Proofing | Performance (conditional) | Accessibility |
Insights (retired?) | Language | Changes (conditional) | Comments | Notes | Protect | Ink**.
Estimated full width ~2000 px with all groups: at 1920 px Excel probably reduces some groups (see reduced forms).

### Proofing

| Col | Control | Tooltip | Size | Kind |
|---|---|---|---|---|
| 1 | Spelling | Spelling (F7) | L | btn |
| 2 | Thesaurus | = label | L | btn |
| 3 | Workbook Statistics | = label | L | btn |

- Reduced form ([ED]): three S rows in one column.
- The Microsoft Check Performance screenshot (`review-mssupport-1.png`, probably Excel for the web) shows only
  Spelling and Workbook Statistics.

### Performance (conditional)

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Check Performance | L | btn (opens Workbook Performance pane) |

- "Select Review > Check Performance" [MS-PERF]; Windows rollout from Current Channel (Preview) 2312 [MS-PERF].
  Group caption "Performance" seen in `review-mssupport-1.png` (likely web ribbon). Not shown in [BS] or [ED].

### Accessibility

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Check Accessibility | L | split | Check Accessibility; Alt Text; Format as Table >; Unmerge Cells; Accessibility Options (?); Accessibility Help (?) |

- Menu items from [MSID] control IDs (labels inferred; the last two unverified).

### Insights (probably obsolete)

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Smart Lookup | L | btn |

- Smart Lookup was retired from 1 January 2025 [MS-SL]. [BS] still shows the group; the Microsoft
  `review-mssupport-1.png` does not. Recommendation: omit, or keep last-priority.

### Language

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Translate | L | btn |

### Changes (conditional)

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Show Changes | L | btn (opens Changes pane) |

- "On the Review tab, select Show Changes" [MS-SHOWCH]. Shown (disabled for a local file) in [ED] 2023 and in
  `review-mssupport-1.png`; not in [BS] crops.

### Comments

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | New Comment | L | btn (Shift+F2 per [BS]) |
| 2 | Delete | L | btn ("Delete Comment" in the web screenshot) |
| 3 | Previous Comment | L | btn |
| 4 | Next Comment | L | btn |
| 5 | Show Comments | L | tgl (Comments pane) |

- Reduced form ([ED]): New Comment L, Delete L, then an icon-only column of 3 (Previous, Next, Show Comments).

### Notes

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Notes | L | dd | New Note; Previous Note; Next Note; Show/Hide Note; Show All Notes; Convert to Comments |

### Protect

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Protect Sheet | L | btn |
| 2 | Protect Workbook | L | tgl |
| 3 | Allow Edit Ranges | L | btn |
| 4 | Unshare Workbook | L | btn (disabled unless a legacy shared workbook is open) |

### Ink

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Hide Ink | L | split ([MSID] `HideInkSplitButton`) | Hide Ink; Delete All Ink on Sheet; Delete All Ink in Workbook |

- [MSID] also has "Start Inking" (pen/touch devices only); not shown in [BS] or [ED].

**Sources (Review):** [BS-REV], [MSID], [ED], [MS-PERF], [MS-SHOWCH], [MS-SL]. Images: `review/review-bettersolutions-1..8.png`
(one per group), `review/review-exceldemy-1.png` (2023, narrow), `review/review-mssupport-1.png` (Microsoft; likely Excel for the web).

**Confidence (Review):** core groups verified by screenshot. Uncertain: whether Performance, Insights and Changes
are shown in a stock 2026 Windows build; Accessibility menu labels; layout at 1920 px.

---

## 5. View

Groups: **Sheet View | Workbook Views | Dark Mode (conditional) | Show | Zoom | Window | Macros**.
Estimated full width ~2050 px with Navigation and Focus Cell: at 1920 px Excel reduces some groups.

### Sheet View

| Row | Control | Size | Kind |
|---|---|---|---|
| 1 | (Switch Sheet View) | - | combo, full group width, shows "Default" |
| 2, item 1 | Keep | S | btn |
| 2, item 2 | Exit | S | btn |
| 2, item 3 | New | S | btn |
| 2, item 4 | Options | S | btn |

- Layout: combo on top, the four buttons in **one horizontal row** under it [BS]. Reduced form ([ED], [view-msqa-1]):
  the four become icon-only. Enabled only for files on OneDrive/SharePoint [BS]; otherwise shown disabled.

### Workbook Views

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Normal | L | tgl (radio-like) |
| 2 | Page Break Preview | L | tgl |
| 3 | Page Layout | L | tgl |
| 4 | Custom Views | L | btn |

- Reduced form ([ED], [view-msqa-1]): Normal and Page Break Preview L; Page Layout and Custom Views S in a column of 2.

### Dark Mode (conditional)

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Switch Modes | L | tgl |

- Shown only when the Office theme is Black (or system setting with Windows dark) [MS-DARK]; Current Channel since 2025.
  Sits between Workbook Views and Show (`view-mstechcommunity-3.png`).

### Show

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Navigation | L | tgl (Navigation pane) | - |
| 2, row 1 | Ruler | S | chk (enabled only in Page Layout view) | - |
| 2, row 2 | Gridlines | S | chk | - |
| 2, row 3 | Formula Bar | S | chk | - |
| 3, row 1 | Headings | S | chk | - |
| 3, row 2 | Data Type Icons | S | chk | - |
| 3, row 3 | Focus Cell | S | split tgl | Focus Cell; Focus Cell Color >; Show Auto-Highlight |

- Verified by Microsoft screenshots [MS-FOCUS] (`view-mstechcommunity-1.png`, `-2.png`) and [view-msqa-1] (2025).
  [BS] crop is older (2 x 2 checkboxes, no Navigation/Focus Cell). Focus Cell: Beta 2410, now Current Channel.
- Reduced form ([ED] 2023): whole group collapses to one "Show" dropdown.

### Zoom

| Col | Control | Size | Kind |
|---|---|---|---|
| 1 | Zoom | L | btn (Zoom dialog) |
| 2 | 100% | L | btn |
| 3 | Zoom to Selection | L | btn |

### Window

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | New Window | L | btn | - |
| 2 | Arrange All | L | btn | - |
| 3 | Freeze Panes | L | dd | Freeze Panes (Unfreeze Panes when frozen); Freeze Top Row; Freeze First Column |
| 4, row 1 | Split | S | tgl | - |
| 4, row 2 | Hide | S | btn | - |
| 4, row 3 | Unhide | S | btn | - |
| (separator) | | | | |
| 5, row 1 | View Side by Side | S | tgl | - |
| 5, row 2 | Synchronous Scrolling | S | tgl | - |
| 5, row 3 | Reset Window Position | S | btn | - |
| 6 | Switch Windows | L | dd | list of open windows |

- Reduced form ([ED]): New Window, Arrange All, Freeze Panes become S (column of 3); columns 4 and 5 icon-only.

### Macros

| Col | Control | Size | Kind | Menu |
|---|---|---|---|---|
| 1 | Macros | L | split | View Macros; Record Macro...; Use Relative References |

**Sources (View):** [BS-VIEW], [MSID], [ED], [MS-FOCUS], [MS-DARK], Microsoft Q&A 5618194. Images: `view/view-bettersolutions-1..6.png`,
`view/view-mstechcommunity-1.png` (Show group with Navigation/Focus Cell), `view/view-mstechcommunity-2.png` (Focus Cell menu),
`view/view-mstechcommunity-3.png` (Dark Mode group), `view/view-msqa-1.png` (2025 user screenshot), `view/view-exceldemy-1.png` (2023, narrow).

**Confidence (View):** verified by screenshot. Uncertain: exact reduction pattern at 1920 px; whether Focus Cell is a
split or a toggle with a separate arrow (screenshots show one rounded control with a separate chevron, consistent with split).

---

## 6. Help

Groups: **Help | Community**. Small tab; fits.

| Group | Col | Control | Size | Kind |
|---|---|---|---|---|
| Help | 1 | Help | L | btn (F1) |
| Help | 2 | Contact Support | L | btn |
| Help | 3 | Feedback | L | btn |
| Help | 4 | Show Training | L | btn |
| Help | 5 | What's New | L | btn |
| Community | 1 | Community | L | btn |
| Community | 2 | Excel Blog | L | btn |

- No launchers, no menus. [MSID] group IDs: `GroupHelpAndSupport` (caption "Help"), `GroupExcelCommunity` (caption "Community").

**Sources (Help):** [BS-HELP], [MSID], [ED]. Images: `help/help-bettersolutions-1.png`, `help/help-bettersolutions-2.png`, `help/help-exceldemy-1.png`.

**Confidence (Help):** verified by screenshot (2023 and 2024+ looks agree).

---

## 7. Data: what 365 has that Excel 2016 did not (short diff)

Current 365 groups: **Get & Transform Data | Queries & Connections | Data Types | Sort & Filter | Data Tools | Forecast | Outline | Analysis (add-ins only)**.

The Excel 2016 column is from memory plus the legacy group IDs still listed in [MSID] (`GroupGetExternalData`,
`GroupPowerQueryData`, `GroupConnections`); it was not checked against a 2016 screenshot.

| Area | Excel 2016 | Excel 365 (2024+) |
|---|---|---|
| Import group | "Get External Data" (From Access, From Web, From Text, From Other Sources, Existing Connections) and/or "Get & Transform" (New Query, Show Queries, From Table, Recent Sources) | **Get & Transform Data**: Get Data (L, dd: From File, From Database, From Azure, From Online Services, From Other Sources, Combine Queries, Launch Query Editor [BS wording], Data Source Settings..., Query Options); S column: From Text/CSV, From Web, From Table/Range; S column: From Picture (dd: Picture From File, Picture From Clipboard), Recent Sources, Existing Connections |
| Connections group | "Connections": Refresh All, Connections, Properties, Edit Links | **Queries & Connections**: Refresh All (L, split: [Refresh All, from memory]; Refresh; Refresh Status; Cancel Refresh; Connection Properties... [BS]); S column: Queries & Connections (tgl, pane), Properties, **Workbook Links** (replaces Edit Links [MS-WBL]; [BS] crop still shows "Edit Links") |
| Data Types | none | **Data Types**: in-ribbon gallery (Stocks, Geography; Currencies in some builds [ED]; organisation types when available) with scroll/more arrows |
| Data Tools | Text to Columns, Flash Fill, Remove Duplicates, Data Validation, Consolidate, What-If Analysis, Relationships, Manage Data Model | Text to Columns (L); S column: Flash Fill, Remove Duplicates, Data Validation (split); S column: Consolidate, Relationships, Manage Data Model. What-If is in Forecast. "Analyze Data" is on Home in 365, not here. |
| Forecast | What-If Analysis, Forecast Sheet | unchanged (What-If Analysis dd: Scenario Manager, Goal Seek, Data Table; Forecast Sheet) |
| Sort & Filter, Outline | | unchanged; Outline has a launcher |

**Sources (Data):** [BS-DATA], [MSID], [ED], [MS-WBL]. Images: `data/data-bettersolutions-1..4.png`, `data/data-exceldemy-1.png`.
**Confidence (Data):** verified by screenshot except the Get Data menu items and the Data Types gallery content (text only).

---

## 8. Brief: other tabs (group captions and main controls)

Sources: [BS] pages for each tab, [MSID] groups, [ED] screenshots where listed. Captions are from [BS] text unless noted.

| Tab | Groups (left to right) and main controls |
|---|---|
| **Draw** | Drawing Tools (Select, Lasso Select, pens gallery with Eraser, Pen, Pen, Highlighter, Add Pen; Draw with Touch on touch devices) / Convert (Ink to Shape, Ink to Math) / Replay (Ink Replay) / Help (Ink Help). Screenshot: `brief/draw-exceldemy-1.png`, `brief/draw-bettersolutions-1.png`. |
| **Automate** (Office Scripts licences only) | Office Scripts (New Script dd: Create in Code Editor, Create from Recording; View Scripts dd: Recent Scripts, Scripts from this Workbook, Samples) / Office Scripts Gallery (gallery) / Power Automate (Automation Templates). Screenshot: `brief/automate-bettersolutions-1.png`. Older layout: Scripting Tools (Record Actions, New Script) / Office Scripts (gallery, All Scripts) / Power Automate (Automate a Task). |
| **Developer** (hidden by default) | Code (Visual Basic L, Macros L; S column: Record Macro, Use Relative References, Macro Security) / Add-ins (Add-ins, Excel Add-ins, COM Add-ins, all L) / Controls (Insert L dd: Form Controls + ActiveX Controls; Design Mode L tgl; S column: Properties, View Code, Run Dialog) / XML (Source L; S column: Map Properties, Expansion Packs, Refresh Data; S column: Import, Export). Screenshot: `brief/developer-exceldemy-1.png`. |
| **Picture Format** | Adjust (Remove Background, Corrections, Color, Artistic Effects, Transparency, Compress Pictures, Change Picture, Reset Picture; "Place in Cell" added 2023+ [MS-PIC]) / Picture Styles (gallery, Picture Border, Picture Effects, Picture Layout; launcher) / Accessibility (Alt Text) / Arrange (Bring Forward, Send Backward, Selection Pane, Align, Group, Rotate) / Size (Crop split, Height, Width; launcher). Text only. |
| **Shape Format** | Insert Shapes (shapes gallery, Edit Shape, Text Box) / Shape Styles (gallery, Shape Fill, Shape Outline, Shape Effects; launcher) / WordArt Styles (gallery, Text Fill, Text Outline, Text Effects; launcher) / Accessibility (Alt Text) / Arrange (as above) / Size (Height, Width; launcher). Text only. |
| **Chart Design** | Chart Layouts (Add Chart Element dd, Quick Layout dd) / Chart Styles (Change Colors dd, styles gallery) / Data (Switch Row/Column, Select Data) / Type (Change Chart Type) / Location (Move Chart). Text only. |
| **Format** (chart) | Current Selection (Chart Elements combo, Format Selection, Reset to Match Style) / Insert Shapes (gallery, Change Shape) / Shape Styles (gallery, Shape Fill, Shape Outline, Shape Effects; launcher) / WordArt Styles (gallery, Text Fill, Text Outline, Text Effects; launcher) / Accessibility (Alt Text) / Arrange / Size (Height, Width; launcher). Tab caption on screen is "Format"; [BS] calls it "Chart Format". Text only. |
| **Table Design** | Properties (Table Name: box, Resize Table) / Tools (Summarize with PivotTable, Remove Duplicates, Convert to Range, Insert Slicer) / External Table Data (Export dd, Refresh split, Properties, Open in Browser, Unlink) / Table Style Options (chk: Header Row, Total Row, Banded Rows, First Column, Last Column, Banded Columns, Filter Button) / Table Styles (gallery). [BS] writes "Summarize to PivotTable"; "Summarize with PivotTable" is from memory. Text only. |
| **PivotTable Analyze** | PivotTable (PivotTable Name box, Options split) / Active Field (Active Field box, Field Settings, Drill Down, Drill Up, Expand Field, Collapse Field; Show Details added 2024) / Group (Group Selection, Ungroup, Group Field) / Filter (Insert Slicer, Insert Timeline, Filter Connections) / Data (Refresh split, Change Data Source split) / Actions (Clear dd, Select dd, Move PivotTable) / Calculations (Fields, Items & Sets dd, OLAP Tools dd, Relationships) / Tools (PivotChart, Recommended PivotTables) / Show (Field List, +/- Buttons, Field Headers toggles). Text only. |
| **PivotTable Design** | Layout (Subtotals dd, Grand Totals dd, Report Layout dd, Blank Rows dd) / PivotTable Style Options (chk: Row Headers, Column Headers, Banded Rows, Banded Columns) / PivotTable Styles (gallery). Text only. |

### File backstage pages (left rail, top to bottom)

Home, New, Open, (separator), Get Add-ins, Info, Save, Save As (shown as "Save a Copy" when AutoSave is on; from memory),
Print, Share, Export, Publish, Close, (separator), Account, Feedback, Options. When the window is short, Feedback and
Options collapse into "More...". Verified by `brief/file-backstage-exceldemy-1.png` (2023: shows Account + More...) and [MSID]
backstage tab IDs (TabInfo, TabOfficeStart, TabRecent, TabSave, TabPrint, TabShare, TabPublish, TabHelp = Account, TabOfficeFeedback).
"Save as Adobe PDF" appears only with the Acrobat add-in.

---

## Appendix A: Sources

- [MSID] https://github.com/OfficeDev/office-fluent-ui-command-identifiers (file `Microsoft 365/Current Channel/excelcontrols.xlsx`, commit "CC identifiers version 2402", 2024-03-18)
- [BS-INS] https://bettersolutions.com/excel/ribbon/insert-tab.htm
- [BS-PL] https://bettersolutions.com/excel/ribbon/page-layout-tab.htm
- [BS-FOR] https://bettersolutions.com/excel/ribbon/formulas-tab.htm
- [BS-REV] https://bettersolutions.com/excel/ribbon/review-tab.htm
- [BS-VIEW] https://bettersolutions.com/excel/ribbon/view-tab.htm
- [BS-HELP] https://bettersolutions.com/excel/ribbon/help-tab.htm
- [BS-DATA] https://bettersolutions.com/excel/ribbon/data-tab.htm
- [BS] brief tabs: https://bettersolutions.com/excel/ribbon/draw-tab.htm, https://bettersolutions.com/excel/ribbon/developer-tab.htm,
  https://bettersolutions.com/excel/office-scripts/automate-tab.htm, https://bettersolutions.com/excel/illustrations/picture-format-tab.htm,
  https://bettersolutions.com/excel/illustrations/shape-format-tab.htm, https://bettersolutions.com/excel/charts/chart-design-tab.htm,
  https://bettersolutions.com/excel/charts/chart-format-tab.htm, https://bettersolutions.com/excel/tables/table-design-tab.htm,
  https://bettersolutions.com/excel/pivot-tables/pivottable-analyze-tab.htm, https://bettersolutions.com/excel/pivot-tables/pivottable-design-tab.htm,
  https://bettersolutions.com/excel/ribbon/contextual-tabs.htm, https://bettersolutions.com/excel/ribbon/file-backstage.htm
- [ED] https://www.exceldemy.com/learn-excel/parts/ribbon/
- [QA-INS] https://learn.microsoft.com/en-us/answers/questions/5811236/add-ins-group-is-missing-in-the-insert-tab
- [MS-CHK] https://techcommunity.microsoft.com/blog/excelblog/introducing-checkboxes-in-excel/4173561
- [MS-PIV] https://support.microsoft.com/en-us/excel/get-started/create-a-pivottable-to-analyze-worksheet-data
- [MS-PIC] https://support.microsoft.com/en-us/excel/insert-picture-in-cell-in-excel
- [MS-3D] https://support.microsoft.com/en-us/office/graphics-visuals/get-creative-with-3d-models
- [MS-3DMAP] https://support.microsoft.com/en-us/excel/get-started-with-3d-maps
- [MS-CHINA] https://support.microsoft.com/en-us/support/known-issues/excel-2d-map-charts-and-3d-maps-are-suspended-for-china
- [MS-FORMS] https://techcommunity.microsoft.com/blog/excelblog/announcing-the-new-microsoft-forms-integration-on-desktop/4356659
- [MS-ADDINS] https://support.microsoft.com/en-us/office/add-ins/view-manage-and-install-add-ins-for-excel-powerpoint-and-word,
  https://techcommunity.microsoft.com/blog/microsoft365insiderblog/access-and-explore-office-add-ins-in-word-excel-and-powerpoint-for-the-web-and-w/4221583
- [MS-BOX] https://support.microsoft.com/en-us/office/create-a-box-and-whisker-chart-62f4219f-db4b-4754-aca8-4743f6190f0d
- [MS-TREE] https://support.microsoft.com/en-us/excel/create-a-treemap-chart-in-office
- [MS-FUNNEL] https://support.microsoft.com/en-us/office/create-a-funnel-chart-ba21bcba-f325-4d9f-93df-97074589a70e
- [MS-COL] https://support.microsoft.com/en-us/excel/present-your-data-in-a-column-chart
- [DUM] https://www.dummies.com/article/technology/software/microsoft-products/excel/how-to-insert-a-chart-via-the-ribbon-in-excel-2016-140131
- [MS-PY] https://support.microsoft.com/en-us/office/python-in-excel-availability-781383e6-86b9-4156-84fb-93e786f7cab0
- [MS-STALE] https://support.microsoft.com/en-us/excel/stale-value-formatting
- [SPP] https://spreadsheetplanet.com/excel-glossary/calculation-modes/ (Partial = former "Automatic except for data tables"; read via search summary only)
- [MS-PERF] https://support.microsoft.com/en-us/excel/cleanup-cells-in-your-workbook,
  https://techcommunity.microsoft.com/blog/microsoft365insiderblog/make-your-workbooks-more-performant-with-check-performance-in-excel-for-windows/4224276
- [MS-SHOWCH] https://support.microsoft.com/en-us/excel/show-changes-that-were-made-in-a-workbook
- [MS-SL] https://support.microsoft.com/en-us/office/get-insights-into-what-you-re-working-on-with-smart-lookup-debf2083-5ac0-4739-8667-ae2467bec044
- [MS-FOCUS] https://techcommunity.microsoft.com/blog/microsoft365insiderblog/increase-ease-of-navigation-with-focus-cell-in-excel/4264531
- [view-msqa-1] https://learn.microsoft.com/en-us/answers/questions/5618194/unable-to-locate-or-activate-focus-cell-feature-in
- [MS-DARK] https://techcommunity.microsoft.com/blog/microsoft365insiderblog/reduce-eye-strain-with-dark-mode-in-excel-for-windows/4268752,
  https://support.microsoft.com/en-us/excel/dark-mode-in-excel
- [MS-WBL] https://support.microsoft.com/en-us/excel/manage-workbook-links

## Appendix B: reference images (local, never committed)

All under `/mnt/games/libreoffice/assets/excel-ref/`: `insert/` (17), `page-layout/` (6), `formulas/` (7), `review/` (10),
`view/` (11), `help/` (3), `data/` (5), `brief/` (5). File names follow `<tab>-<source>-<n>.<ext>`.

# Impress ribbon tabs like PowerPoint (Tabbed Office)

Status: **design, 2026-10-23 (written in task ID1, accepted by the controller); nothing is built yet.** Task I10
updates it with the build results. It follows `product/docs/writer-ribbon-tabs.md` section by section: section 1 is
what the user sees, 2 the LibreOffice-only buttons that leave the tabs, 3 how it is built, 4 the decisions, 5 the
placeholders, 6 the risks. The feature plan is `product/odd/tasks/impress-ribbon-tabs.md`.

Sources: the PowerPoint reference `.superpowers/sdd/2026-10-20-writer-impress-ribbons/research-powerpoint365-ribbon.md`
(its sizes come from per-group crops; the 1920 px fit is measured, not assumed), the code map `map-M1.md` section 5.2
in the same folder (spot-checked), the Writer design and feature document, and the code. Every code claim was read
in the tree during this task unless it is marked **(inferred)**.

How to read the tables:

- **Size**: L = large (icon over label), S = small with label, I = icon only; combo, spin, gal and chk are their own
  sizes (research conventions).
- **Type**: PowerPoint's control type: btn, tgl (stays pressed), split, dd (dropdown), gal (gallery), chk (check
  box), combo, spin. A control mapped to a plain LibreOffice command is built as a button whatever its PowerPoint
  type (decision 9). PowerPoint's dialog launchers are listed under each tab and are not built (decision 8).
- **LibreOffice command**: the command the button runs. `(new menu)` is a menu-only command built with the Writer
  dropdown recipe: a label in `DrawImpressCommands.xcu`, a Popup node (ResourceMenuController, or the named
  controller) and a ToolBox node (GenericPopupToolbarController) in `Controller.xcu` for Module
  `com.sun.star.presentation.PresentationDocument`, and a static popup file in `sd/uiconfig/simpress/popupmenu/`
  (Writer's pattern: `Controller.xcu:1238-1250` and `:3609-3619`). `(widget X)` means the button's widget command
  is X and its action is the URL shown, because the page uses that URL more than once (decision 16). PLACEHOLDER is
  a greyed button or menu item on a family slot (section 5); `[P]` marks a placeholder menu item.
- **Evidence**: `D:n` = line n of `officecfg/registry/data/org/openoffice/Office/UI/DrawImpressCommands.xcu`, `G:n` =
  the same in `GenericCommands.xcu` (the label node); then the declaration (`sdraw.sdi` = `sd/sdi/sdraw.sdi`,
  `svx.sdi` = `svx/sdi/svx.sdi`, `sfx.sdi` = `sfx2/sdi/sfx.sdi`) with its slot id; then one interface that serves
  the slot in Impress (`_drvwsh.sdi`, `drviewsh.sdi`, `drtxtob.sdi`, `ViewShellBase.sdi`, `SlideSorterController.sdi`,
  `_docsh.sdi` in `sd/sdi/`; `appslots.sdi`, `frmslots.sdi`, `docslots.sdi` in `sfx2/sdi/`). An alias shows its
  `TargetURL`. `Controller.xcu` is `officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu`; `menubar.xml` is
  `sd/uiconfig/simpress/menubar/menubar.xml`; `notebookbar.ui` is the stock `sd/uiconfig/simpress/ui/notebookbar.ui`;
  the deck files are `sd/uiconfig/simpress/ui/*.ui`.
- **Labels**: the ribbon shows PowerPoint's label (the table's second column, `office_label`); menus, help and
  tooltips keep LibreOffice's (ruling T9). "LO label" names LibreOffice's where it differs in a way worth knowing.

## 1. What the user sees

### Tab order and labels

File, Home, Insert, Design, **Transitions**, **Animations**, Slide Show, Review, View, (contextual tabs), Extension,
Tools, **Help**. Bold tabs are new to Impress. PowerPoint's Draw and Record tabs, the File backstage and PowerPoint's
contextual tabs are not in this feature (decisions 3, 4 and 5). Impress's own contextual tabs (Table, Image, Draw,
Object, Media, Form, Master, Outline, 3D) stay exactly as they are.

- Stock pages and labels kept: "Home Tab" (`notebookbar.ui:2962`, label `~Home` `:3922`), Insert (`:3941`, `~Insert`
  `:4994`), Design (`:5623`, `~Design` `:5723`), SlideShow (`:5735`, `~Slide Show` `:6223`), Review (`:6235`,
  `~Review` `:6766`), View (`:6778`, `~View` `:7705`). They already carry PowerPoint's tab names.
- **Transitions is the stock Layout page** (`:5006`) relabelled: `LayoutLabel` (`:5611`) goes from `~Layout` to
  `Tra~nsitions` with the `relabel` operation, as Calc relabelled its Layout tab (`product/ui/calc_tabs.json:2-5`);
  the page keeps its id `Layout` and gets generated content (decision 6).
- **Design moves before Transitions** with the `move` operation (Calc's precedent, `calc_tabs.json:11-13`).
- New pages: "Animations" (label `~Animations`, context `TabbedImpress|AnimationsTabLabel`, after Transitions) and
  "Help" (`Hel~p`, context `TabbedImpress|HelpTabLabel`, last, after Tools, as in Calc and Writer), through
  `add_pages`.
- Positions: File (none, as stock), Home 1, Insert 2, Design 3, Transitions 4, Animations 5, Slide Show 6, Review 7,
  View 8, Table 9, Image 10, Draw 11, Object 12, Media 13, Form 14, Master 15, Outline 16, 3D 17, Extension 18,
  Tools 19, Help 20. Stock Tools is 18 (`notebookbar.ui:14666`).
- **Mnemonics**, checked against all 21 tabs of the new ribbon (the 19 stock labels at
  `notebookbar.ui:2951-14666` and the two new ones): the three new letters are free: Tra~nsitions **N**,
  ~Animations **A**, Hel~p **P** (Impress has no Print tab). The stock tabs already repeat letters: D (~Design, ~Draw,
  3~D), M (~Media, ~Master), O (~Object, ~Outline), R (~Review, Fo~rm), T (~Table, ~Tools). Each repeat involves a
  stock contextual tab, so it shows only while that tab is visible; the repeats predate this feature, and the stock
  contextual tabs stay as they are (decision 7). A unit test pins that the three new letters are unique. Hel~p is
  Calc's label (`product/ui/calc_tabs.json:20`); Writer took H~elp only because of its Print tab.
- Only the Home label carries context classes (`context-default`, `context-any`, `context-Text`, `context-DrawText`,
  `context-TextObject`, `notebookbar.ui:3922-3940`); every other main label has none, so it shows in every context,
  and so do the new pages (Writer section 1, the builder's default context Any).
- The "Home Tab" and Layout pages have `valign` `center` (`notebookbar.ui:2962`, `:5006`); a `properties` operation
  sets `fill`, as Writer did for its Home and Layout pages (`product/ui/writer_tabs.json:2-5`).

### Counts

| Tab | Sections | Controls | Real | Placeholder | Omitted | New dropdowns |
|---|---|---|---|---|---|---|
| Home | 7 | 64 (18 form the shape gallery: 17 cells and its arrow) | 63 | 1 (+8 menu items) | 5 | 11 |
| Insert | 9 | 26 | 22 | 4 (+2 menu items) | 3 | 3 |
| Design | 3 | 5 | 5 | 0 (+3 menu items) | 1 | 1 |
| Transitions | 3 | 8 | 7 | 1 | 0 | 0 |
| Animations | 4 | 12 | 10 | 2 | 0 | 0 |
| Slide Show | 3 | 12 | 9 | 3 | 4 | 0 |
| Review | 6 | 18 | 8 | 10 | 1 | 2 |
| View | 7 | 21 | 17 | 4 | 0 | 3 |
| Help | 1 | 5 | 4 | 1 | 0 | 0 |
| **Total** | **43** | **171** | **145** | **26 (+13 menu items = 39 entries on 24 slots)** | **14** | **20 (19 distinct menus)** |

"Real" counts the dropdowns, whose items are real commands except the 13 placeholder menu items, and the 32
approximate mappings (decision 26). 19 of those open the transition deck, the animation deck or the Set Up Slide
Show dialog in place of an inline control (decision 25). `InsertShapesMenu` is on Home and
Insert, so 20 dropdown controls use 19 new menu commands. PowerPoint's dialog launchers are not built and not
counted.

### Home (PowerPoint: Clipboard, Slides, Font, Paragraph, Drawing, Editing, Voice, Sensitivity, Add-ins, Copilot)

| Section | PowerPoint label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Undo | Undo | I | split | `.uno:Undo` | G:4644; sfx.sdi:4719 SID_UNDO; _drvwsh.sdi:2454 | list popup (Controller.xcu:2831); Calc and Writer parity, also in the quick access bar |
| Undo | Redo | I | split | `.uno:Redo` | G:4636; sfx.sdi:3590 SID_REDO; _drvwsh.sdi:2464 | list popup (Controller.xcu:2842) |
| Clipboard | Paste | L | split | `.uno:Paste` | G:4692; sfx.sdi:3206 SID_PASTE; _drvwsh.sdi:99 | SvxClipBoardControl (sd/source/ui/app/sddll.cxx:208) |
| Clipboard | Cut | I | btn | `.uno:Cut` | G:4676; sfx.sdi:905 SID_CUT; _drvwsh.sdi:89 |  |
| Clipboard | Copy | I | btn | `.uno:Copy` | G:4684; sfx.sdi:813 SID_COPY; _drvwsh.sdi:94 | PowerPoint's Copy is a split with Duplicate; kept plain (decision 11) |
| Clipboard | Format Painter | I | tgl | `.uno:FormatPaintbrush` | G:4652; sfx.sdi:4737 SID_FORMATPAINTBRUSH; _drvwsh.sdi:2470 | LO label Clone Formatting |
| Slides | New Slide | L | split | `.uno:InsertPage` | D:858; sdraw.sdi:1659 SID_INSERTPAGE; _drvwsh.sdi:153 | InsertSlideController (Controller.xcu:2099-2104): layout gallery plus Duplicate Slide (slidelayoutcontroller.cxx:216-231); LO label New Page |
| Slides | Reuse Slides | L | btn | `.uno:ImportSlideFromFile` | D:893 (TargetURL `.uno:ImportFromFile`); sdraw.sdi:1540 SID_INSERTFILE; _drvwsh.sdi:1558 | approximate: Insert Slide from File (the Office pane's cloud search is omitted) |
| Slides | Layout | S | split | `.uno:AssignLayout` | D:1171; sdraw.sdi:2137 SID_ASSIGN_LAYOUT; drviewsh.sdi:25 | SlideLayoutController (Controller.xcu:2073-2082): layout gallery plus Reset Slide Layout |
| Slides | Reset | S | btn | `.uno:AssignLayout?Reset:bool=true` (widget `ResetLayout`) | D:1171; sdraw.sdi:2137 SID_ASSIGN_LAYOUT; drviewsh.sdi:25 | re-applies the current layout: AssignLayout without WhatLayout keeps the slide's layout (ViewShellImplementation.cxx:245-271); the unknown argument is ignored (appuno.cxx:877-880) and keeps the controller off (inferred, decision 13) |
| Slides | Section | S | dd | `.uno:HomeSectionMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | AddSlideSection; RenameSlideSection; RemoveSlideSection; RemoveSlideSectionAndSlides; (separator); MoveSlideSectionUp; MoveSlideSectionDown; (separator); .uno:HomeSection?Action:string=removeall [P]; .uno:HomeSection?Action:string=collapseall [P]; .uno:HomeSection?Action:string=expandall [P] |
| Font | Font | combo | combo | `.uno:CharFontName` | G:1594; svx.sdi:1247 SID_ATTR_CHAR_FONT; _drvwsh.sdi:2808 | font box (Controller.xcu:2886) |
| Font | Font Size | combo | combo | `.uno:FontHeight` | G:1790; svx.sdi:3127 SID_ATTR_CHAR_FONTHEIGHT; _drvwsh.sdi:2813 | size box (Controller.xcu:2062) |
| Font | Increase Font Size | I | btn | `.uno:Grow` | G:1626; svx.sdi:11822 SID_GROW_FONT_SIZE; _drvwsh.sdi:2908 |  |
| Font | Decrease Font Size | I | btn | `.uno:Shrink` | G:1640; svx.sdi:11841 SID_SHRINK_FONT_SIZE; _drvwsh.sdi:2903 |  |
| Font | Clear All Formatting | I | btn | `.uno:SetDefault` | G:5315; svx.sdi:7813 SID_SET_DEFAULT; _drvwsh.sdi:1631 |  |
| Font | Bold | I | tgl | `.uno:Bold` | G:1618; svx.sdi:832 SID_ATTR_CHAR_WEIGHT; _drvwsh.sdi:2818 |  |
| Font | Italic | I | tgl | `.uno:Italic` | G:1610; svx.sdi:5197 SID_ATTR_CHAR_POSTURE; _drvwsh.sdi:2823 |  |
| Font | Underline | I | split | `.uno:Underline` | G:1725; svx.sdi:9066 SID_ATTR_CHAR_UNDERLINE; _drvwsh.sdi:2833 | underline popup (Controller.xcu:2820) |
| Font | Text Shadow | I | tgl | `.uno:Shadowed` | G:1665; svx.sdi:8090 SID_ATTR_CHAR_SHADOWED; _drvwsh.sdi:2858 |  |
| Font | Strikethrough | I | tgl | `.uno:Strikeout` | G:1716; svx.sdi:8491 SID_ATTR_CHAR_STRIKEOUT; _drvwsh.sdi:2863 |  |
| Font | Character Spacing | I | dd | `.uno:Spacing` | G:4284; svx.sdi:8347 SID_ATTR_CHAR_KERNING; _drvwsh.sdi:2883 | spacing popup (Controller.xcu:2688) |
| Font | Change Case | I | dd | `.uno:HomeChangeCaseMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | ChangeCaseToSentenceCase; ChangeCaseToLower; ChangeCaseToUpper; ChangeCaseToTitleCase; ChangeCaseToToggleCase; Writer's name |
| Font | Highlight | I | split | `.uno:CharBackColor` | G:3805; svx.sdi:1572 SID_ATTR_CHAR_BACK_COLOR; _drvwsh.sdi:2878 | color popup (Controller.xcu:2798) |
| Font | Font Color | I | split | `.uno:Color` | G:1876; svx.sdi:1554 SID_ATTR_CHAR_COLOR; _drvwsh.sdi:2873 | color popup (Controller.xcu:2776) |
| Paragraph | Bullets | I | split | `.uno:DefaultBullet` | G:3077; svx.sdi:2251 FN_NUM_BULLET_ON; _drvwsh.sdi:806 | Controller.xcu:2139 |
| Paragraph | Numbering | I | split | `.uno:DefaultNumbering` | G:3091; svx.sdi:4985 FN_NUM_NUMBERING_ON; _drvwsh.sdi:811 | Controller.xcu:2106 |
| Paragraph | Decrease List Level | I | btn | `.uno:OutlineLeft` | G:3351; svx.sdi:6384 SID_OUTLINE_LEFT; drtxtob.sdi:268 | LO label Promote |
| Paragraph | Increase List Level | I | btn | `.uno:OutlineRight` | G:3387; svx.sdi:6402 SID_OUTLINE_RIGHT; drtxtob.sdi:273 | LO label Demote |
| Paragraph | Line Spacing | I | dd | `.uno:LineSpacing` | G:1981; svx.sdi:5838 SID_ATTR_PARA_LINESPACE; _drvwsh.sdi:1700 | spacing popup (Controller.xcu:2677) |
| Paragraph | Align Left | I | tgl | `.uno:LeftPara` | G:1910; svx.sdi:5421 SID_ATTR_PARA_ADJUST_LEFT; _drvwsh.sdi:1710 |  |
| Paragraph | Center | I | tgl | `.uno:CenterPara` | G:1932; svx.sdi:1020 SID_ATTR_PARA_ADJUST_CENTER; _drvwsh.sdi:1715 |  |
| Paragraph | Align Right | I | tgl | `.uno:RightPara` | G:1921; svx.sdi:7392 SID_ATTR_PARA_ADJUST_RIGHT; _drvwsh.sdi:1720 |  |
| Paragraph | Justify | I | tgl | `.uno:JustifyPara` | G:1965; svx.sdi:5273 SID_ATTR_PARA_ADJUST_BLOCK; _drvwsh.sdi:1725 |  |
| Paragraph | Add or Remove Columns | I | dd | `.uno:HomeColumnsMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | TextColumnsNumber?TextColumnsNumber:short=1; TextColumnsNumber?TextColumnsNumber:short=2; TextColumnsNumber?TextColumnsNumber:short=3; (separator); TextAttributes; the three column items are `TextColumnsNumber` URL variants (svx.sdi:13498 SID_ATTR_TEXTCOLUMNS_NUMBER; _drvwsh.sdi:3031) with new label nodes (inferred: the argument name equals the slot's, decision 14) |
| Paragraph | Text Direction | S | dd | `.uno:HomeTextDirectionMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | TextdirectionLeftToRight; TextdirectionTopToBottom; (separator); ParaLeftToRight; ParaRightToLeft; the paragraph direction items keep the stock Home buttons (decision 17) |
| Paragraph | Align Text | S | dd | `.uno:HomeAlignTextMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | CellVertTop; CellVertCenter; CellVertBottom; (separator); TextAttributes |
| Paragraph | Convert to SmartArt | S | dd | PLACEHOLDER `.uno:HomeConvertToSmartArt` | family slot, I1 |  |
| Drawing | Text Box (gallery cell) | I | gal | `.uno:Text` | G:1562; svx.sdi:8712 SID_ATTR_CHAR; _drvwsh.sdi:842 | gallery cell (decision 15) |
| Drawing | Line (gallery cell) | I | gal | `.uno:Line` | G:2204; svx.sdi:5603 SID_DRAW_LINE; _drvwsh.sdi:1229 | gallery cell (decision 15) |
| Drawing | Rectangle (gallery cell) | I | gal | `.uno:BasicShapes.rectangle` | G:244; svx.sdi:10703 SID_DRAWTBX_CS_BASIC; _drvwsh.sdi:2661 | gallery cell (decision 15) |
| Drawing | Oval (gallery cell) | I | gal | `.uno:BasicShapes.ellipse` | G:287; svx.sdi:10703 SID_DRAWTBX_CS_BASIC; _drvwsh.sdi:2661 | gallery cell (decision 15) |
| Drawing | Lines and Arrows (gallery cell) | I | gal | `.uno:ArrowsToolbox` | G:2450; svx.sdi:5764 SID_DRAWTBX_ARROWS; _drvwsh.sdi:1391 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | Connectors (gallery cell) | I | gal | `.uno:ConnectorToolbox` | G:2215; svx.sdi:104 SID_DRAWTBX_CONNECTORS; _drvwsh.sdi:1366 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | Basic Shapes (gallery cell) | I | gal | `.uno:BasicShapes` | G:132; svx.sdi:10703 SID_DRAWTBX_CS_BASIC; _drvwsh.sdi:2661 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | Symbol Shapes (gallery cell) | I | gal | `.uno:SymbolShapes` | G:146; svx.sdi:10721 SID_DRAWTBX_CS_SYMBOL; _drvwsh.sdi:2666 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | Block Arrows (gallery cell) | I | gal | `.uno:ArrowShapes` | G:188; svx.sdi:10739 SID_DRAWTBX_CS_ARROW; _drvwsh.sdi:2671 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | Flowchart (gallery cell) | I | gal | `.uno:FlowChartShapes` | G:202; svx.sdi:10757 SID_DRAWTBX_CS_FLOWCHART; _drvwsh.sdi:2676 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | Callouts (gallery cell) | I | gal | `.uno:CalloutShapes` | G:216; svx.sdi:10775 SID_DRAWTBX_CS_CALLOUT; _drvwsh.sdi:2681 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | Stars and Banners (gallery cell) | I | gal | `.uno:StarShapes` | G:230; svx.sdi:10793 SID_DRAWTBX_CS_STAR; _drvwsh.sdi:2686 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | Curves and Polygons (gallery cell) | I | gal | `.uno:LineToolbox` | G:5365; svx.sdi:86 SID_DRAWTBX_LINES; _drvwsh.sdi:1386 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | Freeform: Shape (gallery cell) | I | gal | `.uno:Polygon_Unfilled` | G:5083; svx.sdi:6801 SID_DRAW_POLYGON_NOFILL; _drvwsh.sdi:1274 | gallery cell (decision 15) |
| Drawing | Curve (gallery cell) | I | gal | `.uno:Bezier_Unfilled` | G:5099; svx.sdi:531 SID_DRAW_BEZIER_NOFILL; _drvwsh.sdi:1284 | gallery cell (decision 15) |
| Drawing | Speech Bubble (gallery cell) | I | gal | `.uno:DrawCaption` | G:4378; svx.sdi:982 SID_DRAW_CAPTION; _drvwsh.sdi:1149 | gallery cell (decision 15) |
| Drawing | 3D Objects (gallery cell) | I | gal | `.uno:Objects3DToolbox` | D:197; sdraw.sdi:2437 SID_DRAWTBX_3D_OBJECTS; _drvwsh.sdi:1396 | gallery cell (decision 15); sub-toolbar popup (Controller.xcu ToolBar nodes :1788-2377) |
| Drawing | More shapes (gallery arrow) | I | dd | `.uno:InsertShapesMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | ShapesLineMenu >; Line; Freeline_Unfilled; Freeline; Bezier_Unfilled; BezierFill; Polygon_Unfilled; Polygon_Diagonal_Unfilled; Polygon_Diagonal; (separator); BasicShapes; SymbolShapes; ArrowShapes; FlowChartShapes; CalloutShapes; StarShapes; (separator); ArrowsToolbox; ConnectorToolbox; Objects3DToolbox; the same popup as Insert > Shapes |
| Drawing | Arrange | L | dd | `.uno:HomeArrangeMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | BringToFront; SendToBack; Forward; Backward; (separator); FormatGroup; FormatUngroup; .uno:HomeRegroup [P]; (separator); ObjectAlignLeft; AlignCenter; ObjectAlignRight; AlignUp; AlignMiddle; AlignDown; DistributeSelection; (separator); ToggleObjectRotateMode; MirrorVert; MirrorHorz; (separator); Navigator |
| Drawing | Quick Styles | L | dd | `.uno:SidebarDeck.StyleListDeck` | G:8110; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: the Styles deck with the drawing styles, opened without toggling (Sidebar.cxx:37-59) |
| Drawing | Shape Fill | S | split | `.uno:FillColor` | G:3505; svx.sdi:2845 SID_ATTR_FILL_COLOR; _drvwsh.sdi:1435 | color popup (Controller.xcu:2864) |
| Drawing | Shape Outline | S | split | `.uno:XLineColor` | G:3647; svx.sdi:9275 SID_ATTR_LINE_COLOR; _drvwsh.sdi:1528 | color popup (Controller.xcu:2853) |
| Drawing | Shape Effects | S | dd | `.uno:HomeShapeEffectsMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | .uno:HomeShapeEffect?Effect:string=preset [P]; FillShadow; .uno:HomeShapeEffect?Effect:string=reflection [P]; SidebarDeck.PropertyDeck; .uno:HomeShapeEffect?Effect:string=bevel [P]; ExtrusionToggle |
| Editing | Find | S | dd | `.uno:HomeFindMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | vnd.sun.star.findbar:FocusToFindbar; SearchDialog; Writer's name; PowerPoint's Find is a button (decision 12) |
| Editing | Replace | S | dd | `.uno:HomeReplaceMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | SearchDialog; .uno:HomeReplaceFonts [P]; PowerPoint split; dropdown whose first item is the body (decision 10) |
| Editing | Select | S | dd | `.uno:HomeSelectMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | SelectAll; SelectObject; Navigator; Writer's name; Selection Pane = Navigator (Calc decision 17) |

Menu items (real commands; evidence as above):

- `.uno:AddSlideSection`: D:1233; sdraw.sdi:4269 SID_ADD_SLIDE_SECTION; _drvwsh.sdi:195
- `.uno:RenameSlideSection`: D:1248; sdraw.sdi:4320 SID_RENAME_SLIDE_SECTION; _drvwsh.sdi:210
- `.uno:RemoveSlideSection`: D:1238; sdraw.sdi:4286 SID_REMOVE_SLIDE_SECTION; _drvwsh.sdi:200
- `.uno:RemoveSlideSectionAndSlides`: D:1243; sdraw.sdi:4303 SID_REMOVE_SLIDE_SECTION_AND_SLIDES; _drvwsh.sdi:205
- `.uno:MoveSlideSectionUp`: D:1253; sdraw.sdi:4337 SID_MOVE_SLIDE_SECTION_UP; _drvwsh.sdi:215
- `.uno:MoveSlideSectionDown`: D:1258; sdraw.sdi:4354 SID_MOVE_SLIDE_SECTION_DOWN; _drvwsh.sdi:220
- `.uno:ChangeCaseToSentenceCase`: G:3182; svx.sdi:1114 SID_TRANSLITERATE_SENTENCE_CASE; _drvwsh.sdi:2402
- `.uno:ChangeCaseToLower`: G:3187; svx.sdi:1190 SID_TRANSLITERATE_LOWER; _drvwsh.sdi:2422
- `.uno:ChangeCaseToUpper`: G:3195; svx.sdi:1209 SID_TRANSLITERATE_UPPER; _drvwsh.sdi:2397
- `.uno:ChangeCaseToTitleCase`: G:3203; svx.sdi:1133 SID_TRANSLITERATE_TITLE_CASE; _drvwsh.sdi:2407
- `.uno:ChangeCaseToToggleCase`: G:3208; svx.sdi:1152 SID_TRANSLITERATE_TOGGLE_CASE; _drvwsh.sdi:2412
- `.uno:TextColumnsNumber?TextColumnsNumber:short=1`: URL variant of `.uno:TextColumnsNumber` (no label node yet); svx.sdi:13498 SID_ATTR_TEXTCOLUMNS_NUMBER; _drvwsh.sdi:3031; new label node
- `.uno:TextColumnsNumber?TextColumnsNumber:short=2`: URL variant of `.uno:TextColumnsNumber` (no label node yet); svx.sdi:13498 SID_ATTR_TEXTCOLUMNS_NUMBER; _drvwsh.sdi:3031; new label node
- `.uno:TextColumnsNumber?TextColumnsNumber:short=3`: URL variant of `.uno:TextColumnsNumber` (no label node yet); svx.sdi:13498 SID_ATTR_TEXTCOLUMNS_NUMBER; _drvwsh.sdi:3031; new label node
- `.uno:TextAttributes`: D:168; sdraw.sdi:3315 SID_TEXTATTR_DLG; _drvwsh.sdi:2071
- `.uno:TextdirectionLeftToRight`: G:3050; svx.sdi:8768 SID_TEXTDIRECTION_LEFT_TO_RIGHT; drtxtob.sdi:293
- `.uno:TextdirectionTopToBottom`: G:3058; svx.sdi:8787 SID_TEXTDIRECTION_TOP_TO_BOTTOM; drtxtob.sdi:298
- `.uno:ParaLeftToRight`: G:3765; svx.sdi:9742 SID_ATTR_PARA_LEFT_TO_RIGHT; drtxtob.sdi:173
- `.uno:ParaRightToLeft`: G:3781; svx.sdi:9760 SID_ATTR_PARA_RIGHT_TO_LEFT; drtxtob.sdi:180
- `.uno:CellVertTop`: G:7034; svx.sdi:11535 SID_TABLE_VERT_NONE; _drvwsh.sdi:2913
- `.uno:CellVertCenter`: G:7045; svx.sdi:11516 SID_TABLE_VERT_CENTER; _drvwsh.sdi:2918
- `.uno:CellVertBottom`: G:7056; svx.sdi:11497 SID_TABLE_VERT_BOTTOM; _drvwsh.sdi:2923
- `.uno:ShapesLineMenu` (submenu): G:4322; a menu id only, as Insert > Shape > Line (menubar.xml:221)
- `.uno:Line`: G:2204; svx.sdi:5603 SID_DRAW_LINE; _drvwsh.sdi:1229
- `.uno:Freeline_Unfilled`: G:5384; svx.sdi:3707 SID_DRAW_FREELINE_NOFILL; _drvwsh.sdi:1294
- `.uno:Freeline`: G:5376; svx.sdi:3688 SID_DRAW_FREELINE; _drvwsh.sdi:1289
- `.uno:Bezier_Unfilled`: G:5099; svx.sdi:531 SID_DRAW_BEZIER_NOFILL; _drvwsh.sdi:1284
- `.uno:BezierFill`: G:2854; svx.sdi:663 SID_DRAW_BEZIER_FILL; _drvwsh.sdi:1279
- `.uno:Polygon_Unfilled`: G:5083; svx.sdi:6801 SID_DRAW_POLYGON_NOFILL; _drvwsh.sdi:1274
- `.uno:Polygon_Diagonal_Unfilled`: G:5091; svx.sdi:6783 SID_DRAW_XPOLYGON_NOFILL; _drvwsh.sdi:1264
- `.uno:Polygon_Diagonal`: G:5075; svx.sdi:6765 SID_DRAW_XPOLYGON; _drvwsh.sdi:1259
- `.uno:BasicShapes`: G:132; svx.sdi:10703 SID_DRAWTBX_CS_BASIC; _drvwsh.sdi:2661
- `.uno:SymbolShapes`: G:146; svx.sdi:10721 SID_DRAWTBX_CS_SYMBOL; _drvwsh.sdi:2666
- `.uno:ArrowShapes`: G:188; svx.sdi:10739 SID_DRAWTBX_CS_ARROW; _drvwsh.sdi:2671
- `.uno:FlowChartShapes`: G:202; svx.sdi:10757 SID_DRAWTBX_CS_FLOWCHART; _drvwsh.sdi:2676
- `.uno:CalloutShapes`: G:216; svx.sdi:10775 SID_DRAWTBX_CS_CALLOUT; _drvwsh.sdi:2681
- `.uno:StarShapes`: G:230; svx.sdi:10793 SID_DRAWTBX_CS_STAR; _drvwsh.sdi:2686
- `.uno:ArrowsToolbox`: G:2450; svx.sdi:5764 SID_DRAWTBX_ARROWS; _drvwsh.sdi:1391
- `.uno:ConnectorToolbox`: G:2215; svx.sdi:104 SID_DRAWTBX_CONNECTORS; _drvwsh.sdi:1366
- `.uno:Objects3DToolbox`: D:197; sdraw.sdi:2437 SID_DRAWTBX_3D_OBJECTS; _drvwsh.sdi:1396
- `.uno:BringToFront`: G:4494; svx.sdi:964 SID_FRAME_TO_TOP; _drvwsh.sdi:641
- `.uno:SendToBack`: G:4502; svx.sdi:7795 SID_FRAME_TO_BOTTOM; _drvwsh.sdi:681
- `.uno:Forward`: D:944; sdraw.sdi:905 SID_MOREFRONT; _drvwsh.sdi:646
- `.uno:Backward`: D:952; sdraw.sdi:161 SID_MOREBACK; _drvwsh.sdi:671
- `.uno:FormatGroup`: G:5299; svx.sdi:3449 SID_GROUP; _drvwsh.sdi:499
- `.uno:FormatUngroup`: G:5307; svx.sdi:3561 SID_UNGROUP; _drvwsh.sdi:520
- `.uno:ObjectAlignLeft`: G:2983; svx.sdi:176 SID_OBJECT_ALIGN_LEFT; _drvwsh.sdi:686
- `.uno:AlignCenter`: G:2991; svx.sdi:140 SID_OBJECT_ALIGN_CENTER; _drvwsh.sdi:691
- `.uno:ObjectAlignRight`: G:2999; svx.sdi:231 SID_OBJECT_ALIGN_RIGHT; _drvwsh.sdi:696
- `.uno:AlignUp`: G:3007; svx.sdi:249 SID_OBJECT_ALIGN_UP; _drvwsh.sdi:701
- `.uno:AlignMiddle`: G:3015; svx.sdi:213 SID_OBJECT_ALIGN_MIDDLE; _drvwsh.sdi:706
- `.uno:AlignDown`: G:3023; svx.sdi:158 SID_OBJECT_ALIGN_DOWN; _drvwsh.sdi:711
- `.uno:DistributeSelection`: G:7971; svx.sdi:2306 SID_DISTRIBUTE_DLG; _drvwsh.sdi:536
- `.uno:ToggleObjectRotateMode`: G:2975; svx.sdi:8901 SID_OBJECT_ROTATE; _drvwsh.sdi:882
- `.uno:MirrorVert`: D:960; sdraw.sdi:2037 SID_VERTICAL; _drvwsh.sdi:1921
- `.uno:MirrorHorz`: D:968; sdraw.sdi:2020 SID_HORIZONTAL; _drvwsh.sdi:1911
- `.uno:Navigator`: G:4831; sfx.sdi:2637 SID_NAVIGATOR; _drvwsh.sdi:250
- `.uno:FillShadow`: G:4617; svx.sdi:7978 SID_ATTR_FILL_SHADOW; _drvwsh.sdi:1931
- `.uno:SidebarDeck.PropertyDeck`: G:8105; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51
- `.uno:ExtrusionToggle`: G:6686; svx.sdi:10011 SID_EXTRUSION_TOGGLE; _drvwsh.sdi:2516
- `vnd.sun.star.findbar:FocusToFindbar`: G:1855; framework URL (no slot)
- `.uno:SearchDialog`: G:5990; sfx.sdi:4053 SID_SEARCH_DLG; frmslots.sdi:65
- `.uno:SelectAll`: G:4755; sfx.sdi:4108 SID_SELECTALL; _drvwsh.sdi:716
- `.uno:SelectObject`: G:2967; svx.sdi:8938 SID_OBJECT_SELECT; _drvwsh.sdi:1406

- Omitted: Dictate (Voice, cloud); Sensitivity (account); Add-ins (store); Copilot (cloud); Designer (cloud; also on Design).
- Launchers (not built): Clipboard (Office Clipboard pane: no LibreOffice equivalent); Font: Format > Character... (`.uno:FontDialog`, menubar.xml:398); Paragraph: Format > Paragraph... (`.uno:ParagraphDialog`, menubar.xml:399); Drawing: Format > Text Box and Shape > Area... (`.uno:FormatArea`, menubar.xml:463).

### Insert (PowerPoint: Slides, Tables, Images, Camera, Illustrations, Power BI, Forms, Links, Comments, Text, Symbols, Media)

| Section | PowerPoint label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Slides | New Slide | L | split | `.uno:InsertPage` | D:858; sdraw.sdi:1659 SID_INSERTPAGE; _drvwsh.sdi:153 | InsertSlideController (Controller.xcu:2099-2104), as on Home |
| Slides | Reuse Slides | L | btn | `.uno:ImportSlideFromFile` | D:893 (TargetURL `.uno:ImportFromFile`); sdraw.sdi:1540 SID_INSERTFILE; _drvwsh.sdi:1558 | approximate, as on Home |
| Tables | Table | L | dd | `.uno:InsertTable` | D:1999; svx.sdi:5124 SID_INSERT_TABLE; _drvwsh.sdi:2798 | grid popup (Controller.xcu:2161) |
| Images | Pictures | L | btn | `.uno:InsertGraphic` | G:4227; svx.sdi:4928 SID_INSERT_GRAPHIC; _drvwsh.sdi:412 | This Device; Stock Images and Online Pictures are omitted (cloud) |
| Images | Screenshot | S | dd | PLACEHOLDER `.uno:InsertScreenshot` | family slot, I1 | Calc and Writer family name |
| Images | Photo Album | S | split | `.uno:PhotoAlbumDialog` | D:114; sdraw.sdi:3943 SID_PHOTOALBUM; drviewsh.sdi:201 | one dialog for New and Edit |
| Illustrations | Shapes | L | dd | `.uno:InsertShapesMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | ShapesLineMenu >; Line; Freeline_Unfilled; Freeline; Bezier_Unfilled; BezierFill; Polygon_Unfilled; Polygon_Diagonal_Unfilled; Polygon_Diagonal; (separator); BasicShapes; SymbolShapes; ArrowShapes; FlowChartShapes; CalloutShapes; StarShapes; (separator); ArrowsToolbox; ConnectorToolbox; Objects3DToolbox; Calc and Writer name; Impress nodes |
| Illustrations | Icons | L | btn | `.uno:Gallery` | G:5976; svx.sdi:3728 SID_GALLERY; _drvwsh.sdi:1877 | approximate: the Gallery (Writer decision 18) |
| Illustrations | 3D Models | S | dd | PLACEHOLDER `.uno:Insert3DModels` | family slot, I1 | Calc and Writer family name |
| Illustrations | SmartArt | S | btn | PLACEHOLDER `.uno:InsertSmartArt` | family slot, I1 | Calc and Writer family name |
| Illustrations | Chart | S | btn | `.uno:InsertObjectChart` | G:3066; svx.sdi:5068 SID_INSERT_DIAGRAM; _drvwsh.sdi:436 |  |
| Links | Zoom | L | dd | `.uno:InsertZoomMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | SummaryPage; .uno:InsertZoom?Type:string=section [P]; .uno:InsertZoom?Type:string=slide [P]; Summary Zoom is approximate: LibreOffice's Summary Slide |
| Links | Link | L | dd | `.uno:HyperlinkDialog` | G:4518; sfx.sdi:2002 SID_HYPERLINK_DIALOG; frmslots.sdi:21 | Recent items are omitted |
| Links | Action | L | btn | `.uno:AnimationEffects` | D:1136; sdraw.sdi:37 SID_ANIMATION_EFFECTS; drviewsh.sdi:35 | LO label Interaction...: the same feature (actions on click) |
| Comments | Comment | L | btn | `.uno:InsertAnnotation` | G:2945; svx.sdi:4719 SID_INSERT_POSTIT; drviewsh.sdi:161 |  |
| Text | Text Box | L | dd | `.uno:InsertTextBoxMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | Text; VerticalText; Writer's name; Impress nodes |
| Text | Header & Footer | L | btn | `.uno:HeaderAndFooter` | D:1747; sdraw.sdi:3472 SID_HEADER_AND_FOOTER; _drvwsh.sdi:2476 |  |
| Text | WordArt | L | dd | `.uno:FontworkGalleryFloater` | G:86; svx.sdi:10297 SID_FONTWORK_GALLERY_FLOATER; _drvwsh.sdi:2606 | approximate: the Fontwork gallery (Writer's mapping) |
| Text | Date & Time | I | btn | `.uno:InsertDateFieldVar` | D:546; sdraw.sdi:1591 SID_INSERT_FLD_DATE_VAR; _drvwsh.sdi:2302 | approximate: the variable date field (Writer's mapping); the other date and time fields stay in Insert > Field |
| Text | Slide Number | I | btn | `.uno:InsertSlideField` | D:586 (TargetURL `.uno:InsertPageField`); sdraw.sdi:1710 SID_INSERT_FLD_PAGE; _drvwsh.sdi:2317 |  |
| Text | Object | I | btn | `.uno:InsertObject` | G:3695; svx.sdi:5049 SID_INSERT_OBJECT; _drvwsh.sdi:459 |  |
| Symbols | Equation | L | split | `.uno:InsertMath` | G:3869; svx.sdi:4947 SID_INSERT_MATH; _drvwsh.sdi:469 | approximate: a Formula object; built-in equations and Ink Equation are not built |
| Symbols | Symbol | L | btn | `.uno:CharmapControl` | G:5570; sfx.sdi:268 SID_CHARMAP_CONTROL; _drvwsh.sdi:360 | LibreOffice's control adds a favourites popup (Controller.xcu:2699) |
| Media | Video | L | dd | `.uno:InsertAVMedia` (widget `InsertVideo`) | G:7489; sfx.sdi:5582 SID_INSERT_AVMEDIA; _drvwsh.sdi:2707 | This Device; Stock and Online Videos are omitted (cloud); distinct widget command (decision 16) |
| Media | Audio | L | dd | `.uno:InsertAVMedia` (widget `InsertAudio`) | G:7489; sfx.sdi:5582 SID_INSERT_AVMEDIA; _drvwsh.sdi:2707 | Audio on My PC; Record Audio is omitted with Record (decision 4) |
| Media | Screen Recording | L | btn | PLACEHOLDER `.uno:InsertScreenRecording` | family slot, I1 |  |

Menu items (real commands; evidence as above):

- `.uno:ShapesLineMenu` (submenu): G:4322; a menu id only, as Insert > Shape > Line (menubar.xml:221)
- `.uno:Line`: G:2204; svx.sdi:5603 SID_DRAW_LINE; _drvwsh.sdi:1229
- `.uno:Freeline_Unfilled`: G:5384; svx.sdi:3707 SID_DRAW_FREELINE_NOFILL; _drvwsh.sdi:1294
- `.uno:Freeline`: G:5376; svx.sdi:3688 SID_DRAW_FREELINE; _drvwsh.sdi:1289
- `.uno:Bezier_Unfilled`: G:5099; svx.sdi:531 SID_DRAW_BEZIER_NOFILL; _drvwsh.sdi:1284
- `.uno:BezierFill`: G:2854; svx.sdi:663 SID_DRAW_BEZIER_FILL; _drvwsh.sdi:1279
- `.uno:Polygon_Unfilled`: G:5083; svx.sdi:6801 SID_DRAW_POLYGON_NOFILL; _drvwsh.sdi:1274
- `.uno:Polygon_Diagonal_Unfilled`: G:5091; svx.sdi:6783 SID_DRAW_XPOLYGON_NOFILL; _drvwsh.sdi:1264
- `.uno:Polygon_Diagonal`: G:5075; svx.sdi:6765 SID_DRAW_XPOLYGON; _drvwsh.sdi:1259
- `.uno:BasicShapes`: G:132; svx.sdi:10703 SID_DRAWTBX_CS_BASIC; _drvwsh.sdi:2661
- `.uno:SymbolShapes`: G:146; svx.sdi:10721 SID_DRAWTBX_CS_SYMBOL; _drvwsh.sdi:2666
- `.uno:ArrowShapes`: G:188; svx.sdi:10739 SID_DRAWTBX_CS_ARROW; _drvwsh.sdi:2671
- `.uno:FlowChartShapes`: G:202; svx.sdi:10757 SID_DRAWTBX_CS_FLOWCHART; _drvwsh.sdi:2676
- `.uno:CalloutShapes`: G:216; svx.sdi:10775 SID_DRAWTBX_CS_CALLOUT; _drvwsh.sdi:2681
- `.uno:StarShapes`: G:230; svx.sdi:10793 SID_DRAWTBX_CS_STAR; _drvwsh.sdi:2686
- `.uno:ArrowsToolbox`: G:2450; svx.sdi:5764 SID_DRAWTBX_ARROWS; _drvwsh.sdi:1391
- `.uno:ConnectorToolbox`: G:2215; svx.sdi:104 SID_DRAWTBX_CONNECTORS; _drvwsh.sdi:1366
- `.uno:Objects3DToolbox`: D:197; sdraw.sdi:2437 SID_DRAWTBX_3D_OBJECTS; _drvwsh.sdi:1396
- `.uno:SummaryPage`: D:512; sdraw.sdi:3248 SID_SUMMARY_PAGE; drviewsh.sdi:134
- `.uno:Text`: G:1562; svx.sdi:8712 SID_ATTR_CHAR; _drvwsh.sdi:842
- `.uno:VerticalText`: G:3031; svx.sdi:9143 SID_DRAW_TEXT_VERTICAL; _drvwsh.sdi:847

- Omitted: Cameo (Camera group, cloud); Power BI (cloud); Forms (cloud); Stock Images, Online Pictures, Stock and Online Videos (cloud items of kept controls, not counted).

### Design (PowerPoint: Themes, Variants, Customize, Designer)

| Section | PowerPoint label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Themes | Themes | gal | gal | `.uno:SidebarDeck.SdMasterPagesDeck` | D:2447; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: master slides are LibreOffice's themes; the deck opens without toggling |
| Variants | Variants | gal | gal | `.uno:ThemeSelectorPanel` | G:3545; controller only (Controller.xcu:2128), no slot | the stock theme colors control (notebookbar.ui:5682), kept |
| Variants | More (Variants menu) | I | dd | `.uno:DesignVariantsMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | ThemeDialog; .uno:PageLayoutThemePart?Part:string=fonts [P]; .uno:PageLayoutThemePart?Part:string=effects [P]; .uno:PageLayoutThemePart?Part:string=backgroundstyles [P]; Colors is approximate: the document theme dialog |
| Customize | Slide Size | L | dd | `.uno:SlideSetup` | D:767 (TargetURL `.uno:PageSetup`); sdraw.sdi:2600 SID_PAGESETUP; _drvwsh.sdi:479 | approximate: the Slide Properties dialog sets the size; Standard and Widescreen presets are in its list |
| Customize | Format Background | L | btn | `.uno:SidebarDeck.PropertyDeck` | G:8105; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: the Properties deck shows the Slide panel (background) when nothing is selected (Sidebar.xcu:1160-1177, context DrawImpress default) |

Menu items (real commands; evidence as above):

- `.uno:ThemeDialog`: G:8089; svx.sdi:13293 SID_THEME_DIALOG; _drvwsh.sdi:3071

- Omitted: Designer (cloud).

### Transitions (PowerPoint: Preview, Transition to This Slide, Timing), the stock Layout page, relabelled (decision 6)

| Section | PowerPoint label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Preview | Preview | L | btn | PLACEHOLDER `.uno:PreviewEffects?Target:string=transition` | family slot, I1 | no command plays the transition (the deck's Play button has none, slidetransitionspanel.ui:414) |
| Transition to This Slide | Transition Styles (gallery) | gal | gal | `.uno:SidebarDeck.SdSlideTransitionDeck` (widget `TransitionStyles`) | D:2437; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: the deck's transition list (slidetransitionspanel.ui:57); label inferred |
| Transition to This Slide | Effect Options | L | dd | `.uno:SidebarDeck.SdSlideTransitionDeck` (widget `TransitionEffectOptions`) | D:2437; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Variant (slidetransitionspanel.ui:204) |
| Timing | Sound | combo | combo | `.uno:SidebarDeck.SdSlideTransitionDeck` (widget `TransitionSound`) | D:2437; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Sound (slidetransitionspanel.ui:149) |
| Timing | Duration | spin | spin | `.uno:SidebarDeck.SdSlideTransitionDeck` (widget `TransitionDuration`) | D:2437; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Duration (slidetransitionspanel.ui:114) |
| Timing | Apply To All | S | btn | `.uno:SidebarDeck.SdSlideTransitionDeck` (widget `TransitionApplyToAll`) | D:2437; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Apply Transition to All Slides (slidetransitionspanel.ui:352) |
| Timing | On Mouse Click | chk | chk | `.uno:SidebarDeck.SdSlideTransitionDeck` (widget `TransitionOnMouseClick`) | D:2437; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: On mouse click (slidetransitionspanel.ui:256) |
| Timing | After | chk | chk | `.uno:SidebarDeck.SdSlideTransitionDeck` (widget `TransitionAfter`) | D:2437; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Automatically after (slidetransitionspanel.ui:277-300) |

### Animations (PowerPoint: Preview, Animation, Advanced Animation, Timing), new page

| Section | PowerPoint label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Preview | Preview | L | split | PLACEHOLDER `.uno:PreviewEffects?Target:string=animation` | family slot, I1 | no command plays the animation (the deck's Play button has none, customanimationspanel.ui:590) |
| Animation | Animation Styles (gallery) | gal | gal | `.uno:SidebarDeck.SdCustomAnimationDeck` (widget `AnimationStyles`) | D:2442; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: the deck's effect list (customanimationspanel.ui:388) |
| Animation | Effect Options | L | dd | `.uno:SidebarDeck.SdCustomAnimationDeck` (widget `AnimationEffectOptions`) | D:2442; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: the deck's Options button (customanimationspanel.ui:657) |
| Advanced Animation | Add Animation | L | dd | `.uno:SidebarDeck.SdCustomAnimationDeck` (widget `AddAnimation`) | D:2442; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Add Effect (customanimationspanel.ui:232) |
| Advanced Animation | Animation Pane | S | tgl | `.uno:CustomAnimation` | D:443; sdraw.sdi:817 SID_CUSTOM_ANIMATION_PANEL; drviewsh.sdi:45 | exact: toggles the Animation deck (drviews2.cxx:4227-4248) |
| Advanced Animation | Trigger | S | dd | `.uno:SidebarDeck.SdCustomAnimationDeck` (widget `AnimationTrigger`) | D:2442; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Options > Timing > Trigger (customanimationtimingtab.ui:207-244) |
| Advanced Animation | Animation Painter | S | btn | PLACEHOLDER `.uno:AnimationPainter` | family slot, I1 |  |
| Timing | Start | combo | combo | `.uno:SidebarDeck.SdCustomAnimationDeck` (widget `AnimationStart`) | D:2442; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Start (customanimationspanel.ui:458) |
| Timing | Duration | spin | spin | `.uno:SidebarDeck.SdCustomAnimationDeck` (widget `AnimationDuration`) | D:2442; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Duration (customanimationspanel.ui:506) |
| Timing | Delay | spin | spin | `.uno:SidebarDeck.SdCustomAnimationDeck` (widget `AnimationDelay`) | D:2442; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Delay (customanimationspanel.ui:539) |
| Timing | Move Earlier | S | btn | `.uno:SidebarDeck.SdCustomAnimationDeck` (widget `AnimationMoveEarlier`) | D:2442; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Move Up (customanimationspanel.ui:275) |
| Timing | Move Later | S | btn | `.uno:SidebarDeck.SdCustomAnimationDeck` (widget `AnimationMoveLater`) | D:2442; sfx.sdi:4479 SID_SIDEBAR_DECK; frmslots.sdi:51 | approximate: Move Down (customanimationspanel.ui:296) |

- Launchers (not built): Animation: the effect options dialog, reached from the Animation deck's Options button (customanimationspanel.ui:657).

### Slide Show (PowerPoint: Start Slide Show, Rehearse, Set Up, Monitors, Captions & Subtitles)

| Section | PowerPoint label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Start Slide Show | From Beginning | L | btn | `.uno:Presentation` | D:77; sdraw.sdi:2689 SID_PRESENTATION; drviewsh.sdi:70 |  |
| Start Slide Show | From Current Slide | L | btn | `.uno:PresentationCurrentSlide` | D:85; sdraw.sdi:2707 SID_PRESENTATION_CURRENT_SLIDE; drviewsh.sdi:75 |  |
| Start Slide Show | Custom Slide Show | L | dd | `.uno:CustomShowDialog` | D:659; sdraw.sdi:593 SID_CUSTOMSHOW_DLG; drviewsh.sdi:124 | approximate: the dialog lists, edits and starts the custom shows |
| Set Up | Set Up Slide Show | L | btn | `.uno:PresentationDialog` | D:464; sdraw.sdi:2725 SID_PRESENTATION_DLG; drviewsh.sdi:115 |  |
| Set Up | Hide Slide | L | tgl | `.uno:HideSlide` | D:138; sdraw.sdi:1488 SID_HIDE_SLIDE; SlideSorterController.sdi:174 | Show Slide stays in Slide > Show Slide (section 2) |
| Set Up | Rehearse Timings | L | btn | `.uno:RehearseTimings` | D:106; sdraw.sdi:2864 SID_REHEARSE_TIMINGS; drviewsh.sdi:65 |  |
| Set Up | Record | L | split | PLACEHOLDER `.uno:SlideShowRecord` | family slot, I1 | narration recording: not in LibreOffice |
| Set Up | Play Narrations | chk | chk | PLACEHOLDER `.uno:SlideShowOption?Option:string=narrations` | family slot, I1 |  |
| Set Up | Use Timings | chk | chk | `.uno:PresentationDialog` (widget `SlideShowUseTimings`) | D:464; sdraw.sdi:2725 SID_PRESENTATION_DLG; drviewsh.sdi:115 | approximate: Change slides manually (presentationdialog.ui:421), the inverse |
| Set Up | Show Media Controls | chk | chk | PLACEHOLDER `.uno:SlideShowOption?Option:string=mediacontrols` | family slot, I1 |  |
| Monitors | Monitor | combo | combo | `.uno:PresentationDialog` (widget `SlideShowMonitor`) | D:464; sdraw.sdi:2725 SID_PRESENTATION_DLG; drviewsh.sdi:115 | approximate: Presentation display (presentationdialog.ui:604) |
| Monitors | Use Presenter View | chk | chk | `.uno:PresentationDialog` (widget `SlideShowPresenterView`) | D:464; sdraw.sdi:2725 SID_PRESENTATION_DLG; drviewsh.sdi:115 | approximate: Presenter console (presentationdialog.ui:634) |

- Omitted: Present in Teams (cloud); Rehearse with Coach (cloud); Keep Slides Updated (cloud); Captions & Subtitles (cloud).

### Review (PowerPoint: Proofing, Accessibility, Insights, Language, Comments, Compare, Ink)

| Section | PowerPoint label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Proofing | Spelling | L | btn | `.uno:SpellDialog` | G:4295; svx.sdi:9937 SID_SPELL_DIALOG; _drvwsh.sdi:2511 |  |
| Proofing | Thesaurus | L | btn | `.uno:ThesaurusDialog` | G:4359; svx.sdi:8825 SID_THESAURUS; _drvwsh.sdi:425 |  |
| Accessibility | Check Accessibility | L | split | PLACEHOLDER `.uno:ReviewCheckAccessibility` | family slot, I1 | Calc family name; the accessibility checker panel is Writer-only (Sidebar.xcu:723-745, SwPanelFactory) |
| Language | Translate | S | btn | PLACEHOLDER `.uno:ReviewTranslate` | family slot, I1 | Calc and Writer family name (Calc decision 9, Writer decision 19); the cloud service is not built |
| Language | Language | S | dd | `.uno:ReviewLanguageMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | SetLanguageAllTextMenu; (separator); Hyphenation; ChineseConversion; HangulHanjaConversion; (separator); MoreDictionaries; Writer's name; Impress nodes |
| Comments | New Comment | L | btn | `.uno:InsertAnnotation` | G:2945; svx.sdi:4719 SID_INSERT_POSTIT; drviewsh.sdi:161 |  |
| Comments | Delete | L | split | `.uno:ReviewDeleteCommentMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | DeleteAnnotation; DeleteAllAnnotation; Writer's name; body item first (decision 10) |
| Comments | Previous | L | btn | `.uno:PreviousAnnotation` | D:2031; svx.sdi:4892 SID_PREVIOUS_POSTIT; drviewsh.sdi:186 | real in Impress (a placeholder in Writer) |
| Comments | Next | L | btn | `.uno:NextAnnotation` | D:2023; svx.sdi:4873 SID_NEXT_POSTIT; drviewsh.sdi:191 |  |
| Comments | Show Comments | L | split | `.uno:ShowAnnotations` | G:44; svx.sdi:4762 SID_TOGGLE_NOTES; drviewsh.sdi:156 | a toggle; the Comments pane item has no equivalent |
| Compare | Compare | S | btn | PLACEHOLDER `.uno:ReviewCompare?Action:string=compare` | family slot, I1 | no sd interface serves SID_DOCUMENT_COMPARE (sfx.sdi:738) |
| Compare | Accept | S | split | PLACEHOLDER `.uno:ReviewCompare?Action:string=accept` | family slot, I1 |  |
| Compare | Reject | S | split | PLACEHOLDER `.uno:ReviewCompare?Action:string=reject` | family slot, I1 |  |
| Compare | Previous | S | btn | PLACEHOLDER `.uno:ReviewCompare?Action:string=previous` | family slot, I1 |  |
| Compare | Next | S | btn | PLACEHOLDER `.uno:ReviewCompare?Action:string=next` | family slot, I1 |  |
| Compare | Reviewing Pane | S | tgl | PLACEHOLDER `.uno:ReviewCompare?Action:string=pane` | family slot, I1 |  |
| Compare | End Review | L | btn | PLACEHOLDER `.uno:ReviewCompare?Action:string=endreview` | family slot, I1 |  |
| Ink | Hide Ink | L | split | PLACEHOLDER `.uno:ReviewHideInk` | family slot, I1 | Calc and Writer family name |

Menu items (real commands; evidence as above):

- `.uno:SetLanguageAllTextMenu`: G:7675; a submenu filled by LanguageSelectionMenuController (Controller.xcu:155), no slot
- `.uno:Hyphenation`: D:472; sdraw.sdi:1522 SID_HYPHENATION; _drvwsh.sdi:2287
- `.uno:ChineseConversion`: G:3928; svx.sdi:9918 SID_CHINESE_CONVERSION; _docsh.sdi:38
- `.uno:HangulHanjaConversion`: G:3923; svx.sdi:9900 SID_HANGUL_HANJA_CONVERSION; _docsh.sdi:33
- `.uno:MoreDictionaries`: G:7688; sfx.sdi:5603 SID_MORE_DICTIONARIES; appslots.sdi:345
- `.uno:DeleteAnnotation`: D:2007; svx.sdi:4818 SID_DELETE_POSTIT; drviewsh.sdi:176
- `.uno:DeleteAllAnnotation`: D:2015; svx.sdi:4837 SID_DELETEALL_POSTIT; drviewsh.sdi:181

- Omitted: Smart Lookup (Insights, cloud).

### View (PowerPoint: Presentation Views, Master Views, Show, Zoom, Color/Grayscale, Window, Macros)

| Section | PowerPoint label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Presentation Views | Normal | L | btn | `.uno:NormalMultiPaneGUI` | D:1779; sdraw.sdi:3905 SID_NORMAL_MULTI_PANE_GUI; ViewShellBase.sdi:40 |  |
| Presentation Views | Outline View | L | btn | `.uno:OutlineMode` | D:828; sdraw.sdi:2472 SID_OUTLINE_MODE; ViewShellBase.sdi:70 |  |
| Presentation Views | Slide Sorter | S | btn | `.uno:DiaMode` | D:842; sdraw.sdi:713 SID_SLIDE_SORTER_MODE; ViewShellBase.sdi:65 |  |
| Presentation Views | Notes Page | S | tgl | `.uno:NotesMode` | D:1179; sdraw.sdi:2401 SID_NOTES_MODE; ViewShellBase.sdi:75 |  |
| Presentation Views | Reading View | S | btn | PLACEHOLDER `.uno:ViewMode?Mode:string=reading` | family slot, I1 | Writer's family name, Impress variant |
| Master Views | Slide Master | S | btn | `.uno:SlideMasterPage` | D:525; sdraw.sdi:3142 SID_SLIDE_MASTER_MODE; ViewShellBase.sdi:85 |  |
| Master Views | Handout Master | S | btn | `.uno:HandoutMode` | D:1206; sdraw.sdi:1382 SID_HANDOUT_MASTER_MODE; ViewShellBase.sdi:80 |  |
| Master Views | Notes Master | S | btn | `.uno:NotesMasterPage` | D:533; sdraw.sdi:2384 SID_NOTES_MASTER_MODE; ViewShellBase.sdi:90 |  |
| Show | Ruler | chk | chk | `.uno:ShowRuler` | D:1003; svx.sdi:8187 SID_RULER; _drvwsh.sdi:1805 |  |
| Show | Gridlines | chk | chk | `.uno:GridVisible` | G:5123; svx.sdi:4249 SID_GRID_VISIBLE; _drvwsh.sdi:2222 |  |
| Show | Guides | chk | chk | `.uno:HelplinesVisible` | D:419; sdraw.sdi:1470 SID_HELPLINES_VISIBLE; _drvwsh.sdi:2227 | LO label Display Snap Guides |
| Show | Notes | L | tgl | `.uno:BottomPaneImpress` | D:27; sdraw.sdi:3886 SID_BOTTOM_PANE_IMPRESS; ViewShellBase.sdi:35 | LO label Notes Pane |
| Zoom | Zoom | L | btn | `.uno:Zoom` | G:1523; sfx.sdi:5884 SID_ATTR_ZOOM; _drvwsh.sdi:129 |  |
| Zoom | Fit to Window | L | btn | `.uno:ZoomPage` | G:2169; svx.sdi:9367 SID_SIZE_PAGE; _drvwsh.sdi:756 | LO label Entire Page |
| Color/Grayscale | Color/Grayscale | L | dd | `.uno:ViewColorGrayscaleMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | OutputQualityColor; OutputQualityGrayscale; OutputQualityBlackWhite |
| Window | New Window | L | btn | `.uno:NewWindow` | G:4091; sfx.sdi:2815 SID_NEWWINDOW; frmslots.sdi:215 |  |
| Window | Arrange All | I | btn | PLACEHOLDER `.uno:ViewArrangeAll` | family slot, I1 | Calc and Writer family name |
| Window | Cascade | I | btn | PLACEHOLDER `.uno:ViewCascade` | family slot, I1 |  |
| Window | Move Split | I | btn | PLACEHOLDER `.uno:ViewSplit` | family slot, I1 | Writer family name |
| Window | Switch Windows | L | dd | `.uno:ViewSwitchWindowsMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | the open windows (controller); WindowListMenuController (Controller.xcu:1132), Calc's name |
| Macros | Macros | L | dd | `.uno:ViewMacrosMenu` (new menu) | new: D label, Controller.xcu Popup+ToolBox, sd popupmenu | RunMacro; MacroRecorder; MacroManager; BasicIDEAppear; Calc and Writer name; Macro Manager shows only with experimental mode (Writer W8a) |

Menu items (real commands; evidence as above):

- `.uno:OutputQualityColor`: D:667; sdraw.sdi:2509 SID_OUTPUT_QUALITY_COLOR; _drvwsh.sdi:2347
- `.uno:OutputQualityGrayscale`: D:675; sdraw.sdi:2547 SID_OUTPUT_QUALITY_GRAYSCALE; _drvwsh.sdi:2352
- `.uno:OutputQualityBlackWhite`: D:683; sdraw.sdi:2490 SID_OUTPUT_QUALITY_BLACKWHITE; _drvwsh.sdi:2357
- `.uno:RunMacro`: G:5957; sfx.sdi:2436 SID_RUNMACRO; appslots.sdi:282
- `.uno:MacroRecorder`: G:5606; sfx.sdi:3534 SID_RECORDMACRO; frmslots.sdi:75
- `.uno:MacroManager`: G:5965; sfx.sdi:2454 SID_MACROMANAGER; appslots.sdi:291
- `.uno:BasicIDEAppear`: G:1897; sfx.sdi:397 SID_BASICIDE_APPEAR; appslots.sdi:267

- Launchers (not built): Show: Grid and Guides dialog (no single LibreOffice dialog: the grid is in Tools > Options > LibreOffice Impress > Grid).

### Help (PowerPoint: Help), new page

| Section | PowerPoint label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Help | Help | L | btn | `.uno:HelpIndex` | G:1782; sfx.sdi:1909 SID_HELPINDEX; appslots.sdi:40 |  |
| Help | Contact Support | L | btn | `.uno:QuestionAnswers` | G:5774; sfx.sdi:5156 SID_Q_AND_A; appslots.sdi:131 | Calc's and Writer's Get Help Online |
| Help | Feedback | L | btn | PLACEHOLDER `.uno:HelpFeedback` | family slot, I1 | Calc and Writer family name |
| Help | Show Training | L | btn | `.uno:Documentation` | G:5790; sfx.sdi:5171 SID_DOCUMENTATION; appslots.sdi:135 | User Guides |
| Help | What's New | L | btn | `.uno:WhatsNew` | G:5806; sfx.sdi:5216 SID_WHATSNEW; appslots.sdi:147 |  |

## 2. LibreOffice-only buttons that leave the tabs

The ribbon replaces the content of six stock pages ("Home Tab", Insert, Layout, SlideShow, Review, View) and keeps
the stock Design page's only control, the theme colors box. Those pages and their overflow menus hold commands that
PowerPoint's layout does not have. They leave the ribbon and stay reachable in the menu bar (decision 31).

**70 rows, 68 distinct commands**: `.uno:PresentationLayout` is on the Home and Layout pages, and
`.uno:CapturePoint` is in the Insert menu and on the View page. By class, as in Writer:

- **a (62)**: the same command is in the menu bar, at the path given;
- **b (3)**: an equivalent menu-bar entry does the job (HangingIndent, ObjectPosition, ChangeTheme);
- **c (4)**: no menu-bar entry; the Fontwork toolbar, which View > Toolbars lists (Writer ruling 2, Calc decisions
  19-20);
- **q (1)**: `.uno:Menubar`, in the quick access bar, as in Calc and Writer.

"Was on" says where the command was: the page, its overflow menu, or both. Menu-bar paths are from
`sd/uiconfig/simpress/menubar/menubar.xml` (line given), with LibreOffice's labels. Commands that the new layout
keeps somewhere on the ribbon are not listed (they are in the section 1 tables).

Kept, not leaving:

- `.uno:InsertSlide` and `.uno:DuplicateSlide` (stock Home, `notebookbar.ui:3139-3176`) are aliases whose targets
  stay: `.uno:InsertSlide` has TargetURL `.uno:InsertPage` (D:866), New Slide's command, and `.uno:DuplicateSlide`
  has TargetURL `.uno:DuplicatePage` (D:493), which New Slide's popup dispatches
  (`slidelayoutcontroller.cxx:217`, `:262`).
- `.uno:PresentationMinimizer` (stock "Menu Slide Show", `notebookbar.ui:1805-1808`) stays in the stock "Menu Tools"
  (`:2064-2067`) of the Tools tab, which the feature does not touch.

### Home (23)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:PresentationLayout` | page | D:1152; sdraw.sdi:2793 SID_PRESENTATION_LAYOUT; _drvwsh.sdi:494 | Slide > Change Slide Master... (menubar.xml:550) | a |
| `.uno:SubScript` | page | G:4593; svx.sdi:8510 SID_SET_SUB_SCRIPT; _drvwsh.sdi:2893 | Format > Text > Subscript (menubar.xml:322) | a |
| `.uno:SuperScript` | page | G:4577; svx.sdi:8580 SID_SET_SUPER_SCRIPT; _drvwsh.sdi:2888 | Format > Text > Superscript (menubar.xml:321) | a |
| `.uno:StartPara` | page | G:1943; svx.sdi:5439 SID_ATTR_PARA_ADJUST_START; _drvwsh.sdi:1730 | Format > Align Text > Start (menubar.xml:361) | a |
| `.uno:EndPara` | page | G:1954; svx.sdi:5457 SID_ATTR_PARA_ADJUST_END; _drvwsh.sdi:1735 | Format > Align Text > End (menubar.xml:363) | a |
| `.uno:IncrementIndent` | page | G:5343; svx.sdi:10517 SID_INC_INDENT; drtxtob.sdi:244 | Format > Spacing > Increase Indent (menubar.xml:355) | a |
| `.uno:DecrementIndent` | page | G:5329; svx.sdi:10535 SID_DEC_INDENT; drtxtob.sdi:250 | Format > Spacing > Decrease Indent (menubar.xml:356) | a |
| `.uno:HangingIndent` | page | G:5357; svx.sdi:13036 SID_HANGING_INDENT; drtxtob.sdi:262 | Format > Paragraph... (`.uno:ParagraphDialog`, menubar.xml:399), the indent fields (inferred: the field was not read) | b |
| `.uno:ParaspaceIncrease` | page | G:160; svx.sdi:12986 SID_PARASPACE_INCREASE; drtxtob.sdi:232 | Format > Spacing > Increase Paragraph Spacing (menubar.xml:352) | a |
| `.uno:ParaspaceDecrease` | page | G:174; svx.sdi:12969 SID_PARASPACE_DECREASE; drtxtob.sdi:238 | Format > Spacing > Decrease Paragraph Spacing (menubar.xml:353) | a |
| `.uno:OutlineFont` | menu | G:1705; svx.sdi:6346 SID_ATTR_CHAR_CONTOUR; _drvwsh.sdi:2868 | Format > Text > Outline Font Effect (menubar.xml:325) | a |
| `.uno:Overline` | menu | G:1774; svx.sdi:9085 SID_ATTR_CHAR_OVERLINE; _drvwsh.sdi:2828 | Format > Text > Overline (menubar.xml:319) | a |
| `.uno:ChangeCaseRotateCase` | menu | G:3213; svx.sdi:1171 SID_TRANSLITERATE_ROTATE_CASE; _drvwsh.sdi:2417 | Format > Text > Cycle Case (menubar.xml:332) | a |
| `.uno:InsertNonBreakingSpace` | menu | G:7549; svx.sdi:11359 FN_INSERT_HARD_SPACE; _drvwsh.sdi:375 | Insert > Formatting Mark > No-break Space (menubar.xml:252) | a |
| `.uno:InsertHardHyphen` | menu | G:7527; svx.sdi:11342 FN_INSERT_HARDHYPHEN; _drvwsh.sdi:370 | Insert > Formatting Mark > Non-breaking Hyphen (menubar.xml:253) | a |
| `.uno:InsertSoftHyphen` | menu | G:7538; svx.sdi:11325 FN_INSERT_SOFT_HYPHEN; _drvwsh.sdi:365 | Insert > Formatting Mark > Soft Hyphen (menubar.xml:254) | a |
| `.uno:InsertZWSP` | menu | G:7571; svx.sdi:11257 SID_INSERT_ZWSP; _drvwsh.sdi:395 | Insert > Formatting Mark > Zero-width Space (menubar.xml:256) | a |
| `.uno:InsertWJ` | menu | G:7582; svx.sdi:11274 SID_INSERT_WJ; _drvwsh.sdi:400 | Insert > Formatting Mark > Word Joiner (menubar.xml:257) | a |
| `.uno:InsertLRM` | menu | G:7593; svx.sdi:11291 SID_INSERT_LRM; _drvwsh.sdi:390 | Insert > Formatting Mark > Left-to-Right Mark (menubar.xml:258) | a |
| `.uno:InsertRLM` | menu | G:7604; svx.sdi:11308 SID_INSERT_RLM; _drvwsh.sdi:385 | Insert > Formatting Mark > Right-to-Left Mark (menubar.xml:259) | a |
| `.uno:FontDialog` | menu | G:7225; svx.sdi:3071 SID_CHAR_DLG; _drvwsh.sdi:337 | Format > Character... (menubar.xml:398) | a |
| `.uno:ParagraphDialog` | menu | G:4609; svx.sdi:6618 SID_PARA_DLG; _drvwsh.sdi:348 | Format > Paragraph... (menubar.xml:399) | a |
| `.uno:RestoreEditingView` | menu | D:93; sfx.sdi:2741 SID_RESTORE_EDITING_VIEW; ViewShellBase.sdi:140 | Slide > Jump to Last Edited Slide (menubar.xml:562) | a |

### Insert (9)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:FontworkShapeType` | page | G:100; svx.sdi:10314 SID_FONTWORK_SHAPE_TYPE; _drvwsh.sdi:2611 | **none**: only the Fontwork toolbar (sd/uiconfig/simpress/toolbar/fontworkobjectbar.xml:23-27), which View > Toolbars (`.uno:AvailableToolbars`, menubar.xml:123) lists (ImpressWindowState.xcu:421-432) | c |
| `.uno:FontworkSameLetterHeights` | page | G:108; svx.sdi:10332 SID_FONTWORK_SAME_LETTER_HEIGHTS; _drvwsh.sdi:2631 | **none**: only the Fontwork toolbar (sd/uiconfig/simpress/toolbar/fontworkobjectbar.xml:23-27), which View > Toolbars (`.uno:AvailableToolbars`, menubar.xml:123) lists (ImpressWindowState.xcu:421-432) | c |
| `.uno:FontworkAlignmentFloater` | page | G:116; svx.sdi:10349 SID_FONTWORK_ALIGNMENT_FLOATER; _drvwsh.sdi:2616 | **none**: only the Fontwork toolbar (sd/uiconfig/simpress/toolbar/fontworkobjectbar.xml:23-27), which View > Toolbars (`.uno:AvailableToolbars`, menubar.xml:123) lists (ImpressWindowState.xcu:421-432) | c |
| `.uno:FontworkCharacterSpacingFloater` | page | G:124; svx.sdi:10366 SID_FONTWORK_CHARACTER_SPACING_FLOATER; _drvwsh.sdi:2621 | **none**: only the Fontwork toolbar (sd/uiconfig/simpress/toolbar/fontworkobjectbar.xml:23-27), which View > Toolbars (`.uno:AvailableToolbars`, menubar.xml:123) lists (ImpressWindowState.xcu:421-432) | c |
| `.uno:AnimationObjects` | menu | D:1128; sdraw.sdi:71 SID_ANIMATION_OBJECTS; drviewsh.sdi:30 | Insert > Media > Animated Image... (menubar.xml:209) | a |
| `.uno:TwainSelect` | menu | G:4729; svx.sdi:9028 SID_TWAIN_SELECT; _drvwsh.sdi:2096 | Insert > Media > Scan > Select Source... (menubar.xml:205) | a |
| `.uno:InsertQrCode` | menu | G:7902; svx.sdi:13157 SID_INSERT_QRCODE; _drvwsh.sdi:2981 | Insert > OLE Object > QR and Barcode... (menubar.xml:215) | a |
| `.uno:CapturePoint` | menu | D:992; sdraw.sdi:246 SID_CAPTUREPOINT; _drvwsh.sdi:1795 | Insert > Insert Snap Guide... (menubar.xml:242) | a |
| `.uno:InsertSlidesField` | menu | D:624 (TargetURL `.uno:InsertPagesField`); sdraw.sdi:1744 SID_INSERT_FLD_PAGES; _drvwsh.sdi:2327 | Insert > Field > Slide Count (menubar.xml:274) | a |

### Layout (now Transitions) (15)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:MoveSlideUp` | page + menu | D:2212 (TargetURL `.uno:MovePageUp`); sdraw.sdi:4079 SID_MOVE_PAGE_UP; SlideSorterController.sdi:341 | Slide > Move > Slide Up (menubar.xml:566) | a |
| `.uno:MoveSlideDown` | page + menu | D:2237 (TargetURL `.uno:MovePageDown`); sdraw.sdi:4096 SID_MOVE_PAGE_DOWN; SlideSorterController.sdi:346 | Slide > Move > Slide Down (menubar.xml:567) | a |
| `.uno:ShowSlide` | page + menu | D:130; sdraw.sdi:1505 SID_SHOW_SLIDE; SlideSorterController.sdi:179 | Slide > Show Slide (menubar.xml:558); also on the contextual Master tab | a |
| `.uno:RenameSlide` | page + menu | D:61 (TargetURL `.uno:RenamePage`); sdraw.sdi:2898 SID_RENAMEPAGE; _drvwsh.sdi:185 | Slide > Rename Slide... (menubar.xml:560) | a |
| `.uno:PresentationLayout` | page + menu | D:1152; sdraw.sdi:2793 SID_PRESENTATION_LAYOUT; _drvwsh.sdi:494 | Slide > Change Slide Master... (menubar.xml:550) | a |
| `.uno:DisplayMasterBackground` | page + menu | D:1541; sdraw.sdi:3675 SID_DISPLAY_MASTER_BACKGROUND; _drvwsh.sdi:2788 | Slide > Master Background (menubar.xml:554) | a |
| `.uno:DisplayMasterObjects` | page + menu | D:1549; sdraw.sdi:3691 SID_DISPLAY_MASTER_OBJECTS; _drvwsh.sdi:2793 | Slide > Master Objects (menubar.xml:555) | a |
| `.uno:ObjectAlign` | page | G:7196; svx.sdi:6087 SID_OBJECT_ALIGN; _drvwsh.sdi:1340 | Format > Align Objects (menubar.xml:493) | a |
| `.uno:ObjectPosition` | page | D:917; sdraw.sdi:2419 SID_POSITION; _drvwsh.sdi:1356 | Format > Arrange (`.uno:ArrangeMenu`, menubar.xml:494), the same commands as its sub-toolbar | b |
| `.uno:DeleteSlide` | menu | D:1222 (TargetURL `.uno:DeletePage`); sdraw.sdi:661 SID_DELETE_PAGE; _drvwsh.sdi:1548 | Slide > Delete Slide (menubar.xml:544) | a |
| `.uno:ModifyPage` | menu | D:1025; sdraw.sdi:2088 SID_MODIFYPAGE; drviewsh.sdi:20 | View > Slide Layout (menubar.xml:162) | a |
| `.uno:SelectBackground` | menu | D:1525; sdraw.sdi:3641 SID_SELECT_BACKGROUND; _drvwsh.sdi:2733 | Slide > Set Background Image... (menubar.xml:547); also on the contextual Master tab | a |
| `.uno:InsertMasterPage` | menu | D:1570; sdraw.sdi:3574 SID_INSERT_MASTER_PAGE; _drvwsh.sdi:2713 | Slide > New Master (menubar.xml:551); also on the contextual Master tab | a |
| `.uno:DeleteMasterPage` | menu | D:1578; sdraw.sdi:3594 SID_DELETE_MASTER_PAGE; _drvwsh.sdi:2718 | Slide > Delete Master (menubar.xml:552); also on the contextual Master tab | a |
| `.uno:ExpandPage` | menu | D:504; sdraw.sdi:871 SID_EXPAND_PAGE; drviewsh.sdi:128 | Slide > Expand Slide (menubar.xml:582) | a |

### Design (0)

Nothing leaves.

### Slide Show (2)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:SlideChangeWindow` | page + menu | D:451; sdraw.sdi:3106 SID_SLIDE_TRANSITIONS_PANEL; drviewsh.sdi:50 | View > Slide Transition (menubar.xml:163) | a |
| `.uno:Remote` | menu | D:98; sdraw.sdi:2742 SID_REMOTE_DLG; drviewsh.sdi:119 | Slide Show > Impress Remote... (menubar.xml:593) | a |

### Review (3)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:SpellOnline` | page + menu | G:5507; svx.sdi:8366 SID_AUTOSPELL_CHECK; _drvwsh.sdi:2201 | Tools > Automatic Spell Checking (menubar.xml:601) | a |
| `.uno:RedactDoc` | page | G:5713; sfx.sdi:5102 SID_REDACTDOC; docslots.sdi:251 | Tools > Redact (menubar.xml:617) | a |
| `.uno:EditDoc` | page | G:3422; sfx.sdi:1052 SID_EDITDOC; frmslots.sdi:220 | Edit > Edit Mode (menubar.xml:109) | a |

### View (18)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:ZoomMode` | page | D:1612; sdraw.sdi:3438 SID_ZOOM_MODE; _drvwsh.sdi:736 | View > Zoom > Zoom & Pan (menubar.xml:183) | a |
| `.uno:ZoomPageWidth` | page | G:3741; svx.sdi:9385 SID_SIZE_PAGE_WIDTH; _drvwsh.sdi:766 | View > Zoom > Page Width (menubar.xml:174) | a |
| `.uno:ZoomNext` | page | G:5107; sfx.sdi:4937 SID_ZOOM_NEXT; _drvwsh.sdi:721 | View > Zoom > Zoom Next (menubar.xml:185) | a |
| `.uno:ZoomPrevious` | page | G:5115; sfx.sdi:4973 SID_ZOOM_PREV; _drvwsh.sdi:726 | View > Zoom > Zoom Previous (menubar.xml:184) | a |
| `.uno:Sidebar` | page + menu | G:4858; sfx.sdi:2687 SID_SIDEBAR; frmslots.sdi:46 | View > Sidebar (menubar.xml:161) | a |
| `.uno:LeftPaneImpress` | page + menu | D:1795; sdraw.sdi:3848 SID_LEFT_PANE_IMPRESS; ViewShellBase.sdi:25 | View > Slide Pane (menubar.xml:126) | a |
| `.uno:Menubar` | page + menu | G:7771; sfx.sdi:2705 SID_MENUBAR; appslots.sdi:224 | quick access bar, first item (sd/uiconfig/simpress/toolbar/notebookbarshortcuts.xml:11), as in Calc and Writer | q |
| `.uno:ToggleTabBarVisibility` | page + menu | D:1195; sdraw.sdi:2155 SID_TOGGLE_TABBAR_VISIBILITY; ViewShellBase.sdi:50 | View > Views Tab Bar (menubar.xml:127) | a |
| `.uno:ChangeTheme` | page | G:1491; sfx.sdi:6004 FN_CHANGE_THEME; appslots.sdi:67 | Tools > Options... (`.uno:OptionsTreeDialog`, menubar.xml:659) > LibreOffice > Appearance (inferred: the page was not read) | b |
| `.uno:CapturePoint` | page | D:992; sdraw.sdi:246 SID_CAPTUREPOINT; _drvwsh.sdi:1795 | Insert > Insert Snap Guide... (menubar.xml:242) | a |
| `.uno:SnapPoints` | page | D:1469; sdraw.sdi:3195 SID_SNAP_POINTS; _drvwsh.sdi:2262 | View > Snap Guides > Snap to Object Points (menubar.xml:147) | a |
| `.uno:SnapBorder` | page | D:1453; sdraw.sdi:3159 SID_SNAP_BORDER; _drvwsh.sdi:2252 | View > Snap Guides > Snap to Page Margins (menubar.xml:148) | a |
| `.uno:GridUse` | page + menu | G:4121; svx.sdi:4230 SID_GRID_USE; _drvwsh.sdi:2247 | View > Snap Guides > Snap to Grid (menubar.xml:144) | a |
| `.uno:HelplinesUse` | page + menu | D:1445; sdraw.sdi:1452 SID_HELPLINES_USE; _drvwsh.sdi:2237 | View > Snap Guides > Snap to Snap Guides (menubar.xml:145) | a |
| `.uno:SnapFrame` | page | D:1461; sdraw.sdi:3177 SID_SNAP_FRAME; _drvwsh.sdi:2257 | View > Snap Guides > Snap to Object Border (menubar.xml:146) | a |
| `.uno:HelplinesMove` | page | G:4105; svx.sdi:4325 SID_HELPLINES_MOVE; _drvwsh.sdi:2242 | View > Grid and Helplines > Helplines While Moving (menubar.xml:136) | a |
| `.uno:StatusBarVisible` | menu | G:5835; sfx.sdi:4335 SID_TOGGLESTATUSBAR; frmslots.sdi:70 | View > Status Bar (menubar.xml:125) | a |
| `.uno:Zoom100Percent` | menu | G:2140; svx.sdi:9313 SID_SIZE_REAL; _drvwsh.sdi:751 | View > Zoom > 100% (menubar.xml:179) | a |

## 3. How it is built

The Impress ribbon is built exactly like Calc's and Writer's: `sd/uiconfig/simpress/ui/notebookbar_office.ui` is
the stock `notebookbar.ui` plus the tab operations of `product/ui/impress_tabs.json` plus one generated page per
`product/ui/impress_<tab>.json`. Nothing in the office `.ui` is edited by hand.

### 3.1 Generator for a third app

- **App entry** in `product/ui/gen_ribbon.py` (`class App` `:60-69`, `APPS` `:72-79`):

  ```python
  "impress": App("sd/uiconfig/simpress/ui/notebookbar.ui", "sd/uiconfig/simpress/ui/notebookbar_office.ui",
                 "solenv/sanitizers/ui/modules/simpress.suppr", None, "impress", "impress_tabs.json",
                 "TabbedImpress", "DrawImpressCommands.xcu"),
  ```

  `false` is `None`: `solenv/sanitizers/ui/modules/` has `simpress.suppr` and no `simpress.false`, and
  `regenerate_app` skips a `None` file (`gen_ribbon.py:589-603`). `--all` then rebuilds three apps; `--app` accepts
  `impress` through `choices=APPS` (`:611`). The labels come from `DrawImpressCommands.xcu`, then
  `GenericCommands.xcu`, as the `commands` field says.
- **Tab operations** (`product/ui/impress_tabs.json`; the operations are the ones `apply_tabs` knows,
  `gen_ribbon.py:512-530`). The final file, built up task by task (decision 7):

  ```json
  {
    "relabel": [{"id": "LayoutLabel", "from": "~Layout", "to": "Tra~nsitions"}],
    "properties": [
      {"id": "Home Tab", "name": "valign", "from": "center", "to": "fill"},
      {"id": "Layout", "name": "valign", "from": "center", "to": "fill"}
    ],
    "move": [{"page": "Design", "tab": "DesignLabel", "before": "Layout"}],
    "positions": {
      "Design": 3, "DesignLabel": 3, "Layout": 4, "LayoutLabel": 4,
      "SlideShow": 6, "SlideShowLabel": 6, "Review": 7, "ReviewLabel": 7, "View": 8, "ViewLabel": 8,
      "Table": 9, "TableLabel": 9, "Image": 10, "ImageLabel": 10, "Draw": 11, "DrawLabel": 11,
      "Object": 12, "ObjectLabel": 12, "Media": 13, "MediaLabel": 13, "Form": 14, "FormLabel": 14,
      "Master": 15, "MasterLabel": 15, "Outline": 16, "OutlineLabel": 16, "3D": 17, "3DObjectLabel": 17,
      "Extension": 18, "ExtensionLabel": 18, "Tools": 19, "ToolsLabel": 19
    },
    "add_pages": [
      {"page": "Animations", "prefix": "Animations", "after_tab": "LayoutLabel", "position": 5,
       "tab_id": "AnimationsLabel", "label": "~Animations", "context": "TabbedImpress|AnimationsTabLabel"},
      {"page": "Help", "prefix": "Help", "after_tab": "ToolsLabel", "position": 20,
       "tab_id": "HelpLabel", "label": "Hel~p", "context": "TabbedImpress|HelpTabLabel"}
    ]
  }
  ```

  The ids are the stock ones (`notebookbar.ui`: pages `:2962` "Home Tab", `:5006` Layout, `:5623` Design, `:5735`
  SlideShow, `:6235` Review, `:6778` View, `:7717` Table ... `:14362` Tools; labels `:3922` ... `:14666`; the 3D
  label is `3DObjectLabel` `:14219`). Stock positions end at Tools 18 (`:14662`, `:14673`).
- **Page layouts**: `product/ui/impress_home.json` (page "Home Tab", prefix Home), `impress_insert.json` (Insert),
  `impress_design.json` (Design), `impress_transitions.json` (page Layout, prefix Transitions),
  `impress_animations.json` (Animations), `impress_slideshow.json` (SlideShow), `impress_review.json` (Review),
  `impress_view.json` (View), `impress_help.json` (Help). Each replaced stock page lists its overflow menu in
  `remove_objects`, as Calc and Writer do (`product/ui/writer_layout.json:5`): "Menu Home" (`notebookbar.ui:809`),
  "Menu Insert" (`:1115`), "Menu Slide" (`:1541`, the Layout page's), "Menu Slide Show" (`:1714`), "Menu Review"
  (`:1475`), "Menu View" (`:2111`). The stock Design page has no overflow menu.
- **Widget ids** are `btn<prefix><cmd>`; a URL used twice on one page gets a distinct `cmd` and the real URL as
  `action` (decision 16).
- **Registration**: one line `sd/uiconfig/simpress/ui/notebookbar_office \` in the uifiles list of
  `sd/UIConfig_simpress.mk` (block from `:111`), after `notebookbar_groupedbar_compact` (`:153`), as Writer
  (`sw/UIConfig_swriter.mk:283`) and Calc (`sc/UIConfig_scalc.mk:208`); the new popup files go into the
  popupmenufiles block (`:16-...`).
- **Suppressions**: `simpress.suppr` has 639 lines for the stock `notebookbar.ui`; I0a seeds the same lines with the
  office path, then `sync_suppr` keeps them in line (it drops lines of ids that are gone and adds button-no-label
  for new tool buttons, `gen_ribbon.py:572-582`).
- **Checks**: `product/dev/check-ui.sh` takes the module from the path (`simpress`), so it needs no change for the
  file itself; I0a confirms that by running it.
- **Test helpers** become three-app: `product/tests/commands.py` (`LOOKUP_ORDERS` `:15-18` gains
  `("DrawImpressCommands.xcu", "GenericCommands.xcu")`; `controller_nodes` `:55-70` filters an `Impress` node
  suffix as it filters Writer's), `product/tests/placeholders.py` (`REGISTRIES` `:22` gains
  `placeholders_impress.json`), `product/tests/office.py` (`app()` `:19`).

### 3.2 Mode, picker, profile, launcher, screenshots, UITests

- **Mode**: `officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu`, Impress node `:602`, gains
  `TabbedOffice` with MenuPosition 9 (the Impress modes use 0, 1, 3, 4, 5, 6, 7, 8: `:614` ... `:829`) and
  CommandArg `notebookbar_office.ui`, copied from Calc's node (`:437-464`). Draw's node (`:857`) is not touched.
- **Picker**: `cui/source/dialogs/uitabpage.cxx` `UITabPage::HasTabbedOffice` (`:93-96`) adds `u"Impress"`;
  `GetModeForApp` (`:98-103`) and the welcome dialog (`cui/source/dialogs/welcomedlg.cxx:139-163`) follow it. The
  preview picture is `notebookbar_office_impress.png`, found by W0b's per-app lookup; I11 adds it to
  `vcl/Package_toolbarmode.mk`.
- **Profile**: `product/dev/profile.py` `APPS` (`:18`) gains `"impress": "Impress"`; `build_items` (`:38`) also writes
  `org.openoffice.Office.Impress/Misc/NewDoc/AutoPilot` = false (schema `Impress.xcs:593-599`, default true, read in
  `sd/source/ui/app/optsitem.cxx:264`), so a new presentation opens without the template dialog in the dev profile.
- **Launcher**: `product/dev/office.sh` gets an `impress` case (`:27-28` pattern) with the profile
  `/mnt/games/libreoffice/try-profile-impress`.
- **Screenshots**: `product/dev/shot-tab.sh` gets `--app impress` (`:24-26`), `App=Impress` (`:45`), the profile
  guard (`:50`), the tab list `File,Home,Insert,Design,Transitions,Animations,Slide Show,Review,View,Extension,Tools,Help`
  (`:61-62`) and an `x0` measured in I0b (`:63-66`).
- **UITests**: `product/dev/uitest.sh` maps `--app impress` to `impress_tests2` (`:4-25`). The scaffold is
  `sd/qa/uitest/impress_tests2/notebookbarOffice.py`; the target adds the whole directory
  (`sd/UITest_impress_tests2.mk:10-11`) with `TDOC=sd/qa/uitest/data` (`:15`), so no new gbuild target is needed.
  The UITest profile is fresh, so the template dialog opens first: close it through its "close" button, as
  `sd/qa/uitest/impress_tests2/tdf130440.py:16-19` does. Writer's lessons apply: select tabs with
  `executeAction("SELECT", {"POS": ...})` (`sw/qa/uitest/writer_tests8/notebookbarOffice.py:153`), never a tab CLICK
  on the headless backend; wait with `settle` (`:401`); open only Impress documents.
- **Tests that change**: `product/tests/test_profile.py:99`, `test_calc_launcher.py:145` and
  `test_uitest_script.py:70` use `impress` as the invalid app and switch to another one (`draw`);
  `test_writer_mode.py:52-70` and `:84` assert that Impress has no TabbedOffice and are inverted or moved to
  `test_impress_mode.py`.

### 3.3 Placeholder slots in sd

- **Block**: `#define SID_BOOST (SID_SD_START+900)` in `sd/inc/app.hrc`, after the last define
  (`SID_REMOVE_SLIDE_SECTION_AND_SLIDES (SID_SD_START+458)`, `:437`). `SID_SD_START` is 27000
  (`include/svl/solar.hrc:73`, range to 27999 `:74`), so the slots are 27900-27923 (`SID_BOOST + 0..23`, section 5).
  No define uses `SID_SD_START + 459..999` today.
- **Declarations**: 24 entries in `sd/sdi/sdraw.sdi`, in the format of `AddSlideSection` (`:4269-4285`: SfxVoidItem,
  AutoUpdate FALSE, ReadOnlyDoc FALSE, AccelConfig/MenuConfig/ToolBoxConfig, GroupId).
- **State**: the 24 slots in `interface ViewShellBaseView` (`sd/sdi/ViewShellBase.sdi:19`) with `StateMethod =
  GetState` and no ExecMethod; `ViewShellBase::GetState` (`sd/source/ui/view/ViewShellBase.cxx:706-711`) disables
  them first, before `mpImpl->GetSlotState`, which returns early when there is no DrawController (`:1357-1364`).
  ViewShellBase is under every Impress view (Normal, Outline, Slide Sorter, Notes, masters), so one place covers
  them all (decision 23). `ViewShellBase.sdi` is included only by `sdslots.sdi:88` (Impress), not by Draw's
  `sdgslots.sdi`; `sdraw.sdi` is in both (`sdslots.sdi:77`, `sdgslots.sdi:76`), so Draw knows the declarations but
  no Draw shell serves them.
- **Labels**: one node per placeholder command and URL variant in `DrawImpressCommands.xcu`, with PowerPoint's
  wording (there is no LibreOffice wording for a missing feature), and an explicit icon for every variant (Writer
  lesson: a `?` variant has no icon of its own).
- **Registry and test**: `product/tests/placeholders_impress.json` (slot, offset, command, variants, labels; the
  `placeholders_writer.json` shape) and `product/tests/test_impress_slots.py`, after `test_writer_slots.py`.

### 3.4 Accent

- **Value**: `accent.impress` = `["#C43E1C", "#FF8F6B"]` (light, dark) in `product/themes/palette.json`, and
  `"Impress": "accent.impress"` in its `tab_accents` map.
- **Source (inferred)**: #C43E1C is PowerPoint's orange in the 2019+ Office app-icon family, the family of Word's
  #185ABD that W9a uses for Writer (`palette.json:14`). Microsoft's Fluent 2 color page
  (https://fluent2.microsoft.design/color) shows the PowerPoint swatch only as an image, so no primary text source
  confirms the hex. The dark value #FF8F6B is a lighter tint of the same hue, picked for contrast.
- **Contrast** (WCAG relative luminance, computed): #C43E1C on white 5.18:1; #FF8F6B on #2B2B2B 6.33:1 (Calc's
  dark #5CC27E: 6.39:1; Calc's light #1B7A3E: 5.38:1).
- **Mechanism**: W9a's, landed in d8c601d40: `build_schemes.py:85-100` writes `AccentColor` and `AccentColorDark` per
  app from `tab_accents` (`palette.json:32`), and `lcl_getTabAccentColor` (`NotebookbarTabControl.cxx:156`) reads
  ToolbarMode `Applications/<App>`; its switch already maps `Application::Impress` to `Impress` (`:164`). So
  Impress's accent is data only: the `accent.impress` token, the `tab_accents` entry and a scheme test (task I9).

### 3.5 Icons, menus and labels

- Grey line icons (ruling 8); new menus and placeholders need manifest entries in `product/icons/manifest.json`;
  commands shared with Calc and Writer keep their icons.
- Disabled popup entries show greyed once T10w (W9c) lands; the Impress popups are static files and existing
  controllers, so they follow without extra work.
- Ruling T9: every layout item has PowerPoint's label in `office_label`; new label nodes in
  `DrawImpressCommands.xcu` use LibreOffice wording where a feature exists.

## 4. Decisions

These are the designer's rulings under ruling 9 (the controller rules and records; the user can overturn any of
them). Each one gives its reason.

1. **Reference**: PowerPoint for Microsoft 365, Windows, Current Channel, 2024+ look, 1920 px (research `:5`), as
   Calc and Writer.
2. **Tab set and order**: File, Home, Insert, Design, Transitions, Animations, Slide Show, Review, View, the stock
   contextual tabs, Extension, Tools, Help. Extension and Tools stay with their content, and Help goes last after
   Tools, as in Calc (Calc decision 3) and Writer (Writer decisions 2-3).
3. **Not in this feature**: the File backstage and PowerPoint's contextual tabs (research `:683-705`); Impress's stock
   contextual tabs (Table, Image, Draw, Object, Media, Form, Master, Outline, 3D) stay exactly as they are. Same
   scope line as Writer (Writer decision 4).
4. **PowerPoint's Record tab is out.** Its ten controls (research `:647-668`) are either duplicates or features
   LibreOffice lacks: From Beginning and From Current Slide record narration (Slide Show > Record is already a
   placeholder here); Screen Recording is on Insert > Media (placeholder); Audio is Insert > Audio's Record Audio;
   Save as Show and Export to Video are File (backstage) features; Cameo is on the do-not-build list (research
   `:654`, `:733-737`); Preview and Clear Recording act on recordings LibreOffice cannot make. Built, the tab would be
   almost all greyed placeholders that repeat other tabs, which helps nobody. Record Audio is omitted with it.
5. **PowerPoint's Draw tab is out.** It is an ink tab (pens, highlighter, eraser, lasso select, Draw with Touch, Ink to
   Shape, Ink Replay, research `:613-643`); Impress has no ink objects in edit mode (inferred: no pen or ink
   command exists in `DrawImpressCommands.xcu`; the freehand line `.uno:Freeline_Unfilled` is a shape tool and is
   on Home > Drawing's menu). Its name also clashes with Impress's contextual `~Draw` tab (`notebookbar.ui:9283`,
   label `:10406`). Writer left Word's Draw tab out for the same reason (Writer decision 4).
6. **Transitions is the stock Layout page, relabelled.** `relabel` changes `LayoutLabel` from `~Layout` to
   `Tra~nsitions`; the page keeps its id and position, and its content is generated. Its stock content is slide
   management that PowerPoint keeps on Home or in menus (15 commands, section 2). Reason: the generator has no
   operation that removes a page (`apply_tabs`: relabel, properties, move, positions, add_pages,
   `gen_ribbon.py:512-530`); a new Transitions page next to an emptied Layout page would need a shared-code change,
   and Calc relabelled its Layout tab the same way (`calc_tabs.json:2-5`).
7. **Animations and Help are new pages, and Design moves before Transitions** (`add_pages`, `move`, `positions`,
   section 3.1). Mnemonics: the new letters N (Tra~nsitions), A (~Animations) and P (Hel~p) are unique among all 21
   Impress tabs; Hel~p is Calc's label (`calc_tabs.json:20`). Writer chose H~elp only because of its Print tab
   (`product/odd/tasks/writer-ribbon-tabs.md:860`); Impress has none. The stock repeats (D: ~Design, ~Draw, 3~D;
   M: ~Media, ~Master; O: ~Object, ~Outline; R: ~Review, Fo~rm; T: ~Table, ~Tools) predate this feature and are
   kept: the clashing tabs are stock contextual tabs, and changing their labels would change stock behaviour.
8. **No dialog launchers and no in-group separators** (Writer decision 7): the generator has neither. Each tab lists
   its launchers with the LibreOffice dialog that does the job, reachable from the menu bar.
9. **A control mapped to a plain command is a button**, whatever PowerPoint's type (toggle, check box, combo,
   spin, gallery): the command's state drives the button (Writer decisions 12-13). Check boxes are small-label
   toggles.
10. **PowerPoint splits without a LibreOffice split become dropdowns whose first item is the body action** (Writer
    decision 8, Writer ruling 3): Replace (Replace..., then Replace Fonts [P]) and Comments > Delete (Delete, then
    Delete All).
11. **Copy stays a plain button.** PowerPoint's Copy is a split with Duplicate; a split needs a dedicated command
    (Writer decision 10), and the only extra item would be Duplicate. For slides, New Slide's popup already offers
    Duplicate Slide (`sd/source/ui/controller/slidelayoutcontroller.cxx:216-231`).
12. **Find is a dropdown**, Writer's `HomeFindMenu`: the find toolbar (`vnd.sun.star.findbar:FocusToFindbar`,
    `GenericCommands.xcu:1855`) and Find & Replace. PowerPoint's Find is a plain button; the dropdown keeps Find the
    same in the three apps.
13. **Reset is `.uno:AssignLayout?Reset:bool=true` under the widget `ResetLayout` (inferred).** `.uno:AssignLayout`
    without `WhatLayout` re-applies the slide's current layout (`sd/source/ui/view/ViewShellImplementation.cxx:224-271`),
    which is PowerPoint's Reset. The `?Reset` variant gives the button its own URL, so the SlideLayoutController
    registered for `.uno:AssignLayout` (`Controller.xcu:2073-2082`) does not attach to it (inferred: controllers
    are found by the exact command URL), and the dispatcher ignores the unknown argument
    (`sfx2/source/appl/appuno.cxx:877-880`). The variant gets a label node ("Reset Slide Layout", LibreOffice's own
    wording, `sd/inc/strings.hrc:256`) and an explicit icon. Gate: an I2a UITest moves a title placeholder, presses
    Reset and expects it back; if that fails, Reset becomes a placeholder on a new family slot.
14. **Add or Remove Columns uses `TextColumnsNumber` URL variants (inferred)**: One, Two and Three Columns are
    `.uno:TextColumnsNumber?TextColumnsNumber:short=1|2|3` (slot `SID_ATTR_TEXTCOLUMNS_NUMBER`, `svx.sdi:13498`,
    served by `_drvwsh.sdi:3031`), each with a new label node; More Columns... is `.uno:TextAttributes` (the Text
    dialog, `DrawImpressCommands.xcu:168`; that its Columns tab is the right page is inferred). Inferred: the
    argument named like the slot sets the slot's item. Gate: an I2a UITest gives a text box two columns; if that
    fails, the menu keeps only More Columns....
15. **Home > Drawing's shape gallery is 17 icon-only tool buttons plus the More arrow** (`InsertShapesMenu`, the
    Insert > Shapes popup). The cells are the frequently used tools and the shape sub-toolbars, which keep their
    stock popups (`Controller.xcu` ToolBar nodes `:1788-2377`). A real gallery control would be new C++.
16. **Two items with the same URL on one page get distinct widget commands** with the real URL as `action` (Writer
    decision 11): Video and Audio (`.uno:InsertAVMedia`), Layout and Reset (`.uno:AssignLayout`), the deck controls
    of Transitions and Animations, and the three Set Up Slide Show controls.
17. **The Text Direction menu holds the paragraph direction items** (`.uno:ParaLeftToRight`,
    `.uno:ParaRightToLeft`) that the stock Home page has as buttons, so they do not leave.
18. **Dropdown recipe and names**: one static popup per menu in `sd/uiconfig/simpress/popupmenu/`; a Popup node on
    ResourceMenuController and a ToolBox node on GenericPopupToolbarController per command, for Module
    `com.sun.star.presentation.PresentationDocument`. Node names end in `Impress` (`HomeFindMenuImpressPopup`,
    `HomeFindMenuImpressControl`), as Writer's end in `Writer`. Command names reuse Calc's and Writer's where the
    Office control is the same (HomeFindMenu, HomeSelectMenu, HomeChangeCaseMenu, InsertShapesMenu,
    InsertTextBoxMenu, ReviewLanguageMenu, ReviewDeleteCommentMenu, ViewSwitchWindowsMenu, ViewMacrosMenu). A popup
    controller works only under its original command (Writer lesson, header and footer menus), so a menu that needs
    a controller holds that controller's command as an item (`.uno:SetLanguageAllTextMenu` in Language,
    `Controller.xcu:155`); Switch Windows puts WindowListMenuController (`Controller.xcu:1132`) on its own command,
    as Calc and Writer do, because it reads the open windows, not a command status.
19. **Existing split controllers are reused**: Paste, Undo, Redo, Underline, Font Color, Highlight, Shape Fill,
    Shape Outline, Bullets, Numbering, Line Spacing, Character Spacing, Table, Symbol; New Slide gets
    InsertSlideController (`Controller.xcu:2099-2104`) and Layout gets SlideLayoutController (`:2073-2082`), both
    registered for Impress. InsertSlideController is today used only by a toolbar
    (`sd/uiconfig/simpress/toolbar/insertbar.xml:21`); that it also attaches in a notebookbar is inferred from the
    stock Layout item on `notebookbar.ui:5573`, which gets SlideLayoutController the same way. I2a's UITest opens
    both popups.
20. **Placeholders are plain greyed buttons**, also where PowerPoint has a split, dropdown or check box (Writer
    decision 13): Convert to SmartArt, Screenshot, 3D Models, Record, Check Accessibility, Hide Ink, Play
    Narrations, Show Media Controls.
21. **Family slots**: 39 placeholder entries share 24 slots through URL variants (section 5), as Calc and Writer.
    Family names repeat Calc's and Writer's where the control is the same (InsertScreenshot, Insert3DModels,
    InsertSmartArt, ReviewTranslate, ReviewHideInk, ViewArrangeAll, ViewSplit, HelpFeedback).
22. **The slots are a fork block at the top of the sd range**: `SID_BOOST = SID_SD_START + 900` (27900-27923).
    sd's own slots end at +458 (`sd/inc/app.hrc:437`) and upstream appends after its last define, so the block
    stays clear of merges, as Writer's `FN_BOOST` at 25900 (Writer decision 15).
23. **The always-disabled state lives in ViewShellBase** (`ViewShellBase.sdi`, `ViewShellBase::GetState`): one
    place for every Impress view, and Draw's slot file does not include it (section 3.3).
24. **The stock overflow menus are deleted with their pages** (`remove_objects`), and their items count in section
    2 (Writer decision 17).
25. **Transitions and Animations open the sidebar decks.** LibreOffice has no command per transition, effect or
    timing value: those are panel widgets (`slidetransitionspanel.ui`, `customanimationspanel.ui`), and even the
    decks' Play buttons have no command (`slidetransitionspanel.ui:414`, `customanimationspanel.ui:590`). So each
    PowerPoint control opens the deck that holds it, through `.uno:SidebarDeck.SdSlideTransitionDeck` or
    `.uno:SidebarDeck.SdCustomAnimationDeck` (slot `SID_SIDEBAR_DECK`, `sfx.sdi:4479`, `frmslots.sdi:51`,
    `sfx2/source/view/viewfrm.cxx:3559-3574`). `Sidebar::ShowDeck` shows the sidebar if it is hidden and does not
    toggle (`sfx2/source/sidebar/Sidebar.cxx:37-59`), so pressing a second control keeps the deck open;
    `.uno:SlideChangeWindow` and `.uno:CustomAnimation` toggle (`sd/source/ui/view/drviews2.cxx:4227-4248`), so they
    are used only where PowerPoint's control is itself a toggle (Animation Pane). The Set Up check boxes and the
    Monitor box open the Set Up Slide Show dialog (`.uno:PresentationDialog`), where those settings live
    (`presentationdialog.ui:421`, `:604`, `:634`). Inline controls are later work (section 6).
26. **Approximate mappings are kept** (Writer ruling 4): Reuse Slides = Insert Slide from File; Quick Styles = the
    Styles deck; Icons = the Gallery (Writer decision 18; the research marks PowerPoint's stock icon library "do not
    build", `:271`, so the local Gallery takes its place); Summary Zoom = Summary Slide; WordArt = the Fontwork
    gallery; Date & Time = the variable date field; Equation = a Formula object; Themes = the master slides deck;
    Variants > Colors = the document theme dialog; Slide Size = the Slide Properties dialog; Format Background = the
    Properties deck, which shows the Slide panel when nothing is selected (`Sidebar.xcu:1160-1177`); Custom Slide
    Show = the Custom Slide Shows dialog; Selection Pane = the Navigator (Calc decision 17); the 19 deck and dialog
    controls of decision 25. 32 controls in all. A mapping becomes a placeholder only if a UITest shows it does not
    do the PowerPoint job.
27. **Undo stays on Home** (Calc and Writer ruling 5), as PowerPoint 365's Home has it; it also stays in the quick
    access bar.
28. **Hide Slide is `.uno:HideSlide`; Show Slide leaves to Slide > Show Slide.** PowerPoint has one Hide Slide toggle.
    `SID_HIDE_SLIDE` is served only by `SlideSorterController.sdi:174`; it reaching the slide pane's sorter from
    Normal view is inferred, and I6a's UITest checks it.
29. **14 controls are omitted** (cloud, account or licence; research `:733-737`): Dictate, Sensitivity, Add-ins,
    Copilot, Designer (Home); Cameo, Power BI, Forms (Insert); Designer (Design); Present in Teams, Rehearse with
    Coach, Keep Slides Updated, Captions & Subtitles (Slide Show); Smart Lookup (Review). Cloud items inside kept
    controls (Stock Images, Online Pictures, Stock and Online Videos, Stock 3D Models) are left out of their menus
    and not counted.
30. **Translate is a placeholder and Contact Support is real**, although both are on the research's do-not-build
    list: Calc (Calc decision 9) and Writer (Writer decision 19) have Translate as a placeholder, and their Help tabs
    map Contact Support to Get Help Online (`.uno:QuestionAnswers`). The three ribbons stay the same.
31. **Every LibreOffice command that leaves a stock tab stays reachable** (section 2): class a by its exact menu-bar
    entry, class b by an equivalent entry, class c through View > Toolbars (Writer ruling 2, Calc decisions 19-20),
    class q in the quick access bar. A `LEFT_THE_TAB` test per tab asserts it.
32. **Labels** (ruling T9): the ribbon shows PowerPoint's labels from `office_label`; menus, help and tooltips keep
    LibreOffice's. New label nodes use LibreOffice wording where a LibreOffice feature exists, PowerPoint's
    otherwise (placeholders).
33. **Accent**: PowerPoint orange `#C43E1C` (dark `#FF8F6B`), section 3.4, through W9a's mechanism (ruling 1). The
    hex is inferred (no primary text source).
34. **Icons**: grey line icons (ruling 8); a command reused from Calc or Writer keeps its icon; menus and
    placeholders get explicit icons.
35. **Disabled popup entries show greyed** (T10w), through W9c's change, which covers every app's popups.
36. **Only Impress gets the office `.ui`.** It is registered for Impress's ToolbarMode node; Draw shares sd, its
    `DrawImpressCommands.xcu` and the `sdraw.sdi` pool, but keeps its own notebookbar and no Tabbed Office mode
    (`HasTabbedOffice` stays false for Draw). The new label nodes are additive and never change an existing node.
37. **The dev profile turns the template dialog off** (`NewDoc/AutoPilot` = false), so the launcher and screenshots
    open a blank presentation; UITests use a fresh profile and close the dialog (section 3.2).
38. **The feature starts after Writer's W9 lands**: W9b changes `gen_ribbon.py`, W9a builds the accent and W9c the
    greyed entries; starting earlier would put two writers on the generator.
39. **Delivery** is Writer's: one work-unit commit per task, with the generated output in its own commit where it
    is large (Writer's W0a), and slices of about 700-1100 lines. Receipt-driven review is off for this clone (the
    user's decision, 2026-10-23), so the parent's spot check (unit suite, generator clean, screenshots) is the gate.

## 5. Placeholders

24 family slots, `SID_BOOST_<FAMILY>` = `SID_BOOST + 0..23` (27900-27923, section 3.3), numbered in order of first
appearance; 39 entries: 26 ribbon buttons and 13 menu items. Every entry is greyed and inert in every Impress view
(decision 23). Every command URL and `?` variant gets a label node in `DrawImpressCommands.xcu` with PowerPoint's
wording and an explicit icon. `product/tests/placeholders_impress.json` lists slot, offset, command, variants and
labels, in the shape of `placeholders_writer.json`; I1 writes slots and variants, the tab tasks add the labels.

### Families

| Slot | Offset | Command | Variants and labels |
|---|---|---|---|
| `SID_BOOST_HOME_SECTION` | +0 | `.uno:HomeSection` | `Action:string=removeall` Remove All Sections; `Action:string=collapseall` Collapse All; `Action:string=expandall` Expand All |
| `SID_BOOST_HOME_CONVERT_TO_SMARTART` | +1 | `.uno:HomeConvertToSmartArt` | Convert to SmartArt |
| `SID_BOOST_HOME_REGROUP` | +2 | `.uno:HomeRegroup` | Regroup |
| `SID_BOOST_HOME_SHAPE_EFFECT` | +3 | `.uno:HomeShapeEffect` | `Effect:string=preset` Preset; `Effect:string=reflection` Reflection; `Effect:string=bevel` Bevel |
| `SID_BOOST_HOME_REPLACE_FONTS` | +4 | `.uno:HomeReplaceFonts` | Replace Fonts... |
| `SID_BOOST_INSERT_SCREENSHOT` | +5 | `.uno:InsertScreenshot` | Screenshot |
| `SID_BOOST_INSERT_3D_MODELS` | +6 | `.uno:Insert3DModels` | 3D Models |
| `SID_BOOST_INSERT_SMARTART` | +7 | `.uno:InsertSmartArt` | SmartArt |
| `SID_BOOST_INSERT_ZOOM` | +8 | `.uno:InsertZoom` | `Type:string=section` Section Zoom; `Type:string=slide` Slide Zoom |
| `SID_BOOST_INSERT_SCREEN_RECORDING` | +9 | `.uno:InsertScreenRecording` | Screen Recording |
| `SID_BOOST_PAGE_LAYOUT_THEME_PART` | +10 | `.uno:PageLayoutThemePart` | `Part:string=fonts` Fonts; `Part:string=effects` Effects; `Part:string=backgroundstyles` Background Styles |
| `SID_BOOST_PREVIEW_EFFECTS` | +11 | `.uno:PreviewEffects` | `Target:string=transition` Preview; `Target:string=animation` Preview |
| `SID_BOOST_ANIMATION_PAINTER` | +12 | `.uno:AnimationPainter` | Animation Painter |
| `SID_BOOST_SLIDESHOW_RECORD` | +13 | `.uno:SlideShowRecord` | Record |
| `SID_BOOST_SLIDESHOW_OPTION` | +14 | `.uno:SlideShowOption` | `Option:string=narrations` Play Narrations; `Option:string=mediacontrols` Show Media Controls |
| `SID_BOOST_REVIEW_CHECK_ACCESSIBILITY` | +15 | `.uno:ReviewCheckAccessibility` | Check Accessibility |
| `SID_BOOST_REVIEW_TRANSLATE` | +16 | `.uno:ReviewTranslate` | Translate |
| `SID_BOOST_REVIEW_COMPARE` | +17 | `.uno:ReviewCompare` | `Action:string=compare` Compare; `Action:string=accept` Accept; `Action:string=reject` Reject; `Action:string=previous` Previous; `Action:string=next` Next; `Action:string=pane` Reviewing Pane; `Action:string=endreview` End Review |
| `SID_BOOST_REVIEW_HIDE_INK` | +18 | `.uno:ReviewHideInk` | Hide Ink |
| `SID_BOOST_VIEW_MODE` | +19 | `.uno:ViewMode` | `Mode:string=reading` Reading View |
| `SID_BOOST_VIEW_ARRANGE_ALL` | +20 | `.uno:ViewArrangeAll` | Arrange All |
| `SID_BOOST_VIEW_CASCADE` | +21 | `.uno:ViewCascade` | Cascade |
| `SID_BOOST_VIEW_SPLIT` | +22 | `.uno:ViewSplit` | Move Split |
| `SID_BOOST_HELP_FEEDBACK` | +23 | `.uno:HelpFeedback` | Feedback |

### Entries

| Where | Label | Command URL | Slot (offset) |
|---|---|---|---|
| Home, Section menu | Remove All Sections | `.uno:HomeSection?Action:string=removeall` | `SID_BOOST_HOME_SECTION` (+0) |
| Home, Section menu | Collapse All | `.uno:HomeSection?Action:string=collapseall` | `SID_BOOST_HOME_SECTION` (+0) |
| Home, Section menu | Expand All | `.uno:HomeSection?Action:string=expandall` | `SID_BOOST_HOME_SECTION` (+0) |
| Home, Paragraph | Convert to SmartArt | `.uno:HomeConvertToSmartArt` | `SID_BOOST_HOME_CONVERT_TO_SMARTART` (+1) |
| Home, Arrange menu | Regroup | `.uno:HomeRegroup` | `SID_BOOST_HOME_REGROUP` (+2) |
| Home, Shape Effects menu | Preset | `.uno:HomeShapeEffect?Effect:string=preset` | `SID_BOOST_HOME_SHAPE_EFFECT` (+3) |
| Home, Shape Effects menu | Reflection | `.uno:HomeShapeEffect?Effect:string=reflection` | `SID_BOOST_HOME_SHAPE_EFFECT` (+3) |
| Home, Shape Effects menu | Bevel | `.uno:HomeShapeEffect?Effect:string=bevel` | `SID_BOOST_HOME_SHAPE_EFFECT` (+3) |
| Home, Replace menu | Replace Fonts... | `.uno:HomeReplaceFonts` | `SID_BOOST_HOME_REPLACE_FONTS` (+4) |
| Insert, Images | Screenshot | `.uno:InsertScreenshot` | `SID_BOOST_INSERT_SCREENSHOT` (+5) |
| Insert, Illustrations | 3D Models | `.uno:Insert3DModels` | `SID_BOOST_INSERT_3D_MODELS` (+6) |
| Insert, Illustrations | SmartArt | `.uno:InsertSmartArt` | `SID_BOOST_INSERT_SMARTART` (+7) |
| Insert, Zoom menu | Section Zoom | `.uno:InsertZoom?Type:string=section` | `SID_BOOST_INSERT_ZOOM` (+8) |
| Insert, Zoom menu | Slide Zoom | `.uno:InsertZoom?Type:string=slide` | `SID_BOOST_INSERT_ZOOM` (+8) |
| Insert, Media | Screen Recording | `.uno:InsertScreenRecording` | `SID_BOOST_INSERT_SCREEN_RECORDING` (+9) |
| Design, More (Variants menu) menu | Fonts | `.uno:PageLayoutThemePart?Part:string=fonts` | `SID_BOOST_PAGE_LAYOUT_THEME_PART` (+10) |
| Design, More (Variants menu) menu | Effects | `.uno:PageLayoutThemePart?Part:string=effects` | `SID_BOOST_PAGE_LAYOUT_THEME_PART` (+10) |
| Design, More (Variants menu) menu | Background Styles | `.uno:PageLayoutThemePart?Part:string=backgroundstyles` | `SID_BOOST_PAGE_LAYOUT_THEME_PART` (+10) |
| Transitions, Preview | Preview | `.uno:PreviewEffects?Target:string=transition` | `SID_BOOST_PREVIEW_EFFECTS` (+11) |
| Animations, Preview | Preview | `.uno:PreviewEffects?Target:string=animation` | `SID_BOOST_PREVIEW_EFFECTS` (+11) |
| Animations, Advanced Animation | Animation Painter | `.uno:AnimationPainter` | `SID_BOOST_ANIMATION_PAINTER` (+12) |
| Slide Show, Set Up | Record | `.uno:SlideShowRecord` | `SID_BOOST_SLIDESHOW_RECORD` (+13) |
| Slide Show, Set Up | Play Narrations | `.uno:SlideShowOption?Option:string=narrations` | `SID_BOOST_SLIDESHOW_OPTION` (+14) |
| Slide Show, Set Up | Show Media Controls | `.uno:SlideShowOption?Option:string=mediacontrols` | `SID_BOOST_SLIDESHOW_OPTION` (+14) |
| Review, Accessibility | Check Accessibility | `.uno:ReviewCheckAccessibility` | `SID_BOOST_REVIEW_CHECK_ACCESSIBILITY` (+15) |
| Review, Language | Translate | `.uno:ReviewTranslate` | `SID_BOOST_REVIEW_TRANSLATE` (+16) |
| Review, Compare | Compare | `.uno:ReviewCompare?Action:string=compare` | `SID_BOOST_REVIEW_COMPARE` (+17) |
| Review, Compare | Accept | `.uno:ReviewCompare?Action:string=accept` | `SID_BOOST_REVIEW_COMPARE` (+17) |
| Review, Compare | Reject | `.uno:ReviewCompare?Action:string=reject` | `SID_BOOST_REVIEW_COMPARE` (+17) |
| Review, Compare | Previous | `.uno:ReviewCompare?Action:string=previous` | `SID_BOOST_REVIEW_COMPARE` (+17) |
| Review, Compare | Next | `.uno:ReviewCompare?Action:string=next` | `SID_BOOST_REVIEW_COMPARE` (+17) |
| Review, Compare | Reviewing Pane | `.uno:ReviewCompare?Action:string=pane` | `SID_BOOST_REVIEW_COMPARE` (+17) |
| Review, Compare | End Review | `.uno:ReviewCompare?Action:string=endreview` | `SID_BOOST_REVIEW_COMPARE` (+17) |
| Review, Ink | Hide Ink | `.uno:ReviewHideInk` | `SID_BOOST_REVIEW_HIDE_INK` (+18) |
| View, Presentation Views | Reading View | `.uno:ViewMode?Mode:string=reading` | `SID_BOOST_VIEW_MODE` (+19) |
| View, Window | Arrange All | `.uno:ViewArrangeAll` | `SID_BOOST_VIEW_ARRANGE_ALL` (+20) |
| View, Window | Cascade | `.uno:ViewCascade` | `SID_BOOST_VIEW_CASCADE` (+21) |
| View, Window | Move Split | `.uno:ViewSplit` | `SID_BOOST_VIEW_SPLIT` (+22) |
| Help, Help | Feedback | `.uno:HelpFeedback` | `SID_BOOST_HELP_FEEDBACK` (+23) |

## 6. Risks

No question is left open: every decision is ruled in section 4. These are the real risks, each with its check.

1. **The deck mappings may feel weak** (decision 25). 19 controls on Transitions, Animations and Slide Show open a
   deck or a dialog instead of acting inline; a PowerPoint user expects a transition gallery on the ribbon. Check:
   the I5b and I6b screenshots and the user's visual gate (I11). The real fix is later work: a transition gallery
   and effect controls as notebookbar controllers (new C++), one feature each.
2. **Several mappings are inferred**, each with a UITest gate and a fallback: Reset as an AssignLayout variant
   (decision 13), the TextColumnsNumber variants and the Text dialog's Columns tab (decision 14),
   InsertSlideController in a notebookbar (decision 19), Hide Slide from Normal view (decision 28).
3. **Home's fit at 1920 px.** PowerPoint's Home fits expanded at 1920 px (research `:101-105`), but Home has 64
   controls here and LibreOffice's font and size boxes and labels are wider; Writer's Home needed W2c. Check: I2b
   measures it with `shot-tab.sh` at 1920, 1600 and 1366 px and fits it through control sizes. The generator has no
   collapse-priority key: a section's position decides when it collapses, so sizes (L, S, I) are the only fit lever,
   as in Calc and Writer (PowerPoint collapses the large groups first, research `:671-675`).
4. **The accent hex has no primary text source** (decision 33). Check: the user sees it at I11; the value is one
   token in `palette.json`.
5. **Draw shares the files.** New label nodes in `DrawImpressCommands.xcu` and slot declarations in `sdraw.sdi` are
   also read by Draw. No Draw interface lists the slots and no Draw `.ui` uses the commands, so Draw is unchanged
   (inferred). Check: I1 runs `sd.build`, and I0a proves Draw's notebookbar files untouched.
6. **The template dialog** (decision 37). A UITest that forgets to close it hangs until timeout. Check: the I0b
   scaffold has one helper that opens an Impress document and closes the dialog; every Impress UITest uses it.
7. **Other views disable many controls.** In Outline, Slide Sorter, Notes and the master views, shape and text
   controls are disabled by LibreOffice's own state, as the stock ribbon does today. The UITests run in Normal view;
   I9's screenshots include Slide Sorter.
8. **Duplicate widget ids.** A generated id could equal an id on a stock contextual page, and the office `.ui` would
   then hold two objects with one id. Check: I0a adds a unit test that every id in the office `.ui` is unique.
9. **Concurrency on the generator.** Writer's W9b changes `gen_ribbon.py`; starting earlier would put two writers on
   it (decision 38).

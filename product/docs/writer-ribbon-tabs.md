# Writer ribbon tabs like Word (Tabbed Office)

Status: **design, 2026-10-20; nothing is built yet.** W10 updates this file with the build results.
It follows `product/docs/calc-ribbon-tabs.md`: section 1 here matches its section 1, section 3 its section 3,
section 4 its section 5 (decisions) and section 5 its section 8 (placeholders). Sections 2 and 6 are new.
The feature plan is `product/odd/tasks/writer-ribbon-tabs.md`.

Sources: the Word reference `.superpowers/sdd/2026-10-20-writer-impress-ribbons/research-word365-ribbon.md`
(its section 12 says which sizes come from images), the code map `map-M1.md` in the same folder (spot-checked),
and the Calc documents. Every code claim was read in the tree during this task, unless it is marked
**(inferred)**.

How to read the tables:

- **Size**: L = large (icon over label), S = small with label, I = icon only (research conventions, section
  "Conventions"); combo, spin, gal and chk are their own sizes.
- **Type**: btn, tgl (a button that stays pressed), split, dd (dropdown), gal (gallery), chk (check box),
  combo/spin. Word's dialog launchers are listed under each tab and are not built (decision 7).
- **LibreOffice command**: the command the button runs. `(new menu)` is a menu-only command with no slot, built
  with Calc's dropdown recipe: a label in `WriterCommands.xcu`, a Popup node (ResourceMenuController, or the
  named controller) and a ToolBox node (GenericPopupToolbarController) in `Controller.xcu`, and a popup file in
  `sw/uiconfig/swriter/popupmenu/` (Calc's pattern: `Controller.xcu:613-626` and `:2836-2846`). PLACEHOLDER is a
  greyed button on a family slot (section 5).
- **Evidence**: `W:n` = line n of `officecfg/registry/data/org/openoffice/Office/UI/WriterCommands.xcu`, `G:n` =
  the same in `GenericCommands.xcu` (the label node); then the declaration (`swriter.sdi` = `sw/sdi/swriter.sdi`,
  `svx.sdi` = `svx/sdi/svx.sdi`, `sfx.sdi` = `sfx2/sdi/sfx.sdi`) with its slot id; then one interface that serves
  the slot in Writer (`_textsh.sdi`, `_viewsh.sdi`, `_basesh.sdi`, `viewsh.sdi`, `textsh.sdi`, `wrtapp.sdi`, ... in
  `sw/sdi/`; `appslots.sdi`, `frmslots.sdi` in `sfx2/sdi/`). `Controller.xcu` is
  `officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu`; `menubar.xml` is
  `sw/uiconfig/swriter/menubar/menubar.xml`; `notebookbar.ui` is the stock `sw/uiconfig/swriter/ui/notebookbar.ui`.
- **Labels**: a real command shows LibreOffice's label until T9 is decided (decision 29). The Word label is the
  table's second column and is kept in the layout file (decision 29).

## 1. What the user sees

### Tab order and labels

File, Home, Insert, **Design**, Layout, References, **Mailings**, Review, View, (contextual tabs), Extension,
Tools, **Help**. Bold tabs are new pages. Word's Draw (ink) tab, the File backstage and Word's contextual tabs are
not in this feature. Writer's own contextual tabs (Table, Image, Draw, Object, Media, Print, Form) stay exactly as
they are.

- The stock pages keep their ids and labels: "Home Tab" (`notebookbar.ui:3059`), "Insert Tab" (`:4012`), "Layout
  Tab" (`:5128`), "References Tab" (`:6121`), "Review Tab" (`:6672`), "View Tab" (`:7372`). Their labels are
  already Word's (`TabbedWriter|HomeTabLabel` at `:3997` ... `TabbedWriter|ViewTabLabel` at `:8182`).
- New pages: "Design Tab" (label "Desi~gn", context `TabbedWriter|DesignTabLabel`, after Insert), "Mailings Tab"
  ("~Mailings", after References), "Help Tab" ("Hel~p", last, after Tools, as in Calc). The mnemonics follow
  Word's KeyTips where they are free (research, "Tab KeyTips": Design G). "~Mailings" and "Hel~p" repeat a letter
  of a contextual tab (~Media, ~Print); they never show together with it in normal editing, as in Calc.
- Positions: File 0, Home 1, Insert 2, Design 3, Layout 4, References 5, Mailings 6, Review 7, View 8, Table 9 ...
  Form 15, Extension 16, Tools 17, Help 18. Stock Tools is 15 (`notebookbar.ui:15236-15246`).
- A new page has no `context-*` style classes, so it keeps the default context Any
  (`include/vcl/IContext.hxx:22`; the builder replaces it only when classes exist, `vcl/source/window/builder.cxx:2089-2093`)
  and shows in every context (`vcl/source/control/tabctrl.cxx:2210`), like a stock page with `context-any`
  (`notebookbar.ui:3999-4004`).

### Counts

| Tab | Sections | Controls | Real | Placeholder | Omitted |
|---|---|---|---|---|---|
| Home | 7 | 40 | 40 | 0 (+6 menu items) | 6 |
| Insert | 8 | 27 | 23 | 4 | 6 |
| Design | 2 | 10 | 4 | 6 | 0 |
| Layout | 3 | 19 | 19 | 0 | 1 |
| References | 6 | 21 | 17 | 4 | 3 |
| Mailings | 5 | 21 | 13 | 8 | 0 |
| Review | 10 | 24 | 16 | 8 | 2 |
| View | 8 | 26 | 15 | 11 | 1 |
| Help | 1 | 5 | 4 | 1 | 0 |
| **Total** | **50** | **193** | **151** | **42 (+6 menu items = 48 entries on 24 slots)** | **19** |

"Real" counts the 30 new dropdowns, whose items are real commands except the 6 placeholder menu items. Word's 8
dialog launchers are not built and not counted.

### Home (Word: Clipboard, Font, Paragraph, Styles, Editing, Voice, Sensitivity, Editor, Add-ins, Copilot)

The Undo section is kept first, as on Calc's Home (`product/docs/calc-home-redesign.md:141`), although Word 2024
has Undo and Redo in the quick access bar (research, "Global facts"). Writer's quick access bar also has them
(`sw/uiconfig/swriter/toolbar/notebookbarshortcuts.xml:14-15`). Rows follow the research (Font and Paragraph have
two rows each).

| Section | Word label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Undo | Undo | I | split | `.uno:Undo` | G:4644; sfx.sdi:4719 SID_UNDO; _viewsh.sdi:66 | list popup (Controller.xcu:2414); Calc parity, also QAT |
| Undo | Redo | I | split | `.uno:Redo` | G:4636; sfx.sdi:3590 SID_REDO; _basesh.sdi:59 | list popup (Controller.xcu:2425) |
| Clipboard | Paste | L | split | `.uno:Paste` | G:4692; sfx.sdi:3206 SID_PASTE; _basesh.sdi:90 | SvxClipBoardControl (swmodule.cxx:284) |
| Clipboard | Cut | I | btn | `.uno:Cut` | G:4676; sfx.sdi:905 SID_CUT; _basesh.sdi:77 |  |
| Clipboard | Copy | I | btn | `.uno:Copy` | G:4684; sfx.sdi:813 SID_COPY; _basesh.sdi:84 |  |
| Clipboard | Format Painter | I | btn | `.uno:FormatPaintbrush` | W:3354; sfx.sdi:4737 SID_FORMATPAINTBRUSH; _viewsh.sdi:71 |  |
| Font | Font | combo | combo | `.uno:CharFontName` | G:1594; svx.sdi:1247 SID_ATTR_CHAR_FONT; _textsh.sdi:1473 | font box (Controller.xcu:2469) |
| Font | Font Size | combo | combo | `.uno:FontHeight` | G:1790; svx.sdi:3127 SID_ATTR_CHAR_FONTHEIGHT; _textsh.sdi:1491 | size box (Controller.xcu:1645) |
| Font | Increase Font Size | I | btn | `.uno:Grow` | G:1626; swriter.sdi:2367 FN_GROW_FONT_SIZE; _textsh.sdi:1709 |  |
| Font | Decrease Font Size | I | btn | `.uno:Shrink` | G:1640; swriter.sdi:6114 FN_SHRINK_FONT_SIZE; _textsh.sdi:1715 |  |
| Font | Change Case | I | dd | `.uno:HomeChangeCaseMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | ChangeCaseToSentenceCase; ChangeCaseToLower; ChangeCaseToUpper; ChangeCaseToTitleCase; ChangeCaseToToggleCase |
| Font | Clear All Formatting | I | btn | `.uno:ResetAttributes` | W:1671; swriter.sdi:5456 FN_FORMAT_RESET; _textsh.sdi:789 | LO label Clear Direct Formatting |
| Font | Bold | I | tgl | `.uno:Bold` | G:1618; svx.sdi:832 SID_ATTR_CHAR_WEIGHT; _textsh.sdi:1544 |  |
| Font | Italic | I | tgl | `.uno:Italic` | G:1610; svx.sdi:5197 SID_ATTR_CHAR_POSTURE; _textsh.sdi:1562 |  |
| Font | Underline | I | split | `.uno:Underline` | G:1725; svx.sdi:9066 SID_ATTR_CHAR_UNDERLINE; _textsh.sdi:1580 | underline popup (Controller.xcu:2403) |
| Font | Strikethrough | I | tgl | `.uno:Strikeout` | G:1716; svx.sdi:8491 SID_ATTR_CHAR_STRIKEOUT; _textsh.sdi:1592 |  |
| Font | Subscript | I | tgl | `.uno:SubScript` | W:1341; swriter.sdi:6338 FN_SET_SUB_SCRIPT; _textsh.sdi:1652 |  |
| Font | Superscript | I | tgl | `.uno:SuperScript` | W:1333; swriter.sdi:6356 FN_SET_SUPER_SCRIPT; _textsh.sdi:1646 |  |
| Font | Text Effects and Typography | I | dd | `.uno:HomeTextEffectsMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | OutlineFont; Shadowed; (separator); .uno:HomeTextEffect?Effect:string=reflection [P]; .uno:HomeTextEffect?Effect:string=glow [P]; .uno:HomeTextEffect?Effect:string=numberstyles [P]; .uno:HomeTextEffect?Effect:string=ligatures [P]; .uno:HomeTextEffect?Effect:string=stylisticsets [P] |
| Font | Text Highlight Color | I | split | `.uno:CharBackColor` | G:3805; svx.sdi:1572 SID_ATTR_CHAR_BACK_COLOR; _textsh.sdi:1509 | color popup (Controller.xcu:2381) |
| Font | Font Color | I | split | `.uno:Color` | G:1876; svx.sdi:1554 SID_ATTR_CHAR_COLOR; _textsh.sdi:1538 | color popup (Controller.xcu:2359) |
| Paragraph | Bullets | I | split | `.uno:DefaultBullet` | G:3077; svx.sdi:2251 FN_NUM_BULLET_ON; _textsh.sdi:835 | Controller.xcu:1722 |
| Paragraph | Numbering | I | split | `.uno:DefaultNumbering` | G:3091; svx.sdi:4985 FN_NUM_NUMBERING_ON; _textsh.sdi:801 | Controller.xcu:1689 |
| Paragraph | Multilevel List | I | split | `.uno:SetOutline` | G:3105; svx.sdi:13003 FN_SVX_SET_OUTLINE; _textsh.sdi:908 | Controller.xcu:1733 |
| Paragraph | Decrease Indent | I | btn | `.uno:DecrementIndent` | G:5329; svx.sdi:10535 SID_DEC_INDENT; _textsh.sdi:1415 |  |
| Paragraph | Increase Indent | I | btn | `.uno:IncrementIndent` | G:5343; svx.sdi:10517 SID_INC_INDENT; _textsh.sdi:1421 |  |
| Paragraph | Sort | I | btn | `.uno:SortDialog` | W:3248; swriter.sdi:6131 FN_SORTING_DLG; _textsh.sdi:765 |  |
| Paragraph | Show/Hide | I | tgl | `.uno:ControlCodes` | W:3206; swriter.sdi:647 FN_VIEW_META_CHARS; _viewsh.sdi:1005 | LO label Formatting Marks |
| Paragraph | Align Left | I | tgl | `.uno:LeftPara` | G:1910; svx.sdi:5421 SID_ATTR_PARA_ADJUST_LEFT; _textsh.sdi:1276 |  |
| Paragraph | Center | I | tgl | `.uno:CenterPara` | G:1932; svx.sdi:1020 SID_ATTR_PARA_ADJUST_CENTER; _textsh.sdi:1288 |  |
| Paragraph | Align Right | I | tgl | `.uno:RightPara` | G:1921; svx.sdi:7392 SID_ATTR_PARA_ADJUST_RIGHT; _textsh.sdi:1282 |  |
| Paragraph | Justify | I | tgl | `.uno:JustifyPara` | G:1965; svx.sdi:5273 SID_ATTR_PARA_ADJUST_BLOCK; _textsh.sdi:1294 |  |
| Paragraph | Line and Paragraph Spacing | I | dd | `.uno:LineSpacing` | G:1981; svx.sdi:5838 SID_ATTR_PARA_LINESPACE; _textsh.sdi:1343 | spacing popup (Controller.xcu:2260) |
| Paragraph | Shading | I | split | `.uno:BackgroundColor` | G:3797; svx.sdi:456 SID_BACKGROUND_COLOR; _basesh.sdi:241 | paragraph color (Controller.xcu:2337) |
| Paragraph | Borders | I | btn | `.uno:BorderDialog` | W:1545; swriter.sdi:419 FN_FORMAT_BORDER_DLG; _basesh.sdi:318 | approximate: opens the borders tab for paragraphs (basesh.cxx:2939-2951) |
| Styles | Styles gallery | gal | gal | `.uno:StylesPreview` | G:3521; controller only (Controller.xcu:2491), no slot | style preview gallery |
| Editing | Find | S | dd | `.uno:HomeFindMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | vnd.sun.star.findbar:FocusToFindbar; SearchDialog; GotoPage. Word split; dd |
| Editing | Replace | S | btn | `.uno:SearchDialog` | G:5990; sfx.sdi:4053 SID_SEARCH_DLG; frmslots.sdi:65 |  |
| Editing | Select | S | dd | `.uno:HomeSelectMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | SelectAll; SelectObject; .uno:HomeSelectSimilar [P]; Navigator |
| Editor | Editor | L | btn | `.uno:SpellingAndGrammarDialog` | G:4270; swriter.sdi:8025 FN_SPELL_GRAMMAR_DIALOG; _viewsh.sdi:402 | LibreOffice's checker; cloud parts omitted |

Menu items (all real commands; evidence as above):

- `ChangeCaseToSentenceCase`: G:3182; svx.sdi:1114 SID_TRANSLITERATE_SENTENCE_CASE; _textsh.sdi:1727
- `ChangeCaseToLower`: G:3187; svx.sdi:1190 SID_TRANSLITERATE_LOWER; _textsh.sdi:1757
- `ChangeCaseToUpper`: G:3195; svx.sdi:1209 SID_TRANSLITERATE_UPPER; _textsh.sdi:1751
- `ChangeCaseToTitleCase`: G:3203; svx.sdi:1133 SID_TRANSLITERATE_TITLE_CASE; _textsh.sdi:1733
- `ChangeCaseToToggleCase`: G:3208; svx.sdi:1152 SID_TRANSLITERATE_TOGGLE_CASE; _textsh.sdi:1739
- `OutlineFont`: G:1705; svx.sdi:6346 SID_ATTR_CHAR_CONTOUR; _textsh.sdi:1622
- `Shadowed`: G:1665; svx.sdi:8090 SID_ATTR_CHAR_SHADOWED; _textsh.sdi:1628
- `SearchDialog`: G:5990; sfx.sdi:4053 SID_SEARCH_DLG; frmslots.sdi:65
- `GotoPage`: W:522; svx.sdi:13191 SID_GO_TO_PAGE; _viewsh.sdi:96
- `SelectAll`: G:4755; sfx.sdi:4108 SID_SELECTALL; _textsh.sdi:525
- `SelectObject`: G:2967; svx.sdi:8938 SID_OBJECT_SELECT; _viewsh.sdi:125
- `Navigator`: G:4831; sfx.sdi:2637 SID_NAVIGATOR; frmslots.sdi:31

- Omitted: Left-to-Right and Right-to-Left (conditional in Word: only with an RTL language); Dictate (cloud);
  Sensitivity (account); Add-ins (store); Copilot (cloud).
- Launchers (not built): Clipboard (Office Clipboard pane: no LibreOffice equivalent); Font: Format > Character...
  (menubar.xml:451); Paragraph: Format > Paragraph... (menubar.xml:452); Styles: Styles > Styles (`.uno:DesignerDialog`,
  menubar.xml:621).
- Borders: `.uno:SetBorderStyle` (G:3861, svx.sdi:946) has a split popup, but only the frame and table shells
  serve it (`sw/sdi/_frmsh.sdi:381`, `sw/sdi/_tabsh.sdi:334`), so it would be greyed in body text. The plain
  Borders dialog works on paragraphs (`sw/source/uibase/shells/basesh.cxx:2939-2951`).

### Insert (Word: Pages, Tables, Illustrations, Media, Links, Comments, Header & Footer, Text, Symbols)

| Section | Word label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Pages | Cover Page | S | btn | `.uno:TitlePageDialog` | W:1582; swriter.sdi:5073 FN_FORMAT_TITLEPAGE_DLG; _basesh.sdi:274 | approximate: Title Page dialog; no cover gallery |
| Pages | Blank Page | S | btn | PLACEHOLDER `.uno:InsertBlankPage` | family slot, W1 |  |
| Pages | Page Break | S | btn | `.uno:InsertPagebreak` | W:850; swriter.sdi:3499 FN_INSERT_PAGEBREAK; _textsh.sdi:287 |  |
| Tables | Table | L | dd | `.uno:InsertTable` | W:869; swriter.sdi:3749 FN_INSERT_TABLE; _textsh.sdi:392 | grid popup (Controller.xcu:1744) |
| Illustrations | Pictures | L | btn | `.uno:InsertGraphic` | G:4227; svx.sdi:4928 SID_INSERT_GRAPHIC; _viewsh.sdi:888 | Word dd; its other items are cloud |
| Illustrations | Shapes | S | dd | `.uno:InsertShapesMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | ShapesLineMenu > (Line, Freeline_Unfilled, Freeline, Bezier_Unfilled, BezierFill, Polygon_Unfilled, Polygon_Diagonal_Unfilled, Polygon_Diagonal); BasicShapes; ArrowShapes; FlowChartShapes; StarShapes; CalloutShapes; SymbolShapes; ConnectorToolbox. copy of menubar.xml:290-310 |
| Illustrations | Icons | S | btn | `.uno:Gallery` | G:5976; svx.sdi:3728 SID_GALLERY; _viewsh.sdi:806 | Calc decision 17 |
| Illustrations | 3D Models | S | btn | PLACEHOLDER `.uno:Insert3DModels` | family slot, W1 | Calc name |
| Illustrations | SmartArt | S | btn | PLACEHOLDER `.uno:InsertSmartArt` | family slot, W1 | Calc name |
| Illustrations | Chart | S | btn | `.uno:InsertObjectChart` | G:3066; svx.sdi:5068 SID_INSERT_DIAGRAM; _textsh.sdi:368 |  |
| Illustrations | Screenshot | S | btn | PLACEHOLDER `.uno:InsertScreenshot` | family slot, W1 | Calc name |
| Links | Link | S | btn | `.uno:HyperlinkDialog` | G:4518; sfx.sdi:2002 SID_HYPERLINK_DIALOG; _textsh.sdi:407 | Word dd; its other items are cloud |
| Links | Bookmark | S | btn | `.uno:InsertBookmark` | W:595; swriter.sdi:2614 FN_INSERT_BOOKMARK; _textsh.sdi:137 |  |
| Links | Cross-reference | S | btn | `.uno:InsertReferenceField` | W:712; swriter.sdi:3641 FN_INSERT_REF_FIELD; _textsh.sdi:940 |  |
| Comments | Comment | L | btn | `.uno:InsertAnnotation` | G:2945; swriter.sdi:2559 FN_POSTIT; _textsh.sdi:1079 |  |
| Header & Footer | Header | S | dd | `.uno:InsertHeaderMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | InsertPageHeader. page styles with on/off (Controller.xcu:56-65) |
| Header & Footer | Footer | S | dd | `.uno:InsertFooterMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | InsertPageFooter. Controller.xcu:67-76 |
| Header & Footer | Page Number | S | dd | `.uno:InsertPageNumberMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | PageNumberWizard; InsertPageNumberField; InsertPageCountField |
| Text | Text Box | L | dd | `.uno:InsertTextBoxMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | DrawText; VerticalText |
| Text | Quick Parts | S | dd | `.uno:InsertQuickPartsMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | EditGlossary; (separator); InsertTitleField; InsertTopicField; InsertAuthorField; (separator); InsertField |
| Text | WordArt | S | btn | `.uno:FontworkGalleryFloater` | G:86; svx.sdi:10297 SID_FONTWORK_GALLERY_FLOATER; viewsh.sdi:234 | Fontwork gallery |
| Text | Drop Cap | S | btn | `.uno:FormatDropcap` | W:1598; swriter.sdi:1414 FN_FORMAT_DROPCAPS; _textsh.sdi:59 | approximate: Drop Caps dialog |
| Text | Signature Line | S | btn | `.uno:InsertSignatureLine` | G:7878; svx.sdi:13071 SID_INSERT_SIGNATURELINE; viewsh.sdi:38 |  |
| Text | Date & Time | S | btn | `.uno:InsertDateField` | W:1176; swriter.sdi:2982 FN_INSERT_FLD_DATE; _textsh.sdi:991 | approximate: inserts a date field |
| Text | Object | S | dd | `.uno:InsertObjectMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | InsertObject; InsertDoc. Word split; dd |
| Symbols | Equation | S | btn | `.uno:InsertObjectStarMath` | W:1111; swriter.sdi:3481 FN_INSERT_SMA; _textsh.sdi:374 | Formula object |
| Symbols | Symbol | S | dd | `.uno:CharmapControl` | G:5570; sfx.sdi:268 SID_CHARMAP_CONTROL; _textsh.sdi:202 | recent characters popup (Controller.xcu:2282) |

Menu items (all real commands; evidence as above):

- `Line`: G:2204; svx.sdi:5603 SID_DRAW_LINE; viewsh.sdi:90
- `Freeline_Unfilled`: G:5384; svx.sdi:3707 SID_DRAW_FREELINE_NOFILL; viewsh.sdi:184
- `Freeline`: G:5376; svx.sdi:3688 SID_DRAW_FREELINE; viewsh.sdi:189
- `Bezier_Unfilled`: G:5099; svx.sdi:531 SID_DRAW_BEZIER_NOFILL; viewsh.sdi:174
- `BezierFill`: G:2854; svx.sdi:663 SID_DRAW_BEZIER_FILL; viewsh.sdi:179
- `Polygon_Unfilled`: G:5083; svx.sdi:6801 SID_DRAW_POLYGON_NOFILL; viewsh.sdi:164
- `Polygon_Diagonal_Unfilled`: G:5091; svx.sdi:6783 SID_DRAW_XPOLYGON_NOFILL; viewsh.sdi:154
- `Polygon_Diagonal`: G:5075; svx.sdi:6765 SID_DRAW_XPOLYGON; viewsh.sdi:159
- `BasicShapes`: G:132; svx.sdi:10703 SID_DRAWTBX_CS_BASIC; viewsh.sdi:239
- `ArrowShapes`: G:188; svx.sdi:10739 SID_DRAWTBX_CS_ARROW; viewsh.sdi:249
- `FlowChartShapes`: G:202; svx.sdi:10757 SID_DRAWTBX_CS_FLOWCHART; viewsh.sdi:254
- `StarShapes`: G:230; svx.sdi:10793 SID_DRAWTBX_CS_STAR; viewsh.sdi:264
- `CalloutShapes`: G:216; svx.sdi:10775 SID_DRAWTBX_CS_CALLOUT; viewsh.sdi:259
- `SymbolShapes`: G:146; svx.sdi:10721 SID_DRAWTBX_CS_SYMBOL; viewsh.sdi:244
- `ConnectorToolbox`: G:2215; svx.sdi:104 SID_DRAWTBX_CONNECTORS; viewsh.sdi:284
- `InsertPageHeader`: W:110; swriter.sdi:3570 FN_INSERT_PAGEHEADER; _textsh.sdi:208
- `InsertPageFooter`: W:118; swriter.sdi:3552 FN_INSERT_PAGEFOOTER; _textsh.sdi:213
- `PageNumberWizard`: W:1216; swriter.sdi:3606 FN_PGNUMBER_WIZARD; _textsh.sdi:954
- `InsertPageNumberField`: W:1227; swriter.sdi:3588 FN_INSERT_FLD_PGNUMBER; _textsh.sdi:961
- `InsertPageCountField`: W:1241; swriter.sdi:3518 FN_INSERT_FLD_PGCOUNT; _textsh.sdi:968
- `DrawText`: G:4367; svx.sdi:8731 SID_DRAW_TEXT; viewsh.sdi:209
- `VerticalText`: G:3031; svx.sdi:9143 SID_DRAW_TEXT_VERTICAL; viewsh.sdi:214
- `EditGlossary`: W:22; swriter.sdi:1041 FN_GLOSSARY_DLG; _textsh.sdi:1068
- `InsertTitleField`: W:1265; swriter.sdi:3801 FN_INSERT_FLD_TITLE; _textsh.sdi:984
- `InsertTopicField`: W:1257; swriter.sdi:3818 FN_INSERT_FLD_TOPIC; textsh.sdi:32
- `InsertAuthorField`: W:1273; swriter.sdi:2579 FN_INSERT_FLD_AUTHOR; _textsh.sdi:1019
- `InsertField`: W:677; swriter.sdi:3051 FN_INSERT_FIELD; _textsh.sdi:927
- `InsertObject`: G:3695; svx.sdi:5049 SID_INSERT_OBJECT; _textsh.sdi:386
- `InsertDoc`: G:3226; sfx.sdi:2021 SID_INSERTDOC; _textsh.sdi:131

- Omitted: Media > Online Videos (cloud; the whole group goes); Reuse Files (older build only); Get Add-ins and My
  Add-ins (store, moved to Home); Collaborate (Loop) and Barcode (conditional, research section 2).
- The Header and Footer dropdowns reuse the menu controllers of the menu bar. HeaderMenuController builds its
  items with the fixed URLs `.uno:InsertPageHeader` / `.uno:InsertPageFooter`
  (`framework/source/uielement/headermenucontroller.cxx:92-96`), so it works under a new command name.

### Design (Word: Document Formatting, Page Background), new page

| Section | Word label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Document Formatting | Themes | L | btn | PLACEHOLDER `.uno:PageLayoutThemePart?Part:string=themes` | family slot, W1 | Calc family, new variant |
| Document Formatting | Style Set gallery | gal | btn | PLACEHOLDER `.uno:DesignStyleSet?Action:string=gallery` | family slot, W1 | a plain greyed button |
| Document Formatting | Colors | L | btn | `.uno:ThemeDialog` | G:8089; svx.sdi:13293 SID_THEME_DIALOG; _basesh.sdi:615 | Calc's Colors |
| Document Formatting | Fonts | L | btn | PLACEHOLDER `.uno:PageLayoutThemePart?Part:string=fonts` | family slot, W1 | Calc variant |
| Document Formatting | Paragraph Spacing | S | btn | PLACEHOLDER `.uno:DesignStyleSet?Action:string=spacing` | family slot, W1 |  |
| Document Formatting | Effects | S | btn | PLACEHOLDER `.uno:PageLayoutThemePart?Part:string=effects` | family slot, W1 | Calc variant |
| Document Formatting | Set as Default | S | btn | PLACEHOLDER `.uno:DesignStyleSet?Action:string=setdefault` | family slot, W1 |  |
| Page Background | Watermark | L | btn | `.uno:Watermark` | W:4343; sfx.sdi:4586 SID_WATERMARK; _basesh.sdi:430 | Watermark dialog |
| Page Background | Page Color | L | btn | `.uno:PageAreaDialog` | no label node (W4a adds one); swriter.sdi:5055 FN_FORMAT_PAGE_AREA_DLG; _basesh.sdi:292 | Page Style dialog at Area (basesh.cxx:2924-2926) |
| Page Background | Page Borders | L | btn | `.uno:PageDialog` | W:1574; swriter.sdi:5019 FN_FORMAT_PAGE_DLG; _basesh.sdi:268 | approximate: Page Style dialog; PageDialog takes no page argument (swriter.sdi:5019-5020) |

- `.uno:ThemeSelectorPanel` (G:3545, controller only, `Controller.xcu:1711`) is not used: Writer support for it is
  not verified.
- Page Color opens the page style dialog at its Area tab (`sw/source/uibase/shells/basesh.cxx:2924-2926`). Page
  Borders cannot open at the Borders tab, because `.uno:PageDialog` declares no argument (`swriter.sdi:5019-5020`).

### Layout (Word: Page Setup, Paragraph, Arrange)

| Section | Word label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Page Setup | Margins | L | dd | `.uno:PageMargin` | W:4335; swriter.sdi:8319 SID_ATTR_PAGE_MARGIN; _viewsh.sdi:673 | margin presets (Controller.xcu:2018) |
| Page Setup | Orientation | L | dd | `.uno:Orientation` | W:4316; svx.sdi:6538 SID_ATTR_PAGE_ORIENTATION; _viewsh.sdi:534 | Controller.xcu:2029 |
| Page Setup | Size | L | dd | `.uno:AttributePageSize` | W:4327; svx.sdi:6478 SID_ATTR_PAGE_SIZE; _viewsh.sdi:539 | Controller.xcu:1996 |
| Page Setup | Columns | L | dd | `.uno:PageColumnType` | W:1561; swriter.sdi:8301 SID_ATTR_PAGE_COLUMN; _viewsh.sdi:585 | Controller.xcu:2007 |
| Page Setup | Breaks | S | dd | `.uno:LayoutBreaksMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | InsertPagebreak; InsertColumnBreak; InsertLinebreak; (separator); InsertBreak; InsertSection |
| Page Setup | Line Numbers | S | btn | `.uno:LineNumberingDialog` | W:3071; swriter.sdi:4141 FN_LINE_NUMBERING_DLG; _viewsh.sdi:412 | Word dd; LO has the dialog only |
| Page Setup | Hyphenation | S | btn | `.uno:Hyphenate` | W:3160; swriter.sdi:2420 FN_HYPHENATE_OPT_DLG; viewsh.sdi:74 | Word dd; LO has the dialog only |
| Paragraph | Indent Left | spin | spin | `.uno:LeftParaMargin` | no label node (W4a adds one); svx.sdi:5512 SID_ATTR_PARA_LEFTSPACE; _textsh.sdi:1399 | spin (swmodule.cxx:280) |
| Paragraph | Indent Right | spin | spin | `.uno:RightParaMargin` | no label node (W4a adds one); svx.sdi:5548 SID_ATTR_PARA_RIGHTSPACE; _textsh.sdi:1403 | swmodule.cxx:281 |
| Paragraph | Spacing Before | spin | spin | `.uno:AboveSpacing` | no label node (W4a adds one); svx.sdi:5875 SID_ATTR_PARA_ABOVESPACE; _viewsh.sdi:561 | swmodule.cxx:278 |
| Paragraph | Spacing After | spin | spin | `.uno:BelowSpacing` | no label node (W4a adds one); svx.sdi:5894 SID_ATTR_PARA_BELOWSPACE; _viewsh.sdi:566 | swmodule.cxx:279 |
| Arrange | Position | L | dd | `.uno:AnchorMenu` | G:7445; svx.sdi:13054 SID_ANCHOR_MENU; _basesh.sdi:457 | approximate: anchor popup (Controller.xcu:2604) |
| Arrange | Wrap Text | L | dd | `.uno:LayoutWrapTextMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | SetAnchorToChar; WrapOn; WrapContour; WrapOff; WrapThroughTransparent; WrapThrough; (separator); ContourDialog; TextWrap |
| Arrange | Bring Forward | L | dd | `.uno:PageLayoutBringForwardMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | ObjectForwardOne; BringToFront; SetObjectToForeground. Calc name, Writer node; Word split |
| Arrange | Send Backward | L | dd | `.uno:PageLayoutSendBackwardMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | ObjectBackOne; SendToBack; SetObjectToBackground. Calc name, Writer node; Word split |
| Arrange | Selection Pane | L | btn | `.uno:Navigator` | G:4831; sfx.sdi:2637 SID_NAVIGATOR; frmslots.sdi:31 | Calc decision 17 |
| Arrange | Align | S | dd | `.uno:PageLayoutAlignMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | ObjectAlignLeft; AlignCenter; ObjectAlignRight; AlignUp; AlignMiddle; AlignDown. Calc name |
| Arrange | Group | S | dd | `.uno:PageLayoutGroupMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | FormatGroup; FormatUngroup. Calc name |
| Arrange | Rotate | S | dd | `.uno:PageLayoutRotateMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | RotateRight; RotateLeft; FlipVertical; FlipHorizontal; (separator); TransformDialog. Calc name |

Menu items (all real commands; evidence as above):

- `InsertPagebreak`: W:850; swriter.sdi:3499 FN_INSERT_PAGEBREAK; _textsh.sdi:287
- `InsertColumnBreak`: W:669; swriter.sdi:2802 FN_INSERT_COLUMN_BREAK; _textsh.sdi:350
- `InsertLinebreak`: W:731; swriter.sdi:3225 FN_INSERT_LINEBREAK; _textsh.sdi:293
- `InsertBreak`: W:661; swriter.sdi:2766 FN_INSERT_BREAK_DLG; _textsh.sdi:356
- `InsertSection`: W:150; swriter.sdi:2946 FN_INSERT_REGION; _basesh.sdi:261
- `SetAnchorToChar`: W:1130; swriter.sdi:5768 FN_TOOL_ANCHOR_CHAR; _basesh.sdi:470
- `WrapOn`: W:1693; swriter.sdi:7101 FN_FRAME_WRAP; _basesh.sdi:525
- `WrapContour`: W:2918; swriter.sdi:7033 FN_FRAME_WRAP_CONTOUR; _basesh.sdi:567
- `WrapOff`: W:1685; swriter.sdi:7084 FN_FRAME_NOWRAP; _basesh.sdi:539
- `WrapThroughTransparent`: W:2711; swriter.sdi:7152 FN_FRAME_WRAPTHRU_TRANSP; _basesh.sdi:553
- `WrapThrough`: W:1717; swriter.sdi:7135 FN_FRAME_WRAPTHRU; _basesh.sdi:546
- `ContourDialog`: G:4747; svx.sdi:1702 SID_CONTOUR_DLG; basesh.sdi:31
- `TextWrap`: W:3017; swriter.sdi:6634 FN_DRAW_WRAP_DLG; _drwbase.sdi:21
- `ObjectForwardOne`: G:4399; swriter.sdi:4948 FN_FRAME_UP; _drwbase.sdi:98
- `BringToFront`: G:4494; svx.sdi:964 SID_FRAME_TO_TOP; _drwbase.sdi:84
- `SetObjectToForeground`: G:4476; svx.sdi:7923 SID_OBJECT_HEAVEN; drawsh.sdi:292
- `ObjectBackOne`: G:4407; swriter.sdi:4931 FN_FRAME_DOWN; _drwbase.sdi:105
- `SendToBack`: G:4502; svx.sdi:7795 SID_FRAME_TO_BOTTOM; _drwbase.sdi:91
- `SetObjectToBackground`: G:4468; svx.sdi:7905 SID_OBJECT_HELL; drawsh.sdi:285
- `ObjectAlignLeft`: G:2983; svx.sdi:176 SID_OBJECT_ALIGN_LEFT; _frmsh.sdi:297
- `AlignCenter`: G:2991; svx.sdi:140 SID_OBJECT_ALIGN_CENTER; _frmsh.sdi:283
- `ObjectAlignRight`: G:2999; svx.sdi:231 SID_OBJECT_ALIGN_RIGHT; _frmsh.sdi:290
- `AlignUp`: G:3007; svx.sdi:249 SID_OBJECT_ALIGN_UP; _frmsh.sdi:304
- `AlignMiddle`: G:3015; svx.sdi:213 SID_OBJECT_ALIGN_MIDDLE; _frmsh.sdi:311
- `AlignDown`: G:3023; svx.sdi:158 SID_OBJECT_ALIGN_DOWN; _frmsh.sdi:318
- `FormatGroup`: G:5299; svx.sdi:3449 SID_GROUP; _drwbase.sdi:35
- `FormatUngroup`: G:5307; svx.sdi:3561 SID_UNGROUP; _drwbase.sdi:42
- `RotateRight`: W:1437; svx.sdi:4544 SID_ROTATE_GRAPHIC_RIGHT; _grfsh.sdi:89
- `RotateLeft`: W:1429; svx.sdi:4512 SID_ROTATE_GRAPHIC_LEFT; _grfsh.sdi:75
- `FlipVertical`: G:5233; svx.sdi:12859 SID_FLIP_VERTICAL; _grfsh.sdi:21
- `FlipHorizontal`: G:5225; svx.sdi:12840 SID_FLIP_HORIZONTAL; _grfsh.sdi:28
- `TransformDialog`: G:2047; svx.sdi:8976 SID_ATTR_TRANSFORM; _drwbase.sdi:28

- Omitted: Text Direction (hidden in the English UI, research section 3).
- Launchers (not built): Page Setup: Format > Page Style... (menubar.xml:480); Paragraph: Format > Paragraph...
  (menubar.xml:452).
- The four spin fields are ordinary toolbox items; the controllers registered in
  `sw/source/uibase/app/swmodule.cxx:278-281` draw them, as on the stock Layout tab (`notebookbar.ui:5443-5447`).
- Wrap Text maps Word's items: In Line with Text = As Character (`SetAnchorToChar`), Square = Page Wrap (`WrapOn`),
  Tight/Through = Contour (`WrapContour`), Top and Bottom = None (`WrapOff`), Behind Text = In Background
  (`WrapThroughTransparent`), In Front of Text = Through (`WrapThrough`), Edit Wrap Points = Edit Contour, More
  Layout Options = the wrap dialog.
- Rotate Left/Right serve images only (`sw/sdi/_grfsh.sdi:75`, `:89`); with a shape selected they are disabled.

### References (Word: Table of Contents, Footnotes, Research, Citations & Bibliography, Captions, Index, Table of Authorities)

| Section | Word label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Table of Contents | Table of Contents | L | dd | `.uno:ReferencesTocMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | InsertMultiIndex; EditCurIndex; RemoveTableOf. no built-in TOC gallery |
| Table of Contents | Add Text | S | dd | `.uno:ReferencesAddTextMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | TextBodyParaStyle; Heading1ParaStyle; Heading2ParaStyle; Heading3ParaStyle. approximate: paragraph styles, not outline levels |
| Table of Contents | Update Table | S | btn | `.uno:UpdateCurIndex` | W:224; swriter.sdi:6846 FN_UPDATE_CUR_TOX; _viewsh.sdi:423 |  |
| Footnotes | Insert Footnote | L | btn | `.uno:InsertFootnote` | W:1281; swriter.sdi:3104 FN_INSERT_FOOTNOTE; _textsh.sdi:861 |  |
| Footnotes | Insert Endnote | S | btn | `.uno:InsertEndnote` | W:134; swriter.sdi:3016 FN_INSERT_ENDNOTE; _textsh.sdi:868 |  |
| Footnotes | Next Footnote | S | dd | `.uno:ReferencesNextFootnoteMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | JumpToNextFootnote; JumpToPrevFootnote. Word split; dd |
| Footnotes | Show Notes | S | btn | `.uno:JumpToFootnoteOrAnchor` | W:2736; swriter.sdi:3886 FN_FOOTNOTE_TO_ANCHOR; _textsh.sdi:883 | approximate: jumps between note and anchor |
| Citations & Bibliography | Insert Citation | L | btn | `.uno:InsertAuthoritiesEntry` | W:178; swriter.sdi:2596 FN_INSERT_AUTH_ENTRY_DLG; textsh.sdi:47 | Bibliography Entry dialog |
| Citations & Bibliography | Manage Sources | S | btn | `.uno:BibliographyComponent` | G:2582; sfx.sdi:5430 SID_COMP_BIBLIOGRAPHY; appslots.sdi:328 | Bibliography Database |
| Citations & Bibliography | Style | S | btn | PLACEHOLDER `.uno:ReferencesCitationStyle` | family slot, W1 | Word combo; plain greyed button |
| Citations & Bibliography | Bibliography | S | btn | `.uno:InsertMultiIndex` | W:164; swriter.sdi:3410 FN_INSERT_MULTI_TOX; textsh.sdi:62 | approximate; widget cmd `ReferencesBibliography`, action this URL |
| Captions | Insert Caption | L | btn | `.uno:InsertCaptionDialog` | W:693; swriter.sdi:2784 FN_INSERT_CAPTION; viewsh.sdi:32 |  |
| Captions | Insert Table of Figures | S | btn | `.uno:InsertMultiIndex` | W:164; swriter.sdi:3410 FN_INSERT_MULTI_TOX; textsh.sdi:62 | widget cmd `ReferencesTableOfFigures`, action this URL |
| Captions | Update Table | S | btn | `.uno:UpdateCurIndex` | W:224; swriter.sdi:6846 FN_UPDATE_CUR_TOX; _viewsh.sdi:423 | widget cmd `ReferencesUpdateCaptionTable`, action this URL |
| Captions | Cross-reference | S | btn | `.uno:InsertReferenceField` | W:712; swriter.sdi:3641 FN_INSERT_REF_FIELD; _textsh.sdi:940 |  |
| Index | Mark Entry | L | btn | `.uno:InsertIndexesEntry` | W:913; swriter.sdi:3207 FN_INSERT_IDX_ENTRY_DLG; textsh.sdi:41 |  |
| Index | Insert Index | S | btn | `.uno:InsertMultiIndex` | W:164; swriter.sdi:3410 FN_INSERT_MULTI_TOX; textsh.sdi:62 | widget cmd `ReferencesInsertIndex`, action this URL |
| Index | Update Index | S | btn | `.uno:UpdateCurIndex` | W:224; swriter.sdi:6846 FN_UPDATE_CUR_TOX; _viewsh.sdi:423 | widget cmd `ReferencesUpdateIndex`, action this URL |
| Table of Authorities | Mark Citation | L | btn | PLACEHOLDER `.uno:ReferencesAuthorities?Action:string=mark` | family slot, W1 |  |
| Table of Authorities | Insert Table of Authorities | S | btn | PLACEHOLDER `.uno:ReferencesAuthorities?Action:string=insert` | family slot, W1 |  |
| Table of Authorities | Update Table | S | btn | PLACEHOLDER `.uno:ReferencesAuthorities?Action:string=update` | family slot, W1 |  |

Menu items (all real commands; evidence as above):

- `InsertMultiIndex`: W:164; swriter.sdi:3410 FN_INSERT_MULTI_TOX; textsh.sdi:62
- `EditCurIndex`: W:568; swriter.sdi:1024 FN_EDIT_CURRENT_TOX; _viewsh.sdi:428
- `RemoveTableOf`: W:238; swriter.sdi:5403 FN_REMOVE_CUR_TOX; textsh.sdi:67
- `TextBodyParaStyle`: W:4036; alias of StyleApply (TargetURL, W:4044)
- `Heading1ParaStyle`: W:3884; alias of StyleApply (TargetURL, W:3892)
- `Heading2ParaStyle`: W:3903; alias of StyleApply
- `Heading3ParaStyle`: W:3922; alias of StyleApply
- `JumpToNextFootnote`: W:2746; swriter.sdi:3937 FN_NEXT_FOOTNOTE; _textsh.sdi:888
- `JumpToPrevFootnote`: W:2756; swriter.sdi:4022 FN_PREV_FOOTNOTE; _textsh.sdi:893

- Omitted: Research > Search and Researcher (cloud); Acronyms (conditional, cloud).
- Launcher (not built): Footnotes: Tools > Footnote/Endnote Settings... (menubar.xml:790).
- Add Text applies Body Text and Heading 1-3 (alias commands with a `TargetURL` to `.uno:StyleApply`). Word sets
  the outline level instead; with Writer's default outline numbering the effect on the table of contents is the
  same (inferred).

### Mailings (Word: Create, Start Mail Merge, Write & Insert Fields, Preview Results, Finish), new page

| Section | Word label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Create | Envelopes | L | btn | `.uno:InsertEnvelope` | W:549; swriter.sdi:3033 FN_ENVELOP; wrtapp.sdi:21 |  |
| Create | Labels | L | btn | `.uno:InsertLabels` | G:4484; sfx.sdi:5371 FN_LABEL; wrtapp.sdi:28 | Labels dialog (new document) |
| Start Mail Merge | Start Mail Merge | L | btn | `.uno:MailMergeWizard` | W:1015; swriter.sdi:4313 FN_MAILMERGE_WIZARD; wrtapp.sdi:60 | Word dd; LO wizard |
| Start Mail Merge | Select Recipients | L | dd | `.uno:MailingsSelectRecipientsMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | AddressBookSource; ChangeDatabaseField |
| Start Mail Merge | Edit Recipient List | L | btn | `.uno:ViewDataSourceBrowser` | G:5598; sfx.sdi:4901 SID_VIEW_DATA_SOURCE_BROWSER; _viewsh.sdi:815 | approximate: data sources pane |
| Write & Insert Fields | Highlight Merge Fields | L | tgl | `.uno:Marks` | W:3256; swriter.sdi:4212 FN_VIEW_MARKS; _viewsh.sdi:981 | approximate: field shadings |
| Write & Insert Fields | Address Block | L | btn | PLACEHOLDER `.uno:MailingsField?Field:string=addressblock` | family slot, W1 |  |
| Write & Insert Fields | Greeting Line | L | btn | PLACEHOLDER `.uno:MailingsField?Field:string=greetingline` | family slot, W1 |  |
| Write & Insert Fields | Insert Merge Field | L | btn | `.uno:InsertField` | W:677; swriter.sdi:3051 FN_INSERT_FIELD; _textsh.sdi:927 | approximate: Fields dialog (Database tab) |
| Write & Insert Fields | Rules | S | btn | PLACEHOLDER `.uno:MailingsField?Field:string=rules` | family slot, W1 |  |
| Write & Insert Fields | Match Fields | S | btn | PLACEHOLDER `.uno:MailingsField?Field:string=matchfields` | family slot, W1 |  |
| Write & Insert Fields | Update Labels | S | btn | PLACEHOLDER `.uno:MailingsField?Field:string=updatelabels` | family slot, W1 |  |
| Preview Results | Preview Results | L | tgl | PLACEHOLDER `.uno:MailingsPreview?Action:string=toggle` | family slot, W1 | View > Field Names is the inverse toggle |
| Preview Results | First Record | I | btn | `.uno:MailMergeFirstEntry` | W:1023; swriter.sdi:4330 FN_MAILMERGE_FIRST_ENTRY; wrtapp.sdi:66 | mail merge only |
| Preview Results | Previous Record | I | btn | `.uno:MailMergePrevEntry` | W:1031; swriter.sdi:4347 FN_MAILMERGE_PREV_ENTRY; wrtapp.sdi:72 |  |
| Preview Results | Record box | combo | combo | `.uno:MailMergeCurrentEntry` | W:1039; swriter.sdi:4398 FN_MAILMERGE_CURRENT_ENTRY; wrtapp.sdi:90 | entry field (Controller.xcu:1974) |
| Preview Results | Next Record | I | btn | `.uno:MailMergeNextEntry` | W:1047; swriter.sdi:4364 FN_MAILMERGE_NEXT_ENTRY; wrtapp.sdi:78 |  |
| Preview Results | Last Record | I | btn | `.uno:MailMergeLastEntry` | W:1055; swriter.sdi:4381 FN_MAILMERGE_LAST_ENTRY; wrtapp.sdi:84 |  |
| Preview Results | Find Recipient | S | btn | PLACEHOLDER `.uno:MailingsPreview?Action:string=find` | family slot, W1 |  |
| Preview Results | Check for Errors | S | btn | PLACEHOLDER `.uno:MailingsPreview?Action:string=check` | family slot, W1 |  |
| Finish | Finish & Merge | L | dd | `.uno:MailingsFinishMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | MailMergeCreateDocuments; MailMergePrintDocuments; MailMergeEmailDocuments; MailMergeSaveDocuments |

Menu items (all real commands; evidence as above):

- `AddressBookSource`: G:5540; sfx.sdi:286 SID_TEMPLATE_ADDRESSBOOKSOURCE; appslots.sdi:111
- `ChangeDatabaseField`: W:685; swriter.sdi:507 FN_CHANGE_DBFIELD; _basesh.sdi:145
- `MailMergeCreateDocuments`: W:1071; swriter.sdi:4432 FN_MAILMERGE_CREATE_DOCUMENTS; wrtapp.sdi:101
- `MailMergePrintDocuments`: W:1087; swriter.sdi:4466 FN_MAILMERGE_PRINT_DOCUMENTS; wrtapp.sdi:113
- `MailMergeEmailDocuments`: W:1095; swriter.sdi:4483 FN_MAILMERGE_EMAIL_DOCUMENTS; wrtapp.sdi:119
- `MailMergeSaveDocuments`: W:1079; swriter.sdi:4449 FN_MAILMERGE_SAVE_DOCUMENTS; wrtapp.sdi:107

- The record buttons and the record box serve only a mail merge in progress (`sw/sdi/wrtapp.sdi:66-119`); they
  are greyed otherwise, as in Word (research: "Mailings groups ... are enabled only in a mail merge document").
- Preview Results stays a placeholder: View > Field Names (`.uno:Fieldnames`, W:3272) is the inverse toggle, and a
  button that is pressed when field names are hidden needs its own state code.

### Review (Word: Proofing, Speech, Accessibility, Language, Comments, Markup, Tracking, Compare, Protect, Ink)

| Section | Word label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Proofing | Spelling and Grammar | L | btn | `.uno:SpellingAndGrammarDialog` | G:4270; swriter.sdi:8025 FN_SPELL_GRAMMAR_DIALOG; _viewsh.sdi:402 | Word dd; one dialog does both |
| Proofing | Thesaurus | L | btn | `.uno:ThesaurusDialog` | W:3125; svx.sdi:8825 SID_THESAURUS; _viewsh.sdi:679 |  |
| Proofing | Word Count | L | btn | `.uno:WordCountDialog` | W:3697; swriter.sdi:7587 FN_WORDCOUNT_DIALOG; _textsh.sdi:1844 |  |
| Speech | Read Aloud | L | btn | PLACEHOLDER `.uno:ReviewReadAloud` | family slot, W1 |  |
| Accessibility | Check Accessibility | L | btn | `.uno:AccessibilityCheck` | W:3705; alias: TargetURL .uno:SidebarDeck.A11yCheckDeck (W:3713), SID_SIDEBAR_DECK sfx.sdi:4479 | Word dd; LO opens the check deck |
| Language | Translate | L | btn | PLACEHOLDER `.uno:ReviewTranslate` | family slot, W1 | Calc name and ruling 9 |
| Language | Language | L | dd | `.uno:ReviewLanguageMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | SetLanguageSelectionMenu; SetLanguageParagraphMenu; SetLanguageAllTextMenu; (separator); HangulHanjaConversion; ChineseConversion; MoreDictionaries. submenus by controller (Controller.xcu:146-174) |
| Comments | New Comment | L | btn | `.uno:InsertAnnotation` | G:2945; swriter.sdi:2559 FN_POSTIT; _textsh.sdi:1079 |  |
| Comments | Delete | L | dd | `.uno:ReviewDeleteCommentMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | DeleteComment; DeleteAuthor; DeleteAllNotes. Word split; dd |
| Comments | Previous | L | btn | PLACEHOLDER `.uno:ReviewGoToComment?Direction:string=previous` | family slot, W1 | Calc name |
| Comments | Next | L | btn | PLACEHOLDER `.uno:ReviewGoToComment?Direction:string=next` | family slot, W1 | Calc name |
| Comments | Show Comments | L | tgl | `.uno:ShowAnnotations` | G:44; svx.sdi:4762 SID_TOGGLE_NOTES; _viewsh.sdi:927 | Word dd; LO toggle |
| Markup | Filter All Markup | L | btn | PLACEHOLDER `.uno:ReviewMarkup?Action:string=filter` | family slot, W1 |  |
| Markup | Display for Review | S | btn | PLACEHOLDER `.uno:ReviewMarkup?Action:string=display` | family slot, W1 | Word combo; plain greyed button |
| Markup | Show Markup | S | split | `.uno:ShowTrackedChanges` | W:412; swriter.sdi:6044 FN_REDLINE_SHOW; _viewsh.sdi:195 | popup: in text / margin (Controller.xcu:1413) |
| Markup | Reviewing Pane | S | btn | `.uno:AcceptTrackedChanges` | W:557; swriter.sdi:37 FN_REDLINE_ACCEPT; _viewsh.sdi:201 | approximate: Manage Changes |
| Tracking | Track Changes | L | split | `.uno:TrackChanges` | W:390; swriter.sdi:56 FN_REDLINE_ON; _viewsh.sdi:170 | popup: all views / this view (Controller.xcu:1427) |
| Tracking | Accept | L | dd | `.uno:ReviewAcceptMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | AcceptTrackedChangeToNext; AcceptTrackedChange; AcceptAllTrackedChanges. Word split; dd |
| Tracking | Reject | L | dd | `.uno:ReviewRejectMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | RejectTrackedChangeToNext; RejectTrackedChange; RejectAllTrackedChanges. Word split; dd |
| Tracking | Previous | S | btn | `.uno:PreviousTrackedChange` | W:368; swriter.sdi:8192 FN_REDLINE_PREV_CHANGE; _viewsh.sdi:237 |  |
| Tracking | Next | S | btn | `.uno:NextTrackedChange` | W:357; swriter.sdi:8173 FN_REDLINE_NEXT_CHANGE; _viewsh.sdi:231 |  |
| Compare | Compare | L | dd | `.uno:ReviewCompareMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | CompareDocuments; MergeDocuments |
| Protect | Restrict Editing | L | btn | PLACEHOLDER `.uno:ReviewRestrictEditing` | family slot, W1 |  |
| Ink | Hide Ink | L | btn | PLACEHOLDER `.uno:ReviewHideInk` | family slot, W1 | Calc name |

Menu items (all real commands; evidence as above):

- `SetLanguageSelectionMenu`: G:7659; menu id; LanguageSelectionMenuController (Controller.xcu:146)
- `SetLanguageParagraphMenu`: G:7667; menu id; popup controller (Controller.xcu:168)
- `SetLanguageAllTextMenu`: G:7675; menu id; popup controller (Controller.xcu:157)
- `HangulHanjaConversion`: G:3923; svx.sdi:9900 SID_HANGUL_HANJA_CONVERSION; _viewsh.sdi:685
- `ChineseConversion`: G:3928; svx.sdi:9918 SID_CHINESE_CONVERSION; _viewsh.sdi:691
- `MoreDictionaries`: G:7688; sfx.sdi:5603 SID_MORE_DICTIONARIES; appslots.sdi:345
- `DeleteComment`: G:6994; swriter.sdi:7807 FN_DELETE_COMMENT; _textsh.sdi:1094
- `DeleteAuthor`: G:6978; swriter.sdi:7875 FN_DELETE_NOTE_AUTHOR; _textsh.sdi:1114
- `DeleteAllNotes`: G:6962; swriter.sdi:7891 FN_DELETE_ALL_NOTES; _textsh.sdi:1119
- `AcceptTrackedChangeToNext`: W:321; swriter.sdi:8210 FN_REDLINE_ACCEPT_TONEXT; _viewsh.sdi:243
- `AcceptTrackedChange`: W:307; swriter.sdi:8043 FN_REDLINE_ACCEPT_DIRECT; _viewsh.sdi:207
- `AcceptAllTrackedChanges`: W:332; swriter.sdi:8100 FN_REDLINE_ACCEPT_ALL; docsh.sdi:64
- `RejectTrackedChangeToNext`: W:260; swriter.sdi:8228 FN_REDLINE_REJECT_TONEXT; _viewsh.sdi:249
- `RejectTrackedChange`: W:246; swriter.sdi:8118 FN_REDLINE_REJECT_DIRECT; _viewsh.sdi:213
- `RejectAllTrackedChanges`: W:282; swriter.sdi:8137 FN_REDLINE_REJECT_ALL; docsh.sdi:69
- `CompareDocuments`: G:5197; sfx.sdi:738 SID_DOCUMENT_COMPARE; _viewsh.sdi:256
- `MergeDocuments`: G:5211; sfx.sdi:2525 SID_DOCUMENT_MERGE; _viewsh.sdi:262

- Omitted: Editor (cloud parts; LibreOffice's checker is Spelling and Grammar next to it, and Editor is on Home);
  Protect > Block Authors (co-authoring).
- Launcher (not built): Markup: Tools > Options... (menubar.xml:837), page Writer > Changes.
- Writer has no next or previous comment command (no matching name in WriterCommands.xcu or
  GenericCommands.xcu), so Previous and Next are placeholders on Calc's family name. A later implementation can
  build on Navigate By (`.uno:NavElement` W:3769, `FN_NAV_ELEMENT` `sw/inc/cmdid.h:194`) with `.uno:ScrollToPrevious`
  / `.uno:ScrollToNext` (W:3774, W:3782).

### View (Word: Views, Immersive, Dark Mode, Page Movement, Show, Zoom, Window, Macros, SharePoint)

| Section | Word label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Views | Read Mode | L | tgl | PLACEHOLDER `.uno:ViewMode?Mode:string=read` | family slot, W1 |  |
| Views | Print Layout | L | tgl | `.uno:PrintLayout` | W:30; swriter.sdi:5280 FN_PRINT_LAYOUT; _viewsh.sdi:135 |  |
| Views | Web Layout | L | tgl | `.uno:BrowseView` | G:3449; sfx.sdi:570 SID_BROWSER_MODE; _viewsh.sdi:130 |  |
| Views | Outline | S | tgl | PLACEHOLDER `.uno:ViewMode?Mode:string=outline` | family slot, W1 |  |
| Views | Draft | S | tgl | PLACEHOLDER `.uno:ViewMode?Mode:string=draft` | family slot, W1 |  |
| Immersive | Focus | L | tgl | `.uno:FullScreen` | G:4137; sfx.sdi:1328 SID_WIN_FULLSCREEN; frmslots.sdi:274 | approximate: Full Screen |
| Immersive | Immersive Reader | L | tgl | PLACEHOLDER `.uno:ViewMode?Mode:string=immersive` | family slot, W1 |  |
| Dark Mode | Dark Mode | L | tgl | `.uno:ChangeTheme` | G:1491; sfx.sdi:6004 FN_CHANGE_THEME; appslots.sdi:67 | Calc ruling 9 |
| Page Movement | Vertical | L | tgl | PLACEHOLDER `.uno:ViewPageMovement?Mode:string=vertical` | family slot, W1 |  |
| Page Movement | Side to Side | L | tgl | PLACEHOLDER `.uno:ViewPageMovement?Mode:string=sidetoside` | family slot, W1 |  |
| Show | Ruler | chk | chk | `.uno:Ruler` | W:3063; swriter.sdi:5490 FN_RULER; _viewsh.sdi:939 | small-label toggle |
| Show | Gridlines | chk | chk | `.uno:GridVisible` | G:5123; svx.sdi:4249 SID_GRID_VISIBLE; _viewsh.sdi:1023 | small-label toggle |
| Show | Navigation Pane | chk | chk | `.uno:Navigator` | G:4831; sfx.sdi:2637 SID_NAVIGATOR; frmslots.sdi:31 | small-label toggle |
| Zoom | Zoom | L | btn | `.uno:Zoom` | G:1523; sfx.sdi:5884 SID_ATTR_ZOOM; _viewsh.sdi:486 |  |
| Zoom | 100% | L | btn | `.uno:Zoom100Percent` | G:2140; sfx.sdi:1453 SID_ZOOM_100_PERCENT; appslots.sdi:209 |  |
| Zoom | One Page | S | btn | `.uno:ZoomPage` | G:2169; sfx.sdi:1390 SID_ZOOM_ENTIRE_PAGE; appslots.sdi:184 |  |
| Zoom | Multiple Pages | S | dd | `.uno:ShowMultiplePages` | W:1725; swriter.sdi:5973 FN_SHOW_MULTIPLE_PAGES; viewsh.sdi:522 | LO grid popup (Controller.xcu:1755) |
| Zoom | Page Width | S | btn | `.uno:ZoomPageWidth` | G:3741; sfx.sdi:1348 SID_ZOOM_PAGE_WIDTH; appslots.sdi:194 |  |
| Window | New Window | L | btn | `.uno:NewWindow` | G:4091; sfx.sdi:2815 SID_NEWWINDOW; frmslots.sdi:215 |  |
| Window | Arrange All | L | btn | PLACEHOLDER `.uno:ViewArrangeAll` | family slot, W1 | Calc name |
| Window | Split | L | btn | PLACEHOLDER `.uno:ViewSplit` | family slot, W1 |  |
| Window | View Side by Side | S | tgl | PLACEHOLDER `.uno:ViewSideBySide?Action:string=toggle` | family slot, W1 | Calc name |
| Window | Synchronous Scrolling | S | tgl | PLACEHOLDER `.uno:ViewSideBySide?Action:string=sync` | family slot, W1 | Calc name |
| Window | Reset Window Position | S | btn | PLACEHOLDER `.uno:ViewSideBySide?Action:string=reset` | family slot, W1 | Calc name |
| Window | Switch Windows | L | dd | `.uno:ViewSwitchWindowsMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | WindowList. Calc name, Writer node |
| Macros | Macros | L | dd | `.uno:ViewMacrosMenu` (new menu) | new: W label, Controller.xcu Popup+ToolBox, sw popupmenu | RunMacro; MacroRecorder; MacroManager; BasicIDEAppear. Calc name, Writer node |

Menu items (all real commands; evidence as above):

- `WindowList`: G:7322; no slot; WindowListMenuController (Controller.xcu:1132-1141)
- `RunMacro`: G:5957; sfx.sdi:2436 SID_RUNMACRO; appslots.sdi:282
- `MacroRecorder`: G:5606; sfx.sdi:3534 SID_RECORDMACRO; frmslots.sdi:75
- `MacroManager`: G:5965; sfx.sdi:2454 SID_MACROMANAGER; appslots.sdi:291
- `BasicIDEAppear`: G:1897; sfx.sdi:397 SID_BASICIDE_APPEAR; appslots.sdi:267

- Omitted: SharePoint > Properties (cloud).
- Dark Mode is placed after Immersive (research: `GroupNightMode` is in the 2024 control list, not in the images).
- In Calc the Macro Manager item is hidden unless experimental mode is on (`product/odd/tasks/calc-ribbon-tabs.md:78`);
  the same is expected here (inferred).

### Help (Word: Help), new page

| Section | Word label | Size | Type | LibreOffice command | Evidence | Menu contents, notes |
|---|---|---|---|---|---|---|
| Help | Help | L | btn | `.uno:HelpIndex` | G:1782; sfx.sdi:1909 SID_HELPINDEX; appslots.sdi:40 |  |
| Help | Contact Support | L | btn | `.uno:QuestionAnswers` | G:5774; sfx.sdi:5156 SID_Q_AND_A; appslots.sdi:131 | Calc's Get Help Online |
| Help | Feedback | L | btn | PLACEHOLDER `.uno:HelpFeedback` | family slot, W1 | Calc name and ruling 23 |
| Help | Show Training | L | btn | `.uno:Documentation` | G:5790; sfx.sdi:5171 SID_DOCUMENTATION; appslots.sdi:135 | User Guides |
| Help | What's New | L | btn | `.uno:WhatsNew` | G:5806; sfx.sdi:5216 SID_WHATSNEW; appslots.sdi:147 |  |

- No Community section: Word has none (research section 8). Calc's Blog placeholder is not repeated.

## 2. LibreOffice-only buttons that leave the tabs

What counts: every command of a stock page and of its overflow menu (`Menu Home` `notebookbar.ui:592`,
`Menu Insert` `:1008`, `Menu Page` `:1289`, `Menu References` `:1467`, `Menu Review` `:1593`, `Menu View` `:2222`)
that no tab of the new ribbon keeps and that is not on the File, Extension or Tools tab (they stay). The overflow
menus are counted because the generator deletes them with their pages (`remove_objects`,
`product/ui/gen_ribbon.py:319-324`); Calc's `LEFT_THE_TAB` covered only the page buttons
(`product/tests/test_calc_view_ui.py:72-74`).

**Totals: 75 entries over the six tabs, 74 distinct commands** (`.uno:InsertFieldCtrl` leaves Insert and
References). Classes:

- **a** (59): the same command is in the menu bar.
- **b** (12): only an equivalent entry is in the menu bar; the test asserts the equivalent id.
- **q** (1): `.uno:Menubar` stays in the quick access bar, as in Calc (`product/tests/test_calc_view_ui.py:178`).
- **c** (2): no menu-bar path: `.uno:ArrowsToolbox` and `.uno:InsertDraw`. **They need a ruling** (section 6,
  question 2). Proposal: accept View > Toolbars > Drawing (menubar.xml:195) as their path and assert the toolbar
  files.

Menu-bar paths use the menu labels (ContextLabel where one exists). Every row was checked with
`menu:id=".uno:<command>"` in `menubar.xml`.

### Home (32)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:Spacing` | page | G:4284; svx.sdi:8347 SID_ATTR_CHAR_KERNING; _textsh.sdi:1676 | Format > Character... (`.uno:FontDialog`, menubar.xml:451): character spacing is in that dialog | b |
| `.uno:StartPara` | page | G:1943; svx.sdi:5439 SID_ATTR_PARA_ADJUST_START; _textsh.sdi:1300 | Format > Align Text > Start (`.uno:CommonAlignStart`, menubar.xml:427) | b |
| `.uno:EndPara` | page | G:1954; svx.sdi:5457 SID_ATTR_PARA_ADJUST_END; _textsh.sdi:1306 | Format > Align Text > End (`.uno:CommonAlignEnd`, menubar.xml:429) | b |
| `.uno:HangingIndent` | page | G:5357; svx.sdi:13036 SID_HANGING_INDENT; _viewsh.sdi:655 | Format > Paragraph... (`.uno:ParagraphDialog`, menubar.xml:452), indent fields | b |
| `.uno:ParaLeftToRight` | page + menu | G:3765; svx.sdi:9742 SID_ATTR_PARA_LEFT_TO_RIGHT; _textsh.sdi:1787 | Format > Paragraph... (menubar.xml:452), text direction (inferred: field location not read) | b |
| `.uno:ParaRightToLeft` | page + menu | G:3781; svx.sdi:9760 SID_ATTR_PARA_RIGHT_TO_LEFT; _textsh.sdi:1793 | Format > Paragraph... (menubar.xml:452), text direction (inferred: field location not read) | b |
| `.uno:ParaspaceIncrease` | page | G:160; svx.sdi:12986 SID_PARASPACE_INCREASE; _viewsh.sdi:571 | Format > Spacing > Increase Paragraph Spacing (menubar.xml:418) | a |
| `.uno:ParaspaceDecrease` | page | G:174; svx.sdi:12969 SID_PARASPACE_DECREASE; _viewsh.sdi:578 | Format > Spacing > Decrease Paragraph Spacing (menubar.xml:419) | a |
| `.uno:Overline` | menu | G:1774; svx.sdi:9085 SID_ATTR_CHAR_OVERLINE; _textsh.sdi:1586 | Format > Text > Overline (menubar.xml:384) | a |
| `.uno:ChangeCaseRotateCase` | menu | G:3213; svx.sdi:1171 SID_TRANSLITERATE_ROTATE_CASE; _textsh.sdi:1745 | Format > Text > Cycle Case (menubar.xml:397) | a |
| `.uno:DecrementLevel` | menu | W:2227; swriter.sdi:735 FN_NUM_BULLET_DOWN; _listsh.sdi:21 | Format > Lists > Demote Outline Level (menubar.xml:459) | a |
| `.uno:IncrementLevel` | menu | W:2240; swriter.sdi:2472 FN_NUM_BULLET_UP; _listsh.sdi:77 | Format > Lists > Promote Outline Level (menubar.xml:460) | a |
| `.uno:DecrementSubLevels` | menu | W:2342; swriter.sdi:752 FN_NUM_BULLET_OUTLINE_DOWN; _listsh.sdi:42 | Format > Lists > Demote Outline Level with Subpoints (menubar.xml:461) | a |
| `.uno:IncrementSubLevels` | menu | W:2355; swriter.sdi:2489 FN_NUM_BULLET_OUTLINE_UP; _listsh.sdi:63 | Format > Lists > Promote Outline Level with Subpoints (menubar.xml:462) | a |
| `.uno:InsertNeutralParagraph` | menu | W:2313; swriter.sdi:3428 FN_NUM_BULLET_NONUM; _listsh.sdi:35 | Format > Lists > Insert Unnumbered Entry (menubar.xml:469) | a |
| `.uno:NumberingStart` | menu | W:2802; swriter.sdi:4914 FN_NUMBER_NEWSTART; _textsh.sdi:107 | Format > Lists > Restart Numbering (menubar.xml:470) | a |
| `.uno:ContinueNumbering` | menu | W:3758; swriter.sdi:7755 FN_NUM_CONTINUE; _textsh.sdi:113 | Format > Lists > Add to List (menubar.xml:471) | a |
| `.uno:InsertNonBreakingSpace` | menu | G:7549; svx.sdi:11359 FN_INSERT_HARD_SPACE; _textsh.sdi:237 | Insert > Formatting Mark > No-break Space (menubar.xml:335) | a |
| `.uno:InsertHardHyphen` | menu | G:7527; svx.sdi:11342 FN_INSERT_HARDHYPHEN; _textsh.sdi:231 | Insert > Formatting Mark > Non-breaking Hyphen (menubar.xml:336) | a |
| `.uno:InsertSoftHyphen` | menu | G:7538; svx.sdi:11325 FN_INSERT_SOFT_HYPHEN; _textsh.sdi:225 | Insert > Formatting Mark > Soft Hyphen (menubar.xml:337) | a |
| `.uno:InsertZWSP` | menu | G:7571; svx.sdi:11257 SID_INSERT_ZWSP; _textsh.sdi:261 | Insert > Formatting Mark > Zero-width Space (menubar.xml:339) | a |
| `.uno:InsertWJ` | menu | G:7582; svx.sdi:11274 SID_INSERT_WJ; _textsh.sdi:267 | Insert > Formatting Mark > Word Joiner (menubar.xml:340) | a |
| `.uno:InsertLRM` | menu | G:7593; svx.sdi:11291 SID_INSERT_LRM; _textsh.sdi:255 | Insert > Formatting Mark > Left-to-Right Mark (menubar.xml:341) | a |
| `.uno:InsertRLM` | menu | G:7604; svx.sdi:11308 SID_INSERT_RLM; _textsh.sdi:249 | Insert > Formatting Mark > Right-to-Left Mark (menubar.xml:342) | a |
| `.uno:FontDialog` | menu | G:7225; svx.sdi:3071 SID_CHAR_DLG; _textsh.sdi:1682 | Format > Character... (menubar.xml:451) | a |
| `.uno:OutlineBullet` | menu | G:3414; svx.sdi:6200 SID_OUTLINE_BULLET; _textsh.sdi:914 | Format > Bullets and Numbering... (menubar.xml:477) | a |
| `.uno:ParagraphDialog` | menu | G:4609; svx.sdi:6618 SID_PARA_DLG; _textsh.sdi:1389 | Format > Paragraph... (menubar.xml:452) | a |
| `.uno:ChapterNumberingDialog` | menu | W:3195; swriter.sdi:525 FN_NUMBERING_OUTLINE_DLG; _textsh.sdi:778 | Tools > Heading Numbering... (menubar.xml:788) | a |
| `.uno:SelectionModeDefault` | menu | W:3325; swriter.sdi:7772 FN_SELECTION_MODE_DEFAULT; _textsh.sdi:1814 | Edit > Selection Mode > Standard (menubar.xml:119) | a |
| `.uno:SelectionModeBlock` | menu | W:3333; swriter.sdi:8008 FN_SELECTION_MODE_BLOCK; _textsh.sdi:1819 | Edit > Selection Mode > Block Area (menubar.xml:120) | a |
| `.uno:SelectTextMode` | menu | W:3055; swriter.sdi:7448 FN_READONLY_SELECTION_MODE; _textsh.sdi:1809 | Edit > Select Text (menubar.xml:123) | a |
| `.uno:ShadowCursor` | menu | W:186; swriter.sdi:5938 FN_SHADOWCURSOR; _viewsh.sdi:1063 | Edit > Direct Cursor Mode (menubar.xml:177) | a |

### Insert (13)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:InsertAVMedia` | page + menu | G:7489; sfx.sdi:5582 SID_INSERT_AVMEDIA; _textsh.sdi:362 | Insert > Media > Audio or Video... (menubar.xml:280) | a |
| `.uno:InsertFieldCtrl` | page | W:1165; swriter.sdi:3068 FN_INSERT_FIELD_CTRL; _textsh.sdi:947 | Insert > Field (menubar.xml:362) | a |
| `.uno:ArrowsToolbox` | page | G:2450; svx.sdi:5764 SID_DRAWTBX_ARROWS; viewsh.sdi:140 | **none**: only in the Drawing toolbar (sw/uiconfig/swriter/toolbar/drawbar.xml), which View > Toolbars (menubar.xml:195) shows | c |
| `.uno:BasicShapes.rectangle` | page | G:244; variant of `.uno:BasicShapes` (svx.sdi:10703) | Insert > Shape > Basic Shapes (`.uno:BasicShapes`, menubar.xml:305; inferred: the submenu lists the rectangle) | b |
| `.uno:BasicShapes.ellipse` | page | G:287; variant of `.uno:BasicShapes` (svx.sdi:10703) | Insert > Shape > Basic Shapes (menubar.xml:305; inferred: the submenu lists the ellipse) | b |
| `.uno:DrawCaption` | page | G:4378; svx.sdi:982 SID_DRAW_CAPTION; viewsh.sdi:224 | Insert > Shape > Callout Shapes (`.uno:CalloutShapes`, menubar.xml:309); a custom-shape callout, not the legacy caption object | b |
| `.uno:LineToolbox` | page | G:5365; svx.sdi:86 SID_DRAWTBX_LINES; viewsh.sdi:22 | Insert > Shape > Line (`.uno:ShapesLineMenu`, menubar.xml:292-301) | b |
| `.uno:InsertDraw` | page | G:4303; svx.sdi:2480 SID_INSERT_DRAW; viewsh.sdi:86 | **none**: only in the Standard toolbars (standardbar.xml, singlemode-text.xml, singlemode-table.xml) | c |
| `.uno:StyleApply?Style:string=Horizontal Line` | menu | no label node of its own; sfx.sdi:4496 SID_STYLE_APPLY; _basesh.sdi:374 | Styles > Horizontal Line (`.uno:HorizontalLine`, menubar.xml:600) | b |
| `.uno:TwainSelect` | menu | G:4729; svx.sdi:9028 SID_TWAIN_SELECT; _viewsh.sdi:433 | Insert > Media > Scan > Select Source... (menubar.xml:276) | a |
| `.uno:InsertQrCode` | menu | G:7902; svx.sdi:13157 SID_INSERT_QRCODE; viewsh.sdi:56 | Insert > OLE Object > QR and Barcode... (menubar.xml:286) | a |
| `.uno:InsertFormula` | menu | W:2187; swriter.sdi:3121 FN_EDIT_FORMULA; _textsh.sdi:189 | Table > Edit Formula (menubar.xml:688) | a |
| `.uno:InsertFrameInteract` | menu | W:880; swriter.sdi:3173 FN_INSERT_FRAME_INTERACT; textsh.sdi:21 | Insert > Frame > Frame Interactively (menubar.xml:321) | a |

Kept on another tab (not leaving): `InsertBreak -> Layout > Page Setup`; `InsertEnvelope -> Mailings > Create`; `InsertSection -> Layout > Page Setup`.

### Layout (5)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:WrapIdeal` | page | W:2698; swriter.sdi:7050 FN_FRAME_WRAP_IDEAL; _basesh.sdi:532 | Format > Wrap > Optimal (menubar.xml:544) | a |
| `.uno:WrapLeft` | page | W:2818; swriter.sdi:7067 FN_FRAME_WRAP_LEFT; _basesh.sdi:581 | Format > Wrap > Before (menubar.xml:545) | a |
| `.uno:WrapRight` | page | W:2831; swriter.sdi:7118 FN_FRAME_WRAP_RIGHT; _basesh.sdi:588 | Format > Wrap > After (menubar.xml:546) | a |
| `.uno:PageColumnDialog` | menu | W:1553; swriter.sdi:5001 FN_FORMAT_PAGE_COLUMN_DLG; _basesh.sdi:280 | Format > Columns... (`.uno:FormatColumns`, menubar.xml:484) | b |
| `.uno:UseHeaderFooterMenu` | menu | W:448; swriter.sdi:8702 FN_USE_HEADERFOOTERMENU; _viewsh.sdi:1082 | Insert > Header and Footer > Use header/footer menu (menubar.xml:367) | a |

Kept on another tab (not leaving): `BorderDialog -> Home > Paragraph`; `InsertPageFooter -> Insert > Header & Footer`; `InsertPageHeader -> Insert > Header & Footer`; `PageDialog -> Design > Page Background`; `PageNumberWizard -> Insert > Header & Footer`; `SelectObject -> Home > Editing`; `ThemeDialog -> Design > Document Formatting`; `TitlePageDialog -> Insert > Pages`; `Watermark -> Design > Page Background`.

### References (8)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:UpdateAll` | page | W:541; swriter.sdi:6776 FN_UPDATE_ALL; _basesh.sdi:167 | Tools > Update > Update All (menubar.xml:798) | a |
| `.uno:InsertFootnoteDialog` | menu | W:707; swriter.sdi:3086 FN_INSERT_FOOTNOTE_DLG; _textsh.sdi:920 | Insert > Footnote and Endnote > Insert Special Footnote/Endnote... (menubar.xml:350) | a |
| `.uno:InsertFieldCtrl` | menu | W:1165; swriter.sdi:3068 FN_INSERT_FIELD_CTRL; _textsh.sdi:947 | Insert > Field (menubar.xml:362) | a |
| `.uno:Repaginate` | menu | W:2527; swriter.sdi:5420 FN_REPAGINATE; _basesh.sdi:139 | Tools > Update > Page Formatting (menubar.xml:800) | a |
| `.uno:UpdateFields?UnlockSoftFixed:bool=1` | menu | W:2137; swriter.sdi:6864 FN_UPDATE_FIELDS; _basesh.sdi:151 | Tools > Update > Update Fields (menubar.xml:803) | a |
| `.uno:UpdateAllIndexes` | menu | W:210; swriter.sdi:6794 FN_UPDATE_TOX; _viewsh.sdi:416 | Tools > Update > Indexes and Tables (menubar.xml:804) | a |
| `.uno:UpdateAllLinks` | menu | W:379; swriter.sdi:6811 FN_UPDATE_ALL_LINKS; _basesh.sdi:519 | Tools > Update > Links (menubar.xml:806) | a |
| `.uno:UpdateCharts` | menu | W:584; swriter.sdi:6829 FN_UPDATE_CHARTS; _basesh.sdi:162 | Tools > Update > Charts (menubar.xml:807) | a |

Kept on another tab (not leaving): `InsertBookmark -> Insert > Links`; `InsertPageNumberField -> Insert > Header & Footer`; `ViewDataSourceBrowser -> Mailings > Start Mail Merge`.

### Review (5)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:SpellOnline` | page + menu | G:5507; svx.sdi:8366 SID_AUTOSPELL_CHECK; _viewsh.sdi:895 | Tools > Automatic Spell Checking (menubar.xml:754) | a |
| `.uno:ReplyComment` | page | G:6986; swriter.sdi:7788 FN_REPLY; _textsh.sdi:1084 | Edit > Comment > Reply Comment (menubar.xml:153) | a |
| `.uno:AutoFormatMenu` | menu | W:3737; submenu id, no slot | Tools > AutoCorrect (menubar.xml:773) | a |
| `.uno:ProtectTraceChangeMode` | menu | G:5183; swriter.sdi:5368 FN_REDLINE_PROTECT; _viewsh.sdi:164 | Edit > Track Changes > Protect... (menubar.xml:148) | a |
| `.uno:RedactDoc` | menu | G:5713; sfx.sdi:5102 SID_REDACTDOC; docslots.sdi:251 | Tools > Redact (menubar.xml:785) | a |

Kept on another tab (not leaving): `AutoCorrectDlg -> Menu Tools (stays)`; `AutoFormatApply -> Menu Tools (stays)`; `AutoFormatRedlineApply -> Menu Tools (stays)`; `Hyphenate -> Layout > Page Setup`; `OnlineAutoFormat -> Menu Tools (stays)`.

### View (12)

| Command | Was on | Evidence | Menu-bar path | Class |
|---|---|---|---|---|
| `.uno:ShowWhitespace` | page + menu | W:3234; swriter.sdi:6026 FN_VIEW_SHOW_WHITESPACE; _viewsh.sdi:921 | View > Whitespace (menubar.xml:222) | a |
| `.uno:ZoomOptimal` | page | G:2185; sfx.sdi:1369 SID_ZOOM_OPTIMAL; appslots.sdi:189 | View > Zoom > Optimal View (menubar.xml:243) | a |
| `.uno:Sidebar` | page + menu | G:4858; sfx.sdi:2687 SID_SIDEBAR; frmslots.sdi:46 | View > Sidebar (menubar.xml:232) | a |
| `.uno:Menubar` | page + menu | G:7771; sfx.sdi:2705 SID_MENUBAR; appslots.sdi:224 | quick access bar, first item (sw/uiconfig/swriter/toolbar/notebookbarshortcuts.xml:11), as in Calc | q |
| `.uno:HelplinesMove` | page | G:4105; svx.sdi:4325 SID_HELPLINES_MOVE; _viewsh.sdi:1033 | View > Grids and Helplines > Helplines While Moving (menubar.xml:214) | a |
| `.uno:GridUse` | page + menu | G:4121; svx.sdi:4230 SID_GRID_USE; _viewsh.sdi:1028 | View > Grids and Helplines > Snap to Grid (menubar.xml:213) | a |
| `.uno:ShowResolvedAnnotations` | menu | W:3079; svx.sdi:4779 SID_TOGGLE_RESOLVED_NOTES; _viewsh.sdi:933 | View > Resolved Comments (menubar.xml:226) | a |
| `.uno:StatusBarVisible` | menu | G:5835; sfx.sdi:4335 SID_TOGGLESTATUSBAR; frmslots.sdi:70 | View > Status Bar (menubar.xml:196) | a |
| `.uno:BaselineGridVisible` | menu | W:3606; swriter.sdi:9073 FN_VIEW_BASELINE_GRID_VISIBLE; _viewsh.sdi:1113 | View > Grids and Helplines > Display Baseline Grid (menubar.xml:215) | a |
| `.uno:ShowBoundaries` | menu | W:3288; swriter.sdi:6477 FN_VIEW_BOUNDARIES; _viewsh.sdi:958 | View > Boundaries (menubar.xml:220) | a |
| `.uno:ShowGraphics` | menu | W:3090; swriter.sdi:2331 FN_VIEW_GRAPHIC; _viewsh.sdi:964 | View > Images and Charts (menubar.xml:221) | a |
| `.uno:Fieldnames` | menu | W:3272; swriter.sdi:1287 FN_VIEW_FIELDNAME; _viewsh.sdi:975 | View > Field Names (menubar.xml:229) | a |

Kept on another tab (not leaving): `ControlCodes -> Home > Paragraph`; `Marks -> Mailings > Write & Insert Fields`; `PrintPreview -> Menu File (stays)`; `SelectObject -> Home > Editing`.

The Design, Mailings and Help pages are new, so nothing leaves them.

## 3. How it will be built

### 3.1 The generator for more than one app

Today `product/ui/gen_ribbon.py` is Calc-only in five places: `TABS_FILE` (`:39`), `UPSTREAM_UI`, `OFFICE_UI` and
`SUPPR` (`:41-43`), the `calc_*.json` glob in `page_layouts` (`:446-450`), and `regenerate_all_files`/`main`
(`:484-525`). The page code itself takes its ids, prefixes and gettext context from the layout file
(`emit_item` `:154-163`, `splice` `:304-325`).

- **One app table** replaces those constants: per app the upstream `.ui`, the office `.ui`, the `.suppr` and
  `.false` files, the layout prefix and the tabs file.
  - calc: `sc/uiconfig/scalc/ui/notebookbar.ui` -> `sc/uiconfig/scalc/ui/notebookbar_office.ui`,
    `solenv/sanitizers/ui/modules/scalc.suppr`, `product/ui/calc_*.json`, `product/ui/calc_tabs.json`.
  - writer: `sw/uiconfig/swriter/ui/notebookbar.ui` -> `sw/uiconfig/swriter/ui/notebookbar_office.ui`,
    `solenv/sanitizers/ui/modules/swriter.suppr` and `swriter.false`, `product/ui/writer_*.json`,
    `product/ui/writer_tabs.json`.
- `--all` rebuilds every app; `--app writer` rebuilds one. `--root` stays.
- **Inputs for Writer**:
  - `product/ui/writer_tabs.json`: page `valign` from `center` to `fill` for "Home Tab" (`notebookbar.ui:3062-3063`)
    and "Layout Tab" (`:5131-5132`), as Calc did for `phbLayout` (`product/ui/calc_tabs.json:6-10`); `add_pages` for
    the Design, Mailings and Help pages; `positions` for every page and tab label. The Extension and Tools pages of
    Writer have no `valign` property (`notebookbar.ui:14623-14629`, `:14762-14768`), so no operation there.
  - `product/ui/writer_<tab>.json` for home, insert, design, layout, references, mailings, review, view, help: page
    id (stock ids with spaces, such as `"Home Tab"`; `find_object` matches `id="..."` exactly, `:290-301`), prefix
    (Home, Insert, ...), context `TabbedWriter`, and `remove_objects` with the overflow menu of the page.
  - An optional item key `office_label` holds Word's label. The generator ignores it today (T9, decision 29).
- **Output**: `sw/uiconfig/swriter/ui/notebookbar_office.ui` = stock + tab operations + every generated page,
  the same contract as Calc (`product/tests/office.py:10-24`).
- **Calc stays byte-identical**: record the sha256 of `sc/uiconfig/scalc/ui/notebookbar_office.ui`,
  `scalc.suppr` and `scalc.false` before W0a; after it, `--all` must reproduce them, and the existing test
  "office .ui == upstream + tab operations + every generated page" stays green. No Calc layout file changes.
- **Registration**: add `sw/uiconfig/swriter/ui/notebookbar_office \` to the `gb_UIConfig_add_uifiles` list (`sw/UIConfig_swriter.mk:101`) next to the
  stock variants (`:248-253`) (Calc's line: `sc/UIConfig_scalc.mk:208`); new popup files go into
  `gb_UIConfig_add_popupmenufiles` (`sw/UIConfig_swriter.mk:17-34`).
- **Suppressions**: `solenv/sanitizers/ui/modules/swriter.suppr` has 384 lines for the stock `notebookbar.ui` and
  none for an office file; `swriter.false` has 713 stock lines. W0a seeds copies of both with the office path.
  Only 277 of those 713 lines name widgets that still exist in the stock `notebookbar.ui`, so `swriter.false`
  gets 277 office lines (W0a, 2026-10-20).
  `sync_suppr` (`gen_ribbon.py:461-481`) handles only the `.suppr`; the Writer run also drops `.false` lines whose id
  is gone. `product/dev/check-ui.sh:9-10` hard-codes the Calc files and picks them by app instead.
- **Test tooling per app**: `product/tests/office.py:10-14` keeps its Calc names as aliases (other modules import
  them; `product/tests/test_icons.py:16` has its own Calc path and is not touched) and gains `app("writer")`.
  `product/tests/commands.py:15` (Calc labels, then Generic) gains the Writer order (WriterCommands.xcu, then
  GenericCommands.xcu). The placeholder registry is a separate file, `product/tests/placeholders_writer.json`,
  read by the same `placeholders.py`.

### 3.2 Mode, picker, profile, launcher, screenshots

- **ToolbarMode.xcu**: the Writer node is `officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu:17-296`
  with MenuPositions 0-8. Add a `TabbedOffice` mode copied from Calc's (`:409-436`: Label "Tabbed Office",
  HasNotebookbar true, MenuPosition 9, CommandArg `notebookbar_office.ui`, Sidebar Arrow). sfx2 resolves the file
  at run time (`sfx2/source/notebookbar/SfxNotebookBar.cxx:311-345`, called from
  `sw/source/uibase/app/docsh.cxx:1107`), so sfx2 needs no change.
- **cui whitelist**: "Tabbed Office is only available in Calc" hides the radio button for other apps
  (`cui/source/dialogs/uitabpage.cxx:67-69`), and `GetModeForApp` maps the office file back to `notebookbar.ui` for
  them (`:94-98`), which "Apply to All" uses for Writer (`cui/source/dialogs/uipickerdlg.cxx:90-105`). One helper
  "this app has Tabbed Office" (Calc, Writer) replaces both tests; about 10 lines of C++. Impress stays out until
  its own feature.
- **Preview picture**: `UpdateImage` loads `$BRAND_BASE_DIR/$BRAND_SHARE_SUBDIR/toolbarmode/<file>`
  (`uitabpage.cxx:171-183`) from the mode table (`cui/inc/uimode.hrc:25`, `notebookbar_office.png`, a Calc picture
  packaged by `vcl/Package_toolbarmode.mk:18`). W0b makes `UpdateImage` prefer `notebookbar_office_<app>.png` when it
  exists (about 6 lines of C++); W11 adds `notebookbar_office_writer.png` to the package. Until then Writer shows
  the Calc picture.
- **profile.py**: `CALC_APP` (`product/dev/profile.py:14`) and `build_items` (`:34-38`) write only Calc's
  `Active`/`ActiveCalc`. Add an `app` parameter (calc, writer) that writes `Applications['Writer']/Active` and
  `ActiveWriter` (the schema has `ActiveWriter`, `ToolbarMode.xcs:112`); `product/tests/test_profile.py:29-60` gains
  the Writer cases.
- **Launcher**: `product/dev/calc.sh` starts `soffice --calc` with its profile guard (`:58`, `:63`, `:104`). It becomes
  `product/dev/office.sh <app> <theme>`, and `calc.sh` stays as a one-line wrapper so its users and
  `product/tests/test_calc_launcher.py` keep working (decision 31).
- **shot-tab.sh**: `--calc` (`product/dev/shot-tab.sh:229`), the "no Calc window" check (`:239`), the default
  `SHOT_TABS` (`:246`) and the tab-bar ink rows `y0, y1, x0 = 14, 36, 225` (`:253`) are Calc's. Add an app option,
  Writer's tab list (File, Home, Insert, Design, Layout, References, Mailings, Review, View, Extension, Tools, Help)
  and re-measure `x0`, because Writer's quick access bar has other items (`notebookbarshortcuts.xml:11-16`).
- **UITests**: Writer's target `UITest_writer_tests8` adds the whole `sw/qa/uitest/writer_tests8/` directory with
  documents from `sw/qa/uitest/data` (`sw/UITest_writer_tests8.mk`; targets listed in `sw/Module_sw.mk:275-283`). A
  new file `sw/qa/uitest/writer_tests8/notebookbarOffice.py` therefore needs **no new gbuild target**.
  `product/dev/uitest.sh:10-12` hard-codes `UITest_calc_tests` and its `done.log`; it gains an app option
  (`writer` -> `UITest_writer_tests8`, `workdir/UITest/writer_tests8/done.log`).
- **Builds** (only through `product/dev/lo-make.sh`): `sw.build` (slots, `.sdi`, `.ui`, popups),
  `cui.build`, `officecfg.build` then `postprocess.build` for the `.xcu`/`.xcs` changes, `vcl.build` and
  `sfx2.build` only for the accent.

### 3.3 Placeholder slots

- **Free range** (verified): Writer slots run from `SID_SW_START` 20000 to `SID_SC_START` 26000
  (`include/svl/solar.hrc:69`, `:71`). Evaluating every `#define` of `solar.hrc`, `sfxsids.hrc`, `svxids.hrc`,
  `editids.hrc`, `sw/inc/cmdid.h` and the sw `.hrc` files gives 737 ids in that range, the highest 22610
  (`FN_PAGEBREAK = SID_SW_START + 2610`, `sw/inc/cmdid.h:55`). The largest free gap is 22611-25999.
- **Fork block**: `FN_BOOST = SID_SW_START + 5900` (25900-25999, 100 ids), defined in `cmdid.h` after `:55`, at the
  top of the range as Calc's block is at its ceiling. This feature uses `FN_BOOST+0..+23` (24 slots); 76 stay
  spare. The test proves no other define falls in the block.
- **Shell**: interface `TextEditView` (`sw/sdi/viewsh.sdi:19`), which shell `SwView` imports (`:431-433`). `SwView` is
  on the dispatcher stack under every Writer text subshell, so one entry serves the text, table, frame, graphic,
  draw and OLE contexts. Each slot gets `StateMethod = GetState ;` and no `ExecMethod`, as `SID_DRAWTBX_LINES`
  does (`viewsh.sdi:21-25`). `SwView::GetState` (`sw/source/uibase/uiview/viewstat.cxx:63`) gets one `case` group
  that calls `rSet.DisableItem(nWhich)`.
  - Writer/Web (`SwWebView`, `sw/sdi/wviewsh.sdi:19-31`) and the print preview (`SwPagePreview`, `viewsh.sdi:644`) do
    not import `TextEditView`; there the commands are unknown and the buttons are disabled anyway.
- **Declaration**: `sw/sdi/swriter.sdi`, in the format of `ShowMultiplePages` (`:5973-5988`), with `ReadOnlyDoc =
  FALSE` and `AccelConfig`, `MenuConfig`, `ToolBoxConfig = FALSE`.
- **Labels**: `WriterCommands.xcu`, one node per URL variant: `Label`, `TooltipLabel` "<Label> (not available
  yet)", `Properties` 1, as Calc.
- **Registry and test**: `product/tests/placeholders_writer.json` (slot, offset, base command, variants, labels)
  and `product/tests/test_writer_slots.py`: each slot in the fork block, declared in `swriter.sdi`, listed in
  `viewsh.sdi` with a state method and no execute method, in the `DisableItem` group of `viewstat.cxx`, mentioned
  by no other source, and no gaps or duplicates. It mirrors `product/tests/test_calc_slots.py:80-114`.

### 3.4 The accent (approved by the user on 2026-10-20)

Where the green comes from (verified):

- The selected tab's underline is CSS of the gtk3 plugin: `box-shadow: inset 0 -3px 0 #<ActiveColor>`
  (`vcl/unx/gtk3/custom-theme.cxx:72-75`, rules at `:240-254`). The same `ActiveColor` colors links (`:101`), checked
  check and radio boxes (`:341`, `:357`), progress bars (`:382`) and the focus ring of entries and spin fields (`:483`).
- The CSS provider is built once per screen and cached (`custom-theme.cxx:27-42`, applied from
  `vcl/unx/gtk3/salnativewidgets-gtk.cxx:2354-2356`); `ThemeColors` is a static singleton
  (`include/vcl/themecolors.hxx:42-45`, loaded at `svtools/source/config/colorcfg.cxx:357-370`).
- The scheme maps `ActiveColor` and `ActiveBorderColor` to the token `accent.calc` (#1B7A3E / #5CC27E), and
  `AccentColor` to `selection` (#CFE8D7 / #1E4D2E) (`product/themes/palette.json:13-14`, `:22-23`). `AccentColor`
  becomes the accent, highlight and list-box highlight colors (`colorcfg.cxx:724-728`), so Writer's text selection
  is also green-tinted.
- One soffice process hosts every app, so a color scheme cannot carry a per-app accent.

**Proposal** (narrowest; approved by the user on 2026-10-20): only the tab underline follows the app.

- vcl: `NotebookbarTabControlBase` gets an optional accent color (`include/vcl/tabctrl.hxx`); after the native draw
  of the selected item (`vcl/source/control/tabctrl.cxx:878-900`, in `ImplDrawItem` from `:801`) it overpaints the
  3 px band in that color when one is set. About 20-30 lines.
- sfx2: `NotebookbarTabControl::StateChanged` already identifies the module on `InitShow`
  (`sfx2/source/notebookbar/NotebookbarTabControl.cxx:266-303`, `:290-292`); it reads the app's accent and sets it.
  About 15-20 lines.
- Config: two optional properties `AccentColor` and `AccentColorDark` in the ToolbarMode `Application` group
  (`officecfg/registry/schema/org/openoffice/Office/UI/ToolbarMode.xcs:95-109`), about 10 lines. Values come from
  palette tokens (`accent.writer` = Word blue, `accent.calc` stays green), written by
  `product/themes/build_schemes.py` into the scheme extension it already builds (`ColorSchemes.xcu` at `:84`), about
  25 lines.
- Total: about 35-50 lines of C++, plus tests (a source/config unit test and a pixel check of the underline in a
  Writer screenshot). Check boxes, focus rings, progress bars and the selection tint stay global (green).
- Risk: the overpainted band must line up with the CSS band; checked by screenshot.

**Fallback without C++**: set the roles `ActiveColor` and `ActiveBorderColor` (and, if wanted, `AccentColor`) in
`palette.json` to one app-neutral accent for every app, keeping `CalcCellFocus` green (`palette.json:30`). Calc
then loses its green tab underline.

## 4. Decisions and rulings

Made in the design, each worded so the user can overturn it.

**Scope and reference**

1. **Reference**: Word for Microsoft 365, Windows, Current Channel, 2024+ look, 1920 px (binding ruling). Sizes
   come from the research's per-group crops of a 2022-23 build; the 1920 px fit is measured, not assumed.
2. **Tab set and order**: File, Home, Insert, Design, Layout, References, Mailings, Review, View, Help. Extension and
   Tools stay with their content (binding ruling).
3. **Help goes last**, after Tools, as in Calc (Calc decision 3).
4. **Not in this feature**: Word's Draw tab, the File backstage, Word's contextual tabs. Writer's stock contextual
   tabs stay exactly as they are (binding ruling).
5. **Omitted, 19 controls**: cloud or account controls (Dictate, Sensitivity, Add-ins, Copilot, Online Videos,
   Get/My Add-ins, Loop, Search, Researcher, Acronyms, Editor on Review, Block Authors, SharePoint Properties), the
   older build's Reuse Files, and controls Word hides in an English UI (Left-to-Right, Right-to-Left, Text Direction).
   Barcode is conditional.
6. **Editor on Home is Spelling and Grammar**: LibreOffice's own checker stands in for Word's Editor; its cloud
   parts are omitted. On Review the separate Editor button is dropped because the next button is the same dialog.

**Structure**

7. **No dialog launchers and no in-group separators**, as in Calc: the generator has none
   (`product/docs/design/calc-ribbon-tabs-overview.txt:216`). Each launcher's dialog is listed under its tab with
   its menu-bar path.
8. **Word splits without an existing LibreOffice split become dropdowns** whose first item is Word's body action:
   Find, Object, Bring Forward, Send Backward, Next Footnote, Delete (comment), Accept, Reject. Reason: a split body
   needs a mirror slot in C++ (Calc's AutoSum recipe), and these bodies are often disabled, which is Calc's "VCL
   arrow problem" (`calc-ribbon-tabs-overview.txt:216-219`). No new C++ outside the placeholders, cui and the
   accent.
9. **Existing split controllers are reused**: Paste, Undo, Redo, Underline, the three color buttons, Bullets,
   Numbering, Multilevel List, Track Changes, Show Markup. They already serve other Writer toolbars, which Calc's
   constraint "never put a controller on a command that other toolbars use" allows only for existing controllers.
10. **A dropdown always has its own command** (Calc constraint). Calc's names are reused where the Office control
    is the same (`InsertShapesMenu`, `PageLayout*Menu`, `ViewSwitchWindowsMenu`, `ViewMacrosMenu`), so the icons are
    shared through the manifest; each gets Writer nodes (Module `com.sun.star.text.TextDocument`, node names with a
    `Writer` suffix) and a WriterCommands label, because Calc's nodes are Calc-only (`Controller.xcu:1213-1223`).
11. **Two buttons with the same command on one page** get distinct widget commands with the real URL as `action`
    (`gen_ribbon.py:51-58`, `:69-79`): References has three `InsertMultiIndex` and three `UpdateCurIndex` buttons.
12. **Check boxes are small-label toggles** (View > Show), as in Calc.
13. **Placeholders are plain greyed buttons**, also where Word has a menu, combo or gallery (Style Set, Style,
    Display for Review), as in Calc.
14. **Family slots**: 48 placeholder entries share 24 slots through URL variants, as in Calc (Calc decision 10).
    Calc's family names are reused for the same Office control (`Insert3DModels`, `InsertSmartArt`,
    `InsertScreenshot`, `PageLayoutThemePart`, `ReviewTranslate`, `ReviewGoToComment`, `ReviewHideInk`,
    `ViewArrangeAll`, `ViewSideBySide`, `HelpFeedback`) so they share icons. `PageLayoutThemePart` gains a `themes`
    variant for Design > Themes.
15. **Slots in a fork block at the top of the Writer range** (`FN_BOOST`, 25900-25999): upstream appends near
    22610 and rarely refills old holes; 100 ids leave room for the contextual tabs.
16. **Always-disabled state in `SwView`** (`TextEditView`), one place for every text context.
17. **The overflow menus are deleted with their pages**, and their items count in section 2.

**Content calls**

18. **Gallery is Word's Icons; the Navigator is the Selection Pane and the Navigation Pane** (Calc decision 17).
19. **Dark Mode is kept** (`.uno:ChangeTheme`) and **Translate is a placeholder** (Calc decision 9).
20. **Approximate mappings** run the nearest LibreOffice feature instead of a placeholder: Cover Page = Title Page
    dialog, Borders = paragraph Borders dialog, Date & Time = date field, Drop Cap = Drop Caps dialog, Position =
    anchor menu, Page Borders = Page Style dialog, Show Notes = jump between note and anchor, Add Text = heading
    styles, Bibliography = the index dialog, Edit Recipient List = data sources pane, Highlight Merge Fields = field
    shadings, Insert Merge Field = Fields dialog, Reviewing Pane = Manage Changes, Focus = Full Screen. Each is
    marked "approximate" in section 1.
21. **Line Numbers and Hyphenation are plain buttons**: Word's menus have presets that LibreOffice exposes only in
    its dialogs.
22. **Multiple Pages is LibreOffice's grid dropdown** (`.uno:ShowMultiplePages`), not Word's plain button.
23. **Undo stays on Home** (Calc ruling, `calc-home-redesign.md:141`), although Word 2024 moved it to the quick
    access bar.
24. **Page Number is a dropdown**: the Page Number wizard, the page number field (Word's Current Position) and the
    page count field. This keeps two stock commands that have no menu-bar entry on the ribbon.
25. **Mailings uses LibreOffice's mail-merge commands** where they exist (wizard, record navigation, finish
    actions); the five Write & Insert Fields commands without an equivalent and the three preview commands are
    placeholders on two family slots.
26. **The LibreOffice-only buttons that leave** (section 2) stay reachable in the menu bar, and a test asserts the
    exact or equivalent menu-bar id per command, as Calc's `LEFT_THE_TAB` does. The two without a path wait for a
    ruling.
27. **Icons**: Calc's icon for a reused name; a Fluent glyph with the closest meaning otherwise; menu-only items
    have no icon (Calc decision 24). The b tasks add the manifest entries.
28. **Popup entries that are disabled stay hidden** (LibreOffice default; Calc decision 25). With T10 undecided,
    the Arrange menus show no items while the cursor is in text (section 6).

**Pending user decisions, kept open**

29. **T9 (Office labels)**: the layout files keep Word's label per item (`office_label`), so either Calc option can
    be applied later: WriterCommands.xcu label overrides (they also rename the menus) or ribbon-only URL label
    variants. Nothing is renamed now.
30. **T10 (greyed disabled menu entries)**: popups are static files or existing controllers; nothing in this
    feature depends on the answer. The UITests check item lists from the popup files and the controllers, not the
    rendered menu, as Calc's do (`product/odd/tasks/calc-ribbon-tabs.md:77`).

**Process**

31. **Launcher**: `product/dev/office.sh <app> <theme>` with `calc.sh` as a wrapper, so the profile guard lives in
    one place.
32. **The b tasks wait for the icon worker**: `product/icons/` and `product/tests/test_icons.py` are being edited
    by another worker. Writer icon coverage goes into a new test file until that work lands.
33. **Delivery** is ask-on-risk with work-unit commits; the forecast is far over 400 lines, so the chain strategy is
    asked once before the first commit (plan, "Delivery").

## 5. Placeholders

48 entries on 24 slots (`FN_BOOST+0..+23`), all greyed with the tooltip "<Label> (not available yet)". Six are
menu items (Text Effects, Select). Registry: `product/tests/placeholders_writer.json`. To implement one later,
follow Calc's recipe and flag its entry `"implemented": true`.

| Tab, section | Label | Command (URL variant) | Slot |
|---|---|---|---|
| Home, Text Effects menu | Reflection | `.uno:HomeTextEffect?Effect:string=reflection` | `FN_BOOST_HOME_TEXT_EFFECT` (+0) |
| Home, Text Effects menu | Glow | `.uno:HomeTextEffect?Effect:string=glow` | `FN_BOOST_HOME_TEXT_EFFECT` (+0) |
| Home, Text Effects menu | Number Styles | `.uno:HomeTextEffect?Effect:string=numberstyles` | `FN_BOOST_HOME_TEXT_EFFECT` (+0) |
| Home, Text Effects menu | Ligatures | `.uno:HomeTextEffect?Effect:string=ligatures` | `FN_BOOST_HOME_TEXT_EFFECT` (+0) |
| Home, Text Effects menu | Stylistic Sets | `.uno:HomeTextEffect?Effect:string=stylisticsets` | `FN_BOOST_HOME_TEXT_EFFECT` (+0) |
| Home, Select menu | Select Text with Similar Formatting | `.uno:HomeSelectSimilar` | `FN_BOOST_HOME_SELECT_SIMILAR` (+1) |
| Insert, Pages | Blank Page | `.uno:InsertBlankPage` | `FN_BOOST_INSERT_BLANK_PAGE` (+2) |
| Insert, Illustrations | 3D Models | `.uno:Insert3DModels` | `FN_BOOST_INSERT_3D_MODELS` (+3) |
| Insert, Illustrations | SmartArt | `.uno:InsertSmartArt` | `FN_BOOST_INSERT_SMARTART` (+4) |
| Insert, Illustrations | Screenshot | `.uno:InsertScreenshot` | `FN_BOOST_INSERT_SCREENSHOT` (+5) |
| Design, Document Formatting | Themes | `.uno:PageLayoutThemePart?Part:string=themes` | `FN_BOOST_DESIGN_THEME_PART` (+6) |
| Design, Document Formatting | Fonts | `.uno:PageLayoutThemePart?Part:string=fonts` | `FN_BOOST_DESIGN_THEME_PART` (+6) |
| Design, Document Formatting | Effects | `.uno:PageLayoutThemePart?Part:string=effects` | `FN_BOOST_DESIGN_THEME_PART` (+6) |
| Design, Document Formatting | Style Set | `.uno:DesignStyleSet?Action:string=gallery` | `FN_BOOST_DESIGN_STYLE_SET` (+7) |
| Design, Document Formatting | Paragraph Spacing | `.uno:DesignStyleSet?Action:string=spacing` | `FN_BOOST_DESIGN_STYLE_SET` (+7) |
| Design, Document Formatting | Set as Default | `.uno:DesignStyleSet?Action:string=setdefault` | `FN_BOOST_DESIGN_STYLE_SET` (+7) |
| References, Citations & Bibliography | Style | `.uno:ReferencesCitationStyle` | `FN_BOOST_REFERENCES_CITATION_STYLE` (+8) |
| References, Table of Authorities | Mark Citation | `.uno:ReferencesAuthorities?Action:string=mark` | `FN_BOOST_REFERENCES_AUTHORITIES` (+9) |
| References, Table of Authorities | Insert Table of Authorities | `.uno:ReferencesAuthorities?Action:string=insert` | `FN_BOOST_REFERENCES_AUTHORITIES` (+9) |
| References, Table of Authorities | Update Table | `.uno:ReferencesAuthorities?Action:string=update` | `FN_BOOST_REFERENCES_AUTHORITIES` (+9) |
| Mailings, Write & Insert Fields | Address Block | `.uno:MailingsField?Field:string=addressblock` | `FN_BOOST_MAILINGS_FIELD` (+10) |
| Mailings, Write & Insert Fields | Greeting Line | `.uno:MailingsField?Field:string=greetingline` | `FN_BOOST_MAILINGS_FIELD` (+10) |
| Mailings, Write & Insert Fields | Rules | `.uno:MailingsField?Field:string=rules` | `FN_BOOST_MAILINGS_FIELD` (+10) |
| Mailings, Write & Insert Fields | Match Fields | `.uno:MailingsField?Field:string=matchfields` | `FN_BOOST_MAILINGS_FIELD` (+10) |
| Mailings, Write & Insert Fields | Update Labels | `.uno:MailingsField?Field:string=updatelabels` | `FN_BOOST_MAILINGS_FIELD` (+10) |
| Mailings, Preview Results | Preview Results | `.uno:MailingsPreview?Action:string=toggle` | `FN_BOOST_MAILINGS_PREVIEW` (+11) |
| Mailings, Preview Results | Find Recipient | `.uno:MailingsPreview?Action:string=find` | `FN_BOOST_MAILINGS_PREVIEW` (+11) |
| Mailings, Preview Results | Check for Errors | `.uno:MailingsPreview?Action:string=check` | `FN_BOOST_MAILINGS_PREVIEW` (+11) |
| Review, Speech | Read Aloud | `.uno:ReviewReadAloud` | `FN_BOOST_REVIEW_READ_ALOUD` (+12) |
| Review, Language | Translate | `.uno:ReviewTranslate` | `FN_BOOST_REVIEW_TRANSLATE` (+13) |
| Review, Comments | Previous | `.uno:ReviewGoToComment?Direction:string=previous` | `FN_BOOST_REVIEW_GOTO_COMMENT` (+14) |
| Review, Comments | Next | `.uno:ReviewGoToComment?Direction:string=next` | `FN_BOOST_REVIEW_GOTO_COMMENT` (+14) |
| Review, Markup | Filter All Markup | `.uno:ReviewMarkup?Action:string=filter` | `FN_BOOST_REVIEW_MARKUP` (+15) |
| Review, Markup | Display for Review | `.uno:ReviewMarkup?Action:string=display` | `FN_BOOST_REVIEW_MARKUP` (+15) |
| Review, Protect | Restrict Editing | `.uno:ReviewRestrictEditing` | `FN_BOOST_REVIEW_RESTRICT_EDITING` (+16) |
| Review, Ink | Hide Ink | `.uno:ReviewHideInk` | `FN_BOOST_REVIEW_HIDE_INK` (+17) |
| View, Views | Read Mode | `.uno:ViewMode?Mode:string=read` | `FN_BOOST_VIEW_MODE` (+18) |
| View, Views | Outline | `.uno:ViewMode?Mode:string=outline` | `FN_BOOST_VIEW_MODE` (+18) |
| View, Views | Draft | `.uno:ViewMode?Mode:string=draft` | `FN_BOOST_VIEW_MODE` (+18) |
| View, Immersive | Immersive Reader | `.uno:ViewMode?Mode:string=immersive` | `FN_BOOST_VIEW_MODE` (+18) |
| View, Page Movement | Vertical | `.uno:ViewPageMovement?Mode:string=vertical` | `FN_BOOST_VIEW_PAGE_MOVEMENT` (+19) |
| View, Page Movement | Side to Side | `.uno:ViewPageMovement?Mode:string=sidetoside` | `FN_BOOST_VIEW_PAGE_MOVEMENT` (+19) |
| View, Window | Arrange All | `.uno:ViewArrangeAll` | `FN_BOOST_VIEW_ARRANGE_ALL` (+20) |
| View, Window | Split | `.uno:ViewSplit` | `FN_BOOST_VIEW_SPLIT` (+21) |
| View, Window | View Side by Side | `.uno:ViewSideBySide?Action:string=toggle` | `FN_BOOST_VIEW_SIDE_BY_SIDE` (+22) |
| View, Window | Synchronous Scrolling | `.uno:ViewSideBySide?Action:string=sync` | `FN_BOOST_VIEW_SIDE_BY_SIDE` (+22) |
| View, Window | Reset Window Position | `.uno:ViewSideBySide?Action:string=reset` | `FN_BOOST_VIEW_SIDE_BY_SIDE` (+22) |
| Help, Help | Feedback | `.uno:HelpFeedback` | `FN_BOOST_HELP_FEEDBACK` (+23) |

## 6. Risks and open questions

Ranked by how much the answer changes what gets built.

**Answers (2026-10-20)**

1. **Accent:** the user chose one accent per app ("Uno por app"). Writer gets Word blue and Calc keeps its
   green. Impress will get PowerPoint orange later. This is the C++ route of design section 3.4, done in W9.
2. **`.uno:ArrowsToolbox` and `.uno:InsertDraw`:** controller ruling, following Calc's precedent (decisions
   19-20): they stay reachable through View > Toolbars, and the menu-bar test lists that path.
3. **Word splits that LibreOffice lacks:** controller ruling: they are built as dropdowns for now, the same
   state as Calc's pending D6 (split arrows). Real split bodies can come later, one mirror slot each.
4. **Approximate mappings:** controller ruling: kept, and each one is listed in decision 20. A mapping
   becomes a placeholder only if a UITest shows it does not do the Word job.
5. **Undo on Home:** controller ruling: kept on Home, for Calc parity (calc-home-redesign); it also stays in
   the quick access bar.

**Risks (no decision needed)**

- **Hidden disabled entries** (decision 28): the Wrap Text, Position, Bring Forward, Send Backward, Align, Group and
  Rotate menus have no visible items while the cursor is in text, until T10 is decided. Calc has the same effect.
- **Home at 1920 px**: Home has 40 controls and Word's Home is the tightest tab (research, "1920 px fit"); the
  Styles gallery is the part that flexes. W2b measures it.
- **Module scope of the new dropdowns**: their Controller.xcu nodes are for `com.sun.star.text.TextDocument`. Master
  documents and Writer/Web use other module names, so their dropdowns would open empty if those apps load the
  office `.ui` (inferred; W2a checks which module names load it).
- **New tabs in every context**: a page without classes shows in every context (section 1); the UITests check the
  new tabs in the table, image and print-preview contexts.
- **Spin fields without labels**: four Layout commands have no label node; the label shows in the tooltip and in
  gla11y output, so W4a adds them.

# Microsoft 365 vs LibreOffice: feature gaps

Date: 2026-10-13. Baseline: our tree `/mnt/games/libreoffice/core` = LibreOfficeDev 27.2 alpha
(current master). Latest stable LibreOffice is 26.8.1 (released 26 Aug 2026).

## How this was built, and how far to trust it

- Five read-only researchers: Excel/Calc, Word/Writer, PowerPoint/Impress, suite-wide, and one
  web pass for 2025-2026 news on both sides. The controller spot-checked claims in the tree and
  corrected two wrong ones (see "Corrections").
- **LibreOffice status** was checked in our source tree with targeted searches (tag **V**).
  A "missing" from a search means "not found where we looked", not a proof.
- **Microsoft 365 side** comes mostly from the researchers' knowledge (tag **D**), plus a web
  pass on techcommunity.microsoft.com and support.microsoft.com for 2025-2026 items (URLs
  below). **U** = unverified.
- The TDF wiki (release notes, "Feature Comparison" pages) blocked automated access, so
  LibreOffice release details come from libreoffice.org and press coverage.
- **Size** to implement, rough: S = days, M = weeks, L = months, XL = multi-quarter.

Status: **missing** / **partial** (exists but clearly behind) / **exists**.

## Most impactful gaps (summary)

1. **AI assistant layer, in every app** (Copilot: draft, rewrite, summarize, analyze, agent
   mode, `=COPILOT()`). Nothing in the tree. XL. Can be built provider-agnostic (OpenAI-compatible
   endpoints, Anthropic, local models) on top of UNO.
2. **Real-time co-authoring, cloud AutoSave and version history.** Desktop has none; the
   multi-view base exists (LibreOfficeKit, used by Collabora Online). XL.
3. **Calc data stack**: Power Query-level ETL, Data Model / Relationships / DAX, slicers and
   timelines, linked data types. XL/L. These match our Data tab placeholders.
4. **Visual authoring parity**: SmartArt authoring (import-only today), PowerPoint Morph and
   Zoom, 3D models, record slide show and export to video. L/XL each.
5. **Reading and language tools**: Read Aloud, Immersive Reader / Line Focus, dictation,
   built-in translation. M/L, and very visible.
6. **Whole apps with no counterpart**: Outlook-style mail and calendar, OneNote. XL each.

Cheap wins (S/M): GROUPBY / PIVOTBY / PERCENTOF, TRIMRANGE, the three REGEX* functions,
checkboxes in cells, eyedropper, Animation Painter UI, comment resolve and @mentions in
Impress, accessibility checker in Calc and Impress, Read Aloud via the platform TTS.

## Suite-wide

| Capability | Microsoft 365 | LibreOffice (this tree) | Evidence | Size |
|---|---|---|---|---|
| **AI** | | | | |
| Copilot in apps, Copilot Chat, agents, model choice | In all apps; Agent Mode GA on Windows Jan 2026; OpenAI and Anthropic models selectable | missing (V): no LLM code; only dictionary words match | `rg -w -i "openai\|chatgpt\|ollama\|copilot"` | XL |
| **Collaboration and cloud** | | | | |
| Real-time co-authoring | All apps, presence, cursors | missing on desktop; Collabora Online does it over LibreOfficeKit (D) | `include/LibreOfficeKit/LibreOfficeKit.h:318-351` (V) | XL |
| AutoSave to cloud | Continuous save to OneDrive/SharePoint | partial: periodic recovery save only (V) | `officecfg/.../Recovery.xcs:111-133` | M |
| OneDrive / SharePoint / Google Drive | Native picker, recent, share | partial: CMIS and WebDAV remote files; OneDrive/SharePoint server entries; Google Drive needs build-time keys (V) | `ucb/source/ucp/cmis`, `Common.xcu:440-451`, `configure.ac:3195` | L |
| Share links, permissions, @mentions | In-app Share | missing (U) | | L |
| Version history | Cloud versions, restore, compare | partial: local File > Versions (V) | `sfx2/source/dialog/versdlg.cxx` | M |
| Loop components | Live blocks across apps | missing (U) | | XL |
| **Platforms** | | | | |
| Web apps | Word/Excel/PowerPoint on the web | partial: Collabora Online, outside this tree (D) | | XL |
| Android / iOS | Full editing | partial: Collabora-based apps; no TDF editor (D) | `vcl/ios/` (V) | XL |
| **UI and experience** | | | | |
| Simplified (one-row) ribbon | Toggle | partial: Tabbed notebookbar variants (V) | `sfx2/source/notebookbar/` | M |
| Stock images, icons, videos, stickers | Licensed in-app library | missing: local Gallery only (V) | `extras/source/gallery/` | L (licensing) |
| Online template catalog | Searchable | partial: local templates only (V) | `extras/source/templates/` | M |
| Designer / Design Ideas | AI layout suggestions | missing (U) | | L |
| **Accessibility and language** | | | | |
| Accessibility checker in every app | Word, Excel, PowerPoint | partial: Writer (incl. live check) and sfx2 framework (V); extend to Calc/Impress | `sw/inc/OnlineAccessibilityCheck.hxx` | S-M |
| Read Aloud, Immersive Reader, Dictate | Built in | missing (V for TTS search; U for dictation) | | M-L |
| Translator | Built in | missing in this tree: no DeepL code found (V), although the online help still documents an experimental DeepL "Translate" | help.libreoffice.org `swriter/01/translate.html` | M |
| **Security and compliance** | | | | |
| Sensitivity labels / IRM / DLP (Purview) | Integrated | partial: TSCP/BAF classification exists, no Purview (V) | `include/sfx2/classificationhelper.hxx` | L |
| Content credentials (C2PA) | On AI images | missing (V) | | M |
| **Compatibility and extensibility** | | | | |
| OOXML fidelity | Native | partial, ongoing | `oox/` | XL |
| VBA | Full | partial: VBA compatibility layer (V) | `vbahelper/`, `sc/source/ui/vba/` | XL |
| Office Add-ins (Office.js, AppSource) | Cross-platform JS add-ins | missing: UNO extensions only (V) | | XL |
| Office Scripts / Power Automate | Scripting and flows | missing (U) | | L |

## Excel vs Calc

| Feature | Excel 365 | Calc (this tree) | Evidence | Size |
|---|---|---|---|---|
| **Functions** | | | | |
| GROUPBY, PIVOTBY, PERCENTOF | Formula pivots | missing (V) | no names in `formula/inc/core_resource.hrc` | M-L |
| TRIMRANGE and trim-reference operators | Trim blank edges | missing (V) | same | M |
| IMAGE | Image from URL in a cell | missing (V) | same | M |
| REGEXTEST, REGEXEXTRACT, REGEXREPLACE | Three regex functions | partial: one `REGEX` function (V) | `formula/inc/core_resource.hrc:504,1474` | S |
| IMPORTTEXT, IMPORTCSV | New, Insiders Jan 2026 | missing (V by name) | releasebot.io Excel feed | M |
| Arrays in cells: FLATTEN, HAS, HASANY, HASALL | Insiders Sep 2026 | missing (V by name) | techcommunity Excel blog 4549756 | L |
| STOCKHISTORY, TRANSLATE, DETECTLANGUAGE, VALUETOTEXT, FIELDVALUE | Online / data-type functions | missing (V by name) | | M each |
| COPILOT(), PY() | AI and Python in formulas | missing (V) | | XL |
| Spill behaviour | Full dynamic arrays | partial: `ocSpill` (`#`) exists (V) | `include/formula/opcode.hxx:122` | M |
| **Data and analysis** | | | | |
| Power Query (Get & Transform) | Visual ETL; full experience GA on the web Jan 2026 | partial: Data Provider with CSV/HTML/XML/SQL (V) | `sc/source/ui/dataprovider/` | XL |
| Data Model, Relationships, DAX (Power Pivot) | Multi-table model | missing (U) | Data tab placeholders | XL |
| Slicers and timelines | Interactive filters | missing: OOXML fragment only, no UI (V) | `sc/source/filter/oox/` | L |
| Flash Fill / Formula by Example | Pattern fill (FbE Oct 2025) | missing (V) | Data tab placeholder | M |
| Analyze Data / Ideas | AI insights | missing | | XL |
| Forecast Sheet | One-click ETS forecast + chart | partial: Exponential Smoothing and Moving Average dialogs (V) | Data tab placeholder | M |
| Linked data types (Stocks, Geography) | Typed cells | missing (V) | | L-XL |
| Structured references | `Table1[Col]` | partial (U); editable table styles exist (26.8) | `sc/inc/tablestyle.hxx` | M |
| Checkboxes in cells | Insert > Checkbox | unverified | | M |
| **Charts** | | | | |
| Waterfall, funnel, treemap, sunburst, box and whisker, histogram, Pareto | Full editing | partial: chart types registered in chart2 in this tree (V); 26.8 release says import/export only, not drawable or editable | `chart2/source/inc/servicenames_charttypes.hxx`; debugpoint 26.8 | L |
| Filled map charts | Geography | partial: `RegionMapChartType` service (V), completeness unknown | same file | L |
| **Collaboration and automation** | | | | |
| Threaded comments, @mentions | Modern comments | partial (U) | `sc/source/filter/oox/worksheetfragment.cxx` | M |
| Python in Excel, Office Scripts | Cloud Python; TypeScript scripts | missing; local Python-UNO macros exist | | XL / L |

## Word vs Writer

| Feature | Word 365 | Writer (this tree) | Evidence | Size |
|---|---|---|---|---|
| **Writing assistance and AI** | | | | |
| Copilot (draft, rewrite, summarize, co-create) | All platforms, iPad Jul 2026 | missing (V) | | XL |
| Editor: grammar, style, similarity check | Cloud service | partial: grammar markup and proofreader API, quality depends on LanguageTool (V); no similarity check | `sw/source/core/text/SwGrammarMarkUp.cxx` | L / XL |
| Rewrite, text predictions | Built in | missing (U) | | L |
| Translate | Built in | missing in this tree (V) | see suite-wide | M |
| Dictate / Transcribe, Read Aloud | Built in | missing (V for TTS) | | L / M |
| Researcher, Smart Lookup | Web research | missing (U) | | L |
| **Review and collaboration** | | | | |
| Comment tasks and @mentions | Assign, notify | partial: threading, resolve and parent ID exist (V) | `sw/inc/docufld.hxx:505-552` | M |
| Combine documents | Separate from Compare | partial: Compare exists (V); Combine unclear (U) | `sw/source/uibase/shells/textsh1.cxx` | S-M |
| Link to a location (cloud deep link) | Aug 2026 | partial: bookmarks/headings links exist locally (D) | techcommunity 4541663 | S-M |
| **Layout and graphics** | | | | |
| SmartArt create and edit | Authoring | partial: OOXML import and render only (V) | `oox/source/drawingml/diagram/` | XL |
| 3D models, stock content, Designer | Online services | missing (V/U) | | L |
| Content controls: Repeating Section, Group, Building Block gallery | Full SDT set | partial: 7 types (V) | `sw/inc/formatcontentcontrol.hxx:42-50` | M-L |
| Ink drawing, ink equations | Pen input | missing (U) | | L |
| Edit PDF by reflow | PDF to editable flow | partial: PDF opens in Draw (D) | | XL |
| **References** | | | | |
| In-line math zone, UnicodeMath / LaTeX linear input | Typed math converts live | partial: Math is an OLE object (V) | `starmath/` | L |
| Citation styles and online source search | Style gallery | partial: bibliography DB and fields (V) | `sw/source/uibase/config/dbconfig.cxx` | M-L |
| **Reading** | | | | |
| Immersive Reader, Line Focus | Learning tools | missing (V) | | M |
| Dark document canvas | Toggle | partial: dark UI and app colours exist (V) | `officecfg/.../UI.xcs` | S-M |
| Online templates | Catalog | partial: local only | | M |

## PowerPoint vs Impress

| Feature | PowerPoint 365 | Impress (this tree) | Evidence | Size |
|---|---|---|---|---|
| **Design and AI** | | | | |
| Copilot (create deck, rewrite, notes) | All platforms | missing (V) | | L-XL |
| Designer / Design Ideas | Layout suggestions | missing (V) | | L |
| Alt text auto-generation | AI alt text | missing; checker flags missing alt text (V) | `sfx2/source/accessibility/AccessibilityCheck.cxx` | M |
| SmartArt insert, edit, convert from text | New SmartArt in "PowerPoint Craft" (Jul 2026) | partial: import and render only (V) | `oox/source/drawingml/diagram/` | XL |
| 3D models (glTF) and 3D animation | Insert and animate | missing: legacy 3D scenes only (V) | `sd/source/ui/func/fucon3d.cxx` | L |
| Eyedropper | Pick any colour | missing: only the Color Replacer pipette (V) | `sd/sdi/_drvwsh.sdi:449` | S-M |
| Ink to shape / text | Recognition | missing (U) | | L |
| **Animation and transitions** | | | | |
| Morph transition (+ `p159:morph` OOXML round-trip) | Auto-animate between slides | missing: `.uno:Morphing` is an unrelated Draw blend (V) | `sd/source/ui/func/fumorph.cxx` | L |
| Zoom (summary, section, slide) | Clickable zoom thumbnails | missing (V) | | M-L |
| Transition catalogue | About 48, 3D variants | partial: about 60, different set (V) | `sd/xml/transitions-ogl.xml` | M |
| Animation Painter | Copy animation | partial: backend only, no UI found (U) | `sd/source/core/sdpage_animations.cxx` | S-M |
| **Media and recording** | | | | |
| Record slide show (narration, ink, laser) | Built in | missing: rehearse timings only (V) | `sd/source/ui/slideshow/slideshowimpl.cxx` | L |
| Export to MP4 / animated GIF | Built in | missing (V) | | L |
| Screen recording, Cameo | Built in | missing (V) | | L |
| Audio/video trim, fade, bookmarks | Built in | partial: playback only (V) | `avmedia/` | M |
| **Presenting and collaboration** | | | | |
| Speaker Coach, live captions, Live Presentations | AI and remote audience | missing (V/U) | | L-XL |
| Comments: resolve and @mentions | Modern comments | partial: replies only (V) | `sd/source/ui/annotations/annotationmanager.cxx:343,595` | M |
| Charts linked to a workbook | Live link | partial (U) | | M |

## Apps with no LibreOffice counterpart

| Microsoft 365 app | LibreOffice | Size |
|---|---|---|
| Outlook (mail, calendar, contacts, tasks) | missing (V: no such module) | XL |
| OneNote | missing | XL |
| Teams | missing (out of scope for a suite) | XL |
| Access | partial: Base (forms, queries, reports; HSQLDB, Firebird, MariaDB/MySQL drivers built; PostgreSQL driver in source, not enabled in our build) | L |
| Publisher (retiring Oct 2026) | partial: Draw + libmspub import (D) | M |
| Visio | partial: Draw + libvisio import; no smart stencils (D) | L |
| Project, Planner, Forms, Lists, Clipchamp | missing | L-XL |

## Already present in this tree (do not build)

- **Calc**: the LAMBDA family (LET, LAMBDA, MAP, REDUCE, SCAN, BYROW, BYCOL, MAKEARRAY),
  FILTER, SORT, SORTBY, UNIQUE, XLOOKUP, XMATCH, RANDARRAY, SEQUENCE, array shaping (VSTACK,
  HSTACK, TAKE, DROP, CHOOSECOLS/ROWS, WRAPROWS/COLS, TOCOL/TOROW, EXPAND, TEXTSPLIT,
  TEXTBEFORE/AFTER; shipped in 25.8), sparklines, icon sets and colour scales, Solver with
  sensitivity report, Handle Duplicate Records, pivot Calculated Fields (26.8), statistics
  dialogs (V).
- **Writer**: 7 content-control types, threaded comments with resolve, accessibility checker
  (also live), track-changes lock, mail merge, Navigator, grammar plumbing, watermark,
  Draft view (`FN_DRAFT_VIEW`, 26.8), Paragraph Composer (26.8), Markdown import/export (V).
- **Impress**: shape Combine/Merge/Intersect, slide sections (26.8,
  `sd/inc/SlideSectionManager.hxx`), rehearse timings, embedded fonts (PPTX since 25.8),
  trigger animations, comment replies, presenter console, OpenGL transitions (V).
- **Suite**: command search popup (`sfx2/inc/commandpopup/`), light/dark/system appearance
  (25.2), digital signatures (NSS, mscrypt, GPG), document classification, CMIS/WebDAV
  remote files, PDF 2.0 export (25.8), OpenType variable fonts and editable table styles
  (26.8), Python macros from the Macro manager (26.8).

## Corrections made while compiling

- The Excel researcher listed SEQUENCE as missing: it exists as `ocMatSequence`
  (`formula/inc/core_resource.hrc:1317`).
- The Word researcher listed Draft view as missing: it exists (`sw/sdi/swriter.sdi:5298`,
  `FN_DRAFT_VIEW`).
- Chart types: the tree registers the modern Office chart types, while the 26.8 release
  notes say they are import/export only. Their editing state on master is unverified.

## How this maps to our work

The Data tab placeholders are exactly some of these gaps: From Database (Base/SDBC; enable the
PostgreSQL driver first), Recent Sources, Connections, Properties, Reapply, Flash Fill,
Relationships, Manage Data Model, Forecast Sheet.

## Recent Microsoft 365 items (2025-2026) found on the web

- Excel: arrays/lists in cells with FLATTEN, HAS, HASANY, HASALL (Insiders, Sep 2026);
  IMPORTTEXT/IMPORTCSV and Power Query GA on the web (Jan 2026); `=COPILOT()` (2025, web search
  May 2026); Agent Mode (GA Windows Jan 2026); Formula by Example (Oct 2025); PivotTable
  auto-refresh (Jul 2025); Center Across Selection in the Merge menu (Insiders, Sep 2026).
- Word: Copilot co-create on iPad (Jul 2026), link to a location (Aug 2026), text predictions
  off by default (Sep 2026).
- PowerPoint: "PowerPoint Craft" with new SmartArt and themes (Jul 2026), accessible SmartArt
  descriptions (Aug 2026), Copilot co-create on iPad (Aug 2026).

## Open verification items

- Microsoft side of most rows (from knowledge, not fetched): recheck before committing to a
  roadmap item.
- Calc: checkboxes in cells, structured references, PivotChart interactivity, threaded
  comments in Calc.
- Writer: Combine documents, Table of Authorities, dark document canvas.
- Impress: Animation Painter UI, chart linking.
- TDF Feature Comparison wiki: not retrieved (blocked); worth reading in a browser.

## Sources

- https://techcommunity.microsoft.com/category/microsoft365/blog/excelblog
- https://techcommunity.microsoft.com/blog/excelblog/excel-now-supports-multiple-values-in-a-single-cell/4549756
- https://techcommunity.microsoft.com/blog/microsoft365insiderblog/new-regular-expression-regex-functions-in-excel/4226334
- https://support.microsoft.com/en-us/excel/functions/trimrange-function
- https://support.microsoft.com/en-us/office/using-checkboxes-in-excel-da85546d-c110-49b8-b633-9cebadcaf8d4
- https://techcommunity.microsoft.com/blog/microsoft365insiderblog/link-to-a-location-in-word-for-windows-and-mac/4541663
- https://techcommunity.microsoft.com/category/microsoft365/blog/microsoft_365blog/whats-new-in-powerpoint-craft/4535409
- https://techcommunity.microsoft.com/blog/microsoft365insiderblog/smartart-is-becoming-more-accessible-in-powerpoint/4507653
- https://releasebot.io/updates/microsoft/excel (secondary summary of the Excel blog)
- https://www.libreoffice.org/discover/new-features/
- https://www.debugpoint.com/libreoffice-26-8-features/
- https://itsfoss.com/news/libreoffice-25-8-release/
- https://itsfoss.com/news/libreoffice-26-2-release/
- https://help.libreoffice.org/latest/sv/text/swriter/01/translate.html

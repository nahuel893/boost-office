# Feature: Calc remaining ribbon tabs like Excel (Tabbed Office)

- **Locator:** `product/odd/tasks/calc-ribbon-tabs.md`
- **Engram mirror:** `odd/calc-ribbon-tabs/tasks`
- **Repo / branch:** `/mnt/games/libreoffice/core`, `feature/calc-ribbon-tabs` (from 01ab49af1, the tip of `feature/calc-data-redesign`)
- **SDD workspace:** `/mnt/games/libreoffice/core/.superpowers/sdd/2026-10-15-calc-ribbon-tabs/` (briefs, reports, ledger; never committed)

## Objective

Make every remaining tab of the Tabbed Office Calc ribbon look exactly like Excel's: same tabs, same order, same groups and buttons in the same places. Buttons whose feature LibreOffice lacks are greyed placeholders, as on the Data tab. Implementing those features comes later.

## Problem and why

The user's words (2026-10-15): "te dejo de tarea dejar exactamente igual el resto de pestañas, busca en internet imagenes de referencia. Luego programamos las features faltantes".

Home and Data are done. The other tabs (Insert, Layout, Functions, Review, View, the contextual tabs) are still LibreOffice's upstream pages.

## Rulings (made while the user is away; each can be overturned)

- **Reference:** Excel for Microsoft 365, Windows desktop, at full width (1920 px). The product goal is "Office 365". The Data tab was built from the user's Excel 2016 screenshot; R1 records how the 365 Data tab differs, and changing Data is a separate decision for the user.
- **Tab set and order:** File, Home, Insert, Page Layout, Formulas, Data, Review, View, Help. LibreOffice's Functions tab becomes Formulas, placed before Data. Layout becomes Page Layout.
- **Contextual tabs** (Picture Format, Shape Format, Developer, and the others), Excel's Draw (inking) and Automate tabs, and the File backstage are later slices, not this one.
- **Screenshots** of Microsoft's UI are references only. They are kept outside the repo, in `/mnt/games/libreoffice/assets/excel-ref/`, and never committed.
- **Supersedes** `product/odd/tasks/calc-formulas-tab.md`, which proposed editing the upstream `notebookbar.ui`. The Formulas tab is now built in the Office variant.
- **Placeholders and splits** follow the Data tab recipe (`product/docs/calc-data-redesign.md`). Placeholder slots use the fork-reserved block `SID_NEW_SLOTS+380..+399`, extended as needed and recorded in `sc/inc/sc.hrc`.

## Scope

**In scope:**
- Pages of `sc/uiconfig/scalc/ui/notebookbar_office.ui` generated from `product/ui/calc_<tab>.json`: Insert, Page Layout, Formulas, Review, View, Help.
- Tab order and labels.
- Dropdown and split menus, placeholder commands and slots, icons, tests, docs.

**Out of scope:** implementing placeholder features; contextual tabs; Draw (ink), Automate, File backstage; Writer and Impress; translations.

## Constraints

- Same as Home and Data. Build only through `product/dev/lo-make.sh`. Upstream variants stay untouched; the office `.ui` stays "upstream + generated pages". Commits are Conventional, subject <= 79 chars, no AI attribution. Never commit `.superpowers/`.
- A split or dropdown needs a dedicated command; never put a controller on a command that other toolbars use.
- Every new state-bearing slot is invalidated wherever its original is.
- Never touch the user's Calc (profile `/mnt/games/libreoffice/try-profile`). Kill only your own soffice by PID.

## Acceptance criteria

- Each tab shows Excel's groups and buttons in Excel's order, with placeholders greyed out.
- Tabs appear in Excel's order with Excel's names.
- Unit tests, gla11y/lint and UITests pass. Light and dark screenshots of every tab exist. The user approves them visually.

## TDD

- **Mode:** strict.
- **Runners:**
  - `python3 -I -m unittest discover -s product/tests -t .`
  - `product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.<test>`
  - `product/dev/check-ui.sh sc/uiconfig/scalc/ui/notebookbar_office.ui`
- Layout tests compare each generated page against its design file. Rendering is checked by measured screenshots.

## Delivery

- **Forecast:** large, about 3000+ authored lines (layout JSON, xcu labels and menus, placeholder slots, icon manifest, tests, docs); generated `.ui`/`suppr` excluded.
- **Strategy:** ask-on-risk. No product remote exists yet; publishing (public GitHub fork vs private repo) is waiting for the user's answer.
- **RDD:** on. Pending boundary is f629c100c (the D5 slice is under budget). After each task commit, run `gentle-ai review assess --committed-only`. While the user is away, a due review is recorded as "consent pending" and offered when the user returns.

## Tasks

| ID | Task | Route | Status | Commits | RDD |
|----|------|-------|--------|---------|-----|
| R1 | Reference research: Excel 365 ribbon inventory per tab (groups, buttons, sizes, splits, menus), screenshots outside the repo, report in `product/docs/research/` | delegated (research worker, opus) | [x] 6 main tabs inventoried with screenshots (64 images, outside the repo); 365 Data diff; brief tabs. Parent spot check: Insert matches the 2026 full-width screenshot | ee62c96b2 | passive (docs) |
| L1 | Layout and command map per tab (`product/docs/design/calc-<tab>-tab-layout.txt` + `calc-ribbon-tabs-overview.txt`): LO command per button, placeholders, splits, missing icons | delegated (opus) | [x] 136 controls, 48 placeholders (+3 menu items) on 32 family slots, 29 dropdowns, 1 split, 1 alias, 132 icons; all tabs estimated to fit at 1920 px | see below | passive (docs) |
| T1 | Tab order and labels (Page Layout, Formulas before Data, Help page last) driven by the generator; tooling for URL variants and placeholder families in tests; ALL placeholder slots of the slice (+389..+421) in one sc rebuild | delegated (Sonnet) | [x] 106 unit tests (RED 15), build 0, check-ui 0 new, 15 UITests; task review Approved (minors: doc fixed, UITest RED not observed, tilde to check on screenshot) | 140c825d1, 1e617e331 | high, due: consent pending (user away) |
| T2a / T2b | Insert: a = layout, xcu labels, popups, placeholders' labels, tests, UITests; b = icons, 1920 fit, screenshots | delegated (Sonnet) | a [x] 127 unit tests, build 0, check-ui 0 new, 21 UITests; R3 and R12 proven, R6 popup built (real-window opening left to T2b); task review Approved (minors folded into T2b). b [x] 35 icons, all ten sections at 1920 px (Filters and Sparklines as small-label columns), 1600/1366 measured, R6 submenu opens in a real window, headless `product/dev/shot-tab.sh`; 129 unit tests; review Needs fixes (shot-tab cleanup could kill a Calc it did not start) -> fix round 1 -> re-review all addressed | a: 7093b9168, 497d870ee; b: 682b13cd0, d7ba773f3, 45e2b13f8, 1ad2a7269 | due: consent pending (user away) |
| T3a / T3b | Page Layout (a includes the Print Titles alias slot +16 and the margin-presets spike) | delegated (Sonnet) | a [x] 159 unit tests, build 0, check-ui 0 new, 30 UITests; R4 presets work (Page.TopMargin/BottomMargin; design fixed in 40373694f), R8 enforced, R9 ok; interrupted by a machine reboot and resumed; review Needs fixes (alias enabled in chart/OLE/graphic/media subshells) -> fix round 1 (UITest RED then GREEN) -> re-review all addressed. b [x] 25 icons, all five sections at 1920 px (Arrange folds at 1600/1366), 161 unit tests; review Approved | a: f9d4629c5, a175fcd86, b5df0b800; b: 0ecd4f28e | due: consent pending (user away) |
| T1b | Bugfix: placeholder family variants after the first were drawn enabled. Root cause: `ControllerFactory::CreateToolBoxController` force-enabled items after `update()`, and the bindings only push state to the URL that first bound the slot's dispatch | delegated (opus, systematic debugging) | [x] 2 UITests reading the drawn toolbox state (RED 12/34 items), 161 unit tests, 33 UITests, 8-tab pixel diff: only placeholders changed; Writer notebookbar and sidebars unchanged. Review (opus) Needs fixes: master commands could freeze greyed, regression dumps missing for Writer Compact, Impress groupedbar and read-only -> Edit Document -> fix round 1 (master-command guard; dumps: 0 items differ across pre-T1b / base / fix builds) -> re-review all addressed | 089ea27b7, d9dcad297 | due: consent pending (user away) |
| T1c | Bugfix (pre-existing upstream, raised in T1b): argument-variant URLs of a slot never hear later state changes (`SfxDispatchController_Impl::StateChanged` pushes only to the first-bound URL). Since T1b a variant disabled at build time stays greyed | delegated (opus) | [x] every listener key of the slot's shared dispatch gets the push, labelled with its own URL; 3 UITests RED then GREEN, 36 UITests, 161 unit tests; dumps: only the 7 stale Writer Compact StyleApply variants changed (now match a fresh window). Review (opus) Approved; its own-URL ruling also fixes a misrouting in framework's StyleDispatcher. Parked minors for T8: avoid per-change parse and event copies, check the parseStrict result, replace a fixed sleep in the test helper | 780338626 | due: consent pending (user away) |
| T4a / T4b / T4c | Formulas (a includes the AutoSum split slot +15 with static category menus; c = C++ function-category popup controller replacing the static menus) | delegated (Sonnet) | a [x] 195 unit tests, builds 0, check-ui clean, 49 UITests; AutoSum body mirrors SID_AUTO_SUM (only ScCellShell declares it; nothing invalidates it); R9 failed -> single AutoCalculate toggle (T3c may restore Automatic/Manual); review Approved (minors parked: leftover print in a UITest, text-fragile sdi guards). b [x] 28 icons, 4 glyph substitutes (missing in Fluent 1.1.344), all five sections at 1920 px with no fallback, 198 unit tests, 12 UITests. Review Approved; minors parked for T8: near-identical small icons (tags, e^x pair, Calculate Now/Sheet), dark theme dims disabled icon-only buttons less than light. c [x] FunctionMenuController (sc, svt::PopupMenuControllerBase) serves the eight dropdowns: category lists, More Functions submenus, Recently Used from the LRU, items insert "=NAME(" through `.uno:InsertFunction`, items greyed when InsertFunction is disabled; 205 unit tests, 18 Formulas UITests. Review (opus) Needs fixes: mergelibs release builds would not link because of the svtools export -> fix round 1 (exported unconditionally, plus item greying) -> re-review all addressed. Parked minors for T8: catch a disposed frame in updateFunctionsEnabled; "Function..." stays enabled with a shape selected; translated names for 4 submenus; native-code.py for static builds | a: 2b6e79645, a9b6c4ff2; b: 48da15d7c, 0f83c8230; c: e200d29dc, 4c7834cff | due: consent pending (user away) |
| T3c | Menu items with one boolean argument act as radio items (framework rule: checked = state == argument). Only our Orientation items use it in the whole tree. Restores Excel's Calculation Options if `.uno:AutomaticCalculation` honours its argument | delegated (Sonnet) | [x] MenuBarManager rule (strict single `:bool=true/false` argument and boolean state). Calculation Options restored to Automatic/Manual, which FID_AUTO_CALC honours, with marks verified by screenshot. Orientation stays unmarked: its state is an SvxPageItem; ruling: docsh4.cxx untouched because the sidebar shares that state. 196 unit tests, 22 UITests. Review Approved. Parked minors (T8): anchor the `:bool=` match to the argument name; the framework test is source-text only | b011a55a6, 21575de6f | due: consent pending (user away) |
| T5a / T5b | Review | delegated | [ ] | | |
| T6a / T6b | View (Sheet View group as placeholders, family slot +421) | delegated | [ ] | | |
| T7 | Help | delegated | [ ] | | |
| T8 | Docs (`product/docs/calc-ribbon-tabs.md`), fix the Data doc's menu-bar note, final light/dark screenshots, user gate | delegated | [ ] | | |
| T9 | Excel labels for existing commands (e.g. Header & Footer, WordArt, Object, Equation instead of LibreOffice's labels). Two ways: Calc-only label overrides in CalcCommands.xcu, which also rename the menus; or ribbon-only URL label variants | pending user decision | [ ] | | |

L1 open questions, ruled while the user is away (overturnable):

1. Family slots: accepted. The Calc slot range ends at +424, and one slot per placeholder would need 53 ids.
2. The Help tab goes last, after Tools, matching Excel's "(Developer), Help".
3. View > Sheet View: built as greyed placeholders, family slot +421. It is the first group of Excel's View tab, and it can be implemented without a cloud.
4. Comments and Notes both drive LibreOffice's single comment type.
5. Formulas: the C++ category popup controller is accepted, as T4c, after static menus ship in T4a.
6. Sheet Right-to-Left, Dark Mode and Translate (placeholder) are kept.
7. Icons opens LibreOffice's Gallery. PivotTable is a plain button.

Slots: the functional slots +15 and +16 go in the upstream gap next to Data's +12..+14. Upstream appends new ids at the top and rarely refills old holes. That leaves 3 spare fork ids, +422..+424.

## Progress / evidence

- 2026-10-15: feature created; branch `feature/calc-ribbon-tabs` from 01ab49af1.
- 2026-10-15: R1 done.
  - Omitted:
    - Insert > Tours: absent from the 2026 full-width screenshot.
    - Insert > Add-ins: moved to Home in 2024.
    - Review > Insights: Smart Lookup was retired in 2025.
    - Microsoft-cloud-only items: Insert > Forms, the Automate tab, Review > Changes, Performance.
  - Kept as placeholders when LO lacks them: default conditional controls such as Insert > Checkbox and Formulas > Python.

## Next step

L1 layouts (dispatched), then T1.

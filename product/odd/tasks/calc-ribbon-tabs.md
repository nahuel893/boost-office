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
| R1 | Reference research: Excel 365 ribbon inventory per tab (groups, buttons, sizes, splits, menus), screenshots outside the repo, report in `product/docs/research/` | delegated (research worker) | [ ] | | |
| L1 | Layout and command map per tab (`product/docs/design/calc-<tab>-tab-layout.txt`): LO command per button, placeholders, splits, missing icons | delegated | [ ] | | |
| T1 | Tab order and names: Page Layout, Formulas before Data, Help tab added | delegated | [ ] | | |
| T2 | Insert tab | delegated | [ ] | | |
| T3 | Page Layout tab | delegated | [ ] | | |
| T4 | Formulas tab | delegated | [ ] | | |
| T5 | Review tab | delegated | [ ] | | |
| T6 | View tab | delegated | [ ] | | |
| T7 | Help tab | delegated | [ ] | | |
| T8 | Docs (`product/docs/calc-ribbon-tabs.md`), width fit at 1920 px, light/dark screenshots, user gate | delegated | [ ] | | |

Each tab task includes its placeholders, menus, icons and tests. A tab task can be split if it grows.

## Progress / evidence

- 2026-10-15: feature created; branch `feature/calc-ribbon-tabs` from 01ab49af1.

## Next step

R1 research, then L1 layouts.

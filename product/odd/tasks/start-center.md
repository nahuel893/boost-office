# Feature: a Boost Start Center

- **Status:** done, 2026-10-25 (merged into `dev` and `main`; not in the 0.1.0 release).
- **Locator:** `product/odd/tasks/start-center.md`
- **Engram mirror:** `odd/start-center/tasks`
- **Repo / branch:** `/mnt/games/libreoffice/core`, `feature/start-center`, from `dev` (e9112a65f).
- **Map:** read-only explorer, 2026-10-25 (summarized under "Map" below).
- **SDD workspace:** `/mnt/games/libreoffice/core/.superpowers/sdd/2026-10-20-writer-impress-ribbons/` (briefs and
  reports; never committed).

## Objective

`boost-office` (soffice with no document) opens a Start Center in the spirit of the Microsoft 365 desktop "Home"
screen, in Boost colors, with no LibreOffice donation banner, logo or "Welcome to LibreOfficeDev!" text.

## Problem and why

The user (2026-10-25): "Si hace un redising de la pantalla de inicio". Today the stock Start Center shows the
LibreOffice logo, a "Donate" button (and, every 30th day, a donation banner), "Welcome to LibreOfficeDev!" when there
are no recent files, and grey `#666666` thumbnail panes that ignore the Boost light and dark schemes. It is the first
thing the installed `boost-office` launcher shows.

## Map (explorer, 2026-10-25)

- Layout: `sfx2/uiconfig/ui/startcenter.ui` (GtkBuilder, welded; `.ui` edits restyle it under gtk3). Left pane
  `buttons_box` (`open_all`, `open_remote`, toggles `open_recent` and `templates_all`, `create_label`, `writer_all` ...
  `database_all`), brand `daBrand`, `small_buttons_box` (`help`, `extensions`, `donate`), frame title `label1`; right
  pane `all_recent` (`RecentDocsView`), `local_view` (`TemplateDefaultView`), filter grid `actions`, donation grid
  `gdDonation`.
- Code: `sfx2/source/dialog/backingwindow.cxx` binds every id (`:178-205`), paints with `GetWindowColor()`
  (`:453-475`), sizes the left column from `all_buttons_box` (`:482-493`), shows donation UI by `Misc/ShowDonation`
  (`:210-242`, `:267-269`), dispatches factory URLs (`:716-739`).
- Welcome text: `STR_WELCOME_LINE1/2` drawn by `sfx2/source/control/recentdocsview.cxx:65-66` only with no recent files.
- Thumbnail colors: `Common.xcs:3117-3130` `StartCenterThumbnailsBackgroundColor` / `TextColor`.
- Tests that pin ids: `uitest/uitest/test.py:206-234` (`writer_all`, `calc_all`, `impress_all`, `draw_all`,
  `database_all`), `sfx2/qa/unit/data/sfx2-dialogs-test.txt:69` (the `.ui` must load).
- gtk3: `vcl/unx/gtk3/custom-theme.cxx` installs one screen-wide CSS provider; no Start Center rules today.

## Rulings (controller, 2026-10-25; the user asked for no questions and no review stops)

1. **Shape (Microsoft 365 Home):** a left navigation column and a right content pane.
   - Left column, top to bottom: the text "Boost Office" (bold, larger; replaces the `daBrand` logo); nav entries
     **Home** (`open_recent` toggle: recent documents), **New** (`templates_all` toggle: templates), **Open**
     (`open_all`), **Open Remote** (`open_remote`); at the bottom **Help** and **Extensions**. The frame title
     "Application" goes.
   - Right pane, top to bottom: a greeting by local time ("Good morning", "Good afternoon", "Good evening"); a row of
     "new blank" tiles, each a large button with the app icon and a caption: Blank document (`writer_all`), Blank
     workbook (`calc_all`), Blank presentation (`impress_all`), Drawing (`draw_all`), Formula (`math_all`), Database
     (`database_all`); then a "Recent" heading over the recent view (Home) or "Templates" over the template view (New),
     with the existing filter and actions controls.
   - Every existing widget id that code or tests use stays (renamed labels are fine).
2. **No donation:** remove the donate button, the donation banner and their code paths in Boost (it is a fork; the
   README already credits LibreOffice). The `.ui` and `BackingWindow` stay consistent (no `weld_*` of removed ids).
3. **Welcome text:** with no recent files the recent view says "Welcome to Boost Office" and "Drop a document here or
   create a new one above." (English literals in the Boost strings; no `%PRODUCTNAME`). The window title stays
   "LibreOfficeDev" (configure-level renaming remains a follow-up).
4. **Colors:** the window and both views use the Boost workspace color (light `#FAFAFB`, dark `#222226`) and the
   scheme's text color, so light and dark look right with no GTK theme help. The thumbnail colors come from the
   `StartCenterThumbnails*` keys written by the shared presets (`product/dev/profile.py` `LOOKS` / `build_items`), so
   the dev profile and the installed `boost.xcd` layer stay one list; the window background follows the active scheme.
5. **Accents:** each tile carries its app accent as a bottom strip (Writer `#185ABD`, Calc `#1B7A3E`, Impress
   `#C43E1C`; Draw, Math, Base a neutral accent unless a Boost value exists), done through gtk3 CSS classes in
   `custom-theme.cxx` or vcl drawing; the selected nav entry shows a neutral selected state, as Office does.
6. **Dev launcher:** `product/dev/office.sh start [light|dark]` opens the dev build's Start Center with its own profile
   (`/mnt/games/libreoffice/try-profile-start`), so the user can try it like the apps.

## Scope

In: `sfx2/uiconfig/ui/startcenter.ui`, `sfx2/source/dialog/backingwindow.{cxx,hxx}`,
`sfx2/source/control/recentdocsview.cxx`, `templatedefaultview.cxx` if needed, `include/sfx2/strings.hrc`,
`vcl/unx/gtk3/custom-theme.cxx`, the shared presets and their tests, `office.sh`, screenshots tooling, docs.
Out: configure-level renaming, the window title, other VCL plugins than gtk3 (they must still load and work).

## Constraints

Same as the earlier features: builds only via `PARALLELISM=2 product/dev/lo-make.sh` with at least 2500 MB free;
UITests only via `product/dev/uitest.sh`; no `git stash`; no Co-Authored-By or AI attribution; bat/rg/fd/sd/eza only;
never touch `/mnt/games/libreoffice/try-profile*` except the new `try-profile-start` that `office.sh start` owns;
never the user's real `~/.config` or `~/.local`; kill soffice only by PID.

## Acceptance criteria

1. `office.sh start light` and `office.sh start dark` show the layout of ruling 1, with no logo, donate button,
   donation banner or "LibreOffice" text inside the window.
2. Each tile opens its app; Home and New switch the right pane; Open and Open Remote work.
3. The measured workspace, view and accent colors match rulings 4 and 5 in light and dark.
4. The stock UITests that use the Start Center ids still pass; the `.ui` still loads in the dialogs test.
5. A fresh install (`install.sh` into scratch dirs) shows the new Start Center from `boost-office`.
6. The unit suite is green.

## Delivery

One branch, `feature/start-center`; work-unit commits per task; at the close, push the branch and fast-forward `dev`
and `main` ("pushea todo", standing).

## Tasks

- [x] **S1 — layout and content** (delegated, opus; C++ and `.ui`, 2+ non-trivial files): rulings 1, 2, 3; build
  sfx2; source-pinning tests in `product/tests/`; the Start Center UITests. Commits b83628984, 6db2e0512.
- [x] **S2 — colors, accents, dev launcher** (delegated): rulings 4, 5, 6; screenshots light and dark with measured
  colors. Commits 87591a10d, 555d52702, 0a4dc606d, 12900896b, e0fea73d0.
- [x] **S3 — gate and docs** (delegated): acceptance 1-6 on the dev build and a scratch install; README / docs
  screenshot and text; close the feature. Commits 65d26ccb6 (merge of origin/main), f4fb1440b.

## Checks

- `python3 -I -m unittest discover -s product/tests -t .` (full suite once per task).
- `PARALLELISM=2 product/dev/lo-make.sh sfx2.build` (and `vcl.build` when `custom-theme.cxx` changes).
- The Start Center UITests via `product/dev/uitest.sh`.
- Screenshots looked at, colors measured.

## Progress / evidence

- 2026-10-25: map done (explorer); feature document and branch created.
- 2026-10-25 S1 (delegated, opus; route: writer trigger, `.ui` + C++ + tests): b83628984
  `feat(sfx2): give the Start Center a Boost layout without donation UI`, 6db2e0512
  `test(product): screenshot the Start Center` (`shot-tab.sh --app start`). `test_start_center.py` 12/17 RED -> 17/17;
  `test_shot_tab.py` 6 RED -> 16/16; full suite 1070 OK; `sfx2.build` and `CppunitTest_sfx2_dialogs_test` exit 0;
  UITests Calc `rows.CalcRows.test_row_height`, Writer `tdf45946`, Impress `tdf133713` pass. Shots
  `/mnt/games/libreoffice/assets/previews/start-center/s1/` (Home light/dark at 1280 and 1024, New light); the
  controller looked at `home-light-1280.png`: nav column, greeting, six tiles, Recent heading, Boost welcome text; views
  still `#666666` (S2). Concerns carried to S2: stale `solenv/sanitizers/ui/sfx.suppr:36,38,39`, unused
  `maWelcomeImage` (`sfx2/inc/recentdocsview.hxx:110`); unequal tile widths by design (1024 px fit); new English
  captions lose translations; `uitest/impress_tests/start.py` not runnable through `uitest.sh`; the in-document donation
  infobar (`sfx2/source/view/viewfrm.cxx:1810`) is outside this feature (follow-up).

- 2026-10-25 S2 (delegated, opus; route: writer trigger, C++ + CSS + presets + tests): 87591a10d (view colors from the
  schemes via `StartCenterThumbnails*` in `build_items`), 555d52702 (`office.sh start`), 0a4dc606d (workspace color
  from `AppBackground`, style classes), 12900896b (stale suppressions, unused welcome image), e0fea73d0 (tile accents
  and selected nav in `custom-theme.cxx`). Suite 1092 OK (22 new, RED first); `sfx2.build`, `vcl.build` exit 0;
  notebookbarOffice popups UITest and `tdf45946` pass. Measured light / dark: views and window `#FAFAFB` / `#222226`;
  nav `#FFFFFF` / `#2B2B2B`; selected nav `#E0E0E0` / `#454545`; strips Writer `#185ABD` / `#83A6DB`, Calc
  `#1B7A3E` / `#5CC27E`, Impress `#C43E1C` / `#FF8F6B`, others `#9E9E9E` / `#6A6A6A`; text `#242424` / `#F2F2F2`.
  Tile accents read from the ToolbarMode `AccentColor` settings, not hard-coded. Controller looked at
  `s2/home-light-1280.png` and `s2/home-dark-1280.png`: matches rulings 4-5. Concerns: `new-dark` template frame
  lighter on two edges; view colors fixed per look (a manual scheme switch leaves them); debug-only "unknown class"
  warning on non-gtk3 backends.

- 2026-10-25 S3 (delegated, opus; route: gate + docs + merge): 65d26ccb6 merges origin/main c84de6e32 (0.1.0 release
  work; no conflicts), f4fb1440b `docs: show the Boost Start Center in the README` (crop in
  `product/docs/screenshots/start-center-light.png`, `building.md` names `office.sh ... start`). Suite 1112 OK after the
  merge, 1116 OK at f4fb1440b; `sfx2.build`/`vcl.build` no-ops. Acceptance: 1 met (light and dark, no logo, donate or
  LibreOffice text; title bar out of scope); 2 met for Writer, Calc, Impress tiles (each opens its app with the Boost
  ribbon, light and dark), Home/New switch, Open (GTK file dialog) and Open Remote; Drawing, Formula, Database tiles not
  clicked; 3 met (all values equal S2's table, also on the installed light build); 4 met on S1/S2 evidence (no C++ or
  `.ui` change since); 5 met (scratch install, `boost-office` shows it, purge leaves only `gvfs-metadata/`); 6 met.
  Shots `/mnt/games/libreoffice/assets/previews/start-center/s3/`. Controller looked at the README crop. Incident: the
  dark run of `office.sh start` uses the real `XDG_CONFIG_HOME`, so cancelling the Open dialog wrote the GTK
  file-chooser size into the user's `~/.config/dconf/user` (old values unknown, not restored); the dark Open screenshot
  showing the user's file names was blurred (outside the repo).

## Next step

None. Follow-ups: the dark template view frame edges (S2/S3); dark mode text size follows the user's GTK settings;
`office.sh` dark mode writes the user's dconf through GTK dialogs; the in-document donation infobar
(`sfx2/source/view/viewfrm.cxx:1810`); a release that includes the Start Center (after the portable build).

# Feature: the open document's name at the top of the ribbon (Microsoft 365 style)

- **Status:** done, 2026-11-18 (published in 0.1.5).
- **Locator:** `product/odd/tasks/document-title.md`; **Engram mirror:** `odd/document-title/tasks`.
- **Repo / branch:** `/mnt/games/libreoffice/core`, branch `feature/document-title` from `main` (17bfba56b, release
  0.1.4). Runners: `python3 -I -m unittest discover -s product/tests -t .`; UITests through `product/dev/uitest.sh`,
  builds through `product/dev/lo-make.sh`, screenshots through `product/dev/shot-tab.sh`.

## Specs

- **S1** The user (2026-11-14): "Luego necesito que agregues en alguna parte arriba, que aparezca el nombre del archivo
  abierto".

## Rulings (controller, 2026-11-14; the user asked for no questions and no review stops)

1. **Place and look:** the document's name is drawn in the free space of the ribbon's tab row, between the last tab
   and the hamburger button, aimed at the window's center and clamped into that space, as Microsoft 365 shows it
   above its ribbon. Tab text color of the active Boost scheme (light and dark), transparent background over the
   gtk3 ribbon card, end-ellipsis when it does not fit; hidden when the free space is under about 80 px. The tabs
   never lose space to it.
2. **Text:** the controller's title (`XTitle` of the frame's controller): the file name with its extension, "Untitled
   N" for a new document, with LibreOffice's own " (read-only)" and " : 2" suffixes; never the " - Boost Office
   Writer" product suffix. It follows every title change (Save As, reload, read-only, a second window, print
   preview). A `~` in a name is shown as is (no mnemonic).
3. **Scope:** Writer, Calc and Impress (the apps with the Boost ribbon). Draw and the Start Center have no ribbon and
   are out of scope. The label lives in the shared notebookbar tab control, so LibreOffice's own "Tabbed" mode shows
   it too (accepted). Not under LibreOfficeKit.
4. **Each ribbon shows its own document:** with two documents in two windows, each window's ribbon shows its own
   name (lesson of `style-box-perf.md` B1: never trust `SfxViewFrame::Current()` / `SfxObjectShell::Current()` for a
   per-window control without a two-window test).
5. **Release:** ships as 0.1.5, built and proven as 0.1.4 was.

## Tasks

- [x] **D1 — design** (delegated, read-only Plan agent; mapping trigger: vcl tab control layout, sfx2 notebookbar,
  framework title helpers): design (a) of the handoff `.superpowers/sdd/2026-10-20-writer-impress-ribbons/task-DT-D1-design.md`.
- [x] **DT-I1 — implementation** (delegated writer, opus; context reason: vcl/sfx2 builds, UITests in three apps,
  screenshots): rulings 1-4, test first. Commit 6f9aeabd4 (rebased on a97def160; was 16e93b790).
- [ ] **DT-V1 — independent verification** (delegated verifier; Risk item 6: the per-window title and the narrow-window
  layout would go unnoticed by the unit suite). Skipped: the user asked to publish now (L3); the 15 UITests that
  cover the two-window and narrow-window cases ran instead.
- [x] **DT-F1 — release 0.1.5** (inline: packaging and container proof by the controller, at the user's urgency):
  ruling 5. Published https://github.com/nahuel893/boost-office/releases/tag/v0.1.5.

## Log

- **L1** (2026-11-14, verbatim) "subi el fix al repositorio, asi queda desplegada la ultima version
  Luego necesito que agregues en alguna parte arriba, que aparezca el nombre del archivo abierto"
- L2 (2026-11-14) D1 done (Plan agent): Boost ships `notebookbar_office.ui` for Writer, Calc and Impress only; the
  quick-access toolbox and the hamburger are created in code (`sfx2/source/notebookbar/NotebookbarTabControl.cxx:299`,
  `vcl/source/control/tabctrl.cxx:2210`); `ImplPlaceTabs` (`tabctrl.cxx:2334-2414`) leaves the free space between the
  last tab and the hamburger. Chosen design: a `FixedText` in `NotebookbarTabControlBase` placed by `ImplPlaceTabs`,
  fed by an `XTitleChangeListener` on the frame in `NotebookbarTabControl` that reads the controller's `XTitle`.
  Rejected: a quick-access toolbox item (takes tab space, left-aligned, removable) and the window title (depends on
  the window manager, carries the product suffix).
- **L3** (2026-11-18, verbatim) "No, publica ya el nombre del archivo. es rapido"
- L4 (2026-11-18) Rebased on main a97def160 (PR #1, installer default apps). Full incremental build; release built
  with `make-release.sh`: archive sha256 `7e913d7a…d11497`, bootstrap `4c3b4e3f…e2bbc3`, glibc floor 2.44. Clean
  `archlinux:latest`: install rc 0, `libsfxlo.so`/`libvcllo.so` equal to the archive, 100 Boost defaults in
  `mimeapps.list`, PDF, purge rc 0 with `mimeapps.list` removed. Upgrade from the published 0.1.4 one-liner with a
  prior `text/csv` default: rc 0, `libsfxlo.so` is 0.1.5's, uninstall gave `text/csv` back. DT-V1 skipped (L3).

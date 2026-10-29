# Feature: icon accent fill (one filled element per icon) and release 0.1.3

- **Status:** done, 2026-10-29 (published in 0.1.3).
- **Locator:** `product/odd/tasks/icon-accent-fill.md`; **Engram mirror:** `odd/icon-accent-fill/tasks`.
- **Repo / branch:** `/mnt/games/libreoffice/core`, branch `feature/icon-accent-fill` from `main` (eb51ebde1). Runner:
  `python3 -I -m unittest discover -s product/tests -t .`

## Specs

- **S1** The user (2026-10-29), with a screenshot of the Home tab's Clipboard group (Paste, Cut, Copy, Format Painter,
  all grey outlines): "claude si hay que hacer que los iconos tengan algo de color de relleno en algun elemento del
  icono, no todo muy vacio".
- **S2** (from ruling 8 of `writer-ribbon-tabs.md`, 2026-10-22, still in force) The user rejected the whole-silhouette
  pastel fills ("tienen que ser otros más sencillos y minimalistas. No pegan con el tema de iconos de calc"); the
  rejected look is `/mnt/games/libreoffice/assets/previews/icon-minimal/before-after.png` (top rows).

## Rulings (controller, 2026-10-29; the user asked for no questions and no review stops)

1. **One element, not the silhouette:** an icon with a natural object part gets exactly one element (or one group of
   like elements) filled, as Microsoft 365 ribbon icons do: Paste = the clipboard board, the page stays white; Copy =
   the front page; Cut = the scissor rings; Format Painter = the brush head. The outline stays grey and on top.
2. **Coverage:** icons whose glyph has a closed object part (clipboard, page, folder, brush, table header row, chart
   bars, picture, shape, envelope, lock body, comment bubble, ...) get one; pure-stroke icons (alignment lines, arrows,
   letters such as B/I/U, plain borders) stay line only. Existing meaning badges (green plus or check, red cross,
   conditional-format bars) keep their color and are not the filled element.
3. **Colors by meaning, softer than 2026-10-22:** yellow/tan for clipboard, folder, brush, highlight, lock, note; blue
   for pages, documents, pictures, tables, charts, windows; green and red only where the object already means
   that. Tints lighter than the rejected ones (light and dark schemes both), so the outline still reads first.
4. **Disabled state:** a filled element must not hide a glyph detail when greyed (the W8 Check for Errors lesson).
5. **Release:** ships as 0.1.3, built and proven as 0.1.2 was.

## Tasks

- [x] **F1 — accent fills** (delegated, one writer; context reason: hundreds of per-icon choices and rendered
  previews/screenshots to look at): rulings 1-4, S1-S2. Commits 3f4ca4bfc, 37d4c4f77, af01047ad.
- [x] **F2 — release 0.1.3** (delegated packaging and container proof, as C2 of `ribbon-card.md`; controller
  publishes): ruling 5. Commits c8a744b3c, a547c21f9; published
  https://github.com/nahuel893/boost-office/releases/tag/v0.1.3.

## Log

- **L1** (2026-10-29, verbatim) "claude si hay que hacer que los iconos tengan algo de color de relleno en algun
  elemento del icono, no todo muy vacio"
- L2 (2026-10-29) Found: `manifest.json` has no `fill` since 2a3cb6e54 (IC1, ruling 8); the renderer
  (`build_theme.py` `compose`, `filled_cells`) still supports a whole-silhouette fill only. Branch and document created.
- L3 (2026-10-29) F1 done (delegated, opus): manifest `fill` takes seed points (`"at": [[x, y]]`, 24 px design
  units) that fill the closed outline region they sit in; gaps of about one design unit where Fluent objects overlap
  are bridged; a seed outside a closed region fails the build. 240 of 461 icons filled (blue 177, yellow 56, red 5,
  green 2). Tints light `#FCE6AE` / `#CDE3F8` / `#D3EDCF` / `#F9D5D7`, dark `#5E5034` / `#2D4560` / `#2F5A36` /
  `#5E373B`. Line-only families: arrows, letters, alignment/list lines, borders, color-stripe buttons, symbols,
  gears, people, links, filters. Suite 1155 OK (new icon tests RED against the old code). Preview and Home-tab
  screenshots in `/mnt/games/libreoffice/assets/previews/icon-accent-fill/f1/`; controller looked at the light
  before/after sheet and Calc Home: outline first, one soft accent. Concern: Paste/Cut/Copy look grey in a fresh
  document because they are disabled (vcl greys disabled images, fill included).
- L4 (2026-10-29) F2 done (delegated, opus): archive 214174688 bytes sha256 `48e8ac61…1af89d`, bootstrap
  `25cfd4dd…787d49`, glibc floor 2.44. Suite 1155 OK. Host install with sampled fills; `archlinux:latest` clean rc 0 +
  PDF; upgrade from the real published 0.1.2 one-liner rc 0, icon zips = archive (`196039d8…`, `e0d03471…`), purge
  rc 0; `ubuntu:24.04` refused rc 1. Icon zips are not byte-reproducible (member timestamps).
- L5 (2026-10-29) Publish (controller): `main`/`dev` a547c21f9, tag `v0.1.3`, release with the three assets. Real
  URLs in clean `archlinux:latest`: one-liner rc 0, icon zips `196039d8…` / `e0d03471…` = archive, PDF `%PDF-`,
  purge rc 0; image removed.

# Feature: the ribbon as a rounded card (Microsoft 365 look)

- **Status:** queued, 2026-10-26 (starts once the 0.1.1 archive of `boost-branding.md` is built: one writer in this
  tree at a time, and C1 rebuilds `vcl` into the `instdir` that 0.1.1 is packaged from).
- **Locator:** `product/odd/tasks/ribbon-card.md`
- **Engram mirror:** `odd/ribbon-card/tasks`
- **Repo / branch:** `/mnt/games/libreoffice/core`, branch `feature/ribbon-card` from `main` (410ae2d47 or later).

## Objective

The ribbon body (the commands under the tab names) is drawn as a rounded card on a slightly darker window background,
as Microsoft 365 does, in Writer, Calc and Impress, light and dark.

## Problem and why

The user (2026-10-26), with a Microsoft 365 Excel screenshot: "podes hacer que la cinta tenga un borde redondeado?".
Today (`product/docs/screenshots/calc-home-light.png`) the tab row, the ribbon and the window are one flat white area;
in 365 the tab row sits on a light gray background and the ribbon body is a white card with rounded corners and a few
pixels of margin, set off from the gray around it.

## Rulings (controller, 2026-10-26; the user asked for no questions and no review stops)

1. **Shape:** card corner radius about 8 px; margin about 4-6 px from the window's left and right edges and below the
   card; a 1 px subtle edge or soft shadow (whichever reads like 365 on gtk3); the tab names stay outside the card, on
   the window background, with the selected-tab underline unchanged.
2. **Colors from the Boost schemes:** window/tab-row background a light neutral gray (light) / dark neutral (dark),
   card = the current ribbon color; take existing `palette.json` roles, or add one role with light and dark values if
   none fits (say which). Contrast as in the user's screenshot: visible but quiet.
3. **Scope:** gtk3 (the shipped backend), Tabbed Office ribbons of Writer, Calc and Impress, light and dark; contextual
   tabs and the collapsed ribbon must still look right. Non-gtk3 backends keep rendering something sane.
4. **Release:** ships in 0.1.2, not 0.1.1 (the user, 2026-10-26: "no, que entre en la 0.1.2"); the README screenshots
   of the three apps are retaken.

## Tasks

- [x] **C1 — rounded ribbon card** (delegated, one writer: theme C++, possibly sfx2 notebookbar, palette, tests,
  screenshots; writer trigger): rulings 1-4. Commits c94600f65, 401201c60, 7d1b5309d, f94629eb9.
- [x] **C2 — release 0.1.2** (delegated packaging and container proof, as B2 of `boost-branding.md`; controller
  publishes): ruling 4. Commits 9c45f01b2, 1adfc4cbb; published
  https://github.com/nahuel893/boost-office/releases/tag/v0.1.2.

## Acceptance criteria

1. Screenshots of Writer, Calc and Impress (light and dark) show the ribbon as a rounded card with margins, the tab row
   on the window background; measured colors match the chosen palette roles.
2. The collapsed ribbon, a contextual tab (for example Calc chart or Writer table) and a popup still render correctly.
3. The unit suite is green; the custom-theme UITest regression passes.

## Progress / evidence

- 2026-10-26: requested; queued behind B1 (same working tree, single writer). Moved to 0.1.2 by the user.
- 2026-10-26 C1 (delegated, opus; route: writer trigger, vcl + sfx2 + palette + tests + screenshots): the notebookbar
  is a natively drawn vcl TabControl; gtk3 draws its page as a card through its own CSS node
  (`notebook.boost-ribbon > stack`); sfx2 drops the 6 px box margins under native drawing; new palette token `chrome`
  carried by the scheme's `InactiveColor`. Measured at 1920 px: radius 8 px (aliased corners), side and bottom margins
  4 px, light window `#F0F0F0` / card `#FFFFFF` / edge `#E0E0E0`, dark `#1F1F1F` / `#2B2B2B` / `#454545`. Writer,
  Calc, Impress light and dark, 1366 px collapsed ribbon and its popup, Insert > Table popup, Table contextual tab:
  screenshots in `/mnt/games/libreoffice/assets/previews/ribbon-card/c1/` (controller looked at Calc light and Writer
  dark). README light screenshots retaken. vcl and sfx2 builds rc 0; ribbon popups UITest OK; suite 1149 OK (RED
  observed in `test_ribbon_card.py`). Concerns accepted for 0.1.2: other vcl tab controls under a Boost scheme (Basic
  dialogs) also get the card; editing "Inactive" in Appearance changes the ribbon background; the 6 px margin change
  belongs in `gen_ribbon.py` `.ui` margins later; the corners are not antialiased; the writer started the vcl build at
  2138 MB available (rule is 2500), finished fine.

- 2026-10-26 C2 (delegated, opus; route: per-action packaging and container proof): docs at 0.1.2 (9c45f01b2), notes
  (1adfc4cbb). Archive 213983576 bytes sha256 `4a25bc5ef8b434a4b5fe8abae0c54b1e0006d39d4138c6d7e2be94e82afd5a9f`;
  bootstrap sha256 `baa349bf6c48eb877e05c3cc481e00880efc9a749b9b8f4eae0ba2f110d1e96a`; glibc floor 2.44. Suite 1149 OK.
  Host scratch install: splash, Start Center, Writer and Calc with the card (controller looked at the Writer shot).
  `archlinux:latest` clean rc 0 + PDF; upgrade from the real published 0.1.1 one-liner rc 0,
  `libvclplug_gtk3lo.so` 22e3d670… = archive (0.1.1 was b317c7cd…), PDF, purge rc 0; `ubuntu:24.04` refused rc 1.
- 2026-10-26 publish (controller, inline git/gh): `main`/`dev` 1adfc4cbb, tag `v0.1.2`, release with the three assets.
  Real URLs: clean `archlinux:latest` one-liner installed 0.1.2, `libvclplug_gtk3lo.so` 22e3d670…, `--convert-to pdf`
  wrote `%PDF-`, `--uninstall --purge` rc 0; image removed.
- **Status: done, 2026-10-26.**

## Next step

None for 0.1.2. Follow-ups: antialiased card corners; ribbon margins in `gen_ribbon.py` `.ui` instead of sfx2; a
dedicated scheme role instead of `InactiveColor`; keep the card off non-ribbon tab controls.

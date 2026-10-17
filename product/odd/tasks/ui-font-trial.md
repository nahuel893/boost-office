# Feature: ui-font-trial

**Branch:** `feature/ui-font-trial`, from `feature/calc-ribbon-tabs` (GitHub `dev`) at 79b72a8fc.
**SDD workspace:** `.superpowers/sdd/2026-10-17-ui-font-trial/` (briefs, reports; never committed).
**Engram mirror:** topic `odd/ui-font-trial/tasks`, project `office-boost`.

## Objective
Try two open fonts as the Calc user-interface font, Selawik and Inter. Make it easy to switch
between them, so the user can pick one. After the pick, the screenshots are redone with it.

## Problem and why
- The UI font comes from the system (GTK `gtk-font-name`, "Noto Sans 9" on the dev machine).
  The user says it makes the suite look like old LibreOffice.
- Office uses Segoe UI, which is proprietary and cannot be redistributed.
- The user reviewed four proposals (Selawik, Inter, Source Sans 3, Noto Sans) and asked on
  2026-10-17 to try the first two: "podemos probar con las 2 primeras, y de alguna forma que pueda
  switchear entre las dos".

## Scope
- Bundle both fonts with their SIL OFL 1.1 license texts.
- Add a per-launch switch: `system` (default, unchanged), `selawik` and `inter`. It goes in the
  launcher (`product/dev/calc.sh`) and in the screenshot tool (`product/dev/shot-tab.sh`).
- Take comparison screenshots of every tab with each font, light and dark.
- Build a comparison page where the user can toggle between the two fonts.
- Out of scope:
  - the default cell font (Carlito vs Liberation Sans): a separate decision;
  - choosing the font: the user decides;
  - packaging.

## Constraints
- Never change the user's system: no gsettings writes, no edits under ~/.config, no fonts installed
  in ~/.local/share/fonts or system-wide. Never touch the user's Calc profile
  (/mnt/games/libreoffice/try-profile) from agents.
- Prefer a mechanism the product can keep. A shipped suite sets its own UI font whatever the system
  font is, so the trial should not be throwaway.
  - Configuration or launcher only is preferred.
  - A C++ change in vcl is allowed only if no configuration route works. It must be minimal, and
    with the option unset it must behave exactly as today.
- Builds only through product/dev/lo-make.sh, one at a time; screenshots and UITests one at a
  time.
- English artifacts, Conventional Commits, no AI attribution.

## Tasks

| ID | Task | Route | Status |
|---|---|---|---|
| T1 | Fonts in `product/fonts/`, and the `--font system\|selawik\|inter` switch in calc.sh and shot-tab.sh, with launcher tests | delegated (opus): mechanism research in vcl/GTK plus 2+ non-trivial files | pending |
| T2 | Comparison screenshots for each font: every tab, light and dark, at 1920; a 1366 check of the widest tabs for `>>` overflow | delegated (sonnet): mechanical runs | pending |
| T3 | Comparison page with a Selawik/Inter toggle | inline: one page built from T2's images | pending |

## Acceptance
- With `--font selawik` or `--font inter`, the Calc UI (tab bar, ribbon labels, menus, dialogs)
  renders in that font. With no flag, or with `system`, nothing changes.
- The switch needs no system change. It works in the private headless sway of shot-tab.sh and
  in the user's desktop session.
- Unit tests cover the flag (`python3 -I -m unittest discover -s product/tests -t .`).
- The screenshots show the font change, and say whether either font makes sections collapse into
  `>>`.

## Checks
- `python3 -I -m unittest discover -s product/tests -t .`
- If C++ changes: `product/dev/lo-make.sh vcl.build` (plus any module it needs).
- Screenshots of Home (light) with system, selawik and inter, looked at and compared.

## Delivery
- Forecast: about 200-350 authored lines (scripts, tests, docs). Fonts are vendored binaries and
  do not count.
- Strategy: ask-on-risk.
- The branch stays local until the user picks a font. Then the pick goes to `dev` with new
  screenshots.

## Progress
- 2026-10-17: feature document created. Inline check found that the font path includes
  `$UserInstallation/user/fonts` (vcl/unx/generic/print/helper.cxx:218), and that
  `StyleSettings::SetUseSystemUIFonts` exists in vcl/source/app/settings.cxx:1448.

## Next step
T1.

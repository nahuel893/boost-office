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
| T1 | Fonts in `product/fonts/`, and the `--font system\|selawik\|inter` switch in calc.sh and shot-tab.sh, with launcher tests | delegated (opus): mechanism research in vcl/GTK plus 2+ non-trivial files | done |
| T2 | Comparison screenshots for each font: every tab, light and dark, at 1920; a 1366 check of the widest tabs for `>>` overflow | delegated (sonnet): mechanical runs | done |
| T3 | Comparison page with a Selawik/Inter toggle | inline: one page built from T2's images | done |

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

- 2026-10-17: T1 done.
  - Commits 3c691b180 (fonts), 9a9d75d42 (vcl: `VCLSettings/UIFont/FamilyName`, read by
    the gtk3 plugin) and 01fbf54e3 (launcher switch, tests, docs).
  - Route (b): no configuration-only route works, because GTK `settings.ini` loses to GSettings
    and XSETTINGS, and `UseSystemUIFonts` is never acted on. The plugin sets GTK's
    `gtk-font-name` family for this process and resets pango's font map, which otherwise misses
    the bundled fonts.
  - Checks: unit tests 295 -> 309 OK (re-run by the controller: 309 OK). officecfg, vcl and
    postprocess builds exit 0. Home, a menu and a dialog were captured per font.
  - Task review (opus): spec compliant; quality approved with minor findings. The doc finding is
    fixed. Three edge cases are parked as known limitations in product/docs/ui-font-trial.md:
    the per-thread pango map, the fontconfig reinit, and the unvalidated family name.
  - Parked follow-up: the UI size. Private-config launches (shot-tab.sh, light calc.sh) get
    Noto Sans 11, while the user's desktop is 9. Office uses 9 pt, so the product may need to
    set the size too.

- 2026-10-18: T2 done.
  - 72 shots (48 at 1920, 24 at 1366), all on the first try, every one with the right tab.
  - 9 contact sheets in /mnt/games/libreoffice/assets/previews/font-trial/ (outside the repo).
    Report: .superpowers/sdd/2026-10-17-ui-font-trial/task-T2-report.md.
  - At 1366 the same sections collapse with all three fonts, except Formulas: Selawik keeps
    Defined Names. All shots are at UI size 11 (private config), the same for every font.
  - The agent's session ended before it returned, and the machine rebooted on 2026-10-18 12:10.
    The report and the sheets survived; the raw shots in the scratchpad were lost.
- 2026-10-18: T3 done. Comparison page with font, theme, width and zoom toggles:
  https://claude.ai/artifact/1SnETGQjoKWUwQk2iG9yxr (private).
- RDD for 79b72a8fc..789dabe3c (risk high, 22 files, 599 lines, review due): asked again on
  2026-10-20, and the user declined it for this candidate. Off path for a high tier: the
  writer's own checks plus the independent opus task review of T1 (approved, minor findings
  fixed or parked) stand as the verification.
- 2026-10-20: the planning request of 2026-10-18 (features "in the todo file", plus ADRs) was a
  mistake by the user's account. Work returns to this feature.

## Next step
The user picks a font. Then the pick becomes the product default, and the `dev` screenshots and
the README are redone with it.

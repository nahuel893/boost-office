# Feature: icon-thin-outlines

**Branch:** `feature/icon-thin-outlines`, from `feature/ui-font-trial` at 45acafe53. It goes to GitHub
`dev` together with the Inter font and the white light scheme.
**SDD workspace:** `.superpowers/sdd/2026-10-20-icon-thin-outlines/` (briefs, reports; never committed).
**Engram mirror:** topic `odd/icon-thin-outlines/tasks`, project `office-boost`.

## Objective
Thin outlines on the Boost icons. On 2026-10-20 the user asked: "a los iconos tenés que bajarle el
tamaño de los bordes. Todo borde negro tiene que ser más fino en iconos".

## Problem and why
- product/icons/build_theme.py builds each icon from Fluent System Icons glyphs:
  - the outline comes from the "regular" glyph, drawn in the palette's `line` color (`#424242`
    light, `#D6D6D6` dark);
  - the soft fill comes from the "filled" silhouette;
  - rsvg-convert renders the result to PNG at 16, 24 and 32 px.
- Fluent's regular strokes are heavier than the hairline outlines of Office's ribbon icons, most of
  all on the 24 and 32 px buttons.

## Scope
- Thinner outlines at every size (16, 24, 32) in both themes. Ruling: dark gets the same weight as
  light, so the two stay consistent.
- Every outline layer is thinned, whatever its color, so badges keep the same weight as the base
  glyph.
- Filled shapes, the soft fill silhouettes, rects and the color-stripe band do not change.
- A before/after preview sheet for the user.
- The dev screenshots are retaken with the new icons.
- Out of scope:
  - new glyphs;
  - icon choices;
  - the `main` branch;
  - Writer and Impress icons, which come with their own feature.

## Constraints
- The outlines must not break: no gaps, no vanished dots or thin details. The result must stay crisp
  at 1x.
- The build stays reproducible from the sources: no hand-edited PNGs.
- Only `product/icons/build_theme.py install --instdir` writes the instdir icon zips.
- No LibreOffice build is needed.
- Screenshots one at a time. Never touch /mnt/games/libreoffice/try-profile from agents.
- English artifacts, Conventional Commits, no AI attribution.

## Tasks

| ID | Task | Route | Status |
|---|---|---|---|
| T1 | Thinner outline layers in build_theme.py, with a stroke-width test and a before/after preview sheet | delegated (opus): rendering judgment, code plus tests | done |
| T2 | Rebuild and install the themes, and retake all 8 dev screenshots, light and dark | delegated (sonnet, the T5 screenshot worker): mechanical runs | pending |
| T3 | RDD consent for 5658d8546..HEAD, fast-forward `feature/calc-ribbon-tabs`, push to GitHub `dev` | inline: git state only | pending |

## Acceptance
- The measured outline at 24 and 32 px is about 1 px: thinner than today, and never under 0.75 px.
- At 16 px the outline is no heavier than today.
- Every existing icon test passes.
- The preview sheet shows before and after for the common ribbon icons, at 16, 24 and 32 px, in light
  and dark.
- The dev screenshots show the new icons.

## Checks
- `python3 -I -m unittest discover -s product/tests -t .`
- `python3 -I product/icons/build_theme.py build`, then `install --instdir instdir`.
- Look at the preview sheet and the screenshots.

## Delivery
- Forecast: about 100-200 authored lines, plus regenerated PNGs, which do not count.
- Strategy: ask-on-risk.

## Progress
- 2026-10-20: feature document created.

- 2026-10-20: T1 done.
  - Commit aefe1b1e3: outline layers are eroded through a round stroke mask over their contours,
    rendered at 8x and box-filtered down. Measured widths:
    - 24 px: 1.50 -> 1.00 px;
    - 32 px: 2.00 -> 1.00 px;
    - 16 px: unchanged at 1.00 px; all 230 PNGs per theme are byte-identical.
  - Commit b7bb4328a, the fix for the user's feedback. The user asked for inner lines as thin as
    the border. Their screenshot came from a Calc started before the install. The thin lines then
    showed 1 px white bands, where Fluent's filled silhouette leaves gaps. Now a closed cell is
    filled when the silhouette covers at least half of it.
  - Accepted rulings:
    - fills and highlight rects are trimmed with the outline, and the fill covers the outline's
      area;
    - the art at 32 px moves 0.5 px up-left so that strokes stay crisp;
    - 16 px stays as it is.
  - Known: at 24 px the frame and the inner lines cannot all be sharp, because their centres fall
    on alternating quarter pixels.
  - Checks:
    - tests 313 -> 318 OK (the controller re-ran them: OK);
    - the new width and gap tests were RED first;
    - build and install exit 0;
    - preview sheets in /mnt/games/libreoffice/assets/previews/icon-outlines/, looked at by the
      worker and by the controller (cells icons at 4x).
  - Report: .superpowers/sdd/2026-10-20-icon-thin-outlines/task-T1-report.md.

## Next step
T2: retake the dev screenshots with the new icons.

# Calc Home tab redesign: vertical slice (design spec)

- **Date:** 2026-10-12
- **Status:** written; waiting for the user's review.
- **Sub-project:** 1 of 4 in the UI redesign: visual language, icons, ribbon, details.
  This spec covers only the first vertical slice: Calc's Home tab, end to end.

## 1. Intent

### What the user said
- The goal is an installable, open-source LibreOffice-based suite with a new name, competing
  in the market.
- The UI should be as close as possible to MS Office, "like WPS Office does".
- Before adding features, redesign the UI: better icons, better button layout, better quality.
- The visual reference is both Microsoft 365 familiarity and a compact own identity (WPS).
- Today's pain points: dated, disordered, cluttered, unpolished.
- Key rule: "every tab is divided into sections, like Excel."

### Assumptions (stated, not confirmed by the user)
- One slice, done well, validates the visual language before thousands of icons are drawn.
- The user's own setup (Hyprland, 1920x1080 at scale 1, dark GTK theme) is the first target
  screen. Light mode must be equally finished.

### Success criteria
1. In Calc, a new ribbon variant shows Excel's Home organization: 8 titled sections.
2. Every Home button works, with new Fluent-based icons in light and dark.
3. The ribbon uses the new neutral palette, without the per-app green tint.
4. The user approves before/after screenshots in light and dark.
5. All automatic checks pass (section 7), and no existing ribbon variant changes.

## 2. Approach: "A then B" (approved)

- **Stage A** is declarative only: a new `.ui` variant, a partial icon theme, color schemes and
  configuration. This spec's implementation plan covers stage A.
- **Stage B** is targeted C++, planned separately after stage A's screenshots are approved.
  Its list of items is in section 8.

Product-only work lives in NEW files where possible (fork strategy, rule 2:
`product/docs/fork-strategy.md`).

## 3. Approved design annexes (normative)

The four approved section files are part of this spec. If this document and an annex
disagree, the annex wins and this document gets fixed.

| # | Topic | File |
|---|-------|------|
| 1 | Layout | `product/docs/design/calc-home-tab-layout.txt` |
| 2 | Icons | `product/docs/design/calc-home-icons.txt` |
| 3 | Colors and type | `product/docs/design/calc-home-palette.txt` |
| 4 | Prototype and validation | `product/docs/design/calc-home-prototype.txt` |

## 4. Components

Each unit has one purpose and can be built and checked on its own.

### 4.1 Ribbon variant
- **Purpose:** Calc's Home tab with the 8 sections from annex 1 (Undo, Clipboard, Font,
  Alignment, Number, Styles, Cells, Editing).
- **Files:**
  - **New:** `sc/uiconfig/scalc/ui/notebookbar_office.ui`. It starts as a copy of the full
    Tabbed `notebookbar.ui`, because that one has section captions. Only the Home tab is
    redesigned; the other tabs stay as copied.
  - **Edited:** `officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu`. One new
    mode node for Calc ("Tabbed Office", working name). This is a small, contained exception
    to the new-files rule: modes can only be registered there.
  - **Edited:** `solenv/sanitizers/ui/modules/scalc.suppr`. A `button-no-label` line for
    every new tool button, which the build check requires.
  - **Edited:** `sc/UIConfig_scalc.mk`. One line next to the other variants (L169-173),
    so the new file is packaged.
- **Rules:**
  - Large buttons use `icon_size=5` (32 px). Small buttons use `icon_size=1` (16 px).
    Mapping: `sfx2/source/sidebar/SidebarToolBox.cxx:318-327`.
  - Captions drop the italic and keep `scale=0.9`.
  - Ids follow the existing pattern (`btnHome<Cmd>`, `gdHome<Section>`). Each section grid
    has an a11y `labelled-by` relation to its caption, as in `notebookbar.ui`.
  - Each section is wrapped in a `VclOptionalBox` with a `priority-N` class, so the
    `sfxlo-PriorityMergedHBox` can collapse sections from the right. Only `VclOptionalBox`
    and `sfxlo-DropdownBox` take a priority (`vcl/source/window/builder.cxx:2444-2447`).
- **Generator (product tooling, added 2026-10-12 while planning):**
  - The Home page XML is generated from a JSON layout by `product/ui/gen_ribbon.py`. The
    output is spliced between marker comments, so every other line of the copied file stays
    byte-identical and can still be diffed against upstream `notebookbar.ui`.
  - The same tool keeps the `scalc.suppr` lines in sync with the generated ids.
  - Why: sub-project 3 redoes every tab, and generated sections guarantee consistent ids,
    captions and a11y relations.
- **Dropdown menus marked "~"** in annex 1: spike 0a decides whether they are declarative.
  If they are not, stage A ships the fallback written in annex 1, and the menus move to
  stage B.

### 4.2 Icon theme
- **Purpose:** the 58 Home icons from annex 2, in light and dark.
- **Files (all new, under `product/icons/`; changed 2026-10-12 while planning):**
  - `fluent/`: the vendored subset of Fluent SVGs used by the manifest, plus Fluent's MIT
    `LICENSE`.
  - `custom/` and `overrides/`: our own SVGs (custom glyphs and hand-tuned 16 px versions).
  - `manifest.json`: one entry per icon (commands, layers, accents, large, stripe).
  - `build_theme.py`: renders `cmd/sc_*` (16), `cmd/lc_*` (24) and `cmd/32/*` (32, large
    buttons only) in light and dark, writes `links.txt` aliases and the license, and zips
    `images_boost.zip` and `images_boost_dark.zip`. "boost" is a working name until the
    product name exists.
  - Why not `icon-themes/boost*`: the build scans every `icon-themes/*/` directory for
    command images (`postprocess/CustomTarget_images.mk:97-117`), and packing a theme needs
    the `configure.ac:14586-14600` allow-list. In stage A the zips are copied into
    `instdir/share/config/`, where the runtime scanner finds any `images_<name>.zip`
    (`vcl/source/app/IconThemeScanner.cxx:37-54`). Build integration belongs to packaging.
- **Rules:**
  - The style rules are in annex 2, section 2.
  - The color buttons keep the bottom quarter of the icon empty: LibreOffice paints the
    chosen color there (`svx/source/tbxctrls/tbxcolorupdate.cxx:266-274`).
- **Fallback:** a command missing from the theme falls back to Colibre automatically
  (`vcl/source/image/ImplImageTree.cxx:342-360`). The mixed look on other tabs is expected
  during this slice.
- **Dark:** the user picks `boost_dark` by hand in stage A. A custom theme is not
  auto-switched (`vcl/source/app/IconThemeSelector.cxx:109-117`).

### 4.3 Color schemes and settings
- **Purpose:** the neutral palette from annex 3, through LibreOffice's theme engine.
- **Files (changed 2026-10-12 while planning):**
  - Two ColorScheme entries, "Boost Light" and "Boost Dark", shipped as a configuration-only
    LibreOffice extension. `product/themes/build_schemes.py` generates it from
    `product/themes/palette.json`.
  - The extension holds one `.xcu` under `org.openoffice.Office.UI/ColorScheme/ColorSchemes`,
    the same place as the built-in schemes (`officecfg/.../Office/UI.xcu:135-142`).
  - It is installed into the dev profile with `unopkg`. No upstream file changes.
  - Colors are `xs:int` values (`UI.xcs:53`).
- **UI role mapping**
  - These are the 27 roles in `include/vcl/themecolors.hxx`. Each line gives the annex 3
    token and its light / dark value.

  - **Window and text**
    - `WindowColor`: surface. #E4F2E8 / #2B2B2B.
    - `WindowTextColor`: text. #242424 / #F2F2F2.
    - `BaseColor`: field. #FFFFFF / #1F1F1F.
    - `FieldColor`: field. #FFFFFF / #1F1F1F.
    - `FaceColor`: surface.pressed. #C3DECB / #454545.
    - `ShadowColor`: field.border. #828282 / #7A7A7A.
    - `SeparatorColor`: separator. #9E9E9E / #6A6A6A.
  - **Buttons**
    - `ButtonColor`: surface. #E4F2E8 / #2B2B2B.
    - `ButtonTextColor`: text. #242424 / #F2F2F2.
  - **Accent and disabled**
    - `AccentColor`: selection. #CFE8D7 / #1E4D2E.
    - `DisabledColor`: surface.hover. #D3E8DA / #383838.
    - `DisabledTextColor`: text.disabled. #A6A6A6 / #6E6E6E.
  - **Active and inactive**
    - `ActiveColor`: accent.calc. #1B7A3E / #5CC27E.
    - `ActiveTextColor`: field. #FFFFFF / #1F1F1F.
    - `ActiveBorderColor`: accent.calc. #1B7A3E / #5CC27E.
    - `InactiveColor`: surface. #E4F2E8 / #2B2B2B.
    - `InactiveTextColor`: text.disabled. #A6A6A6 / #6E6E6E.
    - `InactiveBorderColor`: separator. #9E9E9E / #6A6A6A.
  - **Menu bar**
    - `MenuBarColor`: surface. #E4F2E8 / #2B2B2B.
    - `MenuBarTextColor`: text. #242424 / #F2F2F2.
    - `MenuBarHighlightColor`: surface.hover. #D3E8DA / #383838.
    - `MenuBarHighlightTextColor`: text. #242424 / #F2F2F2.
  - **Menus**
    - `MenuColor`: menu. #FFFFFF / #2B2B2B.
    - `MenuTextColor`: text. #242424 / #F2F2F2.
    - `MenuHighlightColor`: menu.hover. #F0F0F0 / #383838.
    - `MenuHighlightTextColor`: text. #242424 / #F2F2F2.
    - `MenuBorderColor`: separator. #9E9E9E / #6A6A6A.

  Document colors (cells, grid, sheet background) stay nil, which means automatic, as in
  the built-in automatic scheme. They are out of scope.
- **Settings for the prototype:**
  - `Office.Common/Appearance/LibreOfficeTheme` = enabled, so our scheme is used.
  - `Office.Common/Misc/NotebookbarColorTransparency` = 255, which removes the green tint.
    `Common.xcs:5236-5243` documents 255 as "full dialog color";
    `vcl/source/control/notebookbar.cxx:268-291` applies it.
  - The selected scheme and icon theme (light or dark, matching the system).

  In this slice, these values are applied through the isolated dev profile. Making them the
  shipped product defaults belongs to the branding and packaging work, not this slice.

## 5. Data flow at runtime

1. Calc starts. The ToolbarMode entry selects `notebookbar_office.ui`.
2. The VCL builder creates the ribbon. Each tool button asks the icon theme for
   `cmd/<size>_<command>`. A missing icon falls back to Colibre.
3. With the theme engine enabled, ThemeColors come from our scheme. gtk3 applies them
   through CSS (`vcl/unx/gtk3/custom-theme.cxx`).
4. NotebookBar paints its background as the dialog color merged with the module color at
   transparency 255, which gives a plain dialog color.
5. Buttons dispatch their existing `.uno:` commands. Nothing new happens at runtime in
   stage A, unless spike 0a allows declarative menus.

## 6. Spikes (step 0, before any product file)

Each spike has a yes/no outcome and a pre-decided fallback.

| Id | Question | If the answer is no |
|----|----------|---------------------|
| 0a | Can the "~" dropdowns be `.ui`/`.xcu` only (popup menus plus controllers)? | Annex 1 fallback; the menus go to stage B |
| 0b | Does the theme engine reach ribbon buttons and hover under gtk3? | Note the gaps; ribbon-scoped CSS goes to stage B |
| 0c | Does LibreOffice switch between two custom schemes with the system? | Pick by hand in stage A; auto-switch goes to stage B. The code says no: explicitly set colors do not follow the OS (`svtools/source/config/colorcfg.cxx:628-641`). The spike confirms it at runtime. |
| 0d | Do a dropped-in icon zip and a configuration-only extension work at runtime? | Packing at build time needs the `configure.ac` allow-list, so it goes to the packaging work |
| 0e | Can a UITest reach notebookbar widgets by id? | Static test of the `.ui` plus a runtime test that the mode loads |

## 7. Testing and checks

- **TDD mode:** strict, from the session configuration. The runner is LibreOffice UITest
  (`make UITest_<name>`) in the dev build. Each test is written first and fails (RED).
- **Tests** (the shape depends on spike 0e):
  - Calc can switch to the new mode, and the ribbon loads.
  - Each of the 8 Home sections exists and has its caption.
  - Each Home button exists and has the command from annex 1.
- **Build checks on the new `.ui`:**
  - `bin/gla11y` with the build's flags and `scalc.suppr`: 0 new errors.
  - `bin/lint-ui.py`: clean.
- **Isolation:** the diff does not touch other `notebookbar*.ui` files.
- **Visual:** before/after PNGs in light and dark at 1920x1080. Width checks at 1366 and
  1024 px (annex 4, section 3).
- **Builds:** under the cgroup memory cap (`systemd-run --user --scope -p MemoryMax=7G ...
  PARALLELISM=6`). A full build at -j10 froze the 14 GB machine.

## 8. Out of scope (stage B and later)

Each item below gets its own plan after stage A is approved:
- Office-like flat tabs with an accent underline, scoped to the ribbon.
- Caption color `text.secondary`. The VCL label attributes support no color today
  (`vcl/source/window/window2.cxx:1472-1521`).
- Automatic light/dark switching of the scheme and the icon theme.
- The "~" menus, if spike 0a sends them here.
- The ">>" collapse for the full Tabbed layout, if the width test fails.

Not part of this redesign slice:
- Other tabs, other apps, dialogs, the status bar.
- The product name and branding.
- Shipped defaults and packaging.
- The paused Formulas-tab feature (`product/odd/tasks/calc-formulas-tab.md`).

## 9. Risks

| Risk | Mitigation |
|------|------------|
| The theme engine is new and only partly reaches gtk3 widgets | Spike 0b runs first; any gaps are listed before step 4 |
| Icons are illegible at 16 px (vertical align, table glyphs) | Hand-tuned 16 px versions; legibility is checked in step 3 screenshots |
| Upstream changes `notebookbar.ui` while we hold a copy | The copy changes only Home; other tabs are re-synced when the product branch is ported |
| The build machine freezes | Memory-capped builds (section 7) |

## 10. Delivery

- **Branch:** `feature/calc-home-redesign` in `/mnt/games/libreoffice/core`, based on the
  same master commit as the dev build.
- **Commits:** one Conventional Commit per step (0 to 4).
- **Upstream:** generic findings are noted as upstream candidates, for example the
  dark icon auto-switch and caption colors.
- **Not delivered here:** pushing, Gerrit and product branches are separate decisions.

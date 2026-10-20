# Boost Office

An office suite based on LibreOffice, with a ribbon that follows Microsoft 365.
"Boost Office" is a working name.

The first application is Calc. Its Tabbed Office ribbon is being rebuilt to match
Excel 365, section by section and button by button.

![Calc Home tab, light theme](product/docs/screenshots/home-light.png)

## Status

| Branch | Content |
|---|---|
| `main` | Calc Home and Data tabs, Fluent-based icons, light and dark color schemes |
| `dev` | Everything on `main`, plus the other Calc tabs: Insert, Page Layout, Formulas, Review, View and Help. It moves to `main` after review |

- Buttons for Excel features that LibreOffice lacks are shown greyed out. They are
  placeholders for features still to be built. The lists are in
  [calc-data-redesign.md](product/docs/calc-data-redesign.md) and, on `dev`, in
  [calc-ribbon-tabs.md](https://github.com/nahuel893/boost-office/blob/dev/product/docs/calc-ribbon-tabs.md).
- The new labels and tooltips are in English only.
- Writer, Impress and the other applications are unchanged from LibreOffice.

## Screenshots

- [Home and Data tabs](product/docs/screenshots/README.md)
- [Every tab (dev)](https://github.com/nahuel893/boost-office/blob/dev/product/docs/screenshots/README.md)

## Where things are

- `product/` holds what belongs to Boost Office and not to LibreOffice:
  - `ui/`: the ribbon layouts and the generator that writes the ribbon pages;
  - `icons/`: the icon theme builder;
  - `themes/`: the color scheme builder;
  - `dev/`: build, run, screenshot and test scripts;
  - `tests/`: unit tests;
  - `docs/`: design notes, research and decisions.
- Everything else is LibreOffice core, plus the changes the ribbon needs. Most of
  those are in `sc/uiconfig/`.

## Build and run (Linux)

1. Install LibreOffice's build dependencies, as described in
   [Building on Linux](https://wiki.documentfoundation.org/Development/BuildingOnLinux).
2. Put the configure options in `autogen.input`, then run `./autogen.sh`. The
   development machine uses gtk3 only, without Java, help, Firebird or PostgreSQL.
3. Build with `product/dev/lo-make.sh`. It runs `make` under a memory cap.
4. After a full build, install the icon theme into the build:
   `python3 -I product/icons/build_theme.py install --instdir instdir`.
5. Open Calc with the product look:
   `product/dev/calc.sh light --profile ~/boost-profile` (or `dark`). The script
   rewrites that profile on each run. The UI font is Inter (bundled, SIL OFL);
   `product/dev/calc.sh light --font system` keeps the desktop's font.

## Tests

- Unit tests: `python3 -I -m unittest discover -s product/tests -t .`
- One Calc UI test: `product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.<test name>`

## License

Same licenses as LibreOffice: see [COPYING](COPYING), [COPYING.MPL](COPYING.MPL)
and [COPYING.LGPL](COPYING.LGPL).

## LibreOffice

This repository is a fork of LibreOffice core. LibreOffice's own README, with an
overview of its code, is in [README-LibreOffice.md](README-LibreOffice.md).
LibreOffice is a trademark of The Document Foundation. Boost Office is not
affiliated with The Document Foundation.

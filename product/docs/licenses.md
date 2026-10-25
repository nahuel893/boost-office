# Licences

Boost Office is LibreOffice plus the files under `product/` and the changes the ribbons needed. Each part keeps its
own licence.

| Part | Licence | Where the text is |
|---|---|---|
| Boost's own code and docs (`product/`, the ribbon changes in `sc/`, `sw/`, `sd/`, `officecfg/`, `cui/` ...) | MPL 2.0 | [COPYING.MPL](../../COPYING.MPL) |
| LibreOffice code the fork inherits | MPL 2.0, with parts under LGPLv3+ and GPLv3+ as upstream states | [COPYING.MPL](../../COPYING.MPL), [COPYING.LGPL](../../COPYING.LGPL), [COPYING](../../COPYING) |
| Third-party libraries LibreOffice bundles (`external/`) | Their own, as upstream lists | upstream's `external/` and its notices |
| Inter (UI font, installed) | SIL Open Font License 1.1 | [Inter's OFL.txt](../fonts/inter/OFL.txt) |
| Selawik (UI font trial, not installed) | SIL Open Font License 1.1 | [Selawik's OFL.txt](../fonts/selawik/OFL.txt) |
| Fluent UI System Icons (the source of the Boost icon theme) | MIT | [LICENSE](../icons/fluent/LICENSE) |

## What Boost bundles

- **Inter 4.1**, by The Inter Project Authors (<https://github.com/rsms/inter>). Four static TrueType files in
  `product/fonts/inter/`, unmodified. `install.sh` copies them to `<prefix>/share/fonts/truetype/`. See
  [product/fonts/inter/README.md](../fonts/inter/README.md).
- **Selawik 1.01**, by Microsoft Corporation (<https://github.com/microsoft/Selawik>). Five static fonts in
  `product/fonts/selawik/`, unmodified, kept for the font trial ([ui-font-trial.md](ui-font-trial.md)); the
  installer does not ship them. "Selawik" is a Reserved Font Name: a modified version must use another name. See
  [product/fonts/selawik/README.md](../fonts/selawik/README.md).
- **Fluent UI System Icons**, copyright Microsoft Corporation, MIT, in `product/icons/fluent/`. The icon theme builder
  (`product/icons/build_theme.py`) reads these SVGs and writes the Boost icon themes (`images_boost.zip`,
  `images_boost_dark.zip`), which are derived from them, so the MIT notice applies to them too.
  `product/icons/custom/` holds the few icons Boost drew itself.

The Boost color schemes (`product/themes/`) and the install layer (`product/install/build_xcd.py`) are generated from
Boost's own data and contain no third-party material.

## Trademarks

Boost Office is not affiliated with or endorsed by The Document Foundation or Microsoft. LibreOffice is a trademark of
The Document Foundation. Microsoft 365, Word, Excel and PowerPoint are trademarks of Microsoft. Microsoft's ribbon is
only the reference for where buttons go: this repository carries no Microsoft screenshots or artwork other than the
MIT-licensed Fluent icons and the OFL-licensed Selawik font above.

## Adding something third-party

Put its licence text next to it, add a row to the table above, and say in the commit where it came from.

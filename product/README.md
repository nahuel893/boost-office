# product/

Everything Boost Office adds to LibreOffice that is not a change inside LibreOffice's own modules. gbuild ignores this
directory. The project overview is the [root README](../README.md).

| Folder | What it holds |
|---|---|
| `dev/` | Memory-capped build (`lo-make.sh`), dev launchers (`office.sh`, `calc.sh`), the dev profile writer (`profile.py`), screenshots (`shot-tab.sh`, `shot.sh`), UI tests (`uitest.sh`) and the `.ui` check (`check-ui.sh`) |
| `docs/` | Design records per app ([Calc](docs/calc-ribbon-tabs.md), [Writer](docs/writer-ribbon-tabs.md), [Impress](docs/impress-ribbon-tabs.md)), the guides ([install](docs/install.md), [building](docs/building.md), [licences](docs/licenses.md)), research, notes, design drafts and screenshots |
| `fonts/` | The bundled UI fonts with their licences: `inter/` (installed) and `selawik/` (font trial only) |
| `icons/` | The icon theme builder (`build_theme.py`), the vendored Fluent SVGs (`fluent/`), Boost's own icons (`custom/`) and the manifest that maps LibreOffice icons to them |
| `install/` | `install.sh`, `uninstall.sh`, the generator of the default settings layer (`build_xcd.py`), the desktop entry template and the configure flag sample |
| `odd/` | `tasks/`: one feature document per feature, with its checklist, decisions and evidence |
| `tests/` | Unit tests (standard library `unittest`) |
| `themes/` | The color schemes: `palette.json` and the builder of the scheme extension (`build_schemes.py`) |
| `ui/` | The ribbon layouts (JSON, one per tab) and the generator that writes the ribbon pages (`gen_ribbon.py`) |

## Common commands

| Task | Command |
|---|---|
| Unit tests | `python3 -I -m unittest discover -s product/tests -t .` |
| Rewrite the ribbon pages from the layouts | `python3 -I product/ui/gen_ribbon.py --all` |
| Build | `PARALLELISM=2 product/dev/lo-make.sh` |
| Screenshot of a tab | `product/dev/shot-tab.sh --app calc\|writer\|impress light Home out.png` |
| Install the build | `product/install/install.sh` |

Contributing: [CONTRIBUTING.md](../CONTRIBUTING.md).

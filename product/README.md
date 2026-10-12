# product/

Product-only tooling for the LibreOffice-based suite (working name "boost").
gbuild ignores this directory. Nothing here is meant for upstream.

- `dev/`: memory-capped builds, the isolated dev profile, screenshots, UI checks.
- `ui/`: the ribbon layout generator and layouts.
- `icons/`: the Fluent-based icon theme builder.
- `themes/`: the color scheme extension builder.
- `docs/`: findings from the stage A spikes.
- `tests/`: unit tests: `python3 -I -m unittest discover -s product/tests -t .`

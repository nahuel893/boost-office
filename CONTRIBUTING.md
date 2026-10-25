# Contributing to Boost Office

Boost Office is a LibreOffice fork. Changes to the ribbons, icons, themes, installer and docs belong here; a bug or
feature that is about LibreOffice itself is better reported to [LibreOffice](https://www.libreoffice.org/get-help/bug/).

## Quick path

1. **Open an issue first**, with the bug or feature template, so the change is agreed before code is written.
2. **Branch** from `main`: `feature/<short-name>` (or `fix/<short-name>`).
3. **Change one thing per commit**, with its tests and docs in the same commit.
4. **Run the unit tests**: `python3 -I -m unittest discover -s product/tests -t .`
5. **Attach a screenshot** for any UI change (see below).
6. **Open a pull request** against `main`; the template lists what to check.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/), subject at most 79 characters:

```
feat(product): add the Boost Office install and uninstall scripts
fix(product): set the Boost workspace color in the color schemes
docs: rewrite the README for Boost Office
test(product): pin the repository docs and GitHub files
```

Use `feat`, `fix`, `docs`, `test`, `refactor` or `chore`; the scope is the module (`product`, `sc`, `sw`, `sd`,
`cui`, `officecfg` ...). A commit is one reviewable unit: the behavior, its tests and its docs together.

## Tests

| What | Command |
|---|---|
| Unit tests (all) | `python3 -I -m unittest discover -s product/tests -t .` |
| One file | `python3 -I -m unittest discover -s product/tests -t . -p test_install.py` |
| A ribbon UI test | `product/dev/uitest.sh [--app calc\|writer\|impress] module.Class.test` (needs a build) |

- Write the test first when a deterministic test is possible; watch it fail, then make it pass.
- Python tools use only the standard library (Pillow for the icon builder) and run with `python3 -I`.
- Shell scripts use `set -eu` (or `set -euo pipefail` in bash) and pass `shellcheck`.
- Tests must never touch your own `~/.config` or `~/.local`: use temporary `HOME` and XDG directories.

## Build

[product/docs/building.md](product/docs/building.md). Builds run through `product/dev/lo-make.sh`, which caps
memory; one build at a time.

## Screenshots for UI changes

Use `product/dev/shot-tab.sh` (it runs its own headless sway and a private profile, so it never touches your session):

```sh
product/dev/shot-tab.sh --app writer light Home /tmp/writer-home.png
```

Attach the PNG to the pull request. Do not commit it, unless the change is to the README's screenshots in
`product/docs/screenshots/`. Never add Microsoft screenshots: describe where the reference ribbon puts a button in
words.

## Where the design lives

| Where | What |
|---|---|
| `product/docs/*-ribbon-tabs.md` | The design record of each app's ribbon: what each tab holds, how it is built, the decisions and the placeholders |
| `product/odd/tasks/` | One feature document per feature: objective, rulings, task list and evidence |
| `product/docs/design/`, `product/docs/research/` | Layout drafts and the reference research |
| `product/README.md` | Index of `product/` |

A change to behavior updates its design record in the same commit. A new ribbon button either runs a LibreOffice
command or is a greyed placeholder; the placeholder lists in each design record say how.

## Licence

By contributing you agree that your changes are under the project's licences: MPL 2.0 for code and docs, and the
licences listed in [product/docs/licenses.md](product/docs/licenses.md) for bundled material.

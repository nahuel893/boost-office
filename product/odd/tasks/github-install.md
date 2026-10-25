# Feature: GitHub-ready repository and an install script

- **Status:** in progress, 2026-10-25 (started after Impress closed at 214697bc3; drafted by the controller on
  2026-10-23).
- **Locator:** `product/odd/tasks/github-install.md`
- **Engram mirror:** `odd/github-install/tasks`
- **Repo / branch:** `/mnt/games/libreoffice/core`, `feature/github-install`, from the tip of
  `feature/impress-ribbon-tabs` (214697bc3).
- **Map:** `.superpowers/sdd/2026-10-20-writer-impress-ribbons/task-GH1-report.md` (GH1, read-only, 2026-10-23).
- **SDD workspace:** `/mnt/games/libreoffice/core/.superpowers/sdd/2026-10-20-writer-impress-ribbons/` (briefs and
  reports; never committed).

## Objective

A reader who lands on the GitHub repository understands what Boost Office is, sees the three apps, and can install
it with one script on a Linux desktop from a built tree; the repository carries no stock LibreOffice automation
that works against Boost.

## Problem and why

The user (2026-10-22): "cuando termines con la triada prepara github y el script de instalacion". Today (GH1): the
README says only Calc is done; `.github/workflows/lockdown.yml` auto-closes every issue and PR and
`.github/FUNDING.yml` points to LibreOffice donations; there is no install path except the dev launcher, which
forces GTK colors and writes dev profiles; the Boost look lives in a dev profile script, not in default
configuration.

## Rulings (controller, 2026-10-23; the user asked for no questions and no review stops)

1. **Name:** "Boost Office" in the README, the installer, launchers and desktop entries. No configure-level
   rebranding now (`--with-product-name` and friends force a full rebuild); listed as a follow-up. The README carries
   a notice: not affiliated with or endorsed by The Document Foundation or Microsoft; LibreOffice is a trademark of
   The Document Foundation.
2. **Install from a build, do not build:** `product/install/install.sh` installs an existing `instdir`
   (default `./instdir`); `product/docs/building.md` explains the build (packages, the tracked flag sample
   `product/install/autogen.input.boost`, `product/dev/lo-make.sh`, time and disk).
3. **Defaults as a configuration layer, not a profile:** one generated `boost.xcd` in `<prefix>/share/registry/`
   (the `xcsxcu` layer reads every `*.xcd` there, `configmgr/source/components.cxx:783-784`) carrying the color
   schemes, the per-app tab accents and the mode defaults now written by `product/dev/profile.py` `build_items`
   (Tabbed Office for Calc, Writer and Impress, the Boost icon theme, the scheme, `LibreOfficeTheme`, the UI font,
   first-run and tips off). Generated from the same data as the dev profile so the two cannot drift. A spike (G0)
   proves it with a fresh profile and a screenshot before anything else is built on it. Fallback if the layer does
   not apply: the scheme `.oxt` as a bundled extension (`share/extensions`) plus first-run profile seeding by the
   launcher, only when the profile does not exist yet.
4. **Per-user install, no root:** prefix `~/.local/opt/boost-office` (override `--prefix`), launchers
   `boost-office`, `boost-writer`, `boost-calc`, `boost-impress` in `~/.local/bin`, desktop entries in
   `~/.local/share/applications`, an install manifest, and `product/install/uninstall.sh` that removes exactly the
   manifest's files (the user profile stays unless `--purge`).
5. **Own profile:** the launchers use `-env:UserInstallation=file://$HOME/.config/boost-office`, so Boost never
   touches an installed LibreOffice's profile.
6. **The user's GTK theme:** the launchers set no `GTK_THEME` and no private `XDG_CONFIG_HOME` (dev-only tricks).
7. **Theme:** `--theme light|dark`, default light (the look the screenshots were reviewed in).
8. **Fonts:** Inter goes into `<prefix>/share/fonts/truetype/` (LibreOffice's own font directory), not the user's
   font directories; the spike checks it is picked up.
9. **GitHub hygiene:** delete `.github/workflows/lockdown.yml` and `.github/FUNDING.yml`; add issue and PR
   templates; no CI workflow yet (which product tests need a built tree is not mapped; follow-up).
10. **README screenshots:** three ribbon crops (Calc, Writer, Impress, light) in `product/docs/screenshots/`, as the
    existing committed ones there. Evidence screenshots of tasks stay outside the repository.
11. **Agent logs stay** (`product/docs/superpowers/`, `product/odd/tasks/`: the design record); a scan removes the
    user's e-mail address and any credential if one is found.
12. **Delivery (updated 2026-10-25):** commits on `feature/github-install`, pushed after each task (the user: "pushea
    todo"); `dev` and `main` fast-forward to the closing commit when the feature closes, as Writer and Impress did.

## Scope

- In: `product/install/` (generator, install and uninstall scripts, desktop entry template, flag sample), their
  tests in `product/tests/`, the README and contributor docs, `.github/` cleanup and templates, three README
  screenshots, an e-mail and credential scan.
- Out: configure-level rebranding, packaging (deb, rpm, Flatpak), CI, Windows and macOS installs, building inside the
  installer.

## Constraints

- Never touch `/mnt/games/libreoffice/try-profile*`, the dev profile's owner settings, or the user's own `~/.config`
  and `~/.local` in tests and gates: scratch `HOME` and XDG directories only (G3).
- Builds only via `product/dev/lo-make.sh` with `PARALLELISM=2`; UITests only via `product/dev/uitest.sh`; one build,
  launch or screenshot at a time, only with at least 2500 MB available (the user plays games on this machine).
- Kill soffice only by PID; never `pkill -f` or `killall`.
- Python tools are stdlib only and run with `python3 -I`; shell scripts are POSIX `sh` or `bash` with `set -eu`.
- Commits: Conventional Commits, subject at most 79 characters, no AI attribution. Never commit `.superpowers` files,
  scratch trees, profiles or evidence screenshots.

## Acceptance criteria

- A fresh profile started from an installed tree shows Tabbed Office with the Boost pages, icons, scheme, per-app
  accent and the Inter UI font in Calc, Writer and Impress, with no dev profile script (G0, G3).
- `install.sh` installs into a prefix, writes launchers, desktop entries and a manifest; `uninstall.sh` removes
  exactly the manifest's files; both support `--dry-run` (G1, G3).
- The README describes Boost Office, shows the three apps and links install and build docs; `.github/` has no
  lockdown workflow or LibreOffice funding file (G2).
- The repository contains no user e-mail address or credential outside git metadata (G2).

## Delivery

Forecast: G0 ~250, G1 ~650, G2 ~700 (mostly docs), G3 ~50 authored changed lines (about 1650 in all). Strategy: the
repository has no review gate or pull request flow (the user pushes branches directly); work-unit commits per task
on this branch, pushed after each task, fast-forward at close (ruling 12). No chained pull requests.

## Tasks

| ID | Task | Route | Done | Commits | Checks |
|----|------|-------|------|---------|--------|
| G0 | Spike: a generated `boost.xcd` in a copy of `instdir` + a fresh profile shows Tabbed Office, Boost icons, scheme and accent in the three apps; Inter in `share/fonts/truetype` is used | delegated (opus; brief `task-G0-brief.md`) | [ ] | | |
| G1 | `product/install/`: the xcd generator (shared data with `profile.py`), `install.sh`, `uninstall.sh`, desktop entry template, flag sample; tests (generator output, install/uninstall into a temp prefix with `--dry-run` and for real) | delegated (opus) | [ ] | | |
| G2 | GitHub: README rewrite, `CONTRIBUTING.md`, `product/docs/install.md`, `building.md`, `licenses.md`, `product/README.md` index, `.github/` cleanup and templates, screenshots, e-mail scan | delegated (sonnet) | [ ] | | |
| G3 | Gate: a real install with a scratch `HOME` and XDG directories (never the user's own `~/.local`), launch each app from its launcher and desktop entry `Exec`, screenshots, uninstall leaves nothing | delegated (sonnet) | [ ] | | |

Route evidence: every task touches two or more non-trivial files or needs builds and screenshots, so each is
delegated to one writer (writer trigger); the parent keeps the spot checks (Impress ruling 22: the worker runs the
full unit suite once at the end; the controller checks the tree, processes and one screenshot).

## Checks

- Unit tests: `python3 -I -m unittest discover -s product/tests -t .` (987 at 214697bc3), once per task at the end.
- Generator: `python3 -I product/install/build_xcd.py --theme light|dark` output parses and matches `profile.py`.
- Visual: screenshots of fresh profiles from an installed tree, looked at.

## Progress / evidence

- 2026-10-25: branch created from 214697bc3; this document created from the 2026-10-23 draft; ruling 12 updated to
  the user's "pushea todo".

## Next step

G0 (delegated, opus; brief `task-G0-brief.md`): the `boost.xcd` spike.

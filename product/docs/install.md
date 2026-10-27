# Install Boost Office

`product/install/install.sh` installs a built tree (an `instdir`) for the current user. It needs no root, does not
build anything and does not touch an installed LibreOffice: Boost Office has its own prefix, launchers and profile.
There are two ways to get the tree: a release (no build), or your own build.

## From a release: one command

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash
```

`boost-office-install.sh` is a small script attached to each release on
<https://github.com/nahuel893/boost-office/releases>. It checks that the system is Linux x86_64 with a glibc at
least as new as the release needs (the floor `make-release.sh` measured on the shipped files, written inside the
script; an older system is refused before anything is downloaded, `--uninstall` is always allowed), `curl` or
`wget`, `tar` with `xz`, `python3` and enough free disk; downloads `boost-office-VERSION-linux-x86_64.tar.xz` from
the same release; checks the archive against the sha256 written inside the script (a mismatch installs nothing);
extracts it into a temp folder under `${XDG_CACHE_HOME:-~/.cache}`; runs the bundled `install.sh`; and deletes the
temp folder, also when something fails. The release archive carries the built tree, the installer and its data, with
the icon themes and the splash images prebuilt (no Pillow, no `rsvg-convert`).

Options go after `bash -s --`:

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash -s -- --theme dark
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash -s -- --uninstall
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash -s -- --uninstall --purge
```

- Every `install.sh` option below works (`--theme`, `--prefix`, `--bindir`, `--dry-run` ...).
- **Upgrade:** run the one-liner again. An install made by `install.sh` at the prefix is replaced (the script adds
  `--force` itself); the profile stays.
- **Uninstall:** `--uninstall` runs the `uninstall.sh` copy that every install keeps in its prefix
  (`~/.local/opt/boost-office/uninstall.sh`), so it downloads nothing; `--purge` also removes the profile, and
  `--prefix DIR` picks an install made with `--prefix DIR`. Running `<prefix>/uninstall.sh` directly does the same.
- The release notes (`product/release/notes-VERSION.md`, also on the release page) list the system it needs (the
  minimum glibc and the libraries) and the distributions it was tested on.

### Manual or offline install from the archive

Download `boost-office-VERSION-linux-x86_64.tar.xz` and `SHA256SUMS` from the release page, then:

```sh
sha256sum -c --ignore-missing SHA256SUMS
tar -xJf boost-office-0.1.2-linux-x86_64.tar.xz
boost-office-0.1.2/install.sh                 # takes every option below; no options: this folder's instdir
```

`install.sh` and `uninstall.sh` at the top of the folder run `product/install/install.sh` and `uninstall.sh` inside
it. The folder can be deleted after the install: the prefix keeps its own `uninstall.sh`. Release files are built
with `product/release/make-release.sh --instdir DIR --version X --out DIR`.

## From a build

1. Build the tree: [building.md](building.md). The result is `instdir/` in the repository root.
2. Install it:

   ```sh
   product/install/install.sh                  # light look
   product/install/install.sh --theme dark     # dark look
   ```

3. Start `boost-writer`, `boost-calc`, `boost-impress` or `boost-office` (the start center), or pick "Boost Writer"
   and the others from the desktop's application menu.

If the launchers are not found, add `~/.local/bin` to your `PATH`; the installer says so when it is missing.

## Requirements

- A built tree: `--instdir DIR` must contain `program/soffice` (a release archive carries one).
- `bash` and `python3`.
- Pillow and `rsvg-convert`, only when `images_boost.zip` and `images_boost_dark.zip` are not already in
  `--icons-dir` (default `product/icons/out`). They are then built there first.
- `rsvg-convert`, only when the splash images `intro.png` and `intro-highres.png` are not already in `--brand-dir`
  (default `product/brand/out`). They are then built there first (`product/brand/build_brand.py build`).
- About 0.7 GB in the prefix.
- `update-desktop-database` and `gtk-update-icon-cache` are used when present; failures are printed and ignored.

## Options of `install.sh`

| Option | Meaning | Default |
|---|---|---|
| `--instdir DIR` | The built tree to install; it must contain `program/soffice` | the `instdir` of the repository, or of the extracted release archive |
| `--prefix DIR` | Where the tree is copied | `~/.local/opt/boost-office` |
| `--bindir DIR` | Where the launchers `boost-office`, `boost-writer`, `boost-calc` and `boost-impress` go | `~/.local/bin` |
| `--theme THEME` | `light` or `dark`: the look of **new** profiles | `light` |
| `--icons-dir DIR` | Where `images_boost.zip` and `images_boost_dark.zip` come from; missing ones are built there | `product/icons/out` |
| `--brand-dir DIR` | Where the splash images `intro.png` and `intro-highres.png` come from; missing ones are built there, and ones that are not the stock pixel sizes (644 x 199, 990 x 254) are refused | `product/brand/out` |
| `--force` | Replace an earlier Boost Office install at `--prefix` (it is uninstalled first; the profile stays) | refuse |
| `--dry-run` | Print every action and write nothing | off |
| `--help` | Show the usage text | |

`--prefix`, `--bindir` and the XDG data directory must be plain paths: a space or a special character is refused.
Run `--dry-run` first to read the plan.

## What goes where

| What | Where |
|---|---|
| The program tree (a copy of `instdir`) | `<prefix>`, default `~/.local/opt/boost-office` |
| The Boost defaults (Tabbed Office, icons, color schemes, tab accents, Inter, the product name "Boost Office") | `<prefix>/share/registry/boost.xcd` |
| The Boost icon themes | `<prefix>/share/config/images_boost.zip` and `images_boost_dark.zip` |
| The Inter UI font | `<prefix>/share/fonts/truetype/` |
| The Boost brand, over the stock LibreOffice one of the copied tree: the splash, the About and Start Center logos, the splash's progress bar | `<prefix>/program/intro.png` and `intro-highres.png` (from `--brand-dir`), `<prefix>/program/shell/{about,logo,logo_inverted,logo-sc,logo-sc_inverted}.svg` (from `product/brand/shell`), the `Progress*` keys of `<prefix>/program/sofficerc` |
| Launchers | `<bindir>`, default `~/.local/bin`: `boost-office`, `boost-writer`, `boost-calc`, `boost-impress` |
| Desktop entries | `${XDG_DATA_HOME:-~/.local/share}/applications/boost-office-*.desktop` (start center, writer, calc, impress) |
| App icons | `${XDG_DATA_HOME:-~/.local/share}/icons/hicolor/<size>/apps/boost-office-*` |
| The install manifest | `<prefix>/.boost-office-install` |
| A copy of `uninstall.sh` (works without the repository or the release folder) | `<prefix>/uninstall.sh` |
| Your profile (settings, recent documents) | `~/.config/boost-office` |

- **The theme is a configuration layer, not a profile.** `boost.xcd` carries the defaults, so a new profile starts in
  Tabbed Office with the Boost look and no dev script.
- **Own profile.** The launchers start `soffice` with `-env:UserInstallation=file://$HOME/.config/boost-office`, so
  an installed LibreOffice keeps its own settings.
- **Your desktop's GTK theme.** The launchers set no `GTK_THEME` and no private `XDG_CONFIG_HOME`. The window frame,
  dialog title bars and some borders follow your GTK theme, and the UI font keeps the desktop's size.
- **Fonts need no `fc-cache`.** Inter sits in LibreOffice's own font folder inside the prefix, not in a user font
  folder, and the program loads it from there.

## The theme applies to new profiles only

A profile keeps the color scheme it first ran with. If `~/.config/boost-office` already exists, reinstalling with
another `--theme` does not switch it, and the installer says so. To switch an existing profile:

- choose **Boost Light** or **Boost Dark** in Tools > Options > Boost Office > Appearance, or
- move `~/.config/boost-office` away (or uninstall with `--purge`) and start again.

## Update

```sh
product/install/install.sh --force
```

`--force` runs the uninstall first (the profile stays), then installs the tree again. Without it, an existing
prefix is refused, and a directory without the install marker is never replaced.

## Uninstall

```sh
product/install/uninstall.sh                 # remove the install, keep the profile
product/install/uninstall.sh --purge         # also remove ~/.config/boost-office
product/install/uninstall.sh --prefix DIR    # an install made with --prefix DIR
product/install/uninstall.sh --dry-run       # print every action, remove nothing
~/.local/opt/boost-office/uninstall.sh       # the copy in the prefix: the same script, the same options
```

| Option | Meaning | Default |
|---|---|---|
| `--prefix DIR` | The install to remove | `~/.local/opt/boost-office` |
| `--purge` | Also remove the profile `~/.config/boost-office` (settings, recent documents) | keep |
| `--dry-run` | Print every action and remove nothing | off |
| `--help` | Show the usage text | |

It removes exactly the files and directories listed in `<prefix>/.boost-office-install`, then the prefix; a directory
the installer created is removed only when empty. It refuses a prefix without that manifest, and a manifest moved to
another prefix. The running apps may write caches (fontconfig, GVfs metadata under `${XDG_DATA_HOME:-~/.local/share}`)
that the installer did not create; those stay.

## Troubleshooting

| Symptom | Check |
|---|---|
| **A stock LibreOffice look** (a classic menu bar, stock icons and colors) | `boost.xcd` did not load. Check that `<prefix>/share/registry/boost.xcd` exists, and that you start `<bindir>/boost-<app>`: another `soffice` (the system's LibreOffice, or the build's own `instdir`) does not read the prefix's layer and uses its own profile. If the file is missing, reinstall with `--force`. If it is there, move `~/.config/boost-office` away: a profile that already stores its own choices overrides the layer |
| The look is right but light when you asked for dark (or the reverse) | The profile is older than the install: the theme applies to new profiles only (above) |
| `boost-writer: command not found` | `<bindir>` is not on `PATH`; add it, or start the launcher by its full path |
| `has no program/soffice` | `--instdir` is not a finished build: [building.md](building.md) |
| `exists and is not a Boost Office install` | `--prefix` holds something else. Pick another prefix; the installer never replaces it |
| An earlier install blocks the new one | Add `--force`, or run `uninstall.sh --prefix DIR` first |
| The window title or the splash says "LibreOfficeDev" | The program was not started from this install (another `soffice`, or the build's own `instdir`), or the install predates 0.1.1: reinstall with `--force`. Strings compiled into the program (the About dialog's copyright line, the window class `libreoffice-*`) keep the build's name |
| No desktop entry in the menu | Check that `boost-office-*.desktop` is in `${XDG_DATA_HOME:-~/.local/share}/applications`. The installer runs `update-desktop-database` when it is present |

To report a problem, use the bug template in `.github/ISSUE_TEMPLATE/` and say which of these you tried.

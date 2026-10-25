# Install Boost Office

`product/install/install.sh` installs a built tree (an `instdir`) for the current user. It needs no root, does not
build anything and does not touch an installed LibreOffice: Boost Office has its own prefix, launchers and profile.

## Quick path

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

- A built tree: `--instdir DIR` must contain `program/soffice`.
- `bash` and `python3`.
- Pillow and `rsvg-convert`, only when `images_boost.zip` and `images_boost_dark.zip` are not already in
  `--icons-dir` (default `product/icons/out`). They are then built there first.
- About 0.7 GB in the prefix.
- `update-desktop-database` and `gtk-update-icon-cache` are used when present; failures are printed and ignored.

## Options of `install.sh`

| Option | Meaning | Default |
|---|---|---|
| `--instdir DIR` | The built tree to install; it must contain `program/soffice` | the repository's `instdir` |
| `--prefix DIR` | Where the tree is copied | `~/.local/opt/boost-office` |
| `--bindir DIR` | Where the launchers `boost-office`, `boost-writer`, `boost-calc` and `boost-impress` go | `~/.local/bin` |
| `--theme THEME` | `light` or `dark`: the look of **new** profiles | `light` |
| `--icons-dir DIR` | Where `images_boost.zip` and `images_boost_dark.zip` come from; missing ones are built there | `product/icons/out` |
| `--force` | Replace an earlier Boost Office install at `--prefix` (it is uninstalled first; the profile stays) | refuse |
| `--dry-run` | Print every action and write nothing | off |
| `--help` | Show the usage text | |

`--prefix`, `--bindir` and the XDG data directory must be plain paths: a space or a special character is refused.
Run `--dry-run` first to read the plan.

## What goes where

| What | Where |
|---|---|
| The program tree (a copy of `instdir`) | `<prefix>`, default `~/.local/opt/boost-office` |
| The Boost defaults (Tabbed Office, icons, color schemes, tab accents, Inter) | `<prefix>/share/registry/boost.xcd` |
| The Boost icon themes | `<prefix>/share/config/images_boost.zip` and `images_boost_dark.zip` |
| The Inter UI font | `<prefix>/share/fonts/truetype/` |
| Launchers | `<bindir>`, default `~/.local/bin`: `boost-office`, `boost-writer`, `boost-calc`, `boost-impress` |
| Desktop entries | `${XDG_DATA_HOME:-~/.local/share}/applications/boost-office-*.desktop` (start center, writer, calc, impress) |
| App icons | `${XDG_DATA_HOME:-~/.local/share}/icons/hicolor/<size>/apps/boost-office-*` |
| The install manifest | `<prefix>/.boost-office-install` |
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

- choose **Boost Light** or **Boost Dark** in Tools > Options > LibreOfficeDev > Appearance, or
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
| The window title says "LibreOfficeDev" | Known: the product name is not rebranded |
| No desktop entry in the menu | Check that `boost-office-*.desktop` is in `${XDG_DATA_HOME:-~/.local/share}/applications`. The installer runs `update-desktop-database` when it is present |

To report a problem, use the bug template in `.github/ISSUE_TEMPLATE/` and say which of these you tried.

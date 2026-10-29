# Boost Office 0.1.3

The fourth preview of Boost Office: a fork of LibreOffice whose Writer, Calc and Impress use a Microsoft 365-like
ribbon. In this release the ribbon icons carry one soft accent fill, as Microsoft 365's icons do. It is a built tree
for Linux x86_64 that installs for your user, without root and without building anything.

**Supported: Arch Linux, Manjaro and other Arch-based or rolling distributions with glibc 2.44 or newer.** On an older
system (Ubuntu 24.04, Debian 12, Fedora 44 ...) the installer stops before downloading anything and says why.
Planned for 0.2.0: a portable build for Ubuntu, Debian and Fedora.

> Boost Office is not affiliated with or endorsed by The Document Foundation or Microsoft. LibreOffice is a trademark
> of The Document Foundation. Microsoft 365, Word, Excel and PowerPoint are trademarks of Microsoft.

## What changed since 0.1.2

- **The icons have one accent fill.** An icon with an object part now fills exactly that part (or one group of like
  parts) with a soft tint, Microsoft 365 style; the grey outline stays on top and still reads first. Paste fills the
  clipboard board and leaves the page white, Copy fills the front page, Cut the scissor rings, Format Painter the
  brush head; tables fill their header row, charts their bars, and folders, pictures, shapes, envelopes, locks and
  comment bubbles their body. 240 of the 461 Boost icons have a fill.
- **Colors by meaning:** yellow for clipboards, folders, brushes, highlights, locks and notes; blue for pages,
  documents, pictures, tables, charts and windows; green and red only where the object already means that. Light
  tints in Boost Light (`#FCE6AE`, `#CDE3F8`, `#D3EDCF`, `#F9D5D7`) and dark ones in Boost Dark (`#5E5034`,
  `#2D4560`, `#2F5A36`, `#5E373B`).
- **Line icons stay lines.** Arrows, letters (B, I, U ...), alignment and list lines, borders, the color-stripe
  buttons, symbols, gears, people, links and filters have no fill. The existing meaning badges (the green plus or
  check, the red cross, the conditional-formatting bars) keep their colors.
- **Disabled buttons stay grey.** A greyed button greys its fill too: for example Paste, Cut and Copy in a new Writer
  document with an empty clipboard and no selection show all grey, and get their fill as soon as they can be used.

The program (the same build as 0.1.2), the rounded ribbon card, the splash, logos, product name, Start Center and the
Inter UI font are unchanged.

## Install

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash
```

The script checks the system first: Linux x86_64, glibc 2.44 or newer, `curl` or `wget`, `tar` with `xz`,
`python3` and free disk. On an older glibc it refuses before downloading anything and exits with code 1:

```text
boost-office-install: Boost Office 0.1.3 needs glibc 2.44 or newer; this system has glibc 2.39.
This release runs only on rolling distributions such as Arch Linux or Manjaro. A build for
Ubuntu, Debian and Fedora is planned. To build Boost Office from source instead, see
https://github.com/nahuel893/boost-office/blob/main/product/docs/building.md
Nothing was downloaded or installed.
```

Then it downloads `boost-office-0.1.3-linux-x86_64.tar.xz` from this release, verifies its sha256 (written inside
the script; a mismatch installs nothing), extracts it into a temp folder, runs the bundled installer and deletes the
temp folder. Then start **Boost Writer**, **Boost Calc**, **Boost Impress** or **Boost Office** from the desktop
menu, or `boost-writer`, `boost-calc`, `boost-impress`, `boost-office` from `~/.local/bin`.

- Dark look: `... | bash -s -- --theme dark`. Every installer option works after `bash -s --` (`--prefix`,
  `--bindir`, `--dry-run` ...).
- Uninstall: `... | bash -s -- --uninstall` (add `--purge` to also remove the profile `~/.config/boost-office`). It
  downloads nothing and works on any glibc: it runs the `uninstall.sh` kept in `~/.local/opt/boost-office/`.

Manual or offline install, in three commands:

```sh
curl -LO https://github.com/nahuel893/boost-office/releases/download/v0.1.3/boost-office-0.1.3-linux-x86_64.tar.xz
tar -xJf boost-office-0.1.3-linux-x86_64.tar.xz
boost-office-0.1.3/install.sh
```

The manual path does not check the glibc version: on an older system the install succeeds but the programs fail to
start. The full guide (options, what goes where, troubleshooting) is `product/docs/install.md`, also inside the
archive.

## Upgrade from 0.1.2, 0.1.1 or 0.1.0

Run the same one-liner again:

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash
```

It finds the earlier install in `~/.local/opt/boost-office`, removes it and installs 0.1.3 in its place ("it is
replaced (the profile stays)"); your profile `~/.config/boost-office` and its settings stay. Close Boost Office
first. If you installed the earlier release with options (`--theme dark`, `--prefix DIR` ...), pass the same ones
again. The fills are part of the Boost icon themes: if you picked another icon theme in Tools > Options > Boost
Office > View, you keep it and its icons.

## What is in it

- **Writer** with Word's tabs: File, Home, Insert, Design, Layout, References, Mailings, Review, View, Help.
- **Calc** with Excel's tabs: File, Home, Insert, Page Layout, Formulas, Data, Review, View, Help.
- **Impress** with PowerPoint's tabs: File, Home, Insert, Design, Transitions, Animations, Slide Show, Review,
  View, Help.
- LibreOffice's Extension and Tools tabs stay. A greyed button is a placeholder for a Microsoft feature LibreOffice
  does not have yet; its tooltip says "(not available yet)".
- The ribbon drawn as a rounded card on the window color.
- The Boost Start Center, splash, logos and product name ("Boost Office" in window titles, dialogs and Tools >
  Options).
- Fluent-based Boost icon themes with one accent fill per icon (above), the Boost Light and Boost Dark color schemes
  with a tab accent per app, and the Inter UI font, all set as defaults by a configuration layer: a new profile
  starts with the Boost look.
- Its own prefix (`~/.local/opt/boost-office`), launchers, desktop entries and profile: an installed LibreOffice is
  not touched.

The program is built from the Boost Office sources at 401201c60 (LibreOffice 27.2 development code with the Boost
changes, including the Start Center and the ribbon card), an optimized build without debug code, the same build as
0.1.2; the icon themes come from the Boost Office sources of this release and the brand from the installer. English
only.

## Requirements

- **Linux x86_64 with glibc 2.44 or newer.** Measured again on the shipped files: the highest symbol version any of
  the 270 ELF files in `instdir` needs is `GLIBC_2.44` (`libsclo.so` and `libskialo.so`; several files need
  `GLIBC_2.43`), plus `GLIBCXX_3.4.32` and `CXXABI_1.3.15` from `libstdc++` (GCC 13 or newer). `make-release.sh`
  measures this floor on the shipped files and writes it into the installer, which checks it. The `libstdc++`
  version is not checked separately: every distribution with glibc 2.44 ships a newer one than GCC 13's.
- **GTK 3 and the usual desktop libraries**, the same as 0.1.2: `libgtk-3`, `libgdk-3`, `libgdk_pixbuf-2.0`,
  `libatk-1.0`, `libpango-1.0`, `libpangocairo-1.0`, `libharfbuzz`, `libcairo`, `libcairo-gobject`, `libglib-2.0`,
  `libgobject-2.0`, `libgio-2.0`, `libgmodule-2.0`, `libdconf`, `libdbus-1`, `libfontconfig`, `libfreetype`,
  `libX11`, `libX11-xcb`, `libXext`, `libXinerama`, `libXrandr`, `libXrender`, `libSM`, `libICE`, `libcups`, the NSS
  libraries (`libnss3`, `libnssutil3`, `libsmime3`, `libssl3`, `libnspr4`, `libplc4`, `libplds4`),
  `libgssapi_krb5`, `libz`, `libstdc++`, `libgcc_s`. Optional: GStreamer 1.0 (media playback) and `libpython3.14`
  (Python scripting).
- **For the splash:** an X11 display or Xwayland (the splash is drawn on X11, as in LibreOffice). On a Wayland
  session without Xwayland the programs start without a splash.
- **For the installer:** `bash`, `python3`, `tar` with `xz`, `curl` or `wget`, `sha256sum`, and about 1.5 GB free
  while installing (205 MB download, 720 MB extracted, about as much installed; the temp folder is removed at the
  end). The splash images and icon themes come prebuilt in the archive, so no image converter is needed.

## Tested

The one-command installer was run against a local copy of these release files (the same script and archive, served
by `python3 -m http.server`), except where the real 0.1.2 URL is named.

| System | Result |
|---|---|
| Manjaro (glibc 2.44), the build machine | Passed: the archive's `install.sh` into a scratch home; `boost-office` opened the Start Center; `boost-writer` and `boost-calc` opened with the filled icons on the ribbon card (measured `#FCE6AE` in the Format Painter brush head, `#CDE3F8` in Copy's front page and in the header row of Calc's Insert, Delete and Format cells buttons; Paste grey while the clipboard is empty); uninstalled with `--purge` |
| `archlinux:latest` container (glibc 2.44), clean | Passed: installed (exit code 0, checksum OK, no temp folder left); the installed icon themes `share/config/images_boost.zip` and `images_boost_dark.zip` have the same sha256 as in the archive; `boost-writer --headless --convert-to pdf` wrote a 20 KB PDF with no extra settings. Packages: `python xz gtk3 nss libcups dbus dconf libx11 libxinerama libxrandr libsm libice krb5 fontconfig cairo curl` |
| `archlinux:latest` container (glibc 2.44), upgrade | Passed: 0.1.2 installed with its published one-liner (`releases/download/v0.1.2/boost-office-install.sh`), then the 0.1.3 script with no options replaced it (exit code 0); afterwards both icon zips are the 0.1.3 ones (sha256 equal to the archive's, different from 0.1.2's), a headless PDF conversion still works, and `--uninstall --purge` (exit code 0) removed the prefix, the profile, the launchers and the desktop entries |
| `ubuntu:24.04` container (glibc 2.39) | Refused, exit code 1, with the message above. The local server saw only the request for the script: no archive download, no install, no `~/.cache` |
| Fedora 44 (glibc 2.43), Debian 12 (glibc 2.36) | Not tested: below the floor, refused like Ubuntu 24.04 |

## Known issues

- **Arch-based (glibc 2.44 or newer) only**, as above; the installer refuses older systems. Planned for 0.2.0: a
  portable build for Ubuntu, Debian and Fedora.
- **Other tab controls get the card too.** Under a Boost scheme every tab control LibreOffice draws itself, not only
  the ribbon, shows its pages as the same rounded card on the window color: for example the Basic IDE's dialogs.
- **The window color around the ribbon is the scheme's Inactive color.** Changing "Inactive" in Tools > Options >
  Boost Office > Appearance changes it. The card's corners are drawn without antialiasing.
- **Some compiled-in text still says LibreOffice.** The About dialog's copyright line ("Copyright © 2000–2026
  LibreOffice contributors.") and its Credits, Website, Release Notes and Build links point to LibreOffice; the window
  class and Wayland app_id are `libreoffice-writer`, `libreoffice-calc` and so on. The About dialog also keeps "Boost
  Office is derived from LibreOffice which was based on OpenOffice.org" on purpose.
- **No spelling dictionaries are bundled.** Install your distribution's Hunspell dictionaries (for example
  `hunspell-en_us`) for spell checking.
- **Linux x86_64 only**: no Windows, macOS or ARM build, and no distribution packages.
- **Unsigned:** the archive and the script carry no signature. Check them against `SHA256SUMS` from this release
  (`sha256sum -c --ignore-missing SHA256SUMS`); the script also checks the archive itself.

## Files

| File | What |
|---|---|
| `boost-office-install.sh` | The one-command installer (8 KB) |
| `boost-office-0.1.3-linux-x86_64.tar.xz` | The built tree, the installer and its data (with the splash images and icon themes prebuilt), the README, the install guide and the licences (205 MB) |
| `SHA256SUMS` | sha256 of both files |

```text
48e8ac614bdfb5058456d5be19ec19ffa5e1b1af9eb076aaa8b21a58da1af89d  boost-office-0.1.3-linux-x86_64.tar.xz
25cfd4dd6edfac9dcca495611e8e581edc8df4c2c6356d222f5703ef1a787d49  boost-office-install.sh
```

## Licences

Boost's own files are under the MPL 2.0, as most of LibreOffice; inherited code keeps its licences (`COPYING`,
`COPYING.MPL`, `COPYING.LGPL` and `instdir/LICENSE` in the archive). Inter is under the SIL Open Font License 1.1 and
the Fluent UI System Icons under MIT: see `product/docs/licenses.md` in the archive.

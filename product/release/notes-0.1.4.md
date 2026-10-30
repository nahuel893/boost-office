# Boost Office 0.1.4

The fifth preview of Boost Office: a fork of LibreOffice whose Writer, Calc and Impress use a Microsoft 365-like
ribbon. This release makes documents with very many styles fast to move around in: the Apply Style list no longer
refills on every cursor move. It is a built tree for Linux x86_64 that installs for your user, without root and
without building anything.

**Supported: Arch Linux, Manjaro and other Arch-based or rolling distributions with glibc 2.44 or newer.** On an older
system (Ubuntu 24.04, Debian 12, Fedora 44 ...) the installer stops before downloading anything and says why.
Planned for 0.2.0: a portable build for Ubuntu, Debian and Fedora.

> Boost Office is not affiliated with or endorsed by The Document Foundation or Microsoft. LibreOffice is a trademark
> of The Document Foundation. Microsoft 365, Word, Excel and PowerPoint are trademarks of Microsoft.

## What changed since 0.1.3

- **Moving the cursor no longer refills the Apply Style list.** Until now Calc, Writer, Impress and Draw rebuilt the
  whole list of the Apply Style box (the style name box in the Styles group) every time the cursor moved, even while
  nobody looked at it. Now the box only shows the name of the current style while you work, and builds its list when
  you click or tab into it or open its drop-down.
- **Documents with very many styles are fast again.** Spreadsheets saved by other programs can carry tens of
  thousands of cell styles. In an .xlsx file with 61,105 cell styles, each cursor move took about 1 second (0.9 s of
  work); now it takes about 0.03 s of work and feels instant. The same file also opens about 2 to 3 seconds sooner
  (ready to use after about 3.4 s instead of 6.2 s on the build machine). Ordinary documents are not slower.
- **The box behaves as before.** It always shows the style of the current selection, and when it opens, its list has
  the same styles in the same order as in 0.1.3, including styles you just created, renamed, hid or deleted. Typing a
  new name in the box still creates a style from the selection, and picking an entry still applies it, with the
  mouse or the keyboard. With two windows open, each box lists the styles of its own document.

The rest of the program (the ribbon, the rounded ribbon card, the icons with their accent fill, the splash, logos,
product name, Start Center and the Inter UI font) is unchanged.

## Install

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash
```

The script checks the system first: Linux x86_64, glibc 2.44 or newer, `curl` or `wget`, `tar` with `xz`,
`python3` and free disk. On an older glibc it refuses before downloading anything and exits with code 1:

```text
boost-office-install: Boost Office 0.1.4 needs glibc 2.44 or newer; this system has glibc 2.39.
This release runs only on rolling distributions such as Arch Linux or Manjaro. A build for
Ubuntu, Debian and Fedora is planned. To build Boost Office from source instead, see
https://github.com/nahuel893/boost-office/blob/main/product/docs/building.md
Nothing was downloaded or installed.
```

Then it downloads `boost-office-0.1.4-linux-x86_64.tar.xz` from this release, verifies its sha256 (written inside
the script; a mismatch installs nothing), extracts it into a temp folder, runs the bundled installer and deletes the
temp folder. Then start **Boost Writer**, **Boost Calc**, **Boost Impress** or **Boost Office** from the desktop
menu, or `boost-writer`, `boost-calc`, `boost-impress`, `boost-office` from `~/.local/bin`.

- Dark look: `... | bash -s -- --theme dark`. Every installer option works after `bash -s --` (`--prefix`,
  `--bindir`, `--dry-run` ...).
- Uninstall: `... | bash -s -- --uninstall` (add `--purge` to also remove the profile `~/.config/boost-office`). It
  downloads nothing and works on any glibc: it runs the `uninstall.sh` kept in `~/.local/opt/boost-office/`.

Manual or offline install, in three commands:

```sh
curl -LO https://github.com/nahuel893/boost-office/releases/download/v0.1.4/boost-office-0.1.4-linux-x86_64.tar.xz
tar -xJf boost-office-0.1.4-linux-x86_64.tar.xz
boost-office-0.1.4/install.sh
```

The manual path does not check the glibc version: on an older system the install succeeds but the programs fail to
start. The full guide (options, what goes where, troubleshooting) is `product/docs/install.md`, also inside the
archive.

## Upgrade from 0.1.3, 0.1.2, 0.1.1 or 0.1.0

Run the same one-liner again:

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash
```

It finds the earlier install in `~/.local/opt/boost-office`, removes it and installs 0.1.4 in its place ("it is
replaced (the profile stays)"); your profile `~/.config/boost-office` and its settings stay. Close Boost Office
first. If you installed the earlier release with options (`--theme dark`, `--prefix DIR` ...), pass the same ones
again. Nothing needs to be set: the faster Apply Style box works in every document and every color scheme.

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
- Fluent-based Boost icon themes with one accent fill per icon, the Boost Light and Boost Dark color schemes with a
  tab accent per app, and the Inter UI font, all set as defaults by a configuration layer: a new profile starts with
  the Boost look.
- Its own prefix (`~/.local/opt/boost-office`), launchers, desktop entries and profile: an installed LibreOffice is
  not touched.

The program is built from the Boost Office sources at 7cd6b02e1 (LibreOffice 27.2 development code with the Boost
changes), an optimized build without debug code. The only program change since 0.1.3 is the Apply Style box, in the
shared library `program/libsvxcorelo.so`; the icon themes come from the Boost Office sources of this release and the
brand from the installer. English only.

## Requirements

- **Linux x86_64 with glibc 2.44 or newer.** Measured again on the shipped files: the highest symbol version any of
  the 270 ELF files in `instdir` needs is `GLIBC_2.44` (`libsclo.so` and `libskialo.so`; several files need
  `GLIBC_2.43`), plus `GLIBCXX_3.4.32` and `CXXABI_1.3.15` from `libstdc++` (GCC 13 or newer). `make-release.sh`
  measures this floor on the shipped files and writes it into the installer, which checks it. The `libstdc++`
  version is not checked separately: every distribution with glibc 2.44 ships a newer one than GCC 13's.
- **GTK 3 and the usual desktop libraries**, the same as 0.1.3: `libgtk-3`, `libgdk-3`, `libgdk_pixbuf-2.0`,
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
by `python3 -m http.server`), except where the real 0.1.3 URL is named.

| System | Result |
|---|---|
| Manjaro (glibc 2.44), the build machine | Passed: the archive's `install.sh` into a scratch home; `boost-calc` opened the .xlsx file with 61,105 cell styles in 2.5 s; 40 cursor moves (down and right, as the arrow keys do) took a median of 0.03 s of work each (at most 0.04 s), and the Apply Style box showed the style of each new cell; uninstalled with `--purge` |
| `archlinux:latest` container (glibc 2.44), clean | Passed: installed (exit code 0, checksum OK, no temp folder left); the installed `program/libsvxcorelo.so` has the same sha256 as in the archive; `boost-writer --headless --convert-to pdf` wrote a 22 KB PDF with no extra settings. Packages: `python xz gtk3 nss libcups dbus dconf libx11 libxinerama libxrandr libsm libice krb5 fontconfig cairo curl` |
| `archlinux:latest` container (glibc 2.44), upgrade | Passed: 0.1.3 installed with its published one-liner (`releases/download/v0.1.3/boost-office-install.sh`), then the 0.1.4 script with no options replaced it (exit code 0); afterwards `program/libsvxcorelo.so` is the 0.1.4 one (sha256 equal to the archive's, different from 0.1.3's), a headless PDF conversion still works, and `--uninstall --purge` (exit code 0) removed the prefix, the profile, the launchers and the desktop entries |
| `ubuntu:24.04` container (glibc 2.39) | Refused, exit code 1, with the message above. The local server saw only the request for the script: no archive download, no install, no `~/.cache` |
| Fedora 44 (glibc 2.43), Debian 12 (glibc 2.36) | Not tested: below the floor, refused like Ubuntu 24.04 |

## Known issues

- **Opening the Apply Style drop-down is still slow in a document with tens of thousands of styles**, as in
  LibreOffice: the box then lists every style, and at about 61,000 cell styles that takes more than a minute. Moving
  around, typing and opening the file are fast; only opening that list is slow. Removing the unused styles from the
  file is the cure.
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
| `boost-office-0.1.4-linux-x86_64.tar.xz` | The built tree, the installer and its data (with the splash images and icon themes prebuilt), the README, the install guide and the licences (205 MB) |
| `SHA256SUMS` | sha256 of both files |

```text
083d784080b6b83a72aeb05a51a9e057ccc2e2e5e8f04d8f62f014c670679452  boost-office-0.1.4-linux-x86_64.tar.xz
860e0277e74f4c95cba4f66146e1264af343c6a0aa1b6e454bb1bd75b993d372  boost-office-install.sh
```

## Licences

Boost's own files are under the MPL 2.0, as most of LibreOffice; inherited code keeps its licences (`COPYING`,
`COPYING.MPL`, `COPYING.LGPL` and `instdir/LICENSE` in the archive). Inter is under the SIL Open Font License 1.1 and
the Fluent UI System Icons under MIT: see `product/docs/licenses.md` in the archive.

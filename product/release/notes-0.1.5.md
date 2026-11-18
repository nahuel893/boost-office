# Boost Office 0.1.5

The sixth preview of Boost Office: a fork of LibreOffice whose Writer, Calc and Impress use a Microsoft 365-like
ribbon. This release shows the open document's name in the ribbon's tab
row, as Microsoft 365 does, and the installer makes Boost the default application for office files. It is a built tree for Linux x86_64 that installs for your user, without root and
without building anything.

**Supported: Arch Linux, Manjaro and other Arch-based or rolling distributions with glibc 2.44 or newer.** On an older
system (Ubuntu 24.04, Debian 12, Fedora 44 ...) the installer stops before downloading anything and says why.
Planned for 0.2.0: a portable build for Ubuntu, Debian and Fedora.

> Boost Office is not affiliated with or endorsed by The Document Foundation or Microsoft. LibreOffice is a trademark
> of The Document Foundation. Microsoft 365, Word, Excel and PowerPoint are trademarks of Microsoft.

## What changed since 0.1.4

- **The document's name in the ribbon.** Writer, Calc and Impress show the name of the open file (for example
  `Budget.xlsx`, `Untitled 1`, or `Report.docx (read-only)`) in the free space of the ribbon's tab row, between the
  last tab and the menu button, centered on the window as far as that space allows. It follows Save As, a second
  window of the same document (`: 2`) and read-only mode. Each window shows its own document. When the window is too
  narrow the name is cut short with an ellipsis, and below about 80 px of free space it is hidden: the tabs never
  give up space for it.
- **Boost opens your office files.** The installer now makes Boost Writer, Calc and Impress the default
  applications for the Word, Excel, PowerPoint, OpenDocument and CSV file types they open (100 types), in
  `~/.config/mimeapps.list` (or `$XDG_CONFIG_HOME/mimeapps.list`). It remembers the application each type had
  before, and uninstalling gives every type back to it, unless you chose another application for that type since.
  Pass `--no-default-apps` to leave the defaults alone.

The rest of the program (the ribbon, the rounded ribbon card, the icons, the splash, logos, product name, Start
Center, the Inter UI font and the faster Apply Style box of 0.1.4) is unchanged.

## Install

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash
```

The script checks the system first: Linux x86_64, glibc 2.44 or newer, `curl` or `wget`, `tar` with `xz`,
`python3` and free disk. On an older glibc it refuses before downloading anything and exits with code 1:

```text
boost-office-install: Boost Office 0.1.5 needs glibc 2.44 or newer; this system has glibc 2.39.
This release runs only on rolling distributions such as Arch Linux or Manjaro. A build for
Ubuntu, Debian and Fedora is planned. To build Boost Office from source instead, see
https://github.com/nahuel893/boost-office/blob/main/product/docs/building.md
Nothing was downloaded or installed.
```

Then it downloads `boost-office-0.1.5-linux-x86_64.tar.xz` from this release, verifies its sha256 (written inside
the script; a mismatch installs nothing), extracts it into a temp folder, runs the bundled installer and deletes the
temp folder. Then start **Boost Writer**, **Boost Calc**, **Boost Impress** or **Boost Office** from the desktop
menu, or `boost-writer`, `boost-calc`, `boost-impress`, `boost-office` from `~/.local/bin`.

- Dark look: `... | bash -s -- --theme dark`. Every installer option works after `bash -s --` (`--prefix`,
  `--bindir`, `--dry-run` ...).
- Uninstall: `... | bash -s -- --uninstall` (add `--purge` to also remove the profile `~/.config/boost-office`). It
  downloads nothing and works on any glibc: it runs the `uninstall.sh` kept in `~/.local/opt/boost-office/`.

Manual or offline install, in three commands:

```sh
curl -LO https://github.com/nahuel893/boost-office/releases/download/v0.1.5/boost-office-0.1.5-linux-x86_64.tar.xz
tar -xJf boost-office-0.1.5-linux-x86_64.tar.xz
boost-office-0.1.5/install.sh
```

The manual path does not check the glibc version: on an older system the install succeeds but the programs fail to
start. The full guide (options, what goes where, troubleshooting) is `product/docs/install.md`, also inside the
archive.

## Upgrade from 0.1.4, 0.1.3, 0.1.2, 0.1.1 or 0.1.0

Run the same one-liner again:

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash
```

It finds the earlier install in `~/.local/opt/boost-office`, removes it and installs 0.1.5 in its place ("it is
replaced (the profile stays)"); your profile `~/.config/boost-office` and its settings stay. Close Boost Office
first. If you installed the earlier release with options (`--theme dark`, `--prefix DIR` ...), pass the same ones
again. Nothing needs to be set: the document's name shows in every window. The upgrade also makes Boost the default
application for office files; add `--no-default-apps` to the one-liner (`... | bash -s -- --no-default-apps`) to
keep your current defaults.

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

The program is built from the Boost Office sources at 6f9aeabd4 (LibreOffice 27.2 development code with the Boost
changes), an optimized build without debug code. The program changes since 0.1.4 are the document title, in the
shared libraries `program/libvcllo.so` (the tab row) and `program/libsfxlo.so` (the title it shows); the installer
change is in `install.sh`, `uninstall.sh` and the new `mimeapps.py`. The icon themes come from the Boost Office
sources of this release and the brand from the installer. English only.

## Requirements

- **Linux x86_64 with glibc 2.44 or newer.** `make-release.sh` measured the floor on this release's files again:
  2.44. As measured for 0.1.4, the highest symbol version any of the ELF files in `instdir` needs is `GLIBC_2.44` (`libsclo.so` and `libskialo.so`; several files need
  `GLIBC_2.43`), plus `GLIBCXX_3.4.32` and `CXXABI_1.3.15` from `libstdc++` (GCC 13 or newer). `make-release.sh`
  measures this floor on the shipped files and writes it into the installer, which checks it. The `libstdc++`
  version is not checked separately: every distribution with glibc 2.44 ships a newer one than GCC 13's.
- **GTK 3 and the usual desktop libraries**, the same as 0.1.4: `libgtk-3`, `libgdk-3`, `libgdk_pixbuf-2.0`,
  `libatk-1.0`, `libpango-1.0`, `libpangocairo-1.0`, `libharfbuzz`, `libcairo`, `libcairo-gobject`, `libglib-2.0`,
  `libgobject-2.0`, `libgio-2.0`, `libgmodule-2.0`, `libdconf`, `libdbus-1`, `libfontconfig`, `libfreetype`,
  `libX11`, `libX11-xcb`, `libXext`, `libXinerama`, `libXrandr`, `libXrender`, `libSM`, `libICE`, `libcups`, the NSS
  libraries (`libnss3`, `libnssutil3`, `libsmime3`, `libssl3`, `libnspr4`, `libplc4`, `libplds4`),
  `libgssapi_krb5`, `libz`, `libstdc++`, `libgcc_s`. Optional: GStreamer 1.0 (media playback) and `libpython3.14`
  (Python scripting).
- **For the splash:** an X11 display or Xwayland (the splash is drawn on X11, as in LibreOffice). On a Wayland
  session without Xwayland the programs start without a splash.
- **For the installer:** `bash`, `python3`, `tar` with `xz`, `curl` or `wget`, `sha256sum`, and about 1.5 GB free
  while installing (214 MB download, 720 MB extracted, about as much installed; the temp folder is removed at the
  end). The splash images and icon themes come prebuilt in the archive, so no image converter is needed.

## Tested

The one-command installer was run against a local copy of these release files (the same script and archive, served
by `python3 -m http.server`), except where the real 0.1.4 URL is named.

| System | Result |
|---|---|
| Manjaro (glibc 2.44), the build machine | Passed: the 15 document title UITests (Writer, Calc and Impress: a new document's name, Save As, read-only, two windows each showing their own document, and a narrow window where the tabs keep their space); the installer and release tests |
| `archlinux:latest` container (glibc 2.44), clean | Passed: installed (exit code 0, checksum OK); the installed `program/libsfxlo.so` and `program/libvcllo.so` have the same sha256 as in the archive; `~/.config/mimeapps.list` makes Boost the default for the 100 file types; `boost-writer --headless --convert-to pdf` wrote a PDF; `--uninstall --purge` (exit code 0) removed the prefix and the `mimeapps.list` the install had created. Packages: `python xz gtk3 nss libcups dbus dconf libx11 libxinerama libxrandr libsm libice krb5 fontconfig cairo curl` |
| `archlinux:latest` container (glibc 2.44), upgrade | Passed: with `text/csv` opening in another application, 0.1.4 installed with its published one-liner (`releases/download/v0.1.4/boost-office-install.sh`), then the 0.1.5 script with no options replaced it (exit code 0, "it is replaced (the profile stays)"); `program/libsfxlo.so` is the 0.1.5 one, `text/csv` opens with Boost Calc, a headless PDF conversion works, and `--uninstall --purge` (exit code 0) removed the prefix and gave `text/csv` back to the other application, leaving `mimeapps.list` as it was before |
| `ubuntu:24.04` and other systems below glibc 2.44 | Not tested again: the glibc check is unchanged since 0.1.4 and refuses them before downloading anything |

## Known issues

- **Big formula workbooks are slow to edit**, as in LibreOffice. In a workbook with hundreds of thousands of formulas
  that read whole columns (`VLOOKUP(...; Sheet!I:M; ...)`, `SUMIFS(Sheet!L:L; ...)`), deleting rows or running
  Data > Remove Duplicates on tens of thousands of rows can keep Calc busy for many minutes, even with AutoCalculate
  off. A fix for Remove Duplicates is in the works.
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
| `boost-office-0.1.5-linux-x86_64.tar.xz` | The built tree, the installer and its data (with the splash images and icon themes prebuilt), the README, the install guide and the licences (214 MB) |
| `SHA256SUMS` | sha256 of both files |

```text
7e913d7aceb584eb9a7760da03f95d1dd53105c9edc79c583198ecff15d11497  boost-office-0.1.5-linux-x86_64.tar.xz
4c3b4e3f0172acf22e74eb2857f4dcf03e04ebe16b9aa9de83dacc15a0e2bbc3  boost-office-install.sh
```

## Licences

Boost's own files are under the MPL 2.0, as most of LibreOffice; inherited code keeps its licences (`COPYING`,
`COPYING.MPL`, `COPYING.LGPL` and `instdir/LICENSE` in the archive). Inter is under the SIL Open Font License 1.1 and
the Fluent UI System Icons under MIT: see `product/docs/licenses.md` in the archive.

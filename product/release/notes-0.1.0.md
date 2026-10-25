# Boost Office 0.1.0

The first preview of Boost Office: a fork of LibreOffice whose Writer, Calc and Impress use a Microsoft 365-like
ribbon. This release is a built tree for Linux x86_64 that installs for your user, without root and without building
anything.

**Supported: Arch Linux, Manjaro and other Arch-based or rolling distributions with glibc 2.44 or newer.** On an older
system (Ubuntu 24.04, Debian 12, Fedora 44 ...) the installer stops before downloading anything and says why.
Planned: a portable build for Ubuntu, Debian and Fedora.

> Boost Office is not affiliated with or endorsed by The Document Foundation or Microsoft. LibreOffice is a trademark
> of The Document Foundation. Microsoft 365, Word, Excel and PowerPoint are trademarks of Microsoft.

## Install

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash
```

The script checks the system first: Linux x86_64, glibc 2.44 or newer, `curl` or `wget`, `tar` with `xz`,
`python3` and free disk. On an older glibc it refuses before downloading anything and exits with code 1:

```text
boost-office-install: Boost Office 0.1.0 needs glibc 2.44 or newer; this system has glibc 2.39.
This release runs only on rolling distributions such as Arch Linux or Manjaro. A build for
Ubuntu, Debian and Fedora is planned. To build Boost Office from source instead, see
https://github.com/nahuel893/boost-office/blob/main/product/docs/building.md
Nothing was downloaded or installed.
```

Then it downloads `boost-office-0.1.0-linux-x86_64.tar.xz` from this release, verifies its
sha256 (written inside the script; a mismatch installs nothing), extracts it into a temp folder, runs the bundled
installer and deletes the temp folder. Then start **Boost Writer**, **Boost Calc**, **Boost Impress** or **Boost
Office** from the desktop menu, or `boost-writer`, `boost-calc`, `boost-impress`, `boost-office` from
`~/.local/bin`.

- Dark look: `... | bash -s -- --theme dark`. Every installer option works after `bash -s --` (`--prefix`,
  `--bindir`, `--dry-run` ...).
- Upgrade: run the same command again; the profile stays.
- Uninstall: `... | bash -s -- --uninstall` (add `--purge` to also remove the profile `~/.config/boost-office`). It
  downloads nothing and works on any glibc: it runs the `uninstall.sh` kept in `~/.local/opt/boost-office/`.

Manual or offline install, in three commands:

```sh
curl -LO https://github.com/nahuel893/boost-office/releases/download/v0.1.0/boost-office-0.1.0-linux-x86_64.tar.xz
tar -xJf boost-office-0.1.0-linux-x86_64.tar.xz
boost-office-0.1.0/install.sh
```

The manual path does not check the glibc version: on an older system the install succeeds but the programs fail to
start. The full guide (options, what goes where, troubleshooting) is `product/docs/install.md`, also inside the
archive.

## What is in it

- **Writer** with Word's tabs: File, Home, Insert, Design, Layout, References, Mailings, Review, View, Help.
- **Calc** with Excel's tabs: File, Home, Insert, Page Layout, Formulas, Data, Review, View, Help.
- **Impress** with PowerPoint's tabs: File, Home, Insert, Design, Transitions, Animations, Slide Show, Review,
  View, Help.
- LibreOffice's Extension and Tools tabs stay. A greyed button is a placeholder for a Microsoft feature LibreOffice
  does not have yet; its tooltip says "(not available yet)".
- Fluent-based Boost icon themes, the Boost Light and Boost Dark color schemes with a tab accent per app, and the
  Inter UI font, all set as defaults by a configuration layer: a new profile starts with the Boost look.
- Its own prefix (`~/.local/opt/boost-office`), launchers, desktop entries and profile: an installed LibreOffice is
  not touched.

The tree is `main` at e9112a65f (LibreOffice 27.2 development code with the Boost changes), an optimized build
without debug code. English only.

## Requirements

- **Linux x86_64 with glibc 2.44 or newer.** Measured on the shipped files: the highest symbol version any of the
  270 ELF files in `instdir` needs is `GLIBC_2.44` (`cosh` and `sinh` in `libsclo.so` and `libskialo.so`; several
  files need `GLIBC_2.43`), plus `GLIBCXX_3.4.32` and `CXXABI_1.3.15` from `libstdc++` (GCC 13 or newer). The tree
  was built on a system with glibc 2.44, so older distributions cannot load it (see below). `make-release.sh`
  measures this floor on the shipped files and writes it into the installer, which checks it. The `libstdc++` version
  is not checked separately: every distribution with glibc 2.44 ships a newer one than GCC 13's.
- **GTK 3 and the usual desktop libraries.** What the program needs from the system, beyond what it ships:
  `libgtk-3`, `libgdk-3`, `libgdk_pixbuf-2.0`, `libatk-1.0`, `libpango-1.0`, `libpangocairo-1.0`, `libharfbuzz`,
  `libcairo`, `libcairo-gobject`, `libglib-2.0`, `libgobject-2.0`, `libgio-2.0`, `libgmodule-2.0`, `libdconf`,
  `libdbus-1`, `libfontconfig`, `libfreetype`, `libX11`, `libX11-xcb`, `libXext`, `libXinerama`, `libXrandr`,
  `libXrender`, `libSM`, `libICE`, `libcups`, the NSS libraries (`libnss3`, `libnssutil3`, `libsmime3`, `libssl3`,
  `libnspr4`, `libplc4`, `libplds4`), `libgssapi_krb5`, `libz`, `libstdc++`, `libgcc_s`. Optional: GStreamer 1.0
  (media playback) and `libpython3.14` (Python scripting).
- **For the installer:** `bash`, `python3`, `tar` with `xz`, `curl` or `wget`, `sha256sum`, and about 1.5 GB free
  while installing (205 MB download, 719 MB extracted, 717 MB installed; the temp folder is removed at the end).

## Tested

The one-command installer was run against a local copy of these release files (the same script and archive,
served by `python3 -m http.server`).

| System | Result |
|---|---|
| Manjaro (glibc 2.44), the build machine | Passed: installed; Writer started from `boost-writer` with the Boost ribbon and the light look (Calc and Impress were checked the same way on an earlier build of this archive with the same program tree); upgraded by running the command again; uninstalled with `--uninstall --purge`, leaving the home exactly as before |
| `archlinux:latest` container (glibc 2.44) | Passed: installed; `boost-writer`, `boost-calc` and `boost-impress --headless --convert-to pdf` turned `.odt`, `.docx`, `.ods`, `.xlsx`, `.odp` and `.pptx` samples into PDFs (15 to 33 KB each) with no extra settings; uninstalled. Packages: `python xz gtk3 nss libcups dbus dconf libx11 libxinerama libxrandr libsm libice krb5 fontconfig cairo` |
| `ubuntu:24.04` container (glibc 2.39) | Refused, exit code 1, with the message above. The local server saw only the request for the script: no archive download, no install, nothing in `~/.cache`. Before the check existed, the program installed there failed to start: ``libc.so.6: version `GLIBC_2.43' not found (required by .../program/libcurl.so.4)`` and ``libm.so.6: version `GLIBC_2.44' not found`` |
| `fedora:latest` container (Fedora 44, glibc 2.43) | Before the check existed, the program installed there failed to start: ``libm.so.6: version `GLIBC_2.44' not found (required by .../program/libskialo.so)``. The installer now refuses it (2.43 is older than 2.44) |
| Debian 12 (glibc 2.36) | Not tested: below the floor, refused like Ubuntu 24.04 |

## Known issues

- **Arch-based (glibc 2.44 or newer) only**, as above; the installer refuses older systems. Planned: a portable
  build for Ubuntu, Debian and Fedora.
- **The window titles say "LibreOfficeDev"**: the product name is not rebranded yet.
- **The Start Center is LibreOffice's stock one** (`boost-office`); its redesign is not in this release.
- **No spelling dictionaries are bundled.** Install your distribution's Hunspell dictionaries (for example
  `hunspell-en_us`) for spell checking.
- **Linux x86_64 only**: no Windows, macOS or ARM build, and no distribution packages.
- **Unsigned:** the archive and the script carry no signature. Check them against `SHA256SUMS` from this release
  (`sha256sum -c --ignore-missing SHA256SUMS`); the script also checks the archive itself.

## Files

| File | What |
|---|---|
| `boost-office-install.sh` | The one-command installer (8 KB) |
| `boost-office-0.1.0-linux-x86_64.tar.xz` | The built tree, the installer and its data, the README, the install guide and the licences (205 MB) |
| `SHA256SUMS` | sha256 of both files |

```text
4269e2e033ca4346298a6d95de0611967d19ffd7faef2bf6eefe024361efb035  boost-office-0.1.0-linux-x86_64.tar.xz
406b12770a34bd0a639aac762d71b52c9053fd8f5e7cb9e9a8b29109228b84a8  boost-office-install.sh
```

## Licences

Boost's own files are under the MPL 2.0, as most of LibreOffice; inherited code keeps its licences (`COPYING`,
`COPYING.MPL`, `COPYING.LGPL` and `instdir/LICENSE` in the archive). Inter is under the SIL Open Font License 1.1 and
the Fluent UI System Icons under MIT: see `product/docs/licenses.md` in the archive.

# Boost Office 0.1.0

The first preview of Boost Office: a fork of LibreOffice whose Writer, Calc and Impress use a Microsoft 365-like
ribbon. This release is a built tree for Linux x86_64 that installs for your user, without root and without building
anything.

> Boost Office is not affiliated with or endorsed by The Document Foundation or Microsoft. LibreOffice is a trademark
> of The Document Foundation. Microsoft 365, Word, Excel and PowerPoint are trademarks of Microsoft.

## Install

```sh
curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash
```

The script checks the system, downloads `boost-office-0.1.0-linux-x86_64.tar.xz` from this release, verifies its
sha256 (written inside the script; a mismatch installs nothing), extracts it into a temp folder, runs the bundled
installer and deletes the temp folder. Then start **Boost Writer**, **Boost Calc**, **Boost Impress** or **Boost
Office** from the desktop menu, or `boost-writer`, `boost-calc`, `boost-impress`, `boost-office` from
`~/.local/bin`.

- Dark look: `... | bash -s -- --theme dark`. Every installer option works after `bash -s --` (`--prefix`,
  `--bindir`, `--dry-run` ...).
- Upgrade: run the same command again; the profile stays.
- Uninstall: `... | bash -s -- --uninstall` (add `--purge` to also remove the profile `~/.config/boost-office`). It
  downloads nothing: it runs the `uninstall.sh` kept in `~/.local/opt/boost-office/`.

Manual or offline install, in three commands:

```sh
curl -LO https://github.com/nahuel893/boost-office/releases/download/v0.1.0/boost-office-0.1.0-linux-x86_64.tar.xz
tar -xJf boost-office-0.1.0-linux-x86_64.tar.xz
boost-office-0.1.0/install.sh
```

The full guide (options, what goes where, troubleshooting) is `product/docs/install.md`, also inside the archive.

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
  was built on a system with glibc 2.44, so older distributions cannot load it (see below).
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

The one-command installer was run against a local copy of these release files (same script, same archive).

| System | Result |
|---|---|
| Manjaro (glibc 2.44), the build machine | Installed, upgraded by running it again, uninstalled with `--uninstall --purge` (the home left exactly as before). Writer, Calc and Impress started from the launchers with the Boost ribbons and the light look; the six sample files were made with its headless converter (HTML, CSV and flat ODP to `.odt`, `.docx`, `.ods`, `.xlsx`, `.odp`, `.pptx`) |
| `archlinux:latest` container (glibc 2.44) | Passed: installed; `.odt`, `.docx`, `.ods`, `.xlsx`, `.odp` and `.pptx` converted to PDF (headless, see the known issue on `SAL_USE_VCLPLUGIN`); uninstalled. Packages: `python xz gtk3 nss libcups dbus dconf libx11 libxinerama libxrandr libsm libice krb5 fontconfig cairo` |
| `fedora:latest` container (Fedora 44, glibc 2.43) | **Does not run.** The installer works, then the program stops at start: ``libm.so.6: version `GLIBC_2.44' not found (required by .../program/libskialo.so)``. Packages: `python3 xz tar gtk3 nss cups-libs dbus-libs dconf libX11-xcb libXinerama libXrandr libSM libICE krb5-libs fontconfig cairo shadow-utils util-linux` |
| `ubuntu:24.04` container (glibc 2.39) | **Does not run**, for the same reason: ``libc.so.6: version `GLIBC_2.43' not found (required by .../program/libcurl.so.4)`` and ``libm.so.6: version `GLIBC_2.44' not found``. Packages: `curl ca-certificates python3 xz-utils libgtk-3-0t64 libnss3 libcups2t64 libdbus-1-3 libdconf1 libx11-xcb1 libxinerama1 libxrandr2 libsm6 libice6 libgssapi-krb5-2 libfontconfig1 libcairo2` |
| Debian 12 (glibc 2.36) | Not tested: below the glibc floor, so it fails like Ubuntu 24.04 |

Rolling distributions that already ship glibc 2.44 (Arch Linux and its derivatives such as Manjaro) can run this
release. Ubuntu 24.04, Debian 12 and Fedora 44 cannot; a build on an older base system is needed for them and is
planned for a later release.

## Known issues

- **A recent glibc only** (2.44 or newer), as above.
- **The window titles say "LibreOfficeDev"**: the product name is not rebranded yet.
- **The Start Center is LibreOffice's stock one** (`boost-office`); its redesign is not in this release.
- **No spelling dictionaries are bundled.** Install your distribution's Hunspell dictionaries (for example
  `hunspell-en_us`) for spell checking.
- **Headless conversion without a display:** the launchers select the GTK 3 interface, so `boost-writer --headless
  --convert-to pdf FILE` on a machine with no display prints `X11 error: Can't open display` and writes nothing. Run
  it as `SAL_USE_VCLPLUGIN=svp boost-writer --headless --convert-to pdf FILE`.
- **Linux x86_64 only**: no Windows, macOS or ARM build, and no distribution packages.
- **Unsigned:** the archive and the script carry no signature. Check them against `SHA256SUMS` from this release
  (`sha256sum -c --ignore-missing SHA256SUMS`); the script also checks the archive itself.

## Files

| File | What |
|---|---|
| `boost-office-install.sh` | The one-command installer (6 KB) |
| `boost-office-0.1.0-linux-x86_64.tar.xz` | The built tree, the installer and its data, the README, the install guide and the licences (205 MB) |
| `SHA256SUMS` | sha256 of both files |

```text
4a148c18cf7de400a753f1247b9a836fbd8d0a57275bd03e4451fade36c1d373  boost-office-0.1.0-linux-x86_64.tar.xz
4fd0841c8b9a74125f3f6e1bade11eabeb24b35c401157278bc2cbfe51372b27  boost-office-install.sh
```

## Licences

Boost's own files are under the MPL 2.0, as most of LibreOffice; inherited code keeps its licences (`COPYING`,
`COPYING.MPL`, `COPYING.LGPL` and `instdir/LICENSE` in the archive). Inter is under the SIL Open Font License 1.1 and
the Fluent UI System Icons under MIT: see `product/docs/licenses.md` in the archive.

# Build Boost Office

Boost Office is LibreOffice's source tree plus the changes in this repository, so you build it as you would
LibreOffice, with a smaller set of flags and a memory cap. The result is `instdir/`; then
[install.md](install.md) installs it.

## Quick path

1. Install the packages below.
2. Copy the flag sample and configure:

   ```sh
   cp product/install/autogen.input.boost autogen.input
   ./autogen.sh
   ```

3. Build, under the memory cap:

   ```sh
   PARALLELISM=2 product/dev/lo-make.sh
   ```

4. Install: `product/install/install.sh` (see [install.md](install.md)).

## Packages

LibreOffice's own dependency list is the reference:
[Building on Linux](https://wiki.documentfoundation.org/Development/BuildingOnLinux). `./autogen.sh` stops and names
what it misses, so the lists below are a starting point, not a complete list.

| | Arch / Manjaro | Debian / Ubuntu |
|---|---|---|
| Toolchain | `base-devel git ccache` | `build-essential git ccache` |
| Most build dependencies | the packages named by `autogen.sh` | `sudo apt build-dep libreoffice` (needs `deb-src` enabled) |
| GTK 3 backend | `gtk3` | `libgtk-3-dev` |
| Build helpers | `nasm gperf zip unzip libxslt` | `nasm gperf zip unzip libxslt1-dev` |
| Fonts, printing | `fontconfig cups` | `libfontconfig1-dev libcups2-dev` |
| Boost tools: python3 with Pillow | `python python-pillow` | `python3 python3-pil` |
| Boost tools: `rsvg-convert` | `librsvg` | `librsvg2-bin` |
| Memory cap in `lo-make.sh` | `systemd` | `systemd` |

The screenshot tool `product/dev/shot-tab.sh` also needs `sway`, `grim` and `jq`; the dev launchers assume the
`adw-gtk3` and `adw-gtk3-dark` GTK themes. You do not need them to build or install.

## The flags

`product/install/autogen.input.boost` is the sample the Boost builds use; each block is commented. In short:

| Flags | Why |
|---|---|
| `--enable-option-checking=fatal` | A misspelled flag fails instead of being ignored |
| `--enable-gtk3`, `--disable-gtk4`, `--disable-qt5`, `--disable-qt6`, `--disable-kf5`, `--disable-kf6` | The Boost look and the screenshots are GTK 3 only |
| `--without-java`, `--without-help`, `--without-helppack-integration`, `--without-myspell-dicts`, `--without-doxygen`, `--disable-firebird-sdbc`, `--disable-postgresql-sdbc` | Leave out what Boost does not use, to shorten the build |

Parallelism is not in the sample: `lo-make.sh` passes it. A machine with more memory can add
`--with-parallelism=N` to its own `autogen.input`. `autogen.input` is ignored by git.

## `product/dev/lo-make.sh`

It runs `make` in the checkout inside a `systemd-run --user --scope` with `MemoryHigh=6G`, `MemoryMax=7G`,
`MemorySwapMax=1G` and `nice -n 10`, because an unrestricted build with ten jobs froze a 14 GB desktop. Extra
arguments go to `make`:

```sh
PARALLELISM=2 product/dev/lo-make.sh                 # a quiet build while you work
product/dev/lo-make.sh                               # default PARALLELISM=6
product/dev/lo-make.sh UITest_calc_tests             # a target
```

## Time, memory and disk

| | Measured |
|---|---|
| Peak memory | about 4.8 GB at `PARALLELISM=6` (the cap is 7 GB) |
| `instdir/` (the result) | about 0.7 GB |
| `workdir/` (objects and intermediate files) | about 4.7 GB |
| ccache | about 0.6 GB, and it grows |
| Time | not recorded: a first LibreOffice build is long; later builds rebuild only what changed |

Lower `PARALLELISM` if the machine is also your desktop.

## Extra tools

- `python3` with Pillow and `rsvg-convert` build the icon themes (`product/icons/build_theme.py`). `install.sh` builds
  `images_boost.zip` and `images_boost_dark.zip` itself when they are missing from `product/icons/out`.
- The tools are Python 3 standard library plus Pillow; run them with `python3 -I`.
- The color scheme extension and the install layer come from `product/themes/build_schemes.py` and
  `product/install/build_xcd.py`; `install.sh` runs them.

## Check the build

```sh
python3 -I -m unittest discover -s product/tests -t .      # unit tests
product/dev/calc.sh light --profile ~/boost-profile         # start the dev build's Calc, light look
```

`product/dev/office.sh calc|writer|impress light|dark` starts each app with a dev profile that
`product/dev/profile.py` rewrites on every run. Pass `--profile DIR` with a directory of its own, so no other profile
is touched.

#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Package a built Boost Office tree (an instdir) as the release archive boost-office-VERSION-linux-x86_64.tar.xz,
# the one-command installer boost-office-install.sh (the archive's sha256 inside) and SHA256SUMS for both. The archive holds one folder, boost-office-VERSION/, laid out like the repository: install.sh
# and uninstall.sh at the top, instdir/, and the files the installer reads from product/ and sysui/ (the icon
# zips prebuilt), so ./install.sh with no arguments installs the bundled instdir. See --help.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
STOCK_APPS="startcenter writer calc impress"
BOOTSTRAP=boost-office-install.sh
# Repository files the bundle carries: the installer and what it reads, the README, the install guide and the
# licence texts. The fonts and the stock desktop entries and app icons are added below.
FILES=(
    README.md COPYING COPYING.MPL COPYING.LGPL
    product/__init__.py product/dev/__init__.py product/dev/profile.py
    product/install/__init__.py product/install/install.sh product/install/uninstall.sh
    product/install/build_xcd.py product/install/boost-office.desktop.in
    product/icons/__init__.py product/icons/build_theme.py product/icons/manifest.json product/icons/fluent/LICENSE
    product/themes/__init__.py product/themes/build_schemes.py product/themes/palette.json
    product/docs/install.md product/docs/licenses.md
)

usage() {
    cat <<EOF
Usage: make-release.sh --instdir DIR --version VERSION --out DIR [--icons-dir DIR]

Package a built Boost Office tree as boost-office-VERSION-linux-x86_64.tar.xz, boost-office-install.sh (the
one-command installer for that archive) and SHA256SUMS in --out.

Options:
  --instdir DIR    the built tree; it must contain program/soffice (its user/ profile and .lock are left out)
  --version X      the release version, for example 0.1.0
  --out DIR        where the three files are written (created when missing)
  --icons-dir DIR  where images_boost.zip and images_boost_dark.zip come from; when they are missing they are
                   built there first, which needs Pillow and rsvg-convert (default: product/icons/out)
  -h, --help       show this help

The glibc floor (the highest GLIBC_ symbol version the shipped files need, measured with readelf) goes
into boost-office-install.sh, which refuses an older system before downloading anything.
EOF
}

die() { echo "make-release.sh: $*" >&2; exit 1; }
bad() { echo "make-release.sh: $*" >&2; echo "Try 'make-release.sh --help'." >&2; exit 2; }
say() { printf '%s\n' "$*"; }

instdir=""
version=""
out=""
icons="$repo/product/icons/out"
while [ $# -gt 0 ]; do
    case "$1" in
    --instdir|--version|--out|--icons-dir)
        [ $# -ge 2 ] || bad "$1 needs a value"
        case "$1" in
        --instdir) instdir=$2 ;;
        --version) version=$2 ;;
        --out) out=$2 ;;
        --icons-dir) icons=$2 ;;
        esac
        shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) bad "unknown option: $1" ;;
    esac
done
[ -n "$instdir" ] || bad "--instdir is required"
[ -n "$out" ] || bad "--out is required"
case "$version" in
"") bad "--version is required" ;;
[!0-9]* | *[!0-9A-Za-z.+-]*) bad "--version must start with a digit and hold only letters, digits, '.', '+' and '-'" ;;
esac

# --- checks: nothing is written before they pass -------------------------------------------------------
instdir=$(realpath -ms -- "$instdir")
out=$(realpath -ms -- "$out")
icons=$(realpath -ms -- "$icons")
[ -f "$instdir/program/soffice" ] || die "$instdir has no program/soffice: pass a built tree to --instdir"
for rel in "${FILES[@]}"; do
    [ -f "$repo/$rel" ] || die "$repo/$rel is missing"
done
bootstrap_in="$here/boost-office-install.sh.in"
[ -f "$bootstrap_in" ] || die "$bootstrap_in is missing"
build_icons=0
[ -f "$icons/images_boost.zip" ] && [ -f "$icons/images_boost_dark.zip" ] || build_icons=1
if [ "$build_icons" = 1 ]; then
    python3 -I -c "import PIL" 2>/dev/null \
        || die "the icon zips are not in $icons, and building them needs Pillow (python3 -m pip install Pillow)"
    command -v rsvg-convert >/dev/null \
        || die "the icon zips are not in $icons, and building them needs rsvg-convert (librsvg)"
fi
command -v xz >/dev/null || die "xz is needed"
command -v readelf >/dev/null || die "readelf (binutils) is needed to measure the glibc floor"

top="boost-office-$version"
name="$top-linux-x86_64.tar.xz"
archive="$out/$name"

# --- the icon zips -------------------------------------------------------------------------------------
if [ "$build_icons" = 1 ]; then
    say "build the icon zips into $icons (Pillow, rsvg-convert)"
    python3 -I "$repo/product/icons/build_theme.py" build --out "$icons" >/dev/null
fi

# --- the bundle, staged in a temp dir inside --out -----------------------------------------------------
mkdir -p -- "$out"
stage=$(mktemp -d "$out/.boost-office-release.XXXXXX")
trap 'rm -rf -- "$stage" "$archive.part"' EXIT
bundle="$stage/$top"
mkdir -- "$bundle"

say "copy $instdir into $top/instdir (without user/ and .lock)"
mkdir -- "$bundle/instdir"
cp -a -- "$instdir/." "$bundle/instdir/"
rm -rf -- "$bundle/instdir/user" "$bundle/instdir/.lock"
chmod 755 "$bundle/instdir"

say "copy the installer, its data, the README, the install guide and the licences"
files=("${FILES[@]}")
for path in "$repo"/product/fonts/inter/*; do
    files+=("${path#"$repo"/}")
done
for app in $STOCK_APPS; do
    files+=("sysui/desktop/menus/$app.desktop")
    for path in "$repo"/sysui/desktop/icons/hicolor/*/apps/"$app".png "$repo"/sysui/desktop/icons/hicolor/*/apps/"$app".svg; do
        [ ! -f "$path" ] || files+=("${path#"$repo"/}")
    done
done
(cd "$repo" && cp -p --parents -- "${files[@]}" "$bundle/")

mkdir -p -- "$bundle/product/icons/out"
cp -- "$icons/images_boost.zip" "$icons/images_boost_dark.zip" "$bundle/product/icons/out/"

# install.sh and uninstall.sh at the top run the real scripts, which find the bundle's instdir, icon zips and
# data through their own path, as in the repository.
for script in install.sh uninstall.sh; do
    cat >"$bundle/$script" <<EOF
#!/bin/sh
# Boost Office $version: run product/install/$script from this folder. See ./$script --help.
here=\$(cd -- "\$(dirname -- "\$0")" && pwd)
exec bash "\$here/product/install/$script" "\$@"
EOF
    chmod 755 "$bundle/$script"
done

# --- the glibc floor: the highest GLIBC_ symbol version any shipped file needs (readelf's version needs) --
glibc_needs() {
    find "$1" -type f -print0 | LC_ALL=C xargs -0 readelf -V -W 2>/dev/null || true
}
floor=$(glibc_needs "$bundle/instdir" | sed -n 's/.*Name: GLIBC_\([0-9][0-9.]*\).*/\1/p' | sort -uV | tail -n 1)
[ -n "$floor" ] || die "no file in $instdir needs a GLIBC_ symbol version: is it a built tree?"
say "the shipped files need glibc $floor or newer"

# --- the archive, the one-command installer and the checksums ------------------------------------------
tree_mb=$(du -sm -- "$bundle" | cut -f1)
say "write $archive"
tar -C "$stage" --sort=name --owner=0 --group=0 --numeric-owner -cf - "$top" | xz -T0 -6 -c >"$archive.part"
mv -f -- "$archive.part" "$archive"
sha=$(sha256sum -- "$archive" | cut -d' ' -f1)
archive_mb=$((($(stat -c %s -- "$archive") + 1048575) / 1048576))

say "write $out/$BOOTSTRAP (version $version, glibc $floor, sha256 $sha)"
text=$(<"$bootstrap_in")
text=${text//@VERSION@/$version}
text=${text//@SHA256@/$sha}
text=${text//@ARCHIVE_MB@/$archive_mb}
text=${text//@TREE_MB@/$tree_mb}
text=${text//@GLIBC_FLOOR@/$floor}
printf '%s\n' "$text" >"$out/$BOOTSTRAP"
chmod 755 "$out/$BOOTSTRAP"

(cd "$out" && sha256sum -- "$name" "$BOOTSTRAP" >SHA256SUMS)
say "write $out/SHA256SUMS"
say "$(du -h -- "$archive" | cut -f1)  $sha  $archive"

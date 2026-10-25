#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Remove a Boost Office install made by install.sh: exactly the files and directories its manifest lists,
# then the prefix. The profile stays unless --purge. See --help.
set -euo pipefail

MARKER="# boost-office-install 1"
MANIFEST=.boost-office-install

usage() {
    cat <<EOF
Usage: uninstall.sh [options]

Remove a Boost Office install made by install.sh: exactly the files and directories listed in its manifest
(<prefix>/$MANIFEST), then the prefix. Directories it created are removed only when empty.

Options:
  --prefix DIR  the install to remove (default: ~/.local/opt/boost-office)
  --purge       also remove the profile ~/.config/boost-office (settings, recent documents)
  --dry-run     print every action and remove nothing
  -h, --help    show this help
EOF
}

die() { echo "uninstall.sh: $*" >&2; exit 1; }
bad() { echo "uninstall.sh: $*" >&2; echo "Try 'uninstall.sh --help'." >&2; exit 2; }
say() { printf '%s\n' "$*"; }

prefix="$HOME/.local/opt/boost-office"
purge=0
dry=0
while [ $# -gt 0 ]; do
    case "$1" in
    --prefix) [ $# -ge 2 ] || bad "--prefix needs a value"; prefix=$2; shift 2 ;;
    --purge) purge=1; shift ;;
    --dry-run) dry=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) bad "unknown option: $1" ;;
    esac
done
prefix=$(realpath -ms -- "$prefix")
profile="$HOME/.config/boost-office"
manifest="$prefix/$MANIFEST"

# --- read and check the manifest: nothing is removed before it passes -----------------------------------
[ -f "$manifest" ] && [ "$(head -n 1 "$manifest")" = "$MARKER" ] \
    || die "$prefix is not a Boost Office install (no $MANIFEST from install.sh); nothing removed"
recorded=""
files=()
dirs=()
while IFS= read -r line; do
    case "$line" in
    "" | "#"*) ;;
    "prefix "*) recorded=${line#prefix } ;;
    "theme "*) ;;
    "file /"*) files+=("${line#file }") ;;
    "dir /"*) dirs+=("${line#dir }") ;;
    *) die "$manifest has a line this script does not know: '$line'; nothing removed" ;;
    esac
done <"$manifest"
[ "$recorded" = "$prefix" ] || die "$manifest was written for ${recorded:-no prefix}, not $prefix; nothing removed"

[ "$dry" = 0 ] || say "Dry run: nothing is removed."

act() {  # act DESCRIPTION COMMAND...: say what is done, and do it unless this is a dry run
    say "$1"; shift
    [ "$dry" = 1 ] || "$@"
}
rmdir_if_empty() { rmdir -- "$1" 2>/dev/null || say "  kept $1: it is not empty"; }

# --- the files written outside the prefix ---------------------------------------------------------------
caches=()
for file in "${files[@]}"; do
    if [ -f "$file" ] || [ -L "$file" ]; then
        act "remove $file" rm -f -- "$file"
    fi
    case "$file" in
    */applications/*.desktop) caches+=("${file%/*}/mimeinfo.cache") ;;
    */icons/hicolor/*) caches+=("${file%%/icons/hicolor/*}/icons/hicolor/icon-theme.cache") ;;
    esac
done
# A cache that was there before the install (so not in the manifest) is refreshed without our entries.
for cache in $(printf '%s\n' "${caches[@]}" | sort -u); do
    [ -f "$cache" ] || continue
    case "$cache" in
    */mimeinfo.cache) tool=(update-desktop-database) ;;
    *) tool=(gtk-update-icon-cache -q) ;;
    esac
    command -v "${tool[0]}" >/dev/null || continue
    act "${tool[0]} ${cache%/*}" "${tool[@]}" "${cache%/*}" || say "  ${tool[0]} failed (ignored)"
done

# --- the prefix, then the directories the install created (deepest first, only when empty) --------------
act "remove $prefix" rm -rf -- "$prefix"
for ((i = ${#dirs[@]} - 1; i >= 0; i--)); do
    [ -d "${dirs[i]}" ] || [ "$dry" = 1 ] || continue
    act "remove the directory ${dirs[i]} if empty" rmdir_if_empty "${dirs[i]}"
done

if [ "$purge" = 1 ]; then
    [ ! -e "$profile" ] || act "remove the profile $profile (--purge)" rm -rf -- "$profile"
elif [ -e "$profile" ]; then
    say "The profile $profile stays (remove it with --purge)."
fi
say "Boost Office is uninstalled from $prefix."

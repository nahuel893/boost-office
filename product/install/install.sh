#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Install a built Boost Office tree (an instdir) for the current user, without root: the tree with the Boost
# defaults layer (boost.xcd), the Inter UI font and the Boost icon themes in a prefix, launchers, desktop
# entries, app icons, and a manifest that uninstall.sh removes exactly. A copy of uninstall.sh goes into the
# prefix, so the install can be removed without the repository or the release folder. See --help.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
MARKER="# boost-office-install 1"
MANIFEST=.boost-office-install
# launcher|soffice flag|desktop entry and icon name|Name|stock entry and icon (sysui/desktop)
APPS="boost-office||boost-office-startcenter|Boost Office|startcenter
boost-writer|--writer|boost-office-writer|Boost Writer|writer
boost-calc|--calc|boost-office-calc|Boost Calc|calc
boost-impress|--impress|boost-office-impress|Boost Impress|impress"

usage() {
    cat <<EOF
Usage: install.sh [options]

Install a built Boost Office tree (an instdir) for the current user, without root.

Options:
  --instdir DIR    the built tree (default: the instdir of the repository, or of the extracted release
                   archive); it must contain program/soffice
  --prefix DIR     where the tree is copied (default: ~/.local/opt/boost-office)
  --bindir DIR     where the launchers boost-office, boost-writer, boost-calc and boost-impress go
                   (default: ~/.local/bin)
  --theme THEME    light or dark: the look of new profiles (default: light)
  --icons-dir DIR  where images_boost.zip and images_boost_dark.zip come from; when they are missing they are
                   built there first, which needs Pillow and rsvg-convert (default: product/icons/out)
  --force          replace an earlier Boost Office install at --prefix (uninstalled first; the profile stays)
  --dry-run        print every action and write nothing
  -h, --help       show this help

Desktop entries and app icons go to \${XDG_DATA_HOME:-~/.local/share}/applications and icons/hicolor. The
launchers use the profile ~/.config/boost-office and the desktop's GTK theme. <prefix>/uninstall.sh (a copy
of uninstall.sh) removes everything this script wrote.
EOF
}

die() { echo "install.sh: $*" >&2; exit 1; }
bad() { echo "install.sh: $*" >&2; echo "Try 'install.sh --help'." >&2; exit 2; }
say() { printf '%s\n' "$*"; }
indent() { local line; while IFS= read -r line; do printf '  %s\n' "$line"; done; }

instdir="$repo/instdir"
prefix="$HOME/.local/opt/boost-office"
bindir="$HOME/.local/bin"
theme=light
icons="$repo/product/icons/out"
force=0
dry=0
while [ $# -gt 0 ]; do
    case "$1" in
    --instdir|--prefix|--bindir|--theme|--icons-dir)
        [ $# -ge 2 ] || bad "$1 needs a value"
        case "$1" in
        --instdir) instdir=$2 ;;
        --prefix) prefix=$2 ;;
        --bindir) bindir=$2 ;;
        --theme) theme=$2 ;;
        --icons-dir) icons=$2 ;;
        esac
        shift 2 ;;
    --force) force=1; shift ;;
    --dry-run) dry=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) bad "unknown option: $1" ;;
    esac
done
case "$theme" in light|dark) ;; *) bad "--theme must be light or dark, not '$theme'" ;; esac

data="${XDG_DATA_HOME:-$HOME/.local/share}"
instdir=$(realpath -ms -- "$instdir")
prefix=$(realpath -ms -- "$prefix")
bindir=$(realpath -ms -- "$bindir")
icons=$(realpath -ms -- "$icons")
appdir=$(realpath -ms -- "$data/applications")
icondir=$(realpath -ms -- "$data/icons/hicolor")
profile="$HOME/.config/boost-office"
# These paths go into the launchers, the desktop entries' Exec lines and the manifest unquoted.
for path in "$prefix" "$bindir" "$appdir" "$icondir"; do
    case "$path" in
    *[!A-Za-z0-9._/+@-]*) die "'$path' has a space or a special character; choose a plain path" ;;
    esac
done
[ "$prefix" != / ] && [ "$prefix" != "$HOME" ] || die "--prefix must be a directory of its own, not $prefix"

# --- checks: nothing is written before they pass -------------------------------------------------------
[ -f "$instdir/program/soffice" ] \
    || die "$instdir has no program/soffice: build Boost Office first (product/docs/building.md) or pass --instdir"
command -v python3 >/dev/null || die "python3 is needed"
build_icons=0
[ -f "$icons/images_boost.zip" ] && [ -f "$icons/images_boost_dark.zip" ] || build_icons=1
if [ "$build_icons" = 1 ]; then
    python3 -I -c "import PIL" 2>/dev/null \
        || die "the icon zips are not in $icons, and building them needs Pillow (python3 -m pip install Pillow)"
    command -v rsvg-convert >/dev/null \
        || die "the icon zips are not in $icons, and building them needs rsvg-convert (librsvg)"
fi
replace=0
if [ -e "$prefix" ] || [ -L "$prefix" ]; then
    [ "$(head -n 1 "$prefix/$MANIFEST" 2>/dev/null || true)" = "$MARKER" ] \
        || die "$prefix exists and is not a Boost Office install (no $MANIFEST from install.sh); choose another --prefix"
    [ "$force" = 1 ] || die "$prefix holds a Boost Office install already; pass --force to replace it"
    replace=1
fi

[ "$dry" = 0 ] || say "Dry run: nothing is written."

# act DESCRIPTION COMMAND...: say what is done, and do it unless this is a dry run.
act() {
    say "$1"; shift
    [ "$dry" = 1 ] || "$@"
}

# The manifest lists every file and directory written outside the prefix. Each path is recorded before it
# is written, so a failed run still leaves a manifest that covers it (once the prefix is in place).
records=()
manifest_live=0
record() {
    records+=("$1 $2")
    [ "$dry" = 1 ] || [ "$manifest_live" = 0 ] || printf '%s %s\n' "$1" "$2" >>"$prefix/$MANIFEST"
}
write_manifest() {
    {
        printf '%s\n' "$MARKER" "prefix $prefix" "theme $theme"
        [ ${#records[@]} = 0 ] || printf '%s\n' "${records[@]}"
    } >"$1"
}

# ensure_dir DIR: mkdir -p, recording each directory it creates.
declare -A planned=()
ensure_dir() {
    local dir=$1 missing=()
    while [ ! -d "$dir" ] && [ -z "${planned[$dir]:-}" ]; do
        missing=("$dir" "${missing[@]}")
        dir=$(dirname "$dir")
    done
    for dir in "${missing[@]}"; do
        planned[$dir]=1
        record dir "$dir"
        act "create $dir" mkdir "$dir"
    done
}

# --- an earlier install goes first (--force) -----------------------------------------------------------
if [ "$replace" = 1 ]; then
    say "uninstall the earlier Boost Office install at $prefix (the profile stays)"
    if [ "$dry" = 1 ]; then
        bash "$here/uninstall.sh" --prefix "$prefix" --dry-run | indent
    else
        bash "$here/uninstall.sh" --prefix "$prefix" | indent
    fi
fi

# --- the tree, assembled in a temp dir next to the prefix and renamed into place ----------------------
ensure_dir "$(dirname "$prefix")"
stage="$(dirname "$prefix")/.boost-office-new.XXXXXX"
if [ "$dry" = 0 ]; then
    stage=$(mktemp -d "$stage")
    trap 'rm -rf -- "$stage"' EXIT
fi
copy_tree() { cp -a -- "$instdir/." "$stage/" && chmod 755 "$stage"; }
act "copy $instdir to $stage" copy_tree

if [ "$build_icons" = 1 ]; then
    act "build the icon zips into $icons (Pillow, rsvg-convert)" \
        python3 -I "$repo/product/icons/build_theme.py" build --out "$icons"
fi
install_icons() {
    mkdir -p "$stage/share/config"
    python3 -I "$repo/product/icons/build_theme.py" install --instdir "$stage" --out "$icons" >/dev/null
}
act "install images_boost.zip and images_boost_dark.zip from $icons into $stage/share/config" install_icons

write_layer() {
    python3 -I "$repo/product/install/build_xcd.py" --theme "$theme" --out "$stage/share/registry/boost.xcd" >/dev/null
}
act "write $stage/share/registry/boost.xcd (theme $theme)" write_layer

act "create $stage/share/fonts/truetype" mkdir -p "$stage/share/fonts/truetype"
for ttf in "$repo"/product/fonts/inter/*.ttf; do
    act "copy $(basename "$ttf") into $stage/share/fonts/truetype" cp -- "$ttf" "$stage/share/fonts/truetype/"
done

copy_uninstall() { cp -- "$here/uninstall.sh" "$stage/uninstall.sh" && chmod 755 "$stage/uninstall.sh"; }
act "copy uninstall.sh into $stage" copy_uninstall

act "write the manifest $stage/$MANIFEST" write_manifest "$stage/$MANIFEST"
act "rename $stage to $prefix" mv -T -- "$stage" "$prefix"
[ "$dry" = 1 ] || { trap - EXIT; manifest_live=1; }

# --- launchers -----------------------------------------------------------------------------------------
write_launcher() {
    cat >"$1" <<EOF
#!/bin/sh
# Boost Office launcher, written by product/install/install.sh (uninstall.sh removes it).
# Its own profile; the desktop's GTK theme; the gtk3 VCL plugin unless SAL_USE_VCLPLUGIN says otherwise.
: "\${SAL_USE_VCLPLUGIN:=gtk3}"
export SAL_USE_VCLPLUGIN
exec '$prefix/program/soffice' ${2:+$2 }-env:UserInstallation="file://\$HOME/.config/boost-office" "\$@"
EOF
    chmod 755 "$1"
}
ensure_dir "$bindir"
while IFS='|' read -r launcher flag _name _title _stock; do
    record file "$bindir/$launcher"
    act "write the launcher $bindir/$launcher" write_launcher "$bindir/$launcher" "$flag"
done <<<"$APPS"

# --- desktop entries (one template; MIME types, categories and texts from the stock sysui entries) -----
stock_value() {  # stock_value FILE KEY: the unlocalized KEY=value of a desktop entry
    local line
    while IFS= read -r line; do
        case "$line" in "$2="*) printf '%s' "${line#*=}"; return ;; esac
    done <"$1"
}
write_desktop() {  # write_desktop OUT NAME ICON EXEC STOCK
    local stock="$repo/sysui/desktop/menus/$5.desktop" text
    text=$(<"$here/boost-office.desktop.in")
    text=${text//@NAME@/"$2"}
    text=${text//@GENERIC_NAME@/"$(stock_value "$stock" GenericName)"}
    text=${text//@COMMENT@/"$(stock_value "$stock" Comment)"}
    text=${text//@ICON@/"$3"}
    text=${text//@EXEC@/"$4"}
    text=${text//@CATEGORIES@/"$(stock_value "$stock" Categories)"}
    text=${text//@MIME_TYPES@/"$(stock_value "$stock" MimeType)"}
    printf '%s\n' "$text" >"$1"
}
ensure_dir "$appdir"
while IFS='|' read -r launcher _flag name title stock; do
    record file "$appdir/$name.desktop"
    act "write the desktop entry $appdir/$name.desktop ($title)" \
        write_desktop "$appdir/$name.desktop" "$title" "$name" "$bindir/$launcher" "$stock"
done <<<"$APPS"

# --- app icons -----------------------------------------------------------------------------------------
for sizedir in "$repo"/sysui/desktop/icons/hicolor/*/apps; do
    size=$(basename "$(dirname "$sizedir")")
    while IFS='|' read -r _launcher _flag name _title stock; do
        for ext in png svg; do
            [ -f "$sizedir/$stock.$ext" ] || continue
            ensure_dir "$icondir/$size/apps"
            record file "$icondir/$size/apps/$name.$ext"
            act "copy the icon $icondir/$size/apps/$name.$ext" \
                cp -- "$sizedir/$stock.$ext" "$icondir/$size/apps/$name.$ext"
        done
    done <<<"$APPS"
done

# --- caches: only with the tools present, never failing on them -----------------------------------------
refresh_desktop_db() { update-desktop-database "$appdir" || say "update-desktop-database failed (ignored)"; }
refresh_icon_cache() { gtk-update-icon-cache -q "$icondir" || say "gtk-update-icon-cache failed (ignored)"; }
if command -v update-desktop-database >/dev/null; then
    [ -e "$appdir/mimeinfo.cache" ] || record file "$appdir/mimeinfo.cache"
    act "update-desktop-database $appdir" refresh_desktop_db
fi
# A user hicolor folder without index.theme has no icon cache (GTK reads it directly): leave it so.
if command -v gtk-update-icon-cache >/dev/null && [ -f "$icondir/index.theme" ]; then
    [ -e "$icondir/icon-theme.cache" ] || record file "$icondir/icon-theme.cache"
    act "gtk-update-icon-cache $icondir" refresh_icon_cache
fi

# --- done ----------------------------------------------------------------------------------------------
if [ "$dry" = 1 ]; then
    say "Dry run: nothing was written."
else
    say "Boost Office ($theme) is installed in $prefix: start it with boost-writer, boost-calc, boost-impress"
    say "or boost-office in $bindir, or from the desktop menu. Remove it with:"
    say "  $prefix/uninstall.sh --prefix $prefix"
fi
case ":$PATH:" in *":$bindir:"*) ;; *) say "Note: $bindir is not on your PATH." ;; esac
if [ -d "$profile" ]; then
    say "Note: the profile $profile exists. --theme sets the look of new profiles only: this profile keeps"
    say "the color scheme it first ran with. To switch it, choose Boost Light or Boost Dark under"
    say "Tools > Options > LibreOfficeDev > Appearance, or move $profile away to start a new profile."
fi

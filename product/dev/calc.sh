#!/usr/bin/env bash
# Open the dev build's Calc in one step, with a chosen look.
# Usage: calc.sh [light|dark|tabbed|tabbed-light|compact] [--font system|selawik|inter] [--profile DIR] [--dry-run]
#   light         Tabbed Office, Boost icons, "Boost Light" scheme (soft green)  [default]
#   dark          Tabbed Office, Boost dark icons, "Boost Dark" scheme
#   tabbed        LibreOffice's original Tabbed ribbon, dark, no product theme
#   tabbed-light  LibreOffice's original Tabbed ribbon, light, no product theme
#   compact       LibreOffice's Tabbed Compact ribbon, dark, no product theme
#   --font        UI font: system (the desktop's), or bundled selawik or inter (any mode). Without it,
#                 light and dark use inter; tabbed, tabbed-light and compact use system.
# The profile (default /mnt/games/libreoffice/try-profile) is rewritten on each run;
# missing icon zips and the color scheme extension are built and installed first.
set -euo pipefail
core="$(cd "$(dirname "$0")/../.." && pwd)"
profile=/mnt/games/libreoffice/try-profile
mode=light
font=
dry=0

usage() { echo "usage: calc.sh [light|dark|tabbed|tabbed-light|compact] [--font system|selawik|inter] [--profile DIR] [--dry-run]" >&2; exit 2; }

while [ $# -gt 0 ]; do
    case "$1" in
    --profile) [ $# -ge 2 ] || usage; profile="$2"; shift 2 ;;
    --font) [ $# -ge 2 ] || usage; case "$2" in system|selawik|inter) font="$2" ;; *) usage ;; esac; shift 2 ;;
    --dry-run) dry=1; shift ;;
    light|dark|tabbed|tabbed-light|compact) mode="$1"; shift ;;
    *) usage ;;
    esac
done

scheme=""
case "$mode" in
light)        args=(--ui office --appearance light --icons boost --scheme "Boost Light" --tint 255)
              scheme=yes; gtk=adw-gtk3 ;;
dark)         args=(--ui office --appearance dark --icons boost_dark --scheme "Boost Dark" --tint 255)
              scheme=yes; gtk=adw-gtk3-dark ;;
tabbed)       args=(--ui tabbed --appearance dark); gtk=adw-gtk3-dark ;;
tabbed-light) args=(--ui tabbed --appearance light); gtk=adw-gtk3 ;;
compact)      args=(--ui compact --appearance dark); gtk=adw-gtk3-dark ;;
esac
# Default font: Inter in the Boost looks, the desktop's font in the stock modes. --font wins.
if [ -z "$font" ]; then
    case "$mode" in light|dark) font=inter ;; *) font=system ;; esac
fi
# The font goes to the profile: the bundled TTFs into user/fonts and VCL's UIFont/FamilyName item.
[ "$font" = system ] || args+=(--font "$font")

soffice="$core/instdir/program/soffice"
unopkg="$core/instdir/program/unopkg"
env_arg="-env:UserInstallation=file://$profile"
gtkcfg=/mnt/games/libreoffice/gtk-light-config

if [ "$dry" = 1 ]; then
    echo "profile: python3 -I product/dev/profile.py ${args[*]} --profile $profile"
    case "$gtk" in *dark) ;; *) echo "private GTK config: $gtkcfg" ;; esac
    echo "extension: reinstall when changed"
    echo "launch: GTK_THEME=$gtk soffice --calc $env_arg"
    exit 0
fi

if pgrep -f "soffice.bin.*UserInstallation=file://$profile" >/dev/null; then
    echo "Calc is already running with $profile: close it first." >&2
    exit 1
fi

# Icon themes: build and install them if they are not in instdir yet.
if [ ! -f "$core/instdir/share/config/images_boost.zip" ]; then
    python3 -I "$core/product/icons/build_theme.py" build
    python3 -I "$core/product/icons/build_theme.py" install --instdir "$core/instdir"
fi

# Color schemes: rebuild the extension when its sources changed, and (re)install it
# into this profile whenever the .oxt is newer than the profile's stamp.
if [ -n "$scheme" ]; then
    oxt="$core/product/themes/out/boost-schemes.oxt"
    themes="$core/product/themes"
    if [ ! -f "$oxt" ] || [ "$themes/build_schemes.py" -nt "$oxt" ] || [ "$themes/palette.json" -nt "$oxt" ]; then
        python3 -I "$themes/build_schemes.py" >/dev/null
    fi
    stamp="$profile/.boost-schemes-installed"
    if [ ! -f "$stamp" ] || [ "$oxt" -nt "$stamp" ] \
       || ! "$unopkg" list "$env_arg" 2>/dev/null | grep -q org.boost.colorschemes; then
        "$unopkg" add -f "$oxt" "$env_arg"
        mkdir -p "$profile" && touch "$stamp"
    fi
fi

python3 -I "$core/product/dev/profile.py" "${args[@]}" --profile "$profile" >/dev/null

case "$gtk" in
*dark) ;;
*)  # Light needs a GTK config without the user's dark gtk-3.0 colors and dconf
    # (same reason as in shot.sh). It must outlive this script, so it is persistent.
    cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
    rm -rf "$gtkcfg"; mkdir -p "$gtkcfg"
    for e in "$cfg"/* "$cfg"/.[!.]*; do
        [ -e "$e" ] || continue
        case "$(basename "$e")" in gtk-3.0|dconf) ;; *) ln -s "$e" "$gtkcfg/" ;; esac
    done
    export XDG_CONFIG_HOME="$gtkcfg" ;;
esac

GTK_THEME="$gtk" SAL_USE_VCLPLUGIN=gtk3 setsid -f "$soffice" --calc --norestore "$env_arg" \
    >/dev/null 2>&1 </dev/null
echo "Calc started ($mode, profile $profile)"

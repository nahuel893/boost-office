#!/usr/bin/env bash
# Screenshot the dev build's Calc window on Sway or Hyprland.
# Usage: shot.sh OUT.png [full|WIDTHxHEIGHT]
# Env:   LO_PROFILE   isolated profile dir (default /mnt/games/libreoffice/dev-profile)
#        LO_GTK_THEME GTK theme for the run (default adw-gtk3-dark; adw-gtk3 for light).
#                     A theme not ending in "dark" also runs with a private GTK config
#                     (see below), because the user's ~/.config/gtk-3.0/gtk.css and dconf
#                     force dark colors on every GTK3 app and GTK_THEME alone cannot undo that.
set -euo pipefail
out="$1"
size="${2:-full}"
core="$(cd "$(dirname "$0")/../.." && pwd)"
profile="${LO_PROFILE:-/mnt/games/libreoffice/dev-profile}"
mkdir -p "$(dirname "$out")"

theme="${LO_GTK_THEME:-adw-gtk3-dark}"
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
case "$theme" in
*dark) ;;
*)  # Private config home: everything linked except GTK3 settings/colors and dconf.
    tmpcfg=$(mktemp -d)
    trap 'rm -rf "$tmpcfg"' EXIT
    for e in "$cfg"/* "$cfg"/.[!.]*; do
        [ -e "$e" ] || continue
        case "$(basename "$e")" in gtk-3.0|dconf) ;; *) ln -s "$e" "$tmpcfg/" ;; esac
    done
    export XDG_CONFIG_HOME="$tmpcfg" ;;
esac

GTK_THEME="$theme" SAL_USE_VCLPLUGIN=gtk3 \
    "$core/instdir/program/soffice" --calc --norestore --nologo \
    "-env:UserInstallation=file://$profile" >/dev/null 2>&1 &

pat="soffice.bin.*UserInstallation=file://$profile"
if [ -n "${SWAYSOCK:-}" ]; then wm=sway; else wm=hypr; fi

# Window of the dev instance only: match by pid, never by title, so a
# regular LibreOffice session on the same desktop is never captured.
find_window() {
    local pids; pids=$(pgrep -f "$pat" | jq -R -s -c 'split("\n") | map(select(. != "") | tonumber)')
    if [ "$wm" = sway ]; then
        swaymsg -t get_tree | jq -r --argjson p "$pids" \
            '[.. | objects | select(.pid? and (.pid as $x | $p | index($x)) and .name?)][0].id // empty'
    else
        hyprctl clients -j | jq -r --argjson p "$pids" \
            '[.[] | select(.pid as $x | $p | index($x))][0].address // empty'
    fi
}

addr=""
for _ in $(seq 120); do
    addr=$(find_window)
    [ -n "$addr" ] && break
    sleep 0.5
done
if [ -z "$addr" ]; then
    echo "no Calc window after 60 s" >&2
    pkill -f "$pat" || true
    exit 1
fi

if [ "$wm" = sway ]; then
    swaymsg "[con_id=$addr] focus" >/dev/null
    if [ "$size" = full ]; then
        swaymsg "[con_id=$addr] fullscreen enable" >/dev/null
    else
        # Each step needs the previous one applied: resizing in the same command as
        # "floating enable" is ignored and the window keeps its floating default size.
        swaymsg "[con_id=$addr] floating enable" >/dev/null
        sleep 1
        swaymsg "[con_id=$addr] resize set width ${size%x*} px height ${size#*x} px" >/dev/null
        sleep 1
        swaymsg "[con_id=$addr] move position center" >/dev/null
    fi
    sleep 3  # let the ribbon re-layout and repaint at the new size
    geom=$(swaymsg -t get_tree | jq -r --argjson a "$addr" \
        '.. | objects | select(.id? == $a) | "\(.rect.x),\(.rect.y) \(.rect.width)x\(.rect.height)"')
    grim -g "$geom" "$out"
    swaymsg "[con_id=$addr] kill" >/dev/null || true
else
    hyprctl dispatch focuswindow "address:$addr" >/dev/null
    if [ "$size" = full ]; then
        hyprctl dispatch fullscreen 0 >/dev/null
    else
        hyprctl dispatch setfloating "address:$addr" >/dev/null
        hyprctl dispatch resizewindowpixel "exact ${size%x*} ${size#*x},address:$addr" >/dev/null
        hyprctl dispatch centerwindow >/dev/null
    fi
    sleep 3
    geom=$(hyprctl clients -j | jq -r --arg a "$addr" \
        '.[] | select(.address == $a) | "\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"')
    grim -g "$geom" "$out"
    hyprctl dispatch closewindow "address:$addr" >/dev/null || true
fi
sleep 2
pkill -f "$pat" || true
echo "$out"

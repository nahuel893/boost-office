#!/usr/bin/env bash
# Screenshot one ribbon tab of the dev build's Calc, Writer or Impress, or its Start Center, in a private
# headless sway.
# Usage: shot-tab.sh [--app calc|writer|impress|start] THEME TAB OUT.png [WIDTH]
#   --app  calc (default), writer, impress, or start (soffice with no document: the Start Center; TAB must be "-")
#   THEME  light | dark   (same look as office.sh: Tabbed Office, Boost icons and scheme)
#   TAB    tab label to click, e.g. Insert, Home, "Page Layout" (found by its ink on the tab bar, in tab order;
#          "-" keeps the tab the app opens with). The tab order is SHOT_TABS (comma-separated), by default
#          Excel's for Calc, and for Writer Word's (design section 3.2 of product/docs/writer-ribbon-tabs.md)
#          without the pages the installed Writer office .ui does not have yet. Impress's is the order of the
#          installed Impress office .ui, without its contextual tabs.
#   OUT    PNG path (put it outside the repo)
#   WIDTH  1920 (default), 1600 or 1366; the headless output is WIDTH x (WIDTH*9/16). --app start also takes
#          1280 (1280x800) and 1024 (1024x640) for the smaller-window checks.
# It never touches the user's session: its own sway (WLR_BACKENDS=headless, one output, own
# Wayland and IPC sockets), the dev profile (LO_PROFILE, default /mnt/games/libreoffice/dev-profile)
# and a private XDG_CONFIG_HOME; it refuses the user's own profiles (office.sh's defaults
# /mnt/games/libreoffice/try-profile, try-profile-writer, try-profile-impress and try-profile-start). Only the PIDs it
# started are killed.
# Whole run is under `timeout` (LO_SHOT_TIMEOUT, default 180 s). Needs sway, grim, jq, python3 + Pillow.
# Env: SHOT_KEEP=1 leaves the sway running (prints its SWAYSOCK) for manual follow-up clicks;
#      SHOT_AFTER="swaymsg-free shell snippet" runs after the tab click with $SWAYSOCK, $WAYLAND_DISPLAY,
#      $SHOT_W, $SHOT_H, $SHOT_PTR exported (used for the Shapes dropdown capture); write "click X Y" to
#      "$SHOT_PTR" (the client moves onto the target first, then presses), and "wait S" to pause.
#      SHOT_FONT=system|selawik|inter picks the UI font, like calc.sh --font (default inter,
#      because the themes are always the Boost looks). SHOT_FONT=system keeps the desktop's font.
set -euo pipefail

app=calc
if [ "${1:-}" = --app ]; then
    case "${2:-}" in calc|writer|impress|start) app="$2" ;; *) echo "--app must be calc|writer|impress|start" >&2; exit 2 ;; esac
    shift 2
fi
theme="${1:?theme light|dark}"; tab="${2:?tab}"; out="${3:?out.png}"; width="${4:-1920}"
case "$theme" in light|dark) ;; *) echo "theme must be light or dark" >&2; exit 2 ;; esac
if [ "$app" = start ]; then
    [ "$tab" = - ] || { echo "--app start takes TAB -" >&2; exit 2; }
    case "$width" in
        1920) height=1080 ;; 1600) height=900 ;; 1366) height=768 ;; 1280) height=800 ;; 1024) height=640 ;;
        *) echo "width: 1920|1600|1366|1280|1024" >&2; exit 2 ;;
    esac
else
    case "$width" in 1920) height=1080 ;; 1600) height=900 ;; 1366) height=768 ;; *) echo "width: 1920|1600|1366" >&2; exit 2 ;; esac
fi
font="${SHOT_FONT:-inter}"
case "$font" in system|selawik|inter) ;; *) echo "SHOT_FONT must be system, selawik or inter" >&2; exit 2 ;; esac

if [ -z "${SHOT_INNER:-}" ]; then
    exec timeout --kill-after=10 "${LO_SHOT_TIMEOUT:-180}" env SHOT_INNER=1 "$0" --app "$app" "$@"
fi

core="$(cd "$(dirname "$0")/../.." && pwd)"
profile="${LO_PROFILE:-/mnt/games/libreoffice/dev-profile}"
soffice="$core/instdir/program/soffice"
unopkg="$core/instdir/program/unopkg"
# Guards first, before anything is started or any trap is installed: refusing must never touch a
# running Calc, Writer or Impress. Never the user's own profiles, never a profile that is in use.
case "$app" in calc) App=Calc ;; writer) App=Writer ;; impress) App=Impress ;; start) App="Start Center" ;; esac
real_profile=$(realpath -m "$profile")
case "$real_profile" in
/mnt/games/libreoffice/try-profile)
    echo "refusing LO_PROFILE=$profile: that is the user's own Calc profile." >&2; exit 1 ;;
/mnt/games/libreoffice/try-profile-writer)
    echo "refusing LO_PROFILE=$profile: that is the user's own Writer profile." >&2; exit 1 ;;
/mnt/games/libreoffice/try-profile-impress)
    echo "refusing LO_PROFILE=$profile: that is the user's own Impress profile." >&2; exit 1 ;;
/mnt/games/libreoffice/try-profile-start)
    echo "refusing LO_PROFILE=$profile: that is the user's own Start Center profile." >&2; exit 1 ;;
esac
if pgrep -f "soffice.bin.*UserInstallation=file://$profile" >/dev/null; then
    echo "$App already runs with $profile: close it first." >&2; exit 1
fi

# Tab order on the bar, and the first tab-bar column after the quick access toolbar (x0, measured at
# 1920 px light; the toolbars differ per app. Writer's and Impress's toolbar ink ends at x=195 and their
# File label starts at x=240, so x0 is the middle of that gap). Writer's list is design section 3.2's,
# filtered to the tabs of the installed office .ui, so that each label keeps its index when later tasks
# add pages. Impress's is read from its installed office .ui alone, so it follows each task that moves or
# adds a tab (Design moved before Transitions in I4a; Transitions, Animations and Help come with I5a and I8a).
calc_tabs="File,Home,Insert,Page Layout,Formulas,Data,Review,View,Extension,Tools,Help"
writer_tabs="File,Home,Insert,Design,Layout,References,Mailings,Review,View,Extension,Tools,Help"
if [ "$app" = calc ]; then
    tabs="$calc_tabs"; bar_x0=225
elif [ "$app" = writer ]; then
    tabs="$writer_tabs"; bar_x0=217
else
    tabs=""; bar_x0=217
fi
if [ -n "${SHOT_TABS:-}" ]; then
    tabs="$SHOT_TABS"
elif [ "$app" = writer ]; then
    tabs=$(python3 -I - "$core/instdir/share/config/soffice.cfg/modules/swriter/ui/notebookbar_office.ui" "$tabs" <<'PYEOF'
import sys
from xml.etree import ElementTree as ET
ui, order = sys.argv[1], sys.argv[2].split(",")
book = ET.parse(ui).getroot().find(".//object[@id='ContextContainer']")
labels = {tab.findtext("object/property[@name='label']").replace("~", "")
          for tab in book.findall("child[@type='tab']")}
print(",".join(name for name in order if name in labels))
PYEOF
    )
elif [ "$app" = impress ]; then
    tabs=$(python3 -I - "$core/instdir/share/config/soffice.cfg/modules/simpress/ui/notebookbar_office.ui" <<'PYEOF'
import sys
from xml.etree import ElementTree as ET
book = ET.parse(sys.argv[1]).getroot().find(".//object[@id='ContextContainer']")
names = []
for tab in book.findall("child[@type='tab']"):
    label = tab.find("object")
    contexts = {c.get("name") for c in label.findall("style/class") if c.get("name").startswith("context-")}
    # a contextual tab (Table, Draw, Master, ...) shows only with its object or view: it has context
    # classes and no context-any
    if not contexts or "context-any" in contexts:
        names.append(label.findtext("property[@name='label']").replace("~", ""))
print(",".join(names))
PYEOF
    )
fi

mkdir -p "$(dirname "$out")"
work=$(mktemp -d)
sway_pid=""; lo_pid=""; ptr_pid=""

# Kill only what this run launched, by PID: Calc runs in its own session (setsid), so its whole
# process group (soffice wrapper + soffice.bin) is ours; sway and the pointer client are single PIDs.
cleanup() {
    trap - EXIT
    exec 8>&- || true
    local pids="$ptr_pid"
    [ -n "$lo_pid" ] && kill -TERM -- "-$lo_pid" 2>/dev/null || true
    [ "${SHOT_KEEP:-0}" = 1 ] || pids="$pids $sway_pid"
    for p in $pids; do kill -TERM "$p" 2>/dev/null || true; done
    for _ in $(seq 25); do   # up to 5 s for a clean exit
        alive=0
        [ -n "$lo_pid" ] && kill -0 -- "-$lo_pid" 2>/dev/null && alive=1
        for p in $pids; do kill -0 "$p" 2>/dev/null && alive=1; done
        [ "$alive" = 0 ] && break
        sleep 0.2
    done
    [ -n "$lo_pid" ] && kill -KILL -- "-$lo_pid" 2>/dev/null || true
    for p in $pids; do kill -KILL "$p" 2>/dev/null || true; done
    [ "${SHOT_KEEP:-0}" = 1 ] || rm -rf "$work"
}
trap cleanup EXIT

# --- profile: the look of office.sh light|dark (profile.py LOOKS), with SHOT_FONT's font ----------------
# The Start Center has no module of its own: Calc's profile settings carry the look.
if [ "$app" = start ]; then
    args=(--app calc --look "$theme" --font "$font")
else
    args=(--app "$app" --look "$theme" --font "$font")
fi
if [ "$theme" = light ]; then gtk=adw-gtk3; else gtk=adw-gtk3-dark; fi
env_arg="-env:UserInstallation=file://$profile"
oxt="$core/product/themes/out/boost-schemes.oxt"
[ -f "$oxt" ] || python3 -I "$core/product/themes/build_schemes.py" >/dev/null
stamp="$profile/.boost-schemes-installed"
installed=$("$unopkg" list "$env_arg" 2>/dev/null || true)   # capture first: rg -q under pipefail can SIGPIPE
if [ ! -f "$stamp" ] || [ "$oxt" -nt "$stamp" ] || ! rg -q org.boost.colorschemes <<<"$installed"; then
    "$unopkg" add -f "$oxt" "$env_arg" >/dev/null
    mkdir -p "$profile" && touch "$stamp"
fi
python3 -I "$core/product/dev/profile.py" "${args[@]}" --profile "$profile" >/dev/null

# --- private config home: the user's dark GTK3 settings must not leak into a light run --------
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
mkdir -p "$work/cfg"
for e in "$cfg"/* "$cfg"/.[!.]*; do
    [ -e "$e" ] || continue
    case "$(basename "$e")" in gtk-3.0|dconf|sway) ;; *) ln -s "$e" "$work/cfg/" ;; esac
done

# --- private headless sway ---------------------------------------------------------------------
cat > "$work/sway.conf" <<EOF
output HEADLESS-1 resolution ${width}x${height} position 0 0
default_border none
exec printenv WAYLAND_DISPLAY > $work/wayland-display
EOF
env -u SWAYSOCK -u WAYLAND_DISPLAY -u DISPLAY -u HYPRLAND_INSTANCE_SIGNATURE \
    WLR_BACKENDS=headless WLR_LIBINPUT_NO_DEVICES=1 WLR_RENDERER=pixman XDG_CONFIG_HOME="$work/cfg" \
    sway -c "$work/sway.conf" >"$work/sway.log" 2>&1 &
sway_pid=$!
export SWAYSOCK="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/sway-ipc.$(id -u).$sway_pid.sock"
for _ in $(seq 60); do
    [ -s "$work/wayland-display" ] && swaymsg -s "$SWAYSOCK" -t get_outputs >/dev/null 2>&1 && break
    kill -0 "$sway_pid" 2>/dev/null || { echo "headless sway died:" >&2; tail -20 "$work/sway.log" >&2; exit 1; }
    sleep 0.5
done
[ -s "$work/wayland-display" ] || { echo "headless sway never came up" >&2; tail -20 "$work/sway.log" >&2; exit 1; }
export WAYLAND_DISPLAY; WAYLAND_DISPLAY=$(<"$work/wayland-display")
export SHOT_W="$width" SHOT_H="$height"

# --- virtual pointer ---------------------------------------------------------------------------
# The headless sway has no input device, so its seat has no pointer and "swaymsg seat cursor" events
# reach nobody. A tiny Wayland client makes a zwlr_virtual_pointer_v1 (sway supports it) and reads
# commands from a FIFO: "move X Y", "press", "release", "click X Y". Raw wire protocol, no libraries.
cat > "$work/ptr.py" <<'PYEOF'
import os, socket, struct, sys, time

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(os.path.join(os.environ["XDG_RUNTIME_DIR"], os.environ["WAYLAND_DISPLAY"]))
W, H = int(os.environ["SHOT_W"]), int(os.environ["SHOT_H"])


def pad(b):
    return b + b"\0" * (-len(b) % 4)


def send(obj, op, payload=b""):
    sock.sendall(struct.pack("<II", obj, ((8 + len(payload)) << 16) | op) + payload)


def string(s):
    b = s.encode() + b"\0"
    return struct.pack("<I", len(b)) + pad(b)


def events():
    sock.settimeout(2)
    buf = b""
    while len(buf) < 8 or len(buf) < (struct.unpack("<II", buf[:8])[1] >> 16):
        buf += sock.recv(65536)
        if len(buf) >= 8 and len(buf) >= (struct.unpack("<II", buf[:8])[1] >> 16):
            break
    out = []
    while len(buf) >= 8:
        obj, w = struct.unpack("<II", buf[:8])
        size, op = w >> 16, w & 0xFFFF
        if len(buf) < size:
            break
        out.append((obj, op, buf[8:size]))
        buf = buf[size:]
    return out


send(1, 1, struct.pack("<I", 2))          # wl_display.get_registry -> id 2
send(1, 0, struct.pack("<I", 3))          # wl_display.sync -> id 3
name = version = None
done = False
while not done:
    for obj, op, data in events():
        if obj == 2 and op == 0:
            n, ln = struct.unpack("<II", data[:8])
            iface = data[8:8 + ln - 1].decode()
            v = struct.unpack("<I", data[8 + ((ln + 3) & ~3):][:4])[0]
            if iface == "zwlr_virtual_pointer_manager_v1":
                name, version = n, min(v, 2)
        if obj == 3:
            done = True
if name is None:
    sys.exit("no zwlr_virtual_pointer_manager_v1")
send(2, 0, struct.pack("<I", name) + string("zwlr_virtual_pointer_manager_v1") + struct.pack("<II", version, 4))
send(4, 0, struct.pack("<II", 0, 5))      # create_virtual_pointer(seat=null) -> id 5
t0 = time.monotonic()


def now():
    return int((time.monotonic() - t0) * 1000)


def move(x, y):
    send(5, 1, struct.pack("<IIIII", now(), int(x), int(y), W, H))
    send(5, 4)


def button(down):
    send(5, 2, struct.pack("<III", now(), 272, 1 if down else 0))
    send(5, 4)


time.sleep(1.5)   # let sway grow the seat's pointer capability and the client bind wl_pointer
print("ready", flush=True)
for line in sys.stdin:
    f = line.split()
    if not f:
        continue
    if f[0] == "move":
        move(f[1], f[2])
    elif f[0] == "press":
        button(True)
    elif f[0] == "release":
        button(False)
    elif f[0] == "click":
        # enter the surface first: a press without a prior motion over the target is dropped
        move(int(f[1]) - 4, int(f[2]) - 4); time.sleep(0.3)
        move(f[1], f[2]); time.sleep(0.4); button(True); time.sleep(0.15); button(False)
    elif f[0] == "wait":
        time.sleep(float(f[1]))
    elif f[0] == "quit":
        break
    time.sleep(0.1)
PYEOF
mkfifo "$work/ptr"
XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" python3 -I "$work/ptr.py" <"$work/ptr" >"$work/ptr.log" 2>&1 &
ptr_pid=$!
exec 8>"$work/ptr"
for _ in $(seq 50); do
    rg -q '^ready' "$work/ptr.log" 2>/dev/null && break
    kill -0 "$ptr_pid" 2>/dev/null || break
    sleep 0.2
done
rg -q '^ready' "$work/ptr.log" 2>/dev/null || { echo "virtual pointer client failed:" >&2; bat -p "$work/ptr.log" >&2; exit 1; }
export SHOT_PTR="$work/ptr"   # SHOT_AFTER snippets write commands here, e.g. echo "click 100 50" > "$SHOT_PTR"
click() { echo "move $(($1 - 4)) $(($2 - 4))" >&8; echo "click $1 $2" >&8; }

# --- Calc, Writer, Impress or the Start Center inside it --------------------------------------
# The Start Center is soffice with no module switch and no document.
launch=(env -u DISPLAY XDG_CONFIG_HOME="$work/cfg" GDK_BACKEND=wayland GTK_THEME="$gtk" SAL_USE_VCLPLUGIN=gtk3 setsid)
if [ "$app" = start ]; then
    "${launch[@]}" "$soffice" --norestore --nologo "$env_arg" >"$work/soffice.log" 2>&1 &
else
    "${launch[@]}" "$soffice" --"$app" --norestore --nologo "$env_arg" >"$work/soffice.log" 2>&1 &
fi
lo_pid=$!

id=""
for _ in $(seq 120); do
    tree=$(swaymsg -t get_tree) || { echo "swaymsg get_tree failed (headless sway gone?)" >&2; exit 1; }
    id=$(jq -r '[.. | objects | select(.pid? and .name? and (.type? == "con" or .type? == "floating_con"))][0].id // empty' <<<"$tree") || { echo "jq could not read the sway tree" >&2; exit 1; }
    [ -n "$id" ] && break
    sleep 0.5
done
[ -n "$id" ] || { echo "no $App window after 60 s" >&2; tail -5 "$work/soffice.log" >&2; exit 1; }
swaymsg "[con_id=$id] fullscreen enable" >/dev/null
sleep 6   # first start: let the ribbon lay out and repaint at the output size


if [ "$tab" != "-" ]; then
    grim "$work/bar.png"
    pos=$(python3 -I - "$work/bar.png" "$tab" "$tabs" "$bar_x0" <<'PYEOF'
# No OCR (tesseract has no language data here): find the label blobs on the tab bar by their ink
# and pick the one at the label's position in the tab order (a number picks the blob by index).
import sys
from PIL import Image
img, tab, order = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
im = Image.open(img).convert("L")
# Tab bar label rows (the label text spans y 12..23 since the ribbon card, C1, took away the 6 px margin above
# the tab bar); the selected tab's pill strokes sit below, at y 27..35, and would join File with Home at
# 1366 px where the labels are only ~20 px apart.
y0, y1, x0 = 8, 25, int(sys.argv[4])   # x0 skips the quick access toolbar on the left
cols = []
for x in range(x0, im.width - 80):
    col = [im.getpixel((x, y)) for y in range(y0, y1)]
    ref = sorted(col)[len(col) // 2]
    cols.append(any(abs(v - ref) > 70 for v in col))
blobs, start, gap = [], None, 0
for i, ink in enumerate(cols + [False] * 40):
    if ink:
        start = i if start is None else start
        gap = 0
    elif start is not None:
        gap += 1
        if gap > 14:               # words of one label are ~5 px apart, labels 30+ px
            if i - gap - start >= 8:   # the active tab's pill edges are 1-2 px blobs
                blobs.append((start + x0, i - gap + x0))
            start = None
idx = int(tab) if tab.isdigit() else [o.lower() for o in order].index(tab.lower())
if not 0 <= idx < len(blobs):
    sys.exit(f"tab {tab}: only {len(blobs)} labels found on the bar")
l, r = blobs[idx]
print((l + r) // 2, 19)
PYEOF
    ) || true
    [ -n "$pos" ] || { echo "tab '$tab' not found on the tab bar" >&2; exit 1; }
    echo "clicking tab $tab at $pos" >&2
    click ${pos% *} ${pos#* }
    sleep 3
fi

if [ -n "${SHOT_AFTER:-}" ]; then
    export SHOT_OUT="$out"
    bash -c "$SHOT_AFTER"
fi
grim "$out"
echo "$out"
[ "${SHOT_KEEP:-0}" = 1 ] && echo "SWAYSOCK=$SWAYSOCK WAYLAND_DISPLAY=$WAYLAND_DISPLAY work=$work" >&2
exit 0

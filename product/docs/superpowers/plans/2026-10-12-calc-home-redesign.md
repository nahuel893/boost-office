# Calc Home Redesign (Stage A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Calc ribbon variant, "Tabbed Office", whose Home tab has Excel's 8 sections, with Fluent-based icons (light and dark) and neutral color schemes. Every step is verified by tests and screenshots, and no existing variant changes.

**Architecture:** Stage A is declarative only.
- A small Python generator turns a JSON layout into the Home page XML inside a copy of Calc's Tabbed `notebookbar.ui`.
- An icon builder turns vendored Fluent SVGs and a manifest into two partial icon-theme zips.
- A scheme builder turns palette tokens into a configuration-only LibreOffice extension with two ColorSchemes.
- Dev scripts run memory-capped builds, preset an isolated profile and take Hyprland screenshots.

**Tech Stack:**
- LibreOffice gbuild, GtkBuilder `.ui` XML read by the VCL builder, officecfg XCU, LibreOffice UITest (Python).
- Python 3 (stdlib, Pillow 12, lxml), `rsvg-convert`, `magick`, Hyprland (`hyprctl`, `grim`, `jq`).

**Spec:** `product/docs/superpowers/specs/2026-10-12-calc-home-redesign-design.md`. Its annexes are normative and live in `product/docs/design/`:
- `calc-home-tab-layout.txt`
- `calc-home-icons.txt`
- `calc-home-palette.txt`
- `calc-home-prototype.txt`

**Plan verification (2026-10-12):** the Python and JSON in Tasks 1, 5, 6, 7, 8 and 9 were extracted from this plan and run in a scratch copy against the real `notebookbar.ui` and the Fluent package.
- The unit tests passed: 33 tests.
- The generated `notebookbar_office.ui` is well-formed.
- `bin/gla11y` with the build's flags reported 0 new warnings and 0 new fatals.
- `bin/lint-ui.py` exited 0.
- The shell scripts, the UITests and every LibreOffice runtime behaviour are unverified until they are executed.

## Global Constraints

**Repository and builds**
- Repository: `/mnt/games/libreoffice/core`. Branch `feature/calc-home-redesign`, created from commit `62abc2329664`.
- Every command below runs from the repository root unless it says otherwise.
- Builds only through `product/dev/lo-make.sh`, which caps make with cgroup limits (MemoryHigh=6G, MemoryMax=7G, MemorySwapMax=1G) and `PARALLELISM=6`. Never run plain `make` at `-j10`: it froze the 14 GB machine.

**Files you may and may not touch**
- Never edit `sc/uiconfig/scalc/ui/notebookbar.ui` or any other existing `notebookbar*.ui`.
- Existing upstream files that may be edited:
  - `officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu`
  - `sc/UIConfig_scalc.mk`
  - `solenv/sanitizers/ui/modules/scalc.suppr`
  - Only if spike 0a selects route P2: `officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu`.
- New upstream-tree files allowed:
  - `sc/uiconfig/scalc/ui/notebookbar_office.ui`
  - `sc/uiconfig/scalc/popupmenu/home_*.xml` (routes P2 and P3 only)
  - `sc/qa/uitest/calc_tests/notebookbarOffice.py`
- Product-only tooling lives in the new top-level directory `product/`. gbuild ignores it.

**Runtime and environment**
- Isolated profile: `/mnt/games/libreoffice/dev-profile`. Never touch `~/.config/libreoffice`.
- Fluent UI System Icons 1.1.344, `regular` style unless a layer says `filled`, MIT. The source checkout is `/mnt/games/libreoffice/assets/fluent/package/icons`; the used subset is vendored into `product/icons/fluent/`.
- Working names:
  - icon themes `boost` and `boost_dark`
  - color schemes `Boost Light` and `Boost Dark`
  - mode label `Tabbed Office`, `CommandArg` = `notebookbar_office.ui`, mode node `TabbedOffice`, `MenuPosition` 9

**Design values**
- Colors: the exact hex values from spec §4.3, which match annex 3.
- Icon line color: `#424242` (light) and `#D6D6D6` (dark).
- Icon accents:
  - green `#107C10` / `#54B054`
  - red `#C50F1F` / `#E9737B`
  - blue `#0F6CBD` / `#479EF5`
  - amber `#AD6800` / `#F2B230`
- At most one accent color per icon.
- Large ribbon buttons use `icon_size` 5 (32 px). Small ones use `icon_size` 1 (16 px).
- The color buttons (`.uno:Color`, `.uno:BackgroundColor`) keep the bottom quarter of each icon fully transparent.

**Conventions**
- All artifacts are in English. Commits follow Conventional Commits, with no AI attribution lines.
- Python runs as `python3 -I`. Product unit tests: `python3 -I -m unittest discover -s product/tests -t .`
- UITests: `product/dev/uitest.sh <module.Class.test>`. The filter needs the exact full name (`uitest/test_main.py:90-94`).
- Strict TDD: write the test, see it fail for the expected reason, implement, see it pass, commit.

## Review Focus

These are the five failure modes most likely to hit a real user. No other test exercises them, so each has its own test in the task that owns the code:

1. **Font color / Fill color:** icon art in the bottom quarter collides with LibreOffice's color stripe, and the button looks broken. Test: Task 7, `test_color_buttons_keep_the_stripe_band_empty`.
2. **A redesigned Home button has no `boost` icon** and silently shows an old Colibre icon in the middle of the new tab. Test: Task 7, `test_every_home_button_has_an_icon`.
3. **The dark zip carries light-mode gray (#424242) lines,** so icons are nearly invisible on the dark ribbon. Test: Task 7, `test_dark_theme_has_no_light_theme_line_color`.
4. **Leaving Tabbed Office breaks the user's previous UI** (Tabbed Compact), or the copy drifts from upstream outside the Home tab. Tests: Task 2, `test_switch_back_to_compact`; Task 6, `test_office_ui_is_upstream_plus_home_layout`.
5. **Menus, selections or the active button become unreadable** with our schemes (contrast below WCAG AA). Test: Task 9, `test_text_roles_meet_wcag_aa`.

---

### Task 1: Dev harness and baseline screenshots

**Files:**
- Create: `product/README.md`
- Create: `product/.gitignore`
- Create: `product/__init__.py`, `product/dev/__init__.py`, `product/tests/__init__.py` (empty)
- Create: `product/dev/lo-make.sh`
- Create: `product/dev/profile.py`
- Create: `product/dev/shot.sh`
- Test: `product/tests/test_profile.py`

**Interfaces:**
- Produces:
  - `product/dev/lo-make.sh <make args...>` runs `make -C <core> PARALLELISM=6 <args>` inside the memory cap and returns make's exit code.
  - `product/dev/profile.py`
    - CLI: `--ui {default,compact,tabbed,office} --appearance {light,dark} [--icons NAME] [--scheme NAME] [--tint N] [--profile DIR]`. It writes `DIR/user/registrymodifications.xcu` and prints the path.
    - Python API:
      - `build_items(ui, appearance, icons=None, scheme=None, tint=None) -> list[tuple[str, str, str]]`
      - `render(items) -> str`
      - `write(profile: Path, items) -> Path`
      - constants `CALC_APP`, `TOOLBAR_MODE`
  - `product/dev/shot.sh OUT.png [full|WIDTHxHEIGHT]`
    - Env: `LO_PROFILE` (default `/mnt/games/libreoffice/dev-profile`) and `LO_GTK_THEME` (default `adw-gtk3-dark`).
    - Starts Calc, screenshots its window and closes it.

- [ ] **Step 1: Create the branch**

```bash
git -C /mnt/games/libreoffice/core switch -c feature/calc-home-redesign 62abc2329664
```

Expected: `Switched to a new branch 'feature/calc-home-redesign'`.

- [ ] **Step 2: Write the failing profile test**

`product/tests/test_profile.py`:

```python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from product.dev import profile

OOR = "{http://openoffice.org/2001/registry}"
APPEARANCE = "/org.openoffice.Office.Common/Appearance"
MISC = "/org.openoffice.Office.Common/Misc"
SCHEME = "/org.openoffice.Office.UI/ColorScheme"


def props(xml):
    root = ET.fromstring(xml)
    out = {}
    for item in root.findall("item"):
        prop = item.find("prop")
        out[(item.get(OOR + "path"), prop.get(OOR + "name"))] = prop.find("value").text
    return out


class ProfileTest(unittest.TestCase):

    def test_office_dark_with_theme(self):
        p = props(profile.render(profile.build_items(
            "office", "dark", icons="boost_dark", scheme="Boost Dark", tint=255)))
        self.assertEqual(p[(profile.CALC_APP, "Active")], "notebookbar_office.ui")
        self.assertEqual(p[(profile.TOOLBAR_MODE, "ActiveCalc")], "notebookbar_office.ui")
        self.assertEqual(p[(APPEARANCE, "ApplicationAppearance")], "2")
        self.assertEqual(p[(MISC, "SymbolStyle")], "boost_dark")
        self.assertEqual(p[(APPEARANCE, "LibreOfficeTheme")], "1")
        self.assertEqual(p[(SCHEME, "CurrentColorScheme")], "Boost Dark")
        self.assertEqual(p[(MISC, "NotebookbarColorTransparency")], "255")

    def test_baseline_has_no_theme_items(self):
        p = props(profile.render(profile.build_items("compact", "light")))
        self.assertEqual(p[(profile.CALC_APP, "Active")], "notebookbar_compact.ui")
        self.assertEqual(p[(APPEARANCE, "ApplicationAppearance")], "1")
        self.assertNotIn((APPEARANCE, "LibreOfficeTheme"), p)
        self.assertNotIn((MISC, "SymbolStyle"), p)
        self.assertNotIn((MISC, "NotebookbarColorTransparency"), p)

    def test_default_ui_sets_no_notebookbar_file(self):
        p = props(profile.render(profile.build_items("default", "light")))
        self.assertEqual(p[(profile.CALC_APP, "Active")], "Default")
        self.assertNotIn((profile.TOOLBAR_MODE, "ActiveCalc"), p)

    def test_write_creates_the_user_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = profile.write(Path(tmp), profile.build_items("tabbed", "light"))
            self.assertEqual(path, Path(tmp) / "user" / "registrymodifications.xcu")
            self.assertIn("<value>notebookbar.ui</value>", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to make sure it fails**

Run: `python3 -I -m unittest discover -s product/tests -t .`
Expected: an ERROR containing `ModuleNotFoundError: No module named 'product'`. The package files do not exist yet.

- [ ] **Step 4: Write the package files, `profile.py` and the scripts**

`product/__init__.py`, `product/dev/__init__.py` and `product/tests/__init__.py` are empty files.

`product/README.md`:

```markdown
# product/

Product-only tooling for the LibreOffice-based suite (working name "boost").
gbuild ignores this directory. Nothing here is meant for upstream.

- `dev/`: memory-capped builds, the isolated dev profile, screenshots, UI checks.
- `ui/`: the ribbon layout generator and layouts.
- `icons/`: the Fluent-based icon theme builder.
- `themes/`: the color scheme extension builder.
- `product/docs/`: findings from the stage A spikes.
- `tests/`: unit tests: `python3 -I -m unittest discover -s product/tests -t .`
```

`product/.gitignore`:

```
__pycache__/
out/
```

`product/dev/lo-make.sh` (then run `chmod +x product/dev/lo-make.sh`):

```bash
#!/usr/bin/env bash
# Run gbuild in the LibreOffice core checkout under a memory cap.
# A full -j10 build froze the 14 GB dev machine on 2026-10-12; confining make
# to a cgroup scope keeps the desktop responsive (peak observed: 4.8 GB at -j6).
set -euo pipefail
core="$(cd "$(dirname "$0")/../.." && pwd)"
exec systemd-run --user --scope --quiet \
    -p MemoryHigh=6G -p MemoryMax=7G -p MemorySwapMax=1G \
    nice -n 10 make -C "$core" PARALLELISM="${PARALLELISM:-6}" "$@"
```

`product/dev/profile.py`:

```python
#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Write registrymodifications.xcu for the isolated LibreOffice dev profile."""
import argparse
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

DEFAULT_PROFILE = Path("/mnt/games/libreoffice/dev-profile")
TOOLBAR_MODE = "/org.openoffice.Office.UI.ToolbarMode"
CALC_APP = TOOLBAR_MODE + "/Applications/org.openoffice.Office.UI.ToolbarMode:Application['Calc']"
APPEARANCE = "/org.openoffice.Office.Common/Appearance"
MISC = "/org.openoffice.Office.Common/Misc"

# ui choice -> (Applications/Calc/Active, ActiveCalc). Active holds the mode's
# CommandArg (sfx2/source/appl/appserv.cxx:1015); ActiveCalc names the .ui file.
UI_MODES = {
    "default": ("Default", None),
    "compact": ("notebookbar_compact.ui", "notebookbar_compact.ui"),
    "tabbed": ("notebookbar.ui", "notebookbar.ui"),
    "office": ("notebookbar_office.ui", "notebookbar_office.ui"),
}
# Office.Common/Appearance/ApplicationAppearance: 0 system, 1 light, 2 dark.
APPEARANCES = {"light": "1", "dark": "2"}


def build_items(ui, appearance, icons=None, scheme=None, tint=None):
    active, ui_file = UI_MODES[ui]
    items = [(CALC_APP, "Active", active)]
    if ui_file:
        items.append((TOOLBAR_MODE, "ActiveCalc", ui_file))
    items.append((APPEARANCE, "ApplicationAppearance", APPEARANCES[appearance]))
    if icons:
        items.append((MISC, "SymbolStyle", icons))
    if scheme:
        # The theme engine ignores color schemes unless LibreOfficeTheme is 1.
        items.append((APPEARANCE, "LibreOfficeTheme", "1"))
        items.append(("/org.openoffice.Office.UI/ColorScheme", "CurrentColorScheme", scheme))
    if tint is not None:
        items.append((MISC, "NotebookbarColorTransparency", str(tint)))
    # Keep screenshots free of first-start and tip dialogs.
    items.append((MISC, "FirstRun", "false"))
    items.append((MISC, "ShowTipOfTheDay", "false"))
    return items


def render(items):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<oor:items xmlns:oor="http://openoffice.org/2001/registry"'
        ' xmlns:xs="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
    ]
    for path, name, value in items:
        lines.append(f'<item oor:path={quoteattr(path)}><prop oor:name="{name}" oor:op="fuse">'
                     f'<value>{escape(value)}</value></prop></item>')
    lines.append("</oor:items>")
    return "\n".join(lines) + "\n"


def write(profile, items):
    path = Path(profile) / "user" / "registrymodifications.xcu"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(items), encoding="utf-8")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ui", choices=sorted(UI_MODES), required=True)
    ap.add_argument("--appearance", choices=sorted(APPEARANCES), required=True)
    ap.add_argument("--icons")
    ap.add_argument("--scheme")
    ap.add_argument("--tint", type=int)
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    args = ap.parse_args(argv)
    print(write(args.profile, build_items(args.ui, args.appearance, args.icons, args.scheme, args.tint)))


if __name__ == "__main__":
    main()
```

`product/dev/shot.sh` (then run `chmod +x product/dev/shot.sh`):

```bash
#!/usr/bin/env bash
# Screenshot the dev build's Calc window on Hyprland.
# Usage: shot.sh OUT.png [full|WIDTHxHEIGHT]
# Env:   LO_PROFILE   isolated profile dir (default /mnt/games/libreoffice/dev-profile)
#        LO_GTK_THEME GTK theme for the run (default adw-gtk3-dark; adw-gtk3 for light)
set -euo pipefail
out="$1"
size="${2:-full}"
core="$(cd "$(dirname "$0")/../.." && pwd)"
profile="${LO_PROFILE:-/mnt/games/libreoffice/dev-profile}"
mkdir -p "$(dirname "$out")"

GTK_THEME="${LO_GTK_THEME:-adw-gtk3-dark}" SAL_USE_VCLPLUGIN=gtk3 \
    "$core/instdir/program/soffice" --calc --norestore --nologo \
    "-env:UserInstallation=file://$profile" >/dev/null 2>&1 &

addr=""
for _ in $(seq 120); do
    addr=$(hyprctl clients -j | jq -r '[.[] | select(.title | test("Calc"))][0].address // empty')
    [ -n "$addr" ] && break
    sleep 0.5
done
if [ -z "$addr" ]; then
    echo "no Calc window after 60 s" >&2
    pkill -f "UserInstallation=file://$profile" || true
    exit 1
fi

hyprctl dispatch focuswindow "address:$addr" >/dev/null
if [ "$size" = full ]; then
    hyprctl dispatch fullscreen 0 >/dev/null
else
    hyprctl dispatch setfloating "address:$addr" >/dev/null
    hyprctl dispatch resizewindowpixel "exact ${size%x*} ${size#*x},address:$addr" >/dev/null
    hyprctl dispatch centerwindow >/dev/null
fi
sleep 3  # let the ribbon re-layout and repaint at the new size

geom=$(hyprctl clients -j | jq -r --arg a "$addr" \
    '.[] | select(.address == $a) | "\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"')
grim -g "$geom" "$out"

hyprctl dispatch closewindow "address:$addr" >/dev/null || true
sleep 2
pkill -f "UserInstallation=file://$profile" || true
echo "$out"
```

- [ ] **Step 5: Run the tests to make sure they pass**

Run: `python3 -I -m unittest discover -s product/tests -t .`
Expected: `Ran 4 tests` ... `OK`.

- [ ] **Step 6: Check the build wrapper**

Run: `product/dev/lo-make.sh build gb_SUPPRESS_TESTS=1; echo "exit $?"`
Expected: `exit 0` within a few minutes, because the tree is already built. While it runs, `systemctl --user list-units --type=scope` lists a `run-*.scope` unit.

- [ ] **Step 7: Take the baseline screenshots**

Run, one block at a time:

```bash
P=/mnt/games/libreoffice/assets/previews
python3 -I product/dev/profile.py --ui compact --appearance dark
product/dev/shot.sh $P/baseline-compact-dark.png
python3 -I product/dev/profile.py --ui tabbed --appearance dark
product/dev/shot.sh $P/baseline-tabbed-dark.png
python3 -I product/dev/profile.py --ui compact --appearance light
LO_GTK_THEME=adw-gtk3 product/dev/shot.sh $P/baseline-compact-light.png
python3 -I product/dev/profile.py --ui tabbed --appearance light
LO_GTK_THEME=adw-gtk3 product/dev/shot.sh $P/baseline-tabbed-light.png
```

Expected:
- Four PNGs at 1920x1080. Check with `magick identify $P/baseline-*.png`.
- Look at each one with the Read tool. The Calc ribbon must be visible, with no start-center, first-run or tip dialog.
- If a dialog or infobar covers the window, find its config key in `officecfg/registry/schema/org/openoffice/Office/Common.xcs`, add it to `build_items` as one more `(MISC, "<Key>", "false")` item with a line in `test_profile.py`, and retake.

- [ ] **Step 8: Commit**

```bash
git add product/
git commit -m "chore(product): add capped build wrapper, dev profile and screenshot tools"
```

---

### Task 2: Tabbed Office variant skeleton (answers spike 0e)

**Files:**
- Create: `sc/uiconfig/scalc/ui/notebookbar_office.ui`. A byte-identical copy of `notebookbar.ui`.
- Modify: `sc/UIConfig_scalc.mk`. Add one line after `:173`.
- Modify: `officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu`. Add a node after the Calc `Tabbed` node, which ends at `:408`.
- Modify: `solenv/sanitizers/ui/modules/scalc.suppr`. Append copies of the `notebookbar.ui` lines.
- Create: `product/dev/uitest.sh`
- Create: `product/dev/check-ui.sh`
- Create: `product/docs/stage-a-findings.md`
- Test: `sc/qa/uitest/calc_tests/notebookbarOffice.py`

**Interfaces:**
- Consumes: `product/dev/lo-make.sh` (Task 1).
- Produces:
  - Calc mode `.uno:ToolbarMode?Mode:string=notebookbar_office.ui`
  - UITest class `notebookbarOffice.NotebookbarOffice`
  - `product/dev/uitest.sh NAME...`
  - `product/dev/check-ui.sh FILE.ui...`
  - The findings file `product/docs/stage-a-findings.md`, with one `## 0x` heading per spike.

- [ ] **Step 1: Write the failing UITest**

`sc/qa/uitest/calc_tests/notebookbarOffice.py`:

```python
# -*- tab-width: 4; indent-tabs-mode: nil; py-indent-offset: 4 -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
from uitest.framework import UITestCase
from uitest.uihelper.common import get_state_as_dict

OFFICE_UI = "notebookbar_office.ui"


class NotebookbarOffice(UITestCase):

    def switch_to(self, ui_file):
        self.xUITest.executeCommand(".uno:ToolbarMode?Mode:string=" + ui_file)

    def test_office_variant_loads(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                xHome = xCalcDoc.getChild("phbHome")
                self.assertEqual("true", get_state_as_dict(xHome)["Visible"])
            finally:
                self.switch_to("Default")

    def test_switch_back_to_compact(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            self.switch_to("notebookbar_compact.ui")
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                # NewDocSection exists only in notebookbar_compact.ui
                xCalcDoc.getChild("NewDocSection")
            finally:
                self.switch_to("Default")

# vim: set shiftwidth=4 softtabstop=4 expandtab:
```

`product/dev/uitest.sh` (then run `chmod +x`):

```bash
#!/usr/bin/env bash
# Run Calc UITests one by one. Names must be full: module.Class.test
# (uitest/test_main.py only filters on an exact full name).
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
core="$(cd "$here/../.." && pwd)"
status=0
for name in "$@"; do
    echo "== $name"
    if ! "$here/lo-make.sh" UITest_calc_tests UITEST_TEST_NAME="$name"; then
        status=1
        tail -n 40 "$core/workdir/UITest/calc_tests/done.log" 2>/dev/null || true
    fi
done
exit $status
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.test_office_variant_loads`
Expected: FAIL. The log shows an exception from `getChild("phbHome")`, because `notebookbar_office.ui` is not installed, so no notebookbar is created.

If the test PASSES at this point, LibreOffice fell back to another notebookbar file and the test proves nothing.
- Record that in the findings file under `## 0e`.
- Change the test to also assert that `notebookbar_office.ui` exists under `instdir/share/config/soffice.cfg/modules/scalc/ui/`.
- Locate instdir as `Path(os.environ["TDOC"]).parents[3] / "instdir"`. `TDOC` is `<src>/sc/qa/uitest/data`, so `parents[3]` is the source root.

- [ ] **Step 3: Add the variant**

1. Copy the file:
   ```bash
   cp sc/uiconfig/scalc/ui/notebookbar.ui sc/uiconfig/scalc/ui/notebookbar_office.ui
   ```

2. In `sc/UIConfig_scalc.mk`, after the line `	sc/uiconfig/scalc/ui/notebookbar_groupedbar_compact \` (`:173`), add:
   ```
       sc/uiconfig/scalc/ui/notebookbar_office \
   ```

3. In `ToolbarMode.xcu`, directly after the `</node>` that closes the Calc `Tabbed` node (`:408`), insert:
   ```xml
           <node oor:name="TabbedOffice" oor:op="replace">
             <prop oor:name="Label">
               <value xml:lang="en-US">Tabbed Office</value>
             </prop>
             <prop oor:name="HasNotebookbar">
               <value>true</value>
             </prop>
             <prop oor:name="IsExperimental">
               <value>false</value>
             </prop>
             <prop oor:name="MenuPosition">
               <value>9</value>
             </prop>
             <prop oor:name="CommandArg">
               <value>notebookbar_office.ui</value>
             </prop>
             <prop oor:name="Toolbars">
               <value>
               </value>
             </prop>
             <prop oor:name="UserToolbars">
               <value>
               </value>
             </prop>
             <prop oor:name="Sidebar">
               <value>Arrow</value>
             </prop>
           </node>
   ```

4. Duplicate the suppressions with the new path. The path is part of each suppression key.
   ```bash
   rg '^sc/uiconfig/scalc/ui/notebookbar\.ui:' solenv/sanitizers/ui/modules/scalc.suppr \
     | sd '^sc/uiconfig/scalc/ui/notebookbar\.ui:' 'sc/uiconfig/scalc/ui/notebookbar_office.ui:' \
     > /tmp/office.suppr
   bat -p /tmp/office.suppr >> solenv/sanitizers/ui/modules/scalc.suppr && rm /tmp/office.suppr
   ```
   Expected: `rg -c 'notebookbar_office.ui:' solenv/sanitizers/ui/modules/scalc.suppr` equals `rg -c 'scalc/ui/notebookbar.ui:' solenv/sanitizers/ui/modules/scalc.suppr`.

`product/dev/check-ui.sh` (then run `chmod +x`). It uses the same gla11y parameters as `solenv/gbuild/UIConfig.mk:132-150`:

```bash
#!/usr/bin/env bash
# Run the build's accessibility check (bin/gla11y) and bin/lint-ui.py on Calc .ui files.
set -euo pipefail
core="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$core"
report="$(mktemp)"
trap 'rm -f "$report"' EXIT
status=0
python3 -I bin/gla11y -P ./ -f solenv/sanitizers/ui/modules/scalc.false \
    -s solenv/sanitizers/ui/modules/scalc.suppr \
    --widgets-suffixignored +ValueSet,HBox,VBox,ToolBox,Preview,PreviewWin,PreviewWindow,PrevWindow \
    --widgets-button +svtlo-ManagedMenuButton \
    --fatal-all --not-fatal-type duplicate-mnemonic --not-fatal-type labelled-by-and-mnemonic \
    --not-fatal-type orphan-label -o "$report" "$@" || status=1
printf '%s\n' "$(<"$report")"
python3 -I bin/lint-ui.py "$@" || status=1
exit $status
```

`product/docs/stage-a-findings.md`:

```markdown
# Stage A spike findings

Each section records the question, what was tried, the observed result and the decision.
Spec: product/docs/superpowers/specs/2026-10-12-calc-home-redesign-design.md §6.

## 0a Declarative dropdown menus

## 0b Theme engine reach under gtk3

## 0c Custom scheme switching with the system

## 0d Runtime packaging (icon zip drop-in, configuration-only extension)

## 0e UITest access to notebookbar widgets
```

- [ ] **Step 4: Build and run the tests to make sure they pass**

```bash
product/dev/check-ui.sh sc/uiconfig/scalc/ui/notebookbar_office.ui
product/dev/lo-make.sh build gb_SUPPRESS_TESTS=1
product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.test_office_variant_loads \
                      notebookbarOffice.NotebookbarOffice.test_switch_back_to_compact
```

Expected:
- `check-ui.sh` prints no fatal lines and exits 0.
- The build exits 0.
- Both UITests PASS.

If `getChild("phbHome")` fails even though the variant loads (spike 0e = NO):
- Record that under `## 0e`.
- Replace the two `getChild` assertions with configuration reads, and rely on the static tests of Task 6 for the content. Add `from libreoffice.uno.propertyvalue import mkPropertyValues` and this helper; `self.xContext` is set in `uitest/uitest/framework.py:33`:

  ```python
      def active_calc_ui(self):
          provider = self.xContext.ServiceManager.createInstanceWithContext(
              "com.sun.star.configuration.ConfigurationProvider", self.xContext)
          access = provider.createInstanceWithArguments(
              "com.sun.star.configuration.ConfigurationAccess",
              mkPropertyValues({"nodepath": "/org.openoffice.Office.UI.ToolbarMode"}))
          return access.getByName("ActiveCalc")
  ```

  Then assert `self.assertEqual(OFFICE_UI, self.active_calc_ui())` after switching to Tabbed Office, and `self.assertEqual("notebookbar_compact.ui", self.active_calc_ui())` after switching back.

- [ ] **Step 5: Record spike 0e**

Under `## 0e` in `product/docs/stage-a-findings.md`, write what was tried (getChild by id after `.uno:ToolbarMode`), the result (YES or NO) and the evidence (test names and PASS/FAIL).

- [ ] **Step 6: Commit**

```bash
git add sc/uiconfig/scalc/ui/notebookbar_office.ui sc/UIConfig_scalc.mk \
  officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu \
  solenv/sanitizers/ui/modules/scalc.suppr sc/qa/uitest/calc_tests/notebookbarOffice.py \
  product/dev/uitest.sh product/dev/check-ui.sh product/docs/stage-a-findings.md
git commit -m "feat(sc): add Tabbed Office notebookbar variant for Calc"
```

---

### Task 3: Spike 0a, dropdown menus without C++

This spike produces a decision, not kept code. Every probe edit is reverted before the commit.

**Files:**
- Modify temporarily: `sc/uiconfig/scalc/ui/notebookbar_office.ui`, `officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu`
- Modify: `product/docs/stage-a-findings.md` (section `## 0a`)

**Interfaces:**
- Produces: a route decision, exactly one of `P3`, `P2` or `FALLBACK`, written as the first line under `## 0a`, e.g. `Decision: P3`. Task 6 reads it.

Background (spec §6):
- A toolbox item whose dropdown comes from a popup menu file normally needs a `.uno:` slot plus a Controller.xcu entry, as with `.uno:RowOperations` (`sc/sdi/scalc.sdi:2254`, `Controller.xcu:375` and `:2068`, `sc/uiconfig/scalc/popupmenu/row_operations.xml`).
- `PopupMenuToolbarController` treats a popup command starting with `private:resource/` as a menu resource (`framework/source/uielement/popuptoolbarcontroller.cxx:93-118`, `:220-227`).

The two candidate routes:
- **P3:** use `private:resource/popupmenu/<name>` directly as the button's `action-name` in the `.ui`. This needs no upstream config edit.
- **P2:** keep an existing command (e.g. `.uno:InsertCell`) as a split button. Add a module-scoped `GenericPopupToolbarController` entry whose `Value` is `private:resource/popupmenu/<name>` (`Controller.xcu:834-835` uses `Value` the same way).

- [ ] **Step 1: Probe P3**

1. In `notebookbar_office.ui`, find `<object class="GtkMenuToolButton" id="btnHomeRowOperations">`. Replace its `action-name` value with `private:resource/popupmenu/row_operations`, and add inside the same object:
   ```xml
   <property name="label" translatable="yes" context="TabbedCalc|btnHomeRowOperations">Rows</property>
   <property name="icon_name">cmd/lc_insertrowsbefore.png</property>
   ```
2. Run:
   ```bash
   product/dev/lo-make.sh sc.build
   python3 -I product/dev/profile.py --ui office --appearance dark
   product/dev/shot.sh /mnt/games/libreoffice/assets/previews/spike-0a-p3.png
   ```
3. Look at the screenshot. Agents cannot click in the GUI, so hand the click test to the human partner through the orchestrator. Ask them to run `instdir/program/soffice --calc -env:UserInstallation=file:///mnt/games/libreoffice/dev-profile`, click the "Rows" button and its arrow, and report back.
4. Write down four facts:
   - (a) The item shows the label "Rows" and an icon.
   - (b) It is enabled.
   - (c) Clicking it, or its arrow, opens the Rows menu.
   - (d) Choosing "Insert Rows Above" inserts a row.

- [ ] **Step 2: Probe P2**

1. Revert P3 with `git checkout -- sc/uiconfig/scalc/ui/notebookbar_office.ui`.
2. In `notebookbar_office.ui`, change `btnHomeRowOperations`'s `action-name` to `.uno:InsertCell`.
3. In `Controller.xcu`, inside the ToolBar section and next to `RowOperationsControl` (`:2068`), add:
   ```xml
       <node oor:name="ProbeInsertCellControl" oor:op="replace">
         <prop oor:name="Command">
           <value>.uno:InsertCell</value>
         </prop>
         <prop oor:name="Module">
           <value>com.sun.star.sheet.SpreadsheetDocument</value>
         </prop>
         <prop oor:name="Controller">
           <value>com.sun.star.comp.framework.GenericPopupToolbarController</value>
         </prop>
         <prop oor:name="Value">
           <value>private:resource/popupmenu/row_operations</value>
         </prop>
       </node>
   ```
4. Run `product/dev/lo-make.sh officecfg.build postprocess.build sc.build`. Then ask the human partner, through the orchestrator as in P3, to try the button and its arrow.
5. Write down three facts:
   - (a) The main part runs Insert Cells.
   - (b) The arrow opens the Rows menu.
   - (c) Every Calc toolbar or notebookbar file that also uses each candidate command would change, because the controller is module-wide. List them:
     ```bash
     rg -l 'uno:(InsertCell|DeleteCell|FormatCellDialog|FillDown|Delete|DataSort|SearchDialog|ToggleMergeCells)<' \
        sc/uiconfig/scalc/toolbar sc/uiconfig/scalc/ui
     ```

- [ ] **Step 3: Decide and revert**

Decision rule:
- `P3` if all of 1a-1d hold.
- Otherwise `P2` if 2a and 2b hold and the list from 2c is empty apart from `notebookbar_office.ui`.
- Otherwise `FALLBACK`.

Revert every probe edit:

```bash
git checkout -- sc/uiconfig/scalc/ui/notebookbar_office.ui \
  officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu
git status --short   # must show only product/docs/stage-a-findings.md
```

Fill `## 0a` with the decision line, the facts and the screenshot path.

- [ ] **Step 4: Commit**

```bash
git add product/docs/stage-a-findings.md
git commit -m "docs(product): record spike 0a on declarative ribbon dropdown menus"
```

---

### Task 4: Spikes 0b, 0c and 0d (theme reach, scheme switching, runtime packaging)

The probe files are throwaway and live outside the repository, in `/mnt/games/libreoffice/spike/`.

**Files:**
- Modify: `product/docs/stage-a-findings.md` (sections `## 0b`, `## 0c`, `## 0d`)

**Interfaces:**
- Consumes: `profile.py`, `shot.sh` (Task 1); the Tabbed Office mode (Task 2).
- Produces:
  - Findings that Task 9 and Task 10 rely on: which ribbon parts follow which ThemeColors role, whether the custom scheme auto-switches, and whether the drop-in zip and the extension both work.
  - A gaps list under `## 0b` that names stage B work.

- [ ] **Step 1: Build the probe icon zip and the probe scheme extension**

```bash
S=/mnt/games/libreoffice/spike; mkdir -p $S/zip/cmd/32 $S/oxt/META-INF
magick -size 16x16 xc:'#FF0000' $S/zip/cmd/sc_bold.png
magick -size 24x24 xc:'#FF0000' $S/zip/cmd/lc_paste.png
magick -size 32x32 xc:'#FF0000' $S/zip/cmd/32/paste.png
(cd $S/zip && zip -qr ../images_probe.zip cmd)
```

Write these three files.

`$S/oxt/description.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<description xmlns="http://openoffice.org/extensions/description/2006"
             xmlns:xlink="http://www.w3.org/1999/xlink">
  <identifier value="org.boost.probe-scheme"/>
  <version value="0.0.1"/>
  <display-name><name lang="en">Probe color scheme</name></display-name>
</description>
```

`$S/oxt/META-INF/manifest.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="http://openoffice.org/2001/manifest">
  <manifest:file-entry manifest:media-type="application/vnd.sun.star.configuration-data"
                       manifest:full-path="ColorSchemes.xcu"/>
</manifest:manifest>
```

`$S/oxt/ColorSchemes.xcu`. Each role gets a loud, distinct color, so a screenshot shows which role paints what:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<oor:component-data xmlns:oor="http://openoffice.org/2001/registry"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" oor:name="UI" oor:package="org.openoffice.Office">
  <node oor:name="ColorScheme">
    <node oor:name="ColorSchemes">
      <node oor:name="Boost Probe" oor:op="replace">
        <node oor:name="WindowColor"><prop oor:name="Color"><value>16711935</value></prop></node>
        <node oor:name="WindowTextColor"><prop oor:name="Color"><value>128</value></prop></node>
        <node oor:name="BaseColor"><prop oor:name="Color"><value>65535</value></prop></node>
        <node oor:name="FieldColor"><prop oor:name="Color"><value>8454143</value></prop></node>
        <node oor:name="ButtonColor"><prop oor:name="Color"><value>16776960</value></prop></node>
        <node oor:name="ButtonTextColor"><prop oor:name="Color"><value>8388608</value></prop></node>
        <node oor:name="FaceColor"><prop oor:name="Color"><value>65280</value></prop></node>
        <node oor:name="SeparatorColor"><prop oor:name="Color"><value>16711680</value></prop></node>
        <node oor:name="AccentColor"><prop oor:name="Color"><value>16744448</value></prop></node>
        <node oor:name="ActiveColor"><prop oor:name="Color"><value>255</value></prop></node>
        <node oor:name="MenuColor"><prop oor:name="Color"><value>8421631</value></prop></node>
        <node oor:name="MenuTextColor"><prop oor:name="Color"><value>16384</value></prop></node>
        <node oor:name="MenuHighlightColor"><prop oor:name="Color"><value>16744640</value></prop></node>
        <node oor:name="MenuBarColor"><prop oor:name="Color"><value>12632064</value></prop></node>
      </node>
    </node>
  </node>
</oor:component-data>
```

Key for the screenshots:

| Color | Role |
|-------|------|
| magenta | Window |
| navy | WindowText |
| cyan | Base |
| light cyan | Field |
| yellow | Button |
| maroon | ButtonText |
| green | Face |
| red | Separator |
| orange | Accent |
| blue | Active |
| periwinkle | Menu |
| dark green | MenuText |
| pink | MenuHighlight |
| olive | MenuBar |

Package and install:

```bash
(cd $S/oxt && zip -qr ../probe-scheme.oxt description.xml META-INF ColorSchemes.xcu)
instdir/program/unopkg add -f $S/probe-scheme.oxt \
  -env:UserInstallation=file:///mnt/games/libreoffice/dev-profile
cp $S/images_probe.zip instdir/share/config/
```

Expected: `unopkg` exits 0, and `instdir/program/unopkg list -env:UserInstallation=file:///mnt/games/libreoffice/dev-profile` lists `org.boost.probe-scheme`.

- [ ] **Step 2: Observe (0b, 0d)**

```bash
P=/mnt/games/libreoffice/assets/previews
python3 -I product/dev/profile.py --ui office --appearance dark --icons probe --scheme "Boost Probe" --tint 255
product/dev/shot.sh $P/spike-0b-probe-dark.png
```

Look at the screenshot and record:
- Under `## 0d`:
  - Does Bold show a red 16 px square, and Paste a red 24 px square? That proves the drop-in zip works, with `icon_size` 3 meaning 24 px.
  - Do the other icons still show Colibre (dark)? That proves the fallback.
  - Does the extension's scheme apply at all? That proves the configuration-only extension works.
- Under `## 0b`, for each ribbon area, which probe color it shows or "unchanged": ribbon background, tab strip, active tab, tab text, toolbox button background, button text and captions, font name combo field, separators between sections, the menu bar and an open menu.

Agents cannot click in the GUI, so ask the human partner, through the orchestrator, for three checks:
- Open the Format menu and send a screenshot (`grim -g "$(slurp)" <path>`).
- Hover a ribbon button and report the hover color.
- Press a toggle button such as Bold and report the pressed color.

Write their answers down as "reported by the user".

- [ ] **Step 3: Observe (0c)**

```bash
python3 -I product/dev/profile.py --ui office --appearance dark --icons probe --scheme "Boost Probe" --tint 255
sd '<value>2</value></prop></item>' '<value>0</value></prop></item>' /mnt/games/libreoffice/dev-profile/user/registrymodifications.xcu
LO_GTK_THEME=adw-gtk3 product/dev/shot.sh $P/spike-0c-system-light.png
LO_GTK_THEME=adw-gtk3-dark product/dev/shot.sh $P/spike-0c-system-dark.png
```

The `sd` line switches ApplicationAppearance to 0, meaning "follow the system". It only matches that one item, because it is the only `<value>2</value>`.

Expected, from code reading (`svtools/source/config/colorcfg.cxx:628-641`): the probe colors are identical in both shots, because explicitly set colors do not follow the OS. Record YES or NO under `## 0c`, with both paths.

- [ ] **Step 4: Clean up the probes**

```bash
instdir/program/unopkg remove org.boost.probe-scheme \
  -env:UserInstallation=file:///mnt/games/libreoffice/dev-profile
rm instdir/share/config/images_probe.zip
```

Expected: `unopkg list` no longer shows the probe.

- [ ] **Step 5: Commit**

```bash
git add product/docs/stage-a-findings.md
git commit -m "docs(product): record spikes 0b-0d on theme reach, scheme switching and packaging"
```

---

### Task 5: Ribbon page generator

**Files:**
- Create: `product/ui/__init__.py` (empty)
- Create: `product/ui/gen_ribbon.py`
- Test: `product/tests/test_gen_ribbon.py`

**Interfaces:**
- Produces:
  - `product/ui/gen_ribbon.py --layout FILE.json --ui REPO_RELATIVE.ui --suppr FILE.suppr`. It rewrites the page in place and syncs the suppressions.
  - Python API:
    - `LayoutError`
    - `validate(layout)`
    - `emit_page(layout) -> list[str]`
    - `splice(ui_text, layout, generated) -> str`
    - `sync_suppr(suppr_text, ui_rel_path, ui_text) -> str`
    - `ids_of(layout)`
- Layout JSON schema, used by Task 6:
  - `page`: id of the tab page box, e.g. `phbHome`.
  - `id_prefix`: e.g. `Home`.
  - `context`: translation context prefix, e.g. `TabbedCalc`.
  - `remove_objects`: list of ids of objects to delete anywhere in the file.
  - `sections`: list of objects with these keys:
    - `name`
    - `caption`
    - `rows` (content rows)
    - `columns`: a list of columns. Each column is a list of toolboxes, stacked from row 0. A toolbox is `{id, style: large|small|small-label, items: [...]}`.
  - Items: `{cmd, kind: button|split (default button), action (default ".uno:"+cmd), label?, icon?}`.
- Generated ids:
  - `pmhb<P>`
  - per section: `ob<P><Name>` (VclOptionalBox, class `priority-<N>`, where the leftmost section gets the highest N), `gd<P><Name>` (GtkGrid) and `lb<P><Name>` (caption)
  - `bx<P><Toolbox>` per toolbox and `btn<P><Cmd>` per item
- Markers: `<!-- product:<P>-begin -->` and `<!-- product:<P>-end -->`.

- [ ] **Step 1: Write the failing tests**

`product/tests/test_gen_ribbon.py`:

```python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import copy
import unittest
from xml.etree import ElementTree as ET

from product.ui import gen_ribbon as g

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<interface domain="sc">
  <object class="GtkMenu" id="Menu Home">
    <property name="visible">True</property>
    <child>
      <object class="GtkMenuItem" id="MenuHome-Old">
        <property name="visible">True</property>
      </object>
    </child>
  </object>
  <object class="GtkBox" id="Root">
    <child>
      <object class="sfxlo-PriorityHBox" id="phbHome">
        <property name="visible">True</property>
        <child>
          <object class="GtkToolButton" id="btnHomeOld">
            <property name="action-name">.uno:Old</property>
          </object>
        </child>
      </object>
      <packing>
        <property name="position">1</property>
      </packing>
    </child>
    <child>
      <object class="GtkLabel" id="keepMe">
        <property name="label">x</property>
      </object>
    </child>
  </object>
</interface>
"""

LAYOUT = {
    "page": "phbHome", "id_prefix": "Home", "context": "TabbedCalc",
    "remove_objects": ["Menu Home"],
    "sections": [
        {"name": "Clipboard", "caption": "Clipboard", "rows": 3, "columns": [
            [{"id": "Paste", "style": "large", "items": [{"cmd": "Paste", "kind": "split"}]}],
            [{"id": "Cut", "style": "small-label", "items": [{"cmd": "Cut"}]},
             {"id": "Copy", "style": "small-label", "items": [{"cmd": "Copy"}]}]]},
        {"name": "Font", "caption": "Font", "rows": 2, "columns": [
            [{"id": "FormatRow", "style": "small", "items": [{"cmd": "Bold"}, {"cmd": "Italic"}]}]]},
    ],
}


def generate(text=FIXTURE, layout=LAYOUT):
    return g.splice(text, layout, g.emit_page(layout))


def placed(root, obj_id):
    """Return (object element, packing element) for the <child> holding obj_id."""
    for child in root.iter("child"):
        obj = child.find("object")
        if obj is not None and obj.get("id") == obj_id:
            return obj, child.find("packing")
    raise AssertionError(f"{obj_id} not found")


class GenRibbonTest(unittest.TestCase):

    def test_output_is_well_formed_xml(self):
        ET.fromstring(generate())

    def test_old_page_content_and_removed_objects_are_gone(self):
        out = generate()
        self.assertNotIn("btnHomeOld", out)
        self.assertNotIn('id="Menu Home"', out)
        self.assertNotIn("MenuHome-Old", out)

    def test_lines_outside_the_page_are_unchanged(self):
        out = generate()
        self.assertTrue(out.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<interface domain="sc">\n'))
        tail = FIXTURE[FIXTURE.index("      <packing>\n        <property name=\"position\">1</property>"):]
        self.assertTrue(out.endswith(tail))

    def test_sections_have_caption_relation_and_priority(self):
        root = ET.fromstring(generate())
        grid = root.find(".//object[@id='gdHomeClipboard']")
        self.assertEqual("lbHomeClipboard", grid.find("accessibility/relation").get("target"))
        label = root.find(".//object[@id='lbHomeClipboard']")
        text = label.find("property[@name='label']")
        self.assertEqual("Clipboard", text.text)
        self.assertEqual("TabbedCalc|labelHomeClipboard", text.get("context"))
        self.assertIsNone(label.find("attributes/attribute[@name='style']"))
        self.assertEqual("0.9", label.find("attributes/attribute[@name='scale']").get("value"))
        self.assertEqual("priority-2", root.find(".//object[@id='obHomeClipboard']/style/class").get("name"))
        self.assertEqual("priority-1", root.find(".//object[@id='obHomeFont']/style/class").get("name"))

    def test_large_toolbox_spans_all_rows_at_32px(self):
        obj, packing = placed(ET.fromstring(generate()), "bxHomePaste")
        self.assertEqual("5", obj.find("property[@name='icon_size']").text)
        self.assertEqual("both", obj.find("property[@name='toolbar-style']").text)
        self.assertEqual("3", packing.find("property[@name='height']").text)
        button = obj.find("child/object")
        self.assertEqual("GtkMenuToolButton", button.get("class"))
        self.assertEqual("btnHomePaste", button.get("id"))
        self.assertEqual(".uno:Paste", button.find("property[@name='action-name']").text)

    def test_small_toolboxes_stack_in_rows_at_16px(self):
        root = ET.fromstring(generate())
        got = {}
        for box_id in ("bxHomeCut", "bxHomeCopy"):
            obj, packing = placed(root, box_id)
            got[box_id] = (packing.find("property[@name='left-attach']").text,
                           packing.find("property[@name='top-attach']").text,
                           obj.find("property[@name='icon_size']").text,
                           obj.find("property[@name='toolbar-style']").text)
        self.assertEqual({"bxHomeCut": ("1", "0", "1", "both-horiz"),
                          "bxHomeCopy": ("1", "1", "1", "both-horiz")}, got)

    def test_caption_and_separator_positions(self):
        root = ET.fromstring(generate())
        _, packing = placed(root, "lbHomeClipboard")
        self.assertEqual(("0", "3", "2"), tuple(packing.find(f"property[@name='{n}']").text
                                                for n in ("left-attach", "top-attach", "width")))
        grid = root.find(".//object[@id='gdHomeClipboard']")
        sep_child = [c for c in grid.findall("child") if c.find("object").get("class") == "GtkSeparator"][0]
        self.assertEqual(("2", "0", "4"), tuple(sep_child.find(f"packing/property[@name='{n}']").text
                                                for n in ("left-attach", "top-attach", "height")))

    def test_splice_is_idempotent(self):
        once = generate()
        self.assertEqual(once, generate(once))

    def test_optional_label_and_icon(self):
        layout = copy.deepcopy(LAYOUT)
        layout["sections"][0]["columns"][0][0]["items"][0] = {
            "cmd": "InsertMenu", "action": "private:resource/popupmenu/home_insert",
            "label": "Insert", "icon": "cmd/lc_insertcell.png"}
        button = ET.fromstring(generate(layout=layout)).find(".//object[@id='btnHomeInsertMenu']")
        self.assertEqual("private:resource/popupmenu/home_insert", button.find("property[@name='action-name']").text)
        self.assertEqual("Insert", button.find("property[@name='label']").text)
        self.assertEqual("TabbedCalc|btnHomeInsertMenu", button.find("property[@name='label']").get("context"))
        self.assertEqual("cmd/lc_insertcell.png", button.find("property[@name='icon_name']").text)

    def test_rejects_large_toolbox_sharing_a_column(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][0]["columns"][0].append({"id": "X", "style": "small", "items": [{"cmd": "X"}]})
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_rejects_too_many_toolboxes_for_the_rows(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][1]["columns"][0] += [
            {"id": "A", "style": "small", "items": [{"cmd": "A"}]},
            {"id": "B", "style": "small", "items": [{"cmd": "B"}]}]
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_rejects_duplicate_ids(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][1]["columns"][0][0]["items"].append({"cmd": "Bold"})
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_suppr_sync(self):
        ui = generate()
        suppr = "\n".join([
            "other.ui://GtkToolButton[@id='btnHomeOld'] button-no-label",
            "x.ui://GtkToolButton[@id='btnHomeOld'] button-no-label",
            "x.ui://GtkMenuItem[@id='MenuHome-Old'] button-no-label",
            "x.ui://GtkLabel[@id='keepMe'] orphan-label",
        ]) + "\n"
        out = g.sync_suppr(suppr, "x.ui", ui).splitlines()
        self.assertIn("other.ui://GtkToolButton[@id='btnHomeOld'] button-no-label", out)
        self.assertNotIn("x.ui://GtkToolButton[@id='btnHomeOld'] button-no-label", out)
        self.assertNotIn("x.ui://GtkMenuItem[@id='MenuHome-Old'] button-no-label", out)
        self.assertIn("x.ui://GtkLabel[@id='keepMe'] orphan-label", out)
        self.assertIn("x.ui://GtkMenuToolButton[@id='btnHomePaste'] button-no-label", out)
        self.assertIn("x.ui://GtkToolButton[@id='btnHomeBold'] button-no-label", out)
        self.assertEqual(len(out), len(set(out)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -I -m unittest discover -s product/tests -t .`
Expected: an ERROR in `test_gen_ribbon` with `ImportError` or `ModuleNotFoundError` for `product.ui`. The four `test_profile` tests still pass.

- [ ] **Step 3: Write `product/ui/__init__.py` (empty) and `product/ui/gen_ribbon.py`**

```python
#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Generate a notebookbar tab page from a JSON layout and splice it into a .ui file.

Only the children of the tab page box are rewritten. Every other line of the
.ui file stays byte-identical, so the file can still be diffed against the
upstream notebookbar.ui it was copied from.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

# style -> (toolbar-style, icon_size); icon_size 5 = 32 px, 1 = 16 px
# (sfx2/source/sidebar/SidebarToolBox.cxx:318-327)
STYLES = {
    "large": ("both", 5),
    "small": ("icons", 1),
    "small-label": ("both-horiz", 1),
}
BUTTON_CLASS = {"button": "GtkToolButton", "split": "GtkMenuToolButton"}
SUPPRESSED_CLASSES = ("GtkToolButton", "GtkMenuToolButton")
INDENT = "  "
OBJECT_OPEN = re.compile(r"<object\b")


class LayoutError(ValueError):
    pass


def ids_of(layout):
    """Yield every widget id the layout creates, in document order."""
    p = layout["id_prefix"]
    yield "pmhb" + p
    for section in layout["sections"]:
        name = section["name"]
        yield from ("ob" + p + name, "gd" + p + name, "lb" + p + name)
        for column in section["columns"]:
            for box in column:
                yield "bx" + p + box["id"]
                for item in box["items"]:
                    yield "btn" + p + item["cmd"]


def validate(layout):
    seen = set()
    for wid in ids_of(layout):
        if wid in seen:
            raise LayoutError(f"duplicate id {wid}")
        seen.add(wid)
    for section in layout["sections"]:
        name, rows = section["name"], section["rows"]
        for column in section["columns"]:
            styles = [box["style"] for box in column]
            for style in styles:
                if style not in STYLES:
                    raise LayoutError(f"{name}: unknown style {style}")
            if "large" in styles and len(column) != 1:
                raise LayoutError(f"{name}: a large toolbox must be alone in its column")
            if len(column) > rows:
                raise LayoutError(f"{name}: {len(column)} toolboxes in a column of {rows} rows")
            for box in column:
                for item in box["items"]:
                    if item.get("kind", "button") not in BUTTON_CLASS:
                        raise LayoutError(f"{name}: unknown kind {item.get('kind')}")


class Writer:
    def __init__(self):
        self.lines = []
        self.level = 0

    def line(self, text):
        self.lines.append(INDENT * self.level + text)

    def open(self, text):
        self.line(text)
        self.level += 1

    def close(self, text):
        self.level -= 1
        self.line(text)

    def prop(self, name, value, extra=""):
        self.line(f'<property name="{name}"{extra}>{escape(str(value))}</property>')

    def packing(self, **props):
        self.open("<packing>")
        for name, value in props.items():
            self.prop(name.replace("_", "-"), value)
        self.close("</packing>")


def emit_item(w, layout, box_style, item):
    p, ctx = layout["id_prefix"], layout["context"]
    kind = item.get("kind", "button")
    wid = f"btn{p}{item['cmd']}"
    w.open("<child>")
    w.open(f'<object class="{BUTTON_CLASS[kind]}" id="{wid}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    if "label" in item:
        w.prop("label", item["label"], f' translatable="yes" context="{ctx}|{wid}"')
    w.prop("action-name", item.get("action", ".uno:" + item["cmd"]))
    if "icon" in item:
        w.prop("icon_name", item["icon"])
    w.close("</object>")
    homogeneous = "False" if box_style == "large" or kind == "split" else "True"
    w.packing(expand="False", homogeneous=homogeneous)
    w.close("</child>")


def emit_box(w, layout, box, col, row, rows):
    p = layout["id_prefix"]
    toolbar_style, icon_size = STYLES[box["style"]]
    large = box["style"] == "large"
    w.open("<child>")
    w.open(f'<object class="sfxlo-NotebookbarToolBox" id="bx{p}{box["id"]}">')
    w.prop("visible", "True")
    w.prop("can-focus", "True")
    if large:
        w.prop("valign", "center")
        w.prop("vexpand", "True")
    w.prop("toolbar-style", toolbar_style)
    w.prop("show-arrow", "False")
    w.prop("icon_size", icon_size)
    for item in box["items"]:
        emit_item(w, layout, box["style"], item)
    w.close("</object>")
    if large:
        w.packing(left_attach=col, top_attach=0, height=rows)
    else:
        w.packing(left_attach=col, top_attach=row)
    w.close("</child>")


def emit_section(w, layout, section, position, priority):
    p, ctx, name = layout["id_prefix"], layout["context"], section["name"]
    rows, ncols = section["rows"], len(section["columns"])
    w.open("<child>")
    w.open(f'<object class="VclOptionalBox" id="ob{p}{name}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.open("<child>")
    w.line(f"<!-- n-columns={ncols + 1} n-rows={rows + 1} -->")
    w.open(f'<object class="GtkGrid" id="gd{p}{name}">')
    for prop_name, value in (("visible", "True"), ("can-focus", "False"),
                             ("margin-start", 6), ("margin-end", 3), ("margin-top", 6),
                             ("margin-bottom", 6), ("row-spacing", 3), ("column-spacing", 3)):
        w.prop(prop_name, value)
    w.open("<child>")
    w.open(f'<object class="GtkLabel" id="lb{p}{name}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("valign", "end")
    w.prop("vexpand", "True")
    w.prop("label", section["caption"], f' translatable="yes" context="{ctx}|label{p}{name}"')
    w.open("<attributes>")
    w.line('<attribute name="scale" value="0.9"/>')
    w.close("</attributes>")
    w.close("</object>")
    w.packing(left_attach=0, top_attach=rows, width=ncols)
    w.close("</child>")
    for col, column in enumerate(section["columns"]):
        for row, box in enumerate(column):
            emit_box(w, layout, box, col, row, rows)
    w.open("<child>")
    w.open('<object class="GtkSeparator">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("orientation", "vertical")
    w.close("</object>")
    w.packing(left_attach=ncols, top_attach=0, height=rows + 1)
    w.close("</child>")
    w.open("<accessibility>")
    w.line(f'<relation type="labelled-by" target="lb{p}{name}"/>')
    w.close("</accessibility>")
    w.close("</object>")
    w.packing(expand="False", fill="True", position=0)
    w.close("</child>")
    w.open("<style>")
    w.line(f'<class name="priority-{priority}"/>')
    w.close("</style>")
    w.close("</object>")
    w.packing(expand="False", fill="True", position=position)
    w.close("</child>")


def emit_page(layout):
    validate(layout)
    p = layout["id_prefix"]
    sections = layout["sections"]
    w = Writer()
    w.open("<child>")
    w.open(f'<object class="sfxlo-PriorityMergedHBox" id="pmhb{p}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("valign", "center")
    for position, section in enumerate(sections):
        # The leftmost section has the highest priority, so it collapses last.
        emit_section(w, layout, section, position, len(sections) - position)
    w.close("</object>")
    w.packing(expand="True", fill="True", position=0)
    w.close("</child>")
    return w.lines


def find_object(lines, obj_id):
    """Return (first, last) line indexes, inclusive, of the <object> with this id."""
    marker = f'id="{obj_id}"'
    first = next((i for i, text in enumerate(lines) if "<object" in text and marker in text), None)
    if first is None:
        raise LayoutError(f"object {obj_id!r} not found")
    depth = 0
    for i in range(first, len(lines)):
        depth += len(OBJECT_OPEN.findall(lines[i])) - lines[i].count("</object>")
        if depth == 0:
            return first, i
    raise LayoutError(f"object {obj_id!r} is not closed")


def splice(ui_text, layout, generated):
    tab = layout["id_prefix"]
    begin, end = f"<!-- product:{tab}-begin -->", f"<!-- product:{tab}-end -->"
    lines = ui_text.split("\n")
    if any(begin in text for text in lines):
        first = next(i for i, text in enumerate(lines) if begin in text)
        last = next(i for i, text in enumerate(lines) if end in text)
    else:
        start, stop = find_object(lines, layout["page"])
        first = next((i for i in range(start + 1, stop) if lines[i].lstrip().startswith("<child")), None)
        if first is None or lines[stop - 1].strip() != "</child>":
            raise LayoutError(f"{layout['page']} must end with its <child> elements")
        last = stop - 1
    indent = lines[first][: len(lines[first]) - len(lines[first].lstrip())]
    lines[first:last + 1] = [indent + begin] + [indent + text for text in generated] + [indent + end]
    for obj_id in layout.get("remove_objects", []):
        try:
            a, b = find_object(lines, obj_id)
        except LayoutError:
            continue
        del lines[a:b + 1]
    return "\n".join(lines)


def sync_suppr(suppr_text, ui_rel_path, ui_text):
    """Drop suppressions for ids gone from the .ui; add button-no-label for new tool buttons."""
    present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', ui_text))
    prefix = ui_rel_path + ":"
    id_in_line = re.compile(r"@id='([^']+)'")
    out, existing = [], set()
    for line in suppr_text.splitlines():
        if line.startswith(prefix):
            match = id_in_line.search(line)
            if match and match.group(1) not in present:
                continue
            if line in existing:
                continue
            existing.add(line)
        out.append(line)
    for cls, wid in re.findall(r'<object class="(GtkToolButton|GtkMenuToolButton)" id="([^"]+)"', ui_text):
        line = f"{prefix}//{cls}[@id='{wid}'] button-no-label"
        if line not in existing:
            out.append(line)
            existing.add(line)
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--layout", required=True, type=Path)
    ap.add_argument("--ui", required=True, help="repository-relative path of the .ui file")
    ap.add_argument("--suppr", required=True, type=Path)
    args = ap.parse_args(argv)
    layout = json.loads(args.layout.read_text(encoding="utf-8"))
    ui_path = Path(args.ui)
    ui_text = splice(ui_path.read_text(encoding="utf-8"), layout, emit_page(layout))
    ui_path.write_text(ui_text, encoding="utf-8")
    args.suppr.write_text(sync_suppr(args.suppr.read_text(encoding="utf-8"), args.ui, ui_text),
                          encoding="utf-8")
    print(f"{args.ui}: {len(list(ids_of(layout)))} generated ids")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to make sure they pass**

Run: `python3 -I -m unittest discover -s product/tests -t .`
Expected: `Ran 17 tests` ... `OK`.

- [ ] **Step 5: Commit**

```bash
git add product/ui/ product/tests/test_gen_ribbon.py
git commit -m "feat(product): add ribbon page generator with suppression sync"
```

---

### Task 6: The Home tab layout (annex 1)

**Files:**
- Create: `product/ui/calc_home.json`
- Modify (generated): `sc/uiconfig/scalc/ui/notebookbar_office.ui`, `solenv/sanitizers/ui/modules/scalc.suppr`
- Create (routes P2/P3 only): `sc/uiconfig/scalc/popupmenu/home_merge.xml`, `home_insert.xml`, `home_delete.xml`, `home_format.xml`, `home_fill.xml`, `home_clear.xml`, `home_sortfilter.xml`, `home_findselect.xml`
- Modify (routes P2/P3 only): `sc/UIConfig_scalc.mk`, the popupmenu list (`:34` region)
- Modify (route P2 only): `Controller.xcu`, the ToolBar section
- Test: `product/tests/test_calc_home_ui.py`, `sc/qa/uitest/calc_tests/notebookbarOffice.py`

**Interfaces:**
- Consumes:
  - `gen_ribbon.py` (Task 5)
  - the `## 0a` decision (Task 3)
  - `uitest.sh`, `check-ui.sh` (Task 2)
- Produces:
  - `product/ui/calc_home.json`, the single source of the Home layout, read by Task 7's coverage test and the UITest.
  - Home ids as in Task 5: sections `Undo, Clipboard, Font, Alignment, Number, Styles, Cells, Editing`.

- [ ] **Step 1: Write the failing static test**

`product/tests/test_calc_home_ui.py`:

```python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import unittest
from pathlib import Path

from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_home.json"
UPSTREAM = ROOT / "sc/uiconfig/scalc/ui/notebookbar.ui"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
SECTIONS = ["Undo", "Clipboard", "Font", "Alignment", "Number", "Styles", "Cells", "Editing"]


class CalcHomeUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))

    def test_sections_follow_annex_1(self):
        self.assertEqual(SECTIONS, [s["name"] for s in self.layout["sections"]])

    def test_office_ui_is_upstream_plus_home_layout(self):
        # Only the Home page may differ from upstream notebookbar.ui; this also
        # proves the file can be regenerated after re-copying a newer upstream.
        expected = g.splice(UPSTREAM.read_text(encoding="utf-8"), self.layout, g.emit_page(self.layout))
        self.assertEqual(expected, OFFICE.read_text(encoding="utf-8"))

    def test_no_italic_captions_on_home(self):
        text = OFFICE.read_text(encoding="utf-8")
        page = text.split("<!-- product:Home-begin -->")[1].split("<!-- product:Home-end -->")[0]
        self.assertNotIn('name="style" value="italic"', page)


if __name__ == "__main__":
    unittest.main()
```

Run: `python3 -I -m unittest discover -s product/tests -t .`
Expected: an ERROR with `FileNotFoundError: ... product/ui/calc_home.json`.

- [ ] **Step 2: Extend the UITest (failing)**

Add to `sc/qa/uitest/calc_tests/notebookbarOffice.py`:
- the imports `import json`, `import os`, `from pathlib import Path`
- the method below

```python
    def test_home_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_home.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                for section in layout["sections"]:
                    xLabel = xCalcDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xCalcDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")
```

`TDOC` is set to `$(SRCDIR)/sc/qa/uitest/data` by `sc/UITest_calc_tests.mk`, so `parents[3]` is the source root.

Run: `product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.test_home_sections_and_toolboxes`
Expected: FAIL, because `calc_home.json` is missing.

- [ ] **Step 3: Write `product/ui/calc_home.json` (FALLBACK sections; valid for every route)**

```json
{
  "page": "phbHome",
  "id_prefix": "Home",
  "context": "TabbedCalc",
  "remove_objects": ["Menu Home"],
  "sections": [
    {"name": "Undo", "caption": "Undo", "rows": 2, "columns": [
      [{"id": "Undo", "style": "small-label", "items": [{"cmd": "Undo", "kind": "split"}]},
       {"id": "Redo", "style": "small-label", "items": [{"cmd": "Redo", "kind": "split"}]}]
    ]},
    {"name": "Clipboard", "caption": "Clipboard", "rows": 3, "columns": [
      [{"id": "Paste", "style": "large", "items": [{"cmd": "Paste", "kind": "split"}]}],
      [{"id": "Cut", "style": "small-label", "items": [{"cmd": "Cut"}]},
       {"id": "Copy", "style": "small-label", "items": [{"cmd": "Copy"}]},
       {"id": "FormatPaintbrush", "style": "small-label", "items": [{"cmd": "FormatPaintbrush"}]}]
    ]},
    {"name": "Font", "caption": "Font", "rows": 2, "columns": [
      [{"id": "FontRow", "style": "small", "items": [
          {"cmd": "CharFontName"}, {"cmd": "FontHeight"}, {"cmd": "Grow"}, {"cmd": "Shrink"}]},
       {"id": "FormatRow", "style": "small", "items": [
          {"cmd": "Bold"}, {"cmd": "Italic"}, {"cmd": "Underline", "kind": "split"}, {"cmd": "Strikeout"},
          {"cmd": "SetBorderStyle", "kind": "split"}, {"cmd": "BackgroundColor", "kind": "split"},
          {"cmd": "Color", "kind": "split"}]}]
    ]},
    {"name": "Alignment", "caption": "Alignment", "rows": 3, "columns": [
      [{"id": "VAlign", "style": "small", "items": [
          {"cmd": "AlignTop"}, {"cmd": "AlignVCenter"}, {"cmd": "AlignBottom"}]},
       {"id": "HAlign", "style": "small", "items": [
          {"cmd": "AlignLeft"}, {"cmd": "AlignHorizontalCenter"}, {"cmd": "AlignRight"}]},
       {"id": "Indent", "style": "small", "items": [
          {"cmd": "DecrementIndent"}, {"cmd": "IncrementIndent"}]}],
      [{"id": "WrapText", "style": "small-label", "items": [{"cmd": "WrapText"}]},
       {"id": "Merge", "style": "small-label", "items": [{"cmd": "ToggleMergeCells"}]}]
    ]},
    {"name": "Number", "caption": "Number", "rows": 2, "columns": [
      [{"id": "NumberFormatType", "style": "small", "items": [{"cmd": "NumberFormatType"}]},
       {"id": "NumberFormat", "style": "small", "items": [
          {"cmd": "NumberFormatCurrency", "kind": "split"}, {"cmd": "NumberFormatPercent"},
          {"cmd": "NumberFormatDecimal"}, {"cmd": "NumberFormatIncDecimals"},
          {"cmd": "NumberFormatDecDecimals"}]}]
    ]},
    {"name": "Styles", "caption": "Styles", "rows": 2, "columns": [
      [{"id": "ConditionalFormatMenu", "style": "large", "items": [
          {"cmd": "ConditionalFormatMenu", "kind": "split"}]}],
      [{"id": "AutoFormat", "style": "large", "items": [{"cmd": "AutoFormat"}]}],
      [{"id": "StyleApply", "style": "small", "items": [{"cmd": "StyleApply"}]}]
    ]},
    {"name": "Cells", "caption": "Cells", "rows": 2, "columns": [
      [{"id": "RowOperations", "style": "large", "items": [{"cmd": "RowOperations", "kind": "split"}]}],
      [{"id": "ColumnOperations", "style": "large", "items": [{"cmd": "ColumnOperations", "kind": "split"}]}],
      [{"id": "FormatCellDialog", "style": "large", "items": [{"cmd": "FormatCellDialog"}]}]
    ]},
    {"name": "Editing", "caption": "Editing", "rows": 3, "columns": [
      [{"id": "AutoSum", "style": "small-label", "items": [{"cmd": "AutoSum"}]},
       {"id": "SortAscending", "style": "small-label", "items": [{"cmd": "SortAscending"}]},
       {"id": "DataFilterAutoFilter", "style": "small-label", "items": [{"cmd": "DataFilterAutoFilter"}]}],
      [{"id": "SearchDialog", "style": "large", "items": [{"cmd": "SearchDialog"}]}]
    ]}
  ]
}
```

- [ ] **Step 4: Apply the route from `## 0a`**

**If `FALLBACK`:** no change. Stage B owns the menus, and Step 3's file is final.

**If `P3` or `P2`:** create the eight popup menus. Each file starts with the 8-line MPL comment header copied from `sc/uiconfig/scalc/popupmenu/row_operations.xml:1-9`, followed by the body below.

| File | Body |
|------|------|
| `home_merge.xml` | `.uno:ToggleMergeCells`, `.uno:MergeCells`, `.uno:SplitCell` |
| `home_insert.xml` | `.uno:InsertCell`, `.uno:InsertRowsBefore`, `.uno:InsertColumnsBefore` |
| `home_delete.xml` | `.uno:DeleteCell`, `.uno:DeleteRows`, `.uno:DeleteColumns` |
| `home_format.xml` | `.uno:FormatCellDialog`, separator, `.uno:RowHeight`, `.uno:ColumnWidth`, `.uno:SetOptimalColumnWidth`, separator, `.uno:HideRow`, `.uno:HideColumn` |
| `home_fill.xml` | `.uno:FillDown`, `.uno:FillRight`, separator, `.uno:FillSeries` |
| `home_clear.xml` | `.uno:Delete`, `.uno:ClearContents`, `.uno:ResetAttributes` |
| `home_sortfilter.xml` | `.uno:SortAscending`, `.uno:SortDescending`, `.uno:DataSort`, separator, `.uno:DataFilterAutoFilter`, `.uno:DataFilterStandardFilter` |
| `home_findselect.xml` | `.uno:SearchDialog`, `.uno:SelectAll` |

Example body (`home_insert.xml`):

```xml
<menu:menupopup xmlns:menu="http://openoffice.org/2001/menu">
  <menu:menuitem menu:id=".uno:InsertCell"/>
  <menu:menuitem menu:id=".uno:InsertRowsBefore"/>
  <menu:menuitem menu:id=".uno:InsertColumnsBefore"/>
</menu:menupopup>
```

A separator is `<menu:menuseparator/>`.

List all eight in `sc/UIConfig_scalc.mk`, next to `sc/uiconfig/scalc/popupmenu/notebookbar \` (`:34`). They go in the same list, without the `.xml` suffix, e.g. `	sc/uiconfig/scalc/popupmenu/home_insert \`.

Then replace these entries in `calc_home.json`.

**Route P3:** the buttons point at the menu resources.

- Alignment, toolbox `Merge`, items:
  ```json
  [{"cmd": "MergeMenu", "action": "private:resource/popupmenu/home_merge", "label": "Merge & Center", "icon": "cmd/sc_togglemergecells.png"}]
  ```
- Cells, columns:
  ```json
  [[{"id": "InsertMenu", "style": "large", "items": [{"cmd": "InsertMenu", "action": "private:resource/popupmenu/home_insert", "label": "Insert", "icon": "cmd/lc_insertcell.png"}]}],
   [{"id": "DeleteMenu", "style": "large", "items": [{"cmd": "DeleteMenu", "action": "private:resource/popupmenu/home_delete", "label": "Delete", "icon": "cmd/lc_deletecell.png"}]}],
   [{"id": "FormatMenu", "style": "large", "items": [{"cmd": "FormatMenu", "action": "private:resource/popupmenu/home_format", "label": "Format", "icon": "cmd/lc_formatcelldialog.png"}]}]]
  ```
- Editing (keep `"rows": 3`), columns:
  ```json
  [[{"id": "AutoSum", "style": "small-label", "items": [{"cmd": "AutoSum"}]},
    {"id": "FillMenu", "style": "small-label", "items": [{"cmd": "FillMenu", "action": "private:resource/popupmenu/home_fill", "label": "Fill", "icon": "cmd/sc_filldown.png"}]},
    {"id": "ClearMenu", "style": "small-label", "items": [{"cmd": "ClearMenu", "action": "private:resource/popupmenu/home_clear", "label": "Clear", "icon": "cmd/sc_delete.png"}]}],
   [{"id": "SortFilterMenu", "style": "large", "items": [{"cmd": "SortFilterMenu", "action": "private:resource/popupmenu/home_sortfilter", "label": "Sort & Filter", "icon": "cmd/lc_sortfiltermenu.png"}]}],
   [{"id": "FindSelectMenu", "style": "large", "items": [{"cmd": "FindSelectMenu", "action": "private:resource/popupmenu/home_findselect", "label": "Find & Select", "icon": "cmd/lc_searchdialog.png"}]}]]
  ```

**Route P2:** split buttons on existing commands.

- Alignment `Merge` item: `{"cmd": "ToggleMergeCells", "kind": "split"}`.
- Cells: three large toolboxes `InsertCell`, `DeleteCell` and `FormatCellDialog`, each with one `split` item of the same command.
- Editing:
  - `AutoSum` large
  - a column with small-label `FillDown` (split) and `Delete` (split)
  - `DataSort` large split
  - `SearchDialog` large split

Add one ToolBar-section node per row of this table to `Controller.xcu`, next to `RowOperationsControl` (`:2068`):

| Node name | Command | Menu |
|-----------|---------|------|
| `HomeMergeControl` | `.uno:ToggleMergeCells` | `home_merge` |
| `HomeInsertControl` | `.uno:InsertCell` | `home_insert` |
| `HomeDeleteControl` | `.uno:DeleteCell` | `home_delete` |
| `HomeFormatControl` | `.uno:FormatCellDialog` | `home_format` |
| `HomeFillControl` | `.uno:FillDown` | `home_fill` |
| `HomeClearControl` | `.uno:Delete` | `home_clear` |
| `HomeSortFilterControl` | `.uno:DataSort` | `home_sortfilter` |
| `HomeFindSelectControl` | `.uno:SearchDialog` | `home_findselect` |

Each node has this shape, shown for the second row:

```xml
    <node oor:name="HomeInsertControl" oor:op="replace">
      <prop oor:name="Command">
        <value>.uno:InsertCell</value>
      </prop>
      <prop oor:name="Module">
        <value>com.sun.star.sheet.SpreadsheetDocument</value>
      </prop>
      <prop oor:name="Controller">
        <value>com.sun.star.comp.framework.GenericPopupToolbarController</value>
      </prop>
      <prop oor:name="Value">
        <value>private:resource/popupmenu/home_insert</value>
      </prop>
    </node>
```

- [ ] **Step 5: Generate, check and build**

```bash
python3 -I product/ui/gen_ribbon.py --layout product/ui/calc_home.json \
  --ui sc/uiconfig/scalc/ui/notebookbar_office.ui --suppr solenv/sanitizers/ui/modules/scalc.suppr
product/dev/check-ui.sh sc/uiconfig/scalc/ui/notebookbar_office.ui
python3 -I -m unittest discover -s product/tests -t .
product/dev/lo-make.sh build gb_SUPPRESS_TESTS=1
```

Expected:
- The generator prints `sc/uiconfig/scalc/ui/notebookbar_office.ui: <N> generated ids`.
- `check-ui.sh` reports no fatal lines and exits 0. If gla11y reports a fatal for a generated widget type other than `button-no-label`, fix the generator so it emits what gla11y expects, add a unit test for it, and regenerate. Do not hand-edit the generated region.
- Unit tests `OK`, with 20 tests.
- The build exits 0.

- [ ] **Step 6: Run the UITests to make sure they pass**

```bash
product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.test_office_variant_loads \
  notebookbarOffice.NotebookbarOffice.test_switch_back_to_compact \
  notebookbarOffice.NotebookbarOffice.test_home_sections_and_toolboxes
```

Expected: all three PASS.

If `"Text"` is not in a label's state dict, print `get_state_as_dict(xLabel)` once and use the key that holds the caption (`WindowUIObject::get_state` sets `Text` at `vcl/source/uitest/uiobject.cxx:331`).

- [ ] **Step 7: Screenshot the layout**

```bash
python3 -I product/dev/profile.py --ui office --appearance dark
product/dev/shot.sh /mnt/games/libreoffice/assets/previews/step2-layout-dark.png
```

Expected:
- The Home tab shows 8 captioned sections in annex 1 order, with plain (not italic) captions and large buttons visibly bigger than in `baseline-tabbed-dark.png`.
- Look at it with the Read tool and note anything clipped in the commit message body.

- [ ] **Step 8: Commit**

```bash
git add product/ui/calc_home.json product/tests/test_calc_home_ui.py \
  sc/uiconfig/scalc/ui/notebookbar_office.ui solenv/sanitizers/ui/modules/scalc.suppr \
  sc/qa/uitest/calc_tests/notebookbarOffice.py
# plus, for routes P2/P3: sc/uiconfig/scalc/popupmenu/home_*.xml sc/UIConfig_scalc.mk
# plus, for route P2: officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu
git commit -m "feat(sc): lay out the Tabbed Office Home tab in Excel's eight sections"
```

---

### Task 7: Icon theme builder and the DIRECT icons

**Files:**
- Create: `product/icons/__init__.py` (empty)
- Create: `product/icons/build_theme.py`
- Create: `product/icons/manifest.json`
- Create: `product/icons/fluent/` (vendored SVGs plus `LICENSE`, filled by the `vendor` command)
- Create: `product/icons/custom/thousands.svg`
- Create: `product/icons/overrides/.gitkeep`
- Test: `product/tests/test_icons.py`

**Interfaces:**
- Consumes:
  - `product/ui/calc_home.json` and the generated `notebookbar_office.ui` (Task 6)
  - the Fluent package at `/mnt/games/libreoffice/assets/fluent/package/icons`
- Produces:
  - `product/icons/build_theme.py`:
    - `vendor --from DIR --license FILE`
    - `build [--out DIR]`, default `product/icons/out`
    - `install --instdir DIR`
    - `sheet --out PNG`
  - Python API:
    - `load_manifest() -> dict`
    - `build(manifest, out: Path) -> dict` with keys `"zips"` (`{"boost": Path, "boost_dark": Path}`) and `"scaled_16"` (a list of `"<icon>:<glyph>"` whose 16 px icon had to be scaled from a 24 px source, which blurs; trimmed 20 px and native 16 px sources are crisp)
    - `compose(entry, colors, size, sources) -> str` (SVG text)
  - Manifest entry:
    - `name`: base file name; the PNGs are `cmd/sc_<name>.png`, `cmd/lc_<name>.png` and `cmd/32/<name>.png`
    - `aliases`: extra command names that get `links.txt` lines
    - `large`: bool, adds the 32 px file
    - `stripe`: `true`, or `{"scale": float, "keep": float}`. It keeps the bottom quarter empty. The defaults are scale 0.8 and keep 0.75; keep is capped at 0.75.
    - `fill`: `{"color": "<palette fill_* key>"}`. It draws the base glyph's Fluent `filled` silhouette in that soft color under the outline, like Office's filled icons. The user chose this over sealing every shape: a touch of white stays.
    - `layers`: list of layer objects. A layer has either `glyph` (with optional `style` regular|filled, default regular; `custom: true` to read `product/icons/custom/<glyph>.svg`) or `rect: [x, y, w, h]` (fractions), plus optional `color` (palette key, default `line`), `scale`, `dx`, `dy`, `opacity` and `knockout`.

- [ ] **Step 1: Write the failing tests**

`product/tests/test_icons.py`:

```python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

from product.icons import build_theme as bt

ROOT = Path(__file__).resolve().parents[2]
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
# Rendered by toolbar controllers as list boxes; they show no icon.
LIST_BOX_COMMANDS = {"charfontname", "fontheight", "numberformattype", "styleapply"}
EXPECTED_SIZE = {"cmd/sc_": 16, "cmd/lc_": 24, "cmd/32/": 32}


def home_page():
    text = OFFICE.read_text(encoding="utf-8")
    body = text.split("<!-- product:Home-begin -->")[1].split("<!-- product:Home-end -->")[0]
    return ET.fromstring("<root>" + body + "</root>")


class IconThemeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.result = bt.build(bt.load_manifest(), Path(cls.tmp.name))
        cls.zips = cls.result["zips"]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def members(self, theme):
        with zipfile.ZipFile(self.zips[theme]) as z:
            names = set(z.namelist())
            links = {}
            if "links.txt" in names:
                for line in z.read("links.txt").decode().splitlines():
                    if line.strip():
                        alias, target = line.split()
                        links[alias] = target
        return names, links

    def has(self, theme, member):
        names, links = self.members(theme)
        return member in names or links.get(member) in names

    def image(self, theme, member):
        with zipfile.ZipFile(self.zips[theme]) as z, z.open(member) as f:
            return Image.open(f).convert("RGBA").copy()

    def test_every_home_button_has_an_icon(self):
        missing = []
        for box in home_page().iter("object"):
            if box.get("class") != "sfxlo-NotebookbarToolBox":
                continue
            large = box.find("property[@name='icon_size']").text == "5"
            for button in box.findall("child/object"):
                icon = button.find("property[@name='icon_name']")
                if icon is not None:
                    wanted = [icon.text]
                else:
                    cmd = button.find("property[@name='action-name']").text.removeprefix(".uno:").lower()
                    if cmd in LIST_BOX_COMMANDS:
                        continue
                    wanted = [f"cmd/sc_{cmd}.png", f"cmd/lc_{cmd}.png"] + ([f"cmd/32/{cmd}.png"] if large else [])
                for theme in self.zips:
                    missing += [f"{theme}:{m}" for m in wanted if not self.has(theme, m)]
        self.assertEqual([], missing)

    def test_png_sizes(self):
        for theme in self.zips:
            names, _ = self.members(theme)
            for member in names:
                for prefix, size in EXPECTED_SIZE.items():
                    if member.startswith(prefix) and member.endswith(".png"):
                        self.assertEqual((size, size), self.image(theme, member).size, f"{theme}:{member}")

    def test_color_buttons_keep_the_stripe_band_empty(self):
        # svx/source/tbxctrls/tbxcolorupdate.cxx:266-274 paints rows H - H/4 .. H-1.
        for theme in self.zips:
            for name in ("color", "backgroundcolor"):
                for member, size in ((f"cmd/sc_{name}.png", 16), (f"cmd/lc_{name}.png", 24)):
                    band = self.image(theme, member).crop((0, size - size // 4, size, size))
                    self.assertEqual(0, band.getextrema()[3][1], f"{theme}:{member}")

    def test_dark_theme_has_no_light_theme_line_color(self):
        names, _ = self.members("boost_dark")
        for member in sorted(n for n in names if n.endswith(".png")):
            for r, g, b, a in self.image("boost_dark", member).get_flattened_data():
                if a > 128 and max(abs(r - 0x42), abs(g - 0x42), abs(b - 0x42)) < 24:
                    self.fail(f"boost_dark:{member} has light-theme line pixels")

    def test_license_and_links(self):
        for theme in self.zips:
            names, links = self.members(theme)
            self.assertIn("LICENSE.fluent.txt", names)
            with zipfile.ZipFile(self.zips[theme]) as z:
                self.assertTrue(z.read("LICENSE.fluent.txt").decode().startswith("MIT License"))
            for alias, target in links.items():
                self.assertIn(target, names, f"{theme}: {alias} -> {target}")

    def test_filled_icons_use_their_fill_color(self):
        # Office-like fills: the paper of "paste" carries the yellow fill.
        for theme, fill in (("boost", "F5C96A"), ("boost_dark", "B08A3A")):
            target = tuple(int(fill[i:i + 2], 16) for i in (0, 2, 4))
            pixels = self.image(theme, "cmd/lc_paste.png").get_flattened_data()
            close = [p for p in pixels if p[3] > 200 and max(abs(p[i] - target[i]) for i in range(3)) < 20]
            self.assertGreater(len(close), 40, f"{theme}: paste fill missing")

    def test_16px_icons_use_crisp_sources(self):
        # 16 px slots use the 20 px design trimmed 1:1, or native 16; never a blurry 24 -> 16.
        self.assertEqual([], self.result["scaled_16"])

    def test_vendored_glyphs_exist(self):
        for entry in bt.load_manifest()["icons"]:
            for layer in entry["layers"]:
                if "glyph" in layer and not layer.get("custom"):
                    path = bt.FLUENT / f"{layer['glyph']}_24_{layer.get('style', 'regular')}.svg"
                    self.assertTrue(path.exists(), path)


if __name__ == "__main__":
    unittest.main()
```

Run: `python3 -I -m unittest discover -s product/tests -t .`
Expected: an ERROR, because `product.icons` cannot be imported.

- [ ] **Step 2: Write `product/icons/build_theme.py`**

```python
#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Build the partial "boost" icon themes from vendored Fluent SVGs and a manifest."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
FLUENT = HERE / "fluent"
CUSTOM = HERE / "custom"
OVERRIDES = HERE / "overrides"
MANIFEST = HERE / "manifest.json"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

# target size -> source sizes to try, best first
# For 16 px slots the 20 px design is preferred and its 2 px padding is trimmed,
# so it renders 1:1 (pixel-crisp) and fills the slot like Excel's small icons;
# native Fluent 16 px glyphs only fill 14 px and looked undersized next to B/I/U.
SOURCE_SIZES = {16: [20, 16, 24], 24: [24, 20, 28], 32: [32, 28, 24]}
FILE_PREFIX = {16: "cmd/sc_", 24: "cmd/lc_", 32: "cmd/32/"}
THEMES = {"boost": "light", "boost_dark": "dark"}


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def inner_markup(path):
    root = ET.parse(path).getroot()
    return "".join(ET.tostring(child, encoding="unicode") for child in root)


class Sources:
    """Find glyph SVGs; remember which 16 px icons had to be scaled from 20 px."""

    def __init__(self):
        self.scaled_16 = []

    def load(self, icon, layer, size, stripe=False):
        """Return (markup, source size, padding to trim) for one glyph layer."""
        glyph, style = layer["glyph"], layer.get("style", "regular")
        if layer.get("custom"):
            # Custom glyphs are drawn on the 24 px grid with 2 px padding.
            return inner_markup(CUSTOM / f"{glyph}.svg"), 24, (2 if size == 16 else 0)
        order = SOURCE_SIZES[size]
        if size == 16 and stripe:
            order = [16, 20, 24]  # color buttons keep native 16 so the stripe band stays free
        for src in order:
            for base in (OVERRIDES, FLUENT):
                path = base / f"{glyph}_{src}_{style}.svg"
                if path.exists():
                    if size == 16 and src not in (16, 20):
                        self.scaled_16.append(f"{icon}:{glyph}")
                    pad = 2 if (size == 16 and src == 20 and not stripe) else 0
                    return inner_markup(path), src, pad
        raise FileNotFoundError(f"{glyph} ({style}) has no source for {size} px")


def compose(entry, colors, size, sources):
    s = size
    defs, body = [], []
    fill = entry.get("fill")
    if fill:
        # Soft color under the outline, like Office's filled icons: the base
        # glyph's Fluent "filled" silhouette in the fill color. Shapes that the
        # filled variant leaves open stay unfilled, which keeps a touch of white.
        base = next(layer for layer in entry["layers"] if "glyph" in layer)
        silhouette = dict(base, style="filled")
        inner, src, pad = sources.load(entry["name"], silhouette, s, bool(entry.get("stripe")))
        k = s / (src - 2 * pad) * base.get("scale", 1)
        dx, dy = base.get("dx", 0) * s - pad * k, base.get("dy", 0) * s - pad * k
        body.append(f'<g transform="translate({dx:g} {dy:g}) scale({k:g})" '
                    f'fill="{colors[fill["color"]]}">{inner}</g>')
    for index, layer in enumerate(entry["layers"]):
        color = colors[layer.get("color", "line")]
        scale = layer.get("scale", 1)
        dx, dy = layer.get("dx", 0) * s, layer.get("dy", 0) * s
        if "rect" in layer:
            x, y, w, h = (v * s for v in layer["rect"])
            markup = (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{color}" '
                      f'fill-opacity="{layer.get("opacity", 1)}"/>')
        else:
            inner, src, pad = sources.load(entry["name"], layer, s, bool(entry.get("stripe")))
            k = s / (src - 2 * pad) * scale
            markup = (f'<g transform="translate({dx - pad * k:g} {dy - pad * k:g}) scale({k:g})" '
                      f'fill="{color}" color="{color}">{inner}</g>')
        if layer.get("knockout"):
            # Cut a gap behind the badge so it stays legible over the base glyph.
            cx, cy, r = dx + scale * s / 2, dy + scale * s / 2, scale * s / 2
            defs.append(f'<mask id="k{index}"><rect width="{s}" height="{s}" fill="#fff"/>'
                        f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="#000"/></mask>')
            body = [f'<g mask="url(#k{index})">{"".join(body)}</g>']
        body.append(markup)
    content = "".join(body)
    stripe = entry.get("stripe")
    if stripe:
        # LibreOffice paints the chosen color over the bottom quarter
        # (svx/source/tbxctrls/tbxcolorupdate.cxx:266-274): keep it empty.
        # "scale" shrinks the art toward the top; "keep" cuts it below that fraction
        # (text_color uses keep 0.6 to drop Fluent's own color bar).
        opts = {"scale": 0.8, "keep": 0.75}
        if isinstance(stripe, dict):
            opts.update(stripe)
        height = min(round(s * opts["keep"]), s - s // 4)
        k = opts["scale"]
        defs.append(f'<clipPath id="top"><rect width="{s}" height="{height}"/></clipPath>')
        content = (f'<g clip-path="url(#top)"><g transform="translate({s * (1 - k) / 2:g} 0) scale({k:g})">'
                   f'{content}</g></g>')
    return (f'<svg xmlns="{SVG_NS}" width="{s}" height="{s}" viewBox="0 0 {s} {s}">'
            f'<defs>{"".join(defs)}</defs>{content}</svg>')


def render_png(svg_text, size, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False, encoding="utf-8") as f:
        f.write(svg_text)
        tmp = Path(f.name)
    try:
        subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-f", "png",
                        "-o", str(out), str(tmp)], check=True)
    finally:
        tmp.unlink()


def build(manifest, out):
    out = Path(out)
    sources = Sources()
    zips = {}
    for theme, mode in THEMES.items():
        colors = manifest["palette"][mode]
        root = out / theme
        if root.exists():
            shutil.rmtree(root)
        links = []
        for entry in manifest["icons"]:
            sizes = [16, 24] + ([32] if entry.get("large") else [])
            for size in sizes:
                target = f"{FILE_PREFIX[size]}{entry['name']}.png"
                render_png(compose(entry, colors, size, sources), size, root / target)
                for alias in entry.get("aliases", []):
                    links.append(f"{FILE_PREFIX[size]}{alias}.png {target}")
        (root / "links.txt").write_text("\n".join(links) + "\n", encoding="utf-8")
        shutil.copyfile(FLUENT / "LICENSE", root / "LICENSE.fluent.txt")
        zip_path = out / f"images_{theme}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    z.write(path, path.relative_to(root).as_posix())
        zips[theme] = zip_path
    return {"zips": zips, "scaled_16": sorted(set(sources.scaled_16))}


def vendor(manifest, src_dir, license_file):
    FLUENT.mkdir(parents=True, exist_ok=True)
    count = 0
    for entry in manifest["icons"]:
        for layer in entry["layers"]:
            if "glyph" not in layer or layer.get("custom"):
                continue
            styles = {layer.get("style", "regular")}
            if entry.get("fill"):
                styles.add("filled")  # silhouette drawn under the outline
            for style in sorted(styles):
                for size in (16, 20, 24, 28, 32):
                    path = Path(src_dir) / f"{layer['glyph']}_{size}_{style}.svg"
                    if path.exists():
                        shutil.copyfile(path, FLUENT / path.name)
                        count += 1
    shutil.copyfile(license_file, FLUENT / "LICENSE")
    return count


def sheet(zips, out):
    """Contact sheet: every icon at 16/24/32 in light and dark, upscaled 2x."""
    rows = []
    for theme, zip_path in zips.items():
        with zipfile.ZipFile(zip_path) as z:
            names = sorted(n for n in z.namelist() if n.startswith("cmd/lc_"))
            for lc in names:
                name = lc.removeprefix("cmd/lc_").removesuffix(".png")
                cells = []
                for member in (f"cmd/sc_{name}.png", lc, f"cmd/32/{name}.png"):
                    if member in z.namelist():
                        with z.open(member) as f:
                            img = Image.open(f).convert("RGBA")
                            cells.append(img.resize((img.width * 2, img.height * 2), Image.NEAREST))
                rows.append((theme, name, cells))
    width, row_h = 520, 72
    canvas = Image.new("RGBA", (width * 2, row_h * ((len(rows) + 1) // 2)), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (theme, name, cells) in enumerate(rows):
        x0, y0 = (i % 2) * width, (i // 2) * row_h
        bg = "#E4F2E8" if theme == "boost" else "#2B2B2B"
        draw.rectangle([x0, y0, x0 + width - 4, y0 + row_h - 4], fill=bg)
        draw.text((x0 + 6, y0 + 6), f"{theme}: {name}", fill="#888888")
        x = x0 + 220
        for cell in cells:
            canvas.alpha_composite(cell, (x, y0 + 4))
            x += cell.width + 12
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("vendor")
    v.add_argument("--from", dest="src", required=True, type=Path)
    v.add_argument("--license", required=True, type=Path)
    b = sub.add_parser("build")
    b.add_argument("--out", type=Path, default=HERE / "out")
    i = sub.add_parser("install")
    i.add_argument("--instdir", type=Path, required=True)
    i.add_argument("--out", type=Path, default=HERE / "out")
    s = sub.add_parser("sheet")
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--build", type=Path, default=HERE / "out")
    args = ap.parse_args(argv)
    manifest = load_manifest()
    if args.cmd == "vendor":
        print(f"vendored {vendor(manifest, args.src, args.license)} files into {FLUENT}")
    elif args.cmd == "build":
        result = build(manifest, args.out)
        print("\n".join(str(p) for p in result["zips"].values()))
        if result["scaled_16"]:
            print("16 px rendered from a 24 px source (blurry):", ", ".join(result["scaled_16"]))
    elif args.cmd == "install":
        for theme in THEMES:
            dest = args.instdir / "share" / "config" / f"images_{theme}.zip"
            shutil.copyfile(args.out / f"images_{theme}.zip", dest)
            print(dest)
    elif args.cmd == "sheet":
        zips = {t: args.build / f"images_{t}.zip" for t in THEMES}
        print(sheet(zips, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Write `product/icons/manifest.json` and `custom/thousands.svg`**

The manifest holds every icon. In this task the DIRECT icons use their final glyphs. The COMPOSE icons that Task 8 finishes start as the single base glyph shown here, so the coverage test can already pass. Task 8 adds their badges, rects and overrides.

```json
{
  "fluent_version": "1.1.344",
  "palette": {
    "light": {"line": "#424242", "green": "#107C10", "red": "#C50F1F", "blue": "#0F6CBD", "amber": "#AD6800",
              "fill_yellow": "#F5C96A", "fill_blue": "#9CC8F2", "fill_cells": "#BFDDF7",
              "fill_red": "#F1A5A8", "fill_green": "#9FD89F"},
    "dark":  {"line": "#D6D6D6", "green": "#54B054", "red": "#E9737B", "blue": "#479EF5", "amber": "#F2B230",
              "fill_yellow": "#B08A3A", "fill_blue": "#3E78B8", "fill_cells": "#2F587C",
              "fill_red": "#B85A60", "fill_green": "#4E8E4E"}
  },
  "icons": [
    {"name": "undo", "layers": [{"glyph": "arrow_undo"}]},
    {"name": "redo", "layers": [{"glyph": "arrow_redo"}]},
    {"name": "paste", "fill": {"color": "fill_yellow"}, "large": true, "layers": [{"glyph": "clipboard_paste"}]},
    {"name": "cut", "layers": [{"glyph": "cut"}]},
    {"name": "copy", "fill": {"color": "fill_blue"}, "layers": [{"glyph": "copy"}]},
    {"name": "formatpaintbrush", "fill": {"color": "fill_yellow"}, "layers": [{"glyph": "paint_brush"}]},
    {"name": "grow", "layers": [{"glyph": "font_increase"}]},
    {"name": "shrink", "layers": [{"glyph": "font_decrease"}]},
    {"name": "bold", "layers": [{"glyph": "text_bold"}]},
    {"name": "italic", "layers": [{"glyph": "text_italic"}]},
    {"name": "underline", "layers": [{"glyph": "text_underline"}]},
    {"name": "strikeout", "layers": [{"glyph": "text_strikethrough"}]},
    {"name": "setborderstyle", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "border_all"}]},
    {"name": "backgroundcolor", "fill": {"color": "fill_yellow"}, "stripe": true, "layers": [{"glyph": "paint_bucket"}]},
    {"name": "color", "stripe": {"scale": 1.0, "keep": 0.6}, "layers": [{"glyph": "text_color"}]},
    {"name": "aligntop", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "textbox_align_top"}]},
    {"name": "alignvcenter", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "textbox_align_middle"}]},
    {"name": "alignbottom", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "textbox_align_bottom"}]},
    {"name": "alignleft", "layers": [{"glyph": "text_align_left"}]},
    {"name": "alignhorizontalcenter", "layers": [{"glyph": "text_align_center"}]},
    {"name": "alignright", "layers": [{"glyph": "text_align_right"}]},
    {"name": "decrementindent", "layers": [{"glyph": "text_indent_decrease"}]},
    {"name": "incrementindent", "layers": [{"glyph": "text_indent_increase"}]},
    {"name": "wraptext", "layers": [{"glyph": "text_wrap"}]},
    {"name": "togglemergecells", "fill": {"color": "fill_cells"}, "aliases": ["mergecells"], "layers": [{"glyph": "table_cells_merge"}]},
    {"name": "splitcell", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table_cells_split"}]},
    {"name": "numberformatcurrency", "fill": {"color": "fill_green"}, "layers": [{"glyph": "money"}]},
    {"name": "numberformatpercent", "layers": [{"glyph": "text_percent"}]},
    {"name": "numberformatdecimal", "layers": [{"glyph": "thousands", "custom": true}]},
    {"name": "numberformatincdecimals", "layers": [{"glyph": "decimal_arrow_right"}]},
    {"name": "numberformatdecdecimals", "layers": [{"glyph": "decimal_arrow_left"}]},
    {"name": "conditionalformatmenu", "fill": {"color": "fill_cells"}, "large": true, "layers": [{"glyph": "table"}]},
    {"name": "styleapply", "fill": {"color": "fill_cells"}, "large": true, "layers": [{"glyph": "table"}]},
    {"name": "autoformat", "fill": {"color": "fill_cells"}, "large": true, "layers": [
      {"glyph": "table"}, {"rect": [0.125, 0.125, 0.75, 0.25], "color": "amber", "opacity": 0.6}]},
    {"name": "insertcell", "fill": {"color": "fill_cells"}, "large": true, "layers": [{"glyph": "table"}]},
    {"name": "insertrowsbefore", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table"}]},
    {"name": "insertcolumnsbefore", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table"}]},
    {"name": "deletecell", "fill": {"color": "fill_cells"}, "large": true, "layers": [{"glyph": "table"}]},
    {"name": "deleterows", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table"}]},
    {"name": "deletecolumns", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table"}]},
    {"name": "rowoperations", "fill": {"color": "fill_cells"}, "large": true, "layers": [{"glyph": "table"}]},
    {"name": "columnoperations", "fill": {"color": "fill_cells"}, "large": true, "layers": [{"glyph": "table"}]},
    {"name": "formatcelldialog", "fill": {"color": "fill_cells"}, "large": true, "layers": [{"glyph": "table_settings"}]},
    {"name": "rowheight", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table_resize_row"}]},
    {"name": "columnwidth", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table_resize_column"}]},
    {"name": "setoptimalcolumnwidth", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table_resize_column"}]},
    {"name": "hiderow", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table_resize_row"}]},
    {"name": "hidecolumn", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table_resize_column"}]},
    {"name": "autosum", "large": true, "layers": [{"glyph": "autosum"}]},
    {"name": "filldown", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table"}]},
    {"name": "fillright", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "table"}]},
    {"name": "fillseries", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "number_row"}]},
    {"name": "delete", "fill": {"color": "fill_red"}, "layers": [{"glyph": "eraser"}]},
    {"name": "clearcontents", "fill": {"color": "fill_red"}, "layers": [{"glyph": "backspace"}]},
    {"name": "resetattributes", "layers": [{"glyph": "text_clear_formatting"}]},
    {"name": "sortascending", "layers": [{"glyph": "text_sort_ascending"}]},
    {"name": "sortdescending", "layers": [{"glyph": "text_sort_descending"}]},
    {"name": "datasort", "large": true, "layers": [{"glyph": "arrow_sort"}]},
    {"name": "sortfiltermenu", "large": true, "layers": [{"glyph": "text_sort_ascending"}]},
    {"name": "datafilterautofilter", "fill": {"color": "fill_blue"}, "layers": [{"glyph": "filter"}]},
    {"name": "datafilterstandardfilter", "fill": {"color": "fill_blue"}, "layers": [{"glyph": "filter"}]},
    {"name": "searchdialog", "fill": {"color": "fill_blue"}, "large": true, "layers": [{"glyph": "search"}]},
    {"name": "selectall", "fill": {"color": "fill_cells"}, "layers": [{"glyph": "select_all_on"}]}
  ]
}
```

`product/icons/custom/thousands.svg`. It is drawn on the 24 px grid and colored by `currentColor`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
  <g fill="none" stroke="currentColor" stroke-width="1.5">
    <ellipse cx="7" cy="11" rx="2.25" ry="4"/>
    <ellipse cx="12.75" cy="11" rx="2.25" ry="4"/>
    <ellipse cx="18.5" cy="11" rx="2.25" ry="4"/>
  </g>
  <path fill="currentColor" d="M3.1 15.2a1.15 1.15 0 1 1 1.15 1.15c0 .9-.45 1.7-1.25 2.15l-.45-.55c.45-.3.7-.65.75-1.05a1.15 1.15 0 0 1-.2-1.7z"/>
</svg>
```

- [ ] **Step 4: Vendor, build and run the tests to make sure they pass**

```bash
touch product/icons/overrides/.gitkeep product/icons/__init__.py
python3 -I product/icons/build_theme.py vendor \
  --from /mnt/games/libreoffice/assets/fluent/package/icons \
  --license /mnt/games/libreoffice/assets/fluent/LICENSE.upstream.txt
python3 -I product/icons/build_theme.py build
python3 -I -m unittest discover -s product/tests -t .
```

Expected:
- `vendor` prints `vendored <N> files` with N > 100.
- `build` prints the two zip paths and no "16 px rendered from a 24 px source" line.
- Unit tests `OK`. All 8 `test_icons` tests pass, including the three Review Focus tests.

- [ ] **Step 5: Install, screenshot and make the contact sheet**

```bash
python3 -I product/icons/build_theme.py install --instdir instdir
python3 -I product/icons/build_theme.py sheet --out /mnt/games/libreoffice/assets/previews/step3-icons-sheet.png
python3 -I product/dev/profile.py --ui office --appearance dark --icons boost_dark
product/dev/shot.sh /mnt/games/libreoffice/assets/previews/step3-icons-dark.png
```

Expected:
- The Home tab shows the Fluent icons, in light gray on the dark ribbon.
- Other tabs still show Colibre icons, which the spec says is expected.
- Look at both PNGs with the Read tool.

- [ ] **Step 6: Commit**

```bash
git add product/icons/ product/tests/test_icons.py
git commit -m "feat(product): build the boost icon themes from Fluent icons"
```

---

### Task 8: COMPOSE icons and custom art

**Files:**
- Modify: `product/icons/manifest.json` (the entries listed below)
- No 16 px overrides are needed: 16 px slots use the trimmed 20 px design (Task 7, changed 2026-10-12 after the user found the small icons undersized). `product/icons/overrides/` stays for future hand-tuned glyphs.
- Test: `product/tests/test_icons.py` (add two tests)

**Interfaces:**
- Consumes: `build_theme.build`, `build_theme.compose` and the manifest schema (Task 7).
- Produces: the final manifest. Every annex 2 COMPOSE entry has its layers.

- [ ] **Step 1: Write the failing tests**

Append to `IconThemeTest` in `product/tests/test_icons.py`:

```python
    def test_badges_use_their_accent(self):
        # (icon, accent hex in light, accent hex in dark)
        cases = [("insertcell", "107C10", "54B054"), ("deletecell", "C50F1F", "E9737B"),
                 ("conditionalformatmenu", "AD6800", "F2B230"), ("sortfiltermenu", "0F6CBD", "479EF5")]
        for name, light, dark in cases:
            for theme, accent in (("boost", light), ("boost_dark", dark)):
                target = tuple(int(accent[i:i + 2], 16) for i in (0, 2, 4))
                pixels = self.image(theme, f"cmd/lc_{name}.png").get_flattened_data()
                close = [p for p in pixels if p[3] > 200 and max(abs(p[i] - target[i]) for i in range(3)) < 20]
                self.assertTrue(close, f"{theme}:{name} has no {accent} pixels")
```

Run: `python3 -I -m unittest discover -s product/tests -t .`
Expected: FAIL for the new test: no accent pixels exist yet.

- [ ] **Step 2: Fill in the COMPOSE layers**

Replace these entries in `manifest.json`. The values are starting points tuned for the 24 px grid. Check them in Step 4's contact sheet and adjust `scale`/`dx`/`dy`/`rect` by eye. Keep at most one accent color per icon.

```json
{"name": "conditionalformatmenu", "fill": {"color": "fill_cells"}, "large": true, "layers": [
  {"glyph": "table"},
  {"glyph": "data_bar_vertical", "style": "filled", "color": "amber", "scale": 0.55, "dx": 0.45, "dy": 0.45, "knockout": true}]},
{"name": "styleapply", "fill": {"color": "fill_cells"}, "large": true, "layers": [
  {"glyph": "table"},
  {"glyph": "paint_brush", "style": "filled", "color": "amber", "scale": 0.55, "dx": 0.45, "dy": 0.45, "knockout": true}]},
{"name": "insertcell", "fill": {"color": "fill_cells"}, "large": true, "layers": [
  {"glyph": "table"},
  {"glyph": "add_circle", "style": "filled", "color": "green", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]},
{"name": "insertrowsbefore", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "table"},
  {"rect": [0.125, 0.125, 0.75, 0.25], "opacity": 0.35},
  {"glyph": "add_circle", "style": "filled", "color": "green", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]},
{"name": "insertcolumnsbefore", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "table"},
  {"rect": [0.125, 0.125, 0.25, 0.75], "opacity": 0.35},
  {"glyph": "add_circle", "style": "filled", "color": "green", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]},
{"name": "deletecell", "fill": {"color": "fill_cells"}, "large": true, "layers": [
  {"glyph": "table"},
  {"glyph": "dismiss_circle", "style": "filled", "color": "red", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]},
{"name": "deleterows", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "table"},
  {"rect": [0.125, 0.125, 0.75, 0.25], "opacity": 0.35},
  {"glyph": "dismiss_circle", "style": "filled", "color": "red", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]},
{"name": "deletecolumns", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "table"},
  {"rect": [0.125, 0.125, 0.25, 0.75], "opacity": 0.35},
  {"glyph": "dismiss_circle", "style": "filled", "color": "red", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]},
{"name": "rowoperations", "fill": {"color": "fill_cells"}, "large": true, "layers": [
  {"glyph": "table"},
  {"rect": [0.125, 0.125, 0.75, 0.25], "opacity": 0.35}]},
{"name": "columnoperations", "fill": {"color": "fill_cells"}, "large": true, "layers": [
  {"glyph": "table"},
  {"rect": [0.125, 0.125, 0.25, 0.75], "opacity": 0.35}]},
{"name": "setoptimalcolumnwidth", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "table_resize_column"},
  {"glyph": "arrow_fit", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]},
{"name": "hiderow", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "table_resize_row"},
  {"glyph": "dismiss_circle", "style": "filled", "scale": 0.45, "dx": 0.55, "dy": 0.55, "knockout": true}]},
{"name": "hidecolumn", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "table_resize_column"},
  {"glyph": "dismiss_circle", "style": "filled", "scale": 0.45, "dx": 0.55, "dy": 0.55, "knockout": true}]},
{"name": "filldown", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "table"},
  {"glyph": "arrow_down", "style": "filled", "color": "blue", "scale": 0.55, "dx": 0.45, "dy": 0.45, "knockout": true}]},
{"name": "fillright", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "table"},
  {"glyph": "arrow_right", "style": "filled", "color": "blue", "scale": 0.55, "dx": 0.45, "dy": 0.45, "knockout": true}]},
{"name": "fillseries", "fill": {"color": "fill_cells"}, "layers": [
  {"glyph": "number_row"},
  {"glyph": "arrow_right", "style": "filled", "color": "blue", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]},
{"name": "sortfiltermenu", "large": true, "layers": [
  {"glyph": "text_sort_ascending"},
  {"glyph": "filter", "style": "filled", "color": "blue", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]},
{"name": "datafilterstandardfilter", "fill": {"color": "fill_blue"}, "layers": [
  {"glyph": "filter"},
  {"glyph": "settings", "style": "filled", "scale": 0.5, "dx": 0.5, "dy": 0.5, "knockout": true}]}
```

Re-run `vendor` (Task 7 Step 4), because the filled glyphs are new. Then run `build`.

- [ ] **Step 3: Rebuild and run the tests to make sure they pass**

```bash
python3 -I product/icons/build_theme.py build
python3 -I -m unittest discover -s product/tests -t .
python3 -I product/icons/build_theme.py install --instdir instdir
python3 -I product/icons/build_theme.py sheet --out /mnt/games/libreoffice/assets/previews/step3-icons-sheet.png
```

Expected:
- All tests `OK`.
- In the sheet, every badge is readable at 16 px, and each icon has at most one accent color.

- [ ] **Step 4: Commit**

```bash
git add product/icons/
git commit -m "feat(product): compose badge icons and hand-tune 16 px glyphs"
```

---

### Task 9: Color scheme extension and profile settings

**Files:**
- Create: `product/themes/__init__.py` (empty)
- Create: `product/themes/palette.json`
- Create: `product/themes/build_schemes.py`
- Test: `product/tests/test_schemes.py`

**Interfaces:**
- Consumes:
  - spike 0b/0d findings (Task 4)
  - `profile.py` and `shot.sh` (Task 1)
- Produces:
  - `product/themes/build_schemes.py [--out FILE.oxt]`, default `product/themes/out/boost-schemes.oxt`
  - Python API:
    - `load_palette() -> dict`
    - `scheme_values(palette) -> dict[str, dict[str, str]]` (scheme, then role, then `#RRGGBB`)
    - `xcu(palette) -> str`
    - `build(palette, out) -> Path`
    - `contrast(hex_a, hex_b) -> float`
  - The schemes `Boost Light` and `Boost Dark`, and the extension identifier `org.boost.colorschemes`.

- [ ] **Step 1: Write the failing tests**

`product/tests/test_schemes.py`:

```python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from product.themes import build_schemes as bs

# Spec §4.3, verbatim: role -> (light, dark)
SPEC = {
    "WindowColor": ("#E4F2E8", "#2B2B2B"), "WindowTextColor": ("#242424", "#F2F2F2"),
    "BaseColor": ("#FFFFFF", "#1F1F1F"), "FieldColor": ("#FFFFFF", "#1F1F1F"),
    "FaceColor": ("#C3DECB", "#454545"), "ShadowColor": ("#828282", "#7A7A7A"),
    "SeparatorColor": ("#B5D3BF", "#4D4D4D"), "ButtonColor": ("#E4F2E8", "#2B2B2B"),
    "ButtonTextColor": ("#242424", "#F2F2F2"), "AccentColor": ("#CFE8D7", "#1E4D2E"),
    "DisabledColor": ("#D3E8DA", "#383838"), "DisabledTextColor": ("#A6A6A6", "#6E6E6E"),
    "ActiveColor": ("#1B7A3E", "#5CC27E"), "ActiveTextColor": ("#FFFFFF", "#1F1F1F"),
    "ActiveBorderColor": ("#1B7A3E", "#5CC27E"), "InactiveColor": ("#E4F2E8", "#2B2B2B"),
    "InactiveTextColor": ("#A6A6A6", "#6E6E6E"), "InactiveBorderColor": ("#B5D3BF", "#4D4D4D"),
    "MenuBarColor": ("#E4F2E8", "#2B2B2B"), "MenuBarTextColor": ("#242424", "#F2F2F2"),
    "MenuBarHighlightColor": ("#D3E8DA", "#383838"), "MenuBarHighlightTextColor": ("#242424", "#F2F2F2"),
    "MenuColor": ("#FFFFFF", "#2B2B2B"), "MenuTextColor": ("#242424", "#F2F2F2"),
    "MenuHighlightColor": ("#F0F0F0", "#383838"), "MenuHighlightTextColor": ("#242424", "#F2F2F2"),
    "MenuBorderColor": ("#B5D3BF", "#4D4D4D"),
}
TEXT_PAIRS = [  # (foreground role, background role) that carry text
    ("WindowTextColor", "WindowColor"), ("WindowTextColor", "BaseColor"),
    ("ButtonTextColor", "ButtonColor"), ("WindowTextColor", "AccentColor"),
    ("ActiveTextColor", "ActiveColor"), ("MenuBarTextColor", "MenuBarColor"),
    ("MenuBarHighlightTextColor", "MenuBarHighlightColor"), ("MenuTextColor", "MenuColor"),
    ("MenuHighlightTextColor", "MenuHighlightColor"),
]
OOR = "{http://openoffice.org/2001/registry}"


class SchemesTest(unittest.TestCase):

    def setUp(self):
        self.palette = bs.load_palette()
        self.values = bs.scheme_values(self.palette)

    def test_all_27_roles_match_the_spec(self):
        self.assertEqual(27, len(SPEC))
        for index, scheme in enumerate(("Boost Light", "Boost Dark")):
            self.assertEqual({role: pair[index] for role, pair in SPEC.items()}, self.values[scheme])

    def test_text_roles_meet_wcag_aa(self):
        for scheme, roles in self.values.items():
            for fg, bg in TEXT_PAIRS:
                ratio = bs.contrast(roles[fg], roles[bg])
                self.assertGreaterEqual(ratio, 4.5, f"{scheme}: {fg} on {bg} = {ratio:.2f}")

    def test_field_border_meets_3_to_1(self):
        for scheme, roles in self.values.items():
            self.assertGreaterEqual(bs.contrast(roles["ShadowColor"], roles["WindowColor"]), 3.0, scheme)

    def test_xcu_stores_colors_as_ints_under_color_schemes(self):
        def child(node, name):
            return next(c for c in node if c.get(OOR + "name") == name)
        root = ET.fromstring(bs.xcu(self.palette))
        self.assertEqual("UI", root.get(OOR + "name"))
        light = child(child(child(root, "ColorScheme"), "ColorSchemes"), "Boost Light")
        self.assertEqual(str(0xE4F2E8), child(light, "WindowColor").find("prop/value").text)

    def test_extension_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            oxt = bs.build(self.palette, Path(tmp) / "boost-schemes.oxt")
            with zipfile.ZipFile(oxt) as z:
                self.assertEqual({"description.xml", "META-INF/manifest.xml", "ColorSchemes.xcu"},
                                 set(z.namelist()))
                self.assertIn("org.boost.colorschemes", z.read("description.xml").decode())


if __name__ == "__main__":
    unittest.main()
```

Run: `python3 -I -m unittest discover -s product/tests -t .`
Expected: an ERROR, because `product.themes` cannot be imported.

- [ ] **Step 2: Write `palette.json` and `build_schemes.py`**

`product/themes/palette.json`:

```json
{
  "schemes": ["Boost Light", "Boost Dark"],
  "tokens": {
    "surface":         ["#E4F2E8", "#2B2B2B"],
    "surface.hover":   ["#D3E8DA", "#383838"],
    "surface.pressed": ["#C3DECB", "#454545"],
    "field":           ["#FFFFFF", "#1F1F1F"],
    "field.border":    ["#828282", "#7A7A7A"],
    "separator":       ["#B5D3BF", "#4D4D4D"],
    "text":            ["#242424", "#F2F2F2"],
    "text.secondary":  ["#616161", "#ADADAD"],
    "text.disabled":   ["#A6A6A6", "#6E6E6E"],
    "accent.calc":     ["#1B7A3E", "#5CC27E"],
    "selection":       ["#CFE8D7", "#1E4D2E"],
    "menu":            ["#FFFFFF", "#2B2B2B"],
    "menu.hover":      ["#F0F0F0", "#383838"]
  },
  "roles": {
    "WindowColor": "surface", "WindowTextColor": "text", "BaseColor": "field", "FieldColor": "field",
    "FaceColor": "surface.pressed", "ShadowColor": "field.border", "SeparatorColor": "separator",
    "ButtonColor": "surface", "ButtonTextColor": "text",
    "AccentColor": "selection", "DisabledColor": "surface.hover", "DisabledTextColor": "text.disabled",
    "ActiveColor": "accent.calc", "ActiveTextColor": "field", "ActiveBorderColor": "accent.calc",
    "InactiveColor": "surface", "InactiveTextColor": "text.disabled", "InactiveBorderColor": "separator",
    "MenuBarColor": "surface", "MenuBarTextColor": "text", "MenuBarHighlightColor": "surface.hover",
    "MenuBarHighlightTextColor": "text",
    "MenuColor": "menu", "MenuTextColor": "text", "MenuHighlightColor": "menu.hover",
    "MenuHighlightTextColor": "text", "MenuBorderColor": "separator"
  }
}
```

`product/themes/build_schemes.py`:

```python
#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Build the "Boost Light"/"Boost Dark" ColorSchemes as a configuration-only extension."""
import argparse
import json
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

HERE = Path(__file__).resolve().parent
PALETTE = HERE / "palette.json"
IDENTIFIER = "org.boost.colorschemes"

DESCRIPTION = f"""<?xml version="1.0" encoding="UTF-8"?>
<description xmlns="http://openoffice.org/extensions/description/2006"
             xmlns:xlink="http://www.w3.org/1999/xlink">
  <identifier value="{IDENTIFIER}"/>
  <version value="0.1.0"/>
  <display-name><name lang="en">Boost color schemes</name></display-name>
</description>
"""
MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="http://openoffice.org/2001/manifest">
  <manifest:file-entry manifest:media-type="application/vnd.sun.star.configuration-data"
                       manifest:full-path="ColorSchemes.xcu"/>
</manifest:manifest>
"""


def load_palette():
    return json.loads(PALETTE.read_text(encoding="utf-8"))


def scheme_values(palette):
    return {scheme: {role: palette["tokens"][token][index] for role, token in palette["roles"].items()}
            for index, scheme in enumerate(palette["schemes"])}


def _luminance(hex_color):
    channels = [int(hex_color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def xcu(palette):
    # Same place as the built-in schemes: officecfg/.../Office/UI.xcu:135-142.
    # Colors are xs:int (UI.xcs:53).
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<oor:component-data xmlns:oor="http://openoffice.org/2001/registry"'
             ' xmlns:xs="http://www.w3.org/2001/XMLSchema" oor:name="UI" oor:package="org.openoffice.Office">',
             '  <node oor:name="ColorScheme">',
             '    <node oor:name="ColorSchemes">']
    for scheme, roles in scheme_values(palette).items():
        lines.append(f'      <node oor:name={quoteattr(scheme)} oor:op="replace">')
        for role, color in roles.items():
            lines.append(f'        <node oor:name="{role}"><prop oor:name="Color">'
                         f'<value>{int(color.lstrip("#"), 16)}</value></prop></node>')
        lines.append("      </node>")
    lines += ["    </node>", "  </node>", "</oor:component-data>"]
    return "\n".join(lines) + "\n"


def build(palette, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("description.xml", DESCRIPTION)
        z.writestr("META-INF/manifest.xml", MANIFEST)
        z.writestr("ColorSchemes.xcu", xcu(palette))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=HERE / "out" / "boost-schemes.oxt")
    args = ap.parse_args(argv)
    print(build(load_palette(), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the tests to make sure they pass**

Run: `python3 -I -m unittest discover -s product/tests -t .`
Expected: `OK`. All 5 `test_schemes` tests pass, including the Review Focus test `test_text_roles_meet_wcag_aa`.

- [ ] **Step 4: Install and screenshot both modes**

```bash
python3 -I product/themes/build_schemes.py
instdir/program/unopkg add -f product/themes/out/boost-schemes.oxt \
  -env:UserInstallation=file:///mnt/games/libreoffice/dev-profile
P=/mnt/games/libreoffice/assets/previews
python3 -I product/dev/profile.py --ui office --appearance dark --icons boost_dark --scheme "Boost Dark" --tint 255
product/dev/shot.sh $P/step4-colors-dark.png
python3 -I product/dev/profile.py --ui office --appearance light --icons boost --scheme "Boost Light" --tint 255
LO_GTK_THEME=adw-gtk3 product/dev/shot.sh $P/step4-colors-light.png
```

Expected:
- `unopkg list` with the same `-env` shows `org.boost.colorschemes`.
- In both screenshots the ribbon is neutral (#E4F2E8 / #2B2B2B areas) with no green tint, and the Home captions are plain.
- Compare against the `## 0b` findings. Every area listed there as "unchanged" is expected to stay unchanged, and becomes a stage B item.

- [ ] **Step 5: Commit**

```bash
git add product/themes/ product/tests/test_schemes.py
git commit -m "feat(product): ship Boost light and dark color schemes as an extension"
```

---

### Task 10: Validation and the user review gate

**Files:**
- Modify: `product/docs/stage-a-findings.md` (add a `## Validation` section)
- Modify: `product/docs/design/calc-home-prototype.txt` (set the status of step 4)

**Interfaces:**
- Consumes: everything above.
- Produces: the screenshot set and contact sheet the user approves, and the stage B list.

- [ ] **Step 1: Run every automatic check**

```bash
python3 -I -m unittest discover -s product/tests -t .
product/dev/check-ui.sh sc/uiconfig/scalc/ui/notebookbar_office.ui
product/dev/uitest.sh notebookbarOffice.NotebookbarOffice.test_office_variant_loads \
  notebookbarOffice.NotebookbarOffice.test_switch_back_to_compact \
  notebookbarOffice.NotebookbarOffice.test_home_sections_and_toolboxes
git diff --stat 62abc2329664 -- 'sc/uiconfig/scalc/ui/notebookbar*.ui'
```

Expected:
- All unit tests `OK`, `check-ui.sh` exits 0, and the 3 UITests PASS.
- The diff stat lists only `notebookbar_office.ui`.

- [ ] **Step 2: Width test**

```bash
P=/mnt/games/libreoffice/assets/previews
python3 -I product/dev/profile.py --ui office --appearance dark --icons boost_dark --scheme "Boost Dark" --tint 255
product/dev/shot.sh $P/final-dark-1920.png
product/dev/shot.sh $P/final-dark-1366.png 1366x768
product/dev/shot.sh $P/final-dark-1024.png 1024x768
```

Expected:
- At 1920 all 8 sections are visible.
- At 1366 and 1024 the right-most sections collapse, and none overlap or clip mid-button.
- If sections clip instead of collapsing, record "collapse: NO" under `## Validation` and list it as stage B. Do not change C++ here.

- [ ] **Step 3: Write the validation record**

Add `## Validation` to `product/docs/stage-a-findings.md`. It lists:
- every screenshot path
- the contact sheet path
- the check results from Step 1
- the width result
- the stage B list, which starts from spec §8 plus every "unchanged" area from `## 0b` and every gap found above
- a known limitation: the dev build is en-US only (no `--with-lang`), so long translated labels are not checked yet

Commit:

```bash
git add product/docs/stage-a-findings.md
git commit -m "docs(product): record stage A validation and stage B list"
```

- [ ] **Step 4: User review gate**

Show the user these files, and ask for approval in one question:
- `step3-icons-sheet.png`
- `final-dark-1920.png`, `step4-colors-light.png`
- the two widths
- the baseline pair (`baseline-tabbed-dark.png`, `baseline-compact-dark.png`)

Stage A is done only after the user approves.

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

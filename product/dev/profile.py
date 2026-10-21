#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Write registrymodifications.xcu for the isolated LibreOffice dev profile."""
import argparse
import shutil
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

DEFAULT_PROFILE = Path("/mnt/games/libreoffice/dev-profile")
FONTS = Path(__file__).resolve().parents[1] / "fonts"
TOOLBAR_MODE = "/org.openoffice.Office.UI.ToolbarMode"
APPLICATION = TOOLBAR_MODE + "/Applications/org.openoffice.Office.UI.ToolbarMode:Application['%s']"
CALC_APP = APPLICATION % "Calc"
WRITER_APP = APPLICATION % "Writer"
# app choice -> its ToolbarMode application name (Applications/<name>, Active<name>).
APPS = {"calc": "Calc", "writer": "Writer"}
APPEARANCE = "/org.openoffice.Office.Common/Appearance"
MISC = "/org.openoffice.Office.Common/Misc"

# ui choice -> (Applications/<app>/Active, Active<app>). Active holds the mode's
# CommandArg (sfx2/source/appl/appserv.cxx:1015); Active<app> names the .ui file.
UI_MODES = {
    "default": ("Default", None),
    "compact": ("notebookbar_compact.ui", "notebookbar_compact.ui"),
    "tabbed": ("notebookbar.ui", "notebookbar.ui"),
    "office": ("notebookbar_office.ui", "notebookbar_office.ui"),
}
# Office.Common/Appearance/ApplicationAppearance: 0 system, 1 light, 2 dark.
APPEARANCES = {"light": "1", "dark": "2"}
# font choice -> VCLSettings/UIFont/FamilyName, which the gtk3 plugin puts in place of the
# desktop's UI font family. "system" writes nothing and keeps the desktop's font.
UI_FONT = "/org.openoffice.VCL/VCLSettings/UIFont"
UI_FONTS = {"system": None, "selawik": "Selawik", "inter": "Inter"}


def build_items(ui, appearance, icons=None, scheme=None, tint=None, font="system", app="calc"):
    active, ui_file = UI_MODES[ui]
    name = APPS[app]
    items = [(APPLICATION % name, "Active", active)]
    if ui_file:
        items.append((TOOLBAR_MODE, "Active" + name, ui_file))
    items.append((APPEARANCE, "ApplicationAppearance", APPEARANCES[appearance]))
    if icons:
        items.append((MISC, "SymbolStyle", icons))
    if scheme:
        # The theme engine ignores color schemes unless LibreOfficeTheme is 1.
        items.append((APPEARANCE, "LibreOfficeTheme", "1"))
        items.append(("/org.openoffice.Office.UI/ColorScheme", "CurrentColorScheme", scheme))
    if tint is not None:
        items.append((MISC, "NotebookbarColorTransparency", str(tint)))
    if UI_FONTS[font]:
        items.append((UI_FONT, "FamilyName", UI_FONTS[font]))
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


def install_fonts(profile, font):
    """Copy the bundled font into the profile's user/fonts, which VCL adds to the font path."""
    dest = Path(profile) / "user" / "fonts"
    dest.mkdir(parents=True, exist_ok=True)
    for ttf in sorted((FONTS / font).glob("*.ttf")):
        shutil.copyfile(ttf, dest / ttf.name)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app", choices=sorted(APPS), default="calc")
    ap.add_argument("--ui", choices=sorted(UI_MODES), required=True)
    ap.add_argument("--appearance", choices=sorted(APPEARANCES), required=True)
    ap.add_argument("--icons")
    ap.add_argument("--scheme")
    ap.add_argument("--tint", type=int)
    ap.add_argument("--font", choices=list(UI_FONTS), default="system")
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    args = ap.parse_args(argv)
    if UI_FONTS[args.font]:
        install_fonts(args.profile, args.font)
    print(write(args.profile, build_items(args.ui, args.appearance, args.icons, args.scheme, args.tint,
                                          args.font, args.app)))


if __name__ == "__main__":
    main()

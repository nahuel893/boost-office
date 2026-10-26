#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Write registrymodifications.xcu for the isolated LibreOffice dev profile."""
import argparse
import json
import shutil
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

DEFAULT_PROFILE = Path("/mnt/games/libreoffice/dev-profile")
FONTS = Path(__file__).resolve().parents[1] / "fonts"
TOOLBAR_MODE = "/org.openoffice.Office.UI.ToolbarMode"
APPLICATION = TOOLBAR_MODE + "/Applications/org.openoffice.Office.UI.ToolbarMode:Application['%s']"
CALC_APP = APPLICATION % "Calc"
WRITER_APP = APPLICATION % "Writer"
IMPRESS_APP = APPLICATION % "Impress"
# app choice -> its ToolbarMode application name (Applications/<name>, Active<name>).
APPS = {"calc": "Calc", "writer": "Writer", "impress": "Impress"}
APPEARANCE = "/org.openoffice.Office.Common/Appearance"
MISC = "/org.openoffice.Office.Common/Misc"
# Impress's Misc/NewDoc/AutoPilot (Impress.xcs, default true) opens the template dialog on a new
# presentation (sd/source/ui/app/optsitem.cxx).
IMPRESS_NEWDOC = "/org.openoffice.Office.Impress/Misc/NewDoc"

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
# A fresh profile has no ooSetupLastVersion, so the welcome dialog opens over the first document
# (sfx2/source/view/viewfrm.cxx:1705-1717) unless Setup/Product/WhatsNew is false.
SETUP_PRODUCT = "/org.openoffice.Setup/Product"
# Setup/Product/ooName (Setup.xcu: ${PRODUCTNAME} of the build) is %PRODUCTNAME in the UI strings, the window titles
# and the Options tree (unotools ConfigManager::getProductName), so a configuration item renames the product with no
# rebuild. Strings compiled into the program keep the build's name.
PRODUCT_NAME = "Boost Office"
# The Start Center's recent and template views paint these colors (sfx2 RecentDocsView and TemplateDefaultView
# UpdateColors; Common.xcs defaults #666666 and #EEEEEE). A Boost scheme gives them its workspace and text
# colors, read from the palette its color scheme is built from.
START_CENTER = "/org.openoffice.Office.Common/Help/StartCenter"
PALETTE = Path(__file__).resolve().parents[1] / "themes" / "palette.json"

# The Boost looks: the build_items arguments of office.sh light|dark, shot-tab.sh light|dark and the
# installed boost.xcd layer (product/install/build_xcd.py), which all take them from here. The icon themes are
# product/icons/build_theme.py's THEMES, the schemes product/themes/palette.json's.
LOOKS = {
    "light": {"ui": "office", "appearance": "light", "icons": "boost", "scheme": "Boost Light", "tint": 255,
              "font": "inter"},
    "dark": {"ui": "office", "appearance": "dark", "icons": "boost_dark", "scheme": "Boost Dark", "tint": 255,
             "font": "inter"},
}


def start_center_colors(scheme):
    """(background, text) of the Start Center views for a palette.json scheme, as xs:int strings; None for
    any other scheme."""
    palette = json.loads(PALETTE.read_text(encoding="utf-8"))
    if scheme not in palette["schemes"]:
        return None
    index = palette["schemes"].index(scheme)
    return tuple(str(int(palette["tokens"][token][index].lstrip("#"), 16)) for token in ("workspace", "text"))


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
        colors = start_center_colors(scheme)
        if colors:
            items.append((START_CENTER, "StartCenterThumbnailsBackgroundColor", colors[0]))
            items.append((START_CENTER, "StartCenterThumbnailsTextColor", colors[1]))
    if tint is not None:
        items.append((MISC, "NotebookbarColorTransparency", str(tint)))
    if UI_FONTS[font]:
        items.append((UI_FONT, "FamilyName", UI_FONTS[font]))
    # Keep screenshots free of first-start, welcome and tip dialogs, and of Impress's template dialog.
    items.append((MISC, "FirstRun", "false"))
    items.append((MISC, "ShowTipOfTheDay", "false"))
    items.append((SETUP_PRODUCT, "WhatsNew", "false"))
    items.append((SETUP_PRODUCT, "ooName", PRODUCT_NAME))
    if app == "impress":
        items.append((IMPRESS_NEWDOC, "AutoPilot", "false"))
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
    ap.add_argument("--app", choices=[*sorted(APPS), "all"], default="calc",
                    help="all: the items of every app, each once (the Start Center opens any of them)")
    ap.add_argument("--look", choices=sorted(LOOKS),
                    help="a Boost look from LOOKS; --ui, --appearance, --icons, --scheme, --tint or --font given as "
                         "well win over its values")
    ap.add_argument("--ui", choices=sorted(UI_MODES), help="required without --look")
    ap.add_argument("--appearance", choices=sorted(APPEARANCES), help="required without --look")
    ap.add_argument("--icons")
    ap.add_argument("--scheme")
    ap.add_argument("--tint", type=int)
    ap.add_argument("--font", choices=list(UI_FONTS), help="default: the look's font, else system")
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    args = ap.parse_args(argv)
    chosen = {"font": "system", **LOOKS.get(args.look, {})}
    chosen.update({key: getattr(args, key) for key in ("ui", "appearance", "icons", "scheme", "tint", "font")
                   if getattr(args, key) is not None})
    if "ui" not in chosen or "appearance" not in chosen:
        ap.error("--ui and --appearance are required without --look")
    if UI_FONTS[chosen["font"]]:
        install_fonts(args.profile, chosen["font"])
    items = []
    for app in (sorted(APPS) if args.app == "all" else [args.app]):
        items += [item for item in build_items(**chosen, app=app) if item not in items]
    print(write(args.profile, items))


if __name__ == "__main__":
    main()

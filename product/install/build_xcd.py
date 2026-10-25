#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Write boost.xcd: the Boost look as a default configuration layer of an installed tree.

Copy the output to <instdir>/share/registry/boost.xcd. The xcsxcu layer reads every *.xcd there
(configmgr/source/components.cxx:750-828) and the file depends on main.xcd, so its values replace the
stock defaults while anything a user changes (the user layer) still wins. It carries the same items the
dev profile writes (product/dev/profile.py build_items) for Calc, Writer and Impress, plus the color
schemes and the per-app tab accents of the scheme extension (product/themes/build_schemes.py).
Usage: python3 -I product/install/build_xcd.py [--theme light|dark] [--out FILE]
"""
import argparse
import ast
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from product.dev import profile  # noqa: E402
from product.themes import build_schemes  # noqa: E402

OOR = "http://openoffice.org/2001/registry"
ET.register_namespace("oor", OOR)
# Every token in palette.json and every scheme list is ordered (light, dark).
THEMES = ("light", "dark")
# office.sh's light and dark looks pass --tint 255 (the one value not in a Python table yet).
TINT = 255
FONT = "inter"
BUILD_THEME = ROOT / "product" / "icons" / "build_theme.py"
# Not in the dev profile, whose ooSetupLastVersion is set: a fresh profile has none, so the welcome
# dialog opens over the first document (sfx2/source/view/viewfrm.cxx:1705-1717) unless WhatsNew is off.
FIRST_START = [("/org.openoffice.Setup/Product", "WhatsNew", "false")]


def _q(name):
    return f"{{{OOR}}}{name}"


def icon_themes():
    """build_theme.THEMES (icon theme -> mode), read from its source: importing it needs Pillow."""
    for node in ast.parse(BUILD_THEME.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "THEMES" for t in node.targets):
            return ast.literal_eval(node.value)
    raise LookupError(f"no THEMES in {BUILD_THEME}")


def preset(theme, palette=None):
    """profile.build_items arguments of the Boost look (office.sh light|dark)."""
    palette = palette or build_schemes.load_palette()
    icons = {mode: name for name, mode in icon_themes().items()}[theme]
    return {"ui": "office", "appearance": theme, "icons": icons,
            "scheme": palette["schemes"][THEMES.index(theme)], "tint": TINT, "font": FONT}


def items(theme, palette=None):
    """The profile items of the three apps, each (path, prop) once."""
    args = preset(theme, palette)
    out = {}
    for app in profile.APPS:
        for path, prop, value in profile.build_items(**args, app=app) + FIRST_START:
            if out.setdefault((path, prop), value) != value:
                raise ValueError(f"{path}/{prop}: {out[(path, prop)]} or {value}")
    return [(path, prop, value) for (path, prop), value in out.items()]


def _component(root, package, name):
    for comp in root.findall(_q("component-data")):
        if comp.get(_q("package")) == package and comp.get(_q("name")) == name:
            return comp
    return ET.SubElement(root, _q("component-data"), {_q("name"): name, _q("package"): package})


def _child(parent, tag, name):
    for child in parent.findall(tag):
        if child.get(_q("name")) == name:
            return child
    return ET.SubElement(parent, tag, {_q("name"): name})


def _set(parent, name, value):
    prop = _child(parent, "prop", name)
    for old in list(prop):
        prop.remove(old)
    ET.SubElement(prop, "value").text = value


def _add_item(root, path, name, value):
    # path as in registrymodifications.xcu: /package.Component/Group/template:Type['Member']/...
    head, *segments = path.strip("/").split("/")
    package, component = head.rsplit(".", 1)
    node = _component(root, package, component)
    for segment in segments:
        if segment.endswith("']"):
            segment = segment[segment.index("['") + 2:-2]
        node = _child(node, "node", segment)
    _set(node, name, value)


def _merge(dst, src):
    for child in src:
        if child.tag == "node":
            node = _child(dst, "node", child.get(_q("name")))
            if child.get(_q("op")):
                node.set(_q("op"), child.get(_q("op")))
            _merge(node, child)
        elif child.tag == "prop":
            _set(dst, child.get(_q("name")), child.findtext("value"))


def render(theme):
    palette = build_schemes.load_palette()
    root = ET.Element(_q("data"))
    ET.SubElement(root, "dependency", {"file": "main"})
    for path, name, value in items(theme, palette):
        _add_item(root, path, name, value)
    for xcu in (build_schemes.xcu(palette), build_schemes.toolbarmode_xcu(palette)):
        src = ET.fromstring(xcu)
        _merge(_component(root, src.get(_q("package")), src.get(_q("name"))), src)
    ET.indent(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=THEMES, default="light")
    ap.add_argument("--out", type=Path, help="file to write (default: stdout)")
    args = ap.parse_args(argv)
    text = render(args.theme)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(args.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

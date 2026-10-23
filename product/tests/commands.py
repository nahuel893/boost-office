# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Command labels, tooltips and image flags as LibreOffice resolves them for one app (Calc by default).

A command is looked up in the app's file first (CalcCommands.xcu, WriterCommands.xcu), then in
GenericCommands.xcu; the other modules' files never apply. Every test reads commands through here.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "officecfg/registry/data/org/openoffice/Office/UI"
OOR = "{http://openoffice.org/2001/registry}"
LOOKUP_ORDERS = {  # most specific first
    "calc": ("CalcCommands.xcu", "GenericCommands.xcu"),
    "writer": ("WriterCommands.xcu", "GenericCommands.xcu"),
}
LOOKUP_ORDER = LOOKUP_ORDERS["calc"]


def properties(prop_name, ui_dir=UI_DIR, app="calc"):
    """Command name -> the value of one property, the first file of the app's lookup order defining it wins."""
    found = {}
    for file in LOOKUP_ORDERS[app]:
        here = {}
        for node in ET.parse(Path(ui_dir) / file).iter("node"):
            name = node.get(OOR + "name")
            if name and name.startswith(".uno:"):
                for prop in node.findall("prop"):
                    if prop.get(OOR + "name") == prop_name:
                        here[name] = prop.findtext("value")  # within one file the later node wins
        for name, value in here.items():
            found.setdefault(name, value)  # across files the earlier one wins
    return found


def commands_xcu(ui_dir=UI_DIR, app="calc"):
    """Label of every command the app knows: ".uno:Name" (or a variant URL node) -> label."""
    return properties("Label", ui_dir, app)


def tooltips(ui_dir=UI_DIR, app="calc"):
    return properties("TooltipLabel", ui_dir, app)


def flagged_commands(ui_dir=UI_DIR, app="calc"):
    """Commands with the image flag (Properties bit 1) in the app's lookup order."""
    return {name for name, value in properties("Properties", ui_dir, app).items() if int(value) & 1}


WRITER_SUFFIX = ("WriterPopup", "WriterControl")


def controller_nodes(controller_xcu=UI_DIR / "Controller.xcu", app="calc"):
    """Controller.xcu nodes that name a command: node name -> {Command, Controller, Module, Value}.

    A Writer node that shares its command with Calc carries a "Writer" suffix (InsertShapesMenuWriterPopup).
    Those nodes are left out unless app is "writer", so Calc's one-node-per-command checks keep their meaning.
    Several modules can hold a node of one name (the stock "c1", "c5" language nodes, DistributeControl): the
    first keeps the plain name, later ones get "#2", "#3", ... so no node is lost.
    """
    nodes = {}
    for node in ET.parse(controller_xcu).iter("node"):
        props = {p.get(OOR + "name"): p.findtext("value") for p in node.findall("prop")}
        name = node.get(OOR + "name")
        if "Command" in props and (app == "writer" or not name.endswith(WRITER_SUFFIX)):
            key, count = name, 1
            while key in nodes:
                count += 1
                key = "%s#%d" % (name, count)
            nodes[key] = props
    return nodes

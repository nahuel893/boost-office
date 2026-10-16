# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Command labels, tooltips and image flags as LibreOffice resolves them for Calc.

A command is looked up in CalcCommands.xcu first, then in GenericCommands.xcu; the other
modules' files (Writer, Draw, ...) never apply to Calc. Every test reads commands through here.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "officecfg/registry/data/org/openoffice/Office/UI"
OOR = "{http://openoffice.org/2001/registry}"
LOOKUP_ORDER = ("CalcCommands.xcu", "GenericCommands.xcu")  # most specific first


def properties(prop_name, ui_dir=UI_DIR):
    """Command name -> the value of one property, the first file in LOOKUP_ORDER defining it wins."""
    found = {}
    for file in LOOKUP_ORDER:
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


def commands_xcu(ui_dir=UI_DIR):
    """Label of every command Calc knows: ".uno:Name" (or a variant URL node) -> label."""
    return properties("Label", ui_dir)


def tooltips(ui_dir=UI_DIR):
    return properties("TooltipLabel", ui_dir)


def flagged_commands(ui_dir=UI_DIR):
    """Commands with the image flag (Properties bit 1) in the Calc lookup order."""
    return {name for name, value in properties("Properties", ui_dir).items() if int(value) & 1}


def controller_nodes(controller_xcu=UI_DIR / "Controller.xcu"):
    """Controller.xcu nodes that name a command: node name -> {Command, Controller, Module, Value}."""
    nodes = {}
    for node in ET.parse(controller_xcu).iter("node"):
        props = {p.get(OOR + "name"): p.findtext("value") for p in node.findall("prop")}
        if "Command" in props:
            nodes[node.get(OOR + "name")] = props
    return nodes

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Command labels resolve the way LibreOffice resolves them for Calc: CalcCommands, then Generic."""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import commands

XCU = """<?xml version="1.0" encoding="UTF-8"?>
<oor:component-data xmlns:oor="http://openoffice.org/2001/registry" oor:name="%s" oor:package="x">
<node oor:name="UserInterface"><node oor:name="Commands">%s</node></node></oor:component-data>"""
NODE = ('<node oor:name="%s" oor:op="replace"><prop oor:name="Label"><value>%s</value></prop>'
        '<prop oor:name="TooltipLabel"><value>tip %s</value></prop></node>')


def write(directory, name, *nodes):
    body = "".join(NODE % (cmd, label, label) for cmd, label in nodes)
    (directory / (name + ".xcu")).write_text(XCU % (name, body), encoding="utf-8")


class CommandLookupTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        write(self.dir, "CalcCommands", (".uno:Both", "Calc label"), (".uno:CalcOnly", "Calc only"))
        write(self.dir, "GenericCommands", (".uno:Both", "Generic label"), (".uno:GenericOnly", "Generic only"))
        write(self.dir, "WriterCommands", (".uno:Both", "Writer label"), (".uno:WriterOnly", "Writer only"))

    def test_calc_wins_over_generic_and_other_modules_are_ignored(self):
        labels = commands.commands_xcu(self.dir)
        self.assertEqual("Calc label", labels[".uno:Both"])
        self.assertEqual("Calc only", labels[".uno:CalcOnly"])
        self.assertEqual("Generic only", labels[".uno:GenericOnly"])
        self.assertNotIn(".uno:WriterOnly", labels)

    def test_tooltips_follow_the_same_order(self):
        tips = commands.tooltips(self.dir)
        self.assertEqual("tip Calc label", tips[".uno:Both"])
        self.assertEqual("tip Generic only", tips[".uno:GenericOnly"])

    def test_the_real_calc_labels_come_from_calc_commands_first(self):
        labels = commands.commands_xcu()
        self.assertEqual("Print Titles", labels[".uno:PageLayoutPrintTitles"])
        self.assertIn(".uno:Open", labels)  # a Generic command


class ControllerNodesTest(unittest.TestCase):

    def test_nodes_that_share_a_name_are_all_kept(self):
        xcu = XCU % ("Controller", "".join(
            '<node oor:name="%s"><prop oor:name="Command"><value>%s</value></prop></node>' % pair
            for pair in (("c1", ".uno:A"), ("c1", ".uno:B"), ("c1", ".uno:C"), ("d", ".uno:D"))))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Controller.xcu"
            path.write_text(xcu, encoding="utf-8")
            nodes = commands.controller_nodes(path)
        self.assertEqual({"c1": ".uno:A", "c1#2": ".uno:B", "c1#3": ".uno:C", "d": ".uno:D"},
                         {name: props["Command"] for name, props in nodes.items()})

    def test_every_node_of_the_real_file_that_names_a_command_is_kept(self):
        named = [n for n in ET.parse(commands.UI_DIR / "Controller.xcu").iter("node")
                 if any(p.get(commands.OOR + "name") == "Command" for p in n.findall("prop"))]
        # Impress's nodes (names ending ImpressPopup or ImpressControl) are left out for Writer, as Writer's
        # are for Impress; no other node is lost to a name collision
        others = commands.APP_SUFFIXES["impress"]
        mine = [n for n in named if not n.get(commands.OOR + "name").endswith(others)]
        self.assertEqual(len(mine), len(commands.controller_nodes(app="writer")))


if __name__ == "__main__":
    unittest.main()

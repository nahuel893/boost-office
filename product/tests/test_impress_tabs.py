# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Impress's Tabbed Office ribbon: notebookbar_office.ui is the stock notebookbar.ui, the tab
operations of impress_tabs.json, then every impress_<tab>.json page, the same contract as Calc's
and Writer's.

The test tooling reads Impress's files through the same modules as Calc's and Writer's:
office.app("impress"), commands with app="impress", placeholders.registry("impress").
"""
import collections
import json
import re
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from product.tests import commands, office, placeholders
from product.ui import gen_ribbon as g

IMPRESS = office.app("impress")
STOCK_UI = "sd/uiconfig/simpress/ui/notebookbar.ui"
OFFICE_UI = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
MAKEFILE = "sd/UIConfig_simpress.mk"
ID_IN_LINE = re.compile(r"@id='([^']+)'")


class ImpressOfficeUiTest(unittest.TestCase):

    def setUp(self):
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def test_the_office_ui_is_stock_plus_tab_operations_plus_every_generated_page(self):
        self.assertEqual(office.expected_office_ui("impress"), self.office)

    def test_regenerating_the_office_ui_changes_nothing(self):
        tabs = json.loads(IMPRESS.tabs.read_text(encoding="utf-8"))
        self.assertEqual(self.office, g.regenerate_all(self.office, tabs, office.page_layouts("impress")))

    def test_every_object_id_is_unique(self):
        # the builder finds a widget by its id, so a second object with the same id is never reached
        ids = collections.Counter(obj.get("id") for obj in ET.fromstring(self.office).iter("object")
                                  if obj.get("id"))
        self.assertGreater(len(ids), 1000)
        self.assertEqual({}, {wid: count for wid, count in ids.items() if count > 1})

    def test_the_home_and_layout_pages_fill_the_tab_page(self):
        # upstream centers them (notebookbar.ui "Home Tab", "Layout"), which would put their
        # captions on another baseline than the other tabs'; Calc and Writer did the same
        root = ET.fromstring(self.office)
        for wid in ("Home Tab", "Layout"):
            valign = [p.text for p in root.find(f".//object[@id='{wid}']").findall("property[@name='valign']")]
            self.assertEqual(["fill"], valign, wid)

    def test_the_app_table_names_the_impress_files(self):
        self.assertEqual(office.ROOT / STOCK_UI, IMPRESS.upstream)
        self.assertEqual(office.ROOT / OFFICE_UI, IMPRESS.office)
        self.assertEqual(office.ROOT / "solenv/sanitizers/ui/modules/simpress.suppr", IMPRESS.suppr)
        # the module has no simpress.false, so there is no false-positive file to keep in sync
        self.assertIsNone(IMPRESS.false)
        self.assertFalse((office.ROOT / "solenv/sanitizers/ui/modules/simpress.false").exists())
        self.assertEqual(office.UI_DIR / "impress_tabs.json", IMPRESS.tabs)
        self.assertEqual(("impress", "TabbedImpress", "DrawImpressCommands.xcu"),
                         (g.APPS["impress"].prefix, g.APPS["impress"].context, g.APPS["impress"].commands))

    def test_the_office_ui_is_installed_with_the_other_impress_notebookbars(self):
        makefile = (office.ROOT / MAKEFILE).read_text(encoding="utf-8")
        self.assertIn("\tsd/uiconfig/simpress/ui/notebookbar_groupedbar_compact \\\n"
                      "\tsd/uiconfig/simpress/ui/notebookbar_office \\\n", makefile)

    def test_every_ui_the_makefile_installs_has_a_file(self):
        # A .ui listed in gb_UIConfig_add_uifiles without its file breaks the build, and one that is
        # dropped must leave the list too.
        makefile = (office.ROOT / MAKEFILE).read_text(encoding="utf-8")
        registered = re.findall(r"^\t(sd/uiconfig/simpress/ui/[\w-]+) \\$", makefile, re.MULTILINE)
        self.assertGreater(len(registered), 50)
        missing = [ui for ui in registered if not (office.ROOT / (ui + ".ui")).is_file()]
        self.assertEqual([], missing)


class ImpressSuppressionsTest(unittest.TestCase):
    """simpress.suppr holds an office copy of every stock notebookbar.ui line."""

    def setUp(self):
        self.office = IMPRESS.office.read_text(encoding="utf-8")
        self.present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office))
        self.suppr = IMPRESS.suppr.read_text(encoding="utf-8")

    def test_every_stock_line_has_an_office_copy_while_its_widget_is_there(self):
        lines = self.suppr.splitlines()
        stock = [line for line in lines if line.startswith(STOCK_UI + ":")]
        self.assertTrue(stock)
        copies = {line for line in lines if line.startswith(OFFICE_UI + ":")}
        missing = []
        for line in stock:
            match = ID_IN_LINE.search(line)
            if match and match.group(1) not in self.present:
                continue  # a generated page replaced that widget
            if OFFICE_UI + line[len(STOCK_UI):] not in copies:
                missing.append(line)
        self.assertEqual([], missing)

    def test_the_suppressions_are_in_sync_with_the_office_ui(self):
        self.assertEqual(self.suppr, g.sync_suppr(self.suppr, OFFICE_UI, self.office))


XCU = ('<?xml version="1.0" encoding="UTF-8"?>\n<oor:component-data '
       'xmlns:oor="http://openoffice.org/2001/registry" oor:name="%s" oor:package="x">'
       '<node oor:name="UserInterface"><node oor:name="%s">%s</node></node></oor:component-data>')


class ImpressToolingTest(unittest.TestCase):

    def test_impress_labels_come_from_draw_impress_commands_then_generic(self):
        node = '<node oor:name="%s" oor:op="replace"><prop oor:name="Label"><value>%s</value></prop></node>'
        with tempfile.TemporaryDirectory() as tmp:
            for name, nodes in (("CalcCommands", ((".uno:Both", "Calc"), (".uno:CalcOnly", "Calc only"))),
                                ("WriterCommands", ((".uno:Both", "Writer"), (".uno:WriterOnly", "Writer only"))),
                                ("DrawImpressCommands", ((".uno:Both", "Impress"),
                                                         (".uno:ImpressOnly", "Impress only"))),
                                ("GenericCommands", ((".uno:Both", "Generic"), (".uno:GenericOnly", "Generic only")))):
                body = "".join(node % pair for pair in nodes)
                (Path(tmp) / (name + ".xcu")).write_text(XCU % (name, "Commands", body), encoding="utf-8")
            labels = commands.commands_xcu(tmp, app="impress")
        self.assertEqual("Impress", labels[".uno:Both"])
        self.assertEqual("Impress only", labels[".uno:ImpressOnly"])
        self.assertEqual("Generic only", labels[".uno:GenericOnly"])
        self.assertNotIn(".uno:CalcOnly", labels)
        self.assertNotIn(".uno:WriterOnly", labels)

    def test_the_real_labels_differ_per_app(self):
        self.assertEqual("Email as ~Microsoft PowerPoint Presentation...",
                         commands.commands_xcu(app="impress")[".uno:SendMailDocAsMS"])
        self.assertEqual("Email as ~Microsoft Word...", commands.commands_xcu(app="writer")[".uno:SendMailDocAsMS"])
        self.assertEqual("Email as ~Microsoft Excel...", commands.commands_xcu()[".uno:SendMailDocAsMS"])
        # the generator reads the same files for the label a ribbon button shows
        self.assertEqual("Email as Microsoft PowerPoint Presentation",
                         g.shown_labels(str(office.ROOT), "impress")[".uno:SendMailDocAsMS"])

    def test_each_app_sees_its_own_controller_nodes_and_no_other_apps(self):
        # A node that shares its command with another app's carries its app's suffix
        # (InsertShapesMenuWriterPopup); only that app's checks see it.
        node = ('<node oor:name="%s" oor:op="replace"><prop oor:name="Command"><value>.uno:Shared</value></prop>'
                '<prop oor:name="Module"><value>m</value></prop></node>')
        names = ("SharedPopup", "SharedWriterPopup", "SharedWriterControl", "SharedImpressPopup",
                 "SharedImpressControl")
        with tempfile.TemporaryDirectory() as tmp:
            xcu = Path(tmp) / "Controller.xcu"
            xcu.write_text(XCU % ("Controller", "Registered", "".join(node % name for name in names)),
                           encoding="utf-8")
            seen = {app: set(commands.controller_nodes(xcu, app=app)) for app in ("calc", "writer", "impress")}
        self.assertEqual({"SharedPopup"}, seen["calc"])
        self.assertEqual({"SharedPopup", "SharedWriterPopup", "SharedWriterControl"}, seen["writer"])
        self.assertEqual({"SharedPopup", "SharedImpressPopup", "SharedImpressControl"}, seen["impress"])

    def test_each_app_has_its_own_placeholder_registry(self):
        self.assertEqual(placeholders.REGISTRY, placeholders.registry("calc"))
        self.assertEqual(Path(placeholders.__file__).with_name("placeholders_writer.json"),
                         placeholders.registry("writer"))
        self.assertEqual(Path(placeholders.__file__).with_name("placeholders_impress.json"),
                         placeholders.registry("impress"))


if __name__ == "__main__":
    unittest.main()

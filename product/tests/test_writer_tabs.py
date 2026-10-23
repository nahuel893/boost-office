# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Writer's Tabbed Office ribbon: notebookbar_office.ui is the stock notebookbar.ui, the tab
operations of writer_tabs.json, then every writer_<tab>.json page, the same contract as Calc's.

The test tooling reads Writer's files through the same modules as Calc's: office.app("writer"),
commands with app="writer", placeholders.registry("writer").
"""
import json
import re
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from product.tests import commands, office, placeholders
from product.ui import gen_ribbon as g

WRITER = office.app("writer")
STOCK_UI = "sw/uiconfig/swriter/ui/notebookbar.ui"
OFFICE_UI = "sw/uiconfig/swriter/ui/notebookbar_office.ui"
ID_IN_LINE = re.compile(r"@id='([^']+)'")


class WriterOfficeUiTest(unittest.TestCase):

    def setUp(self):
        self.office = WRITER.office.read_text(encoding="utf-8")

    def test_the_office_ui_is_stock_plus_tab_operations_plus_every_generated_page(self):
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_regenerating_the_office_ui_changes_nothing(self):
        tabs = json.loads(WRITER.tabs.read_text(encoding="utf-8"))
        self.assertEqual(self.office, g.regenerate_all(self.office, tabs, office.page_layouts("writer")))

    def test_the_home_and_layout_pages_fill_the_tab_page(self):
        # upstream centers them (notebookbar.ui "Home Tab", "Layout Tab"), which would put their
        # captions on another baseline than the other tabs'; Calc did the same for phbLayout
        root = ET.fromstring(self.office)
        for wid in ("Home Tab", "Layout Tab"):
            valign = [p.text for p in root.find(f".//object[@id='{wid}']").findall("property[@name='valign']")]
            self.assertEqual(["fill"], valign, wid)

    def test_the_app_table_names_the_writer_files(self):
        self.assertEqual(office.ROOT / STOCK_UI, WRITER.upstream)
        self.assertEqual(office.ROOT / OFFICE_UI, WRITER.office)
        self.assertEqual(office.ROOT / "solenv/sanitizers/ui/modules/swriter.suppr", WRITER.suppr)
        self.assertEqual(office.ROOT / "solenv/sanitizers/ui/modules/swriter.false", WRITER.false)
        self.assertEqual(office.UI_DIR / "writer_tabs.json", WRITER.tabs)

    def test_the_office_ui_is_installed_with_the_other_writer_notebookbars(self):
        makefile = (office.ROOT / "sw/UIConfig_swriter.mk").read_text(encoding="utf-8")
        self.assertIn("\tsw/uiconfig/swriter/ui/notebookbar_office \\\n", makefile)

    def test_every_ui_the_makefile_installs_has_a_file(self):
        # A .ui listed in gb_UIConfig_add_uifiles without its file breaks the build, and one that is
        # dropped must leave the list too.
        makefile = (office.ROOT / "sw/UIConfig_swriter.mk").read_text(encoding="utf-8")
        registered = re.findall(r"^\t(sw/uiconfig/swriter/ui/[\w-]+) \\$", makefile, re.MULTILINE)
        self.assertGreater(len(registered), 100)
        missing = [ui for ui in registered if not (office.ROOT / (ui + ".ui")).is_file()]
        self.assertEqual([], missing)


class WriterSuppressionsTest(unittest.TestCase):
    """swriter.suppr and swriter.false hold an office copy of every stock notebookbar.ui line."""

    def setUp(self):
        self.office = WRITER.office.read_text(encoding="utf-8")
        self.present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office))

    def test_every_stock_line_has_an_office_copy_while_its_widget_is_there(self):
        for path in (WRITER.suppr, WRITER.false):
            with self.subTest(path.name):
                lines = path.read_text(encoding="utf-8").splitlines()
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
        suppr = WRITER.suppr.read_text(encoding="utf-8")
        self.assertEqual(suppr, g.sync_suppr(suppr, OFFICE_UI, self.office))
        false = WRITER.false.read_text(encoding="utf-8")
        self.assertEqual(false, g.sync_false(false, OFFICE_UI, self.office))


class WriterToolingTest(unittest.TestCase):

    def test_writer_labels_come_from_writer_commands_then_generic(self):
        xcu = ('<?xml version="1.0" encoding="UTF-8"?>\n<oor:component-data '
               'xmlns:oor="http://openoffice.org/2001/registry" oor:name="%s" oor:package="x">'
               '<node oor:name="UserInterface"><node oor:name="Commands">%s</node></node></oor:component-data>')
        node = '<node oor:name="%s" oor:op="replace"><prop oor:name="Label"><value>%s</value></prop></node>'
        with tempfile.TemporaryDirectory() as tmp:
            for name, nodes in (("CalcCommands", ((".uno:Both", "Calc"), (".uno:CalcOnly", "Calc only"))),
                                ("WriterCommands", ((".uno:Both", "Writer"), (".uno:WriterOnly", "Writer only"))),
                                ("GenericCommands", ((".uno:Both", "Generic"), (".uno:GenericOnly", "Generic only")))):
                body = "".join(node % pair for pair in nodes)
                (Path(tmp) / (name + ".xcu")).write_text(xcu % (name, body), encoding="utf-8")
            labels = commands.commands_xcu(tmp, app="writer")
        self.assertEqual("Writer", labels[".uno:Both"])
        self.assertEqual("Writer only", labels[".uno:WriterOnly"])
        self.assertEqual("Generic only", labels[".uno:GenericOnly"])
        self.assertNotIn(".uno:CalcOnly", labels)

    def test_the_real_labels_differ_per_app(self):
        self.assertEqual("Email as ~Microsoft Word...", commands.commands_xcu(app="writer")[".uno:SendMailDocAsMS"])
        self.assertEqual("Email as ~Microsoft Excel...", commands.commands_xcu()[".uno:SendMailDocAsMS"])

    def test_each_app_has_its_own_placeholder_registry(self):
        self.assertEqual(placeholders.REGISTRY, placeholders.registry("calc"))
        self.assertEqual(Path(placeholders.__file__).with_name("placeholders_writer.json"),
                         placeholders.registry("writer"))


if __name__ == "__main__":
    unittest.main()

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_home.json"
DATA_LAYOUT = ROOT / "product/ui/calc_data.json"
UPSTREAM = ROOT / "sc/uiconfig/scalc/ui/notebookbar.ui"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
CONTROLLER_XCU = ROOT / "officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu"
OOR = "{http://openoffice.org/2001/registry}"
SECTIONS = ["Undo", "Clipboard", "Font", "Alignment", "Number", "Styles", "Cells", "Editing"]


class CalcHomeUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))

    def test_sections_follow_annex_1(self):
        self.assertEqual(SECTIONS, [s["name"] for s in self.layout["sections"]])

    def test_office_ui_is_upstream_plus_home_layout(self):
        # Only the Home page may differ from upstream notebookbar.ui; this also
        # proves the file can be regenerated after re-copying a newer upstream.
        # (the Data page is generated too; test_calc_data_ui checks it)
        expected = UPSTREAM.read_text(encoding="utf-8")
        for layout in (self.layout, json.loads(DATA_LAYOUT.read_text(encoding="utf-8"))):
            expected = g.splice(expected, layout, g.emit_page(layout))
        self.assertEqual(expected, OFFICE.read_text(encoding="utf-8"))

    def test_no_italic_captions_on_home(self):
        text = OFFICE.read_text(encoding="utf-8")
        page = text.split("<!-- product:Home-begin -->")[1].split("<!-- product:Home-end -->")[0]
        self.assertNotIn('name="style" value="italic"', page)

    def test_merge_center_is_an_instant_split_button(self):
        # The body runs .uno:HomeMergeCenter; only the arrow opens the menu.
        items = [i for s in self.layout["sections"] for c in s["columns"] for b in c
                 for i in b["items"] if i["cmd"] == "HomeMergeCenter"]
        self.assertEqual(1, len(items))
        self.assertEqual("split", items[0]["kind"])
        page = OFFICE.read_text(encoding="utf-8").split("<!-- product:Home-begin -->")[1]
        self.assertIn(".uno:HomeMergeCenter", page)
        self.assertNotIn(".uno:HomeMergeMenu", page)
        node = self.controller_node("HomeMergeMenuControl")
        self.assertEqual(".uno:HomeMergeCenter", node["Command"])
        self.assertEqual("com.sun.star.comp.framework.GenericPopupToolbarController", node["Controller"])
        self.assertEqual(".uno:HomeMergeMenu", node["Value"])

    def test_no_controller_on_toggle_merge_cells(self):
        text = CONTROLLER_XCU.read_text(encoding="utf-8")
        self.assertNotIn("<value>.uno:ToggleMergeCells</value>", text)

    def controller_node(self, name):
        for node in ET.parse(CONTROLLER_XCU).iter("node"):
            if node.get(OOR + "name") == name:
                return {p.get(OOR + "name"): p.findtext("value") for p in node.findall("prop")}
        self.fail(name + " not found")


if __name__ == "__main__":
    unittest.main()

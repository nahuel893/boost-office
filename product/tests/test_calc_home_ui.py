# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import office
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_home.json"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
CONTROLLER_XCU = ROOT / "officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu"
OOR = "{http://openoffice.org/2001/registry}"
SECTIONS = ["Undo", "Clipboard", "Font", "Alignment", "Number", "Styles", "Cells", "Editing"]


# Excel's label per item where it differs from LibreOffice's (T9w: the ribbon shows it). Source: the Excel
# label in product/docs/design/calc-home-tab-layout.txt (its button map, matched against Excel 365)
EXCEL_LABELS = {".uno:FormatPaintbrush": "Format Painter", ".uno:ConditionalFormatMenu": "Conditional Formatting",
    ".uno:AutoFormat": "Format as Table", ".uno:AutoSum": "AutoSum"}


class CalcHomeUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))

    def test_excels_label_is_in_office_label_where_it_differs_from_libreoffices(self):
        # T9w: the ribbon shows Excel's label (gen_ribbon turns office_label into the button's label);
        # menus, help and tooltips keep LibreOffice's. Icon-only buttons and placeholders have none.
        got = {g.item_url(i): i["office_label"] for s in self.layout["sections"] for b in g.boxes_of(s)
               for i in b["items"] if "office_label" in i}
        self.assertEqual(EXCEL_LABELS, got)

    def test_sections_follow_annex_1(self):
        self.assertEqual(SECTIONS, [s["name"] for s in self.layout["sections"]])

    def test_office_ui_is_upstream_plus_tabs_and_generated_pages(self):
        # Only the tab operations (calc_tabs.json) and the generated pages may differ from
        # upstream notebookbar.ui; this also proves the file can be regenerated after
        # re-copying a newer upstream. (test_calc_tabs and test_calc_data_ui check the rest)
        self.assertIn("Home", [layout["id_prefix"] for layout in office.page_layouts()])
        self.assertEqual(office.expected_office_ui(), OFFICE.read_text(encoding="utf-8"))

    def test_no_italic_captions_on_home(self):
        text = OFFICE.read_text(encoding="utf-8")
        page = text.split("<!-- product:Home-begin -->")[1].split("<!-- product:Home-end -->")[0]
        self.assertNotIn('name="style" value="italic"', page)

    def test_merge_center_is_an_instant_split_button(self):
        # The body runs .uno:HomeMergeCenter; only the arrow opens the menu.
        items = [i for s in self.layout["sections"] for b in g.boxes_of(s)
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

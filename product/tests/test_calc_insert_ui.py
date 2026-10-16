# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Insert tab: layout vs product/docs/design/calc-insert-tab-layout.txt, labels, menus."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import office, placeholders
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands, tooltips
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_insert.json"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
SUPPR = ROOT / "solenv/sanitizers/ui/modules/scalc.suppr"
UI_DIR = ROOT / "officecfg/registry/data/org/openoffice/Office/UI"
POPUPMENU = ROOT / "sc/uiconfig/scalc/popupmenu"
OOR = "{http://openoffice.org/2001/registry}"
MENU = "{http://openoffice.org/2001/menu}"
CHART = ".uno:InsertChartType?Type:string="
SPARK = ".uno:InsertSparkline?Type:string="

# section -> (caption, [(style, [url, ...]) per toolbox in document order])
DESIGN = {
    "Tables": ("Tables", [("large", [".uno:DataDataPilotRun"]),
                          ("large", [".uno:InsertRecommendedPivotTables"]),
                          ("large", [".uno:InsertCalcTable"])]),
    "Illustrations": ("Illustrations", [
        ("small-label", [".uno:InsertPicturesMenu"]), ("small-label", [".uno:InsertShapesMenu"]),
        ("small-label", [".uno:Gallery"]), ("small", [".uno:Insert3DModels"]),
        ("small", [".uno:InsertSmartArt"]), ("small", [".uno:InsertScreenshot"])]),
    "Controls": ("Controls", [("large", [".uno:InsertCellCheckbox"])]),
    "Charts": ("Charts", [
        ("large", [".uno:InsertObjectChart"])]
        + [("small", [CHART + v]) for v in ("columnbar", "linearea", "piedoughnut", "hierarchy",
                                            "statistic", "scatterbubble", "waterfall", "combo")]
        + [("large", [CHART + "map"]), ("large", [".uno:InsertPivotChart"])]),
    # fit ladder F1/F2 of the design (1920 px): Filters and Sparklines are one column of small labelled buttons
    "Sparklines": ("Sparklines", [("small-label", [SPARK + v]) for v in ("line", "column", "stacked")]),
    "Filters": ("Filters", [("small-label", [".uno:InsertSlicer"]), ("small-label", [".uno:InsertTimeline"])]),
    "Links": ("Links", [("large", [".uno:HyperlinkDialog"])]),
    "Comments": ("Comments", [("large", [".uno:InsertAnnotation"])]),
    "Text": ("Text", [("large", [u]) for u in (".uno:DrawText", ".uno:EditHeaderAndFooter",
                                              ".uno:FontworkGalleryFloater",
                                              ".uno:InsertSignatureLine", ".uno:InsertObject")]),
    "Symbols": ("Symbols", [("large", [".uno:InsertObjectStarMath"]), ("large", [".uno:CharmapControl"])]),
}
# charts: column 2 holds three chart types, column 3 three, column 4 two (3 + 3 + 2)
CHART_COLUMNS = [1, 3, 3, 2, 1, 1]
MENUS = {  # command: (label, popup resource, popup items in order, "submenu" -> its items)
    "InsertPicturesMenu": ("Pictures", "insert_pictures", [".uno:InsertPictureInCell", ".uno:InsertGraphic"]),
    "InsertShapesMenu": ("Shapes", "insert_shapes", [
        ".uno:ShapesLineMenu", ".uno:BasicShapes", ".uno:ArrowShapes", ".uno:FlowChartShapes",
        ".uno:StarShapes", ".uno:CalloutShapes", ".uno:SymbolShapes", ".uno:ConnectorToolbox"]),
}
LINE_MENU = [".uno:Line", ".uno:Freeline_Unfilled", ".uno:Freeline", ".uno:Bezier_Unfilled",
             ".uno:BezierFill", ".uno:Polygon_Unfilled", ".uno:Polygon_Diagonal_Unfilled",
             ".uno:Polygon_Diagonal"]
SPARK_LABELS = {SPARK + "line": "Line", SPARK + "column": "Column", SPARK + "stacked": "Win/Loss"}
INSERT_PLACEHOLDERS = {url: label for url, label in placeholders.labels_by_url().items()
                       if url.startswith(".uno:Insert")}


class CalcInsertUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = OFFICE.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))  # the columns' toolboxes, then the footer

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("phbInsert", self.layout["page"])
        self.assertEqual("Insert", self.layout["id_prefix"])
        self.assertEqual("TabbedCalc", self.layout["context"])
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        for section in self.layout["sections"]:
            self.assertEqual(DESIGN[section["name"]][0], section["caption"])
            self.assertEqual(3, section["rows"], section["name"])

    def test_every_control_is_there_in_order_with_its_size(self):
        for section in self.layout["sections"]:
            got = [(b["style"], [g.item_url(i) for i in b["items"]]) for b in self.boxes(section)]
            self.assertEqual(DESIGN[section["name"]][1], got, section["name"])

    def test_chart_types_are_a_three_column_icon_grid(self):
        charts = next(s for s in self.layout["sections"] if s["name"] == "Charts")
        self.assertEqual(CHART_COLUMNS, [len(c) for c in charts["columns"]])

    def test_pictures_and_shapes_are_dropdowns_the_rest_are_plain_buttons(self):
        for item in self.items():
            expected = "split" if item["cmd"] in ("InsertPicturesMenu", "InsertShapesMenu") else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_url_variants_carry_a_short_id_and_the_url_as_action(self):
        variants = [i for i in self.items() if "action" in i]
        self.assertEqual(9 + 3, len(variants))
        for item in variants:
            self.assertRegex(item["cmd"], r"^[A-Za-z0-9]+$")
            self.assertNotIn("?", item["cmd"])
        self.assertEqual(len(variants), len({i["cmd"] for i in variants}))

    def test_the_old_insert_page_and_its_overflow_menu_are_gone(self):
        self.assertIn("Menu Insert", self.layout["remove_objects"])
        for old in ('id="Menu Insert"', 'id="Insert-Menu"', 'Insert-InsertButton:Menu Insert',
                    'id="MenuInsert-'):
            self.assertNotIn(old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Insert-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Insert-end -->"))

    def test_office_ui_is_upstream_plus_tabs_and_every_generated_page(self):
        self.assertIn("Insert", {layout["id_prefix"] for layout in office.page_layouts()})
        self.assertEqual(office.expected_office_ui(), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        # risk R12: ids must be unique in the whole file, not only inside the page
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual([], dupes)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu()
        for item in self.items():
            self.assertIn(g.item_url(item), labels, item["cmd"])

    def test_every_new_command_has_the_image_flag(self):
        flagged = flagged_commands()
        for item in self.items():
            if "icon" not in item:
                self.assertIn(g.item_url(item), flagged, item["cmd"] + " is left out of the image list")
        for cmd in INSERT_PLACEHOLDERS:
            self.assertIn(cmd, flagged, cmd)

    def test_placeholder_labels_and_tooltips_follow_excel(self):
        labels, tips = commands_xcu(), tooltips()
        expected = sum(len(placeholders.urls(e)) for e in placeholders.load() if 389 <= e["offset"] <= 398)
        self.assertEqual(expected, len(INSERT_PLACEHOLDERS))  # one per plain slot and per chart-type variant
        for url, label in INSERT_PLACEHOLDERS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_place_in_cell_is_a_labelled_placeholder_and_sits_before_image_in_the_pictures_menu(self):
        self.assertIn(".uno:InsertPictureInCell", INSERT_PLACEHOLDERS)
        self.assertEqual(INSERT_PLACEHOLDERS[".uno:InsertPictureInCell"], commands_xcu()[".uno:InsertPictureInCell"])
        self.assertLess(MENUS["InsertPicturesMenu"][2].index(".uno:InsertPictureInCell"),
                        MENUS["InsertPicturesMenu"][2].index(".uno:InsertGraphic"))

    def test_the_registry_labels_every_insert_slot_and_variant(self):
        for entry in placeholders.load():
            if entry["offset"] not in range(389, 399):
                continue
            if "variants" in entry:
                self.assertEqual(entry["variants"], list(entry["variant_labels"]), entry["command"])
            else:
                self.assertIn("label", entry, entry["command"])

    def test_every_insert_placeholder_is_on_the_page_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes().values()}
        used = {g.item_url(i) for i in self.items()}
        for url in INSERT_PLACEHOLDERS:
            if url != ".uno:InsertPictureInCell":  # a menu item, not a button
                self.assertIn(url, used, url)
            self.assertNotIn(url, controlled, url)

    def test_sparkline_variants_have_labels(self):
        labels = commands_xcu()
        for url, label in SPARK_LABELS.items():
            self.assertEqual(label, labels[url], url)

    def test_dropdown_commands_have_labels_and_popup_and_toolbar_controllers(self):
        labels, nodes = commands_xcu(), controller_nodes()
        for cmd, (label, resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd]
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in ours}
            self.assertEqual({"ResourceMenuController", "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertEqual(resource, kinds["ResourceMenuController"]["Value"])
            for kind in kinds.values():
                self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", kind["Module"])
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])

    def menu_ids(self, element):
        return [e.get(MENU + "id") for e in element
                if e.tag in (MENU + "menuitem", MENU + "menu")]

    def test_popup_files_exist_are_registered_and_list_the_design_items(self):
        mk = (ROOT / "sc/UIConfig_scalc.mk").read_text(encoding="utf-8")
        for _label, resource, items in MENUS.values():
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("sc/uiconfig/scalc/popupmenu/" + resource + " \\", mk)
            self.assertEqual(items, self.menu_ids(ET.parse(path).getroot()), resource)

    def test_the_shapes_line_submenu_lists_its_eight_shapes(self):
        root = ET.parse(POPUPMENU / "insert_shapes.xml").getroot()
        line = next(m for m in root.iter(MENU + "menu") if m.get(MENU + "id") == ".uno:ShapesLineMenu")
        self.assertEqual(LINE_MENU, self.menu_ids(line.find(MENU + "menupopup")))

    def test_suppr_has_an_entry_for_every_insert_button(self):
        suppr = SUPPR.read_text(encoding="utf-8")
        prefix = "sc/uiconfig/scalc/ui/notebookbar_office.ui:"
        for wid in g.ids_of(self.layout):
            if wid.startswith("btn"):
                self.assertRegex(suppr, re.escape(prefix) + r"//Gtk(Menu)?ToolButton\[@id='"
                                 + re.escape(wid) + r"'\] button-no-label")

    def test_suppr_has_no_entry_for_the_removed_upstream_widgets(self):
        suppr = SUPPR.read_text(encoding="utf-8")
        present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office))
        prefix = "sc/uiconfig/scalc/ui/notebookbar_office.ui:"
        for line in suppr.splitlines():
            match = re.search(r"@id='([^']+)'", line)
            if line.startswith(prefix) and match:
                self.assertIn(match.group(1), present, line)

    def test_regenerating_the_page_changes_nothing(self):
        regenerated = g.splice(self.office, self.layout, g.emit_page(self.layout))
        self.assertEqual(self.office, regenerated)
        suppr = SUPPR.read_text(encoding="utf-8")
        self.assertEqual(suppr, g.sync_suppr(suppr, "sc/uiconfig/scalc/ui/notebookbar_office.ui", regenerated))


if __name__ == "__main__":
    unittest.main()

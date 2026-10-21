# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Writer Insert tab: layout vs product/docs/writer-ribbon-tabs.md section 1 "Insert", the seven
new dropdowns (popup files, controllers, labels), the four placeholders, and the commands that leave
the tab (section 2, "Insert (13)")."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import office, placeholders
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands, tooltips
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
WRITER = office.app("writer")
LAYOUT = ROOT / "product/ui/writer_insert.json"
OFFICE_REL = "sw/uiconfig/swriter/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sw/uiconfig/swriter/popupmenu"
TOOLBARS = ROOT / "sw/uiconfig/swriter/toolbar"
MENUBAR = ROOT / "sw/uiconfig/swriter/menubar/menubar.xml"
MENU = "{http://openoffice.org/2001/menu}"
TEXT_MODULE = "com.sun.star.text.TextDocument"
SEP = "-"  # a separator in a menu item list
FRAMEWORK = "com.sun.star.comp.framework."


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Insert".
# Size: L = large, S = small-label. The Media section (Online Videos) is cloud and is omitted.
DESIGN = {
    "Pages": ("Pages", 3, [("small-label", uno("TitlePageDialog")), ("small-label", uno("InsertBlankPage")),
                           ("small-label", uno("InsertPagebreak"))]),
    "Tables": ("Tables", 3, [("large", uno("InsertTable"))]),
    "Illustrations": ("Illustrations", 3, [
        ("large", uno("InsertGraphic")),
        ("small-label", uno("InsertShapesMenu")), ("small-label", uno("Gallery")),
        ("small-label", uno("Insert3DModels")), ("small-label", uno("InsertSmartArt")),
        ("small-label", uno("InsertObjectChart")), ("small-label", uno("InsertScreenshot"))]),
    "Links": ("Links", 3, [("small-label", uno("HyperlinkDialog")), ("small-label", uno("InsertBookmark")),
                           ("small-label", uno("InsertReferenceField"))]),
    "Comments": ("Comments", 3, [("large", uno("InsertAnnotation"))]),
    "HeaderFooter": ("Header & Footer", 3, [
        ("small-label", uno("InsertHeaderMenu")), ("small-label", uno("InsertFooterMenu")),
        ("small-label", uno("InsertPageNumberMenu"))]),
    "Text": ("Text", 3, [
        ("large", uno("InsertTextBoxMenu")),
        ("small-label", uno("InsertQuickPartsMenu")), ("small-label", uno("FontworkGalleryFloater")),
        ("small-label", uno("FormatDropcap")),
        ("small-label", uno("InsertSignatureLine")), ("small-label", uno("InsertDateField")),
        ("small-label", uno("InsertObjectMenu"))]),
    "Symbols": ("Symbols", 3, [("small-label", uno("InsertObjectStarMath")), ("small-label", uno("CharmapControl"))]),
}
SHAPES = {"Pages": [3], "Tables": [1], "Illustrations": [1, 3, 3], "Links": [3], "Comments": [1],
          "HeaderFooter": [3], "Text": [1, 3, 3], "Symbols": [2]}
# Word's label per item (design decision 29: it stays in "office_label" until T9 is decided)
WORD_LABELS = {
    "TitlePageDialog": "Cover Page", "InsertBlankPage": "Blank Page", "InsertPagebreak": "Page Break",
    "InsertTable": "Table", "InsertGraphic": "Pictures", "InsertShapesMenu": "Shapes", "Gallery": "Icons",
    "Insert3DModels": "3D Models", "InsertSmartArt": "SmartArt", "InsertObjectChart": "Chart",
    "InsertScreenshot": "Screenshot", "HyperlinkDialog": "Link", "InsertBookmark": "Bookmark",
    "InsertReferenceField": "Cross-reference", "InsertAnnotation": "Comment", "InsertHeaderMenu": "Header",
    "InsertFooterMenu": "Footer", "InsertPageNumberMenu": "Page Number", "InsertTextBoxMenu": "Text Box",
    "InsertQuickPartsMenu": "Quick Parts", "FontworkGalleryFloater": "WordArt", "FormatDropcap": "Drop Cap",
    "InsertSignatureLine": "Signature Line", "InsertDateField": "Date & Time", "InsertObjectMenu": "Object",
    "InsertObjectStarMath": "Equation", "CharmapControl": "Symbol"}
# Word's dropdowns: the seven new menus, Table (grid popup) and Symbol (recent characters popup)
SPLITS = {"InsertTable", "CharmapControl", "InsertShapesMenu", "InsertHeaderMenu", "InsertFooterMenu",
          "InsertPageNumberMenu", "InsertTextBoxMenu", "InsertQuickPartsMenu", "InsertObjectMenu"}

# command -> (label, controller, popup resource or None, popup items in order); design section 1 "Menu contents"
MENUS = {
    "InsertShapesMenu": ("Shapes", "ResourceMenuController", "insert_shapes",
                         uno("ShapesLineMenu", "BasicShapes", "ArrowShapes", "FlowChartShapes", "StarShapes",
                             "CalloutShapes", "SymbolShapes", "ConnectorToolbox")),
    "InsertHeaderMenu": ("Header", "ResourceMenuController", "insert_header", uno("InsertPageHeader")),
    "InsertFooterMenu": ("Footer", "ResourceMenuController", "insert_footer", uno("InsertPageFooter")),
    "InsertPageNumberMenu": ("Page Number", "ResourceMenuController", "insert_pagenumber",
                             uno("PageNumberWizard", "InsertPageNumberField", "InsertPageCountField")),
    "InsertTextBoxMenu": ("Text Box", "ResourceMenuController", "insert_textbox", uno("DrawText", "VerticalText")),
    "InsertQuickPartsMenu": ("Quick Parts", "ResourceMenuController", "insert_quickparts",
                             uno("EditGlossary") + [SEP] + uno("InsertTitleField", "InsertTopicField",
                                                               "InsertAuthorField") + [SEP]
                             + uno("InsertField")),
    "InsertObjectMenu": ("Object", "ResourceMenuController", "insert_object", uno("InsertObject", "InsertDoc")),
}
# Header and Footer are plain dropdowns like the rest: the popup file holds the stock page-style command, which
# the registered HeaderMenuController/FooterMenuController turns into a submenu of the page styles.
LINE_MENU = uno("Line", "Freeline_Unfilled", "Freeline", "Bezier_Unfilled", "BezierFill", "Polygon_Unfilled",
                "Polygon_Diagonal_Unfilled", "Polygon_Diagonal")
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, Insert rows)
    ".uno:InsertBlankPage": "Blank Page", ".uno:Insert3DModels": "3D Models", ".uno:InsertSmartArt": "SmartArt",
    ".uno:InsertScreenshot": "Screenshot"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("writer"))
INSERT_SLOTS = [2, 3, 4, 5]

# design section 2 "Insert (13)": command -> (class, menu-bar id that keeps it reachable).
# a: the same command is in the menu bar; b: only an equivalent entry is; c: neither (see CLASS_C).
LEFT_THE_TAB = {
    "InsertAVMedia": ("a", "InsertAVMedia"), "InsertFieldCtrl": ("a", "InsertFieldCtrl"),
    "TwainSelect": ("a", "TwainSelect"), "InsertQrCode": ("a", "InsertQrCode"),
    "InsertFormula": ("a", "InsertFormula"), "InsertFrameInteract": ("a", "InsertFrameInteract"),
    "BasicShapes.rectangle": ("b", "BasicShapes"), "BasicShapes.ellipse": ("b", "BasicShapes"),
    "DrawCaption": ("b", "CalloutShapes"), "LineToolbox": ("b", "ShapesLineMenu"),
    "StyleApply?Style:string=Horizontal Line": ("b", "HorizontalLine"),
    "ArrowsToolbox": ("c", "AvailableToolbars"), "InsertDraw": ("c", "AvailableToolbars"),
}
# class c, controller ruling (2026-10-20, answer 2): no menu-bar entry; the toolbar that holds the command
# stays reachable through View > Toolbars (menubar.xml, ".uno:AvailableToolbars")
CLASS_C = {"ArrowsToolbox": ["drawbar.xml"],
           "InsertDraw": ["standardbar.xml", "singlemode-text.xml", "singlemode-table.xml"]}


def all_controller_nodes():
    """Every Controller.xcu node with a Command; unlike controller_nodes() it keeps nodes that share a name."""
    root = ET.parse(ROOT / "officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu").getroot()
    oor = "{http://openoffice.org/2001/registry}"
    out = []
    for node in root.iter("node"):
        props = {p.get(oor + "name"): p.findtext("value") for p in node.findall("prop")}
        if "Command" in props:
            out.append(props)
    return out


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class WriterInsertUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = WRITER.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Insert Tab", self.layout["page"])
        self.assertEqual("Insert", self.layout["id_prefix"])
        self.assertEqual("TabbedWriter", self.layout["context"])
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        for section in self.layout["sections"]:
            caption, rows, _ = DESIGN[section["name"]]
            self.assertEqual(caption, section["caption"])
            self.assertEqual(rows, section["rows"], section["name"])

    def test_every_control_is_there_in_order_with_its_size(self):
        for section in self.layout["sections"]:
            got = [(b["style"], [g.item_url(i) for i in b["items"]]) for b in self.boxes(section)]
            self.assertEqual(DESIGN[section["name"]][2], got, section["name"])
        self.assertEqual(27, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_dropdowns_are_split_the_rest_are_plain_buttons(self):
        for item in self.items():
            expected = "split" if item["cmd"] in SPLITS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_words_label_in_office_label(self):
        # design decision 29: nothing is renamed now; either T9 option can be applied later
        self.assertEqual(WORD_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_the_omitted_media_group_and_cloud_controls_are_absent(self):
        # design section 1: Media > Online Videos is cloud; Reuse Files, Get Add-ins, Loop and Barcode too
        self.assertNotIn("Media", [s["name"] for s in self.layout["sections"]])
        for cmd in ("InsertAVMedia", "InsertQrCode"):
            self.assertNotIn(cmd, {i["cmd"] for i in self.items()})

    def test_the_old_insert_page_and_its_overflow_menu_are_gone(self):
        self.assertIn("Menu Insert", self.layout["remove_objects"])
        for old in ('id="Menu Insert"', "Insert-InsertButton:Menu Insert", 'id="Insert-Menu"', 'id="MenuInsert-'):
            self.assertNotIn(old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Insert-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Insert-end -->"))
        self.assertIn('id="Insert Tab"', self.office)  # the page itself stays, with the tab label

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Insert", {layout["id_prefix"] for layout in office.page_layouts("writer")})
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(13, len(LEFT_THE_TAB))
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_url(i) for i in self.items()} | {g.item_command(i) for i in self.items()}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)
            own = 'menu:id=".uno:%s"' % name
            if kind == "a":
                self.assertEqual(name, menu_id)
            else:
                self.assertNotEqual(name, menu_id)
                self.assertNotIn(own, menubar, name + " is not in the menu bar: class " + kind)
        self.assertEqual({"a": 6, "b": 5, "c": 2}, {k: sum(1 for v in LEFT_THE_TAB.values() if v[0] == k)
                                                    for k in "abc"})

    def test_the_two_commands_without_a_menu_bar_entry_stay_in_their_toolbars(self):
        # class c: the Drawing and Standard toolbars hold them, and View > Toolbars shows those
        self.assertEqual({n for n, v in LEFT_THE_TAB.items() if v[0] == "c"}, set(CLASS_C))
        for name, files in CLASS_C.items():
            for file in files:
                self.assertIn('xlink:href=".uno:%s"' % name, (TOOLBARS / file).read_text(encoding="utf-8"), file)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="writer")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_new_menus_and_placeholders_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="writer"), tooltips(app="writer")
        for cmd, (label, _controller, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_new_commands_have_the_image_flag(self):
        flagged = flagged_commands(app="writer")
        for cmd in MENUS:
            self.assertIn(".uno:" + cmd, flagged, cmd)
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_the_menu_items_are_known_commands(self):
        labels = commands_xcu(app="writer")
        for _label, _controller, _resource, items in MENUS.values():
            for url in items or []:
                if url != SEP:
                    self.assertIn(url, labels, url)
        for url in LINE_MENU:
            self.assertIn(url, labels, url)

    def test_the_registry_labels_every_insert_slot(self):
        registry = placeholders.registry("writer")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items()
                                              if u.startswith(".uno:Insert")})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        for offset in INSERT_SLOTS:
            self.assertTrue(entries[offset]["command"].startswith("Insert"))
            self.assertIn(".uno:" + entries[offset]["command"], PLACEHOLDER_LABELS)

    def test_every_insert_placeholder_is_on_the_page_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="writer").values()}
        on_page = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, on_page, url)
            self.assertNotIn(url, controlled, url)

    def test_each_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        nodes = controller_nodes(app="writer")
        self.assertEqual(7, len(MENUS))
        for cmd, (_label, popup, resource, _items) in MENUS.items():  # popup: the menu controller class
            # Calc owns InsertShapesMenu for its own module: only the Writer nodes count here
            ours = [(k, v) for k, v in nodes.items() if v["Command"] == ".uno:" + cmd and v.get("Module") == TEXT_MODULE]
            kinds = {v["Controller"].rsplit(".", 1)[1]: (k, v) for k, v in ours}
            toolbar = kinds["GenericPopupToolbarController"][1]
            self.assertEqual({popup, "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertNotIn("Value", toolbar)
            self.assertEqual(resource, kinds[popup][1]["Value"])
            self.assertTrue(kinds[popup][1]["Controller"].startswith(FRAMEWORK))

    def test_calcs_shapes_nodes_are_untouched_and_the_writer_ones_have_their_own_names(self):
        nodes = controller_nodes(app="writer")
        calc = {k for k, v in nodes.items() if v["Command"] == ".uno:InsertShapesMenu"
                and v.get("Module") == "com.sun.star.sheet.SpreadsheetDocument"}
        self.assertEqual({"InsertShapesMenuPopup", "InsertShapesMenuControl"}, calc)
        ours = {k for k, v in nodes.items() if v["Command"] == ".uno:InsertShapesMenu"
                and v.get("Module") == TEXT_MODULE}
        self.assertEqual({"InsertShapesMenuWriterPopup", "InsertShapesMenuWriterControl"}, ours)

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        # the seven dropdown commands are new: only the Insert page and the controller nodes name them
        toolbars = list(TOOLBARS.glob("*.xml"))
        uis = [p for p in (ROOT / "sw/uiconfig/swriter/ui").glob("notebookbar*.ui") if p != WRITER.office]
        self.assertTrue(toolbars and uis)
        for cmd in MENUS:
            for path in toolbars + uis:
                self.assertNotIn(".uno:" + cmd, path.read_text(encoding="utf-8"), "%s in %s" % (cmd, path.name))

    def menu_ids(self, element):
        out = []
        for e in element:
            if e.tag in (MENU + "menuitem", MENU + "menu"):
                out.append(e.get(MENU + "id"))
            elif e.tag == MENU + "menuseparator":
                out.append(SEP)
        return out

    def test_popup_files_exist_are_registered_and_list_the_design_items(self):
        mk = read("sw/UIConfig_swriter.mk")
        files = [(r, i) for _l, _c, r, i in MENUS.values() if r]
        self.assertEqual(7, len(files))
        for resource, items in files:
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("\tsw/uiconfig/swriter/popupmenu/" + resource + " \\\n", mk)
            self.assertEqual(items, self.menu_ids(ET.parse(path).getroot()), resource)

    def test_header_and_footer_popups_hold_only_the_page_style_item_and_the_buttons_are_not_split(self):
        nodes = controller_nodes(app="writer")
        for cmd, item in (("InsertHeaderMenu", ".uno:InsertPageHeader"), ("InsertFooterMenu", ".uno:InsertPageFooter")):
            self.assertEqual([item], MENUS[cmd][3])
            toolbar = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd
                       and v["Controller"].endswith("GenericPopupToolbarController")]
            self.assertEqual(1, len(toolbar), cmd)
            self.assertNotIn("Value", toolbar[0], cmd)

    def test_the_shapes_line_submenu_lists_its_eight_shapes(self):
        root = ET.parse(POPUPMENU / "insert_shapes.xml").getroot()
        line = next(e for e in root if e.get(MENU + "id") == ".uno:ShapesLineMenu")
        self.assertEqual(LINE_MENU, self.menu_ids(line.find(MENU + "menupopup")))

    def test_suppr_has_an_entry_for_every_button(self):
        suppr = WRITER.suppr.read_text(encoding="utf-8")
        for wid in g.ids_of(self.layout):
            if wid.startswith("btn"):
                self.assertRegex(suppr, re.escape(OFFICE_REL + ":") + r"//Gtk(Menu)?ToolButton\[@id='"
                                 + re.escape(wid) + r"'\] button-no-label")

    def test_regenerating_the_page_changes_nothing(self):
        regenerated = g.splice(self.office, self.layout, g.emit_page(self.layout))
        self.assertEqual(self.office, regenerated)
        suppr = WRITER.suppr.read_text(encoding="utf-8")
        self.assertEqual(suppr, g.sync_suppr(suppr, OFFICE_REL, regenerated))
        false = WRITER.false.read_text(encoding="utf-8")
        self.assertEqual(false, g.sync_false(false, OFFICE_REL, regenerated))


if __name__ == "__main__":
    unittest.main()

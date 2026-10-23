# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Impress Insert tab (Slides, Tables, Images, Illustrations, Links, Comments, Text, Symbols, Media):
layout vs product/docs/impress-ribbon-tabs.md section 1 "Insert", the two new dropdowns (popup files,
controllers, labels), the Insert placeholders, and the commands that leave the tab (section 2,
"Insert (9)")."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import office, placeholders
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands, tooltips
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
IMPRESS = office.app("impress")
LAYOUT = ROOT / "product/ui/impress_insert.json"
OFFICE_REL = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sd/uiconfig/simpress/popupmenu"
TOOLBARS = ROOT / "sd/uiconfig/simpress/toolbar"
MENUBAR = ROOT / "sd/uiconfig/simpress/menubar/menubar.xml"
MENU = "{http://openoffice.org/2001/menu}"
PRESENTATION_MODULE = "com.sun.star.presentation.PresentationDocument"
SEP = "-"  # a separator in a menu item list
ZOOM = ".uno:InsertZoom?Type:string="
AVMEDIA = ".uno:InsertAVMedia"


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Insert".
# Size: L = large, S = small-label, I = small (icon). Cameo, Power BI and Forms are cloud and omitted.
DESIGN = {
    "Slides": ("Slides", 3, [("large", uno("InsertPage")), ("large", uno("ImportSlideFromFile"))]),
    "Tables": ("Tables", 3, [("large", uno("InsertTable"))]),
    "Images": ("Images", 3, [("large", uno("InsertGraphic")), ("small-label", uno("InsertScreenshot")),
                             ("small-label", uno("PhotoAlbumDialog"))]),
    "Illustrations": ("Illustrations", 3, [("large", uno("InsertShapesMenu")), ("large", uno("Gallery")),
                                           ("small-label", uno("Insert3DModels")),
                                           ("small-label", uno("InsertSmartArt")),
                                           ("small-label", uno("InsertObjectChart"))]),
    "Links": ("Links", 3, [("large", uno("InsertZoomMenu")), ("large", uno("HyperlinkDialog")),
                           ("large", uno("AnimationEffects"))]),
    "Comments": ("Comments", 3, [("large", uno("InsertAnnotation"))]),
    "Text": ("Text", 3, [("large", uno("InsertTextBoxMenu")), ("large", uno("HeaderAndFooter")),
                         ("large", uno("FontworkGalleryFloater")), ("small", uno("InsertDateFieldVar")),
                         ("small", uno("InsertSlideField")), ("small", uno("InsertObject"))]),
    "Symbols": ("Symbols", 3, [("large", uno("InsertMath")), ("large", uno("CharmapControl"))]),
    # decision 16: Video and Audio share .uno:InsertAVMedia and get distinct widget commands
    "Media": ("Media", 3, [("large", [AVMEDIA]), ("large", [AVMEDIA]), ("large", uno("InsertScreenRecording"))]),
}
SHAPES = {"Slides": [1, 1], "Tables": [1], "Images": [1, 2], "Illustrations": [1, 1, 3], "Links": [1, 1, 1],
          "Comments": [1], "Text": [1, 1, 1, 3], "Symbols": [1, 1], "Media": [1, 1, 1]}
# PowerPoint's label per item (T9w); the layout item's "cmd" (the widget command) is the key
POWERPOINT_LABELS = {
    "InsertPage": "New Slide", "ImportSlideFromFile": "Reuse Slides", "InsertTable": "Table",
    "InsertGraphic": "Pictures", "InsertScreenshot": "Screenshot", "PhotoAlbumDialog": "Photo Album",
    "InsertShapesMenu": "Shapes", "Gallery": "Icons", "Insert3DModels": "3D Models",
    "InsertSmartArt": "SmartArt", "InsertObjectChart": "Chart", "InsertZoomMenu": "Zoom",
    "HyperlinkDialog": "Link", "AnimationEffects": "Action", "InsertAnnotation": "Comment",
    "InsertTextBoxMenu": "Text Box", "HeaderAndFooter": "Header & Footer",
    "FontworkGalleryFloater": "WordArt", "InsertDateFieldVar": "Date & Time", "InsertSlideField": "Slide Number",
    "InsertObject": "Object", "InsertMath": "Equation", "CharmapControl": "Symbol", "InsertVideo": "Video",
    "InsertAudio": "Audio", "InsertScreenRecording": "Screen Recording"}
# PowerPoint's splits and dropdowns that LibreOffice can fill ("split" only means "has an arrow"): New Slide
# (InsertSlideController), Table (grid popup), Symbol (favourites popup) and the three menus. Photo Album,
# Link, Equation, Video and Audio have no menu of their own and are plain buttons (design decision 9); the
# placeholders are plain greyed buttons (decision 20).
SPLITS = {"InsertPage", "InsertTable", "InsertShapesMenu", "InsertZoomMenu", "InsertTextBoxMenu", "CharmapControl"}

# command -> (label, popup resource, popup items in order); design section 1 "Insert"
MENUS = {
    "InsertZoomMenu": ("Zoom", "insert_zoom", uno("SummaryPage") + [ZOOM + "section", ZOOM + "slide"]),
    "InsertTextBoxMenu": ("Text Box", "insert_textbox", uno("Text", "VerticalText")),
    # reused from Home (I2c): same popup file and Controller.xcu nodes, not copied
    "InsertShapesMenu": ("Shapes", "home_shapes", None),
}
NEW_MENUS = ("InsertZoomMenu", "InsertTextBoxMenu")
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, the Insert rows)
    ".uno:InsertScreenshot": "Screenshot", ".uno:Insert3DModels": "3D Models", ".uno:InsertSmartArt": "SmartArt",
    ZOOM + "section": "Section Zoom", ZOOM + "slide": "Slide Zoom",
    ".uno:InsertScreenRecording": "Screen Recording"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("impress"))
INSERT_SLOTS = [5, 6, 7, 8, 9]

# design section 2 "Insert (9)": command -> (class, menu-bar id that keeps it reachable).
# a: the same command is in the menu bar; c: neither, the Fontwork toolbar that holds it is listed in View > Toolbars.
LEFT_THE_TAB = {
    "FontworkShapeType": ("c", "AvailableToolbars"), "FontworkSameLetterHeights": ("c", "AvailableToolbars"),
    "FontworkAlignmentFloater": ("c", "AvailableToolbars"),
    "FontworkCharacterSpacingFloater": ("c", "AvailableToolbars"),
    "AnimationObjects": ("a", "AnimationObjects"), "TwainSelect": ("a", "TwainSelect"),
    "InsertQrCode": ("a", "InsertQrCode"), "CapturePoint": ("a", "CapturePoint"),
    "InsertSlidesField": ("a", "InsertSlidesField"),
}
CLASS_C = {name: ["fontworkobjectbar.xml"] for name, v in LEFT_THE_TAB.items() if v[0] == "c"}
OLD_PAGE_WIDGETS = ["btnInsertInsertSlide", "btnInsertAnimationObjects", "btnInsertTwainSelect",
                    "btnInsertInsertQrCode"]  # stock ids that must be gone


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ImpressInsertUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Insert", self.layout["page"])
        self.assertEqual("Insert", self.layout["id_prefix"])
        self.assertEqual("TabbedImpress", self.layout["context"])
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        for section in self.layout["sections"]:
            caption, rows, _ = DESIGN[section["name"]]
            self.assertEqual(caption, section["caption"])
            self.assertEqual(rows, section["rows"], section["name"])

    def test_every_control_is_there_in_order_with_its_size(self):
        for section in self.layout["sections"]:
            got = [(b["style"], [g.item_url(i) for i in b["items"]]) for b in self.boxes(section)]
            self.assertEqual(DESIGN[section["name"]][2], got, section["name"])
        self.assertEqual(26, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_dropdowns_and_split_buttons_are_split_the_rest_are_plain(self):
        for item in self.items():
            expected = "split" if item["cmd"] in SPLITS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_powerpoints_label_in_office_label(self):
        # T9w: gen_ribbon turns office_label into the button's label; menus, help and tooltips keep LibreOffice's
        self.assertEqual(POWERPOINT_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_video_and_audio_have_distinct_widget_commands_for_one_real_command(self):
        # design decision 16: two items with the same URL on one page get distinct widget commands
        by_cmd = {i["cmd"]: i for i in self.items()}
        self.assertEqual(AVMEDIA, by_cmd["InsertVideo"]["action"])
        self.assertEqual(AVMEDIA, by_cmd["InsertAudio"]["action"])
        for wid in ("btnInsertInsertVideo", "btnInsertInsertAudio"):
            self.assertEqual(1, self.office.count('id="%s"' % wid), wid)
        self.assertEqual(2, len(re.findall(r'<property name="action-name">%s</property>' % re.escape(AVMEDIA),
                                           self.office.split("<!-- product:Insert-begin -->")[1]
                                           .split("<!-- product:Insert-end -->")[0])))

    def test_no_url_variant_item_is_on_the_ribbon(self):
        # the ? variants (Section Zoom, Slide Zoom) live in the Zoom menu only, so no layout item needs an icon
        for item in self.items():
            self.assertNotIn("?", g.item_url(item), item["cmd"])

    def test_the_old_insert_page_and_its_overflow_menu_are_gone(self):
        self.assertIn("Menu Insert", self.layout["remove_objects"])
        for old in ('id="Menu Insert"', "Insert-InsertButton:Menu Insert"):
            self.assertNotIn(old, self.office)
        for old in OLD_PAGE_WIDGETS:
            self.assertNotIn('id="%s"' % old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Insert-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Insert-end -->"))
        self.assertIn('id="Insert"', self.office)  # the page itself stays, with the tab label

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Insert", {layout["id_prefix"] for layout in office.page_layouts("impress")})
        self.assertEqual(office.expected_office_ui("impress"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(9, len(LEFT_THE_TAB))
        self.assertEqual({"a": 5, "c": 4}, {k: sum(1 for v in LEFT_THE_TAB.values() if v[0] == k) for k in "ac"})
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()}
        in_menus = {u for _l, _r, items in MENUS.values() for u in items or []}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertNotIn(".uno:" + name, in_menus, name)
            self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)
            if kind == "a":
                self.assertEqual(name, menu_id)
            else:
                self.assertNotIn('menu:id=".uno:%s"' % name, menubar, name + " is not in the menu bar: class c")

    def test_the_four_fontwork_commands_stay_in_the_fontwork_toolbar(self):
        # class c: the Fontwork toolbar holds them, and View > Toolbars lists that toolbar
        self.assertEqual({n for n, v in LEFT_THE_TAB.items() if v[0] == "c"}, set(CLASS_C))
        for name, files in CLASS_C.items():
            for file in files:
                self.assertIn('xlink:href=".uno:%s"' % name, (TOOLBARS / file).read_text(encoding="utf-8"), file)
        windowstate = read("officecfg/registry/data/org/openoffice/Office/UI/ImpressWindowState.xcu")
        node = windowstate.split('private:resource/toolbar/fontworkobjectbar"')[1].split("</node>")[0]
        self.assertRegex(node, r'(?s)HideFromToolbarMenu".*?<value>false</value>')

    def test_the_stock_insert_page_commands_either_stay_or_are_in_the_leave_list(self):
        # every command of the stock Insert page and its overflow menu stays on the ribbon (this page, a
        # dropdown item, or Home's Drawing section, which keeps the shape tools) or is in the leave list. The
        # stock aliases New Slide and Duplicate Slide act through New Slide's popup.
        stock = ET.parse(ROOT / "sd/uiconfig/simpress/ui/notebookbar.ui").getroot()
        commands = set()
        for wid in ("Insert", "Menu Insert"):
            node = next(o for o in stock.iter("object") if o.get("id") == wid)
            commands |= {p.text for p in node.iter("property") if p.get("name") == "action-name"}
        home = json.loads((ROOT / "product/ui/impress_home.json").read_text(encoding="utf-8"))
        on_tab = {g.item_command(i) for layout in (self.layout, home) for s in layout["sections"]
                  for b in g.boxes_of(s) for i in b["items"]}
        on_tab |= {u for cmd in NEW_MENUS for u in MENUS[cmd][2]}
        left = {".uno:" + name for name in LEFT_THE_TAB}
        aliases = {".uno:InsertSlide": ".uno:InsertPage", ".uno:DuplicateSlide": ".uno:InsertPage"}
        self.assertGreater(len(commands), 30)
        for url in sorted(commands):
            url = aliases.get(url, url)
            self.assertTrue(url in on_tab or url in left, url)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="impress")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_new_menus_and_placeholder_items_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_new_commands_have_the_image_flag(self):
        flagged = flagged_commands(app="impress")
        for cmd in NEW_MENUS:
            self.assertIn(".uno:" + cmd, flagged, cmd)
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_the_menu_items_are_known_commands(self):
        labels = commands_xcu(app="impress")
        for cmd in NEW_MENUS:
            for url in MENUS[cmd][2]:
                self.assertIn(url, labels, url)

    def test_the_registry_labels_every_insert_slot_and_variant(self):
        registry = placeholders.registry("impress")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items() if u.startswith(".uno:Insert")})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        for offset, command in zip(INSERT_SLOTS, ("InsertScreenshot", "Insert3DModels", "InsertSmartArt",
                                                  "InsertZoom", "InsertScreenRecording")):
            self.assertEqual(command, entries[offset]["command"])
        self.assertEqual(["Type:string=section", "Type:string=slide"], entries[8]["variants"])
        self.assertEqual({"Type:string=section": "Section Zoom", "Type:string=slide": "Slide Zoom"},
                         entries[8]["variant_labels"])

    def test_the_placeholder_items_have_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        for url in PLACEHOLDER_LABELS:
            self.assertNotIn(url, controlled, url)

    def impress_nodes(self, command):
        return [v for v in controller_nodes(app="impress").values()
                if v["Command"] == command and v["Module"] == PRESENTATION_MODULE]

    def test_each_new_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        for cmd in NEW_MENUS + ("InsertShapesMenu",):
            resource = MENUS[cmd][1]
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in self.impress_nodes(".uno:" + cmd)}
            self.assertEqual({"ResourceMenuController", "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])
            self.assertEqual(resource, kinds["ResourceMenuController"]["Value"])

    def test_the_shapes_menu_is_reused_not_copied(self):
        text = read("officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu")
        self.assertEqual(1, text.count('<node oor:name="InsertShapesMenuImpressPopup" oor:op="replace">'))
        self.assertEqual(1, text.count('<node oor:name="InsertShapesMenuImpressControl" oor:op="replace">'))
        self.assertFalse(list(POPUPMENU.glob("insert_shapes*")))
        mk = read("sd/UIConfig_simpress.mk")
        self.assertEqual(1, mk.count("popupmenu/home_shapes "))

    def test_impress_nodes_carry_the_impress_suffix(self):
        text = read("officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu")
        for cmd in NEW_MENUS:
            self.assertEqual(1, text.count('<node oor:name="%sImpressPopup" oor:op="replace">' % cmd), cmd)
            self.assertEqual(1, text.count('<node oor:name="%sImpressControl" oor:op="replace">' % cmd), cmd)

    def test_the_other_apps_text_box_nodes_are_not_touched(self):
        # Calc's and Writer's InsertTextBoxMenu nodes keep their names and modules
        nodes = {k: v for k, v in controller_nodes(app="impress").items() if v["Command"] == ".uno:InsertTextBoxMenu"}
        self.assertEqual("com.sun.star.text.TextDocument", nodes["InsertTextBoxMenuPopup"]["Module"])
        self.assertEqual("insert_textbox", nodes["InsertTextBoxMenuPopup"]["Value"])

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        # the two dropdown commands are new: only the Insert page and the controller nodes name them
        toolbars = list(TOOLBARS.glob("*.xml"))
        uis = [p for p in (ROOT / "sd/uiconfig/simpress/ui").glob("notebookbar*.ui") if p != IMPRESS.office]
        self.assertTrue(toolbars and uis)
        for cmd in ("InsertZoomMenu", "InsertTextBoxMenu"):
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
        mk = read("sd/UIConfig_simpress.mk")
        for cmd in NEW_MENUS:
            _label, resource, items = MENUS[cmd]
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("\tsd/uiconfig/simpress/popupmenu/" + resource + " \\\n", mk)
            self.assertEqual(items, self.menu_ids(ET.parse(path).getroot()), resource)

    def test_the_shapes_popup_lists_the_design_items_with_the_line_submenu(self):
        # design section 1: ShapesLineMenu >; separator; the six shape galleries; separator; the three toolboxes
        root = ET.parse(POPUPMENU / "home_shapes.xml").getroot()
        self.assertEqual(uno("ShapesLineMenu") + [SEP] + uno("BasicShapes", "SymbolShapes", "ArrowShapes",
                                                             "FlowChartShapes", "CalloutShapes", "StarShapes")
                         + [SEP] + uno("ArrowsToolbox", "ConnectorToolbox", "Objects3DToolbox"),
                         self.menu_ids(root))
        submenu = root.find(MENU + "menu")
        self.assertEqual(uno("Line", "Freeline_Unfilled", "Freeline", "Bezier_Unfilled", "BezierFill",
                             "Polygon_Unfilled", "Polygon_Diagonal_Unfilled", "Polygon_Diagonal"),
                         self.menu_ids(submenu.find(MENU + "menupopup")))

    def test_the_stock_controllers_of_the_real_buttons_are_kept(self):
        controlled = {}
        for v in controller_nodes(app="impress").values():
            if v["Module"] in ("", PRESENTATION_MODULE, None):
                controlled.setdefault(v["Command"], set()).add(v["Controller"].rsplit(".", 1)[1])
        self.assertIn("InsertSlideController", controlled[".uno:InsertPage"])
        self.assertIn("TableToolBoxControl", controlled[".uno:InsertTable"])
        self.assertIn("InsertSymbolToolBoxControl", controlled[".uno:CharmapControl"])

    def test_suppr_has_an_entry_for_every_button(self):
        suppr = IMPRESS.suppr.read_text(encoding="utf-8")
        for wid in g.ids_of(self.layout):
            if wid.startswith("btn"):
                self.assertRegex(suppr, re.escape(OFFICE_REL + ":") + r"//Gtk(Menu)?ToolButton\[@id='"
                                 + re.escape(wid) + r"'\] button-no-label")

    def test_regenerating_the_page_changes_nothing(self):
        regenerated = g.splice(self.office, self.layout, g.emit_page(self.layout))
        self.assertEqual(self.office, regenerated)
        suppr = IMPRESS.suppr.read_text(encoding="utf-8")
        self.assertEqual(suppr, g.sync_suppr(suppr, OFFICE_REL, regenerated))
        self.assertIsNone(IMPRESS.false)


if __name__ == "__main__":
    unittest.main()

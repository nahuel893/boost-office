# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Impress Design tab (Themes, Variants, Customize), moved before Transitions: layout vs
product/docs/impress-ribbon-tabs.md section 1 "Design", the Variants dropdown (popup file, controllers,
labels), the three Design placeholders, the move of the tab, and the commands that leave the tab (section 2,
"Design (0)": none)."""
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
LAYOUT = ROOT / "product/ui/impress_design.json"
OFFICE_REL = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sd/uiconfig/simpress/popupmenu"
MENU = "{http://openoffice.org/2001/menu}"
PRESENTATION_MODULE = "com.sun.star.presentation.PresentationDocument"
PART = ".uno:PageLayoutThemePart?Part:string="
MASTERS = ".uno:SidebarDeck.SdMasterPagesDeck"
PROPERTIES = ".uno:SidebarDeck.PropertyDeck"


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Design".
# Size: L = large, I = small (icon). Themes and the variants box are galleries in PowerPoint; LibreOffice has
# no gallery for them, so they are large boxes. Designer is cloud and omitted.
DESIGN = {
    "Themes": ("Themes", 3, [("large", [MASTERS])]),
    "Variants": ("Variants", 3, [("large", uno("ThemeSelectorPanel")), ("small", uno("DesignVariantsMenu"))]),
    "Customize": ("Customize", 3, [("large", uno("SlideSetup")), ("large", [PROPERTIES])]),
}
SHAPES = {"Themes": [1], "Variants": [1, 1], "Customize": [1, 1]}
# PowerPoint's label per item (T9w); the layout item's "cmd" (the widget command) is the key
POWERPOINT_LABELS = {
    "SidebarDeck.SdMasterPagesDeck": "Themes", "ThemeSelectorPanel": "Variants", "DesignVariantsMenu": "More",
    "SlideSetup": "Slide Size", "SidebarDeck.PropertyDeck": "Format Background"}
# Only the Variants menu is a dropdown: Slide Size and Format Background have no menu of their own in
# LibreOffice and are plain buttons (design decision 9), as are the deck button and the theme colors box.
SPLITS = {"DesignVariantsMenu"}

# command -> (label, popup resource, popup items in order); design section 1 "Design"
MENUS = {"DesignVariantsMenu": ("Variants", "design_variants",
                                uno("ThemeDialog") + [PART + "fonts", PART + "effects", PART + "backgroundstyles"])}
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, the Design rows)
    PART + "fonts": "Fonts", PART + "effects": "Effects", PART + "backgroundstyles": "Background Styles"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("impress"))
DESIGN_SLOT = 10

# design section 2 "Design (0)": nothing leaves the tab
LEFT_THE_TAB = {}
# the stock Design page had one widget group; its ids must be gone
OLD_PAGE_WIDGETS = ["gdDesignTheme", "lbDesignTheme", "bxDesignThemeColorsPanel", "btnDesignThemeColorsPanel"]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ImpressDesignUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Design", self.layout["page"])
        self.assertEqual("Design", self.layout["id_prefix"])
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
        self.assertEqual(5, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_dropdown_is_split_the_rest_are_plain(self):
        for item in self.items():
            expected = "split" if item["cmd"] in SPLITS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_powerpoints_label_in_office_label(self):
        # T9w: gen_ribbon turns office_label into the button's label; menus, help and tooltips keep LibreOffice's
        self.assertEqual(POWERPOINT_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_no_url_variant_item_is_on_the_ribbon(self):
        # the ? variants (Fonts, Effects, Background Styles) live in the Variants menu only, so no layout
        # item needs an explicit icon for one
        for item in self.items():
            self.assertNotIn("?", g.item_url(item), item["cmd"])

    def test_the_stock_theme_colors_box_stays_as_the_variants_box(self):
        # the stock page's only control, .uno:ThemeSelectorPanel, is kept (design section 1) with its
        # controller untouched (Controller.xcu, no module)
        self.assertIn(".uno:ThemeSelectorPanel", {g.item_url(i) for i in self.items()})
        nodes = [v for v in controller_nodes(app="impress").values() if v["Command"] == ".uno:ThemeSelectorPanel"]
        self.assertEqual(["com.sun.star.comp.svx.ThemeColorsToolBoxControl"], [v["Controller"] for v in nodes])
        self.assertEqual(1, self.office.count('action-name">.uno:ThemeSelectorPanel<'))

    def test_the_old_design_page_widgets_are_gone(self):
        self.assertEqual([], self.layout.get("remove_objects", []))  # the stock page has no overflow menu
        for old in OLD_PAGE_WIDGETS:
            self.assertNotIn('id="%s"' % old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Design-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Design-end -->"))
        self.assertIn('id="Design"', self.office)  # the page itself stays, with the tab label

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Design", {layout["id_prefix"] for layout in office.page_layouts("impress")})
        self.assertEqual(office.expected_office_ui("impress"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def tab_order(self):
        root = ET.fromstring(self.office)
        book = root.find(".//object[@id='ContextContainer']")
        pages = [c.find("object").get("id") for c in book.findall("child") if c.get("type") != "tab"]
        labels = [c.find("object").get("id") for c in book.findall("child[@type='tab']")]
        return book, pages, labels

    def test_design_moves_before_the_layout_page_which_becomes_transitions(self):
        tabs = json.loads(IMPRESS.tabs.read_text(encoding="utf-8"))
        self.assertEqual([{"page": "Design", "tab": "DesignLabel", "before": "Layout"}], tabs["move"])
        self.assertEqual({"Design": 3, "DesignLabel": 3, "Layout": 4, "LayoutLabel": 4},
                         {k: v for k, v in tabs["positions"].items() if k in ("Design", "DesignLabel", "Layout",
                                                                                "LayoutLabel")})
        _book, pages, labels = self.tab_order()
        self.assertEqual(["File", "Home Tab", "Insert", "Design", "Layout", "Animations", "SlideShow", "Review",
                          "View"], pages[:9])
        self.assertEqual(["FileLabel", "HomeLabel", "InsertLabel", "DesignLabel", "LayoutLabel", "AnimationsLabel",
                          "SlideShowLabel", "ReviewLabel", "ViewLabel"], labels[:9])

    def test_the_moved_tab_and_page_carry_the_new_positions(self):
        book, pages, labels = self.tab_order()
        positions = {}
        for child in book.findall("child"):
            obj = child.find("object")
            positions[obj.get("id")] = child.findtext("packing/property[@name='position']")
        self.assertEqual(("3", "3"), (positions["Design"], positions["DesignLabel"]))
        self.assertEqual(("4", "4"), (positions["Layout"], positions["LayoutLabel"]))
        self.assertEqual(("5", "5"), (positions["Animations"], positions["AnimationsLabel"]))
        self.assertEqual(("6", "6"), (positions["SlideShow"], positions["SlideShowLabel"]))

    def test_the_tab_label_stays_design_with_its_mnemonic(self):
        self.assertRegex(self.office, r'context="TabbedImpress\|DesignTabLabel">~Design</property>')

    def test_the_commands_that_left_the_tab_are_none(self):
        # design section 2 "Design (0)": the stock page held only the theme colors box, which stays
        self.assertEqual({}, LEFT_THE_TAB)
        stock = ET.parse(ROOT / "sd/uiconfig/simpress/ui/notebookbar.ui").getroot()
        node = next(o for o in stock.iter("object") if o.get("id") == "Design")
        commands = {p.text for p in node.iter("property") if p.get("name") == "action-name"}
        self.assertEqual({".uno:ThemeSelectorPanel"}, commands)
        self.assertLessEqual(commands, {g.item_url(i) for i in self.items()})

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="impress")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_new_menu_and_placeholder_items_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_new_commands_have_the_image_flag(self):
        flagged = flagged_commands(app="impress")
        for cmd in MENUS:
            self.assertIn(".uno:" + cmd, flagged, cmd)
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_the_menu_items_are_known_commands(self):
        labels = commands_xcu(app="impress")
        for cmd in MENUS:
            for url in MENUS[cmd][2]:
                self.assertIn(url, labels, url)

    def test_slide_size_reads_the_slide_properties_command(self):
        # .uno:SlideSetup has a TargetURL and no dispatch of its own: it runs .uno:PageSetup (the Slide
        # Properties dialog), whose state decides whether the button is enabled
        text = read("officecfg/registry/data/org/openoffice/Office/UI/DrawImpressCommands.xcu")
        node = text.split('<node oor:name=".uno:SlideSetup" oor:op="replace">')[1].split("</node>")[0]
        self.assertIn("<value>.uno:PageSetup</value>", node)
        self.assertIn("Slide Properties...", node)

    def test_the_registry_labels_every_design_slot_and_variant(self):
        registry = placeholders.registry("impress")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items() if u.startswith(".uno:PageLayout")})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        self.assertEqual("PageLayoutThemePart", entries[DESIGN_SLOT]["command"])
        self.assertEqual(["Part:string=fonts", "Part:string=effects", "Part:string=backgroundstyles"],
                         entries[DESIGN_SLOT]["variants"])
        self.assertEqual({"Part:string=fonts": "Fonts", "Part:string=effects": "Effects",
                          "Part:string=backgroundstyles": "Background Styles"},
                         entries[DESIGN_SLOT]["variant_labels"])

    def test_the_placeholder_items_have_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        for url in PLACEHOLDER_LABELS:
            self.assertNotIn(url, controlled, url)

    def impress_nodes(self, command):
        return [v for v in controller_nodes(app="impress").values()
                if v["Command"] == command and v["Module"] == PRESENTATION_MODULE]

    def test_the_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        for cmd, (_label, resource, _items) in MENUS.items():
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in self.impress_nodes(".uno:" + cmd)}
            self.assertEqual({"ResourceMenuController", "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])
            self.assertEqual(resource, kinds["ResourceMenuController"]["Value"])

    def test_impress_nodes_carry_the_impress_suffix(self):
        text = read("officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu")
        for cmd in MENUS:
            self.assertEqual(1, text.count('<node oor:name="%sImpressPopup" oor:op="replace">' % cmd), cmd)
            self.assertEqual(1, text.count('<node oor:name="%sImpressControl" oor:op="replace">' % cmd), cmd)

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        # the dropdown command is new: only the Design page and the controller nodes name it
        toolbars = list((ROOT / "sd/uiconfig/simpress/toolbar").glob("*.xml"))
        uis = [p for p in (ROOT / "sd/uiconfig/simpress/ui").glob("notebookbar*.ui") if p != IMPRESS.office]
        self.assertTrue(toolbars and uis)
        for path in toolbars + uis:
            self.assertNotIn(".uno:DesignVariantsMenu", path.read_text(encoding="utf-8"), path.name)

    def menu_ids(self, element):
        out = []
        for e in element:
            if e.tag in (MENU + "menuitem", MENU + "menu"):
                out.append(e.get(MENU + "id"))
            elif e.tag == MENU + "menuseparator":
                out.append("-")
        return out

    def test_popup_file_exists_is_registered_and_lists_the_design_items(self):
        mk = read("sd/UIConfig_simpress.mk")
        for _cmd, (_label, resource, items) in MENUS.items():
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("\tsd/uiconfig/simpress/popupmenu/" + resource + " \\\n", mk)
            self.assertEqual(items, self.menu_ids(ET.parse(path).getroot()), resource)

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

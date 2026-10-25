# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Impress View tab (Presentation Views, Master Views, Show, Zoom, Color/Grayscale, Window, Macros), the stock
View page regenerated: layout vs product/docs/impress-ribbon-tabs.md section 1 "View", the three new dropdowns (popup
files, controllers, labels), the five placeholders, and the commands that leave the tab (section 2, "View (18)")."""
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
LAYOUT = ROOT / "product/ui/impress_view.json"
OFFICE_REL = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sd/uiconfig/simpress/popupmenu"
MENUBAR = ROOT / "sd/uiconfig/simpress/menubar/menubar.xml"
SHORTCUTS = ROOT / "sd/uiconfig/simpress/toolbar/notebookbarshortcuts.xml"
MENU = "{http://openoffice.org/2001/menu}"
PRESENTATION_MODULE = "com.sun.star.presentation.PresentationDocument"
SEP = "-"  # a separator in a menu item list
READING = ".uno:ViewMode?Mode:string=reading"


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "View".
# Size: L = large, S = small-label, I = small (icon only). The design's chk controls (Ruler, Gridlines, Guides) and
# its toggles (Notes Page, Notes) are plain buttons, the generator's closest kind (a real toggle command shows its
# state itself); every dropdown is a split.
DESIGN = {
    "PresentationViews": ("Presentation Views", 3, [
        ("large", uno("NormalMultiPaneGUI")), ("large", uno("OutlineMode")), ("small-label", uno("DiaMode")),
        ("small-label", uno("NotesMode")), ("small-label", [READING])]),
    "MasterViews": ("Master Views", 3, [
        ("small-label", uno("SlideMasterPage")), ("small-label", uno("HandoutMode")),
        ("small-label", uno("NotesMasterPage"))]),
    "Show": ("Show", 3, [
        ("small-label", uno("ShowRuler")), ("small-label", uno("GridVisible")),
        ("small-label", uno("HelplinesVisible")), ("large", uno("BottomPaneImpress"))]),
    "Zoom": ("Zoom", 3, [("large", uno("Zoom")), ("large", uno("ZoomPage"))]),
    "ColorGrayscale": ("Color/Grayscale", 3, [("large", uno("ViewColorGrayscaleMenu"))]),
    "Window": ("Window", 3, [
        ("large", uno("NewWindow")), ("small", uno("ViewArrangeAll")), ("small", uno("ViewCascade")),
        ("small", uno("ViewSplit")), ("large", uno("ViewSwitchWindowsMenu"))]),
    "Macros": ("Macros", 3, [("large", uno("ViewMacrosMenu"))]),
}
SHAPES = {"PresentationViews": [1, 1, 3], "MasterViews": [3], "Show": [3, 1], "Zoom": [1, 1],
          "ColorGrayscale": [1], "Window": [1, 3, 1], "Macros": [1]}
# PowerPoint's label per item; the layout item's "cmd" (the widget command) is the key
POWERPOINT_LABELS = {
    "NormalMultiPaneGUI": "Normal", "OutlineMode": "Outline View", "DiaMode": "Slide Sorter",
    "NotesMode": "Notes Page", "ViewReadingView": "Reading View", "SlideMasterPage": "Slide Master",
    "HandoutMode": "Handout Master", "NotesMasterPage": "Notes Master", "ShowRuler": "Ruler",
    "GridVisible": "Gridlines", "HelplinesVisible": "Guides", "BottomPaneImpress": "Notes", "Zoom": "Zoom",
    "ZoomPage": "Fit to Window", "ViewColorGrayscaleMenu": "Color/Grayscale", "NewWindow": "New Window",
    "ViewArrangeAll": "Arrange All", "ViewCascade": "Cascade", "ViewSplit": "Move Split",
    "ViewSwitchWindowsMenu": "Switch Windows", "ViewMacrosMenu": "Macros"}
SPLITS = {"ViewColorGrayscaleMenu", "ViewSwitchWindowsMenu", "ViewMacrosMenu"}

# command -> (label, popup resource or None for the window list, popup items in order); design section 1
MENUS = {
    "ViewColorGrayscaleMenu": ("Color/Grayscale", "view_colorgrayscale",
                               uno("OutputQualityColor", "OutputQualityGrayscale", "OutputQualityBlackWhite")),
    "ViewSwitchWindowsMenu": ("Switch Windows", None, []),  # WindowListMenuController fills it
    "ViewMacrosMenu": ("Macros", "view_macros", uno("RunMacro", "MacroRecorder", "MacroManager", "BasicIDEAppear")),
}
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, the View rows)
    READING: "Reading View", ".uno:ViewArrangeAll": "Arrange All", ".uno:ViewCascade": "Cascade",
    ".uno:ViewSplit": "Move Split"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("impress"))
VIEW_SLOTS = [19, 20, 21, 22]

# design section 2 "View (18)": command -> (class, menu-bar id that keeps it reachable).
# Class a: the same command in the menu bar; q: the quick access bar's first button; b: reachable through another
# command (Dark Mode: Tools > Options > LibreOffice > Appearance, the Options dialog is `.uno:OptionsTreeDialog`).
LEFT_THE_TAB = {
    "ZoomMode": ("a", "ZoomMode"), "ZoomPageWidth": ("a", "ZoomPageWidth"), "ZoomNext": ("a", "ZoomNext"),
    "ZoomPrevious": ("a", "ZoomPrevious"), "Sidebar": ("a", "Sidebar"), "LeftPaneImpress": ("a", "LeftPaneImpress"),
    "Menubar": ("q", "Menubar"), "ToggleTabBarVisibility": ("a", "ToggleTabBarVisibility"),
    "ChangeTheme": ("b", "OptionsTreeDialog"), "CapturePoint": ("a", "CapturePoint"),
    "SnapPoints": ("a", "SnapPoints"), "SnapBorder": ("a", "SnapBorder"), "GridUse": ("a", "GridUse"),
    "HelplinesUse": ("a", "HelplinesUse"), "SnapFrame": ("a", "SnapFrame"), "HelplinesMove": ("a", "HelplinesMove"),
    "StatusBarVisible": ("a", "StatusBarVisible"), "Zoom100Percent": ("a", "Zoom100Percent")}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def stock_commands(*page_ids):
    stock = ET.parse(ROOT / "sd/uiconfig/simpress/ui/notebookbar.ui").getroot()
    commands, ids = set(), set()
    for wid in page_ids:
        node = next(o for o in stock.iter("object") if o.get("id") == wid)
        commands |= {p.text for p in node.iter("property") if p.get("name") == "action-name"}
        ids |= {o.get("id") for o in node.iter("object")}
    return commands, ids


class ImpressViewUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("View", self.layout["page"])  # the stock page keeps its id
        self.assertEqual("View", self.layout["id_prefix"])
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
        self.assertEqual(21, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_dropdowns_are_split_the_rest_are_plain_buttons(self):
        self.assertEqual(SPLITS, {i["cmd"] for i in self.items() if i.get("kind") == "split"})
        for item in self.items():
            if item["cmd"] not in SPLITS:
                self.assertEqual("button", item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_powerpoints_label_in_office_label(self):
        self.assertEqual(POWERPOINT_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_the_url_variant_has_its_own_widget_command_and_an_explicit_icon_that_exists(self):
        manifest = json.loads((ROOT / "product/icons/manifest.json").read_text(encoding="utf-8"))
        names = {e["name"] for e in manifest["icons"]}
        for item in self.items():
            if "?" in g.item_url(item):
                self.assertTrue(item.get("icon"), item["cmd"])
                self.assertNotIn("?", item["cmd"])
            if "icon" in item:
                name = item["icon"].removeprefix("cmd/").removeprefix("32/").removeprefix("sc_")
                self.assertIn(name.removesuffix(".png"), names, item["cmd"])
        self.assertEqual(["ViewReadingView"], [i["cmd"] for i in self.items() if "?" in g.item_url(i)])

    def test_the_overflow_menu_goes_with_the_stock_buttons(self):
        self.assertEqual(["Menu View"], self.layout["remove_objects"])
        _commands, ids = stock_commands("View")
        _menu, menu_ids = stock_commands("Menu View")
        present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office))
        self.assertTrue(ids and menu_ids)
        # a stock id the new layout generates again is the new widget, not a leftover
        gone = (ids | menu_ids | {"Menu View"}) - {"View", "pmhbView", "ViewLabel"} - set(g.ids_of(self.layout))
        self.assertEqual(set(), gone & present)
        self.assertIn('id="View"', self.office)  # the page itself stays, with the tab label
        self.assertEqual(1, self.office.count("<!-- product:View-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:View-end -->"))

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("View", {layout["id_prefix"] for layout in office.page_layouts("impress")})
        self.assertEqual(office.expected_office_ui("impress"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_view_follows_review(self):
        root = ET.fromstring(self.office)
        book = root.find(".//object[@id='ContextContainer']")
        pages = [c.find("object").get("id") for c in book.findall("child") if c.get("type") != "tab"]
        tabs = [c.find("object").get("id") for c in book.findall("child[@type='tab']")]
        self.assertEqual(["Review", "View", "Table"], pages[7:10])
        self.assertEqual(["ReviewLabel", "ViewLabel", "TableLabel"], tabs[7:10])

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(18, len(LEFT_THE_TAB))
        self.assertEqual({"a": 16, "b": 1, "q": 1}, {k: sum(1 for v in LEFT_THE_TAB.values() if v[0] == k)
                                                      for k in "abq"})
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()} | {g.item_url(i) for i in self.items()}
        in_menus = {u for _l, _r, items in MENUS.values() for u in items}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertNotIn(".uno:" + name, in_menus, name)
            if kind == "a":
                self.assertEqual(name, menu_id)
                self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)
            elif kind == "q":  # the Menubar toggle is the quick access bar's first button, as in Calc and Writer
                items = re.findall(r'xlink:href="([^"]+)"', SHORTCUTS.read_text(encoding="utf-8"))
                self.assertEqual(".uno:" + menu_id, items[0], name)
            else:  # b: Dark Mode is a setting of Tools > Options > LibreOffice > Appearance
                self.assertEqual("OptionsTreeDialog", menu_id)
                self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)

    def test_the_stock_view_page_commands_either_stay_or_are_in_the_leave_list(self):
        # every command of the stock View page and its overflow menu is on this page, in a dropdown, or in the
        # leave list; the leave list is reachable (test above)
        commands, _ = stock_commands("View", "Menu View")
        on_tab = {g.item_url(i) for i in self.items()} | {u for _l, _r, items in MENUS.values() for u in items}
        left = {".uno:" + name for name in LEFT_THE_TAB}
        self.assertGreater(len(commands), 20)
        self.assertEqual(set(), commands - on_tab - left)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="impress")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])
            if "action" in item:
                self.assertIn(url, labels, item["cmd"])

    def test_the_new_menus_and_placeholders_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
        self.assertEqual(4, len(PLACEHOLDER_LABELS))
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
        for _label, _resource, items in MENUS.values():
            for url in items:
                self.assertIn(url, labels, url)

    def test_the_registry_labels_every_view_slot_and_variant(self):
        registry = placeholders.registry("impress")
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        self.assertEqual(["ViewMode", "ViewArrangeAll", "ViewCascade", "ViewSplit"],
                         [entries[o]["command"] for o in VIEW_SLOTS])
        self.assertEqual(["Mode:string=reading"], entries[19]["variants"])
        self.assertEqual({"Mode:string=reading": "Reading View"}, entries[19]["variant_labels"])
        self.assertEqual(["Arrange All", "Cascade", "Move Split"], [entries[o]["label"] for o in (20, 21, 22)])
        by_url = placeholders.labels_by_url(registry)
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, by_url[url], url)

    def test_the_placeholders_have_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        for url in PLACEHOLDER_LABELS:
            self.assertNotIn(url, controlled, url)

    def impress_nodes(self, command):
        return [v for v in controller_nodes(app="impress").values()
                if v["Command"] == command and v["Module"] == PRESENTATION_MODULE]

    def test_each_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        for cmd, (_label, resource, _items) in MENUS.items():
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in self.impress_nodes(".uno:" + cmd)}
            popup = "WindowListMenuController" if resource is None else "ResourceMenuController"
            self.assertEqual({popup, "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])
            if resource is None:
                self.assertNotIn("Value", kinds[popup])
            else:
                self.assertEqual(resource, kinds[popup]["Value"])

    def test_impress_nodes_carry_the_impress_suffix(self):
        text = read("officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu")
        for cmd in MENUS:
            self.assertIn('<node oor:name="%sImpressPopup" oor:op="replace">' % cmd, text)
            self.assertIn('<node oor:name="%sImpressControl" oor:op="replace">' % cmd, text)

    def test_calc_and_writer_keep_their_own_nodes(self):
        # Calc and Writer own Switch Windows and Macros (Color/Grayscale is Impress's alone)
        for app, module in (("calc", "com.sun.star.sheet.SpreadsheetDocument"),
                            ("writer", "com.sun.star.text.TextDocument")):
            nodes = controller_nodes(app=app).values()
            for cmd in ("ViewSwitchWindowsMenu", "ViewMacrosMenu"):
                own = [v for v in nodes if v["Command"] == ".uno:" + cmd and v["Module"] == module]
                self.assertEqual(2, len(own), (cmd, app))
        impress = controller_nodes(app="impress").values()
        self.assertEqual([], [v for v in impress if v["Command"] == ".uno:ViewColorGrayscaleMenu"
                              and v["Module"] != PRESENTATION_MODULE])

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        toolbars = list((ROOT / "sd/uiconfig/simpress/toolbar").glob("*.xml"))
        uis = [p for p in (ROOT / "sd/uiconfig/simpress/ui").glob("notebookbar*.ui") if p != IMPRESS.office]
        self.assertTrue(toolbars and uis)
        for cmd in MENUS:
            for path in toolbars + uis:
                self.assertNotIn(".uno:" + cmd, path.read_text(encoding="utf-8"), "%s in %s" % (cmd, path.name))
        # the real commands of the menus get no controller of the new menus' kind
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()
                      if v["Module"] == PRESENTATION_MODULE}
        for url in uno("OutputQualityColor", "OutputQualityGrayscale", "OutputQualityBlackWhite", "RunMacro",
                       "MacroRecorder", "MacroManager", "BasicIDEAppear", "NewWindow", "Zoom", "ZoomPage"):
            self.assertNotIn(url, controlled, url)

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
        for _label, resource, items in MENUS.values():
            if resource is None:
                continue
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("\tsd/uiconfig/simpress/popupmenu/" + resource + " \\\n", mk)
            self.assertEqual(items, self.menu_ids(ET.parse(path).getroot()), resource)
        # the window list has no popup file: the controller lists the open windows
        self.assertFalse((POPUPMENU / "view_switchwindows.xml").exists())

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

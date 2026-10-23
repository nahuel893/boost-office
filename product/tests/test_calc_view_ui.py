# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The View tab: layout vs product/docs/design/calc-view-tab-layout.txt (plus the Sheet View group),
labels, menus, placeholders, the widget ids (R12) and the commands that leave the tab (R14)."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import office, placeholders
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands, tooltips
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_view.json"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
SUPPR = ROOT / "solenv/sanitizers/ui/modules/scalc.suppr"
POPUPMENU = ROOT / "sc/uiconfig/scalc/popupmenu"
MENUBAR = ROOT / "sc/uiconfig/scalc/menubar/menubar.xml"
SHORTCUTS = ROOT / "sc/uiconfig/scalc/toolbar/notebookbarshortcuts.xml"
MENU = "{http://openoffice.org/2001/menu}"
SHEET_VIEW = ".uno:ViewSheetView?Action:string="
VISIBILITY = ".uno:ViewWindowVisibility?Action:string="
SIDE_BY_SIDE = ".uno:ViewSideBySide?Action:string="
SEP = "-"  # a separator in a menu item list
WINDOW_LIST = "com.sun.star.comp.framework.WindowListMenuController"

# section -> (caption, [(style, [url, ...]) per toolbox in document order])
DESIGN = {
    # Excel's Sheet View group (controller ruling): its reduced form, "Default" instead of the combo
    # and the four icon-only buttons in one row, all placeholders of the family slot +421
    "SheetView": ("Sheet View", [("small-label", [SHEET_VIEW + "switch"]),
                                 ("small", [SHEET_VIEW + v for v in ("keep", "exit", "new", "options")])]),
    "WorkbookViews": ("Workbook Views", [("large", [".uno:NormalViewMode"]), ("large", [".uno:PagebreakMode"]),
                                         ("large", [".uno:ViewPageLayout"]), ("large", [".uno:ViewCustomViews"])]),
    "DarkMode": ("Dark Mode", [("large", [".uno:ChangeTheme"])]),
    "Show": ("Show", [("large", [".uno:Navigator"]), ("small-label", [".uno:ViewRuler"]),
                      ("small-label", [".uno:ToggleSheetGrid"]), ("small-label", [".uno:InputLineVisible"]),
                      ("small-label", [".uno:ViewRowColumnHeaders"]),
                      ("small-label", [".uno:ViewColumnRowHighlighting"])]),
    "Zoom": ("Zoom", [("large", [".uno:Zoom"]), ("large", [".uno:Zoom100Percent"]),
                      ("large", [".uno:ZoomOptimal"])]),
    "Window": ("Window", [("large", [".uno:NewWindow"]), ("large", [".uno:ViewArrangeAll"]),
                          ("large", [".uno:ViewFreezePanesMenu"]), ("small-label", [".uno:SplitWindow"]),
                          ("small-label", [VISIBILITY + "hide"]), ("small-label", [VISIBILITY + "unhide"]),
                          ("small-label", [SIDE_BY_SIDE + "toggle"]), ("small-label", [SIDE_BY_SIDE + "sync"]),
                          ("small-label", [SIDE_BY_SIDE + "reset"]), ("large", [".uno:ViewSwitchWindowsMenu"])]),
    "Macros": ("Macros", [("large", [".uno:ViewMacrosMenu"])]),
}
SHAPES = {"SheetView": [2], "WorkbookViews": [1] * 4, "DarkMode": [1], "Show": [1, 3, 2],
          "Zoom": [1] * 3, "Window": [1, 1, 1, 3, 3, 1], "Macros": [1]}
MENUS = {  # command: (label, popup resource or None for the framework window list, popup items in order)
    "ViewFreezePanesMenu": ("Freeze Panes", "view_freezepanes",
                            [".uno:FreezePanes", ".uno:FreezePanesRow", ".uno:FreezePanesColumn"]),
    "ViewMacrosMenu": ("Macros", "view_macros", [".uno:MacroManager", ".uno:MacroRecorder", SEP,
                                                 ".uno:RunMacro", ".uno:BasicIDEAppear"]),
    "ViewSwitchWindowsMenu": ("Switch Windows", None, []),
}
PLACEHOLDER_LABELS = {  # URL -> label
    SHEET_VIEW + "switch": "Default", SHEET_VIEW + "keep": "Keep", SHEET_VIEW + "exit": "Exit",
    SHEET_VIEW + "new": "New", SHEET_VIEW + "options": "Options",
    ".uno:ViewPageLayout": "Page Layout", ".uno:ViewCustomViews": "Custom Views",
    ".uno:ViewRuler": "Ruler", ".uno:ViewArrangeAll": "Arrange All",
    VISIBILITY + "hide": "Hide", VISIBILITY + "unhide": "Unhide",
    SIDE_BY_SIDE + "toggle": "View Side by Side", SIDE_BY_SIDE + "sync": "Synchronous Scrolling",
    SIDE_BY_SIDE + "reset": "Reset Window Position"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS)  # implemented ones are no placeholder
VIEW_SLOTS = list(range(413, 419)) + [421]
# R14: the LibreOffice-only buttons the old page had; each must stay reachable
LEFT_THE_MENU_BAR = ["ZoomPage", "ZoomPageWidth", "FullScreen", "ViewValueHighlighting", "ViewHiddenColRow",
                     "DesignerDialog", "Sidebar", "StatusBarVisible"]
LEFT_THE_TAB = LEFT_THE_MENU_BAR + ["Menubar"]
OLD_PAGE_WIDGETS = ["btnViewZoomPage", "btnViewFullScreen", "btnViewMenubar", "btnViewViewValueHighlighting",
                    "btnViewToggleFormula", "btnViewViewHiddenColRow", "btnInsertDesignerDialog",
                    "btnViewSidebar", "btnViewFreezePanes"]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


# Excel's label per item where it differs from LibreOffice's (T9w: the ribbon shows it). Source: the Excel
# control of each row in product/docs/design/calc-view-tab-layout.txt
EXCEL_LABELS = {".uno:NormalViewMode": "Normal", ".uno:PagebreakMode": "Page Break Preview",
    ".uno:ChangeTheme": "Switch Modes", ".uno:Navigator": "Navigation", ".uno:ToggleSheetGrid": "Gridlines",
    ".uno:ViewRowColumnHeaders": "Headings", ".uno:ViewColumnRowHighlighting": "Focus Cell",
    ".uno:ZoomOptimal": "Zoom to Selection", ".uno:SplitWindow": "Split"}


class CalcViewUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = OFFICE.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))  # the columns' toolboxes, then the footer

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_excels_label_is_in_office_label_where_it_differs_from_libreoffices(self):
        # T9w: the ribbon shows Excel's label (gen_ribbon turns office_label into the button's label);
        # menus, help and tooltips keep LibreOffice's. Icon-only buttons and placeholders have none.
        self.assertEqual(EXCEL_LABELS, office.office_labels(self.layout))

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("phbView", self.layout["page"])
        self.assertEqual("View", self.layout["id_prefix"])
        self.assertEqual("TabbedCalc", self.layout["context"])
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        for section in self.layout["sections"]:
            self.assertEqual(DESIGN[section["name"]][0], section["caption"])
            self.assertEqual(3, section["rows"], section["name"])

    def test_every_control_is_there_in_order_with_its_size(self):
        for section in self.layout["sections"]:
            got = [(b["style"], [g.item_url(i) for i in b["items"]]) for b in self.boxes(section)]
            self.assertEqual(DESIGN[section["name"]][1], got, section["name"])

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_sheet_view_is_the_first_group_in_excels_reduced_form(self):
        first = self.layout["sections"][0]
        self.assertEqual("SheetView", first["name"])
        switch, buttons = first["columns"][0]
        self.assertEqual("small-label", switch["style"])  # "Default" stands for Excel's combo
        self.assertEqual("small", buttons["style"])       # four icon-only buttons in one row
        self.assertEqual(["keep", "exit", "new", "options"],
                         [i["action"].rsplit("=", 1)[1] for i in buttons["items"]])
        self.assertEqual(5, sum(1 for i in self.items() if i.get("action", "").startswith(SHEET_VIEW)))

    def test_the_menu_commands_are_dropdowns_the_rest_are_plain_buttons(self):
        for item in self.items():
            expected = "split" if item["cmd"] in MENUS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_url_variants_carry_a_short_id_the_url_as_action_and_a_plain_icon_name(self):
        variants = [i for i in self.items() if "action" in i]
        self.assertEqual(5 + 2 + 3, len(variants))
        for item in variants:
            base, value = re.match(r"\.uno:(\w+)\?\w+:\w+=(\w+)$", item["action"]).groups()
            self.assertEqual("cmd/sc_%s_%s.png" % (base.lower(), value), item["icon"], item["cmd"])
        self.assertEqual(len(variants), len({i["cmd"] for i in variants}))

    def test_the_old_view_page_and_its_overflow_menu_are_gone(self):
        self.assertIn("Menu View", self.layout["remove_objects"])
        for old in ('id="Menu View"', "View-ViewButton:Menu View", 'id="View-Menu"', 'id="MenuView-'):
            self.assertNotIn(old, self.office)
        for wid in OLD_PAGE_WIDGETS:
            self.assertNotIn('id="%s"' % wid, self.office)
        self.assertEqual(1, self.office.count("<!-- product:View-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:View-end -->"))

    def test_office_ui_is_upstream_plus_tabs_and_every_generated_page(self):
        self.assertIn("View", {layout["id_prefix"] for layout in office.page_layouts()})
        self.assertEqual(office.expected_office_ui(), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        # R12: Navigator, View Grid Lines and View Headers are on Page Layout and on View
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_a_command_on_two_pages_has_a_different_widget_on_each(self):
        seen = {}
        for layout in office.page_layouts():
            for section in layout["sections"]:
                for box in g.boxes_of(section):
                    for item in box["items"]:
                        seen.setdefault(g.item_url(item), []).append(
                            "btn" + layout["id_prefix"] + item["cmd"])
        shared = {url: ids for url, ids in seen.items() if len(ids) > 1}
        for url in (".uno:Navigator", ".uno:ToggleSheetGrid", ".uno:ViewRowColumnHeaders"):
            self.assertEqual(2, len(shared[url]), url)
            self.assertIn("btnView" + url[len(".uno:"):], shared[url], url)
            self.assertIn("btnPageLayout" + url[len(".uno:"):], shared[url], url)
        for url, ids in shared.items():
            self.assertEqual(len(ids), len(set(ids)), url)

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        # R14: Entire Page/Page Width, Full Screen, Value Highlighting, Hidden Row/Column, Styles,
        # Sidebar and Status Bar are in the menu bar; the Menubar toggle is the quick access bar's
        # first button; Show Formulas is on the Formulas tab; Freeze Panes is in the dropdown
        menubar = MENUBAR.read_text(encoding="utf-8")
        for name in LEFT_THE_MENU_BAR:
            self.assertIn('menu:id=".uno:%s"' % name, menubar, name)
        self.assertIn('xlink:href=".uno:Menubar"', SHORTCUTS.read_text(encoding="utf-8"))
        on_tab = {g.item_command(i) for i in self.items()}
        for name in LEFT_THE_TAB:
            self.assertNotIn(".uno:" + name, on_tab, name)
        formulas = json.loads(read("product/ui/calc_formulas.json"))
        formulas_cmds = {i["cmd"] for s in formulas["sections"] for b in g.boxes_of(s) for i in b["items"]}
        self.assertIn("ToggleFormula", formulas_cmds)
        self.assertIn(".uno:FreezePanes", MENUS["ViewFreezePanesMenu"][2])

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu()
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])
            if "action" in item:
                self.assertIn(url, labels, item["cmd"])

    def test_every_new_command_has_the_image_flag(self):
        flagged = flagged_commands()
        for item in self.items():
            if "icon" not in item:
                self.assertIn(g.item_url(item), flagged, item["cmd"] + " is left out of the image list")
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_placeholder_labels_and_tooltips_follow_excel(self):
        labels, tips = commands_xcu(), tooltips()
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_variant_labels_with_an_ampersand_are_escaped_in_the_xcu(self):
        # variant nodes are named with the full URL; "&" would break the XML
        xcu = read("officecfg/registry/data/org/openoffice/Office/UI/CalcCommands.xcu")
        for url in PLACEHOLDER_LABELS:
            self.assertIn('oor:name="%s"' % url.replace("&", "&amp;"), xcu, url)

    def test_the_registry_labels_every_view_slot_and_variant(self):
        by_url = placeholders.labels_by_url()
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items()
                                              if u.startswith(".uno:View") and "Menu" not in u})
        entries = {e["offset"]: e for e in placeholders.load_all()}
        for offset in VIEW_SLOTS:
            entry = entries[offset]
            if "variants" in entry:
                self.assertEqual(entry["variants"], list(entry["variant_labels"]), entry["command"])
            else:
                self.assertIn("label", entry, entry["command"])
        self.assertEqual(["Action:string=" + v for v in ("switch", "keep", "exit", "new", "options")],
                         entries[421]["variants"])

    def test_every_view_placeholder_is_on_the_page_and_has_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes().values()}
        used = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, used, url)
            self.assertNotIn(url, controlled, url)

    def test_dropdown_commands_have_labels_and_popup_and_toolbar_controllers(self):
        labels, nodes = commands_xcu(), controller_nodes()
        self.assertEqual(3, len(MENUS))
        for cmd, (label, resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd]
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in ours}
            popup = "WindowListMenuController" if resource is None else "ResourceMenuController"
            self.assertEqual({popup, "GenericPopupToolbarController"}, set(kinds), cmd)
            for kind in kinds.values():
                self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", kind["Module"])
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])
            if resource is None:  # R7: the framework's window list under the new command, no popup file
                self.assertNotIn("Value", kinds[popup])
                self.assertEqual(WINDOW_LIST, kinds[popup]["Controller"])
            else:
                self.assertEqual(resource, kinds[popup]["Value"])

    def menu_ids(self, element):
        out = []
        for e in element:
            if e.tag in (MENU + "menuitem", MENU + "menu"):
                out.append(e.get(MENU + "id"))
            elif e.tag == MENU + "menuseparator":
                out.append(SEP)
        return out

    def test_popup_files_exist_are_registered_and_list_the_design_items(self):
        mk = read("sc/UIConfig_scalc.mk")
        for _label, resource, items in MENUS.values():
            if resource is None:
                self.assertFalse((POPUPMENU / "view_switchwindows.xml").exists())
                continue
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("sc/uiconfig/scalc/popupmenu/" + resource + " \\", mk)
            self.assertEqual(items, self.menu_ids(ET.parse(path).getroot()), resource)

    def test_every_popup_item_is_a_known_command(self):
        labels = commands_xcu()
        for _label, _resource, items in MENUS.values():
            for url in items:
                if url != SEP:
                    self.assertIn(url, labels, url)

    def test_suppr_has_an_entry_for_every_button(self):
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

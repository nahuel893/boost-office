# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Writer View tab: layout vs product/docs/writer-ribbon-tabs.md section 1 "View", the two dropdowns
(Switch Windows through the framework's window list, Macros through a popup file), the eleven placeholders,
and the commands that leave the tab (section 2, "View (12)")."""
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
LAYOUT = ROOT / "product/ui/writer_view.json"
OFFICE_REL = "sw/uiconfig/swriter/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sw/uiconfig/swriter/popupmenu"
TOOLBARS = ROOT / "sw/uiconfig/swriter/toolbar"
MENUBAR = ROOT / "sw/uiconfig/swriter/menubar/menubar.xml"
SHORTCUTS = TOOLBARS / "notebookbarshortcuts.xml"
MENU = "{http://openoffice.org/2001/menu}"
TEXT_MODULE = "com.sun.star.text.TextDocument"
SEP = "-"  # a separator in a menu item list
FRAMEWORK = "com.sun.star.comp.framework."
WINDOW_LIST = FRAMEWORK + "WindowListMenuController"

MODE = ".uno:ViewMode?Mode:string="
MOVEMENT = ".uno:ViewPageMovement?Mode:string="
SIDE_BY_SIDE = ".uno:ViewSideBySide?Action:string="


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "View".
# Size: L = large, S = small-label; chk (Show) is a small-label toggle. SharePoint > Properties (cloud) is omitted.
DESIGN = {
    "Views": ("Views", 3, [
        ("large", [MODE + "read"]), ("large", uno("PrintLayout")), ("large", uno("BrowseView")),
        ("small-label", [MODE + "outline"]), ("small-label", [MODE + "draft"])]),
    "Immersive": ("Immersive", 3, [("large", uno("FullScreen")), ("large", [MODE + "immersive"])]),
    "DarkMode": ("Dark Mode", 3, [("large", uno("ChangeTheme"))]),
    "PageMovement": ("Page Movement", 3, [
        ("large", [MOVEMENT + "vertical"]), ("large", [MOVEMENT + "sidetoside"])]),
    "Show": ("Show", 3, [
        ("small-label", uno("Ruler")), ("small-label", uno("GridVisible")), ("small-label", uno("Navigator"))]),
    "Zoom": ("Zoom", 3, [
        ("large", uno("Zoom")), ("large", uno("Zoom100Percent")), ("small-label", uno("ZoomPage")),
        ("small-label", uno("MultiplePagesPerRow")), ("small-label", uno("ZoomPageWidth"))]),
    "Window": ("Window", 3, [
        ("large", uno("NewWindow")), ("large", uno("ViewArrangeAll")), ("large", uno("ViewSplit")),
        ("small-label", [SIDE_BY_SIDE + "toggle"]), ("small-label", [SIDE_BY_SIDE + "sync"]),
        ("small-label", [SIDE_BY_SIDE + "reset"]), ("large", uno("ViewSwitchWindowsMenu"))]),
    "Macros": ("Macros", 3, [("large", uno("ViewMacrosMenu"))]),
}
SHAPES = {"Views": [1, 1, 1, 2], "Immersive": [1, 1], "DarkMode": [1], "PageMovement": [1, 1], "Show": [3],
          "Zoom": [1, 1, 3], "Window": [1, 1, 1, 3, 1], "Macros": [1]}
# Word's label per widget command (T9w: the ribbon shows it, unless it equals LibreOffice's label)
WORD_LABELS = {
    "ReadMode": "Read Mode", "PrintLayout": "Print Layout", "BrowseView": "Web Layout", "Outline": "Outline",
    "Draft": "Draft", "FullScreen": "Focus", "ImmersiveReader": "Immersive Reader", "ChangeTheme": "Dark Mode",
    "PageMovementVertical": "Vertical", "PageMovementSideToSide": "Side to Side", "Ruler": "Ruler",
    "GridVisible": "Gridlines", "Navigator": "Navigation Pane", "Zoom": "Zoom", "Zoom100Percent": "100%",
    "ZoomPage": "One Page", "MultiplePagesPerRow": "Multiple Pages", "ZoomPageWidth": "Page Width",
    "NewWindow": "New Window", "ViewArrangeAll": "Arrange All", "ViewSplit": "Split",
    "SideBySide": "View Side by Side", "SyncScrolling": "Synchronous Scrolling",
    "ResetWindowPosition": "Reset Window Position", "ViewSwitchWindowsMenu": "Switch Windows",
    "ViewMacrosMenu": "Macros"}
# the dropdowns: two new commands. Multiple Pages is a plain button, as in Word: the editing view's multi-page
# layout (.uno:MultiplePagesPerRow, the status bar's), not print preview's .uno:ShowMultiplePages grid (W9b)
NEW_MENUS = {"ViewSwitchWindowsMenu", "ViewMacrosMenu"}
SPLITS = NEW_MENUS

# command -> (label, popup resource or None for the framework window list, popup items in order); design section 1.
# The label is also the menu's, so it is LibreOffice-style; Word's is office_label. Macro Manager is flagged
# experimental in GenericCommands.xcu, so the framework hides it unless experimental mode is on.
MENUS = {
    "ViewSwitchWindowsMenu": ("Switch Windows", None, []),
    "ViewMacrosMenu": ("Macros", "view_macros", uno("RunMacro", "MacroRecorder", "MacroManager", "BasicIDEAppear")),
}
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, View rows)
    MODE + "read": "Read Mode", MODE + "outline": "Outline", MODE + "draft": "Draft",
    MODE + "immersive": "Immersive Reader", MOVEMENT + "vertical": "Vertical",
    MOVEMENT + "sidetoside": "Side to Side", ".uno:ViewArrangeAll": "Arrange All", ".uno:ViewSplit": "Split",
    SIDE_BY_SIDE + "toggle": "View Side by Side", SIDE_BY_SIDE + "sync": "Synchronous Scrolling",
    SIDE_BY_SIDE + "reset": "Reset Window Position"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("writer"))
VIEW_SLOTS = [18, 19, 20, 21, 22]

# design section 2 "View (12)": command -> (class, menu-bar id that keeps it reachable).
# a: the same command is in the menu bar; q: it is the quick access bar's first button.
LEFT_THE_TAB = {
    "ShowWhitespace": ("a", "ShowWhitespace"),                  # View > Whitespace
    "ZoomOptimal": ("a", "ZoomOptimal"),                        # View > Zoom > Optimal View
    "Sidebar": ("a", "Sidebar"),                                # View > Sidebar
    "Menubar": ("q", "Menubar"),                                # quick access bar, first item
    "HelplinesMove": ("a", "HelplinesMove"),                    # View > Grids and Helplines > Helplines While Moving
    "GridUse": ("a", "GridUse"),                                # View > Grids and Helplines > Snap to Grid
    "ShowResolvedAnnotations": ("a", "ShowResolvedAnnotations"),  # View > Resolved Comments
    "StatusBarVisible": ("a", "StatusBarVisible"),              # View > Status Bar
    "BaselineGridVisible": ("a", "BaselineGridVisible"),        # View > Grids and Helplines > Display Baseline Grid
    "ShowBoundaries": ("a", "ShowBoundaries"),                  # View > Boundaries
    "ShowGraphics": ("a", "ShowGraphics"),                      # View > Images and Charts
    "Fieldnames": ("a", "Fieldnames"),                          # View > Field Names
}
# the stock commands that stay elsewhere (section 2, "Kept on another tab"): command -> where
KEPT_ELSEWHERE = {"ControlCodes": "Home", "SelectObject": "Home", "Marks": "Mailings", "PrintPreview": "File"}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def stock_commands(object_id):
    """The action names inside one object of the stock notebookbar.ui."""
    lines = (ROOT / "sw/uiconfig/swriter/ui/notebookbar.ui").read_text(encoding="utf-8").split("\n")
    start = next(i for i, line in enumerate(lines) if '<object' in line and 'id="%s"' % object_id in line)
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == " " * indent + "</object>")
    return set(re.findall(r'action-name">([^<]+)<', "\n".join(lines[start:end])))


def layout_urls(name):
    layout = json.loads(read("product/ui/%s.json" % name))
    return {g.item_url(i) for s in layout["sections"] for b in g.boxes_of(s) for i in b["items"]}


class WriterViewUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = WRITER.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("View Tab", self.layout["page"])
        self.assertEqual("View", self.layout["id_prefix"])
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
        # design counts: 8 sections, 26 controls, 15 real, 11 placeholders
        self.assertEqual(26, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_dropdowns_are_split_the_rest_are_plain_buttons(self):
        for item in self.items():
            expected = "split" if item["cmd"] in SPLITS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_words_label_in_office_label(self):
        # T9w: gen_ribbon turns office_label into the button's label; menus, help and tooltips keep LibreOffice's
        self.assertEqual(WORD_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def button(self, cmd):
        """The property map of the generated button `btnView<cmd>`."""
        for obj in ET.fromstring(self.office).iter("object"):
            if obj.get("id") == "btnView" + cmd:
                return {p.get("name"): p.text for p in obj.findall("property")}
        self.fail("no button for " + cmd)

    def test_the_ribbon_label_of_every_button_is_words(self):
        # what the ribbon shows is the .ui label, else the command's own label (T9w leaves the label out when
        # LibreOffice already shows Word's text)
        shown = g.shown_labels(str(ROOT), "writer")
        for cmd, word in WORD_LABELS.items():
            button = self.button(cmd)
            self.assertEqual(word, button.get("label", shown[button["action-name"]]), cmd)

    def test_the_ribbon_label_differs_from_the_menu_label_where_the_menu_is_libreoffices(self):
        labels = commands_xcu(app="writer")
        # approximate mappings (decision 20): Focus runs Full Screen
        self.assertEqual("Focus", self.button("FullScreen")["label"])
        self.assertNotEqual("Focus", labels[".uno:FullScreen"])
        self.assertEqual(".uno:FullScreen", self.button("FullScreen")["action-name"])

    def test_the_approximate_and_toggle_mappings_use_the_designed_commands(self):
        urls = {i["cmd"]: g.item_url(i) for i in self.items()}
        self.assertEqual(".uno:FullScreen", urls["FullScreen"])
        self.assertEqual(".uno:ChangeTheme", urls["ChangeTheme"])
        self.assertEqual(".uno:Navigator", urls["Navigator"])
        self.assertEqual(".uno:MultiplePagesPerRow", urls["MultiplePagesPerRow"])
        self.assertNotIn(".uno:ShowMultiplePages", urls.values())

    def test_nothing_cloud_is_on_the_page(self):
        # omitted: SharePoint > Properties
        self.assertEqual(8, len(self.layout["sections"]))
        self.assertNotIn("SharePoint", {i.get("office_label") for i in self.items()})

    def test_the_old_view_page_and_its_overflow_menu_are_gone(self):
        self.assertEqual(["Menu View"], self.layout["remove_objects"])
        for old in ('id="Menu View"', "View-ViewButton:Menu View", 'id="MenuView-'):
            self.assertNotIn(old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:View-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:View-end -->"))
        self.assertIn('id="View Tab"', self.office)  # the page itself stays, with the tab label

    def test_the_tab_keeps_its_place_and_label(self):
        # View is an existing page: writer_tabs.json does not move it and adds no page for it
        tabs = json.loads(WRITER.tabs.read_text(encoding="utf-8"))
        self.assertEqual(8, tabs["positions"]["View Tab"])
        self.assertEqual(8, tabs["positions"]["ViewLabel"])
        self.assertEqual([], [a for a in tabs["add_pages"] if a["page"] == "View Tab"])
        self.assertIn('context="TabbedWriter|ViewTabLabel">~View</property>', self.office)

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("View", {layout["id_prefix"] for layout in office.page_layouts("writer")})
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(12, len(LEFT_THE_TAB))
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_url(i) for i in self.items()} | {g.item_command(i) for i in self.items()}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertEqual(name, menu_id)
            if kind == "a":
                self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)
            else:  # q: the Menubar toggle is the quick access bar's first button, as in Calc
                self.assertEqual("q", kind)
                items = re.findall(r'xlink:href="([^"]+)"', SHORTCUTS.read_text(encoding="utf-8"))
                self.assertEqual(".uno:" + menu_id, items[0], name)
        self.assertEqual({"a": 11, "q": 1}, {k: sum(1 for v in LEFT_THE_TAB.values() if v[0] == k)
                                             for k in "aq"})

    def test_the_commands_kept_elsewhere_are_still_on_their_tab_or_in_the_menu_bar(self):
        menubar = MENUBAR.read_text(encoding="utf-8")
        select_menu = ET.parse(POPUPMENU / "home_select.xml").getroot()  # Home > Editing > Select
        tabs = {"Home": layout_urls("writer_home") | {i for i in self.menu_ids(select_menu)},
                "Mailings": layout_urls("writer_mailings")}
        for name, where in KEPT_ELSEWHERE.items():
            if where == "File":  # Print Preview stays in the File menu
                self.assertIn('menu:id=".uno:%s"' % name, menubar, name)
            else:
                self.assertIn(".uno:" + name, tabs[where], name)

    def test_every_stock_command_is_kept_dropped_to_the_menu_bar_or_on_another_tab(self):
        # the stock page and its overflow menu: whatever is not on the new page or in its menus is in the
        # leave list or kept elsewhere
        stock = stock_commands("View Tab") | stock_commands("Menu View")
        on_tab = {g.item_url(i) for i in self.items()} | {u for _l, _r, items in MENUS.values() for u in items}
        left = {".uno:" + n for n in LEFT_THE_TAB}
        elsewhere = {".uno:" + n for n in KEPT_ELSEWHERE}
        self.assertEqual(set(), stock - on_tab - left - elsewhere)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="writer")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])
            if "action" in item:
                self.assertIn(url, labels, item["cmd"])

    def test_the_new_menus_and_placeholders_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="writer"), tooltips(app="writer")
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd], cmd)
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)
        self.assertEqual(11, len(PLACEHOLDER_LABELS))

    def test_the_new_commands_have_the_image_flag(self):
        flagged = flagged_commands(app="writer")
        for cmd in MENUS:
            self.assertIn(".uno:" + cmd, flagged, cmd)
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_the_menu_items_are_known_commands(self):
        labels = commands_xcu(app="writer")
        for _label, _resource, items in MENUS.values():
            for url in items:
                if url != SEP:
                    self.assertIn(url, labels, url)

    def test_the_registry_labels_every_view_slot(self):
        registry = placeholders.registry("writer")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items() if u.startswith(".uno:View")})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        for offset in VIEW_SLOTS:
            self.assertTrue(entries[offset]["command"].startswith("View"))

    def test_every_view_placeholder_is_on_the_page_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="writer").values()}
        on_page = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, on_page, url)
            self.assertNotIn(url, controlled, url)

    def test_each_new_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        nodes = controller_nodes(app="writer")
        self.assertEqual(2, len(MENUS))
        for cmd, (_label, resource, _items) in MENUS.items():
            ours = {k: v for k, v in nodes.items()
                    if v["Command"] == ".uno:" + cmd and v["Module"] == TEXT_MODULE}
            # Calc owns both names: the Writer nodes carry the Writer suffix
            self.assertEqual({cmd + "WriterPopup", cmd + "WriterControl"}, set(ours), cmd)
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in ours.values()}
            popup = "WindowListMenuController" if resource is None else "ResourceMenuController"
            self.assertEqual({popup, "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])
            for v in ours.values():
                self.assertTrue(v["Controller"].startswith(FRAMEWORK))
            if resource is None:  # the framework's window list under the new command, no popup file
                self.assertNotIn("Value", kinds[popup])
                self.assertEqual(WINDOW_LIST, kinds[popup]["Controller"])
            else:
                self.assertEqual(resource, kinds[popup]["Value"])

    def test_multiple_pages_keeps_its_stock_controller(self):
        ours = [v for v in controller_nodes(app="writer").values() if v["Command"] == ".uno:ShowMultiplePages"]
        self.assertEqual(["com.sun.star.comp.svx.TableToolBoxControl"], [v["Controller"] for v in ours])

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        # the two dropdown commands are new to Writer: only the View page and the controller nodes name them
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
        for _label, resource, items in MENUS.values():
            if resource is None:  # R7: the window list needs no popup file
                self.assertEqual([], sorted(POPUPMENU.glob("view_switch*.xml")))
                continue
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("\tsw/uiconfig/swriter/popupmenu/" + resource + " \\\n", mk)
            self.assertEqual(items, self.menu_ids(ET.parse(path).getroot()), resource)

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

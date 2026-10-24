# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Impress Transitions tab (Preview, Transition to This Slide, Timing), the stock Layout page relabelled:
layout vs product/docs/impress-ribbon-tabs.md section 1 "Transitions", the relabel and the tab order, the one
placeholder, the deck controls, and the commands that leave the tab (section 2, "Layout (now Transitions) (15)")."""
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
LAYOUT = ROOT / "product/ui/impress_transitions.json"
OFFICE_REL = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
MENUBAR = ROOT / "sd/uiconfig/simpress/menubar/menubar.xml"
DECK = ".uno:SidebarDeck.SdSlideTransitionDeck"
PREVIEW = ".uno:PreviewEffects?Target:string=transition"


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1
# "Transitions". Size: L = large, S = small-label. PowerPoint's gallery, combo, spin and check box types are
# buttons here (design decisions 9 and 25): each one only opens the Transition deck, so all of them share its URL.
DESIGN = {
    "Preview": ("Preview", 3, [("large", [PREVIEW])]),
    "Transition": ("Transition to This Slide", 3, [("large", [DECK]), ("large", [DECK])]),
    "Timing": ("Timing", 3, [("small-label", [DECK]), ("small-label", [DECK]), ("small-label", [DECK]),
                             ("small-label", [DECK]), ("small-label", [DECK])]),
}
SHAPES = {"Preview": [1], "Transition": [1, 1], "Timing": [3, 2]}
# PowerPoint's label per item (T9w); the layout item's "cmd" (the widget command) is the key. The deck URL is used
# seven times, so each deck control has a widget command of its own (design section 3.1, "Widget ids").
POWERPOINT_LABELS = {
    "PreviewTransition": "Preview", "TransitionStyles": "Transition Styles",
    "TransitionEffectOptions": "Effect Options", "TransitionSound": "Sound", "TransitionDuration": "Duration",
    "TransitionApplyToAll": "Apply To All", "TransitionOnMouseClick": "On Mouse Click",
    "TransitionAfter": "After"}
DECK_CONTROLS = [cmd for cmd in POWERPOINT_LABELS if cmd != "PreviewTransition"]
PLACEHOLDER_LABELS = {PREVIEW: "Preview"}  # URL -> label (design section 5, the Transitions row)
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("impress"))
PREVIEW_SLOT = 11

# design section 2 "Layout (now Transitions) (15)": command -> (class, menu-bar id that keeps it reachable).
# a: the same command is in the menu bar; b: an equivalent menu-bar entry (ObjectPosition's commands are the
# Format > Arrange submenu's).
LEFT_THE_TAB = {
    "MoveSlideUp": ("a", "MoveSlideUp"), "MoveSlideDown": ("a", "MoveSlideDown"), "ShowSlide": ("a", "ShowSlide"),
    "RenameSlide": ("a", "RenameSlide"), "PresentationLayout": ("a", "PresentationLayout"),
    "DisplayMasterBackground": ("a", "DisplayMasterBackground"),
    "DisplayMasterObjects": ("a", "DisplayMasterObjects"), "ObjectAlign": ("a", "ObjectAlign"),
    "ObjectPosition": ("b", "ArrangeMenu"), "DeleteSlide": ("a", "DeleteSlide"), "ModifyPage": ("a", "ModifyPage"),
    "SelectBackground": ("a", "SelectBackground"), "InsertMasterPage": ("a", "InsertMasterPage"),
    "DeleteMasterPage": ("a", "DeleteMasterPage"), "ExpandPage": ("a", "ExpandPage"),
}
# stock Layout page and "Menu Slide" commands that are not in the leave list because the ribbon keeps them on
# another tab; Hide Slide is Slide Show's (I6a, design decision 28).
KEPT_ELSEWHERE = {
    ".uno:HideSlide": "Slide Show",
    ".uno:AssignLayout": "Home", ".uno:HeaderAndFooter": "Insert", ".uno:SlideSetup": "Design",
    ".uno:ToggleObjectRotateMode": "Home (Arrange menu)", ".uno:ImportSlideFromFile": "Insert",
    ".uno:SummaryPage": "Insert (Zoom menu)"}
ALIASES = {".uno:InsertSlide": ".uno:InsertPage", ".uno:DuplicateSlide": ".uno:InsertPage"}
MNEMONIC = re.compile(r"~(.)")


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def stock_ids(page):
    stock = ET.parse(ROOT / "sd/uiconfig/simpress/ui/notebookbar.ui").getroot()
    node = next(o for o in stock.iter("object") if o.get("id") == page)
    return node, {o.get("id") for o in node.iter("object")} - {page}


class ImpressTransitionsUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Layout", self.layout["page"])  # the stock page keeps its id
        self.assertEqual("Transitions", self.layout["id_prefix"])
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
        self.assertEqual(8, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_every_control_is_a_plain_button(self):
        # PowerPoint's gallery, dropdown, combo, spin and check box types have no LibreOffice control: each one
        # opens the deck, so none has a menu (design decisions 9 and 25)
        for item in self.items():
            self.assertEqual("button", item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_powerpoints_label_in_office_label(self):
        # T9w: gen_ribbon turns office_label into the button's label; menus, help and tooltips keep LibreOffice's
        self.assertEqual(POWERPOINT_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_the_deck_controls_share_one_url_and_differ_by_widget_command_and_icon(self):
        decks = [i for i in self.items() if g.item_url(i) == DECK]
        self.assertEqual(DECK_CONTROLS, [i["cmd"] for i in decks])
        self.assertEqual(len(decks), len({i["cmd"] for i in decks}))
        for item in decks:
            self.assertEqual(DECK, item["action"], item["cmd"])
            self.assertTrue(item.get("icon", "").startswith("cmd/"), item["cmd"])  # the deck's own icon (I5b)
            self.assertIn(item["cmd"].lower() + ".png", item["icon"], item["cmd"])  # its own name (I5b)
            self.assertIn('id="btnTransitions%s"' % item["cmd"], self.office)

    def test_the_toggling_slide_change_command_is_not_used(self):
        # .uno:SlideChangeWindow toggles the deck; a deck control must show it and keep it shown (decision 25)
        self.assertNotIn(".uno:SlideChangeWindow", {g.item_url(i) for i in self.items()})
        self.assertNotIn(".uno:SlideChangeWindow", {g.item_command(i) for i in self.items()})

    def test_the_url_variant_has_an_explicit_icon(self):
        for item in self.items():
            if "?" in g.item_url(item):
                self.assertTrue(item.get("icon"), item["cmd"])

    def test_the_overflow_menu_goes_with_the_stock_buttons(self):
        self.assertEqual(["Menu Slide"], self.layout["remove_objects"])
        _node, ids = stock_ids("Layout")
        _menu, menu_ids = stock_ids("Menu Slide")
        present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office))
        self.assertTrue(ids and menu_ids)
        self.assertEqual(set(), (ids | menu_ids | {"Menu Slide", "pmhbLayout"}) & present)
        self.assertIn('id="Layout"', self.office)  # the page itself stays, with the tab label
        self.assertEqual(1, self.office.count("<!-- product:Transitions-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Transitions-end -->"))

    def test_the_stale_valign_operation_on_the_vanished_box_is_gone(self):
        # pmhbLayout disappears with the stock page content: set_property would raise "object not found"
        tabs = json.loads(IMPRESS.tabs.read_text(encoding="utf-8"))
        ids = [op["id"] for op in tabs["properties"]]
        self.assertNotIn("pmhbLayout", ids)
        self.assertIn("Layout", ids)  # the page itself still fills the tab page
        self.assertEqual(1, ids.count("Home Tab"))

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Transitions", {layout["id_prefix"] for layout in office.page_layouts("impress")})
        self.assertEqual(office.expected_office_ui("impress"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def tab_order(self):
        root = ET.fromstring(self.office)
        book = root.find(".//object[@id='ContextContainer']")
        pages = [c.find("object").get("id") for c in book.findall("child") if c.get("type") != "tab"]
        tabs = [c.find("object") for c in book.findall("child[@type='tab']")]
        return book, pages, tabs

    def test_the_layout_tab_reads_transitions_with_mnemonic_n(self):
        tabs = json.loads(IMPRESS.tabs.read_text(encoding="utf-8"))
        self.assertEqual([{"id": "LayoutLabel", "from": "~Layout", "to": "Tra~nsitions"}], tabs["relabel"])
        self.assertRegex(self.office, r'context="TabbedImpress\|LayoutTabLabel">Tra~nsitions</property>')
        self.assertNotIn(">~Layout<", self.office)

    def test_the_new_mnemonics_are_unique_among_the_tabs(self):
        # Tra~nsitions N and ~Animations A are free in all 20 tabs of the ribbon so far (Hel~p is I8a's)
        _book, _pages, tabs = self.tab_order()
        letters = {}
        for tab in tabs:
            match = MNEMONIC.search(tab.findtext("property[@name='label']"))
            letters.setdefault(match.group(1).lower(), []).append(tab.get("id"))
        self.assertEqual(["LayoutLabel"], letters["n"])
        self.assertEqual(["AnimationsLabel"], letters["a"])

    def test_the_tab_order_is_powerpoints_up_to_view(self):
        _book, pages, tabs = self.tab_order()
        self.assertEqual(["File", "Home Tab", "Insert", "Design", "Layout", "Animations", "SlideShow", "Review",
                          "View"], pages[:9])
        self.assertEqual(["FileLabel", "HomeLabel", "InsertLabel", "DesignLabel", "LayoutLabel", "AnimationsLabel",
                          "SlideShowLabel", "ReviewLabel", "ViewLabel"], [t.get("id") for t in tabs[:9]])
        self.assertEqual("ExtensionLabel", tabs[-2].get("id"))
        self.assertEqual("ToolsLabel", tabs[-1].get("id"))

    def test_every_tab_and_page_after_design_carries_its_position(self):
        book, _pages, _tabs = self.tab_order()
        positions = {}
        for child in book.findall("child"):
            position = child.findtext("packing/property[@name='position']")
            if position is not None:  # File has none, as stock
                positions[child.find("object").get("id")] = int(position)
        want = {"Design": 3, "Layout": 4, "Animations": 5, "SlideShow": 6, "Review": 7, "View": 8, "Table": 9,
                "Image": 10, "Draw": 11, "Object": 12, "Media": 13, "Form": 14, "Master": 15, "Outline": 16,
                "3D": 17, "Extension": 18, "Tools": 19}
        for page, position in want.items():
            label = {"Layout": "LayoutLabel", "3D": "3DObjectLabel"}.get(page, page + "Label")
            self.assertEqual((position, position), (positions[page], positions[label]), page)

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(15, len(LEFT_THE_TAB))
        self.assertEqual({"a": 14, "b": 1}, {k: sum(1 for v in LEFT_THE_TAB.values() if v[0] == k) for k in "ab"})
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)
            if kind == "a":
                self.assertEqual(name, menu_id)
            else:
                self.assertNotIn('menu:id=".uno:%s"' % name, menubar, name + " has an equivalent entry: class b")

    def test_the_stock_layout_page_commands_either_stay_or_are_in_the_leave_list(self):
        # every command of the stock Layout page and its overflow menu is in the leave list, or stays on the
        # ribbon (another tab), or is an alias of a kept command
        stock = ET.parse(ROOT / "sd/uiconfig/simpress/ui/notebookbar.ui").getroot()
        commands = set()
        for wid in ("Layout", "Menu Slide"):
            node = next(o for o in stock.iter("object") if o.get("id") == wid)
            commands |= {p.text for p in node.iter("property") if p.get("name") == "action-name"}
        left = {".uno:" + name for name in LEFT_THE_TAB}
        self.assertGreater(len(commands), 20)
        for url in sorted(commands):
            if url in left or url in KEPT_ELSEWHERE or url in ALIASES:
                continue
            self.fail(url)
        for url in KEPT_ELSEWHERE:
            self.assertIn(url, commands, url)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="impress")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_placeholder_has_the_designed_label_and_tooltip(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_placeholder_has_the_image_flag(self):
        flagged = flagged_commands(app="impress")
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_the_registry_labels_the_preview_slot_and_its_transition_variant(self):
        registry = placeholders.registry("impress")
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        self.assertEqual("PreviewEffects", entries[PREVIEW_SLOT]["command"])
        self.assertEqual(["Target:string=transition", "Target:string=animation"], entries[PREVIEW_SLOT]["variants"])
        self.assertEqual("Preview", entries[PREVIEW_SLOT]["variant_labels"]["Target:string=transition"])
        self.assertEqual("Preview", placeholders.labels_by_url(registry)[PREVIEW])

    def test_the_placeholder_has_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        for url in PLACEHOLDER_LABELS:
            self.assertNotIn(url, controlled, url)

    def test_the_deck_commands_have_labels_and_no_new_controller(self):
        labels = commands_xcu(app="impress")
        self.assertIn(DECK, labels)
        self.assertNotIn(DECK, {v["Command"] for v in controller_nodes(app="impress").values()})

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

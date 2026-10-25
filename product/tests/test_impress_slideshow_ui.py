# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Impress Slide Show tab (Start Slide Show, Set Up, Monitors), the stock SlideShow page regenerated:
layout vs product/docs/impress-ribbon-tabs.md section 1 "Slide Show", the three placeholders, the three Set Up
Slide Show controls, Hide Slide, and the commands that leave the tab (section 2, "Slide Show (2)")."""
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
LAYOUT = ROOT / "product/ui/impress_slideshow.json"
OFFICE_REL = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
MENUBAR = ROOT / "sd/uiconfig/simpress/menubar/menubar.xml"
DIALOG = ".uno:PresentationDialog"
RECORD = ".uno:SlideShowRecord"
NARRATIONS = ".uno:SlideShowOption?Option:string=narrations"
MEDIA_CONTROLS = ".uno:SlideShowOption?Option:string=mediacontrols"

# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1
# "Slide Show". Size: L = large, S = small-label. Custom Slide Show is a dropdown in PowerPoint and Record a split:
# both are plain large buttons here (no menu to open, controller ruling 23); the check boxes and the combo that
# only open the Set Up Slide Show dialog are buttons with PowerPoint's label (design decision 25).
DESIGN = {
    "StartSlideShow": ("Start Slide Show", 3, [("large", [".uno:Presentation"]),
                                               ("large", [".uno:PresentationCurrentSlide"]),
                                               ("large", [".uno:CustomShowDialog"])]),
    "SetUp": ("Set Up", 3, [("large", [DIALOG]), ("large", [".uno:HideSlide"]), ("large", [".uno:RehearseTimings"]),
                            ("large", [RECORD]), ("small-label", [NARRATIONS]), ("small-label", [DIALOG]),
                            ("small-label", [MEDIA_CONTROLS])]),
    "Monitors": ("Monitors", 3, [("small-label", [DIALOG]), ("small-label", [DIALOG])]),
}
SHAPES = {"StartSlideShow": [1, 1, 1], "SetUp": [1, 1, 1, 1, 3], "Monitors": [2]}
# PowerPoint's label per item (T9w); the layout item's "cmd" (the widget command) is the key
POWERPOINT_LABELS = {
    "Presentation": "From Beginning", "PresentationCurrentSlide": "From Current Slide",
    "CustomShowDialog": "Custom Slide Show", "PresentationDialog": "Set Up Slide Show", "HideSlide": "Hide Slide",
    "RehearseTimings": "Rehearse Timings", "SlideShowRecord": "Record", "SlideShowPlayNarrations": "Play Narrations",
    "SlideShowUseTimings": "Use Timings", "SlideShowShowMediaControls": "Show Media Controls",
    "SlideShowMonitor": "Monitor", "SlideShowPresenterView": "Use Presenter View"}
# the three controls that only open the Set Up Slide Show dialog: a widget command of their own each (decision 25)
DIALOG_CONTROLS = ["SlideShowUseTimings", "SlideShowMonitor", "SlideShowPresenterView"]
PLACEHOLDER_LABELS = {RECORD: "Record", NARRATIONS: "Play Narrations", MEDIA_CONTROLS: "Show Media Controls"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("impress"))
RECORD_SLOT, OPTION_SLOT = 13, 14

# design section 2 "Slide Show (2)": command -> (class, menu-bar id that keeps it reachable); both class a.
LEFT_THE_TAB = {"SlideChangeWindow": ("a", "SlideChangeWindow"), "Remote": ("a", "Remote")}
# stock SlideShow page and "Menu Slide Show" commands that are not in the leave list because the ribbon keeps them
# on another tab (the menu bar has them all)
KEPT_ELSEWHERE = {
    ".uno:CustomAnimation": "Animations (Animation Pane)", ".uno:OutputQualityColor": "View (Color/Grayscale)",
    ".uno:OutputQualityGrayscale": "View (Color/Grayscale)", ".uno:PresentationMinimizer": "Tools"}


def stock_commands(*page_ids):
    stock = ET.parse(ROOT / "sd/uiconfig/simpress/ui/notebookbar.ui").getroot()
    commands, ids = set(), set()
    for wid in page_ids:
        node = next(o for o in stock.iter("object") if o.get("id") == wid)
        commands |= {p.text for p in node.iter("property") if p.get("name") == "action-name"}
        ids |= {o.get("id") for o in node.iter("object")}
    return commands, ids


class ImpressSlideShowUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("SlideShow", self.layout["page"])  # the stock page keeps its id
        self.assertEqual("SlideShow", self.layout["id_prefix"])
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
        self.assertEqual(12, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_every_control_is_a_plain_button_without_an_arrow(self):
        # ruling 23: Custom Slide Show and Record have no menu, so no arrow
        for item in self.items():
            self.assertEqual("button", item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_powerpoints_label_in_office_label(self):
        # T9w: gen_ribbon turns office_label into the button's label; menus, help and tooltips keep LibreOffice's
        self.assertEqual(POWERPOINT_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_the_set_up_dialog_has_four_controls_with_distinct_widget_commands(self):
        dialog = [i for i in self.items() if g.item_url(i) == DIALOG]
        self.assertEqual(["PresentationDialog"] + DIALOG_CONTROLS, [i["cmd"] for i in dialog])
        self.assertEqual(4, len({i["cmd"] for i in dialog}))
        self.assertNotIn("action", dialog[0])  # Set Up Slide Show is the real command
        for item in dialog[1:]:
            self.assertEqual(DIALOG, item["action"], item["cmd"])
            self.assertEqual("cmd/sc_%s.png" % item["cmd"].lower(), item["icon"], item["cmd"])  # shared URL: own icon
            self.assertIn('id="btnSlideShow%s"' % item["cmd"], self.office)

    def test_hide_slide_is_the_real_command_without_an_action(self):
        # decision 28: one Hide Slide toggle; Show Slide stays in Slide > Show Slide
        item = next(i for i in self.items() if i["cmd"] == "HideSlide")
        self.assertEqual(".uno:HideSlide", g.item_url(item))
        self.assertNotIn("action", item)
        self.assertNotIn(".uno:ShowSlide", {g.item_url(i) for i in self.items()})
        self.assertIn('menu:id=".uno:ShowSlide"', MENUBAR.read_text(encoding="utf-8"))

    def test_the_url_variants_have_an_explicit_icon_that_exists(self):
        manifest = json.loads((ROOT / "product/icons/manifest.json").read_text(encoding="utf-8"))
        for item in self.items():
            if "?" in g.item_url(item):
                self.assertTrue(item.get("icon"), item["cmd"])
            if "icon" in item:
                # a Boost manifest entry of that name (test_impress_icons checks the built members)
                name = item["icon"].removeprefix("cmd/").removeprefix("sc_").removesuffix(".png")
                self.assertIn(name, {e["name"] for e in manifest["icons"]}, item["cmd"])

    def test_the_overflow_menu_goes_with_the_stock_buttons(self):
        self.assertEqual(["Menu Slide Show"], self.layout["remove_objects"])
        _commands, ids = stock_commands("SlideShow")
        _menu, menu_ids = stock_commands("Menu Slide Show")
        present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office))
        self.assertTrue(ids and menu_ids)
        self.assertEqual(set(), ((ids | menu_ids | {"Menu Slide Show"}) - {"SlideShow", "pmhbSlideShow"}) & present)
        self.assertIn('id="SlideShow"', self.office)  # the page itself stays, with the tab label
        self.assertEqual(1, self.office.count("<!-- product:SlideShow-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:SlideShow-end -->"))

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("SlideShow", {layout["id_prefix"] for layout in office.page_layouts("impress")})
        self.assertEqual(office.expected_office_ui("impress"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_slide_show_follows_animations_and_precedes_review(self):
        root = ET.fromstring(self.office)
        book = root.find(".//object[@id='ContextContainer']")
        pages = [c.find("object").get("id") for c in book.findall("child") if c.get("type") != "tab"]
        tabs = [c.find("object").get("id") for c in book.findall("child[@type='tab']")]
        self.assertEqual(["Animations", "SlideShow", "Review"], pages[5:8])
        self.assertEqual(["AnimationsLabel", "SlideShowLabel", "ReviewLabel"], tabs[5:8])
        self.assertRegex(self.office, r'context="TabbedImpress\|SlideTabLabel">~Slide Show</property>')

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(2, len(LEFT_THE_TAB))
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()} | {g.item_url(i) for i in self.items()}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertEqual("a", kind)
            self.assertEqual(name, menu_id)
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)

    def test_the_stock_slide_show_page_commands_either_stay_or_are_in_the_leave_list(self):
        # every command of the stock SlideShow page and its overflow menu is on this page, or in the leave list,
        # or stays on the ribbon (another tab); all of them are in the menu bar
        commands, _ = stock_commands("SlideShow", "Menu Slide Show")
        on_tab = {g.item_url(i) for i in self.items()}
        left = {".uno:" + name for name in LEFT_THE_TAB}
        menubar = MENUBAR.read_text(encoding="utf-8")
        self.assertGreater(len(commands), 8)
        for url in sorted(commands):
            self.assertTrue(url in on_tab or url in left or url in KEPT_ELSEWHERE, url)
            self.assertIn('menu:id="%s"' % url, menubar, url)
        for url in KEPT_ELSEWHERE:
            self.assertIn(url, commands, url)
        for url in left:
            self.assertIn(url, commands, url)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="impress")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_placeholders_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        self.assertEqual(3, len(PLACEHOLDER_LABELS))
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_placeholders_have_the_image_flag(self):
        flagged = flagged_commands(app="impress")
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_the_registry_labels_the_record_and_option_slots(self):
        registry = placeholders.registry("impress")
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        self.assertEqual("SlideShowRecord", entries[RECORD_SLOT]["command"])
        self.assertEqual("Record", entries[RECORD_SLOT]["label"])
        self.assertEqual("SlideShowOption", entries[OPTION_SLOT]["command"])
        self.assertEqual(["Option:string=narrations", "Option:string=mediacontrols"], entries[OPTION_SLOT]["variants"])
        self.assertEqual({"Option:string=narrations": "Play Narrations",
                          "Option:string=mediacontrols": "Show Media Controls"},
                         entries[OPTION_SLOT]["variant_labels"])
        labels = placeholders.labels_by_url(registry)
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)

    def test_no_command_of_the_tab_has_a_new_controller_or_popup(self):
        # the dropdown-looking controls open the real dialogs; a controller works only under its own command
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        for item in self.items():
            self.assertNotIn(g.item_url(item), controlled, item["cmd"])
            self.assertNotIn(g.item_command(item), controlled, item["cmd"])

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

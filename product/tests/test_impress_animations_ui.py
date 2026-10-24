# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Impress Animations tab (Preview, Animation, Advanced Animation, Timing), a new page after Transitions:
layout vs product/docs/impress-ribbon-tabs.md section 1 "Animations", the added page and its tab label, the
two placeholders, the deck controls, and the one toggle (Animation Pane)."""
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
LAYOUT = ROOT / "product/ui/impress_animations.json"
OFFICE_REL = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
DECK = ".uno:SidebarDeck.SdCustomAnimationDeck"
PREVIEW = ".uno:PreviewEffects?Target:string=animation"
PANE = ".uno:CustomAnimation"
PAINTER = ".uno:AnimationPainter"


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1
# "Animations". Size: L = large, S = small-label. The gallery, dropdown, combo and spin types are buttons that
# open the Animation deck (design decisions 9 and 25); Preview is a split in PowerPoint and a plain placeholder
# button here (a placeholder has no menu); Animation Pane is the one exact control, a toggle.
DESIGN = {
    "Preview": ("Preview", 3, [("large", [PREVIEW])]),
    "Animation": ("Animation", 3, [("large", [DECK]), ("large", [DECK])]),
    "Advanced": ("Advanced Animation", 3, [("large", [DECK]), ("small-label", [PANE]), ("small-label", [DECK]),
                                           ("small-label", [PAINTER])]),
    "Timing": ("Timing", 3, [("small-label", [DECK]), ("small-label", [DECK]), ("small-label", [DECK]),
                             ("small-label", [DECK]), ("small-label", [DECK])]),
}
SHAPES = {"Preview": [1], "Animation": [1, 1], "Advanced": [1, 3], "Timing": [3, 2]}
# PowerPoint's label per item (T9w); the layout item's "cmd" (the widget command) is the key
POWERPOINT_LABELS = {
    "PreviewAnimation": "Preview", "AnimationStyles": "Animation Styles",
    "AnimationEffectOptions": "Effect Options", "AddAnimation": "Add Animation", "CustomAnimation": "Animation Pane",
    "AnimationTrigger": "Trigger", "AnimationPainter": "Animation Painter", "AnimationStart": "Start",
    "AnimationDuration": "Duration", "AnimationDelay": "Delay", "AnimationMoveEarlier": "Move Earlier",
    "AnimationMoveLater": "Move Later"}
DECK_CONTROLS = ["AnimationStyles", "AnimationEffectOptions", "AddAnimation", "AnimationTrigger", "AnimationStart",
                 "AnimationDuration", "AnimationDelay", "AnimationMoveEarlier", "AnimationMoveLater"]
PLACEHOLDER_LABELS = {PREVIEW: "Preview", PAINTER: "Animation Painter"}  # URL -> label (design section 5)
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("impress"))
PREVIEW_SLOT, PAINTER_SLOT = 11, 12
TAB_ADDED = {"page": "Animations", "prefix": "Animations", "after_tab": "LayoutLabel", "position": 5,
             "tab_id": "AnimationsLabel", "label": "~Animations", "context": "TabbedImpress|AnimationsTabLabel"}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ImpressAnimationsUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Animations", self.layout["page"])
        self.assertEqual("Animations", self.layout["id_prefix"])
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

    def test_every_control_is_a_plain_button(self):
        for item in self.items():
            self.assertEqual("button", item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_powerpoints_label_in_office_label(self):
        self.assertEqual(POWERPOINT_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_the_deck_controls_share_one_url_and_differ_by_widget_command_and_icon(self):
        decks = [i for i in self.items() if g.item_url(i) == DECK]
        self.assertEqual(DECK_CONTROLS, [i["cmd"] for i in decks])
        self.assertEqual(len(decks), len({i["cmd"] for i in decks}))
        for item in decks:
            self.assertEqual(DECK, item["action"], item["cmd"])
            self.assertTrue(item.get("icon", "").startswith("cmd/"), item["cmd"])  # the deck's own icon (I5b)
            self.assertIn("sidebardeck.sdcustomanimationdeck", item["icon"], item["cmd"])
            self.assertIn('id="btnAnimations%s"' % item["cmd"], self.office)

    def test_animation_pane_is_the_exact_toggle_and_the_others_do_not_toggle(self):
        by_cmd = {i["cmd"]: i for i in self.items()}
        self.assertNotIn("action", by_cmd["CustomAnimation"])
        self.assertEqual(PANE, g.item_url(by_cmd["CustomAnimation"]))
        self.assertEqual(1, [g.item_command(i) for i in self.items()].count(PANE))

    def test_the_url_variant_has_an_explicit_icon(self):
        for item in self.items():
            if "?" in g.item_url(item):
                self.assertTrue(item.get("icon"), item["cmd"])

    def test_the_page_is_added_after_transitions_at_position_5(self):
        tabs = json.loads(IMPRESS.tabs.read_text(encoding="utf-8"))
        self.assertIn(TAB_ADDED, tabs["add_pages"])
        self.assertRegex(self.office, r'context="TabbedImpress\|AnimationsTabLabel">~Animations</property>')
        self.assertEqual(1, self.office.count("<!-- product:Animations-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Animations-end -->"))
        self.assertEqual(5, tabs["add_pages"][0]["position"])
        # the pages after it moved up by one
        self.assertEqual({"SlideShow": 6, "SlideShowLabel": 6, "Review": 7, "ReviewLabel": 7, "View": 8,
                          "ViewLabel": 8, "Tools": 19, "ToolsLabel": 19},
                         {k: tabs["positions"][k] for k in ("SlideShow", "SlideShowLabel", "Review", "ReviewLabel",
                                                            "View", "ViewLabel", "Tools", "ToolsLabel")})

    def test_the_animations_tab_follows_the_transitions_tab(self):
        root = ET.fromstring(self.office)
        book = root.find(".//object[@id='ContextContainer']")
        labels = [c.find("object").get("id") for c in book.findall("child[@type='tab']")]
        self.assertEqual("AnimationsLabel", labels[labels.index("LayoutLabel") + 1])
        self.assertEqual("SlideShowLabel", labels[labels.index("AnimationsLabel") + 1])
        self.assertEqual("Animations", self.layout["page"])

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Animations", {layout["id_prefix"] for layout in office.page_layouts("impress")})
        self.assertEqual(office.expected_office_ui("impress"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="impress")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_placeholders_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        self.assertEqual({PREVIEW: "Preview", PAINTER: "Animation Painter"}, PLACEHOLDER_LABELS)
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_placeholders_have_the_image_flag(self):
        flagged = flagged_commands(app="impress")
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_the_registry_labels_the_preview_and_painter_slots(self):
        registry = placeholders.registry("impress")
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        self.assertEqual("PreviewEffects", entries[PREVIEW_SLOT]["command"])
        self.assertEqual({"Target:string=transition": "Preview", "Target:string=animation": "Preview"},
                         entries[PREVIEW_SLOT]["variant_labels"])
        self.assertEqual(("AnimationPainter", "Animation Painter"),
                         (entries[PAINTER_SLOT]["command"], entries[PAINTER_SLOT]["label"]))
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual("Preview", by_url[PREVIEW])
        self.assertEqual("Animation Painter", by_url[PAINTER])

    def test_the_placeholders_have_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        for url in PLACEHOLDER_LABELS:
            self.assertNotIn(url, controlled, url)

    def test_the_real_commands_keep_their_stock_labels_and_add_no_controller(self):
        labels = commands_xcu(app="impress")
        for url in (DECK, PANE):
            self.assertIn(url, labels)
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        self.assertNotIn(DECK, controlled)
        self.assertNotIn(PANE, controlled)

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

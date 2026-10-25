# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Impress Help tab (new page, last tab): layout vs product/docs/impress-ribbon-tabs.md section 1 "Help", the
Feedback placeholder, and the tab operation that adds the page after Tools with the mnemonic P."""
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
LAYOUT = ROOT / "product/ui/impress_help.json"
OFFICE_REL = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
FEEDBACK = ".uno:HelpFeedback"
TAB_ADDED = {"page": "Help", "prefix": "Help", "after_tab": "ToolsLabel", "position": 20,
             "tab_id": "HelpLabel", "label": "Hel~p", "context": "TabbedImpress|HelpTabLabel"}

# section -> (caption, rows, [(style, [url]) per toolbox]); design section 1 "Help". Every button is large.
DESIGN = {"Help": ("Help", 3, [("large", [url]) for url in (
    ".uno:HelpIndex", ".uno:QuestionAnswers", FEEDBACK, ".uno:Documentation", ".uno:WhatsNew")])}
POWERPOINT_LABELS = {"HelpIndex": "Help", "QuestionAnswers": "Contact Support", "HelpFeedback": "Feedback",
                     "Documentation": "Show Training", "WhatsNew": "What's New"}
PLACEHOLDER_LABELS = placeholders.drop_implemented({FEEDBACK: "Feedback"}, placeholders.registry("impress"))
HELP_SLOT = 23


class ImpressHelpUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def items(self):
        return [i for s in self.layout["sections"] for b in g.boxes_of(s) for i in b["items"]]

    def test_page_and_section_follow_the_design(self):
        self.assertEqual("Help", self.layout["page"])
        self.assertEqual("Help", self.layout["id_prefix"])
        self.assertEqual("TabbedImpress", self.layout["context"])
        self.assertNotIn("remove_objects", self.layout)  # a new page has no stock buttons
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        section = self.layout["sections"][0]
        caption, rows, controls = DESIGN["Help"]
        self.assertEqual((caption, rows), (section["caption"], section["rows"]))
        self.assertEqual(controls, [(b["style"], [g.item_url(i) for i in b["items"]]) for b in g.boxes_of(section)])
        self.assertEqual([1] * 5, [len(c) for c in section["columns"]])

    def test_every_item_is_a_plain_button_with_powerpoints_label(self):
        self.assertEqual(POWERPOINT_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})
        for item in self.items():
            self.assertEqual("button", item.get("kind", "button"), item["cmd"])

    def test_contact_support_is_the_real_online_help_command(self):
        # decision 30: Contact Support is real, as Calc's and Writer's
        self.assertIn(".uno:QuestionAnswers", [g.item_url(i) for i in self.items()])
        self.assertNotIn(".uno:QuestionAnswers", placeholders.all_urls(placeholders.registry("impress")))

    def test_the_page_is_added_after_tools_at_position_20(self):
        tabs = json.loads(IMPRESS.tabs.read_text(encoding="utf-8"))
        self.assertIn(TAB_ADDED, tabs["add_pages"])
        self.assertRegex(self.office, r'context="TabbedImpress\|HelpTabLabel">Hel~p</property>')
        self.assertEqual(1, self.office.count("<!-- product:Help-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Help-end -->"))

    def test_help_is_the_last_tab_and_page_after_tools(self):
        root = ET.fromstring(self.office)
        book = root.find(".//object[@id='ContextContainer']")
        pages = [c.find("object").get("id") for c in book.findall("child") if c.get("type") != "tab"]
        tabs = [c.find("object").get("id") for c in book.findall("child[@type='tab']")]
        self.assertEqual(["Extension", "Tools", "Help"], pages[-3:])
        self.assertEqual(["ExtensionLabel", "ToolsLabel", "HelpLabel"], tabs[-3:])
        positions = {c.find("object").get("id"): c.findtext("packing/property[@name='position']")
                     for c in book.findall("child") if c.find("packing/property[@name='position']") is not None}
        self.assertEqual(("20", "20"), (positions["Help"], positions["HelpLabel"]))

    def test_the_new_mnemonic_is_unique_among_the_tabs(self):
        root = ET.fromstring(self.office)
        book = root.find(".//object[@id='ContextContainer']")
        letters = {}
        for tab in (c.find("object") for c in book.findall("child[@type='tab']")):
            match = re.search(r"~(\w)", tab.findtext("property[@name='label']") or "")
            if match:
                letters.setdefault(match.group(1).lower(), []).append(tab.get("id"))
        self.assertEqual(["HelpLabel"], letters["p"])

    def test_the_help_tab_follows_the_other_tabs_in_the_office_ui(self):
        self.assertIn("Help", {layout["id_prefix"] for layout in office.page_layouts("impress")})
        self.assertEqual(office.expected_office_ui("impress"), self.office)
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_every_command_has_a_label_and_the_placeholder_a_tooltip(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        for item in self.items():
            self.assertIn(g.item_url(item), labels, item["cmd"])
        self.assertEqual({FEEDBACK: "Feedback"}, PLACEHOLDER_LABELS)
        self.assertEqual("Feedback", labels[FEEDBACK])
        self.assertEqual("Feedback (not available yet)", tips[FEEDBACK])
        self.assertIn(FEEDBACK, flagged_commands(app="impress"))

    def test_the_registry_labels_the_feedback_slot_and_it_has_no_controller(self):
        entries = {e["offset"]: e for e in placeholders.load_all(placeholders.registry("impress"))}
        self.assertEqual(("HelpFeedback", "Feedback"), (entries[HELP_SLOT]["command"], entries[HELP_SLOT]["label"]))
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        self.assertNotIn(FEEDBACK, controlled)

    def test_suppr_has_an_entry_for_every_button(self):
        suppr = IMPRESS.suppr.read_text(encoding="utf-8")
        for wid in g.ids_of(self.layout):
            if wid.startswith("btn"):
                self.assertRegex(suppr, re.escape(OFFICE_REL + ":") + r"//GtkToolButton\[@id='"
                                 + re.escape(wid) + r"'\] button-no-label")

    def test_regenerating_the_page_changes_nothing(self):
        regenerated = g.splice(self.office, self.layout, g.emit_page(self.layout))
        self.assertEqual(self.office, regenerated)
        suppr = IMPRESS.suppr.read_text(encoding="utf-8")
        self.assertEqual(suppr, g.sync_suppr(suppr, OFFICE_REL, regenerated))


if __name__ == "__main__":
    unittest.main()

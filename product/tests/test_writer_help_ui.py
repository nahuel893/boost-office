# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Writer Help tab: layout vs product/docs/writer-ribbon-tabs.md section 1 "Help", its place (last, position
18, after Tools), the placeholder, the labels and the widget ids. Help is a new page, so no command leaves it."""
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
LAYOUT = ROOT / "product/ui/writer_help.json"
OFFICE_REL = "sw/uiconfig/swriter/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sw/uiconfig/swriter/popupmenu"

# section -> (caption, rows, [(style, [url]) per toolbox in document order]); design section 1 "Help"
DESIGN = {
    "Help": ("Help", 3, [("large", [".uno:HelpIndex"]), ("large", [".uno:QuestionAnswers"]),
                         ("large", [".uno:HelpFeedback"]), ("large", [".uno:Documentation"]),
                         ("large", [".uno:WhatsNew"])]),
}
# Word's label per widget command (T9w)
WORD_LABELS = {"HelpIndex": "Help", "QuestionAnswers": "Contact Support", "HelpFeedback": "Feedback",
               "Documentation": "Show Training", "WhatsNew": "What's New"}
PLACEHOLDER_LABELS = {".uno:HelpFeedback": "Feedback"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("writer"))
HELP_SLOTS = [23]
# the tab, as writer_tabs.json adds it: position 18, after Tools (17)
TAB = {"page": "Help Tab", "prefix": "Help", "after_tab": "ToolsLabel", "position": 18,
       "tab_id": "HelpLabel", "context": "TabbedWriter|HelpTabLabel"}
# Every Writer tab label's access key. P (Print) and L (Layout) are taken at the same time as Help, H is Home's:
# the Help label uses E (H~elp), the one letter of "Help" that no other label uses.
TAB_LABELS = {"FileTabLabel": "~File", "HomeTabLabel": "~Home", "InsertTabLabel": "~Insert",
              "DesignTabLabel": "Desi~gn", "LayoutTabLabel": "~Layout", "ReferencesTabLabel": "Reference~s",
              "MailingsTabLabel": "M~ailings", "ReviewTabLabel": "~Review", "ViewTabLabel": "~View",
              "TableTabLabel": "~Table", "ImageTabLabel": "Ima~ge", "DrawTabLabel": "~Draw",
              "ObjectTabLabel": "~Object", "MediaTabLabel": "~Media", "PrintTabLabel": "~Print",
              "FormTabLabel": "Fo~rm", "ExtensionLabel": "E~xtension", "ToolsTabLabel": "~Tools",
              "HelpTabLabel": "H~elp"}


class WriterHelpUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = WRITER.office.read_text(encoding="utf-8")
        self.tabs = json.loads(WRITER.tabs.read_text(encoding="utf-8"))

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Help Tab", self.layout["page"])
        self.assertEqual("Help", self.layout["id_prefix"])
        self.assertEqual("TabbedWriter", self.layout["context"])
        self.assertEqual([], self.layout.get("remove_objects", []))
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        for section in self.layout["sections"]:
            caption, rows, _ = DESIGN[section["name"]]
            self.assertEqual(caption, section["caption"])
            self.assertEqual(rows, section["rows"])

    def test_every_control_is_there_in_order_as_a_large_button(self):
        for section in self.layout["sections"]:
            got = [(b["style"], [g.item_url(i) for i in b["items"]]) for b in self.boxes(section)]
            self.assertEqual(DESIGN[section["name"]][2], got, section["name"])
            self.assertEqual([1] * 5, [len(c) for c in section["columns"]])  # one control per column
        self.assertEqual(5, len(self.items()))  # design counts: 1 section, 5 controls, 4 real, 1 placeholder

    def test_no_item_is_a_dropdown_or_a_url_variant(self):
        for item in self.items():
            self.assertEqual("button", item.get("kind", "button"), item["cmd"])
            self.assertNotIn("action", item, item["cmd"])
            self.assertNotIn("icon", item, item["cmd"])  # icons resolve by command name

    def test_every_item_keeps_words_label_in_office_label(self):
        self.assertEqual(WORD_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_the_ribbon_label_of_every_button_is_words(self):
        shown = g.shown_labels(str(ROOT), "writer")
        for obj in ET.fromstring(self.office).iter("object"):
            for cmd, word in WORD_LABELS.items():
                if obj.get("id") == "btnHelp" + cmd:
                    props = {p.get("name"): p.text for p in obj.findall("property")}
                    self.assertEqual(word, props.get("label", shown[props["action-name"]]), cmd)

    def test_the_help_page_is_generated_between_its_markers(self):
        self.assertEqual(1, self.office.count("<!-- product:Help-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Help-end -->"))
        body = self.office.split("<!-- product:Help-begin -->")[1].split("<!-- product:Help-end -->")[0]
        self.assertIn('id="pmhbHelp"', body)
        self.assertEqual(5, body.count('class="GtkToolButton"'))
        self.assertEqual(1, body.count('class="GtkLabel"'))  # one caption
        self.assertIn('id="lbHelpHelp"', body)
        self.assertIn(">Help<", body)

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Help", {layout["id_prefix"] for layout in office.page_layouts("writer")})
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_help_is_the_last_tab_at_position_18_after_tools(self):
        adds = [a for a in self.tabs["add_pages"] if a["page"] == "Help Tab"]
        self.assertEqual(1, len(adds))
        for key, value in TAB.items():
            self.assertEqual(value, adds[0][key], key)
        self.assertEqual(17, self.tabs["positions"]["Tools Tab"])
        self.assertEqual(17, self.tabs["positions"]["ToolsLabel"])
        self.assertEqual(18, max(a["position"] for a in self.tabs["add_pages"]))
        self.assertEqual(18, max(max(self.tabs["positions"].values()), 18))
        # in the generated .ui the page and its tab label both sit at position 18, after Tools
        root = ET.fromstring(self.office)
        notebook = next(o for o in root.iter("object") if o.get("id") == "ContextContainer")
        def positions(kind):
            found = []
            for child in notebook.findall("child"):
                position = child.find("packing/property[@name='position']")
                if child.get("type") == kind and position is not None:
                    found.append((child.find("object").get("id"), position.text))
            return found
        pages, tabs = positions(None), positions("tab")
        self.assertEqual(("Help Tab", "18"), max(pages, key=lambda p: int(p[1])))
        self.assertEqual(("HelpLabel", "18"), max(tabs, key=lambda p: int(p[1])))
        # File is first and has no explicit position; every other page and label has its own, 1..18
        self.assertEqual(list(range(1, 19)), sorted(int(p) for _id, p in pages))
        self.assertEqual(list(range(1, 19)), sorted(int(p) for _id, p in tabs))

    def test_the_tab_label_has_an_access_key_no_other_label_shares(self):
        got = dict(re.findall(r'context="TabbedWriter\|(\w+)">([^<]*~[^<]*)</property>', self.office))
        self.assertEqual(TAB_LABELS, got)
        keys = {name: label.split("~")[1][0].lower() for name, label in got.items()}
        help_key = keys.pop("HelpTabLabel")
        self.assertEqual("e", help_key)
        # E is not the access key of any other tab (Extension is X), so Help never clashes, with or without a
        # contextual tab (Print P, Media M, Table T ...)
        self.assertNotIn(help_key, keys.values())

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="writer")
        for item in self.items():
            self.assertIn(g.item_url(item), labels, item["cmd"])

    def test_the_placeholder_has_the_image_flag_label_and_tooltip(self):
        labels, tips, flagged = commands_xcu(app="writer"), tooltips(app="writer"), flagged_commands(app="writer")
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)
            self.assertIn(url, flagged, url)
        self.assertEqual(1, len(PLACEHOLDER_LABELS))

    def test_labels_follow_the_design(self):
        labels = commands_xcu(app="writer")
        for url, label in {".uno:HelpIndex": "%PRODUCTNAME Help", ".uno:QuestionAnswers": "Get Help Online",
                           ".uno:Documentation": "User Guides", ".uno:WhatsNew": "What's New"}.items():
            self.assertEqual(label, labels[url].replace("~", ""), url)

    def test_the_registry_labels_the_help_slot(self):
        registry = placeholders.registry("writer")
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        self.assertEqual(["HelpFeedback"], [entries[o]["command"] for o in HELP_SLOTS])
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in placeholders.labels_by_url(registry).items()
                                              if u.startswith(".uno:Help")})

    def test_the_placeholder_is_on_the_page_and_has_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="writer").values()}
        used = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, used, url)
            self.assertNotIn(url, controlled, url)

    def test_the_page_adds_no_dropdown_command_or_popup_file(self):
        self.assertEqual([], sorted(POPUPMENU.glob("help_*.xml")))
        self.assertNotIn("popupmenu/help_", (ROOT / "sw/UIConfig_swriter.mk").read_text(encoding="utf-8"))

    def test_nothing_leaves_the_help_tab(self):
        # the page is new: no stock page or menu is removed, so no command leaves it
        self.assertEqual([], self.layout.get("remove_objects", []))
        self.assertNotIn("Help Tab", self.tabs.get("positions", {}))

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

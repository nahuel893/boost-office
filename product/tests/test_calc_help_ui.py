# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Help tab: layout vs product/docs/design/calc-help-tab-layout.txt, labels, placeholders,
the widget ids (R12) and the buttons that stay elsewhere."""
import json
import re
import unittest
from pathlib import Path

from product.tests import office, placeholders
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands, tooltips
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_help.json"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
SUPPR = ROOT / "solenv/sanitizers/ui/modules/scalc.suppr"

# section -> (caption, [command per large toolbox in document order])
DESIGN = {
    "Help": ("Help", [".uno:HelpIndex", ".uno:QuestionAnswers", ".uno:HelpFeedback",
                      ".uno:Documentation", ".uno:WhatsNew"]),
    "Community": ("Community", [".uno:GetInvolved", ".uno:HelpBlog"]),
}
PLACEHOLDER_LABELS = {".uno:HelpFeedback": "Feedback", ".uno:HelpBlog": "Blog"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS)  # implemented ones are no placeholder
SHOWN_LABELS = {".uno:HelpIndex": "%PRODUCTNAME Help", ".uno:QuestionAnswers": "Get Help Online",
                ".uno:Documentation": "User Guides", ".uno:WhatsNew": "What's New",
                ".uno:GetInvolved": "Get Involved"}
HELP_SLOTS = [419, 420]
# the Help menu entries that Excel has no button for stay in the menu bar
STAY_IN_THE_MENU = ["ExtendedHelp", "TipOfTheDay", "CommandPopup", "SafeMode", "Donation", "ShowLicense", "About"]


# Excel's label per item where it differs from LibreOffice's (T9w: the ribbon shows it). Source: the Excel
# control of each row in product/docs/design/calc-help-tab-layout.txt
EXCEL_LABELS = {".uno:HelpIndex": "Help", ".uno:QuestionAnswers": "Contact Support",
    ".uno:Documentation": "Show Training", ".uno:GetInvolved": "Community"}


class CalcHelpUiTest(unittest.TestCase):

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
        got = {g.item_url(i): i["office_label"] for s in self.layout["sections"] for b in g.boxes_of(s)
               for i in b["items"] if "office_label" in i}
        self.assertEqual(EXCEL_LABELS, got)

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("phbHelp", self.layout["page"])
        self.assertEqual("Help", self.layout["id_prefix"])
        self.assertEqual("TabbedCalc", self.layout["context"])
        self.assertEqual([], self.layout["remove_objects"])
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        for section in self.layout["sections"]:
            self.assertEqual(DESIGN[section["name"]][0], section["caption"])
            self.assertEqual(3, section["rows"], section["name"])

    def test_every_control_is_there_in_order_as_a_large_button(self):
        for section in self.layout["sections"]:
            got = [(b["style"], [g.item_url(i) for i in b["items"]]) for b in self.boxes(section)]
            self.assertEqual([("large", [c]) for c in DESIGN[section["name"]][1]], got, section["name"])
            # one control per column: five and two columns, no menus, no launchers
            self.assertEqual([1] * len(DESIGN[section["name"]][1]), [len(c) for c in section["columns"]])
        self.assertEqual(7, len(self.items()))

    def test_no_item_is_a_dropdown_or_a_url_variant(self):
        for item in self.items():
            self.assertEqual("button", item.get("kind", "button"), item["cmd"])
            self.assertNotIn("action", item, item["cmd"])
            self.assertNotIn("icon", item, item["cmd"])  # icons resolve by command name

    def test_the_help_page_is_generated_between_its_markers(self):
        self.assertEqual(1, self.office.count("<!-- product:Help-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Help-end -->"))
        body = self.office.split("<!-- product:Help-begin -->")[1].split("<!-- product:Help-end -->")[0]
        self.assertIn('id="pmhbHelp"', body)
        self.assertEqual(7, body.count('class="GtkToolButton"'))
        self.assertEqual(2, body.count('class="GtkLabel"'))  # one caption per section
        for section in self.layout["sections"]:
            self.assertIn('id="lbHelp%s"' % section["name"], body)
            self.assertIn(">%s<" % section["caption"], body)

    def test_office_ui_is_upstream_plus_tabs_and_every_generated_page(self):
        self.assertIn("Help", {layout["id_prefix"] for layout in office.page_layouts()})
        self.assertEqual(office.expected_office_ui(), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        # R12: GetInvolved and HelpIndex also have buttons elsewhere in the ribbon
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu()
        for item in self.items():
            self.assertIn(g.item_url(item), labels, item["cmd"])

    def test_every_button_has_the_image_flag(self):
        flagged = flagged_commands()
        for item in self.items():
            self.assertIn(g.item_url(item), flagged, item["cmd"] + " is left out of the image list")

    def test_labels_follow_the_design(self):
        labels = commands_xcu()
        for url, label in {**SHOWN_LABELS, **PLACEHOLDER_LABELS}.items():
            self.assertEqual(label, labels[url].replace("~", ""), url)

    def test_placeholder_labels_and_tooltips_follow_excel(self):
        labels, tips = commands_xcu(), tooltips()
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)
        self.assertNotIn("Excel", labels[".uno:HelpBlog"])  # no Microsoft product name

    def test_the_registry_labels_both_help_slots(self):
        by_url = placeholders.labels_by_url()
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items() if u in PLACEHOLDER_LABELS})
        entries = {e["offset"]: e for e in placeholders.load_all()}
        self.assertEqual(["HelpFeedback", "HelpBlog"], [entries[o]["command"] for o in HELP_SLOTS])
        for offset in HELP_SLOTS:
            self.assertNotIn("variants", entries[offset])

    def test_both_placeholders_are_on_the_page_and_have_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes().values()}
        used = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, used, url)
            self.assertNotIn(url, controlled, url)

    def test_the_page_adds_no_dropdown_command_or_popup_file(self):
        self.assertEqual([], sorted((ROOT / "sc/uiconfig/scalc/popupmenu").glob("help_*.xml")))
        self.assertNotIn("popupmenu/help_", (ROOT / "sc/UIConfig_scalc.mk").read_text(encoding="utf-8"))

    def test_the_other_help_menu_entries_stay_in_the_menu_bar(self):
        # What's This?, Tip of the Day, Search Commands, Troubleshoot Mode, Donate, License, About
        menubar = (ROOT / "sc/uiconfig/scalc/menubar/menubar.xml").read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()}
        for name in STAY_IN_THE_MENU:
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertIn('menu:id=".uno:%s"' % name, menubar, name)

    def test_suppr_has_an_entry_for_every_button(self):
        suppr = SUPPR.read_text(encoding="utf-8")
        prefix = "sc/uiconfig/scalc/ui/notebookbar_office.ui:"
        ids = [w for w in g.ids_of(self.layout) if w.startswith("btn")]
        self.assertEqual(7, len(ids))
        for wid in ids:
            self.assertRegex(suppr, re.escape(prefix) + r"//Gtk(Menu)?ToolButton\[@id='"
                             + re.escape(wid) + r"'\] button-no-label")

    def test_regenerating_the_page_changes_nothing(self):
        regenerated = g.splice(self.office, self.layout, g.emit_page(self.layout))
        self.assertEqual(self.office, regenerated)
        suppr = SUPPR.read_text(encoding="utf-8")
        self.assertEqual(suppr, g.sync_suppr(suppr, "sc/uiconfig/scalc/ui/notebookbar_office.ui", regenerated))


if __name__ == "__main__":
    unittest.main()

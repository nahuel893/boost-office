# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Review tab: layout vs product/docs/design/calc-review-tab-layout.txt, labels, menus,
placeholders, the widget ids (R12) and the commands that leave the tab (R14)."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import office, placeholders
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands, tooltips
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_review.json"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
SUPPR = ROOT / "solenv/sanitizers/ui/modules/scalc.suppr"
POPUPMENU = ROOT / "sc/uiconfig/scalc/popupmenu"
MENUBAR = ROOT / "sc/uiconfig/scalc/menubar/menubar.xml"
MENU = "{http://openoffice.org/2001/menu}"
GOTO = ".uno:ReviewGoToComment?Direction:string="
SEP = "-"  # a separator in a menu item list

# section -> (caption, [(style, [url, ...]) per toolbox in document order])
DESIGN = {
    "Proofing": ("Proofing", [("large", [".uno:SpellDialog"]), ("large", [".uno:ThesaurusDialog"]),
                              ("large", [".uno:SetDocumentProperties"])]),
    "Accessibility": ("Accessibility", [("large", [".uno:ReviewAccessibilityMenu"])]),
    "Language": ("Language", [("large", [".uno:ReviewTranslate"])]),
    "Comments": ("Comments", [("large", [".uno:InsertAnnotation"]), ("large", [".uno:DeleteNote"]),
                              ("large", [GOTO + "previous"]), ("large", [GOTO + "next"]),
                              ("large", [".uno:ShowAnnotations"])]),
    "Notes": ("Notes", [("large", [".uno:ReviewNotesMenu"])]),
    "Protect": ("Protect", [("large", [".uno:Protect"]), ("large", [".uno:ToolProtectionDocument"]),
                            ("large", [".uno:ReviewAllowEditRanges"]), ("large", [".uno:ShareDocument"])]),
    "Ink": ("Ink", [("large", [".uno:ReviewHideInk"])]),
}
MENUS = {  # command: (label, popup resource, popup items in order)
    "ReviewAccessibilityMenu": ("Check Accessibility", "review_accessibility",
                                [".uno:ReviewCheckAccessibility", ".uno:ObjectTitleDescription",
                                 ".uno:AutoFormat", ".uno:SplitCell"]),
    "ReviewNotesMenu": ("Notes", "review_notes",
                        [".uno:InsertAnnotation", ".uno:EditAnnotation", SEP, GOTO + "previous",
                         GOTO + "next", SEP, ".uno:NoteVisible", ".uno:ShowAllNotes",
                         ".uno:HideAllNotes", ".uno:DeleteAllNotes"]),
}
PLACEHOLDER_LABELS = {  # URL -> label; the first one is a menu item only
    ".uno:ReviewCheckAccessibility": "Check Accessibility", ".uno:ReviewTranslate": "Translate",
    GOTO + "previous": "Previous Comment", GOTO + "next": "Next Comment",
    ".uno:ReviewAllowEditRanges": "Allow Edit Ranges", ".uno:ReviewHideInk": "Hide Ink"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS)  # implemented ones are no placeholder
REVIEW_SLOTS = range(408, 413)
# R14: the LibreOffice-only buttons the old page had; each must stay reachable from the menu bar
LEFT_THE_TAB = ["SpellOnline", "Hyphenate", "TraceChangeMode", "AcceptChanges", "CompareDocuments",
                "MergeDocuments", "RedactDoc"]
OLD_PAGE_WIDGETS = ["btnReviewSpellOnline", "btnReviewHyphenate", "btnReviewTraceChangeMode",
                    "btnReviewAcceptChanges", "btnReviewCompareDocuments", "btnReviewMergeDocuments",
                    "btnReviewRedactDoc", "btnReviewEditAnnotation", "btnReviewShowAllNotes",
                    "btnReviewHideAllNotes", "btnReviewDeleteAllNotes"]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class CalcReviewUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = OFFICE.read_text(encoding="utf-8")

    def boxes(self, section):
        return [b for c in section["columns"] for b in c]

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("phbReview", self.layout["page"])
        self.assertEqual("Review", self.layout["id_prefix"])
        self.assertEqual("TabbedCalc", self.layout["context"])
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        for section in self.layout["sections"]:
            self.assertEqual(DESIGN[section["name"]][0], section["caption"])
            self.assertEqual(3, section["rows"], section["name"])

    def test_every_control_is_there_in_order_with_its_size(self):
        for section in self.layout["sections"]:
            got = [(b["style"], [g.item_url(i) for i in b["items"]]) for b in self.boxes(section)]
            self.assertEqual(DESIGN[section["name"]][1], got, section["name"])

    def test_every_section_is_one_toolbox_per_column(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual({"Proofing": [1] * 3, "Accessibility": [1], "Language": [1],
                          "Comments": [1] * 5, "Notes": [1], "Protect": [1] * 4, "Ink": [1]}, shapes)

    def test_the_menu_commands_are_dropdowns_the_rest_are_plain_buttons(self):
        for item in self.items():
            expected = "split" if item["cmd"] in MENUS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_url_variants_carry_a_short_id_the_url_as_action_and_a_plain_icon_name(self):
        variants = [i for i in self.items() if "action" in i]
        self.assertEqual(["CommentPrevious", "CommentNext"], [i["cmd"] for i in variants])
        for item in variants:
            base, value = re.match(r"\.uno:(\w+)\?\w+:\w+=(\w+)$", item["action"]).groups()
            self.assertEqual("cmd/32/%s_%s.png" % (base.lower(), value), item["icon"], item["cmd"])

    def test_the_old_review_page_and_its_overflow_menu_are_gone(self):
        self.assertIn("Menu Review", self.layout["remove_objects"])
        for old in ('id="Menu Review"', "Review-ReviewButton:Menu Review", 'id="Review-Menu"',
                    'id="MenuReview-'):
            self.assertNotIn(old, self.office)
        for wid in OLD_PAGE_WIDGETS:
            self.assertNotIn('id="%s"' % wid, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Review-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Review-end -->"))

    def test_office_ui_is_upstream_plus_tabs_and_every_generated_page(self):
        self.assertIn("Review", {layout["id_prefix"] for layout in office.page_layouts()})
        self.assertEqual(office.expected_office_ui(), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        # R12: Insert's Comment and Review's Comment (and the Navigator-like commands that appear on
        # several pages) are separate widgets, because every id carries its page prefix
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
        self.assertIn(".uno:InsertAnnotation", shared)
        for url, ids in shared.items():
            self.assertEqual(len(ids), len(set(ids)), url)

    def test_the_menu_bar_keeps_every_command_that_left_the_tab(self):
        # R14: Automatic Spell Checking, Hyphenation, Track Changes, Compare/Merge, Redact
        menubar = MENUBAR.read_text(encoding="utf-8")
        for name in LEFT_THE_TAB:
            self.assertIn('menu:id=".uno:%s"' % name, menubar, name)
        on_tab = {g.item_command(i) for i in self.items()}
        for name in LEFT_THE_TAB:
            self.assertNotIn(".uno:" + name, on_tab, name)

    def test_comments_and_notes_drive_the_one_libreoffice_comment_type(self):
        # the Comments group and the Notes menu both use LibreOffice's comment commands
        notes = MENUS["ReviewNotesMenu"][2]
        comment_commands = {".uno:InsertAnnotation", ".uno:DeleteNote", ".uno:ShowAnnotations"}
        self.assertLessEqual(comment_commands, {g.item_url(i) for i in self.items()})
        self.assertIn(".uno:InsertAnnotation", notes)
        # Previous/Next are the same two URL variants in both places: no extra slot, no extra label
        self.assertEqual(2, sum(1 for e in placeholders.load_all() if e["command"] == "ReviewGoToComment"
                                for _ in e["variants"]))

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

    def test_the_registry_labels_every_review_slot_and_variant(self):
        by_url = placeholders.labels_by_url()
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items()
                                              if u.startswith(".uno:Review")})
        for entry in placeholders.load():
            if entry["offset"] in REVIEW_SLOTS and "variants" in entry:
                self.assertEqual(entry["variants"], list(entry["variant_labels"]), entry["command"])

    def test_every_review_placeholder_is_on_the_page_or_in_a_menu_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes().values()}
        used = {g.item_url(i) for i in self.items()}
        menu_items = {u for _l, _r, items in MENUS.values() for u in items}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, used | menu_items, url)
            self.assertNotIn(url, controlled, url)
        self.assertNotIn(".uno:ReviewCheckAccessibility", used)  # it is only the menu's first item

    def test_dropdown_commands_have_labels_and_popup_and_toolbar_controllers(self):
        labels, nodes = commands_xcu(), controller_nodes()
        self.assertEqual(2, len(MENUS))
        for cmd, (label, resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd]
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in ours}
            self.assertEqual({"ResourceMenuController", "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertEqual(resource, kinds["ResourceMenuController"]["Value"])
            for kind in kinds.values():
                self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", kind["Module"])
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])

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

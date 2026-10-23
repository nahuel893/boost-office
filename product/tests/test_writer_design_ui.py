# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Writer Design tab: layout vs product/docs/writer-ribbon-tabs.md section 1 "Design" (a new page),
the six placeholders of section 5, the new label node and the tab operation that adds the page."""
import json
import re
import unittest
from pathlib import Path

from product.tests import office, placeholders
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands, tooltips
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
WRITER = office.app("writer")
LAYOUT = ROOT / "product/ui/writer_design.json"
OFFICE_REL = "sw/uiconfig/swriter/ui/notebookbar_office.ui"
PART = ".uno:PageLayoutThemePart?Part:string="
STYLE = ".uno:DesignStyleSet?Action:string="

# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Design".
# Size: L = large, S = small-label; the Style Set gallery is a wide greyed button.
DESIGN = {
    "DocumentFormatting": ("Document Formatting", 3, [
        ("large", [PART + "themes"]), ("large", [STYLE + "gallery"]), ("large", [".uno:ThemeDialog"]),
        ("large", [PART + "fonts"]),
        ("small-label", [STYLE + "spacing"]), ("small-label", [PART + "effects"]),
        ("small-label", [STYLE + "setdefault"])]),
    "PageBackground": ("Page Background", 3, [
        ("large", [".uno:Watermark"]), ("large", [".uno:PageAreaDialog"]), ("large", [".uno:PageDialog"])]),
}
SHAPES = {"DocumentFormatting": [1, 1, 1, 1, 3], "PageBackground": [1, 1, 1]}
# Word's label per item (T9w: the ribbon shows it, unless it equals LibreOffice's label; menus keep LibreOffice's)
WORD_LABELS = {
    PART + "themes": "Themes", STYLE + "gallery": "Style Set", ".uno:ThemeDialog": "Colors",
    PART + "fonts": "Fonts", STYLE + "spacing": "Paragraph Spacing", PART + "effects": "Effects",
    STYLE + "setdefault": "Set as Default", ".uno:Watermark": "Watermark", ".uno:PageAreaDialog": "Page Color",
    ".uno:PageDialog": "Page Borders"}
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, Design rows)
    PART + "themes": "Themes", PART + "fonts": "Fonts", PART + "effects": "Effects",
    STYLE + "gallery": "Style Set", STYLE + "spacing": "Paragraph Spacing", STYLE + "setdefault": "Set as Default"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("writer"))
DESIGN_SLOTS = {6: "PageLayoutThemePart", 7: "DesignStyleSet"}
# the style set gallery flexes like Word's, so it takes the width the page leaves free (W2c)
# the Style Set placeholder stays a plain button: an expanded greyed box left an empty gap mid-group (W4b)
EXPANDING = set()
# the real commands the design keeps from LibreOffice; the new label node is PageAreaDialog
REAL = [".uno:ThemeDialog", ".uno:Watermark", ".uno:PageAreaDialog", ".uno:PageDialog"]


class WriterDesignUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = WRITER.office.read_text(encoding="utf-8")
        self.tabs = json.loads(WRITER.tabs.read_text(encoding="utf-8"))

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Design Tab", self.layout["page"])
        self.assertEqual("Design", self.layout["id_prefix"])
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
        self.assertEqual(10, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_every_control_is_a_plain_button_and_none_takes_the_free_width(self):
        # no Design control has a dropdown: Word's menus here are galleries and cloud lists (decision 13)
        for item in self.items():
            self.assertEqual("button", item.get("kind", "button"), item["cmd"])
        for section in self.layout["sections"]:
            for box in self.boxes(section):
                url = g.item_url(box["items"][0])
                self.assertEqual(url in EXPANDING, bool(box.get("expand")), url)

    def test_every_item_keeps_words_label_in_office_label(self):
        self.assertEqual(WORD_LABELS, {g.item_url(i): i.get("office_label") for i in self.items()})

    def test_nothing_leaves_the_design_tab_because_the_page_is_new(self):
        stock = (ROOT / "sw/uiconfig/swriter/ui/notebookbar.ui").read_text(encoding="utf-8")
        self.assertNotIn('id="Design Tab"', stock)
        self.assertEqual([], self.layout.get("remove_objects", []))

    def test_the_tab_operations_add_the_page_between_insert_and_layout(self):
        adds = {a["page"]: a for a in self.tabs["add_pages"]}
        add = adds["Design Tab"]
        self.assertEqual({"page": "Design Tab", "prefix": "Design", "after_tab": "InsertLabel", "position": 3,
                          "tab_id": "DesignLabel", "label": "Desi~gn", "context": "TabbedWriter|DesignTabLabel"},
                         add)
        self.assertIn('id="DesignLabel"', self.office)
        self.assertEqual(1, self.office.count("<!-- product:Design-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Design-end -->"))
        order = [self.office.index('id="%s"' % i) for i in ("Insert Tab", "Design Tab", "Layout Tab")]
        self.assertEqual(sorted(order), order)

    def test_the_tabs_after_design_are_shifted_by_one_position(self):
        positions = self.tabs["positions"]
        for number, name in enumerate(("Layout", "References", "Mailings", "Review", "View", "Table", "Image", "Draw",
                                       "Object", "Media", "Print", "Form", "Extension", "Tools"), start=4):
            if name == "Mailings":
                continue  # a new page like Design: add_pages places it (test_writer_mailings_ui)
            self.assertEqual(number, positions[name + " Tab"], name)
            self.assertEqual(number, positions[name + "Label"], name)

    def test_the_design_page_has_no_context_so_it_shows_everywhere(self):
        # like the stock Home/Insert pages: no context-* style class on the page (design section 1)
        start = self.office.index('id="Design Tab"')
        page = self.office[start:self.office.index("<!-- product:Design-end -->")]
        self.assertNotIn("context-", page)

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Design", {layout["id_prefix"] for layout in office.page_layouts("writer")})
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="writer")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_page_color_has_a_label_node_of_its_own(self):
        # design section 5 / plan: .uno:PageAreaDialog had no label node anywhere; W4a adds one
        xcu = (ROOT / "officecfg/registry/data/org/openoffice/Office/UI/WriterCommands.xcu").read_text(
            encoding="utf-8")
        self.assertIn('<node oor:name=".uno:PageAreaDialog" oor:op="replace">', xcu)
        self.assertTrue(commands_xcu(app="writer")[".uno:PageAreaDialog"])
        self.assertIn(".uno:PageAreaDialog", flagged_commands(app="writer"))

    def test_the_placeholders_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="writer"), tooltips(app="writer")
        # every row left is still an unimplemented slot of the registry (implementing one drops it)
        self.assertLessEqual(set(PLACEHOLDER_LABELS), set(placeholders.all_urls(placeholders.registry("writer"))))
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_placeholders_have_the_image_flag(self):
        flagged = flagged_commands(app="writer")
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_the_registry_labels_every_design_slot(self):
        registry = placeholders.registry("writer")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items()
                                              if u.startswith((PART, STYLE))})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        for offset, command in DESIGN_SLOTS.items():
            self.assertEqual(command, entries[offset]["command"])

    def test_every_design_placeholder_is_on_the_page_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="writer").values()}
        on_page = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, on_page, url)
            self.assertNotIn(url, controlled, url)

    def test_the_real_commands_are_on_the_page_and_the_others_are_not_commands_of_calc_dropdowns(self):
        on_page = {g.item_url(i) for i in self.items()}
        for url in REAL:
            self.assertIn(url, on_page, url)
        self.assertEqual(4, len(on_page & set(REAL)))
        self.assertEqual(6, len(on_page - set(REAL)))

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

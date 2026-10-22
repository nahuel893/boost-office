# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Writer References tab: layout vs product/docs/writer-ribbon-tabs.md section 1 "References", the
three new dropdowns (popup files, controllers, labels), the four placeholders, and the commands that
leave the tab (section 2, "References (8)")."""
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
LAYOUT = ROOT / "product/ui/writer_references.json"
OFFICE_REL = "sw/uiconfig/swriter/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sw/uiconfig/swriter/popupmenu"
TOOLBARS = ROOT / "sw/uiconfig/swriter/toolbar"
MENUBAR = ROOT / "sw/uiconfig/swriter/menubar/menubar.xml"
MENU = "{http://openoffice.org/2001/menu}"
TEXT_MODULE = "com.sun.star.text.TextDocument"
SEP = "-"  # a separator in a menu item list
FRAMEWORK = "com.sun.star.comp.framework."


def uno(*names):
    return [".uno:" + name for name in names]


AUTH = ".uno:ReferencesAuthorities?Action:string="
# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "References".
# Size: L = large, S = small-label. Research (Search, Researcher) is cloud and is omitted.
DESIGN = {
    "TableOfContents": ("Table of Contents", 3, [
        ("large", uno("ReferencesTocMenu")),
        ("small-label", uno("ReferencesAddTextMenu")), ("small-label", uno("UpdateCurIndex"))]),
    "Footnotes": ("Footnotes", 3, [
        ("large", uno("InsertFootnote")),
        ("small-label", uno("InsertEndnote")), ("small-label", uno("ReferencesNextFootnoteMenu")),
        ("small-label", uno("JumpToFootnoteOrAnchor"))]),
    "Citations": ("Citations & Bibliography", 3, [
        ("large", uno("InsertAuthoritiesEntry")),
        ("small-label", uno("BibliographyComponent")), ("small-label", uno("ReferencesCitationStyle")),
        ("small-label", uno("InsertMultiIndex"))]),
    "Captions": ("Captions", 3, [
        ("large", uno("InsertCaptionDialog")),
        ("small-label", uno("InsertMultiIndex")), ("small-label", uno("UpdateCurIndex")),
        ("small-label", uno("InsertReferenceField"))]),
    "Index": ("Index", 3, [
        ("large", uno("InsertIndexesEntry")),
        ("small-label", uno("InsertMultiIndex")), ("small-label", uno("UpdateCurIndex"))]),
    "Authorities": ("Table of Authorities", 3, [
        ("large", [AUTH + "mark"]),
        ("small-label", [AUTH + "insert"]), ("small-label", [AUTH + "update"])]),
}
SHAPES = {"TableOfContents": [1, 2], "Footnotes": [1, 3], "Citations": [1, 3], "Captions": [1, 3],
          "Index": [1, 2], "Authorities": [1, 2]}
# Word's label per widget command (T9w: the ribbon shows it, unless it equals LibreOffice's label)
WORD_LABELS = {
    "ReferencesTocMenu": "Table of Contents", "ReferencesAddTextMenu": "Add Text", "UpdateCurIndex": "Update Table",
    "InsertFootnote": "Insert Footnote", "InsertEndnote": "Insert Endnote",
    "ReferencesNextFootnoteMenu": "Next Footnote", "JumpToFootnoteOrAnchor": "Show Notes",
    "InsertAuthoritiesEntry": "Insert Citation", "BibliographyComponent": "Manage Sources",
    "ReferencesCitationStyle": "Style", "ReferencesBibliography": "Bibliography",
    "InsertCaptionDialog": "Insert Caption", "ReferencesTableOfFigures": "Insert Table of Figures",
    "ReferencesUpdateCaptionTable": "Update Table", "InsertReferenceField": "Cross-reference",
    "InsertIndexesEntry": "Mark Entry", "ReferencesInsertIndex": "Insert Index",
    "ReferencesUpdateIndex": "Update Index", "ReferencesMarkCitation": "Mark Citation",
    "ReferencesInsertAuthorities": "Insert Table of Authorities", "ReferencesUpdateAuthorities": "Update Table"}
# design decision 11: the buttons that share a real command get a widget command of their own and the URL as action
DUPLICATES = {
    "ReferencesBibliography": ".uno:InsertMultiIndex", "ReferencesTableOfFigures": ".uno:InsertMultiIndex",
    "ReferencesInsertIndex": ".uno:InsertMultiIndex", "ReferencesUpdateCaptionTable": ".uno:UpdateCurIndex",
    "ReferencesUpdateIndex": ".uno:UpdateCurIndex"}
# the dropdowns: Word's three (Table of Contents, Add Text, Next Footnote) are all new commands
SPLITS = {"ReferencesTocMenu", "ReferencesAddTextMenu", "ReferencesNextFootnoteMenu"}

# command -> (label, popup resource, popup items in order); design section 1 "Menu contents".
# The label is also the menu's, so it is LibreOffice-style; Word's is office_label.
MENUS = {
    "ReferencesTocMenu": ("Table of Contents", "references_toc",
                          uno("InsertMultiIndex", "EditCurIndex", "RemoveTableOf")),
    "ReferencesAddTextMenu": ("Add Text to Contents", "references_addtext",
                              uno("TextBodyParaStyle", "Heading1ParaStyle", "Heading2ParaStyle",
                                  "Heading3ParaStyle")),
    "ReferencesNextFootnoteMenu": ("Go to Footnote", "references_nextfootnote",
                                   uno("JumpToNextFootnote", "JumpToPrevFootnote")),
}
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, References rows)
    ".uno:ReferencesCitationStyle": "Style", AUTH + "mark": "Mark Citation",
    AUTH + "insert": "Insert Table of Authorities", AUTH + "update": "Update Table"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("writer"))
REFERENCES_SLOTS = [8, 9]

# design section 2 "References (8)": command -> (class, menu-bar id that keeps it reachable).
# a: the same command is in the menu bar; b: only an equivalent entry is; c: neither.
LEFT_THE_TAB = {
    "UpdateAll": ("a", "UpdateAll"), "InsertFootnoteDialog": ("a", "InsertFootnoteDialog"),
    "InsertFieldCtrl": ("a", "InsertFieldCtrl"), "Repaginate": ("a", "Repaginate"),
    "UpdateFields?UnlockSoftFixed:bool=1": ("a", "UpdateFields?UnlockSoftFixed:bool=1"),
    "UpdateAllIndexes": ("a", "UpdateAllIndexes"), "UpdateAllLinks": ("a", "UpdateAllLinks"),
    "UpdateCharts": ("a", "UpdateCharts"),
}
# the stock commands that stay on another tab (section 2, "Kept on another tab")
KEPT_ELSEWHERE = {"InsertBookmark": "Insert", "InsertPageNumberField": "Insert",
                  "ViewDataSourceBrowser": "Mailings"}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def stock_commands(object_id):
    """The action names inside one object of the stock notebookbar.ui."""
    lines = (ROOT / "sw/uiconfig/swriter/ui/notebookbar.ui").read_text(encoding="utf-8").split("\n")
    start = next(i for i, line in enumerate(lines) if '<object' in line and 'id="%s"' % object_id in line)
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == " " * indent + "</object>")
    return set(re.findall(r'action-name">([^<]+)<', "\n".join(lines[start:end])))


class WriterReferencesUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = WRITER.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("References Tab", self.layout["page"])
        self.assertEqual("References", self.layout["id_prefix"])
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
        self.assertEqual(21, len(self.items()))

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
        """The property map of the generated button `btnReferences<cmd>`."""
        for obj in ET.fromstring(self.office).iter("object"):
            if obj.get("id") == "btnReferences" + cmd:
                return {p.get("name"): p.text for p in obj.findall("property")}
        self.fail("no button for " + cmd)

    def test_the_ribbon_label_of_the_shared_commands_is_words_not_the_commands(self):
        # what the ribbon shows is the .ui label, else the command's own label (T9w leaves the label out when
        # LibreOffice already shows Word's text, as for Update Index)
        shown = g.shown_labels(str(ROOT), "writer")
        for cmd in list(DUPLICATES) + ["UpdateCurIndex"]:
            button = self.button(cmd)
            self.assertEqual(WORD_LABELS[cmd], button.get("label", shown[button["action-name"]]), cmd)
            if cmd != "ReferencesUpdateIndex":
                self.assertIn("label", button, cmd)  # the shared command's own label is not Word's

    def test_the_research_group_and_cloud_controls_are_absent(self):
        names = {s["name"] for s in self.layout["sections"]}
        self.assertFalse({"Research", "Search", "Researcher"} & names)
        labels = {i.get("office_label") for i in self.items()}
        self.assertFalse({"Search", "Researcher", "Acronyms"} & labels)

    def test_the_old_references_page_and_its_overflow_menu_are_gone(self):
        self.assertIn("Menu References", self.layout["remove_objects"])
        for old in ('id="Menu References"', "References-ReferencesButton:Menu References", 'id="References-Menu"',
                    'id="MenuReference-', 'id="References-UpdateAll"'):
            self.assertNotIn(old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:References-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:References-end -->"))
        self.assertIn('id="References Tab"', self.office)  # the page itself stays, with the tab label

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("References", {layout["id_prefix"] for layout in office.page_layouts("writer")})
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_the_duplicate_buttons_have_distinct_widget_ids_and_the_real_url_as_action(self):
        # design decision 11: three InsertMultiIndex and three UpdateCurIndex buttons on one page
        by_url = {}
        for item in self.items():
            by_url.setdefault(g.item_url(item), []).append(item)
        for url in (".uno:InsertMultiIndex", ".uno:UpdateCurIndex"):
            self.assertEqual(3, len(by_url[url]), url)
            widgets = ["btnReferences" + i["cmd"] for i in by_url[url]]
            self.assertEqual(3, len(set(widgets)), widgets)
            for widget in widgets:
                self.assertEqual(1, self.office.count('id="%s"' % widget), widget)
        for cmd, url in DUPLICATES.items():
            self.assertEqual(url, self.button(cmd)["action-name"], cmd)

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(8, len(LEFT_THE_TAB))
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_url(i) for i in self.items()} | {g.item_command(i) for i in self.items()}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)
            own = 'menu:id=".uno:%s"' % name
            if kind == "a":
                self.assertEqual(name, menu_id)
            else:
                self.assertNotEqual(name, menu_id)
                self.assertNotIn(own, menubar, name + " is not in the menu bar: class " + kind)
        self.assertEqual({"a": 8, "b": 0, "c": 0}, {k: sum(1 for v in LEFT_THE_TAB.values() if v[0] == k)
                                                    for k in "abc"})

    def test_every_stock_command_is_kept_dropped_to_the_menu_bar_or_on_another_tab(self):
        # the stock page and its overflow menu: whatever is not on the new page is in the leave list or kept
        stock = stock_commands("References Tab") | stock_commands("Menu References")
        on_tab = {g.item_url(i) for i in self.items()}
        left = {".uno:" + n for n in LEFT_THE_TAB}
        elsewhere = {".uno:" + n for n in KEPT_ELSEWHERE}
        self.assertEqual(set(), stock - on_tab - left - elsewhere)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="writer")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_new_menus_and_placeholders_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="writer"), tooltips(app="writer")
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd], cmd)
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

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
                self.assertIn(url, labels, url)

    def test_the_registry_labels_every_references_slot(self):
        registry = placeholders.registry("writer")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items()
                                              if u.startswith(".uno:References")})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        for offset in REFERENCES_SLOTS:
            self.assertTrue(entries[offset]["command"].startswith("References"))

    def test_every_references_placeholder_is_on_the_page_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="writer").values()}
        on_page = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, on_page, url)
            self.assertNotIn(url, controlled, url)

    def test_each_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        nodes = controller_nodes(app="writer")
        self.assertEqual(3, len(MENUS))
        for cmd, (_label, resource, _items) in MENUS.items():
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd]
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in ours}
            self.assertEqual({"ResourceMenuController", "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])
            self.assertEqual(resource, kinds["ResourceMenuController"]["Value"])
            for v in ours:
                self.assertEqual(TEXT_MODULE, v["Module"])
                self.assertTrue(v["Controller"].startswith(FRAMEWORK))
            # Calc does not know these commands: the node names carry no Writer suffix
            self.assertEqual({cmd + "Popup", cmd + "Control"}, {k for k, v in nodes.items()
                                                               if v["Command"] == ".uno:" + cmd})

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        # the three dropdown commands are new: only the References page and the controller nodes name them
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

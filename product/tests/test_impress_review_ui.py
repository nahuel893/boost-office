# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Impress Review tab (Proofing, Accessibility, Language, Comments, Compare, Ink), the stock Review page
regenerated: layout vs product/docs/impress-ribbon-tabs.md section 1 "Review", the two new dropdowns (popup files,
controllers, labels), the ten placeholders, and the commands that leave the tab (section 2, "Review (3)")."""
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
LAYOUT = ROOT / "product/ui/impress_review.json"
OFFICE_REL = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sd/uiconfig/simpress/popupmenu"
MENUBAR = ROOT / "sd/uiconfig/simpress/menubar/menubar.xml"
MENU = "{http://openoffice.org/2001/menu}"
PRESENTATION_MODULE = "com.sun.star.presentation.PresentationDocument"
SEP = "-"  # a separator in a menu item list
COMPARE = ".uno:ReviewCompare?Action:string="


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Review".
# Size: L = large, S = small-label. The design's "split" placeholders and Show Comments (a toggle without a menu)
# are plain buttons (no menu to open, controller ruling 23).
DESIGN = {
    "Proofing": ("Proofing", 3, [("large", uno("SpellDialog")), ("large", uno("ThesaurusDialog"))]),
    "Accessibility": ("Accessibility", 3, [("large", uno("ReviewCheckAccessibility"))]),
    "Language": ("Language", 3, [("small-label", uno("ReviewTranslate")),
                                 ("small-label", uno("ReviewLanguageMenu"))]),
    "Comments": ("Comments", 3, [("large", uno("InsertAnnotation")), ("large", uno("ReviewDeleteCommentMenu")),
                                 ("large", uno("PreviousAnnotation")), ("large", uno("NextAnnotation")),
                                 ("large", uno("ShowAnnotations"))]),
    "Compare": ("Compare", 3, [("small-label", [COMPARE + "compare"]), ("small-label", [COMPARE + "accept"]),
                               ("small-label", [COMPARE + "reject"]), ("small-label", [COMPARE + "previous"]),
                               ("small-label", [COMPARE + "next"]), ("small-label", [COMPARE + "pane"]),
                               ("large", [COMPARE + "endreview"])]),
    "Ink": ("Ink", 3, [("large", uno("ReviewHideInk"))]),
}
SHAPES = {"Proofing": [1, 1], "Accessibility": [1], "Language": [2], "Comments": [1, 1, 1, 1, 1],
          "Compare": [3, 3, 1], "Ink": [1]}
# PowerPoint's label per item; the layout item's "cmd" (the widget command) is the key
POWERPOINT_LABELS = {
    "SpellDialog": "Spelling", "ThesaurusDialog": "Thesaurus", "ReviewCheckAccessibility": "Check Accessibility",
    "ReviewTranslate": "Translate", "ReviewLanguageMenu": "Language", "InsertAnnotation": "New Comment",
    "ReviewDeleteCommentMenu": "Delete", "PreviousAnnotation": "Previous", "NextAnnotation": "Next",
    "ShowAnnotations": "Show Comments", "ReviewCompare": "Compare", "ReviewCompareAccept": "Accept",
    "ReviewCompareReject": "Reject", "ReviewComparePrevious": "Previous", "ReviewCompareNext": "Next",
    "ReviewComparePane": "Reviewing Pane", "ReviewCompareEndReview": "End Review", "ReviewHideInk": "Hide Ink"}
SPLITS = {"ReviewLanguageMenu", "ReviewDeleteCommentMenu"}

# command -> (label, popup resource, popup items in order); design section 1 "Menu contents"
MENUS = {
    "ReviewLanguageMenu": ("Language", "review_language",
                           uno("SetLanguageAllTextMenu") + [SEP] + uno("Hyphenation", "ChineseConversion",
                                                                        "HangulHanjaConversion") + [SEP]
                           + uno("MoreDictionaries")),
    # decision 10: the body item (Delete) comes first
    "ReviewDeleteCommentMenu": ("Delete Comments", "review_deletecomment",
                                uno("DeleteAnnotation", "DeleteAllAnnotation")),
}
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, the Review rows)
    ".uno:ReviewCheckAccessibility": "Check Accessibility", ".uno:ReviewTranslate": "Translate",
    COMPARE + "compare": "Compare", COMPARE + "accept": "Accept", COMPARE + "reject": "Reject",
    COMPARE + "previous": "Previous", COMPARE + "next": "Next", COMPARE + "pane": "Reviewing Pane",
    COMPARE + "endreview": "End Review", ".uno:ReviewHideInk": "Hide Ink"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("impress"))
REVIEW_SLOTS = [15, 16, 17, 18]

# design section 2 "Review (3)": command -> (class, menu-bar id that keeps it reachable); all class a.
LEFT_THE_TAB = {"SpellOnline": ("a", "SpellOnline"), "RedactDoc": ("a", "RedactDoc"), "EditDoc": ("a", "EditDoc")}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def stock_commands(*page_ids):
    stock = ET.parse(ROOT / "sd/uiconfig/simpress/ui/notebookbar.ui").getroot()
    commands, ids = set(), set()
    for wid in page_ids:
        node = next(o for o in stock.iter("object") if o.get("id") == wid)
        commands |= {p.text for p in node.iter("property") if p.get("name") == "action-name"}
        ids |= {o.get("id") for o in node.iter("object")}
    return commands, ids


class ImpressReviewUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Review", self.layout["page"])  # the stock page keeps its id
        self.assertEqual("Review", self.layout["id_prefix"])
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
        self.assertEqual(18, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_dropdowns_are_split_the_rest_are_plain_buttons(self):
        self.assertEqual(SPLITS, {i["cmd"] for i in self.items() if i.get("kind") == "split"})
        for item in self.items():
            if item["cmd"] not in SPLITS:
                self.assertEqual("button", item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_powerpoints_label_in_office_label(self):
        self.assertEqual(POWERPOINT_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_the_url_variants_have_their_own_widget_command_and_an_explicit_icon_that_exists(self):
        manifest = json.loads((ROOT / "product/icons/manifest.json").read_text(encoding="utf-8"))
        names = {e["name"] for e in manifest["icons"]}
        compare = [i for i in self.items() if g.item_url(i).startswith(COMPARE)]
        self.assertEqual(7, len(compare))
        self.assertEqual(7, len({i["cmd"] for i in compare}))
        for item in self.items():
            if "?" in g.item_url(item):
                self.assertTrue(item.get("icon"), item["cmd"])
            if "icon" in item:
                name = item["icon"].removeprefix("cmd/").removeprefix("32/").removeprefix("sc_")
                self.assertIn(name.removesuffix(".png"), names, item["cmd"])

    def test_the_overflow_menu_goes_with_the_stock_buttons(self):
        self.assertEqual(["Menu Review"], self.layout["remove_objects"])
        _commands, ids = stock_commands("Review")
        _menu, menu_ids = stock_commands("Menu Review")
        present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office))
        self.assertTrue(ids and menu_ids)
        # a stock id the new layout generates again (btnReviewSpellDialog) is the new widget, not a leftover
        gone = (ids | menu_ids | {"Menu Review"}) - {"Review", "pmhbReview"} - set(g.ids_of(self.layout))
        self.assertEqual(set(), gone & present)
        self.assertIn('id="Review"', self.office)  # the page itself stays, with the tab label
        self.assertEqual(1, self.office.count("<!-- product:Review-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Review-end -->"))

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Review", {layout["id_prefix"] for layout in office.page_layouts("impress")})
        self.assertEqual(office.expected_office_ui("impress"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_review_follows_slide_show_and_precedes_view(self):
        root = ET.fromstring(self.office)
        book = root.find(".//object[@id='ContextContainer']")
        pages = [c.find("object").get("id") for c in book.findall("child") if c.get("type") != "tab"]
        tabs = [c.find("object").get("id") for c in book.findall("child[@type='tab']")]
        self.assertEqual(["SlideShow", "Review", "View"], pages[6:9])
        self.assertEqual(["SlideShowLabel", "ReviewLabel", "ViewLabel"], tabs[6:9])

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(3, len(LEFT_THE_TAB))
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()} | {g.item_url(i) for i in self.items()}
        in_menus = {u for _l, _r, items in MENUS.values() for u in items}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertEqual("a", kind)
            self.assertEqual(name, menu_id)
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertNotIn(".uno:" + name, in_menus, name)
            self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)

    def test_the_stock_review_page_commands_either_stay_or_are_in_the_leave_list(self):
        # every command of the stock Review page and its overflow menu is on this page, in a dropdown, or in the
        # leave list; the leave list is in the menu bar
        commands, _ = stock_commands("Review", "Menu Review")
        on_tab = {g.item_url(i) for i in self.items()} | {u for _l, _r, items in MENUS.values() for u in items}
        left = {".uno:" + name for name in LEFT_THE_TAB}
        menubar = MENUBAR.read_text(encoding="utf-8")
        self.assertGreater(len(commands), 10)
        for url in sorted(commands):
            self.assertTrue(url in on_tab or url in left, url)
            if url in left:
                self.assertIn('menu:id="%s"' % url, menubar, url)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="impress")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_new_menus_and_placeholders_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
        self.assertEqual(10, len(PLACEHOLDER_LABELS))
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_new_commands_have_the_image_flag(self):
        flagged = flagged_commands(app="impress")
        for cmd in MENUS:
            self.assertIn(".uno:" + cmd, flagged, cmd)
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_the_menu_items_are_known_commands(self):
        labels = commands_xcu(app="impress")
        for _label, _resource, items in MENUS.values():
            for url in items:
                if url != SEP:
                    self.assertIn(url, labels, url)

    def test_the_registry_labels_every_review_slot_and_variant(self):
        registry = placeholders.registry("impress")
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        self.assertEqual(["ReviewCheckAccessibility", "ReviewTranslate", "ReviewCompare", "ReviewHideInk"],
                         [entries[o]["command"] for o in REVIEW_SLOTS])
        self.assertEqual("Check Accessibility", entries[15]["label"])
        self.assertEqual("Translate", entries[16]["label"])
        self.assertEqual("Hide Ink", entries[18]["label"])
        self.assertEqual(["Action:string=" + v for v in ("compare", "accept", "reject", "previous", "next", "pane",
                                                         "endreview")], entries[17]["variants"])
        by_url = placeholders.labels_by_url(registry)
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, by_url[url], url)

    def test_the_placeholders_have_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        for url in PLACEHOLDER_LABELS:
            self.assertNotIn(url, controlled, url)

    def impress_nodes(self, command):
        return [v for v in controller_nodes(app="impress").values()
                if v["Command"] == command and v["Module"] == PRESENTATION_MODULE]

    def test_each_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        for cmd, (_label, resource, _items) in MENUS.items():
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in self.impress_nodes(".uno:" + cmd)}
            self.assertEqual({"ResourceMenuController", "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])
            self.assertEqual(resource, kinds["ResourceMenuController"]["Value"])

    def test_impress_nodes_carry_the_impress_suffix(self):
        text = read("officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu")
        for cmd in MENUS:
            self.assertIn('<node oor:name="%sImpressPopup" oor:op="replace">' % cmd, text)
            self.assertIn('<node oor:name="%sImpressControl" oor:op="replace">' % cmd, text)

    def test_writer_keeps_its_own_nodes_and_no_controller_is_on_an_existing_command(self):
        # the Writer nodes of the same commands stay as they are, and the real comment commands get none
        nodes = controller_nodes(app="impress").values()
        writer = [v for v in nodes if v["Command"] == ".uno:ReviewLanguageMenu"
                  and v["Module"] == "com.sun.star.text.TextDocument"]
        self.assertEqual(2, len(writer))
        controlled = {v["Command"] for v in nodes if v["Module"] in (PRESENTATION_MODULE,)}
        for url in uno("SpellDialog", "ThesaurusDialog", "InsertAnnotation", "PreviousAnnotation",
                       "NextAnnotation", "ShowAnnotations", "DeleteAnnotation", "DeleteAllAnnotation"):
            self.assertNotIn(url, controlled, url)

    def test_the_language_menu_opens_with_the_language_submenu_its_controller_builds(self):
        # SetLanguageAllTextMenu is filled by LanguageSelectionMenuController under its own command (Controller.xcu)
        nodes = controller_nodes(app="impress").values()
        controllers = {v["Controller"].rsplit(".", 1)[1] for v in nodes
                       if v["Command"] == ".uno:SetLanguageAllTextMenu"}
        self.assertEqual({"LanguageSelectionMenuController"}, controllers)
        items = self.menu_ids(ET.parse(POPUPMENU / "review_language.xml").getroot())
        self.assertEqual(".uno:SetLanguageAllTextMenu", items[0])

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        toolbars = list((ROOT / "sd/uiconfig/simpress/toolbar").glob("*.xml"))
        uis = [p for p in (ROOT / "sd/uiconfig/simpress/ui").glob("notebookbar*.ui") if p != IMPRESS.office]
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
        mk = read("sd/UIConfig_simpress.mk")
        for _label, resource, items in MENUS.values():
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("\tsd/uiconfig/simpress/popupmenu/" + resource + " \\\n", mk)
            self.assertEqual(items, self.menu_ids(ET.parse(path).getroot()), resource)

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

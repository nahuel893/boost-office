# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Writer Review tab: layout vs product/docs/writer-ribbon-tabs.md section 1 "Review", the five new
dropdowns (popup files, controllers, labels), the eight placeholders, and the commands that leave the tab
(section 2, "Review (5)")."""
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
LAYOUT = ROOT / "product/ui/writer_review.json"
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


GOTO = ".uno:ReviewGoToComment?Direction:string="
MARKUP = ".uno:ReviewMarkup?Action:string="
# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Review".
# Size: L = large, S = small-label. Editor (cloud) and Block Authors (co-authoring) are omitted.
DESIGN = {
    "Proofing": ("Proofing", 3, [
        ("large", uno("SpellingAndGrammarDialog")), ("large", uno("ThesaurusDialog")),
        ("large", uno("WordCountDialog"))]),
    "Speech": ("Speech", 3, [("large", uno("ReviewReadAloud"))]),
    "Accessibility": ("Accessibility", 3, [("large", uno("AccessibilityCheck"))]),
    "Language": ("Language", 3, [("large", uno("ReviewTranslate")), ("large", uno("ReviewLanguageMenu"))]),
    "Comments": ("Comments", 3, [
        ("large", uno("InsertAnnotation")), ("large", uno("ReviewDeleteCommentMenu")),
        ("large", [GOTO + "previous"]), ("large", [GOTO + "next"]), ("large", uno("ShowAnnotations"))]),
    "Markup": ("Markup", 3, [
        ("large", [MARKUP + "filter"]),
        ("small-label", [MARKUP + "display"]), ("small-label", uno("ShowTrackedChanges")),
        ("small-label", uno("AcceptTrackedChanges"))]),
    "Tracking": ("Tracking", 3, [
        ("large", uno("TrackChanges")), ("large", uno("ReviewAcceptMenu")), ("large", uno("ReviewRejectMenu")),
        ("small-label", uno("PreviousTrackedChange")), ("small-label", uno("NextTrackedChange"))]),
    "Compare": ("Compare", 3, [("large", uno("ReviewCompareMenu"))]),
    "Protect": ("Protect", 3, [("large", uno("ReviewRestrictEditing"))]),
    "Ink": ("Ink", 3, [("large", uno("ReviewHideInk"))]),
}
SHAPES = {"Proofing": [1, 1, 1], "Speech": [1], "Accessibility": [1], "Language": [1, 1],
          "Comments": [1, 1, 1, 1, 1], "Markup": [1, 3], "Tracking": [1, 1, 1, 2], "Compare": [1],
          "Protect": [1], "Ink": [1]}
# Word's label per widget command (T9w: the ribbon shows it, unless it equals LibreOffice's label)
WORD_LABELS = {
    "SpellingAndGrammarDialog": "Spelling and Grammar", "ThesaurusDialog": "Thesaurus",
    "WordCountDialog": "Word Count", "ReviewReadAloud": "Read Aloud", "AccessibilityCheck": "Check Accessibility",
    "ReviewTranslate": "Translate", "ReviewLanguageMenu": "Language", "InsertAnnotation": "New Comment",
    "ReviewDeleteCommentMenu": "Delete", "ReviewCommentPrevious": "Previous", "ReviewCommentNext": "Next",
    "ShowAnnotations": "Show Comments", "ReviewFilterAllMarkup": "Filter All Markup",
    "ReviewDisplayForReview": "Display for Review", "ShowTrackedChanges": "Show Markup",
    "AcceptTrackedChanges": "Reviewing Pane", "TrackChanges": "Track Changes", "ReviewAcceptMenu": "Accept",
    "ReviewRejectMenu": "Reject", "PreviousTrackedChange": "Previous", "NextTrackedChange": "Next",
    "ReviewCompareMenu": "Compare", "ReviewRestrictEditing": "Restrict Editing", "ReviewHideInk": "Hide Ink"}
# the dropdowns: five new commands; Show Markup and Track Changes reuse the stock split controllers
NEW_MENUS = {"ReviewLanguageMenu", "ReviewDeleteCommentMenu", "ReviewAcceptMenu", "ReviewRejectMenu",
             "ReviewCompareMenu"}
SPLITS = NEW_MENUS | {"ShowTrackedChanges", "TrackChanges"}
# the stock split controllers (Controller.xcu): command -> the popup they open
STOCK_SPLITS = {".uno:ShowTrackedChanges": ".uno:ShowTrackedChangesMenu",
                ".uno:TrackChanges": ".uno:RecordTrackedChangesMenu"}

# command -> (label, popup resource, popup items in order); design section 1 "Menu contents".
# The label is also the menu's, so it is LibreOffice-style; Word's is office_label.
MENUS = {
    "ReviewLanguageMenu": ("Language", "review_language",
                           uno("SetLanguageSelectionMenu", "SetLanguageParagraphMenu", "SetLanguageAllTextMenu")
                           + [SEP] + uno("HangulHanjaConversion", "ChineseConversion", "MoreDictionaries")),
    "ReviewDeleteCommentMenu": ("Delete Comments", "review_deletecomment",
                                uno("DeleteComment", "DeleteAuthor", "DeleteAllNotes")),
    "ReviewAcceptMenu": ("Accept Changes", "review_accept",
                         uno("AcceptTrackedChangeToNext", "AcceptTrackedChange", "AcceptAllTrackedChanges")),
    "ReviewRejectMenu": ("Reject Changes", "review_reject",
                         uno("RejectTrackedChangeToNext", "RejectTrackedChange", "RejectAllTrackedChanges")),
    "ReviewCompareMenu": ("Compare Documents", "review_compare", uno("CompareDocuments", "MergeDocuments")),
}
# the three language items open their submenu through a controller of their own (Controller.xcu c13-c15)
LANGUAGE_SUBMENUS = uno("SetLanguageSelectionMenu", "SetLanguageParagraphMenu", "SetLanguageAllTextMenu")
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, Review rows)
    ".uno:ReviewReadAloud": "Read Aloud", ".uno:ReviewTranslate": "Translate",
    GOTO + "previous": "Previous Comment", GOTO + "next": "Next Comment",
    MARKUP + "filter": "Filter All Markup", MARKUP + "display": "Display for Review",
    ".uno:ReviewRestrictEditing": "Restrict Editing", ".uno:ReviewHideInk": "Hide Ink"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("writer"))
REVIEW_SLOTS = [12, 13, 14, 15, 16, 17]

# design section 2 "Review (5)": command -> (class, menu-bar id that keeps it reachable).
# a: the same command is in the menu bar; b: only an equivalent entry is; c: neither.
LEFT_THE_TAB = {
    "SpellOnline": ("a", "SpellOnline"),                     # Tools > Automatic Spell Checking
    "ReplyComment": ("a", "ReplyComment"),                   # Edit > Comment > Reply Comment
    "AutoFormatMenu": ("a", "AutoFormatMenu"),               # Tools > AutoCorrect
    "ProtectTraceChangeMode": ("a", "ProtectTraceChangeMode"),  # Edit > Track Changes > Protect...
    "RedactDoc": ("a", "RedactDoc"),                         # Tools > Redact
}
# the stock commands that stay elsewhere (section 2, "Kept on another tab")
KEPT_ELSEWHERE = {"AutoCorrectDlg": "Tools", "AutoFormatApply": "Tools", "AutoFormatRedlineApply": "Tools",
                  "OnlineAutoFormat": "Tools", "Hyphenate": "Layout"}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def stock_commands(object_id):
    """The action names inside one object of the stock notebookbar.ui."""
    lines = (ROOT / "sw/uiconfig/swriter/ui/notebookbar.ui").read_text(encoding="utf-8").split("\n")
    start = next(i for i, line in enumerate(lines) if '<object' in line and 'id="%s"' % object_id in line)
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == " " * indent + "</object>")
    return set(re.findall(r'action-name">([^<]+)<', "\n".join(lines[start:end])))


class WriterReviewUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = WRITER.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Review Tab", self.layout["page"])
        self.assertEqual("Review", self.layout["id_prefix"])
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
        self.assertEqual(24, len(self.items()))  # design counts: 24 controls, 16 real, 8 placeholders

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
        """The property map of the generated button `btnReview<cmd>`."""
        for obj in ET.fromstring(self.office).iter("object"):
            if obj.get("id") == "btnReview" + cmd:
                return {p.get("name"): p.text for p in obj.findall("property")}
        self.fail("no button for " + cmd)

    def test_the_ribbon_label_of_every_button_is_words(self):
        # what the ribbon shows is the .ui label, else the command's own label (T9w leaves the label out when
        # LibreOffice already shows Word's text)
        shown = g.shown_labels(str(ROOT), "writer")
        for cmd, word in WORD_LABELS.items():
            button = self.button(cmd)
            self.assertEqual(word, button.get("label", shown[button["action-name"]]), cmd)

    def test_the_ribbon_label_differs_from_the_menu_label_where_the_menu_is_libreoffices(self):
        labels = commands_xcu(app="writer")
        for cmd, word in (("ReviewDeleteCommentMenu", "Delete"), ("ReviewAcceptMenu", "Accept"),
                          ("ReviewRejectMenu", "Reject"), ("ReviewCompareMenu", "Compare")):
            self.assertNotEqual(word, labels[".uno:" + cmd], cmd)
            self.assertEqual(word, self.button(cmd)["label"], cmd)
        # an approximate mapping: Reviewing Pane is Manage Changes
        self.assertEqual("Reviewing Pane", self.button("AcceptTrackedChanges")["label"])
        self.assertIn("Manage", labels[".uno:AcceptTrackedChanges"])

    def test_the_approximate_and_toggle_mappings_use_the_designed_commands(self):
        # decision 20: Reviewing Pane = Manage Changes; Show Comments is the LibreOffice toggle
        urls = {i["cmd"]: g.item_url(i) for i in self.items()}
        self.assertEqual(".uno:AcceptTrackedChanges", urls["AcceptTrackedChanges"])
        self.assertEqual(".uno:ShowAnnotations", urls["ShowAnnotations"])
        self.assertEqual(".uno:AccessibilityCheck", urls["AccessibilityCheck"])

    def test_nothing_cloud_or_word_only_is_on_the_page(self):
        # omitted: Editor (cloud) and Block Authors (co-authoring); the page is Word's ten groups
        self.assertEqual(10, len(self.layout["sections"]))
        labels = {i.get("office_label") for i in self.items()}
        self.assertFalse({"Editor", "Block Authors"} & labels)

    def test_the_old_review_page_and_its_overflow_menu_are_gone(self):
        self.assertEqual(["Menu Review"], self.layout["remove_objects"])
        for old in ('id="Menu Review"', "Review-ReviewButton:Menu Review", 'id="gdReviewSpelling"',
                    'id="MenuReview-'):
            self.assertNotIn(old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Review-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Review-end -->"))
        self.assertIn('id="Review Tab"', self.office)  # the page itself stays, with the tab label

    def test_the_tab_keeps_its_place_and_label(self):
        # Review is an existing page: writer_tabs.json does not move it
        tabs = json.loads(WRITER.tabs.read_text(encoding="utf-8"))
        self.assertEqual(7, tabs["positions"]["Review Tab"])
        self.assertEqual(7, tabs["positions"]["ReviewLabel"])
        self.assertEqual([], [a for a in tabs["add_pages"] if a["page"] == "Review Tab"])
        self.assertIn('context="TabbedWriter|ReviewTabLabel">~Review</property>', self.office)

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Review", {layout["id_prefix"] for layout in office.page_layouts("writer")})
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(5, len(LEFT_THE_TAB))
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
        self.assertEqual({"a": 5, "b": 0, "c": 0}, {k: sum(1 for v in LEFT_THE_TAB.values() if v[0] == k)
                                                    for k in "abc"})

    def test_the_commands_kept_elsewhere_are_still_on_their_tab_or_in_the_menu_bar(self):
        menubar = MENUBAR.read_text(encoding="utf-8")
        layout = json.loads(read("product/ui/writer_layout.json"))
        on_layout = {g.item_url(i) for s in layout["sections"] for b in g.boxes_of(s) for i in b["items"]}
        for name, where in KEPT_ELSEWHERE.items():
            self.assertIn('menu:id=".uno:%s"' % name, menubar, name)  # Tools tab (stays) is the menu's content
            if where == "Layout":
                self.assertIn(".uno:" + name, on_layout, name)

    def test_every_stock_command_is_kept_dropped_to_the_menu_bar_or_on_another_tab(self):
        # the stock page and its overflow menu: whatever is not on the new page or in its menus is in the
        # leave list or kept elsewhere
        stock = stock_commands("Review Tab") | stock_commands("Menu Review")
        on_tab = {g.item_url(i) for i in self.items()} | {u for _l, _r, items in MENUS.values() for u in items}
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
        self.assertEqual(8, len(PLACEHOLDER_LABELS))

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
                if url != SEP:
                    self.assertIn(url, labels, url)

    def test_the_registry_labels_every_review_slot(self):
        registry = placeholders.registry("writer")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items()
                                              if u.startswith(".uno:Review")})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        for offset in REVIEW_SLOTS:
            self.assertTrue(entries[offset]["command"].startswith("Review"))

    def test_every_review_placeholder_is_on_the_page_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="writer").values()}
        on_page = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, on_page, url)
            self.assertNotIn(url, controlled, url)

    def test_each_new_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        nodes = controller_nodes(app="writer")
        self.assertEqual(5, len(MENUS))
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

    def test_show_markup_and_track_changes_keep_their_stock_split_controllers(self):
        nodes = controller_nodes(app="writer")
        for url, popup in STOCK_SPLITS.items():
            ours = [v for v in nodes.values() if v["Command"] == url]
            self.assertEqual(["GenericPopupToolbarController"], [v["Controller"].rsplit(".", 1)[1] for v in ours], url)
            self.assertEqual(popup, ours[0]["Value"], url)

    def test_the_language_items_have_the_controllers_of_their_own(self):
        # the stock nodes are named c13-c15, a name that repeats in other sets of the file, so read them by command
        oor = "{http://openoffice.org/2001/registry}"
        found = {}
        for node in ET.parse(ROOT / "officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu").iter("node"):
            props = {p.get(oor + "name"): p.findtext("value") for p in node.findall("prop")}
            if props.get("Command") in LANGUAGE_SUBMENUS:
                found.setdefault(props["Command"], []).append(props["Controller"])
        self.assertEqual({url: [FRAMEWORK + "LanguageSelectionMenuController"] for url in LANGUAGE_SUBMENUS}, found)

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        # the five dropdown commands are new: only the Review page and the controller nodes name them
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

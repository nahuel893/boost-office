# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Writer Mailings tab: layout vs product/docs/writer-ribbon-tabs.md section 1 "Mailings", the two new
dropdowns (popup files, controllers, labels), the eight placeholders, and the tab's place in writer_tabs.json.

Mailings is a new page, so nothing leaves it (section 2): there is no leave list to check."""
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
LAYOUT = ROOT / "product/ui/writer_mailings.json"
OFFICE_REL = "sw/uiconfig/swriter/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sw/uiconfig/swriter/popupmenu"
TOOLBARS = ROOT / "sw/uiconfig/swriter/toolbar"
MENU = "{http://openoffice.org/2001/menu}"
TEXT_MODULE = "com.sun.star.text.TextDocument"
SEP = "-"  # a separator in a menu item list
FRAMEWORK = "com.sun.star.comp.framework."


def uno(*names):
    return [".uno:" + name for name in names]


FIELD = ".uno:MailingsField?Field:string="
PREVIEW = ".uno:MailingsPreview?Action:string="
# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Mailings".
# Size: L = large, S = small-label, I = icon only (the record buttons and the record box share one toolbox).
DESIGN = {
    "Create": ("Create", 3, [
        ("large", uno("InsertEnvelope")), ("large", uno("InsertLabels"))]),
    "StartMailMerge": ("Start Mail Merge", 3, [
        ("large", uno("MailMergeWizard")), ("large", uno("MailingsSelectRecipientsMenu")),
        ("large", uno("ViewDataSourceBrowser"))]),
    "WriteInsertFields": ("Write & Insert Fields", 3, [
        ("large", uno("Marks")), ("large", [FIELD + "addressblock"]), ("large", [FIELD + "greetingline"]),
        ("large", uno("InsertField")),
        ("small-label", [FIELD + "rules"]), ("small-label", [FIELD + "matchfields"]),
        ("small-label", [FIELD + "updatelabels"])]),
    "PreviewResults": ("Preview Results", 3, [
        ("large", [PREVIEW + "toggle"]),
        ("small", uno("MailMergeFirstEntry", "MailMergePrevEntry", "MailMergeCurrentEntry",
                      "MailMergeNextEntry", "MailMergeLastEntry")),
        ("small-label", [PREVIEW + "find"]), ("small-label", [PREVIEW + "check"])]),
    "Finish": ("Finish", 3, [
        ("large", uno("MailingsFinishMenu"))]),
}
SHAPES = {"Create": [1, 1], "StartMailMerge": [1, 1, 1], "WriteInsertFields": [1, 1, 1, 1, 3],
          "PreviewResults": [1, 3], "Finish": [1]}
# Word's label per widget command (T9w: the ribbon shows it, unless it equals LibreOffice's label)
WORD_LABELS = {
    "InsertEnvelope": "Envelopes", "InsertLabels": "Labels", "MailMergeWizard": "Start Mail Merge",
    "MailingsSelectRecipientsMenu": "Select Recipients", "ViewDataSourceBrowser": "Edit Recipient List",
    "Marks": "Highlight Merge Fields", "MailingsAddressBlock": "Address Block",
    "MailingsGreetingLine": "Greeting Line", "InsertField": "Insert Merge Field", "MailingsRules": "Rules",
    "MailingsMatchFields": "Match Fields", "MailingsUpdateLabels": "Update Labels",
    "MailingsPreviewResults": "Preview Results", "MailMergeFirstEntry": "First Record",
    "MailMergePrevEntry": "Previous Record", "MailMergeCurrentEntry": "Record box",
    "MailMergeNextEntry": "Next Record", "MailMergeLastEntry": "Last Record",
    "MailingsFindRecipient": "Find Recipient", "MailingsCheckForErrors": "Check for Errors",
    "MailingsFinishMenu": "Finish & Merge"}
# the dropdowns: Word's two (Select Recipients, Finish & Merge) are new commands; Word's Start Mail Merge and
# Insert Merge Field dropdowns stay plain buttons (LibreOffice has a wizard and a dialog there)
SPLITS = {"MailingsSelectRecipientsMenu", "MailingsFinishMenu"}

# command -> (label, popup resource, popup items in order); design section 1 "Menu contents".
# The label is also the menu's, so it is LibreOffice-style; Word's is office_label.
MENUS = {
    "MailingsSelectRecipientsMenu": ("Select Recipients", "mailings_selectrecipients",
                                     uno("AddressBookSource", "ChangeDatabaseField")),
    "MailingsFinishMenu": ("Finish Mail Merge", "mailings_finish",
                           uno("MailMergeCreateDocuments", "MailMergePrintDocuments",
                               "MailMergeEmailDocuments", "MailMergeSaveDocuments")),
}
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, Mailings rows)
    FIELD + "addressblock": "Address Block", FIELD + "greetingline": "Greeting Line", FIELD + "rules": "Rules",
    FIELD + "matchfields": "Match Fields", FIELD + "updatelabels": "Update Labels",
    PREVIEW + "toggle": "Preview Results", PREVIEW + "find": "Find Recipient", PREVIEW + "check": "Check for Errors"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("writer"))
MAILINGS_SLOTS = [10, 11]
# the record buttons and the record box serve only a mail merge in progress (sw/sdi/wrtapp.sdi:66-119)
RECORD_COMMANDS = uno("MailMergeFirstEntry", "MailMergePrevEntry", "MailMergeCurrentEntry",
                      "MailMergeNextEntry", "MailMergeLastEntry")

# design section 1 "Tab order and labels": Mailings is page 6, after References. The mnemonic is not the
# design's "~Mailings": M repeats the contextual Media tab, A is free among the Writer tabs.
TAB_LABEL = "M~ailings"
POSITIONS = {  # id -> position; every page and tab label after References shifts by one
    "Layout Tab": 4, "LayoutLabel": 4, "References Tab": 5, "ReferencesLabel": 5,
    "Mailings Tab": 6, "MailingsLabel": 6,
    "Review Tab": 7, "ReviewLabel": 7, "View Tab": 8, "ViewLabel": 8,
    "Table Tab": 9, "TableLabel": 9, "Image Tab": 10, "ImageLabel": 10, "Draw Tab": 11, "DrawLabel": 11,
    "Object Tab": 12, "ObjectLabel": 12, "Media Tab": 13, "MediaLabel": 13, "Print Tab": 14, "PrintLabel": 14,
    "Form Tab": 15, "FormLabel": 15, "Extension Tab": 16, "ExtensionLabel": 16,
    "Tools Tab": 17, "ToolsLabel": 17}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class WriterMailingsUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = WRITER.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Mailings Tab", self.layout["page"])
        self.assertEqual("Mailings", self.layout["id_prefix"])
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
        self.assertEqual(21, len(self.items()))  # design counts: 21 controls, 13 real, 8 placeholders

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
        """The property map of the generated button `btnMailings<cmd>`."""
        for obj in ET.fromstring(self.office).iter("object"):
            if obj.get("id") == "btnMailings" + cmd:
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
        # Finish & Merge: the menu says "Finish Mail Merge", the ribbon "Finish & Merge"
        labels = commands_xcu(app="writer")
        self.assertEqual("Finish Mail Merge", labels[".uno:MailingsFinishMenu"])
        self.assertEqual("Finish & Merge", self.button("MailingsFinishMenu")["label"])
        self.assertEqual("Mail Merge Wizard", labels[".uno:MailMergeWizard"].rstrip(".").replace("~", ""))
        self.assertEqual("Start Mail Merge", self.button("MailMergeWizard")["label"])

    def test_nothing_cloud_or_word_only_is_on_the_page(self):
        # the design omits no Mailings control: the page is Word's five groups, nothing else
        self.assertEqual(5, len(self.layout["sections"]))
        self.assertNotIn("remove_objects", self.layout)  # a new page replaces nothing

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Mailings", {layout["id_prefix"] for layout in office.page_layouts("writer")})
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_the_page_follows_references_with_the_designed_tab_label(self):
        tabs = json.loads(WRITER.tabs.read_text(encoding="utf-8"))
        self.assertEqual({k: v for k, v in POSITIONS.items() if not k.startswith("Mailings")}, tabs["positions"])
        adds = [a for a in tabs["add_pages"] if a["page"] == "Mailings Tab"]
        self.assertEqual([{"page": "Mailings Tab", "prefix": "Mailings", "after_tab": "ReferencesLabel",
                           "position": 6, "tab_id": "MailingsLabel", "label": TAB_LABEL,
                           "context": "TabbedWriter|MailingsTabLabel"}], adds)
        # the generated UI: every page and tab label sits at its position
        root = ET.fromstring(self.office)
        parent = {child: node for node in root.iter() for child in node}
        for wid, position in POSITIONS.items():
            obj = next(o for o in root.iter("object") if o.get("id") == wid)
            packing = parent[obj].find("packing/property[@name='position']")
            self.assertEqual(str(position), packing.text, wid)

    def test_the_tab_label_is_the_first_text_of_its_context_and_its_mnemonic_is_free(self):
        self.assertIn('<property name="label" translatable="yes" context="TabbedWriter|MailingsTabLabel">'
                      + TAB_LABEL + '</property>', self.office)
        letters = {}
        for context, text in re.findall(r'context="TabbedWriter\|(\w+TabLabel)">([^<]*)<', self.office):
            match = re.search(r"~(.)", text)
            if match:
                letters.setdefault(match.group(1).lower(), []).append(context)
        self.assertEqual(["MailingsTabLabel"], letters["a"])  # A: no other Writer tab uses it

    def test_the_tabs_are_in_words_order(self):
        order = re.findall(r'context="TabbedWriter\|(\w+)TabLabel"', self.office)
        self.assertEqual(["File", "Home", "Insert", "Design", "Layout", "References", "Mailings", "Review", "View",
                          "Table", "Image", "Draw", "Object", "Media", "Print", "Form", "Tools", "Help"],
                         [t for t in order if t != "Extension"])

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
                self.assertIn(url, labels, url)

    def test_the_registry_labels_every_mailings_slot(self):
        registry = placeholders.registry("writer")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items()
                                              if u.startswith(".uno:Mailings")})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        for offset in MAILINGS_SLOTS:
            self.assertTrue(entries[offset]["command"].startswith("Mailings"))

    def test_every_mailings_placeholder_is_on_the_page_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="writer").values()}
        on_page = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, on_page, url)
            self.assertNotIn(url, controlled, url)

    def test_the_record_controls_keep_their_stock_controllers(self):
        # the record box is an entry field of the stock Controller.xcu node (lo.writer.MMCurrentEntryController);
        # this task adds no controller to the four record commands
        nodes = controller_nodes(app="writer")
        for url in RECORD_COMMANDS:
            ours = [k for k, v in nodes.items() if v["Command"] == url]
            self.assertLessEqual(len(ours), 1, url)
            self.assertTrue(all(k.startswith("lo.writer.") for k in ours), url)

    def test_each_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        nodes = controller_nodes(app="writer")
        self.assertEqual(2, len(MENUS))
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
        # the two dropdown commands are new: only the Mailings page and the controller nodes name them
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

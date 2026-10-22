# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Writer Home tab: layout vs product/docs/writer-ribbon-tabs.md section 1 "Home", the four new
dropdowns (popup files, controllers, labels), the placeholder menu items, and the commands that leave
the tab (section 2, "Home (32)")."""
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
LAYOUT = ROOT / "product/ui/writer_home.json"
OFFICE_REL = "sw/uiconfig/swriter/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sw/uiconfig/swriter/popupmenu"
MENUBAR = ROOT / "sw/uiconfig/swriter/menubar/menubar.xml"
SHORTCUTS = ROOT / "sw/uiconfig/swriter/toolbar/notebookbarshortcuts.xml"
MENU = "{http://openoffice.org/2001/menu}"
TEXT_MODULE = "com.sun.star.text.TextDocument"
SEP = "-"  # a separator in a menu item list
EFFECT = ".uno:HomeTextEffect?Effect:string="
FINDBAR = "vnd.sun.star.findbar:FocusToFindbar"


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Home".
# Size: I = small (icon), L = large, S = small-label, gal = large (the Styles gallery spans the section).
DESIGN = {
    "Undo": ("Undo", 2, [("small", uno("Undo")), ("small", uno("Redo"))]),
    "Clipboard": ("Clipboard", 3, [("large", uno("Paste")), ("small", uno("Cut")), ("small", uno("Copy")),
                                   ("small", uno("FormatPaintbrush"))]),
    "Font": ("Font", 2, [("small", uno("CharFontName", "FontHeight", "Grow", "Shrink", "HomeChangeCaseMenu",
                                       "ResetAttributes")),
                         ("small", uno("Bold", "Italic", "Underline", "Strikeout", "SubScript", "SuperScript",
                                       "HomeTextEffectsMenu", "CharBackColor", "Color"))]),
    "Paragraph": ("Paragraph", 2, [("small", uno("DefaultBullet", "DefaultNumbering", "SetOutline",
                                                 "DecrementIndent", "IncrementIndent", "SortDialog",
                                                 "ControlCodes")),
                                   ("small", uno("LeftPara", "CenterPara", "RightPara", "JustifyPara",
                                                 "LineSpacing", "BackgroundColor", "BorderDialog"))]),
    "Styles": ("Styles", 3, [("large", uno("StylesPreview"))]),
    "Editing": ("Editing", 3, [("small-label", uno("HomeFindMenu")), ("small-label", uno("SearchDialog")),
                               ("small-label", uno("HomeSelectMenu"))]),
    "Editor": ("Editor", 3, [("large", uno("SpellingAndGrammarDialog"))]),
}
SHAPES = {"Undo": [2], "Clipboard": [1, 3], "Font": [2], "Paragraph": [2], "Styles": [1], "Editing": [3],
          "Editor": [1]}
# Word's label per item (T9w: the ribbon shows it, unless it equals LibreOffice's label; menus keep LibreOffice's)
WORD_LABELS = {
    "Undo": "Undo", "Redo": "Redo", "Paste": "Paste", "Cut": "Cut", "Copy": "Copy",
    "FormatPaintbrush": "Format Painter", "CharFontName": "Font", "FontHeight": "Font Size",
    "Grow": "Increase Font Size", "Shrink": "Decrease Font Size", "HomeChangeCaseMenu": "Change Case",
    "ResetAttributes": "Clear All Formatting", "Bold": "Bold", "Italic": "Italic", "Underline": "Underline",
    "Strikeout": "Strikethrough", "SubScript": "Subscript", "SuperScript": "Superscript",
    "HomeTextEffectsMenu": "Text Effects and Typography", "CharBackColor": "Text Highlight Color",
    "Color": "Font Color", "DefaultBullet": "Bullets", "DefaultNumbering": "Numbering",
    "SetOutline": "Multilevel List", "DecrementIndent": "Decrease Indent", "IncrementIndent": "Increase Indent",
    "SortDialog": "Sort", "ControlCodes": "Show/Hide", "LeftPara": "Align Left", "CenterPara": "Center",
    "RightPara": "Align Right", "JustifyPara": "Justify", "LineSpacing": "Line and Paragraph Spacing",
    "BackgroundColor": "Shading", "BorderDialog": "Borders", "StylesPreview": "Styles",
    "HomeFindMenu": "Find", "SearchDialog": "Replace", "HomeSelectMenu": "Select",
    "SpellingAndGrammarDialog": "Editor"}
SPLITS = {"Undo", "Redo", "Paste", "Underline", "CharBackColor", "Color", "DefaultBullet", "DefaultNumbering",
          "SetOutline", "LineSpacing", "BackgroundColor", "HomeChangeCaseMenu", "HomeTextEffectsMenu",
          "HomeFindMenu", "HomeSelectMenu"}

# command -> (label, popup resource, popup items in order); design section 1 "Menu contents"
MENUS = {
    "HomeChangeCaseMenu": ("Change Case", "home_changecase",
                           uno("ChangeCaseToSentenceCase", "ChangeCaseToLower", "ChangeCaseToUpper",
                               "ChangeCaseToTitleCase", "ChangeCaseToToggleCase")),
    "HomeTextEffectsMenu": ("Text Effects and Typography", "home_texteffects",
                            uno("OutlineFont", "Shadowed") + [SEP]
                            + [EFFECT + v for v in ("reflection", "glow", "numberstyles", "ligatures",
                                                    "stylisticsets")]),
    "HomeFindMenu": ("Find", "home_find", [FINDBAR] + uno("SearchDialog", "GotoPage")),
    "HomeSelectMenu": ("Select", "home_select", uno("SelectAll", "SelectObject", "HomeSelectSimilar", "Navigator")),
}
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, Home rows)
    EFFECT + "reflection": "Reflection", EFFECT + "glow": "Glow", EFFECT + "numberstyles": "Number Styles",
    EFFECT + "ligatures": "Ligatures", EFFECT + "stylisticsets": "Stylistic Sets",
    ".uno:HomeSelectSimilar": "Select Text with Similar Formatting"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("writer"))
HOME_SLOTS = [0, 1]

# design section 2 "Home (32)": command -> (class, menu-bar id that keeps it reachable).
# a: the same command is in the menu bar; b: only an equivalent entry is.
LEFT_THE_TAB = {
    "Spacing": ("b", "FontDialog"), "StartPara": ("b", "CommonAlignStart"), "EndPara": ("b", "CommonAlignEnd"),
    "HangingIndent": ("b", "ParagraphDialog"), "ParaLeftToRight": ("b", "ParagraphDialog"),
    "ParaRightToLeft": ("b", "ParagraphDialog"),
    "ParaspaceIncrease": ("a", "ParaspaceIncrease"), "ParaspaceDecrease": ("a", "ParaspaceDecrease"),
    "Overline": ("a", "Overline"), "ChangeCaseRotateCase": ("a", "ChangeCaseRotateCase"),
    "DecrementLevel": ("a", "DecrementLevel"), "IncrementLevel": ("a", "IncrementLevel"),
    "DecrementSubLevels": ("a", "DecrementSubLevels"), "IncrementSubLevels": ("a", "IncrementSubLevels"),
    "InsertNeutralParagraph": ("a", "InsertNeutralParagraph"), "NumberingStart": ("a", "NumberingStart"),
    "ContinueNumbering": ("a", "ContinueNumbering"), "InsertNonBreakingSpace": ("a", "InsertNonBreakingSpace"),
    "InsertHardHyphen": ("a", "InsertHardHyphen"), "InsertSoftHyphen": ("a", "InsertSoftHyphen"),
    "InsertZWSP": ("a", "InsertZWSP"), "InsertWJ": ("a", "InsertWJ"), "InsertLRM": ("a", "InsertLRM"),
    "InsertRLM": ("a", "InsertRLM"), "FontDialog": ("a", "FontDialog"), "OutlineBullet": ("a", "OutlineBullet"),
    "ParagraphDialog": ("a", "ParagraphDialog"), "ChapterNumberingDialog": ("a", "ChapterNumberingDialog"),
    "SelectionModeDefault": ("a", "SelectionModeDefault"), "SelectionModeBlock": ("a", "SelectionModeBlock"),
    "SelectTextMode": ("a", "SelectTextMode"), "ShadowCursor": ("a", "ShadowCursor"),
}
OLD_PAGE_WIDGETS = ["btnHomeFocusToFindbar", "btnHomeStylesPreview"]  # stock ids that must not appear twice


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class WriterHomeUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = WRITER.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Home Tab", self.layout["page"])
        self.assertEqual("Home", self.layout["id_prefix"])
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
        self.assertEqual(40, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_styles_gallery_alone_takes_the_free_width_of_home(self):
        # Word: the Styles gallery is the widest group on Home and the one that flexes, so it
        # shrinks first (research-word365-ribbon.md, "1920 px fit"). Stock notebookbar.ui does the
        # same with hexpand on gdHomeStyle and bxHomeStylesPreview and expand on the item.
        expanding = [b["id"] for s in self.layout["sections"] for b in self.boxes(s) if b.get("expand")]
        self.assertEqual(["StylesPreview"], expanding)
        page = ET.fromstring(self.office).find(".//object[@id='pmhbHome']")
        got = {obj.get("id") for obj in page.iter("object")
               if [p.text for p in obj.findall("property[@name='hexpand']")] == ["True"]}
        self.assertEqual({"obHomeStyles", "gdHomeStyles", "gcHomeStyles", "bxHomeStylesPreview"}, got)
        item = next(c for c in page.iter("child") if c.find("object").get("id") == "btnHomeStylesPreview")
        self.assertEqual("True", item.find("packing/property[@name='expand']").text)

    def test_the_dropdowns_and_split_buttons_are_split_the_rest_are_plain(self):
        for item in self.items():
            expected = "split" if item["cmd"] in SPLITS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_words_label_in_office_label(self):
        # T9w: gen_ribbon turns office_label into the button's label; menus, help and tooltips keep LibreOffice's
        self.assertEqual(WORD_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_the_old_home_page_and_its_overflow_menu_are_gone(self):
        self.assertIn("Menu Home", self.layout["remove_objects"])
        for old in ('id="Menu Home"', "Home-HomeButton:Menu Home", 'id="Home-Menu"', 'id="MenuHome-'):
            self.assertNotIn(old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Home-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Home-end -->"))
        self.assertIn('id="Home Tab"', self.office)  # the page itself stays, with the tab label

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Home", {layout["id_prefix"] for layout in office.page_layouts("writer")})
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(32, len(LEFT_THE_TAB))
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)
            if kind == "a":
                self.assertEqual(name, menu_id)
            else:
                self.assertNotEqual(name, menu_id)
                self.assertNotIn('menu:id=".uno:%s"' % name, menubar, name + " is not in the menu bar: class b")

    def test_undo_stays_on_home_and_in_the_quick_access_bar(self):
        shortcuts = SHORTCUTS.read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()}
        for name in ("Undo", "Redo"):
            self.assertIn('xlink:href=".uno:%s"' % name, shortcuts)
            self.assertIn(".uno:" + name, on_tab)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="writer")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_new_menus_and_placeholder_items_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="writer"), tooltips(app="writer")
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
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
        generic = read("officecfg/registry/data/org/openoffice/Office/UI/GenericCommands.xcu")
        for _label, _resource, items in MENUS.values():
            for url in items:
                if url == SEP:
                    continue
                if url == FINDBAR:
                    self.assertIn('oor:name="%s"' % url, generic)
                else:
                    self.assertIn(url, labels, url)

    def test_the_registry_labels_every_home_slot_and_variant(self):
        registry = placeholders.registry("writer")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items() if u.startswith(".uno:Home")})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        self.assertEqual(["Effect:string=" + v for v in ("reflection", "glow", "numberstyles", "ligatures",
                                                         "stylisticsets")], entries[0]["variants"])
        self.assertEqual("Select Text with Similar Formatting", entries[1]["label"])
        for offset in HOME_SLOTS:
            self.assertTrue(entries[offset]["command"].startswith("Home"))

    def test_the_placeholder_items_have_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes().values()}
        for url in PLACEHOLDER_LABELS:
            self.assertNotIn(url, controlled, url)

    def test_each_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        nodes = controller_nodes()
        self.assertEqual(4, len(MENUS))
        for cmd, (_label, resource, _items) in MENUS.items():
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd]
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in ours}
            self.assertEqual({"ResourceMenuController", "GenericPopupToolbarController"}, set(kinds), cmd)
            for kind in kinds.values():
                self.assertEqual(TEXT_MODULE, kind["Module"])
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])
            self.assertEqual(resource, kinds["ResourceMenuController"]["Value"])

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        # the four dropdown commands are new: only the Home page and the two controller nodes name them
        toolbars = [p for p in (ROOT / "sw/uiconfig/swriter/toolbar").glob("*.xml")]
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

    def test_the_find_menu_starts_with_the_find_toolbar(self):
        items = self.menu_ids(ET.parse(POPUPMENU / "home_find.xml").getroot())
        self.assertEqual(FINDBAR, items[0])

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

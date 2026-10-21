# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Writer Layout tab: layout vs product/docs/writer-ribbon-tabs.md section 1 "Layout", the seven
new dropdowns (popup files, controllers, labels), the five new label nodes, and the commands that leave
the tab (section 2, "Layout (5)")."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import office
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
WRITER = office.app("writer")
LAYOUT = ROOT / "product/ui/writer_layout.json"
OFFICE_REL = "sw/uiconfig/swriter/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sw/uiconfig/swriter/popupmenu"
TOOLBARS = ROOT / "sw/uiconfig/swriter/toolbar"
MENUBAR = ROOT / "sw/uiconfig/swriter/menubar/menubar.xml"
MENU = "{http://openoffice.org/2001/menu}"
TEXT_MODULE = "com.sun.star.text.TextDocument"
CALC_MODULE = "com.sun.star.sheet.SpreadsheetDocument"
SEP = "-"  # a separator in a menu item list
FRAMEWORK = "com.sun.star.comp.framework."


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Layout".
# Size: L = large, S = small-label, spin = the four paragraph fields (small boxes).
DESIGN = {
    "PageSetup": ("Page Setup", 3, [
        ("large", uno("PageMargin")), ("large", uno("Orientation")), ("large", uno("AttributePageSize")),
        ("large", uno("PageColumnType")),
        ("small-label", uno("LayoutBreaksMenu")), ("small-label", uno("LineNumberingDialog")),
        ("small-label", uno("Hyphenate"))]),
    "Paragraph": ("Paragraph", 3, [
        ("small", uno("LeftParaMargin")), ("small", uno("RightParaMargin")),
        ("small", uno("AboveSpacing")), ("small", uno("BelowSpacing"))]),
    "Arrange": ("Arrange", 3, [
        ("large", uno("AnchorMenu")), ("large", uno("LayoutWrapTextMenu")),
        ("large", uno("PageLayoutBringForwardMenu")), ("large", uno("PageLayoutSendBackwardMenu")),
        ("large", uno("Navigator")),
        ("small-label", uno("PageLayoutAlignMenu")), ("small-label", uno("PageLayoutGroupMenu")),
        ("small-label", uno("PageLayoutRotateMenu"))]),
}
SHAPES = {"PageSetup": [1, 1, 1, 1, 3], "Paragraph": [2, 2], "Arrange": [1, 1, 1, 1, 1, 3]}
# Word: a caption row (Indent, Spacing) then two spin rows, so the spins start on the second row
SPIN_ROWS = {"LeftParaMargin": 1, "AboveSpacing": 1}
# Word's label per item (design decision 29: it stays in "office_label" until T9 is decided)
WORD_LABELS = {
    "PageMargin": "Margins", "Orientation": "Orientation", "AttributePageSize": "Size",
    "PageColumnType": "Columns", "LayoutBreaksMenu": "Breaks", "LineNumberingDialog": "Line Numbers",
    "Hyphenate": "Hyphenation", "LeftParaMargin": "Indent Left", "RightParaMargin": "Indent Right",
    "AboveSpacing": "Spacing Before", "BelowSpacing": "Spacing After", "AnchorMenu": "Position",
    "LayoutWrapTextMenu": "Wrap Text", "PageLayoutBringForwardMenu": "Bring Forward",
    "PageLayoutSendBackwardMenu": "Send Backward", "Navigator": "Selection Pane",
    "PageLayoutAlignMenu": "Align", "PageLayoutGroupMenu": "Group", "PageLayoutRotateMenu": "Rotate"}
SPINS = ("LeftParaMargin", "RightParaMargin", "AboveSpacing", "BelowSpacing")
# Word's dropdowns: the seven new menus and the five stock ones that already have a controller
SPLITS = {"PageMargin", "Orientation", "AttributePageSize", "PageColumnType", "LayoutBreaksMenu", "AnchorMenu",
          "LayoutWrapTextMenu", "PageLayoutBringForwardMenu", "PageLayoutSendBackwardMenu",
          "PageLayoutAlignMenu", "PageLayoutGroupMenu", "PageLayoutRotateMenu"}
# the stock dropdowns' own controllers (design section 1 evidence)
STOCK_CONTROLLERS = {
    "PageMargin": "lo.writer.PageMarginToolBoxControl", "Orientation": "lo.writer.PageOrientationToolBoxControl",
    "AttributePageSize": "lo.writer.PageSizeToolBoxControl", "PageColumnType": "lo.writer.PageColumnToolBoxControl"}

# command -> (label, popup resource, popup items in order); design section 1 "Menu contents"
MENUS = {
    "LayoutBreaksMenu": ("Breaks", "layout_breaks",
                         uno("InsertPagebreak", "InsertColumnBreak", "InsertLinebreak") + [SEP]
                         + uno("InsertBreak", "InsertSection")),
    "LayoutWrapTextMenu": ("Wrap Text", "layout_wraptext",
                           uno("SetAnchorToChar", "WrapOn", "WrapContour", "WrapOff", "WrapThroughTransparent",
                               "WrapThrough") + [SEP] + uno("ContourDialog", "TextWrap")),
    "PageLayoutBringForwardMenu": ("Bring Forward", "layout_bringforward",
                                   uno("ObjectForwardOne", "BringToFront", "SetObjectToForeground")),
    "PageLayoutSendBackwardMenu": ("Send Backward", "layout_sendbackward",
                                   uno("ObjectBackOne", "SendToBack", "SetObjectToBackground")),
    "PageLayoutAlignMenu": ("Align", "layout_align",
                            uno("ObjectAlignLeft", "AlignCenter", "ObjectAlignRight", "AlignUp", "AlignMiddle",
                                "AlignDown")),
    "PageLayoutGroupMenu": ("Group", "layout_group", uno("FormatGroup", "FormatUngroup")),
    "PageLayoutRotateMenu": ("Rotate", "layout_rotate",
                             uno("RotateRight", "RotateLeft", "FlipVertical", "FlipHorizontal") + [SEP]
                             + uno("TransformDialog")),
}
# the dropdown commands that Calc already owns (its names, Writer nodes with a "Writer" suffix)
CALC_NAMES = {"PageLayoutBringForwardMenu", "PageLayoutSendBackwardMenu", "PageLayoutAlignMenu",
              "PageLayoutGroupMenu", "PageLayoutRotateMenu"}
NEW_LABELS = {  # the five missing label nodes of the plan (LibreOffice's own wording; Word's is office_label)
    ".uno:LeftParaMargin": "Before Text Indent", ".uno:RightParaMargin": "After Text Indent",
    ".uno:AboveSpacing": "Above Paragraph Spacing", ".uno:BelowSpacing": "Below Paragraph Spacing"}

# design section 2 "Layout (5)": command -> (class, menu-bar id that keeps it reachable).
# a: the same command is in the menu bar; b: only an equivalent entry is.
LEFT_THE_TAB = {
    "WrapIdeal": ("a", "WrapIdeal"), "WrapLeft": ("a", "WrapLeft"), "WrapRight": ("a", "WrapRight"),
    "PageColumnDialog": ("b", "FormatColumns"), "UseHeaderFooterMenu": ("a", "UseHeaderFooterMenu"),
}
# the stock commands that stay on another tab (section 2, "Kept on another tab")
KEPT_ELSEWHERE = {"PageDialog": "Design", "Watermark": "Design", "TitlePageDialog": "Insert",
                  "PageNumberWizard": "Insert"}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def stock_commands(object_id):
    """The action names inside one object of the stock notebookbar.ui."""
    lines = (ROOT / "sw/uiconfig/swriter/ui/notebookbar.ui").read_text(encoding="utf-8").split("\n")
    start = next(i for i, line in enumerate(lines) if '<object' in line and 'id="%s"' % object_id in line)
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == " " * indent + "</object>")
    return set(re.findall(r'action-name">([^<]+)<', "\n".join(lines[start:end])))


class WriterLayoutUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = WRITER.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Layout Tab", self.layout["page"])
        self.assertEqual("Layout", self.layout["id_prefix"])
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
        self.assertEqual(19, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_paragraph_spins_start_on_the_second_row_under_word_caption_row(self):
        paragraph = next(s for s in self.layout["sections"] if s["name"] == "Paragraph")
        for column in paragraph["columns"]:
            self.assertEqual(SPIN_ROWS[column[0]["items"][0]["cmd"]], column[0]["row"])
            self.assertEqual([1, 2], g.rows_of(column))

    def test_the_dropdowns_are_split_the_rest_are_plain_buttons(self):
        for item in self.items():
            expected = "split" if item["cmd"] in SPLITS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_words_label_in_office_label(self):
        # design decision 29: nothing is renamed now; either T9 option can be applied later
        self.assertEqual(WORD_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_text_direction_is_omitted_and_the_old_layout_page_and_its_overflow_menu_are_gone(self):
        self.assertNotIn("TextDirection", {i["cmd"] for i in self.items()})
        self.assertIn("Menu Page", self.layout["remove_objects"])
        for old in ('id="Menu Page"', "Layout-PageButton:Menu Page", 'id="Layout-Menu"', 'id="MenuPage-',
                    'id="gdLayoutParagraphLayout"', 'id="boxLeftParaMargin"'):
            self.assertNotIn(old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Layout-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Layout-end -->"))
        self.assertIn('id="Layout Tab"', self.office)  # the page itself stays, with the tab label

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Layout", {layout["id_prefix"] for layout in office.page_layouts("writer")})
        self.assertEqual(office.expected_office_ui("writer"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_the_layout_page_still_fills_the_tab_page(self):
        # the stock page centers (notebookbar.ui "Layout Tab"); writer_tabs.json sets fill, as Home does
        tabs = json.loads(WRITER.tabs.read_text(encoding="utf-8"))
        self.assertIn({"id": "Layout Tab", "name": "valign", "from": "center", "to": "fill"}, tabs["properties"])

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
        self.assertEqual({"a": 4, "b": 1}, {k: sum(1 for v in LEFT_THE_TAB.values() if v[0] == k) for k in "ab"})

    def test_every_stock_command_is_kept_dropped_to_the_menu_bar_or_on_another_tab(self):
        # the stock page and its overflow menu: whatever is not on the new page is in the leave list or kept
        stock = stock_commands("Layout Tab") | stock_commands("Menu Page")
        on_tab = {g.item_url(i) for i in self.items()}
        left = {".uno:" + n for n in LEFT_THE_TAB}
        elsewhere = {".uno:" + n for n in KEPT_ELSEWHERE}
        # SelectObject, BorderDialog, ThemeDialog and the header/footer commands stay on Home, Design, Insert
        other_tabs = {".uno:SelectObject", ".uno:BorderDialog", ".uno:ThemeDialog", ".uno:InsertPageHeader",
                      ".uno:InsertPageFooter"}
        # the Insert menu items now in the new dropdowns or on other pages
        in_menus = {".uno:" + url[len(".uno:"):] for _l, _r, items in MENUS.values() for url in items
                    if url != SEP}
        self.assertEqual(set(), stock - on_tab - left - elsewhere - other_tabs - in_menus)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="writer")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_four_spin_commands_have_label_nodes_of_their_own(self):
        labels = commands_xcu(app="writer")
        flagged = flagged_commands(app="writer")
        xcu = read("officecfg/registry/data/org/openoffice/Office/UI/WriterCommands.xcu")
        for url, label in NEW_LABELS.items():
            self.assertIn('<node oor:name="%s" oor:op="replace">' % url, xcu, url)
            self.assertEqual(label, labels[url], url)
            self.assertIn(url, flagged, url)

    def test_the_new_menus_have_the_designed_labels_and_the_image_flag(self):
        labels, flagged = commands_xcu(app="writer"), flagged_commands(app="writer")
        self.assertEqual(7, len(MENUS))
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd], cmd)
            self.assertIn(".uno:" + cmd, flagged, cmd)

    def test_the_menu_items_are_known_commands(self):
        labels = commands_xcu(app="writer")
        for _label, _resource, items in MENUS.values():
            for url in items:
                if url != SEP:
                    self.assertIn(url, labels, url)

    def test_each_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        nodes = controller_nodes(app="writer")
        for cmd, (_label, resource, _items) in MENUS.items():
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd and v.get("Module") == TEXT_MODULE]
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in ours}
            self.assertEqual({"ResourceMenuController", "GenericPopupToolbarController"}, set(kinds), cmd)
            self.assertNotIn("Value", kinds["GenericPopupToolbarController"])
            self.assertEqual(resource, kinds["ResourceMenuController"]["Value"])
            for v in ours:
                self.assertTrue(v["Controller"].startswith(FRAMEWORK))

    def test_the_writer_nodes_of_calcs_names_carry_a_writer_suffix_and_calcs_are_untouched(self):
        nodes = controller_nodes(app="writer")
        for cmd in CALC_NAMES:
            calc = {k for k, v in nodes.items() if v["Command"] == ".uno:" + cmd and v.get("Module") == CALC_MODULE}
            self.assertEqual({cmd + "Popup", cmd + "Control"}, calc)
            ours = {k for k, v in nodes.items() if v["Command"] == ".uno:" + cmd and v.get("Module") == TEXT_MODULE}
            self.assertEqual({cmd + "WriterPopup", cmd + "WriterControl"}, ours)
        for cmd in set(MENUS) - CALC_NAMES:
            ours = {k for k, v in nodes.items() if v["Command"] == ".uno:" + cmd}
            self.assertEqual({cmd + "Popup", cmd + "Control"}, ours)

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        # the seven dropdown commands are new to Writer: only the Layout page and the controller nodes name them
        toolbars = list(TOOLBARS.glob("*.xml"))
        uis = [p for p in (ROOT / "sw/uiconfig/swriter/ui").glob("notebookbar*.ui") if p != WRITER.office]
        self.assertTrue(toolbars and uis)
        for cmd in MENUS:
            for path in toolbars + uis:
                self.assertNotIn(".uno:" + cmd, path.read_text(encoding="utf-8"), "%s in %s" % (cmd, path.name))

    def test_the_stock_dropdowns_keep_their_own_controllers(self):
        nodes = controller_nodes(app="writer")
        for cmd, controller in STOCK_CONTROLLERS.items():
            self.assertTrue(any(v["Command"] == ".uno:" + cmd and v["Controller"] == controller
                                for v in nodes.values()), cmd)
        self.assertTrue(any(v["Command"] == ".uno:AnchorMenu" and v["Controller"].endswith("ResourceMenuController")
                            and v["Value"] == "anchor" for v in nodes.values()))

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
        for cmd, (_label, resource, items) in MENUS.items():
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

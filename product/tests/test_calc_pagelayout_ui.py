# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Page Layout tab: layout vs product/docs/design/calc-pagelayout-tab-layout.txt, labels, menus,
the Print Titles alias and the Orientation trap (risk R8)."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import office, placeholders
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands, tooltips
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_pagelayout.json"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
SUPPR = ROOT / "solenv/sanitizers/ui/modules/scalc.suppr"
POPUPMENU = ROOT / "sc/uiconfig/scalc/popupmenu"
MENU = "{http://openoffice.org/2001/menu}"
PART = ".uno:PageLayoutThemePart?Part:string="
FIT = ".uno:PageLayoutScaleToFit?Dimension:string="
OPTION = ".uno:PageLayoutPrintOption?Option:string="
ORIENTATION = ".uno:Orientation?isLandscape:bool="
SIZE = ".uno:CalcPageSize?PaperFormat:short="
MARGIN = (".uno:CalcPageMargin?Page.LeftMargin:long=%d&Page.RightMargin:long=%d"
          "&Page.TopMargin:long=%d&Page.BottomMargin:long=%d")

# section -> (caption, [(style, [url, ...]) per toolbox in document order])
DESIGN = {
    "Themes": ("Themes", [("large", [".uno:ChooseDesign"]), ("small-label", [".uno:ThemeDialog"]),
                          ("small-label", [PART + "fonts"]), ("small-label", [PART + "effects"])]),
    "PageSetup": ("Page Setup", [
        ("large", [".uno:PageLayoutMarginsMenu"]), ("large", [".uno:PageLayoutOrientationMenu"]),
        ("large", [".uno:PageLayoutSizeMenu"]), ("large", [".uno:PageLayoutPrintAreaMenu"]),
        ("large", [".uno:PageLayoutBreaksMenu"]), ("large", [".uno:PageLayoutBackground"]),
        ("large", [".uno:PageLayoutPrintTitles"])]),
    "ScaleToFit": ("Scale to Fit", [("small-label", [FIT + v]) for v in ("width", "height", "scale")]),
    "SheetOptions": ("Sheet Options", [
        ("large", [".uno:SheetRightToLeft"]), ("small-label", [".uno:ToggleSheetGrid"]),
        ("small-label", [OPTION + "gridlines"]), ("small-label", [".uno:ViewRowColumnHeaders"]),
        ("small-label", [OPTION + "headings"])]),
    "Arrange": ("Arrange", [
        ("large", [".uno:PageLayoutBringForwardMenu"]), ("large", [".uno:PageLayoutSendBackwardMenu"]),
        ("large", [".uno:Navigator"]), ("large", [".uno:PageLayoutAlignMenu"]),
        ("large", [".uno:PageLayoutGroupMenu"]), ("large", [".uno:PageLayoutRotateMenu"])]),
}
SEP = "-"  # a separator in a menu item list
SIZES = {"Letter": 8, "Legal": 9, "Tabloid": 10, "Executive": 23, "Statement": 38, "A3": 3, "A4": 4,
         "A5": 5, "B4 (JIS)": 34, "B5 (JIS)": 35, "Envelope #10": 28, "Envelope DL": 17}
MARGINS = {"Normal": (1778, 1778, 1905, 1905), "Wide": (2540, 2540, 2540, 2540),
           "Narrow": (635, 635, 1905, 1905)}
MENUS = {  # command: (label, popup resource, popup items in order)
    "PageLayoutMarginsMenu": ("Margins", "pagelayout_margins",
                              [MARGIN % v for v in MARGINS.values()] + [SEP, ".uno:PageFormatDialog"]),
    "PageLayoutOrientationMenu": ("Orientation", "pagelayout_orientation",
                                  [ORIENTATION + "false", ORIENTATION + "true"]),
    "PageLayoutSizeMenu": ("Size", "pagelayout_size",
                           [SIZE + str(n) for n in SIZES.values()] + [SEP, ".uno:PageFormatDialog"]),
    "PageLayoutPrintAreaMenu": ("Print Area", "pagelayout_printarea",
                                [".uno:DefinePrintArea", ".uno:DeletePrintArea", ".uno:AddPrintArea",
                                 ".uno:EditPrintArea"]),
    "PageLayoutBreaksMenu": ("Breaks", "pagelayout_breaks",
                             [".uno:InsertBreakMenu", ".uno:DelBreakMenu", ".uno:DeleteAllBreaks"]),
    "PageLayoutBringForwardMenu": ("Bring Forward", "pagelayout_bringforward",
                                   [".uno:ObjectForwardOne", ".uno:BringToFront"]),
    "PageLayoutSendBackwardMenu": ("Send Backward", "pagelayout_sendbackward",
                                   [".uno:ObjectBackOne", ".uno:SendToBack"]),
    "PageLayoutAlignMenu": ("Align", "pagelayout_align",
                            [".uno:ObjectAlignLeft", ".uno:AlignCenter", ".uno:ObjectAlignRight", SEP,
                             ".uno:AlignUp", ".uno:AlignMiddle", ".uno:AlignDown", SEP,
                             ".uno:GridUse", ".uno:GridVisible"]),
    "PageLayoutGroupMenu": ("Group", "pagelayout_group", [".uno:FormatGroup", ".uno:FormatUngroup"]),
    "PageLayoutRotateMenu": ("Rotate", "pagelayout_rotate",
                             [".uno:ToggleObjectRotateMode", ".uno:ObjectMirrorVertical",
                              ".uno:ObjectMirrorHorizontal", SEP, ".uno:TransformDialog"]),
}
SUBMENUS = {  # popup resource -> {submenu command: its items}
    "pagelayout_breaks": {".uno:InsertBreakMenu": [".uno:InsertRowBreak", ".uno:InsertColumnBreak"],
                          ".uno:DelBreakMenu": [".uno:DeleteRowbreak", ".uno:DeleteColumnbreak"]},
}
PLACEHOLDER_LABELS = {
    PART + "fonts": "Fonts", PART + "effects": "Effects", ".uno:PageLayoutBackground": "Background",
    FIT + "width": "Width", FIT + "height": "Height", FIT + "scale": "Scale",
    OPTION + "gridlines": "Print Gridlines", OPTION + "headings": "Print Headings"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS)  # implemented ones are no placeholder
PAGELAYOUT_SLOTS = range(399, 403)


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def sdi_row(path, slot):
    match = re.search(r"^\s*" + slot + r"\s*\[(.*)\]", read(path), re.M)
    return match.group(1).strip() if match else None


class CalcPageLayoutUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = OFFICE.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))  # the columns' toolboxes, then the footer

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("phbLayout", self.layout["page"])
        self.assertEqual("PageLayout", self.layout["id_prefix"])
        self.assertEqual("TabbedCalc", self.layout["context"])
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        for section in self.layout["sections"]:
            self.assertEqual(DESIGN[section["name"]][0], section["caption"])
            self.assertEqual(3, section["rows"], section["name"])

    def test_every_control_is_there_in_order_with_its_size(self):
        for section in self.layout["sections"]:
            got = [(b["style"], [g.item_url(i) for i in b["items"]]) for b in self.boxes(section)]
            self.assertEqual(DESIGN[section["name"]][1], got, section["name"])

    def test_the_themes_and_arrange_sections_have_the_design_column_shape(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual({"Themes": [1, 3], "PageSetup": [1] * 7, "ScaleToFit": [3],
                          "SheetOptions": [1, 2, 2], "Arrange": [1] * 6}, shapes)

    def test_the_menu_commands_are_dropdowns_the_rest_are_plain_buttons(self):
        for item in self.items():
            expected = "split" if item["cmd"] in MENUS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_url_variants_carry_a_short_id_the_url_as_action_and_a_plain_icon_name(self):
        variants = [i for i in self.items() if "action" in i]
        self.assertEqual(2 + 3 + 2, len(variants))
        for item in variants:
            self.assertRegex(item["cmd"], r"^[A-Za-z0-9]+$")
            base, value = re.match(r"\.uno:(\w+)\?\w+:\w+=(\w+)$", item["action"]).groups()
            self.assertEqual("cmd/sc_%s_%s.png" % (base.lower(), value), item["icon"], item["cmd"])
        self.assertEqual(len(variants), len({i["cmd"] for i in variants}))

    def test_the_old_layout_page_and_its_overflow_menu_are_gone(self):
        self.assertIn("Menu Page", self.layout["remove_objects"])
        for old in ('id="Menu Page"', 'Layout-LayoutButton:Menu Page', 'id="Layout-Menu"',
                    'id="MenuLayout-'):
            self.assertNotIn(old, self.office)
        for old in ("btnLayoutEditPrintArea", "btnLayoutSheetRightToLeft", "btnLayoutPageFormatDialog"):
            self.assertNotIn(old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:PageLayout-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:PageLayout-end -->"))

    def test_office_ui_is_upstream_plus_tabs_and_every_generated_page(self):
        self.assertIn("PageLayout", {layout["id_prefix"] for layout in office.page_layouts()})
        self.assertEqual(office.expected_office_ui(), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_orientation_is_never_a_ribbon_item_only_menu_items_with_arguments(self):
        # risk R8: Controller.xcu registers a module-less toolbox controller (the Writer library's
        # PageOrientationToolBoxControl) for .uno:Orientation, so it must not be a toolbox button
        for layout in office.page_layouts():
            for section in layout["sections"]:
                for box in g.boxes_of(section):
                    for item in box["items"]:
                        self.assertNotEqual(".uno:Orientation", g.item_command(item), layout["page"])
        self.assertNotRegex(self.office, r'action-name">\.uno:Orientation[<?]')
        controlled = {v["Command"]: v for v in controller_nodes().values()}
        self.assertEqual("", controlled[".uno:Orientation"].get("Module", ""))  # the reason for the trap
        # the two Orientation menu items are the only place the command appears, as URL variants
        popup = (POPUPMENU / "pagelayout_orientation.xml").read_text(encoding="utf-8")
        self.assertEqual([".uno:Orientation?isLandscape:bool=false", ".uno:Orientation?isLandscape:bool=true"],
                         re.findall(r'menu:id="([^"]+)"', popup))
        self.assertEqual(2, len(re.findall(r"\.uno:Orientation\b", " ".join(
            i for _l, _r, items in MENUS.values() for i in items))))

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu()
        for item in self.items():
            self.assertIn(g.item_url(item), labels, item["cmd"])

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

    def test_the_registry_labels_every_page_layout_slot_and_variant(self):
        by_url = placeholders.labels_by_url()
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items()
                                              if u.startswith(".uno:PageLayout")})
        for entry in placeholders.load():
            if entry["offset"] in PAGELAYOUT_SLOTS and "variants" in entry:
                self.assertEqual(entry["variants"], list(entry["variant_labels"]), entry["command"])

    def test_every_page_layout_placeholder_is_on_the_page_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes().values()}
        used = {g.item_url(i) for i in self.items()}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, used, url)
            self.assertNotIn(url, controlled, url)

    def test_menu_variants_have_labels(self):
        labels = commands_xcu()
        for label, number in SIZES.items():
            self.assertEqual(label, labels[SIZE + str(number)], label)
        for label, values in MARGINS.items():
            self.assertEqual(label, labels[MARGIN % values], label)
        self.assertEqual("Portrait", labels[ORIENTATION + "false"])
        self.assertEqual("Landscape", labels[ORIENTATION + "true"])

    def test_the_print_titles_alias_has_excels_label(self):
        self.assertEqual("Print Titles", commands_xcu()[".uno:PageLayoutPrintTitles"])
        self.assertIn(".uno:PageLayoutPrintTitles", flagged_commands())

    def test_dropdown_commands_have_labels_and_popup_and_toolbar_controllers(self):
        labels, nodes = commands_xcu(), controller_nodes()
        self.assertEqual(10, len(MENUS))
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

    def test_the_breaks_popup_uses_the_menu_bars_two_submenus(self):
        for resource, subs in SUBMENUS.items():
            root = ET.parse(POPUPMENU / (resource + ".xml")).getroot()
            for menu in root.iter(MENU + "menu"):
                self.assertEqual(subs[menu.get(MENU + "id")], self.menu_ids(menu.find(MENU + "menupopup")))

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


class PrintTitlesAliasTest(unittest.TestCase):
    """.uno:PageLayoutPrintTitles mirrors .uno:EditPrintArea (state, execute, invalidation)."""

    SLOT, ORIGINAL = "FID_PAGELAYOUT_PRINT_TITLES", "SID_OPENDLG_EDIT_PRINTAREA"

    def test_the_slot_is_sid_new_slots_plus_16_in_the_gap_next_to_the_data_split_bodies(self):
        text = read("sc/inc/sc.hrc")
        self.assertRegex(text, r"#define\s+" + self.SLOT + r"\s+\(SID_NEW_SLOTS\+16\)")
        self.assertEqual(1, len(re.findall(r"SID_NEW_SLOTS\s*\+\s*16\b", text)))

    def test_the_slot_has_a_scalc_sdi_entry_like_the_original_but_for_the_toolbox(self):
        sdi = read("sc/sdi/scalc.sdi")
        mine = re.search(r"SfxVoidItem PageLayoutPrintTitles " + self.SLOT + r"\n\(\)\n\[(.*?)\n\]", sdi, re.S)
        orig = re.search(r"SfxVoidItem EditPrintArea " + self.ORIGINAL + r"\n\(\)\n\[(.*?)\n\]", sdi, re.S)
        self.assertIsNotNone(mine)
        self.assertIn("ReadOnlyDoc = FALSE", mine.group(1))  # like the original
        self.assertIn("ReadOnlyDoc = FALSE", orig.group(1))
        self.assertIn("ToolBoxConfig = TRUE", mine.group(1))

    def test_the_slot_reuses_the_originals_execute_and_state_methods(self):
        original = sdi_row("sc/sdi/docsh.sdi", self.ORIGINAL)
        self.assertEqual("ExecMethod = Execute; StateMethod = GetState;", original)
        # docsh.sdi lists the original in TableSelection; the alias sits in the sibling interface
        # Tables of the same shell (ScTabViewShell), so it runs the same Execute and GetState
        self.assertEqual(original, sdi_row("sc/sdi/tabvwsh.sdi", self.SLOT))
        self.assertIn("import Tables", read("sc/sdi/tabvwsh.sdi"))
        self.assertIn("import TableSelection", read("sc/sdi/tabvwsh.sdi"))

    def case_labels(self, path):
        """Groups of consecutive case labels in a source file."""
        return [re.findall(r"case (\w+):", m.group(0))
                for m in re.finditer(r"(?:\s*case \w+:\s*\n)+", read(path))]

    def test_execute_shares_the_originals_case(self):
        groups = [g_ for g_ in self.case_labels("sc/source/ui/view/tabvwsh3.cxx") if self.ORIGINAL in g_]
        self.assertEqual(1, len(groups))
        self.assertIn(self.SLOT, groups[0])

    def test_state_shares_the_originals_shared_document_rule_and_disables_in_drawing_modes(self):
        groups = [g_ for g_ in self.case_labels("sc/source/ui/view/tabvwsha.cxx") if self.ORIGINAL in g_]
        self.assertEqual(1, len(groups))
        self.assertIn(self.SLOT, groups[0])
        # the original is also disabled by drawsh.sdi and drtxtob.sdi (StateDisableItems); the alias
        # lives in the view shell below them, so its state method does the same for the same modes
        state = read("sc/source/ui/view/tabvwsha.cxx")
        match = re.search(r"case " + self.SLOT + r":(.*?)break;", state, re.S)
        self.assertIsNotNone(match)
        # ScDrawShell and every shell derived from it (chart, OLE, graphic, media, draw form)
        for flag in ("bActiveDrawSh", "bActiveDrawTextSh", "bActiveDrawFormSh", "bActiveOleObjectSh",
                     "bActiveChartSh", "bActiveGraphicSh", "bActiveMediaSh"):
            self.assertIn(flag, match.group(1))
        self.assertIn("rSet.DisableItem", match.group(1))

    def test_every_invalidation_of_the_original_also_hits_the_alias(self):
        # Any mention of the original in a file that calls Invalidate (directly, through rBindings or
        # pBindings, or in a slot id array handed to it) must be matched by a mention of the alias
        for path in (ROOT / "sc/source").rglob("*.cxx"):
            text = path.read_text(encoding="utf-8", errors="replace")
            if self.ORIGINAL not in text or "Invalidate" not in text:
                continue
            if path.name in ("tabvwsh3.cxx", "tabvwsha.cxx", "reffact.cxx", "tabvwshc.cxx"):
                continue  # Execute, state and dialog creation, no invalidation (checked below)
            n_orig = len(re.findall(r"\b" + self.ORIGINAL + r"\b", text))
            n_new = len(re.findall(r"\b" + self.SLOT + r"\b", text))
            self.assertGreaterEqual(n_new, n_orig, f"{self.SLOT} not mirrored in {path}")
        for name in ("tabvwsh3.cxx", "tabvwsha.cxx", "reffact.cxx", "tabvwshc.cxx"):
            text = read("sc/source/ui/view/" + name)
            for m in re.finditer(r"Invalidate[^;]*?\b" + self.ORIGINAL + r"\b[^;]*;", text, re.S):
                self.assertRegex(m.group(0), self.SLOT, name)

    def test_orientation_items_have_the_radio_style_the_framework_rule_needs(self):
        root = ET.parse(POPUPMENU / "pagelayout_orientation.xml").getroot()
        items = [e for e in root if e.tag == MENU + "menuitem"]
        self.assertEqual(2, len(items))
        for item in items:
            self.assertEqual("radio", item.get(MENU + "style"), item.get(MENU + "id"))

    def test_the_alias_is_a_functional_slot_not_a_placeholder(self):
        self.assertNotIn(self.SLOT, [e["slot"] for e in placeholders.load_all()])
        self.assertNotIn("PageLayoutPrintTitles", [e["command"] for e in placeholders.load_all()])


if __name__ == "__main__":
    unittest.main()

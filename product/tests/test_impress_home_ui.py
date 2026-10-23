# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Impress Home tab (Undo, Clipboard, Slides, Font, Paragraph, Drawing, Editing): layout vs
product/docs/impress-ribbon-tabs.md section 1 "Home", the eleven new dropdowns (popup files, controllers,
labels), the placeholder menu items, the Reset variant, and the commands that leave the tab
(section 2, "Home (23)")."""
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
LAYOUT = ROOT / "product/ui/impress_home.json"
OFFICE_REL = "sd/uiconfig/simpress/ui/notebookbar_office.ui"
POPUPMENU = ROOT / "sd/uiconfig/simpress/popupmenu"
MENUBAR = ROOT / "sd/uiconfig/simpress/menubar/menubar.xml"
SHORTCUTS = ROOT / "sd/uiconfig/simpress/toolbar/notebookbarshortcuts.xml"
MENU = "{http://openoffice.org/2001/menu}"
PRESENTATION_MODULE = "com.sun.star.presentation.PresentationDocument"
SEP = "-"  # a separator in a menu item list
SECTION = ".uno:HomeSection?Action:string="
EFFECT = ".uno:HomeShapeEffect?Effect:string="
RESET = ".uno:AssignLayout?Reset:bool=true"


def uno(*names):
    return [".uno:" + name for name in names]


# section -> (caption, rows, [(style, [url, ...]) per toolbox in document order]); design section 1 "Home".
# Size: I = small (icon), L = large, S = small-label; the font and size boxes are combos in a small toolbox.
DESIGN = {
    "Undo": ("Undo", 2, [("small", uno("Undo")), ("small", uno("Redo"))]),
    "Clipboard": ("Clipboard", 3, [("large", uno("Paste")), ("small", uno("Cut")), ("small", uno("Copy")),
                                   ("small", uno("FormatPaintbrush"))]),
    "Slides": ("Slides", 3, [("large", uno("InsertPage")), ("large", uno("ImportSlideFromFile")),
                             ("small-label", uno("AssignLayout")), ("small-label", [RESET]),
                             ("small-label", uno("HomeSectionMenu"))]),
    "Font": ("Font", 2, [("small", uno("CharFontName", "FontHeight", "Grow", "Shrink", "SetDefault")),
                         ("small", uno("Bold", "Italic", "Underline", "Shadowed", "Strikeout", "Spacing",
                                       "HomeChangeCaseMenu", "CharBackColor", "Color"))]),
    "Paragraph": ("Paragraph", 3, [("small", uno("DefaultBullet", "DefaultNumbering", "OutlineLeft",
                                                 "OutlineRight", "LineSpacing")),
                                   ("small", uno("LeftPara", "CenterPara", "RightPara", "JustifyPara",
                                                 "HomeColumnsMenu")),
                                   ("small-label", uno("HomeTextDirectionMenu")),
                                   ("small-label", uno("HomeAlignTextMenu")),
                                   ("small-label", uno("HomeConvertToSmartArt"))]),
    # decision 15: 17 icon-only tool cells plus the More arrow, three rows of six
    "Drawing": ("Drawing", 3, [("small", uno("Text", "Line", "BasicShapes.rectangle", "BasicShapes.ellipse",
                                             "ArrowsToolbox", "ConnectorToolbox")),
                               ("small", uno("BasicShapes", "SymbolShapes", "ArrowShapes", "FlowChartShapes",
                                             "CalloutShapes", "StarShapes")),
                               ("small", uno("LineToolbox", "Polygon_Unfilled", "Bezier_Unfilled", "DrawCaption",
                                             "Objects3DToolbox", "InsertShapesMenu")),
                               ("large", uno("HomeArrangeMenu")), ("large", uno("SidebarDeck.StyleListDeck")),
                               ("small-label", uno("FillColor")), ("small-label", uno("XLineColor")),
                               ("small-label", uno("HomeShapeEffectsMenu"))]),
    "Editing": ("Editing", 3, [("small-label", uno("HomeFindMenu")), ("small-label", uno("HomeReplaceMenu")),
                               ("small-label", uno("HomeSelectMenu"))]),
}
SHAPES = {"Undo": [2], "Clipboard": [1, 3], "Slides": [1, 1, 3], "Font": [2], "Paragraph": [2, 3],
          "Drawing": [3, 1, 1, 3], "Editing": [3]}
# PowerPoint's label per item (T9w: the ribbon shows it, unless it equals LibreOffice's label; menus keep
# LibreOffice's). The layout item's "cmd" is the key; Reset is the widget command ResetLayout.
POWERPOINT_LABELS = {
    "Undo": "Undo", "Redo": "Redo", "Paste": "Paste", "Cut": "Cut", "Copy": "Copy",
    "FormatPaintbrush": "Format Painter", "InsertPage": "New Slide", "ImportSlideFromFile": "Reuse Slides",
    "AssignLayout": "Layout", "ResetLayout": "Reset", "HomeSectionMenu": "Section",
    "CharFontName": "Font", "FontHeight": "Font Size", "Grow": "Increase Font Size",
    "Shrink": "Decrease Font Size", "SetDefault": "Clear All Formatting", "Bold": "Bold", "Italic": "Italic",
    "Underline": "Underline", "Shadowed": "Text Shadow", "Strikeout": "Strikethrough",
    "Spacing": "Character Spacing", "HomeChangeCaseMenu": "Change Case", "CharBackColor": "Highlight",
    "Color": "Font Color", "DefaultBullet": "Bullets", "DefaultNumbering": "Numbering",
    "OutlineLeft": "Decrease List Level", "OutlineRight": "Increase List Level", "LineSpacing": "Line Spacing",
    "LeftPara": "Align Left", "CenterPara": "Center", "RightPara": "Align Right", "JustifyPara": "Justify",
    "HomeColumnsMenu": "Add or Remove Columns", "HomeTextDirectionMenu": "Text Direction",
    "HomeAlignTextMenu": "Align Text", "HomeConvertToSmartArt": "Convert to SmartArt",
    "Text": "Text Box", "Line": "Line", "BasicShapes.rectangle": "Rectangle", "BasicShapes.ellipse": "Oval",
    "ArrowsToolbox": "Lines and Arrows", "ConnectorToolbox": "Connectors", "BasicShapes": "Basic Shapes",
    "SymbolShapes": "Symbol Shapes", "ArrowShapes": "Block Arrows", "FlowChartShapes": "Flowchart",
    "CalloutShapes": "Callouts", "StarShapes": "Stars and Banners", "LineToolbox": "Curves and Polygons",
    "Polygon_Unfilled": "Freeform: Shape", "Bezier_Unfilled": "Curve", "DrawCaption": "Speech Bubble",
    "Objects3DToolbox": "3D Objects", "InsertShapesMenu": "More Shapes", "HomeArrangeMenu": "Arrange",
    "SidebarDeck.StyleListDeck": "Quick Styles", "FillColor": "Shape Fill", "XLineColor": "Shape Outline",
    "HomeShapeEffectsMenu": "Shape Effects", "HomeFindMenu": "Find", "HomeReplaceMenu": "Replace",
    "HomeSelectMenu": "Select"}
# PowerPoint's splits and dropdowns: "split" only means "has an arrow" (a dropdown has no body action of
# its own, but is built the same way); the placeholder Convert to SmartArt is a plain greyed button
# (design decision 20).
SPLITS = {"Undo", "Redo", "Paste", "InsertPage", "AssignLayout", "HomeSectionMenu", "Underline", "Spacing",
          "HomeChangeCaseMenu", "CharBackColor", "Color", "DefaultBullet", "DefaultNumbering", "LineSpacing",
          "HomeColumnsMenu", "HomeTextDirectionMenu", "HomeAlignTextMenu", "InsertShapesMenu",
          "HomeArrangeMenu", "FillColor", "XLineColor", "HomeShapeEffectsMenu", "HomeFindMenu",
          "HomeReplaceMenu", "HomeSelectMenu"}

# command -> (label, popup resource, popup items in order); design section 1 "Menu contents"
MENUS = {
    "HomeSectionMenu": ("Section", "home_section",
                        uno("AddSlideSection", "RenameSlideSection", "RemoveSlideSection",
                            "RemoveSlideSectionAndSlides") + [SEP] + uno("MoveSlideSectionUp",
                                                                          "MoveSlideSectionDown") + [SEP]
                        + [SECTION + v for v in ("removeall", "collapseall", "expandall")]),
    "HomeChangeCaseMenu": ("Change Case", "home_changecase",
                           uno("ChangeCaseToSentenceCase", "ChangeCaseToLower", "ChangeCaseToUpper",
                               "ChangeCaseToTitleCase", "ChangeCaseToToggleCase")),
    # decision 14's gate failed (TextColumnsNumber has no UNO slot mapping, see the UITest), so the menu keeps
    # only More Columns..., the Text dialog
    "HomeColumnsMenu": ("Columns", "home_columns", uno("TextAttributes")),
    "HomeTextDirectionMenu": ("Text Direction", "home_textdirection",
                              uno("TextdirectionLeftToRight", "TextdirectionTopToBottom") + [SEP]
                              + uno("ParaLeftToRight", "ParaRightToLeft")),
    "HomeAlignTextMenu": ("Align Text", "home_aligntext",
                          uno("CellVertTop", "CellVertCenter", "CellVertBottom") + [SEP]
                          + uno("TextAttributes")),
    "InsertShapesMenu": ("Shapes", "home_shapes",
                         uno("ShapesLineMenu") + [SEP] + uno("BasicShapes", "SymbolShapes", "ArrowShapes",
                                                             "FlowChartShapes", "CalloutShapes",
                                                             "StarShapes") + [SEP]
                         + uno("ArrowsToolbox", "ConnectorToolbox", "Objects3DToolbox")),
    "HomeArrangeMenu": ("Arrange", "home_arrange",
                        uno("BringToFront", "SendToBack", "Forward", "Backward") + [SEP]
                        + uno("FormatGroup", "FormatUngroup", "HomeRegroup") + [SEP]
                        + uno("ObjectAlignLeft", "AlignCenter", "ObjectAlignRight", "AlignUp", "AlignMiddle",
                              "AlignDown", "DistributeSelection") + [SEP]
                        + uno("ToggleObjectRotateMode", "MirrorVert", "MirrorHorz") + [SEP]
                        + uno("Navigator")),
    "HomeShapeEffectsMenu": ("Shape Effects", "home_shapeeffects",
                             [EFFECT + "preset"] + uno("FillShadow") + [EFFECT + "reflection"]
                             + uno("SidebarDeck.PropertyDeck") + [EFFECT + "bevel"] + uno("ExtrusionToggle")),
    "HomeFindMenu": ("Find", "home_find", ["vnd.sun.star.findbar:FocusToFindbar"] + uno("SearchDialog")),
    "HomeReplaceMenu": ("Replace", "home_replace", uno("SearchDialog", "HomeReplaceFonts")),
    "HomeSelectMenu": ("Select", "home_select", uno("SelectAll", "SelectObject", "Navigator")),
}
PLACEHOLDER_LABELS = {  # URL -> label (design section 5, the Home rows)
    SECTION + "removeall": "Remove All Sections", SECTION + "collapseall": "Collapse All",
    SECTION + "expandall": "Expand All", ".uno:HomeConvertToSmartArt": "Convert to SmartArt",
    ".uno:HomeRegroup": "Regroup", EFFECT + "preset": "Preset", EFFECT + "reflection": "Reflection",
    EFFECT + "bevel": "Bevel", ".uno:HomeReplaceFonts": "Replace Fonts..."}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS, placeholders.registry("impress"))
VARIANT_LABELS = {RESET: "Reset Slide Layout"}  # design decision 13: LibreOffice's own wording (strings.hrc)
HOME_SLOTS = [0, 1, 2, 3, 4]

# design section 2 "Home (23)": command -> (class, menu-bar id that keeps it reachable).
# a: the same command is in the menu bar; b: only an equivalent entry is.
LEFT_THE_TAB = {
    "PresentationLayout": ("a", "PresentationLayout"), "SubScript": ("a", "SubScript"),
    "SuperScript": ("a", "SuperScript"), "StartPara": ("a", "StartPara"), "EndPara": ("a", "EndPara"),
    "IncrementIndent": ("a", "IncrementIndent"), "DecrementIndent": ("a", "DecrementIndent"),
    "HangingIndent": ("b", "ParagraphDialog"),
    "ParaspaceIncrease": ("a", "ParaspaceIncrease"), "ParaspaceDecrease": ("a", "ParaspaceDecrease"),
    "OutlineFont": ("a", "OutlineFont"), "Overline": ("a", "Overline"),
    "ChangeCaseRotateCase": ("a", "ChangeCaseRotateCase"),
    "InsertNonBreakingSpace": ("a", "InsertNonBreakingSpace"), "InsertHardHyphen": ("a", "InsertHardHyphen"),
    "InsertSoftHyphen": ("a", "InsertSoftHyphen"), "InsertZWSP": ("a", "InsertZWSP"),
    "InsertWJ": ("a", "InsertWJ"), "InsertLRM": ("a", "InsertLRM"), "InsertRLM": ("a", "InsertRLM"),
    "FontDialog": ("a", "FontDialog"), "ParagraphDialog": ("a", "ParagraphDialog"),
    "RestoreEditingView": ("a", "RestoreEditingView"),
}
OLD_PAGE_WIDGETS = ["btnHomeInsertSlide", "btnHomeDuplicatePage", "btnHomePresentationLayout",
                    "btnHomeStartPara", "btnHomeHangingIndent"]  # stock ids that must be gone


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ImpressHomeUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = IMPRESS.office.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("Home Tab", self.layout["page"])
        self.assertEqual("Home", self.layout["id_prefix"])
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
        self.assertEqual(64, len(self.items()))

    def test_every_section_is_the_designed_toolbox_columns(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_dropdowns_and_split_buttons_are_split_the_rest_are_plain(self):
        for item in self.items():
            expected = "split" if item["cmd"] in SPLITS else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])

    def test_every_item_keeps_powerpoints_label_in_office_label(self):
        # T9w: gen_ribbon turns office_label into the button's label; menus, help and tooltips keep LibreOffice's
        self.assertEqual(POWERPOINT_LABELS, {i["cmd"]: i.get("office_label") for i in self.items()})

    def test_reset_has_its_own_widget_command_and_an_icon(self):
        # design decisions 13 and 16: Layout and Reset share .uno:AssignLayout; the ? variant needs an icon
        by_cmd = {i["cmd"]: i for i in self.items()}
        self.assertEqual(RESET, by_cmd["ResetLayout"]["action"])
        self.assertTrue(by_cmd["ResetLayout"].get("icon"))
        self.assertNotIn("action", by_cmd["AssignLayout"])
        self.assertNotIn("kind", by_cmd["ResetLayout"])

    def test_the_old_home_page_and_its_overflow_menu_are_gone(self):
        self.assertIn("Menu Home", self.layout["remove_objects"])
        for old in ('id="Menu Home"', "Home-HomeButton:Menu Home", 'id="Home-Menu"', 'id="MenuHome-'):
            self.assertNotIn(old, self.office)
        for old in OLD_PAGE_WIDGETS:
            self.assertNotIn('id="%s"' % old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Home-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Home-end -->"))
        self.assertIn('id="Home Tab"', self.office)  # the page itself stays, with the tab label

    def test_office_ui_is_stock_plus_tabs_and_every_generated_page(self):
        self.assertIn("Home", {layout["id_prefix"] for layout in office.page_layouts("impress")})
        self.assertEqual(office.expected_office_ui("impress"), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_the_commands_that_left_the_tab_stay_reachable(self):
        self.assertEqual(23, len(LEFT_THE_TAB))
        self.assertEqual(22, sum(1 for kind, _ in LEFT_THE_TAB.values() if kind == "a"))
        menubar = MENUBAR.read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()}
        in_menus = {u for _l, _r, items in MENUS.values() for u in items}
        for name, (kind, menu_id) in LEFT_THE_TAB.items():
            self.assertNotIn(".uno:" + name, on_tab, name)
            self.assertNotIn(".uno:" + name, in_menus, name)
            self.assertIn('menu:id=".uno:%s"' % menu_id, menubar, name)
            if kind == "a":
                self.assertEqual(name, menu_id)
            else:
                self.assertNotEqual(name, menu_id)
                self.assertNotIn('menu:id=".uno:%s"' % name, menubar, name + " is not in the menu bar: class b")

    def test_the_stock_home_page_commands_either_stay_or_are_in_the_leave_list(self):
        # every command of the stock Home page and its overflow menu stays on the ribbon (page or dropdown
        # item), is in the leave list, or belongs to a later task (Start from First Slide: I6a). The stock aliases New Slide and Duplicate Slide act through New Slide's popup.
        stock = ET.parse(ROOT / "sd/uiconfig/simpress/ui/notebookbar.ui").getroot()
        commands = set()
        for wid in ("Home Tab", "Menu Home"):
            node = next(o for o in stock.iter("object") if o.get("id") == wid)
            commands |= {p.text for p in node.iter("property") if p.get("name") == "action-name"}
        on_tab = {g.item_command(i) for i in self.items()} | {u for _l, _r, items in MENUS.values() for u in items}
        left = {".uno:" + name for name in LEFT_THE_TAB}
        later = {".uno:Presentation"}
        aliases = {".uno:InsertSlide": ".uno:InsertPage", ".uno:DuplicateSlide": ".uno:InsertPage"}
        self.assertGreater(len(commands), 50)
        for url in sorted(commands):
            url = aliases.get(url, url)
            self.assertTrue(url in on_tab or url in left or url in later, url)

    def test_undo_stays_on_home_and_in_the_quick_access_bar(self):
        shortcuts = SHORTCUTS.read_text(encoding="utf-8")
        on_tab = {g.item_command(i) for i in self.items()}
        for name in ("Undo", "Redo"):
            self.assertIn('xlink:href=".uno:%s"' % name, shortcuts)
            self.assertIn(".uno:" + name, on_tab)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu(app="impress")
        for item in self.items():
            url = g.item_url(item)
            self.assertTrue(url in labels or url.split("?")[0] in labels, item["cmd"])

    def test_the_new_menus_and_placeholder_items_have_the_designed_labels_and_tooltips(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_reset_variant_has_its_own_label_node(self):
        labels, tips = commands_xcu(app="impress"), tooltips(app="impress")
        for url, label in VARIANT_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertNotIn(url, tips, url + " is a real command: no 'not available yet' tooltip")
        # Draw shares the file: the base commands keep their labels
        self.assertEqual("Slide Layout", labels[".uno:AssignLayout"])

    def test_the_new_commands_have_the_image_flag(self):
        flagged = flagged_commands(app="impress")
        for cmd in MENUS:
            self.assertIn(".uno:" + cmd, flagged, cmd)
        for url in list(PLACEHOLDER_LABELS) + list(VARIANT_LABELS):
            self.assertIn(url, flagged, url)

    def test_the_menu_items_are_known_commands(self):
        labels = commands_xcu(app="impress")
        for _label, _resource, items in MENUS.values():
            for url in items:
                if url != SEP and not url.startswith("vnd.sun.star.findbar:"):  # framework URL, in GenericCommands
                    self.assertIn(url, labels, url)

    def test_the_registry_labels_every_home_slot_and_variant(self):
        registry = placeholders.registry("impress")
        by_url = placeholders.labels_by_url(registry)
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items() if u.startswith(".uno:Home")})
        entries = {e["offset"]: e for e in placeholders.load_all(registry)}
        self.assertEqual(["Action:string=" + v for v in ("removeall", "collapseall", "expandall")],
                         entries[0]["variants"])
        self.assertEqual("Convert to SmartArt", entries[1]["label"])
        self.assertEqual("HomeRegroup", entries[2]["command"])
        self.assertEqual(["Effect:string=" + v for v in ("preset", "reflection", "bevel")], entries[3]["variants"])
        self.assertEqual("HomeReplaceFonts", entries[4]["command"])
        for offset in HOME_SLOTS:
            self.assertTrue(entries[offset]["command"].startswith("Home"))

    def test_the_placeholder_items_have_no_controller(self):
        controlled = {v["Command"] for v in controller_nodes(app="impress").values()}
        for url in PLACEHOLDER_LABELS:
            self.assertNotIn(url, controlled, url)

    def impress_nodes(self, command):
        return [v for v in controller_nodes(app="impress").values()
                if v["Command"] == command and v["Module"] == PRESENTATION_MODULE]

    def test_each_dropdown_has_a_popup_and_a_toolbar_controller_of_its_own(self):
        self.assertEqual(11, len(MENUS))
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

    def test_new_slide_and_layout_keep_their_slide_controllers_and_reset_has_none(self):
        # design decisions 13 and 19: InsertPage and AssignLayout have a controller registered for Impress
        # (Controller.xcu), the ? variant of Reset is another URL and gets none
        nodes = controller_nodes(app="impress").values()
        controllers = {v["Command"]: v["Controller"] for v in nodes if v["Module"] == PRESENTATION_MODULE}
        self.assertEqual("com.sun.star.comp.sd.InsertSlideController", controllers[".uno:InsertPage"])
        self.assertEqual("com.sun.star.comp.sd.SlideLayoutController", controllers[".uno:AssignLayout"])
        self.assertNotIn(RESET, {v["Command"] for v in nodes})

    def test_the_layout_popups_add_duplicate_slide_and_reset_slide_layout(self):
        # design decision 19: New Slide's popup (InsertSlideController, mbInsertPage) adds the Duplicate
        # Slide button to the layout gallery, Layout's (SlideLayoutController) the Reset Slide Layout one,
        # and that button dispatches the controller's own command URL without a layout: the same dispatch
        # as the Reset button of the Slides section (decision 13)
        src = read("sd/source/ui/controller/slidelayoutcontroller.cxx")
        self.assertRegex(src, r'if\( bInsertPage \)\s+sSlotStr = "\.uno:DuplicatePage";')
        self.assertIn("sSlotTitle = SdResId( STR_RESET_LAYOUT );", src)
        self.assertIn('"Reset Slide Layout"', read("sd/inc/strings.hrc"))
        self.assertRegex(src, r"aArgs = \{ comphelper::makePropertyValue\(u\"WhatLayout\"_ustr")
        self.assertIn("mxControl->dispatchCommand( sCommandURL, aArgs );", src)

    def test_no_controller_was_put_on_a_command_other_toolbars_use(self):
        # the five dropdown commands are new: only the Home page and the controller nodes name them
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

    def test_the_shapes_menu_has_the_line_submenu_with_the_eight_line_tools(self):
        # design section 1: ShapesLineMenu > Line, Freeline_Unfilled, Freeline, Bezier_Unfilled, BezierFill,
        # Polygon_Unfilled, Polygon_Diagonal_Unfilled, Polygon_Diagonal (the Insert > Shape > Line submenu)
        root = ET.parse(POPUPMENU / "home_shapes.xml").getroot()
        submenu = root.find(MENU + "menu")
        self.assertEqual(".uno:ShapesLineMenu", submenu.get(MENU + "id"))
        self.assertEqual(uno("Line", "Freeline_Unfilled", "Freeline", "Bezier_Unfilled", "BezierFill",
                             "Polygon_Unfilled", "Polygon_Diagonal_Unfilled", "Polygon_Diagonal"),
                         self.menu_ids(submenu.find(MENU + "menupopup")))

    def test_the_find_menu_starts_with_the_find_toolbar_and_replace_with_find_and_replace(self):
        # design decisions 10 and 12
        find = self.menu_ids(ET.parse(POPUPMENU / "home_find.xml").getroot())
        self.assertEqual("vnd.sun.star.findbar:FocusToFindbar", find[0])
        self.assertEqual(".uno:SearchDialog", self.menu_ids(ET.parse(POPUPMENU / "home_replace.xml").getroot())[0])

    def test_the_drawing_cells_keep_the_stock_controllers_of_their_commands(self):
        # design decision 15: the shape sub-toolbars keep their stock popups (ToolbarAsMenuController or
        # SubToolBarController, Controller.xcu), Shape Fill and Outline their color popups; none of them is new
        controlled = {}
        for v in controller_nodes(app="impress").values():
            if v["Module"] in ("", PRESENTATION_MODULE, None):
                controlled.setdefault(v["Command"], set()).add(v["Controller"].rsplit(".", 1)[1])
        for name in ("ArrowsToolbox", "ConnectorToolbox", "BasicShapes", "SymbolShapes", "ArrowShapes",
                     "FlowChartShapes", "CalloutShapes", "StarShapes", "LineToolbox", "Objects3DToolbox",
                     "FillColor", "XLineColor"):
            self.assertTrue(controlled.get(".uno:" + name), name)
        for cmd in ("HomeArrangeMenu", "HomeShapeEffectsMenu", "HomeFindMenu", "HomeReplaceMenu",
                    "HomeSelectMenu", "InsertShapesMenu"):
            self.assertEqual({"ResourceMenuController", "GenericPopupToolbarController"}, controlled[".uno:" + cmd])

    def test_the_section_menu_ends_with_the_three_placeholder_items(self):
        items = self.menu_ids(ET.parse(POPUPMENU / "home_section.xml").getroot())
        self.assertEqual([SECTION + v for v in ("removeall", "collapseall", "expandall")], items[-3:])

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

# -*- tab-width: 4; indent-tabs-mode: nil; py-indent-offset: 4 -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import json
import os
import time
import uno
import unohelper
from contextlib import contextmanager
from pathlib import Path

from uitest.framework import UITestCase
from uitest.uihelper.calc import enter_text_to_cell
from uitest.uihelper.common import get_state_as_dict
from libreoffice.uno.propertyvalue import mkPropertyValues
from com.sun.star.frame import XStatusListener

OFFICE_UI = "notebookbar_office.ui"

# Tab position -> page. Excel's order: File, Home, Insert, Page Layout, Formulas, Data, Review,
# View; the contextual tabs (Image .. Form, positions 8-13) only show with their object, and
# Extension and Tools (Excel's Developer) stay where upstream has them. Help is last.
TAB_PAGES = {0: "phbFile", 1: "phbHome", 2: "phbInsert", 3: "phbLayout", 4: "phbFunctions",
             5: "phbData", 6: "phbReview", 7: "phbView", 14: "phbExtension", 15: "phbTools",
             16: "phbHelp"}
TAB_COUNT = 17


def placeholder_urls(src, only=None):
    """Every command URL of the shared placeholder registry (product/tests/placeholders.json)."""
    entries = json.loads((src / "product" / "tests" / "placeholders.json").read_text(encoding="utf-8"))
    urls = []
    for entry in entries:
        if only is None or only(entry):
            urls += [entry["command"] + "?" + v for v in entry.get("variants", [])] or [entry["command"]]
    return urls


class StateListener(unohelper.Base, XStatusListener):
    def __init__(self):
        self.enabled = None
        self.history = []  # every IsEnabled the frame pushed, in order

    def statusChanged(self, aEvent):
        self.enabled = aEvent.IsEnabled
        self.history.append(aEvent.IsEnabled)

    def disposing(self, aEvent):
        pass


class NotebookbarOffice(UITestCase):

    def switch_to(self, ui_file):
        self.xUITest.executeCommand(".uno:ToolbarMode?Mode:string=" + ui_file)

    def test_office_variant_loads(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                xHome = xCalcDoc.getChild("phbHome")
                self.assertEqual("true", get_state_as_dict(xHome)["Visible"])
            finally:
                self.switch_to("Default")

    def test_switch_back_to_compact(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            self.switch_to("notebookbar_compact.ui")
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                # NewDocSection exists only in notebookbar_compact.ui
                xCalcDoc.getChild("NewDocSection")
            finally:
                self.switch_to("Default")

    def test_home_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_home.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                for section in layout["sections"]:
                    xLabel = xCalcDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xCalcDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_data_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_data.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(8, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xCalcDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xCalcDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def dispatch_enabled(self, name, timeout=5):
        """IsEnabled of .uno:<name> as the frame reports it to a status listener."""
        xDesktop = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.xContext)
        xFrame = xDesktop.getCurrentFrame()
        xTransformer = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.util.URLTransformer", self.xContext)
        aURL = uno.createUnoStruct("com.sun.star.util.URL")
        aURL.Complete = ".uno:" + name
        aURL = xTransformer.parseStrict(aURL)[1]
        xDispatch = xFrame.queryDispatch(aURL, "", 0)
        self.assertIsNotNone(xDispatch, name)
        listener = StateListener()
        xDispatch.addStatusListener(listener, aURL)
        try:
            deadline = time.time() + timeout
            while listener.enabled is None and time.time() < deadline:
                time.sleep(0.05)
        finally:
            xDispatch.removeStatusListener(listener, aURL)
        self.assertIsNotNone(listener.enabled, "no state reported for " + name)
        return listener.enabled

    @contextmanager
    def watched_state(self, name):
        """Keep ONE status listener on .uno:<name>; it must be told about later changes.

        Unlike dispatch_enabled(), which registers a new listener (and so re-runs GetState)
        for every query, this only sees states that SFX pushes after an Invalidate().
        """
        xDesktop = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.xContext)
        xTransformer = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.util.URLTransformer", self.xContext)
        aURL = uno.createUnoStruct("com.sun.star.util.URL")
        aURL.Complete = ".uno:" + name
        aURL = xTransformer.parseStrict(aURL)[1]
        xDispatch = xDesktop.getCurrentFrame().queryDispatch(aURL, "", 0)
        self.assertIsNotNone(xDispatch, name)
        listener = StateListener()
        xDispatch.addStatusListener(listener, aURL)
        try:
            self.wait_for(lambda: listener.enabled is not None, "no initial state for " + name)
            yield listener
        finally:
            xDispatch.removeStatusListener(listener, aURL)

    def wait_for(self, condition, message, timeout=5):
        deadline = time.time() + timeout
        while not condition() and time.time() < deadline:
            time.sleep(0.05)
        self.assertTrue(condition(), message)

    def check_placeholders_are_disabled_and_inert(self, names):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            enter_text_to_cell(xGrid, "A1", "keep")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.assertTrue(self.dispatch_enabled("DataSort"))  # control: a real, enabled slot
            for name in names:
                self.assertFalse(self.dispatch_enabled(name), name)
                self.xUITest.executeCommand(".uno:" + name)  # must do nothing, not even a dialog
            xSheet = document.Sheets.getByIndex(0)
            self.assertEqual("keep", xSheet.getCellRangeByName("A1").String)

    def test_data_placeholders_have_a_slot_that_is_always_disabled(self):
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["command"].startswith("Data"))
        self.assertEqual(9, len(names))
        self.check_placeholders_are_disabled_and_inert(names)

    def test_every_placeholder_of_the_slice_is_disabled_and_inert(self):
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src)
        self.assertEqual(61, len(names))  # 42 slots, 19 extra family variants
        self.check_placeholders_are_disabled_and_inert(names)

    def placeholder_buttons(self, src):
        """(label, toolbox item) of every placeholder button on the generated ribbon pages.

        Reads the toolbox items themselves, not a status listener: what the ribbon draws.
        """
        labels = {}
        for entry in json.loads((src / "product" / "tests" / "placeholders.json").read_text(encoding="utf-8")):
            base = ".uno:" + entry["command"]
            if "label" in entry:
                labels[base] = entry["label"]
            for variant, label in entry.get("variant_labels", {}).items():
                labels[base + "?" + variant] = label
        xCalcDoc = self.xUITest.getTopFocusWindow()
        buttons = []
        for path in sorted((src / "product" / "ui").glob("calc_*.json")):
            layout = json.loads(path.read_text(encoding="utf-8"))
            for section in layout.get("sections", []):
                for column in section["columns"]:
                    for box in column:
                        xBox = xCalcDoc.getChild("bx" + layout["id_prefix"] + box["id"])
                        for pos, item in enumerate(box["items"]):
                            url = item.get("action") or ".uno:" + item["cmd"]
                            if url in labels:
                                # a box's items are inserted in order, item ids count from 1
                                xItem = xBox.getChild("toolboxitem-%d" % (pos + 1))
                                self.assertEqual(labels[url], get_state_as_dict(xItem)["Text"].replace("~", ""))
                                buttons.append((labels[url], xItem))
        # Data 9, Insert 17 (9 chart-type variants), Page Layout 8 (7 variants of 3 families)
        self.assertEqual(34, len(buttons))
        return buttons

    def check_placeholder_buttons_are_drawn_disabled(self, src):
        buttons = self.placeholder_buttons(src)
        # the bindings may push the slot state later than the controller is created: wait for it
        enabled = lambda: [label for label, xItem in buttons if get_state_as_dict(xItem)["Enabled"] != "false"]
        deadline = time.time() + 5
        while enabled() and time.time() < deadline:
            time.sleep(0.05)
        self.assertEqual([], enabled(), "placeholder buttons drawn enabled")

    def test_every_placeholder_button_is_drawn_disabled(self):
        # Every variant of a family slot (Fonts/Effects, the nine chart types, ...) is its own
        # button on the same always-disabled slot; each one must be drawn disabled, not only the first.
        src = Path(os.environ["TDOC"]).parents[3]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                self.check_placeholder_buttons_are_drawn_disabled(src)
            finally:
                self.switch_to("Default")

    def test_placeholder_buttons_stay_disabled_when_the_ribbon_is_built_again(self):
        # A second build of the ribbon in the same window binds to slot states the window already
        # knows; nothing pushes them again, so the controllers' first state must be kept.
        src = Path(os.environ["TDOC"]).parents[3]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                self.check_placeholder_buttons_are_drawn_disabled(src)
                self.switch_to("notebookbar_compact.ui")
                self.switch_to(OFFICE_UI)
                self.check_placeholder_buttons_are_drawn_disabled(src)
            finally:
                self.switch_to("Default")

    def test_insert_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_insert.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(10, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xCalcDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xCalcDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_insert_placeholders_are_disabled_and_inert(self):
        # 10 slots: 9 plain ones (one is a Pictures menu item) and the chart-type family of 9 variants
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: 389 <= e["offset"] <= 398)
        self.assertEqual(18, len(names))
        self.check_placeholders_are_disabled_and_inert(names)

    def test_insert_existing_commands_are_enabled(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            # the two dropdown commands have no slot: their popups are checked below
            for name in ("InsertGraphic", "Gallery", "InsertCalcTable", "InsertObjectChart",
                         "DataDataPilotRun", "HyperlinkDialog", "InsertAnnotation",
                         "DrawText", "EditHeaderAndFooter", "FontworkGalleryFloater",
                         "InsertSignatureLine", "InsertObject", "InsertObjectStarMath",
                         "CharmapControl"):
                self.assertTrue(self.dispatch_enabled(name), name)

    def popup_of(self, command, resource):
        """The awt popup menu the ribbon dropdown `command` shows, built by its menu controller."""
        xDesktop = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.xContext)
        xFrame = xDesktop.getCurrentFrame()
        xFactory = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.PopupMenuControllerFactory", self.xContext)
        self.assertTrue(xFactory.hasController(command, "com.sun.star.sheet.SpreadsheetDocument"), command)
        xController = xFactory.createInstanceWithArgumentsAndContext(
            command, mkPropertyValues({"Frame": xFrame, "CommandURL": command,
                                       "Value": resource,
                                       "ModuleIdentifier": "com.sun.star.sheet.SpreadsheetDocument"}),
            self.xContext)
        self.assertIsNotNone(xController, command)
        xPopup = self.xContext.ServiceManager.createInstanceWithContext("com.sun.star.awt.PopupMenu", self.xContext)
        xController.setPopupMenu(xPopup)
        xController.updatePopupMenu()
        return xPopup

    def popup_commands(self, xPopup):
        commands = []
        for pos in range(xPopup.getItemCount()):
            nId = xPopup.getItemId(pos)
            command = xPopup.getCommand(nId)
            if command:  # separators have none
                commands.append(command)
        return commands

    def test_insert_shapes_dropdown_builds_its_submenus(self):
        # risk R6: a product popup with submenus (Line) and single items that open toolbar submenus
        with self.ui_test.create_doc_in_start_center("calc"):
            xPopup = self.popup_of(".uno:InsertShapesMenu", "insert_shapes")
            self.assertEqual([".uno:ShapesLineMenu", ".uno:BasicShapes", ".uno:ArrowShapes",
                              ".uno:FlowChartShapes", ".uno:StarShapes", ".uno:CalloutShapes",
                              ".uno:SymbolShapes", ".uno:ConnectorToolbox"], self.popup_commands(xPopup))
            xLine = xPopup.getPopupMenu(xPopup.getItemId(0))
            self.assertIsNotNone(xLine)
            self.assertEqual(8, xLine.getItemCount())
            self.assertEqual(".uno:Line", xLine.getCommand(xLine.getItemId(0)))

    def test_insert_pictures_dropdown_lists_place_in_cell_and_image(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            xPopup = self.popup_of(".uno:InsertPicturesMenu", "insert_pictures")
            self.assertEqual([".uno:InsertPictureInCell", ".uno:InsertGraphic"], self.popup_commands(xPopup))

    def test_insert_sparkline_variants_stay_enabled_and_open_the_dialog(self):
        # risk R3: the slot declares no Type argument; sfx2 must ignore it, not disable the button
        with self.ui_test.create_doc_in_start_center("calc"):
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            for cell, text in (("A1", "1"), ("B1", "2"), ("C1", "3"), ("D1", "")):
                enter_text_to_cell(xGrid, cell, text)
            xGrid.executeAction("SELECT", mkPropertyValues({"RANGE": "D1"}))
            for value in ("line", "column", "stacked"):
                name = "InsertSparkline?Type:string=" + value
                self.assertTrue(self.dispatch_enabled(name), name)
                with self.ui_test.execute_dialog_through_command(".uno:" + name, close_button="cancel") as xDialog:
                    self.assertIsNotNone(xDialog.getChild("cancel"))  # the Sparkline dialog, as without argument

    def test_family_variant_url_is_disabled_and_does_nothing(self):
        # A URL variant of a family slot reaches the same always-disabled slot: the status
        # listener hears "disabled" and a dispatch changes nothing (risk R3).
        self.check_placeholders_are_disabled_and_inert(["InsertChartType?Type:string=map"])

    def page_style(self, document):
        xSheet = document.Sheets.getByIndex(0)
        return document.StyleFamilies.getByName("PageStyles").getByName(xSheet.PageStyle)

    def test_pagelayout_margin_presets_work_through_url_arguments(self):
        # risk R4 spike: complex items (SvxLRSpaceItem, SvxULSpaceItem) as "Page.<Member>" URL arguments
        presets = {
            "Normal": (1778, 1778, 1905, 1905), "Wide": (2540, 2540, 2540, 2540),
            "Narrow": (635, 635, 1905, 1905)}
        with self.ui_test.create_doc_in_start_center("calc") as document:
            for name, (left, right, upper, lower) in presets.items():
                self.xUITest.executeCommand(
                    ".uno:CalcPageMargin?Page.LeftMargin:long=%d&Page.RightMargin:long=%d"
                    "&Page.TopMargin:long=%d&Page.BottomMargin:long=%d" % (left, right, upper, lower))
                xStyle = self.page_style(document)
                got = (xStyle.LeftMargin, xStyle.RightMargin, xStyle.TopMargin, xStyle.BottomMargin)
                self.assertEqual((left, right, upper, lower), got, name)

    def test_pagelayout_orientation_and_size_variants_change_the_page_style(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            self.xUITest.executeCommand(".uno:Orientation?isLandscape:bool=true")
            xStyle = self.page_style(document)
            self.assertTrue(xStyle.IsLandscape)
            self.assertGreater(xStyle.Width, xStyle.Height)
            self.xUITest.executeCommand(".uno:Orientation?isLandscape:bool=false")
            self.assertFalse(xStyle.IsLandscape)
            self.assertLess(xStyle.Width, xStyle.Height)
            self.xUITest.executeCommand(".uno:CalcPageSize?PaperFormat:short=8")  # Letter
            self.assertEqual((21590, 27940), (xStyle.Width, xStyle.Height))

    def test_pagelayout_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_pagelayout.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(5, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xCalcDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xCalcDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_pagelayout_placeholders_are_disabled_and_inert(self):
        # 4 slots: Fonts/Effects, Background, Width/Height/Scale, Print Gridlines/Print Headings
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: 399 <= e["offset"] <= 402)
        self.assertEqual(8, len(names))
        self.check_placeholders_are_disabled_and_inert(names)

    def test_pagelayout_print_titles_alias_follows_its_original_and_opens_the_same_dialog(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.assertTrue(self.dispatch_enabled("EditPrintArea"))
            self.assertTrue(self.dispatch_enabled("PageLayoutPrintTitles"))
            with self.ui_test.execute_modeless_dialog_through_command(
                    ".uno:PageLayoutPrintTitles", close_button="cancel") as xDialog:
                # the Edit Print Ranges dialog: print range, rows and columns to repeat
                self.assertIsNotNone(xDialog.getChild("edprintarea"))
                self.assertIsNotNone(xDialog.getChild("edrepeatrow"))
                self.assertIsNotNone(xDialog.getChild("edrepeatcol"))
            # with a drawing object selected the original is disabled, and so is the alias
            xShape = self.select_new_shape(document, 1000)
            self.assertIsNotNone(xShape)
            self.assertFalse(self.dispatch_enabled("EditPrintArea"))
            self.assertFalse(self.dispatch_enabled("PageLayoutPrintTitles"))
            self.select_rows(document, "A1")  # selecting a cell range leaves drawing mode
            self.assertEqual(self.dispatch_enabled("EditPrintArea"), self.dispatch_enabled("PageLayoutPrintTitles"))
            self.assertTrue(self.dispatch_enabled("PageLayoutPrintTitles"))

    def test_pagelayout_print_titles_alias_is_disabled_for_image_and_ole_selections_like_its_original(self):
        # Every ScDrawShell subshell (graphic, OLE, chart, media, draw form) disables the original. The
        # grid's SELECT OBJECT action marks the object like a mouse click (only the view's mark list
        # changes), unlike the API's select(), which also switches the drawing shell on.
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xPage = document.DrawPages.getByIndex(0)
            for n, (service, clsid) in enumerate((
                    ("com.sun.star.drawing.GraphicObjectShape", None),
                    ("com.sun.star.drawing.OLE2Shape", "12DCAE26-281F-416F-a234-c3086127382e"))):
                xShape = document.createInstance(service)
                if clsid:
                    xShape.CLSID = clsid
                xShape.Name = "T3aObject%d" % n
                xPage.add(xShape)
                xShape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", 1000 + 4000 * n, 1000))
                xShape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", 3000, 2000))
                self.select_rows(document, "A1")
                self.assertTrue(self.dispatch_enabled("PageLayoutPrintTitles"), service)
                xGrid.executeAction("SELECT", mkPropertyValues({"OBJECT": xShape.Name}))
                self.assertFalse(self.dispatch_enabled("EditPrintArea"), service)
                self.assertEqual(self.dispatch_enabled("EditPrintArea"),
                                 self.dispatch_enabled("PageLayoutPrintTitles"), service)

    def select_new_shape(self, document, x, count=1, service="com.sun.star.drawing.RectangleShape", clsid=None):
        """Add `count` shapes to the first sheet, select them all, return the last one."""
        xPage = document.DrawPages.getByIndex(0)
        xShapes = self.xContext.ServiceManager.createInstance("com.sun.star.drawing.ShapeCollection")
        xShape = None
        for n in range(count):
            xShape = document.createInstance(service)
            if clsid:
                xShape.CLSID = clsid
            xPage.add(xShape)
            xShape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", x + 4000 * n, 1000))
            xShape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", 3000, 2000))
            xShapes.add(xShape)
        document.CurrentController.select(xShapes)
        return xShape

    def test_pagelayout_each_dropdown_has_an_enabled_command(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "B2"}))
            for name in ("PageFormatDialog",                                  # Margins
                         "Orientation?isLandscape:bool=true",                 # Orientation
                         "CalcPageSize?PaperFormat:short=4",                  # Size
                         "DefinePrintArea", "InsertRowBreak"):                # Print Area, Breaks
                self.assertTrue(self.dispatch_enabled(name), name)
            # the Arrange dropdowns act on drawing objects: disabled without one ...
            for name in ("ObjectForwardOne", "BringToFront", "ObjectBackOne", "SendToBack",
                         "ObjectAlignLeft", "FormatGroup", "ObjectMirrorVertical"):
                self.assertFalse(self.dispatch_enabled(name), name)
            # ... and enabled once two shapes are selected
            self.select_new_shape(document, 1000, 2)
            for name in ("ObjectForwardOne", "BringToFront", "ObjectBackOne", "SendToBack",
                         "ObjectAlignLeft", "FormatGroup", "ObjectMirrorVertical", "TransformDialog"):
                self.assertTrue(self.dispatch_enabled(name), name)

    def test_pagelayout_dropdown_popups_list_their_items(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            expected = {
                ("PageLayoutMarginsMenu", "pagelayout_margins"): 4,
                ("PageLayoutOrientationMenu", "pagelayout_orientation"): 2,
                ("PageLayoutSizeMenu", "pagelayout_size"): 13,
                ("PageLayoutPrintAreaMenu", "pagelayout_printarea"): 4,
                ("PageLayoutBreaksMenu", "pagelayout_breaks"): 3,
                ("PageLayoutBringForwardMenu", "pagelayout_bringforward"): 2,
                ("PageLayoutSendBackwardMenu", "pagelayout_sendbackward"): 2,
                ("PageLayoutAlignMenu", "pagelayout_align"): 8,
                ("PageLayoutGroupMenu", "pagelayout_group"): 2,
                ("PageLayoutRotateMenu", "pagelayout_rotate"): 4}
            for (command, resource), count in expected.items():
                xPopup = self.popup_of(".uno:" + command, resource)
                self.assertEqual(count, len(self.popup_commands(xPopup)), command)

    def command_label(self, url):
        """The label the framework resolves for a command URL (what a menu item shows)."""
        xDescriptions = self.xContext.getValueByName("/singletons/com.sun.star.frame.theUICommandDescription")
        xModule = xDescriptions.getByName("com.sun.star.sheet.SpreadsheetDocument")
        props = {p.Name: p.Value for p in xModule.getByName(url)}
        return props["Label"].replace("~", "")

    def test_pagelayout_variant_menu_items_resolve_their_labels_and_are_not_all_checked(self):
        # risk R9: .uno:Orientation has one boolean state; both argument variants must not both show a check mark
        with self.ui_test.create_doc_in_start_center("calc"):
            xPopup = self.popup_of(".uno:PageLayoutOrientationMenu", "pagelayout_orientation")
            commands = self.popup_commands(xPopup)
            self.assertEqual([".uno:Orientation?isLandscape:bool=false", ".uno:Orientation?isLandscape:bool=true"],
                             commands)
            self.assertEqual(["Portrait", "Landscape"], [self.command_label(c) for c in commands])
            checked = [xPopup.isItemChecked(xPopup.getItemId(pos)) for pos in range(xPopup.getItemCount())]
            self.assertLess(sum(checked), 2, "both Orientation variants are checked: %s" % checked)
            xPopup = self.popup_of(".uno:PageLayoutSizeMenu", "pagelayout_size")
            self.assertEqual("Letter", self.command_label(self.popup_commands(xPopup)[0]))
            xPopup = self.popup_of(".uno:PageLayoutMarginsMenu", "pagelayout_margins")
            self.assertEqual(["Normal", "Wide", "Narrow"],
                             [self.command_label(c) for c in self.popup_commands(xPopup)[:3]])

    def test_pagelayout_breaks_dropdown_builds_its_submenus(self):
        # risk R6, second half: the menu bar's own submenus inside a ribbon dropdown
        with self.ui_test.create_doc_in_start_center("calc"):
            xPopup = self.popup_of(".uno:PageLayoutBreaksMenu", "pagelayout_breaks")
            self.assertEqual([".uno:InsertBreakMenu", ".uno:DelBreakMenu", ".uno:DeleteAllBreaks"],
                             self.popup_commands(xPopup))
            xInsert = xPopup.getPopupMenu(xPopup.getItemId(0))
            self.assertEqual([".uno:InsertRowBreak", ".uno:InsertColumnBreak"], self.popup_commands(xInsert))
            xDelete = xPopup.getPopupMenu(xPopup.getItemId(1))
            self.assertEqual([".uno:DeleteRowbreak", ".uno:DeleteColumnbreak"], self.popup_commands(xDelete))

    def test_tabs_are_in_excels_order(self):
        # The tab texts are not exposed to UITests; select each tab position and check which
        # page shows. The texts are checked against the .ui by product/tests/test_calc_tabs.py
        # and by screenshot.
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                xTabs = xCalcDoc.getChild("ContextContainer")
                self.assertEqual(str(TAB_COUNT), get_state_as_dict(xTabs)["PageCount"])
                for pos, page in TAB_PAGES.items():
                    xTabs.executeAction("SELECT", mkPropertyValues({"POS": str(pos)}))
                    self.wait_for(lambda: get_state_as_dict(xCalcDoc.getChild(page))["ReallyVisible"] == "true",
                                  "tab %d does not show %s" % (pos, page))
                    self.assertEqual(str(pos), get_state_as_dict(xTabs)["CurrPagePos"])
            finally:
                self.switch_to("Default")

    def select_rows(self, document, rows):
        document.CurrentController.select(document.Sheets.getByIndex(0).getCellRangeByName(rows))

    def rows_hidden_by_collapse(self, document, first, last):
        """Collapse the outline over rows first..last (0-based) and report whether row `first` hid."""
        xSheet = document.Sheets.getByIndex(0)
        aAddr = xSheet.getCellRangeByName("A%d:A%d" % (first + 1, last + 1)).RangeAddress
        xSheet.hideDetail(aAddr)
        hidden = not xSheet.Rows.getByIndex(first).IsVisible
        xSheet.showDetail(aAddr)
        return hidden

    def test_data_group_and_ungroup_slots_follow_the_selection(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.assertFalse(self.rows_hidden_by_collapse(document, 1, 2))
            self.select_rows(document, "2:3")
            self.xUITest.executeCommand(".uno:DataGroup")
            self.assertTrue(self.rows_hidden_by_collapse(document, 1, 2))
            # a selection change in between must refresh the cached slot state
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.assertFalse(self.dispatch_enabled("DataUngroup"))
            self.select_rows(document, "2:3")
            self.assertTrue(self.dispatch_enabled("DataUngroup"))
            self.xUITest.executeCommand(".uno:DataUngroup")
            self.assertFalse(self.rows_hidden_by_collapse(document, 1, 2))
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.select_rows(document, "2:3")
            self.assertFalse(self.dispatch_enabled("DataUngroup"))

    def test_data_ungroup_listener_is_told_about_state_changes(self):
        # One listener stays registered, so every update below was pushed to it, not produced by
        # a GetState run for a freshly attached listener. This proves end-to-end freshness only:
        # a control probe showed pushes also reach slots without a mirror, so it cannot tell
        # which Invalidate() (olinefun.cxx, tabview3.cxx) caused a push. See
        # product/docs/calc-data-redesign.md, "Known limitations".
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.select_rows(document, "2:3")
            with self.watched_state("DataUngroup") as listener:
                self.assertFalse(listener.enabled)  # no group yet
                # same selection: the outline operation is what changes the state here
                self.xUITest.executeCommand(".uno:DataGroup")
                self.wait_for(lambda: listener.enabled is True, "group did not enable Ungroup: %s" % listener.history)
                # selection change only: the view must invalidate the slot
                xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
                self.wait_for(lambda: listener.enabled is False, "selection did not disable Ungroup: %s" % listener.history)

    def test_data_merge_center_listener_is_told_about_selection_changes(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            with self.watched_state("HomeMergeCenter") as listener:
                self.assertFalse(listener.enabled)  # a single cell cannot merge
                xGrid.executeAction("SELECT", mkPropertyValues({"RANGE": "A1:B2"}))
                self.wait_for(lambda: listener.enabled is True, "range did not enable it: %s" % listener.history)
                xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
                self.wait_for(lambda: listener.enabled is False, "cell did not disable it: %s" % listener.history)

    def test_data_refresh_without_database_range_does_nothing(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            enter_text_to_cell(xGrid, "A1", "keep")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.assertFalse(self.dispatch_enabled("DataRefresh"))
            self.xUITest.executeCommand(".uno:DataRefresh")
            self.assertEqual("keep", document.Sheets.getByIndex(0).getCellRangeByName("A1").String)

    def test_home_merge_center_slot_merges_and_centers(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xCalcDoc = self.xUITest.getTopFocusWindow()
            xGrid = xCalcDoc.getChild("grid_window")
            enter_text_to_cell(xGrid, "A1", "merged")
            # a selection change before dispatch must refresh the slot state
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            xGrid.executeAction("SELECT", mkPropertyValues({"RANGE": "A1:B2"}))
            self.xUITest.executeCommand(".uno:HomeMergeCenter")
            xCell = document.Sheets.getByIndex(0).getCellRangeByName("A1")
            self.assertTrue(xCell.IsMerged)
            self.assertEqual("CENTER", xCell.HoriJustify.value)
            # second dispatch toggles: reads fresh state and unmerges
            self.xUITest.executeCommand(".uno:HomeMergeCenter")
            self.assertFalse(xCell.IsMerged)

    def test_ui_picker_lists_office_variant(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            with self.ui_test.execute_dialog_through_command(".uno:UIPicker") as xDialog:
                xRadio = xDialog.getChild("rbButton10")
                self.assertEqual("Tabbed Office", get_state_as_dict(xRadio)["Text"])
                xRadio.executeAction("CLICK", tuple())
                self.assertEqual("true", get_state_as_dict(xRadio)["Checked"])

    def test_ui_picker_hides_office_variant_in_writer(self):
        # notebookbar_office.ui exists only for Calc
        with self.ui_test.create_doc_in_start_center("writer"):
            with self.ui_test.execute_dialog_through_command(".uno:UIPicker") as xDialog:
                xRadio = xDialog.getChild("rbButton10")
                self.assertEqual("false", get_state_as_dict(xRadio)["Visible"])
                # the regular Tabbed button stays available
                xTabbed = xDialog.getChild("rbButton2")
                self.assertEqual("true", get_state_as_dict(xTabbed)["Visible"])

# vim: set shiftwidth=4 softtabstop=4 expandtab:

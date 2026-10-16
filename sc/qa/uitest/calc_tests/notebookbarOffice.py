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
CALC_MODULE = "com.sun.star.sheet.SpreadsheetDocument"
FUNCTION_DIALOG = ".uno:FunctionDialog"
# what a Function Library menu item dispatches (T4c): the upper-case name, looked up in category 0 (all)
INSERT_FUNCTION = ".uno:InsertFunction?FunctionName:string=%s&FunctionCategory:short=0"

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
        self.state = None  # the State of the last event
        self.history = []  # every IsEnabled the frame pushed, in order
        self.urls = []  # the FeatureURL.Complete of every event, in order

    def statusChanged(self, aEvent):
        self.enabled = aEvent.IsEnabled
        self.state = aEvent.State
        self.history.append(aEvent.IsEnabled)
        self.urls.append(aEvent.FeatureURL.Complete)

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
        listener.url = aURL.Complete  # the URL it listens on, as the dispatch keys it
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
        self.assertEqual(65, len(names))  # 42 slots, 23 extra family variants
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
        # Data 9, Insert 17 (9 chart-type variants), Page Layout 8 (7 variants of 3 families),
        # Formulas 7 (4 Python variants, Evaluate Formula, Watch Window, Calculate Sheet),
        # Review 5 (Translate, Previous and Next Comment, Allow Edit Ranges, Hide Ink),
        # View 14 (5 Sheet View, Page Layout, Custom Views, Ruler, Arrange All, Hide, Unhide, 3 Side by Side),
        # Help 2 (Feedback, Blog)
        self.assertEqual(62, len(buttons))
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

    def menu_controller(self, command, resource=None):
        """The menu controller of the ribbon dropdown `command` and the awt popup menu it built.

        `resource` is the popup file a ResourceMenuController reads (its "Value"); the Function
        Library menus (T4c) need none: their controller builds them from the command."""
        xDesktop = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.xContext)
        xFrame = xDesktop.getCurrentFrame()
        xFactory = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.PopupMenuControllerFactory", self.xContext)
        self.assertTrue(xFactory.hasController(command, CALC_MODULE), command)
        args = {"Frame": xFrame, "CommandURL": command, "ModuleIdentifier": CALC_MODULE}
        if resource is not None:
            args["Value"] = resource
        xController = xFactory.createInstanceWithArgumentsAndContext(
            command, mkPropertyValues(args), self.xContext)
        self.assertIsNotNone(xController, command)
        xPopup = self.xContext.ServiceManager.createInstanceWithContext("com.sun.star.awt.PopupMenu", self.xContext)
        xController.setPopupMenu(xPopup)
        xController.updatePopupMenu()
        return xController, xPopup

    def popup_of(self, command, resource):
        """The awt popup menu the ribbon dropdown `command` shows, built by its menu controller."""
        return self.menu_controller(command, resource)[1]

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

    def wait_until_empty(self, items, timeout=5):
        """Poll items() until it returns an empty list; return its last value."""
        deadline = time.time() + timeout
        while items() and time.time() < deadline:
            time.sleep(0.05)
        return items()

    def wait_until_quiet(self, listeners, quiet=1.0, timeout=10):
        """Wait until no listener has heard an event for `quiet` seconds: the bindings push
        pending states from a 300 ms timer (TIMEOUT_FIRST, sfx2 bindings.cxx), so after a second
        of silence every push already arrived and the next count starts after them."""
        deadline = time.time() + timeout
        heard = [len(listener.history) for listener in listeners]
        since = time.time()
        while time.time() < deadline:
            time.sleep(0.05)
            now = [len(listener.history) for listener in listeners]
            if now != heard:
                heard, since = now, time.time()
            elif time.time() - since >= quiet:
                return
        self.fail("the listeners kept hearing events: %s" % [listener.history for listener in listeners])

    def check_main_and_variant_listeners_hear_state_changes(self, document):
        # URLs that differ only in their arguments bind the same slot and share its dispatch,
        # which the first of them bound. Every listener must be told about later state changes,
        # one event per change, each with its own URL: controllers match FeatureURL.Complete.
        # Selecting a drawing object takes the cell shell, and so the Sparkline slot, away.
        self.xUITest.getTopFocusWindow().getChild("grid_window").executeAction(
            "SELECT", mkPropertyValues({"CELL": "A1"}))
        with self.watched_state("InsertSparkline") as main, \
                self.watched_state("InsertSparkline?Type:string=column") as variant:
            listeners = (main, variant)
            not_told = lambda state: [listener.url for listener in listeners if listener.enabled is not state]
            self.wait_until_quiet(listeners)  # the slot cache's first push arrives before counting
            start = [len(listener.history) for listener in listeners]
            self.assertEqual([], not_told(True))
            self.select_new_shape(document, 1000)
            self.assertEqual([], self.wait_until_empty(lambda: not_told(False)), "a shape disabled the slot")
            self.select_rows(document, "A1")  # back to the cells
            self.assertEqual([], self.wait_until_empty(lambda: not_told(True)), "a cell enabled the slot")
            self.wait_until_quiet(listeners)  # a duplicate or extra event arrives before checking
            for listener, n in zip(listeners, start):
                self.assertEqual([False, True], listener.history[n:], listener.url)
                self.assertEqual({listener.url}, set(listener.urls), listener.url)

    def test_argument_variant_listener_hears_later_state_changes(self):
        # Default UI: the plain .uno:InsertSparkline bound the slot first.
        with self.ui_test.create_doc_in_start_center("calc") as document:
            self.check_main_and_variant_listeners_hear_state_changes(document)

    def test_main_url_listener_hears_its_own_url_when_a_variant_bound_the_slot(self):
        # Office UI: the Sparkline Line button's URL (...?Type:string=line) bound the slot first.
        with self.ui_test.create_doc_in_start_center("calc") as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_main_and_variant_listeners_hear_state_changes(document)
            finally:
                self.switch_to("Default")

    def test_sparkline_buttons_follow_their_slot_state(self):
        # The three Sparkline buttons are argument variants of one slot; each one must be drawn
        # with the slot's current state, not only the variant whose URL bound the slot first.
        with self.ui_test.create_doc_in_start_center("calc") as document:
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                xCalcDoc.getChild("grid_window").executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
                buttons = {box: xCalcDoc.getChild("bxInsert" + box).getChild("toolboxitem-1")
                           for box in ("SparklineLine", "SparklineColumn", "SparklineWinLoss")}
                drawn_not = lambda state: sorted(box for box, xItem in buttons.items()
                                                 if get_state_as_dict(xItem)["Enabled"] != state)
                self.assertEqual([], self.wait_until_empty(lambda: drawn_not("true")), "drawn disabled at start")
                self.select_new_shape(document, 1000)
                self.assertEqual([], self.wait_until_empty(lambda: drawn_not("false")),
                                 "drawn enabled with a shape selected")
                self.select_rows(document, "A1")
                self.assertEqual([], self.wait_until_empty(lambda: drawn_not("true")),
                                 "drawn disabled with a cell selected again")
            finally:
                self.switch_to("Default")

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

    def test_formulas_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_formulas.json").read_text(encoding="utf-8"))
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

    def test_formulas_placeholders_are_disabled_and_inert(self):
        # 5 slots: the Python family (4 variants), Error Checking (a menu item), Evaluate Formula,
        # Watch Window and Calculate Sheet
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: 403 <= e["offset"] <= 407)
        self.assertEqual(8, len(names))
        self.check_placeholders_are_disabled_and_inert(names)

    def fill_row(self, xGrid, row, values=("1", "2", "3")):
        for col, text in zip("ABC", values):
            enter_text_to_cell(xGrid, "%s%d" % (col, row), text)

    def test_formulas_autosum_body_inserts_a_sum_like_autosum(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xSheet = document.Sheets.getByIndex(0)
            for row in (1, 2, 3, 4, 5, 6):
                self.fill_row(xGrid, row)
            for row, command, formula in (
                    (1, ".uno:AutoSum", "=SUM(A1:C1)"),
                    (2, ".uno:FormulasAutoSum", "=SUM(A2:C2)"),
                    (3, ".uno:AutoSum?Function:string=average", "=AVERAGE(A3:C3)"),
                    (4, ".uno:AutoSum?Function:string=count", "=COUNT(A4:C4)"),
                    (5, ".uno:AutoSum?Function:string=max", "=MAX(A5:C5)"),
                    (6, ".uno:AutoSum?Function:string=min", "=MIN(A6:C6)")):
                xGrid.executeAction("SELECT", mkPropertyValues({"RANGE": "A%d:C%d" % (row, row)}))
                self.xUITest.executeCommand(command)
                xCell = xSheet.getCellRangeByName("D%d" % row)
                self.assertEqual(formula, xCell.Formula, command)
            self.assertEqual(xSheet.getCellRangeByName("D1").Value, xSheet.getCellRangeByName("D2").Value)

    def test_formulas_autosum_body_ignores_an_argument_it_does_not_declare(self):
        # risk R3: .uno:FormulasAutoSum declares no Function argument; sfx2 must ignore it and still
        # run the plain sum (it does not reach the average branch of the shared Execute)
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            self.fill_row(xGrid, 1)
            xGrid.executeAction("SELECT", mkPropertyValues({"RANGE": "A1:C1"}))
            self.assertTrue(self.dispatch_enabled("FormulasAutoSum?Function:string=average"))
            self.xUITest.executeCommand(".uno:FormulasAutoSum?Function:string=average")
            self.assertEqual("=SUM(A1:C1)", document.Sheets.getByIndex(0).getCellRangeByName("D1").Formula)

    def test_formulas_autosum_body_state_matches_autosum_in_every_mode(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            same = lambda: (self.dispatch_enabled("AutoSum"), self.dispatch_enabled("FormulasAutoSum"))
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.assertEqual((True, True), same())
            xGrid.executeAction("SELECT", mkPropertyValues({"RANGE": "A1:B2"}))
            self.assertEqual((True, True), same())
            self.select_new_shape(document, 1000)  # a drawing object takes the cell shell away
            original, body = same()
            self.assertFalse(original)
            self.assertEqual(original, body)
            self.select_rows(document, "A1")
            self.assertEqual((True, True), same())
            xPage = document.DrawPages.getByIndex(0)
            for n, (service, clsid) in enumerate((
                    ("com.sun.star.drawing.GraphicObjectShape", None),
                    ("com.sun.star.drawing.OLE2Shape", "12DCAE26-281F-416F-a234-c3086127382e"))):
                xShape = document.createInstance(service)
                if clsid:
                    xShape.CLSID = clsid
                xShape.Name = "T4aObject%d" % n
                xPage.add(xShape)
                xShape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", 1000 + 4000 * n, 1000))
                xShape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", 3000, 2000))
                self.select_rows(document, "A1")
                xGrid.executeAction("SELECT", mkPropertyValues({"OBJECT": xShape.Name}))
                original, body = same()
                self.assertEqual(original, body, service)
            # in cell edit mode the two stay alike too
            self.select_rows(document, "A1")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            xGrid.executeAction("TYPE", mkPropertyValues({"KEYCODE": "F2"}))
            self.assertEqual(*same())
            xGrid.executeAction("TYPE", mkPropertyValues({"KEYCODE": "ESC"}))

    def test_formulas_autosum_body_listener_hears_what_the_original_hears(self):
        # One listener each stays registered: both slots must be told about the same state changes
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            with self.watched_state("AutoSum") as original, self.watched_state("FormulasAutoSum") as body:
                time.sleep(1)
                start = [len(original.history), len(body.history)]
                self.assertEqual((True, True), (original.enabled, body.enabled))
                self.select_new_shape(document, 1000)
                self.wait_for(lambda: original.enabled is False and body.enabled is False,
                              "a shape did not disable both: %s %s" % (original.history, body.history))
                self.select_rows(document, "A1")
                self.wait_for(lambda: original.enabled is True and body.enabled is True,
                              "a cell did not enable both: %s %s" % (original.history, body.history))
                time.sleep(1)
                self.assertEqual(original.history[start[0]:], body.history[start[1]:])

    def test_formulas_autosum_button_is_drawn_like_the_original_state(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                xCalcDoc.getChild("grid_window").executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
                xItem = xCalcDoc.getChild("bxFormulasAutoSum").getChild("toolboxitem-1")
                drawn = lambda: get_state_as_dict(xItem)["Enabled"]
                self.wait_for(lambda: drawn() == "true", "AutoSum body drawn disabled at start")
                self.select_new_shape(document, 1000)
                self.wait_for(lambda: drawn() == "false", "AutoSum body drawn enabled with a shape selected")
                self.assertFalse(self.dispatch_enabled("AutoSum"))
                self.select_rows(document, "A1")
                self.wait_for(lambda: drawn() == "true", "AutoSum body drawn disabled with a cell selected")
            finally:
                self.switch_to("Default")

    def test_formulas_autosum_menu_is_usable_when_the_body_is(self):
        # VCL arrow check: while the body is disabled the arrow is too, so the menu must offer
        # nothing that works then. Every AutoSum item shares the body's shell; the only item that is
        # enabled with a shape selected would be a hole in this rule (Function... is checked here).
        with self.ui_test.create_doc_in_start_center("calc") as document:
            self.select_new_shape(document, 1000)
            body = self.dispatch_enabled("FormulasAutoSum")
            items = {name: self.dispatch_enabled(name) for name in (
                "AutoSum", "AutoSum?Function:string=average", "AutoSum?Function:string=count",
                "AutoSum?Function:string=max", "AutoSum?Function:string=min", "FunctionDialog")}
            self.assertFalse(body)
            self.assertEqual([], [name for name, enabled in items.items() if enabled and not body],
                             "menu items usable while the body (and with it the arrow) is disabled")

    def test_formulas_each_dropdown_has_an_enabled_command(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "B2"}))
            for name in ("FunctionDialog", "InsertFunction",                # Function Library menus
                         "FormulasAutoSum", "AutoSum",                       # AutoSum
                         "InsertName",                                       # Use in Formula
                         "ClearArrows", "ClearArrowPrecedents", "ClearArrowDependents",
                         "ShowErrors",                                       # Error Checking
                         "AutomaticCalculation",                             # Calculation Options
                         "DefineName", "AddName", "CreateNames", "ShowPrecedents", "ShowDependents",
                         "ToggleFormula", "Calculate"):
                self.assertTrue(self.dispatch_enabled(name), name)

    def test_formulas_dropdown_popups_list_their_items(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            for command in ("FormulasRecentlyUsedMenu", "FormulasFinancialMenu", "FormulasLogicalMenu",
                            "FormulasTextMenu", "FormulasDateTimeMenu", "FormulasLookupMenu",
                            "FormulasMathMenu", "FormulasMoreFunctionsMenu"):
                xPopup = self.menu_controller(".uno:" + command)[1]
                self.assertEqual(FUNCTION_DIALOG, self.popup_commands(xPopup)[-1], command)
            expected = {
                ("FormulasAutoSumMenu", "formulas_autosum"): [
                    ".uno:AutoSum", ".uno:AutoSum?Function:string=average",
                    ".uno:AutoSum?Function:string=count", ".uno:AutoSum?Function:string=max",
                    ".uno:AutoSum?Function:string=min", ".uno:FunctionDialog"],
                ("FormulasUseInFormulaMenu", "formulas_useinformula"): [".uno:InsertName"],
                ("FormulasRemoveArrowsMenu", "formulas_removearrows"): [
                    ".uno:ClearArrows", ".uno:ClearArrowPrecedents", ".uno:ClearArrowDependents"],
                ("FormulasErrorCheckingMenu", "formulas_errorchecking"): [
                    ".uno:FormulasErrorChecking", ".uno:ShowErrors"],
                ("FormulasCalcOptionsMenu", "formulas_calcoptions"): [
                    ".uno:AutomaticCalculation?AutomaticCalculation:bool=true",
                    ".uno:AutomaticCalculation?AutomaticCalculation:bool=false"]}
            for (command, resource), items in expected.items():
                xPopup = self.popup_of(".uno:" + command, resource)
                self.assertEqual(items, self.popup_commands(xPopup), command)

    def test_review_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_review.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(7, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xCalcDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xCalcDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_review_placeholders_are_disabled_and_inert(self):
        # 5 slots: Check Accessibility (a menu item), Translate, the Previous/Next Comment family
        # (2 variants), Allow Edit Ranges and Hide Ink
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: 408 <= e["offset"] <= 412)
        self.assertEqual(6, len(names))
        self.check_placeholders_are_disabled_and_inert(names)

    def test_review_each_dropdown_has_an_enabled_command(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "B2"}))
            for name in ("InsertAnnotation",                                  # Comments, Notes
                         "SpellDialog", "Protect", "ToolProtectionDocument", "ShareDocument"):
                self.assertTrue(self.dispatch_enabled(name), name)
            # AutoFormat (Check Accessibility menu) needs a range of cells
            document.getCurrentController().select(document.Sheets.getByIndex(0).getCellRangeByName("A1:C3"))
            self.assertTrue(self.dispatch_enabled("AutoFormat"), "AutoFormat")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "B2"}))
            # the commands that need a comment: disabled without one, enabled once B2 has one
            for name in ("DeleteNote", "EditAnnotation", "ShowAllNotes", "HideAllNotes"):
                self.assertFalse(self.dispatch_enabled(name), name)
            address = document.Sheets.getByIndex(0).getCellRangeByName("B2").CellAddress
            document.Sheets.getByIndex(0).Annotations.insertNew(address, "a comment")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "B2"}))
            for name in ("DeleteNote", "EditAnnotation", "ShowAllNotes", "HideAllNotes", "NoteVisible"):
                self.assertTrue(self.dispatch_enabled(name), name)

    def test_review_dropdown_popups_list_their_items(self):
        goto = ".uno:ReviewGoToComment?Direction:string="
        with self.ui_test.create_doc_in_start_center("calc"):
            xPopup = self.popup_of(".uno:ReviewAccessibilityMenu", "review_accessibility")
            self.assertEqual([".uno:ReviewCheckAccessibility", ".uno:ObjectTitleDescription",
                              ".uno:AutoFormat", ".uno:SplitCell"], self.popup_commands(xPopup))
            xPopup = self.popup_of(".uno:ReviewNotesMenu", "review_notes")
            self.assertEqual([".uno:InsertAnnotation", ".uno:EditAnnotation", goto + "previous",
                              goto + "next", ".uno:NoteVisible", ".uno:ShowAllNotes",
                              ".uno:HideAllNotes", ".uno:DeleteAllNotes"], self.popup_commands(xPopup))

    def test_review_menu_placeholders_resolve_their_labels_and_are_disabled(self):
        goto = ".uno:ReviewGoToComment?Direction:string="
        with self.ui_test.create_doc_in_start_center("calc"):
            self.assertEqual("Check Accessibility", self.command_label(".uno:ReviewCheckAccessibility"))
            self.assertEqual("Previous Comment", self.command_label(goto + "previous"))
            self.assertEqual("Next Comment", self.command_label(goto + "next"))
            # the items are the always-disabled placeholder slots (a popup built by its controller
            # alone does not refresh item states, so ask the frame, as a status listener would)
            for name in ("ReviewCheckAccessibility", "ReviewGoToComment?Direction:string=previous",
                         "ReviewGoToComment?Direction:string=next"):
                self.assertFalse(self.dispatch_enabled(name), name)

    def test_view_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_view.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(7, len(layout["sections"]))
                self.assertEqual("phbView", layout["page"])
                self.assertEqual("Sheet View", layout["sections"][0]["caption"])
                for section in layout["sections"]:
                    xLabel = xCalcDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xCalcDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_view_placeholders_are_disabled_and_inert(self):
        # 7 slots: Page Layout, Custom Views, Ruler, Arrange All, the Hide/Unhide family (2 variants),
        # the Side by Side family (3) and the Sheet View family (5)
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: 413 <= e["offset"] <= 418 or e["offset"] == 421)
        self.assertEqual(14, len(names))
        self.check_placeholders_are_disabled_and_inert(names)

    def test_view_each_dropdown_has_an_enabled_command(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "B2"}))
            for name in ("FreezePanes", "FreezePanesRow", "FreezePanesColumn",   # Freeze Panes
                         "MacroManager", "RunMacro", "BasicIDEAppear",           # Macros
                         "NewWindow", "SplitWindow",                             # Window
                         "NormalViewMode", "PagebreakMode", "ChangeTheme", "Navigator",
                         "ToggleSheetGrid", "InputLineVisible", "ViewRowColumnHeaders",
                         "ViewColumnRowHighlighting", "Zoom", "Zoom100Percent", "ZoomOptimal"):
                self.assertTrue(self.dispatch_enabled(name), name)

    def test_view_dropdown_popups_list_their_items(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            xPopup = self.popup_of(".uno:ViewFreezePanesMenu", "view_freezepanes")
            self.assertEqual([".uno:FreezePanes", ".uno:FreezePanesRow", ".uno:FreezePanesColumn"],
                             self.popup_commands(xPopup))
            xPopup = self.popup_of(".uno:ViewMacrosMenu", "view_macros")
            # Macro Manager is flagged experimental: the framework hides it unless experimental mode
            # is on, in the menu bar as here, so it is the first item only in that mode
            commands = self.popup_commands(xPopup)
            self.assertEqual([".uno:MacroRecorder", ".uno:RunMacro", ".uno:BasicIDEAppear"], commands[-3:])
            self.assertIn(commands[:-3], ([], [".uno:MacroManager"]))

    def test_view_switch_windows_dropdown_fills_with_the_open_windows(self):
        # risk R7: the framework's window list controller, registered under the new command and
        # without a popup file, must list the open windows when the dropdown opens
        with self.ui_test.create_doc_in_start_center("calc"):
            xController, xPopup = self.menu_controller(".uno:ViewSwitchWindowsMenu")
            event = uno.createUnoStruct("com.sun.star.awt.MenuEvent")
            event.Source = xPopup
            xController.itemActivated(event)
            windows = [xPopup.getItemId(pos) for pos in range(xPopup.getItemCount())
                       if 4600 <= xPopup.getItemId(pos) <= 4699]
            self.assertGreaterEqual(len(windows), 1)
            texts = [xPopup.getItemText(nId) for nId in windows]
            self.assertTrue(any("Untitled" in text for text in texts), texts)
            self.assertEqual(1, sum(1 for nId in windows if xPopup.isItemChecked(nId)), "the active window")

    def test_view_placeholder_labels_resolve_for_every_variant(self):
        src = Path(os.environ["TDOC"]).parents[3]
        entries = json.loads((src / "product" / "tests" / "placeholders.json").read_text(encoding="utf-8"))
        with self.ui_test.create_doc_in_start_center("calc"):
            count = 0
            for entry in entries:
                if not (413 <= entry["offset"] <= 418 or entry["offset"] == 421):
                    continue
                base = ".uno:" + entry["command"]
                for variant, label in entry.get("variant_labels", {}).items():
                    self.assertEqual(label, self.command_label(base + "?" + variant), variant)
                    count += 1
                if "label" in entry:
                    self.assertEqual(entry["label"], self.command_label(base))
                    count += 1
            self.assertEqual(14, count)

    def test_help_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_help.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(2, len(layout["sections"]))
                self.assertEqual("phbHelp", layout["page"])
                for section in layout["sections"]:
                    xLabel = xCalcDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xCalcDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_help_placeholders_are_disabled_and_inert(self):
        # 2 slots, no variants: Feedback and Blog
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: 419 <= e["offset"] <= 420)
        self.assertEqual(["HelpFeedback", "HelpBlog"], [n.removeprefix(".uno:") for n in names])
        self.check_placeholders_are_disabled_and_inert(names)

    def test_help_placeholder_buttons_are_drawn_disabled_and_the_others_enabled(self):
        # what the ribbon draws: toolboxitem `Enabled`. Only the two placeholders are disabled.
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "calc_help.json").read_text(encoding="utf-8"))
        disabled = {"HelpFeedback", "HelpBlog"}
        with self.ui_test.create_doc_in_start_center("calc"):
            self.switch_to(OFFICE_UI)
            try:
                xCalcDoc = self.xUITest.getTopFocusWindow()
                drawn = {}
                for section in layout["sections"]:
                    for column in section["columns"]:
                        for box in column:
                            xBox = xCalcDoc.getChild("bx" + layout["id_prefix"] + box["id"])
                            drawn[box["items"][0]["cmd"]] = xBox.getChild("toolboxitem-1")
                self.assertEqual(7, len(drawn))
                self.wait_for(lambda: all((get_state_as_dict(x)["Enabled"] == "false") == (cmd in disabled)
                                          for cmd, x in drawn.items()),
                              "Help buttons not drawn as designed: " + str(
                                  {c: get_state_as_dict(x)["Enabled"] for c, x in drawn.items()}))
            finally:
                self.switch_to("Default")

    def test_help_existing_commands_are_enabled(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            for name in ("HelpIndex", "QuestionAnswers", "Documentation", "WhatsNew", "GetInvolved"):
                self.assertTrue(self.dispatch_enabled(name), name)

    def test_help_placeholder_labels_resolve(self):
        src = Path(os.environ["TDOC"]).parents[3]
        entries = json.loads((src / "product" / "tests" / "placeholders.json").read_text(encoding="utf-8"))
        with self.ui_test.create_doc_in_start_center("calc"):
            count = 0
            for entry in entries:
                if 419 <= entry["offset"] <= 420:
                    self.assertEqual(entry["label"], self.command_label(".uno:" + entry["command"]))
                    count += 1
            self.assertEqual(2, count)

    def test_formulas_variant_menu_items_resolve_their_labels(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            xPopup = self.popup_of(".uno:FormulasAutoSumMenu", "formulas_autosum")
            self.assertEqual(["Sum", "Average", "Count Numbers", "Max", "Min", "Function"],
                             [self.command_label(c).replace("...", "") for c in self.popup_commands(xPopup)])

    def test_formulas_calculation_options_automatic_and_manual_set_the_mode(self):
        # risk R9: both items are URL variants of one boolean slot; the slot honours the argument,
        # so picking the mode that is already current leaves it unchanged (it does not toggle).
        # The check marks are set by MenuBarManager on a real menu activation, which an awt popup
        # built here never gets: they are checked by screenshot (see the T3c report).
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xPopup = self.popup_of(".uno:FormulasCalcOptionsMenu", "formulas_calcoptions")
            auto = ".uno:AutomaticCalculation?AutomaticCalculation:bool="
            self.assertEqual([auto + "true", auto + "false"], self.popup_commands(xPopup))
            self.assertEqual(["Automatic", "Manual"],
                             [self.command_label(c) for c in self.popup_commands(xPopup)])
            self.assertTrue(document.isAutomaticCalculationEnabled())
            for automatic in (True, False, False, True, True):
                self.xUITest.executeCommand(auto + str(automatic).lower())
                self.assertEqual(automatic, document.isAutomaticCalculationEnabled())

    def functions_by_category(self):
        """{category id: {upper-case name: description}} as Calc's FunctionDescriptions service lists them."""
        xDescriptions = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.sheet.FunctionDescriptions", self.xContext)
        out = {}
        for i in range(xDescriptions.getCount()):
            props = {p.Name: p.Value for p in xDescriptions.getByIndex(i)}
            out.setdefault(props["Category"], {})[props["Name"].upper()] = props["Description"]
        return out

    def function_items(self, xPopup):
        """The function names a Function Library menu lists (checking each item's command), and the
        commands after its separator."""
        names, tail, past_separator = [], [], False
        for pos in range(xPopup.getItemCount()):
            nId = xPopup.getItemId(pos)
            if nId == 0:  # the separator
                past_separator = True
            elif past_separator:
                tail.append(xPopup.getCommand(nId))
            else:
                name = xPopup.getItemText(nId)
                self.assertEqual(INSERT_FUNCTION % name, xPopup.getCommand(nId))
                names.append(name)
        return names, tail

    def item_id(self, xPopup, text):
        for pos in range(xPopup.getItemCount()):
            if xPopup.getItemText(xPopup.getItemId(pos)) == text:
                return xPopup.getItemId(pos)
        self.fail("no menu item " + text)

    def select_item(self, xController, xMenu, nId):
        """What a click on the item does: the menu tells its listener, the controller."""
        aEvent = uno.createUnoStruct("com.sun.star.awt.MenuEvent")
        aEvent.Source = xMenu
        aEvent.MenuId = nId
        xController.itemSelected(aEvent)

    def test_formulas_function_menus_list_their_category_and_end_with_the_function_dialog(self):
        # T4c: the design's category of each menu; the items are the functions of the category in
        # the UI language, each inserting itself, then "Function..." after a separator
        with self.ui_test.create_doc_in_start_center("calc"):
            functions = self.functions_by_category()
            for command, category in (("FormulasFinancialMenu", 3), ("FormulasLogicalMenu", 5),
                                      ("FormulasTextMenu", 10), ("FormulasDateTimeMenu", 2),
                                      ("FormulasLookupMenu", 9), ("FormulasMathMenu", 6)):
                names, tail = self.function_items(self.menu_controller(".uno:" + command)[1])
                expected = set(functions[category])
                if category == 2:
                    expected.discard("WEEKNUM_OOO")  # hidden, as in the Function Wizard
                self.assertEqual(sorted(expected), sorted(names), command)
                self.assertEqual(len(names), len(set(names)), command)
                self.assertEqual([FUNCTION_DIALOG], tail, command)

    def test_formulas_financial_and_lookup_menus_list_excels_functions(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            descriptions = self.functions_by_category()[3]
            xPopup = self.menu_controller(".uno:FormulasFinancialMenu")[1]
            names, tail = self.function_items(xPopup)
            self.assertTrue({"PMT", "NPV", "FV", "PV", "RATE", "IRR"} <= set(names), names)
            self.assertEqual("Function...", self.command_label(tail[-1]))
            self.assertEqual("Function...", xPopup.getItemText(xPopup.getItemId(xPopup.getItemCount() - 1))
                             .replace("~", ""))
            # the tooltip: the signature, then the short description of the Function Wizard
            tip = xPopup.getTipHelpText(self.item_id(xPopup, "PMT"))
            self.assertTrue(tip.startswith("PMT("), tip)
            self.assertTrue(tip.endswith("\n" + descriptions["PMT"]), tip)
            names, _tail = self.function_items(self.menu_controller(".uno:FormulasLookupMenu")[1])
            self.assertTrue({"VLOOKUP", "HLOOKUP", "INDEX", "MATCH", "XLOOKUP"} <= set(names), names)

    def test_formulas_more_functions_has_the_five_category_submenus(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            functions = self.functions_by_category()
            xPopup = self.menu_controller(".uno:FormulasMoreFunctionsMenu")[1]
            submenus = [(".uno:FormulasStatisticalMenu", "Statistical", 8),
                        (".uno:FormulasEngineeringMenu", "Engineering", 11),
                        (".uno:FormulasInformationMenu", "Information", 4),
                        (".uno:FormulasDatabaseMenu", "Database", 1),
                        (".uno:FormulasArrayMenu", "Array", 7)]
            self.assertEqual([c for c, _l, _n in submenus] + [FUNCTION_DIALOG], self.popup_commands(xPopup))
            self.assertEqual(0, xPopup.getItemId(len(submenus)), "a separator before Function...")
            listed = {}
            for pos, (command, label, category) in enumerate(submenus):
                nId = xPopup.getItemId(pos)
                self.assertEqual(label, self.command_label(command))
                self.assertEqual(label, xPopup.getItemText(nId).replace("~", ""))
                xSubmenu = xPopup.getPopupMenu(nId)
                self.assertIsNotNone(xSubmenu, command)
                names, tail = self.function_items(xSubmenu)
                self.assertEqual(sorted(functions[category]), sorted(names), command)
                self.assertEqual([], tail, command)
                listed[label] = set(names)
            self.assertTrue({"AVERAGEIF", "STDEV", "MEDIAN"} <= listed["Statistical"])
            self.assertTrue({"CONVERT", "DEC2BIN", "BESSELJ"} <= listed["Engineering"])
            self.assertTrue({"ISBLANK", "CELL"} <= listed["Information"])

    def test_formulas_function_item_inserts_the_function_like_the_sidebar(self):
        # SID_INS_FUNCTION starts input mode and inserts "=NAME(" plus the argument names, as the
        # Functions sidebar does; nothing is entered until the user confirms
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xCalcDoc = self.xUITest.getTopFocusWindow()
            xGrid = xCalcDoc.getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "B2"}))
            xController, xPopup = self.menu_controller(".uno:FormulasMathMenu")
            nId = self.item_id(xPopup, "SUM")
            self.assertEqual(INSERT_FUNCTION % "SUM", xPopup.getCommand(nId))
            self.select_item(xController, xPopup, nId)
            xInput = xCalcDoc.getChild("sc_input_window")
            self.wait_for(lambda: get_state_as_dict(xInput)["Text"].startswith("=SUM("),
                          "the input line shows: " + get_state_as_dict(xInput)["Text"])
            xGrid.executeAction("TYPE", mkPropertyValues({"KEYCODE": "ESC"}))
            self.assertEqual("", document.Sheets.getByIndex(0).getCellRangeByName("B2").Formula)

    def test_formulas_recently_used_lists_a_function_after_it_is_used(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            xCalcDoc = self.xUITest.getTopFocusWindow()
            xGrid = xCalcDoc.getChild("grid_window")
            enter_text_to_cell(xGrid, "A1", "=DEGREES(1)")  # a typed formula (ScViewFunc::EnterData)
            xRecentController, xRecent = self.menu_controller(".uno:FormulasRecentlyUsedMenu")
            names, tail = self.function_items(xRecent)
            self.assertEqual("DEGREES", names[0], names)
            self.assertEqual([FUNCTION_DIALOG], tail)
            # picked from a menu, like the Functions sidebar does
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "B1"}))
            xController, xPopup = self.menu_controller(".uno:FormulasTextMenu")
            self.select_item(xController, xPopup, self.item_id(xPopup, "REPT"))
            xInput = xCalcDoc.getChild("sc_input_window")
            self.wait_for(lambda: get_state_as_dict(xInput)["Text"].startswith("=REPT("), "REPT not inserted")
            xGrid.executeAction("TYPE", mkPropertyValues({"KEYCODE": "ESC"}))
            # the dropdown rebuilds its menu each time it opens (PopupMenuToolbarController)
            xRecentController.updatePopupMenu()
            names, tail = self.function_items(xRecent)
            self.assertEqual(["REPT", "DEGREES"], names[:2])
            self.assertEqual([FUNCTION_DIALOG], tail)

    def function_item_states(self, xPopup):
        """The set of enabled states of the function items (up to the separator)."""
        states = set()
        for pos in range(xPopup.getItemCount()):
            nId = xPopup.getItemId(pos)
            if nId == 0:
                break
            states.add(xPopup.isItemEnabled(nId))
        return states

    def test_formulas_function_items_are_disabled_while_insert_function_is(self):
        # With a drawing object selected .uno:InsertFunction is disabled (no cell shell): a menu
        # built then shows its function items disabled, so none can be picked (nor reach the
        # recently used list); with a cell selected they are enabled.
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.assertTrue(self.dispatch_enabled("InsertFunction"))
            xController, xPopup = self.menu_controller(".uno:FormulasLogicalMenu")
            self.assertEqual({True}, self.function_item_states(xPopup))
            xShape = document.createInstance("com.sun.star.drawing.RectangleShape")
            xShape.Name = "T4cShape"
            document.DrawPages.getByIndex(0).add(xShape)
            xShape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", 1000, 1000))
            xShape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", 3000, 2000))
            xGrid.executeAction("SELECT", mkPropertyValues({"OBJECT": "T4cShape"}))
            self.assertFalse(self.dispatch_enabled("InsertFunction"))
            xController.updatePopupMenu()  # the dropdown opens again
            self.assertEqual({False}, self.function_item_states(xPopup))
            xMore = self.menu_controller(".uno:FormulasMoreFunctionsMenu")[1]
            self.assertEqual({False}, self.function_item_states(xMore.getPopupMenu(xMore.getItemId(0))))
            self.select_rows(document, "A1")
            xController.updatePopupMenu()
            self.assertEqual({True}, self.function_item_states(xPopup))

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

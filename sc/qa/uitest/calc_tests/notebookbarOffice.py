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

    def test_insert_dropdowns_and_menu_items_are_enabled(self):
        with self.ui_test.create_doc_in_start_center("calc"):
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            # the two dropdown commands have no slot: their popups are checked below
            for name in ("InsertGraphic", "Gallery", "InsertCalcTable", "InsertObjectChart",
                         "DataDataPilotRun", "HyperlinkDialog", "InsertAnnotation", "DrawText"):
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

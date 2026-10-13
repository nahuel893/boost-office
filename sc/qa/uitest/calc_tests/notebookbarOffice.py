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

    def test_data_placeholders_have_a_slot_that_is_always_disabled(self):
        placeholders = ["DataFromDatabase", "DataRecentSources", "DataConnections",
                        "DataConnectionProperties", "DataFilterReapply", "DataFlashFill",
                        "DataRelationships", "DataManageModel", "DataForecastSheet"]
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            enter_text_to_cell(xGrid, "A1", "keep")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.assertTrue(self.dispatch_enabled("DataSort"))  # control: a real, enabled slot
            for name in placeholders:
                self.assertFalse(self.dispatch_enabled(name), name)
                self.xUITest.executeCommand(".uno:" + name)  # must do nothing, not even a dialog
            xSheet = document.Sheets.getByIndex(0)
            self.assertEqual("keep", xSheet.getCellRangeByName("A1").String)

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
        # One listener stays registered, so every update below was pushed by an Invalidate()
        # mirror (olinefun.cxx for the group, tabview3.cxx for the selection), not by a GetState
        # run for a freshly attached listener.
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xGrid = self.xUITest.getTopFocusWindow().getChild("grid_window")
            xGrid.executeAction("SELECT", mkPropertyValues({"CELL": "A1"}))
            self.select_rows(document, "2:3")
            with self.watched_state("DataUngroup") as listener:
                self.assertFalse(listener.enabled)  # no group yet
                # same selection: only the outline operation can have invalidated the slot
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

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
from pathlib import Path

from uitest.framework import UITestCase
from uitest.uihelper.calc import enter_text_to_cell
from uitest.uihelper.common import get_state_as_dict
from libreoffice.uno.propertyvalue import mkPropertyValues

OFFICE_UI = "notebookbar_office.ui"


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

    def test_home_merge_center_slot_merges_and_centers(self):
        with self.ui_test.create_doc_in_start_center("calc") as document:
            xCalcDoc = self.xUITest.getTopFocusWindow()
            xGrid = xCalcDoc.getChild("grid_window")
            enter_text_to_cell(xGrid, "A1", "merged")
            xGrid.executeAction("SELECT", mkPropertyValues({"RANGE": "A1:B2"}))
            self.xUITest.executeCommand(".uno:HomeMergeCenter")
            xCell = document.Sheets.getByIndex(0).getCellRangeByName("A1")
            self.assertTrue(xCell.IsMerged)
            self.assertEqual("CENTER", xCell.HoriJustify.value)

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

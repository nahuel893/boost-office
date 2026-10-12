# -*- tab-width: 4; indent-tabs-mode: nil; py-indent-offset: 4 -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
from uitest.framework import UITestCase
from uitest.uihelper.common import get_state_as_dict

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

# vim: set shiftwidth=4 softtabstop=4 expandtab:

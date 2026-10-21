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
from pathlib import Path

from uitest.framework import UITestCase
from uitest.uihelper.common import get_state_as_dict
from libreoffice.uno.propertyvalue import mkPropertyValues
from com.sun.star.accessibility.AccessibleRole import PAGE_TAB_LIST, DOCUMENT_TEXT, PARAGRAPH
from com.sun.star.beans import PropertyValue
from com.sun.star.frame import XStatusListener

OFFICE_UI = "notebookbar_office.ui"

# The pages of today's generated Writer office .ui (sw/uiconfig/swriter/ui/notebookbar_office.ui),
# in tab order: (tab label without its mnemonic, page id). Tasks that add pages update this list;
# W8a reaches Word's order. Table .. Form are the contextual tabs: they only show with their object.
TABS = [("File", "File Tab"), ("Home", "Home Tab"), ("Insert", "Insert Tab"), ("Layout", "Layout Tab"),
        ("References", "References Tab"), ("Review", "Review Tab"), ("View", "View Tab"),
        ("Table", "Table Tab"), ("Image", "Image Tab"), ("Draw", "Draw Tab"), ("Object", "Object Tab"),
        ("Media", "Media Tab"), ("Print", "Print Tab"), ("Form", "Form Tab"),
        ("Extension", "Extension Tab"), ("Tools", "Tools Tab")]
CONTEXTUAL = {"Table", "Image", "Draw", "Object", "Media", "Print", "Form"}


def placeholder_entries(src):
    """The placeholders of Writer's registry (product/tests/placeholders_writer.json).

    An entry flagged "implemented" stays in the file but is no placeholder any more.
    """
    entries = json.loads((src / "product" / "tests" / "placeholders_writer.json").read_text(encoding="utf-8"))
    return [entry for entry in entries if not entry.get("implemented")]


def placeholder_count(src):
    """How many command URLs the placeholders answer to."""
    return sum(len(entry.get("variants", [None])) for entry in placeholder_entries(src))


def placeholder_urls(src):
    """Every command URL of the placeholders: the base command, or one per variant."""
    urls = []
    for entry in placeholder_entries(src):
        urls += [entry["command"] + "?" + v for v in entry.get("variants", [])] or [entry["command"]]
    return urls


class StateListener(unohelper.Base, XStatusListener):
    def __init__(self):
        self.enabled = None

    def statusChanged(self, aEvent):
        self.enabled = aEvent.IsEnabled

    def disposing(self, aEvent):
        pass


class NotebookbarOffice(UITestCase):

    def switch_to(self, ui_file):
        self.xUITest.executeCommand(".uno:ToolbarMode?Mode:string=" + ui_file)

    def wait_for(self, condition, message, timeout=5):
        deadline = time.time() + timeout
        while not condition() and time.time() < deadline:
            time.sleep(0.05)
        self.assertTrue(condition(), message)

    def toolbar_mode(self, path):
        provider = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.configuration.ConfigurationProvider", self.xContext)
        access = provider.createInstanceWithArguments(
            "com.sun.star.configuration.ConfigurationAccess",
            (PropertyValue(Name="nodepath", Value="/org.openoffice.Office.UI.ToolbarMode"),))
        return access.getByHierarchicalName(path)

    def tab_labels(self, document, count):
        """The page tab names of the ribbon's tab control, read from the accessibility tree.

        The tab texts are not in the UITest state of a tab control. The window's peer hands out its
        accessible through the "XAccessible" property (toolkit/source/awt/vclxwindow.cxx). The ribbon
        is a child of the window's frame, so the search starts at the top of the tree; the document
        text is skipped.
        """
        xWindow = document.CurrentController.Frame.ContainerWindow
        xAcc = xWindow.getProperty("XAccessible").getAccessibleContext()
        while xAcc.getAccessibleParent() is not None:
            xAcc = xAcc.getAccessibleParent().getAccessibleContext()
        queue = [xAcc]
        while queue:
            xAcc = queue.pop(0)
            role = xAcc.getAccessibleRole()
            if role == PAGE_TAB_LIST and xAcc.getAccessibleChildCount() == count:
                return [xAcc.getAccessibleChild(i).getAccessibleContext().getAccessibleName()
                        for i in range(count)]
            if role not in (DOCUMENT_TEXT, PARAGRAPH):
                queue += [xAcc.getAccessibleChild(i).getAccessibleContext()
                          for i in range(xAcc.getAccessibleChildCount())]
        self.fail("no tab list with %d tabs in the accessibility tree" % count)

    def test_tabbed_office_loads(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            self.switch_to(OFFICE_UI)
            try:
                # sfx2 shows the notebookbar only for a mode of the app, and loads the file in
                # ActiveWriter (sfx2/source/notebookbar/SfxNotebookBar.cxx)
                self.assertEqual(OFFICE_UI, self.toolbar_mode("Applications/Writer/Active"))
                self.assertEqual(OFFICE_UI, self.toolbar_mode("ActiveWriter"))
                xWriterDoc = self.xUITest.getTopFocusWindow()
                xHome = xWriterDoc.getChild("Home Tab")
                self.assertEqual("true", get_state_as_dict(xHome)["Visible"])
            finally:
                self.switch_to("Default")

    def test_tab_order(self):
        with self.ui_test.create_doc_in_start_center("writer") as document:
            self.switch_to(OFFICE_UI)
            try:
                xWriterDoc = self.xUITest.getTopFocusWindow()
                xTabs = xWriterDoc.getChild("ContextContainer")
                self.assertEqual(str(len(TABS)), get_state_as_dict(xTabs)["PageCount"])
                self.assertEqual([label for label, _ in TABS], self.tab_labels(document, len(TABS)))
                for pos, (label, page) in enumerate(TABS):
                    if label in CONTEXTUAL:
                        continue
                    xTabs.executeAction("SELECT", mkPropertyValues({"POS": str(pos)}))
                    self.wait_for(lambda: get_state_as_dict(xWriterDoc.getChild(page))["ReallyVisible"] == "true",
                                  "tab %d does not show %s" % (pos, page))
                    self.assertEqual(str(pos), get_state_as_dict(xTabs)["CurrPagePos"])
            finally:
                self.switch_to("Default")

    def dispatch_enabled(self, name, timeout=5):
        """IsEnabled of .uno:<name> as the frame reports it to a status listener."""
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
            self.wait_for(lambda: listener.enabled is not None, "no state reported for " + name, timeout)
        finally:
            xDispatch.removeStatusListener(listener, aURL)
        return listener.enabled

    def test_placeholder_slots_disabled(self):
        # every URL of product/tests/placeholders_writer.json (W1: 48 on 24 slots) is a known
        # command of a Writer text document, always disabled, and dispatching it does nothing
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src)
        self.assertEqual(placeholder_count(src), len(names))  # one per plain slot, one per family variant
        with self.ui_test.create_doc_in_start_center("writer") as document:
            document.Text.String = "keep"
            document.setModified(False)
            self.assertTrue(self.dispatch_enabled("InsertPagebreak"))  # control: a real, enabled slot
            for name in names:
                self.assertFalse(self.dispatch_enabled(name), name)
                self.xUITest.executeCommand(".uno:" + name)  # must do nothing, not even a dialog
            self.assertEqual("keep", document.Text.String)
            self.assertEqual(1, document.CurrentController.PageCount)
            self.assertFalse(document.isModified())

# vim: set shiftwidth=4 softtabstop=4 expandtab:

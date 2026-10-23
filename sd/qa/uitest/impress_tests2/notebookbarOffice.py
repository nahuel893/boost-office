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
from uitest.uihelper.common import get_state_as_dict
from libreoffice.uno.propertyvalue import mkPropertyValues
from com.sun.star.accessibility.AccessibleRole import PAGE_TAB_LIST, DOCUMENT_PRESENTATION, DOCUMENT_TEXT, PARAGRAPH
from com.sun.star.beans import PropertyValue
from com.sun.star.frame import XStatusListener

OFFICE_UI = "notebookbar_office.ui"

# The pages of today's generated Impress office .ui (sd/uiconfig/simpress/ui/notebookbar_office.ui),
# in tab order: (tab label without its mnemonic, page id). Tasks that change the tabs update this list;
# I8a reaches PowerPoint's order. Table .. 3D are the contextual tabs: they only show with their object
# or view.
TABS = [("File", "File"), ("Home", "Home Tab"), ("Insert", "Insert"), ("Layout", "Layout"), ("Design", "Design"),
        ("Slide Show", "SlideShow"), ("Review", "Review"), ("View", "View"),
        ("Table", "Table"), ("Image", "Image"), ("Draw", "Draw"), ("Object", "Object"), ("Media", "Media"),
        ("Form", "Form"), ("Master", "Master"), ("Outline", "Outline"), ("3D", "3D"),
        ("Extension", "Extension"), ("Tools", "Tools")]
CONTEXTUAL = {"Table", "Image", "Draw", "Object", "Media", "Form", "Master", "Outline", "3D"}


def placeholder_entries(src):
    """The placeholders of Impress's registry (product/tests/placeholders_impress.json).

    An entry flagged "implemented" stays in the file but is no placeholder any more.
    """
    entries = json.loads((src / "product" / "tests" / "placeholders_impress.json").read_text(encoding="utf-8"))
    return [entry for entry in entries if not entry.get("implemented")]


def placeholder_count(src):
    """How many command URLs the placeholders answer to."""
    return sum(len(entry.get("variants", [None])) for entry in placeholder_entries(src))


def placeholder_urls(src, only=None):
    """Every command URL of the placeholders: the base command, or one per variant."""
    urls = []
    for entry in placeholder_entries(src):
        if only is None or only(entry):
            urls += [entry["command"] + "?" + v for v in entry.get("variants", [])] or [entry["command"]]
    return urls


class StateListener(unohelper.Base, XStatusListener):
    def __init__(self):
        self.enabled = None
        self.state = None

    def statusChanged(self, aEvent):
        self.enabled = aEvent.IsEnabled
        self.state = aEvent.State

    def disposing(self, aEvent):
        pass


class NotebookbarOffice(UITestCase):

    @contextmanager
    def impress_doc(self):
        """A new Impress document, ready to use: every Impress ribbon UITest opens its document here.

        The UITest profile is fresh, so the template dialog opens first; close it, as tdf130440.py does.
        """
        with self.ui_test.create_doc_in_start_center("impress") as document:
            xTemplateDlg = self.xUITest.getTopFocusWindow()
            self.ui_test.close_dialog_through_button(xTemplateDlg.getChild("close"))
            yield document

    def switch_to(self, ui_file):
        self.xUITest.executeCommand(".uno:ToolbarMode?Mode:string=" + ui_file)

    def wait_for(self, condition, message, timeout=5):
        deadline = time.time() + timeout
        while not condition() and time.time() < deadline:
            time.sleep(0.05)
        self.assertTrue(condition(), message)

    def settle(self, read, timeout=5):
        """Process events until read() gives the same value twice in a row; return that value.

        Fails when the value is still changing after `timeout` seconds."""
        xToolkit = self.xContext.ServiceManager.createInstance("com.sun.star.awt.Toolkit")
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            xToolkit.processEventsToIdle()
            value = read()
            if value == last:
                return value
            last = value
            time.sleep(0.1)
        self.fail("the value did not settle in %s s, the last read was %r" % (timeout, last))

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
        is a child of the window's frame, so the search starts at the top of the tree; the slides and
        their text are skipped.
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
            if role not in (DOCUMENT_PRESENTATION, DOCUMENT_TEXT, PARAGRAPH):
                queue += [xAcc.getAccessibleChild(i).getAccessibleContext()
                          for i in range(xAcc.getAccessibleChildCount())]
        self.fail("no tab list with %d tabs in the accessibility tree" % count)

    def dispatch_enabled(self, name, timeout=5):
        """IsEnabled of .uno:<name> as the frame reports it to a status listener."""
        return self.dispatch_status(name, timeout).enabled

    def dispatch_status(self, name, timeout=5):
        """The StateListener of .uno:<name> after the frame reported its status (IsEnabled and State)."""
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
        return listener

    def assert_disabled_and_inert(self, names):
        """Each command is known, reported disabled, and dispatching it does nothing, not even a dialog."""
        self.assertTrue(self.dispatch_enabled("LeftPaneImpress"))  # control: a real ViewShellBase slot
        for name in names:
            self.assertFalse(self.dispatch_enabled(name), name)
            self.xUITest.executeCommand(".uno:" + name)

    def test_placeholder_slots_disabled(self):
        # every URL of product/tests/placeholders_impress.json (I1: 39 on 24 slots) is a known command of
        # an Impress document and disabled in every view: ViewShellBase, under every view, disables them
        # (design decision 23). Checked here in Normal and in Slide Sorter view.
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src)
        self.assertEqual(placeholder_count(src), len(names))  # one per plain slot, one per family variant
        with self.impress_doc() as document:
            slide = document.DrawPages[0]
            self.assertGreater(slide.Count, 0)
            slide.getByIndex(0).String = "keep"
            shapes = slide.Count
            document.setModified(False)

            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assert_disabled_and_inert(names)

            self.xUITest.executeCommand(".uno:DiaMode")
            self.wait_for(lambda: self.dispatch_status("DiaMode").state is True, "no Slide Sorter view")
            self.assertTrue(self.settle(lambda: self.dispatch_status("DiaMode").state))
            self.assert_disabled_and_inert(names)

            self.assertEqual(1, document.DrawPages.Count)
            self.assertEqual(shapes, slide.Count)
            self.assertEqual("keep", slide.getByIndex(0).String)
            self.assertFalse(document.isModified())

    def test_tabbed_office_loads(self):
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                # sfx2 shows the notebookbar only for a mode of the app, and loads the file in
                # ActiveImpress (sfx2/source/notebookbar/SfxNotebookBar.cxx)
                self.assertEqual(OFFICE_UI, self.toolbar_mode("Applications/Impress/Active"))
                self.assertEqual(OFFICE_UI, self.settle(lambda: self.toolbar_mode("ActiveImpress")))
                xImpressDoc = self.xUITest.getTopFocusWindow()
                xHome = xImpressDoc.getChild("Home Tab")
                self.assertEqual("true", self.settle(lambda: get_state_as_dict(xHome)["Visible"]))
            finally:
                self.switch_to("Default")

    def test_tab_order(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                xTabs = xImpressDoc.getChild("ContextContainer")
                self.assertEqual(str(len(TABS)), self.settle(lambda: get_state_as_dict(xTabs)["PageCount"]))
                self.assertEqual([label for label, _ in TABS], self.tab_labels(document, len(TABS)))
                for pos, (label, page) in enumerate(TABS):
                    if label in CONTEXTUAL:
                        continue
                    xTabs.executeAction("SELECT", mkPropertyValues({"POS": str(pos)}))
                    self.wait_for(lambda: get_state_as_dict(xImpressDoc.getChild(page))["ReallyVisible"] == "true",
                                  "tab %d does not show %s" % (pos, page))
                    self.assertEqual(str(pos), self.settle(lambda: get_state_as_dict(xTabs)["CurrPagePos"]))
            finally:
                self.switch_to("Default")

# vim: set shiftwidth=4 softtabstop=4 expandtab:

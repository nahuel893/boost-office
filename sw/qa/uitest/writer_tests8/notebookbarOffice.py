# -*- tab-width: 4; indent-tabs-mode: nil; py-indent-offset: 4 -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import base64
import json
import os
import tempfile
import time
import uno
import unohelper
from pathlib import Path

from uitest.framework import UITestCase
from uitest.uihelper.common import get_state_as_dict
from libreoffice.uno.propertyvalue import mkPropertyValues
from com.sun.star.accessibility.AccessibleRole import PAGE_TAB_LIST, DOCUMENT_TEXT, PARAGRAPH
from com.sun.star.awt.PosSize import SIZE
from com.sun.star.beans import PropertyValue
from com.sun.star.frame import XStatusListener

OFFICE_UI = "notebookbar_office.ui"
WRITER_MODULE = "com.sun.star.text.TextDocument"
# a 1x1 PNG, the picture of the image context
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==")
HOME_SLOTS = (0, 1)  # SID offsets of the Home placeholders: Text Effects family, Select Similar
INSERT_SLOTS = (2, 3, 4, 5)  # Blank Page, 3D Models, SmartArt, Screenshot
DESIGN_SLOTS = (6, 7)  # the Themes/Fonts/Effects family and the Style Set/Paragraph Spacing/Set as Default family

# The pages of today's generated Writer office .ui (sw/uiconfig/swriter/ui/notebookbar_office.ui),
# in tab order: (tab label without its mnemonic, page id). Tasks that add pages update this list;
# W8a reaches Word's order. Table .. Form are the contextual tabs: they only show with their object.
TABS = [("File", "File Tab"), ("Home", "Home Tab"), ("Insert", "Insert Tab"), ("Design", "Design Tab"),
        ("Layout", "Layout Tab"), ("References", "References Tab"), ("Review", "Review Tab"), ("View", "View Tab"),
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

    def test_home_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "writer_home.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("writer"):
            self.switch_to(OFFICE_UI)
            try:
                xWriterDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(7, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xWriterDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xWriterDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def visible_tabs(self, document):
        """The names of the ribbon tabs that have a tab on screen.

        The tab list holds every page; a page that the context hides has empty bounds
        (TabControl::SetPageVisible), which the accessible page reports as a zero width.
        """
        xWindow = document.CurrentController.Frame.ContainerWindow
        xAcc = xWindow.getProperty("XAccessible").getAccessibleContext()
        while xAcc.getAccessibleParent() is not None:
            xAcc = xAcc.getAccessibleParent().getAccessibleContext()
        queue = [xAcc]
        while queue:
            xAcc = queue.pop(0)
            role = xAcc.getAccessibleRole()
            if role == PAGE_TAB_LIST and xAcc.getAccessibleChildCount() == len(TABS):
                pages = [xAcc.getAccessibleChild(i).getAccessibleContext() for i in range(len(TABS))]
                return [page.getAccessibleName() for page in pages if page.getBounds().Width > 0]
            if role not in (DOCUMENT_TEXT, PARAGRAPH):
                queue += [xAcc.getAccessibleChild(i).getAccessibleContext()
                          for i in range(xAcc.getAccessibleChildCount())]
        self.fail("no tab list with %d tabs in the accessibility tree" % len(TABS))

    def check_tab_is_shown(self, document, tab, contextual):
        """`tab` has a tab on screen; `contextual` (a tab of the object, or None) proves the context."""
        if contextual:
            self.wait_for(lambda: contextual in self.visible_tabs(document), contextual + " tab is not shown", 10)
        else:
            self.wait_for(lambda: tab in self.visible_tabs(document), tab + " tab is not shown", 10)
            self.assertFalse(CONTEXTUAL & set(self.visible_tabs(document)))
        self.assertIn(tab, self.visible_tabs(document))

    def check_home_tab_is_shown(self, document, contextual):
        self.check_tab_is_shown(document, "Home", contextual)

    def check_tab_in_every_context(self, document, tab):
        """The tab shows in the text, table, image and print-preview contexts of a Writer document."""
        self.check_tab_is_shown(document, tab, None)
        # table: the cursor in a cell
        xTable = document.createInstance("com.sun.star.text.TextTable")
        xTable.initialize(2, 2)
        document.Text.insertTextContent(document.Text.End, xTable, False)
        document.CurrentController.ViewCursor.gotoRange(xTable.getCellByName("A1").Start, False)
        self.check_tab_is_shown(document, tab, "Table")
        # image: a selected picture
        with tempfile.TemporaryDirectory() as tmp:
            picture = Path(tmp) / "pixel.png"
            picture.write_bytes(PNG)
            xGraphic = document.createInstance("com.sun.star.text.TextGraphicObject")
            xGraphic.GraphicURL = picture.as_uri()
            xGraphic.AnchorType = uno.Enum("com.sun.star.text.TextContentAnchorType", "AS_CHARACTER")
            document.CurrentController.ViewCursor.gotoRange(document.Text.End, False)
            document.Text.insertTextContent(document.CurrentController.ViewCursor, xGraphic, False)
            document.CurrentController.select(xGraphic)
            self.check_tab_is_shown(document, tab, "Image")
        # print preview
        document.CurrentController.select(document.Text.Start)
        self.xUITest.executeCommand(".uno:PrintPreview")
        try:
            self.check_tab_is_shown(document, tab, "Print")
        finally:
            self.xUITest.executeCommand(".uno:ClosePreview")
        self.check_tab_is_shown(document, tab, None)

    def test_home_tab_is_visible_in_the_text_table_image_and_print_preview_contexts(self):
        with self.ui_test.create_doc_in_start_center("writer") as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_home_tab_is_shown(document, None)
                # table: the cursor in a cell
                xTable = document.createInstance("com.sun.star.text.TextTable")
                xTable.initialize(2, 2)
                document.Text.insertTextContent(document.Text.End, xTable, False)
                document.CurrentController.ViewCursor.gotoRange(xTable.getCellByName("A1").Start, False)
                self.check_home_tab_is_shown(document, "Table")
                # image: a selected picture
                with tempfile.TemporaryDirectory() as tmp:
                    picture = Path(tmp) / "pixel.png"
                    picture.write_bytes(PNG)
                    xGraphic = document.createInstance("com.sun.star.text.TextGraphicObject")
                    xGraphic.GraphicURL = picture.as_uri()
                    xGraphic.AnchorType = uno.Enum("com.sun.star.text.TextContentAnchorType", "AS_CHARACTER")
                    document.CurrentController.ViewCursor.gotoRange(document.Text.End, False)
                    document.Text.insertTextContent(document.CurrentController.ViewCursor, xGraphic, False)
                    document.CurrentController.select(xGraphic)
                    self.check_home_tab_is_shown(document, "Image")
                # print preview
                document.CurrentController.select(document.Text.Start)
                self.xUITest.executeCommand(".uno:PrintPreview")
                try:
                    self.check_home_tab_is_shown(document, "Print")
                finally:
                    self.xUITest.executeCommand(".uno:ClosePreview")
                self.check_home_tab_is_shown(document, None)
            finally:
                self.switch_to("Default")

    def test_home_placeholders_are_disabled_and_inert(self):
        # 2 slots: the Text Effects family (5 variants in its menu) and Select Text with Similar Formatting
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in HOME_SLOTS)
        self.assertEqual(6, len(names))
        with self.ui_test.create_doc_in_start_center("writer") as document:
            document.Text.String = "keep"
            document.setModified(False)
            self.assertTrue(self.dispatch_enabled("InsertPagebreak"))  # control: a real, enabled slot
            for name in names:
                self.assertFalse(self.dispatch_enabled(name), name)
                self.xUITest.executeCommand(".uno:" + name)  # must do nothing, not even a dialog
            self.assertEqual("keep", document.Text.String)
            self.assertFalse(document.isModified())

    def menu_controller(self, command, resource, with_controller=False):
        """The menu controller of the ribbon dropdown `command` and the awt popup menu it built.

        `resource` is the popup file the ResourceMenuController reads (its "Value"); None for a menu
        controller of its own (Header, Footer)."""
        xDesktop = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.xContext)
        xFactory = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.PopupMenuControllerFactory", self.xContext)
        self.assertTrue(xFactory.hasController(command, WRITER_MODULE), command)
        args = {"Frame": xDesktop.getCurrentFrame(), "CommandURL": command, "ModuleIdentifier": WRITER_MODULE}
        if resource:
            args["Value"] = resource
        xController = xFactory.createInstanceWithArgumentsAndContext(
            command, mkPropertyValues(args), self.xContext)
        self.assertIsNotNone(xController, command)
        xPopup = self.xContext.ServiceManager.createInstanceWithContext("com.sun.star.awt.PopupMenu", self.xContext)
        xController.setPopupMenu(xPopup)
        xController.updatePopupMenu()
        return (xPopup, xController) if with_controller else xPopup

    def popup_commands(self, xPopup):
        commands = []
        for pos in range(xPopup.getItemCount()):
            command = xPopup.getCommand(xPopup.getItemId(pos))
            if command:  # separators have none
                commands.append(command)
        return commands

    def command_label(self, url):
        """The label the framework resolves for a command URL (what a menu item shows)."""
        xDescriptions = self.xContext.getValueByName("/singletons/com.sun.star.frame.theUICommandDescription")
        props = {p.Name: p.Value for p in xDescriptions.getByName(WRITER_MODULE).getByName(url)}
        return props["Label"].replace("~", "")

    def test_home_dropdown_popups_list_their_items_through_the_real_controllers(self):
        effect = ".uno:HomeTextEffect?Effect:string="
        with self.ui_test.create_doc_in_start_center("writer"):
            expected = {
                ("HomeChangeCaseMenu", "home_changecase"): [
                    ".uno:ChangeCaseToSentenceCase", ".uno:ChangeCaseToLower", ".uno:ChangeCaseToUpper",
                    ".uno:ChangeCaseToTitleCase", ".uno:ChangeCaseToToggleCase"],
                ("HomeTextEffectsMenu", "home_texteffects"): [
                    ".uno:OutlineFont", ".uno:Shadowed"] + [effect + v for v in (
                        "reflection", "glow", "numberstyles", "ligatures", "stylisticsets")],
                ("HomeFindMenu", "home_find"): ["vnd.sun.star.findbar:FocusToFindbar", ".uno:SearchDialog",
                                                ".uno:GotoPage"],
                ("HomeSelectMenu", "home_select"): [".uno:SelectAll", ".uno:SelectObject",
                                                    ".uno:HomeSelectSimilar", ".uno:Navigator"]}
            for (command, resource), items in expected.items():
                xPopup = self.menu_controller(".uno:" + command, resource)
                self.assertEqual(items, self.popup_commands(xPopup), command)

    def test_home_find_menu_starts_with_the_find_toolbar(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            xPopup = self.menu_controller(".uno:HomeFindMenu", "home_find")
            self.assertEqual("vnd.sun.star.findbar:FocusToFindbar", xPopup.getCommand(xPopup.getItemId(0)))

    def test_home_menu_placeholders_resolve_their_labels_and_are_disabled(self):
        effect = "HomeTextEffect?Effect:string="
        with self.ui_test.create_doc_in_start_center("writer"):
            for value, label in (("reflection", "Reflection"), ("glow", "Glow"), ("numberstyles", "Number Styles"),
                                 ("ligatures", "Ligatures"), ("stylisticsets", "Stylistic Sets")):
                self.assertEqual(label, self.command_label(".uno:" + effect + value))
                self.assertFalse(self.dispatch_enabled(effect + value), value)
            self.assertEqual("Select Text with Similar Formatting", self.command_label(".uno:HomeSelectSimilar"))
            self.assertFalse(self.dispatch_enabled("HomeSelectSimilar"))
            for command, label in (("HomeChangeCaseMenu", "Change Case"),
                                   ("HomeTextEffectsMenu", "Text Effects and Typography"),
                                   ("HomeFindMenu", "Find"), ("HomeSelectMenu", "Select")):
                self.assertEqual(label, self.command_label(".uno:" + command))

    def width(self, xParent, wid):
        return int(get_state_as_dict(xParent.getChild(wid))["Size"].split("x")[0])

    def settle(self, read, timeout=5):
        """Process events until read() gives the same value twice in a row; return that value."""
        xToolkit = self.xContext.ServiceManager.createInstance("com.sun.star.awt.Toolkit")
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            xToolkit.processEventsToIdle()
            value = read()
            if value == last:
                break
            last = value
            time.sleep(0.1)
        return last

    def test_home_styles_gallery_takes_the_free_width_and_shrinks_first(self):
        # Word: the Styles gallery is the widest group on Home and the one that flexes. It gets the
        # width Home leaves free, and gives it back first when the window narrows: every group stays.
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "writer_home.json").read_text(encoding="utf-8"))
        sections = ["ob" + layout["id_prefix"] + s["name"] for s in layout["sections"]]
        with self.ui_test.create_doc_in_start_center("writer") as document:
            self.switch_to(OFFICE_UI)
            xWindow = document.CurrentController.Frame.ContainerWindow
            old = xWindow.getPosSize()
            try:
                xWriterDoc = self.xUITest.getTopFocusWindow()

                def state():
                    """(Home page width, gallery width, the Home sections that collapsed)"""
                    hidden = [s for s in sections
                              if get_state_as_dict(xWriterDoc.getChild(s))["Visible"] != "true"]
                    return (self.width(xWriterDoc, "Home Tab"), self.width(xWriterDoc, "bxHomeStylesPreview"),
                            hidden)

                # The UITest window is about 800 px wide: Home collapses four groups there, the
                # gallery among them, so the window is set to the widths the design targets.
                got = {}
                for size in (1920, 1600, 1366):
                    xWindow.setPosSize(0, 0, size, 900, SIZE)
                    got[size] = self.settle(state)
                for size, (page, gallery, hidden) in got.items():
                    self.assertEqual([], hidden, "%d: Home collapses (page %d, gallery %d px)" % (size, page, gallery))
                # at 1920 px, room for at least 5 style previews (100 px each, StylesPreviewWindow.cxx)
                self.assertGreaterEqual(got[1920][1], 5 * 100, got)
                # the gallery gives back every pixel the page loses, before any group collapses
                for size in (1600, 1366):
                    self.assertEqual(got[1920][0] - got[size][0], got[1920][1] - got[size][1], got)
            finally:
                xWindow.setPosSize(old.X, old.Y, old.Width, old.Height, SIZE)
                self.switch_to("Default")

    def test_home_dropdown_items_that_are_real_commands_are_enabled(self):
        with self.ui_test.create_doc_in_start_center("writer") as document:
            document.Text.String = "Hello world"
            document.CurrentController.select(document.Text)
            for name in ("ChangeCaseToLower", "ChangeCaseToUpper", "ChangeCaseToTitleCase", "OutlineFont",
                         "Shadowed", "SearchDialog", "GotoPage", "SelectAll", "Navigator"):
                self.assertTrue(self.dispatch_enabled(name), name)

    def test_insert_sections_and_toolboxes(self):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / "writer_insert.json").read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("writer"):
            self.switch_to(OFFICE_UI)
            try:
                xWriterDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(8, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xWriterDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xWriterDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_insert_tab_is_visible_in_the_text_table_image_and_print_preview_contexts(self):
        with self.ui_test.create_doc_in_start_center("writer") as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Insert")
            finally:
                self.switch_to("Default")

    def test_insert_placeholders_are_disabled_and_inert(self):
        # 4 slots: Blank Page, 3D Models, SmartArt and Screenshot
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in INSERT_SLOTS)
        self.assertEqual(4, len(names))
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

    def test_insert_dropdown_popups_list_their_items_through_the_real_controllers(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            expected = {
                ("InsertShapesMenu", "insert_shapes"): [
                    ".uno:ShapesLineMenu", ".uno:BasicShapes", ".uno:ArrowShapes", ".uno:FlowChartShapes",
                    ".uno:StarShapes", ".uno:CalloutShapes", ".uno:SymbolShapes", ".uno:ConnectorToolbox"],
                ("InsertPageNumberMenu", "insert_pagenumber"): [
                    ".uno:PageNumberWizard", ".uno:InsertPageNumberField", ".uno:InsertPageCountField"],
                ("InsertTextBoxMenu", "insert_textbox"): [".uno:DrawText", ".uno:VerticalText"],
                ("InsertQuickPartsMenu", "insert_quickparts"): [
                    ".uno:EditGlossary", ".uno:InsertTitleField", ".uno:InsertTopicField",
                    ".uno:InsertAuthorField", ".uno:InsertField"],
                ("InsertObjectMenu", "insert_object"): [".uno:InsertObject", ".uno:InsertDoc"]}
            for (command, resource), items in expected.items():
                xPopup = self.menu_controller(".uno:" + command, resource)
                self.assertEqual(items, self.popup_commands(xPopup), command)

    def test_insert_quick_parts_menu_groups_its_items_with_separators(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            xPopup = self.menu_controller(".uno:InsertQuickPartsMenu", "insert_quickparts")
            shape = [bool(xPopup.getCommand(xPopup.getItemId(pos))) for pos in range(xPopup.getItemCount())]
            self.assertEqual([True, False, True, True, True, False, True], shape)

    def test_insert_shapes_submenus_open(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            xPopup = self.menu_controller(".uno:InsertShapesMenu", "insert_shapes")
            line = next(xPopup.getItemId(pos) for pos in range(xPopup.getItemCount())
                        if xPopup.getCommand(xPopup.getItemId(pos)) == ".uno:ShapesLineMenu")
            xSub = xPopup.getPopupMenu(line)
            self.assertIsNotNone(xSub, "Line has no submenu")
            self.assertEqual([".uno:Line", ".uno:Freeline_Unfilled", ".uno:Freeline", ".uno:Bezier_Unfilled",
                              ".uno:BezierFill", ".uno:Polygon_Unfilled", ".uno:Polygon_Diagonal_Unfilled",
                              ".uno:Polygon_Diagonal"], self.popup_commands(xSub))
            # the other seven entries are commands whose own controllers open a shape gallery
            for url in (".uno:BasicShapes", ".uno:ArrowShapes", ".uno:FlowChartShapes", ".uno:StarShapes",
                        ".uno:CalloutShapes", ".uno:SymbolShapes", ".uno:ConnectorToolbox"):
                self.assertTrue(self.dispatch_enabled(url[len(".uno:"):]), url)

    def test_insert_header_and_footer_dropdowns_list_the_documents_page_styles(self):
        with self.ui_test.create_doc_in_start_center("writer") as document:
            xStyles = document.StyleFamilies.getByName("PageStyles")
            extra = document.createInstance("com.sun.star.style.PageStyle")
            xStyles.insertByName("Boost Insert Test", extra)
            names = [n for n in xStyles.ElementNames if xStyles.getByName(n).IsPhysical]
            self.assertIn("Boost Insert Test", names)
            self.assertGreaterEqual(len(names), 2)
            for command, resource, uno_command, is_on in (
                    (".uno:InsertHeaderMenu", "insert_header", ".uno:InsertPageHeader", "HeaderIsOn"),
                    (".uno:InsertFooterMenu", "insert_footer", ".uno:InsertPageFooter", "FooterIsOn")):
                # a plain dropdown: the toolbar node has no "Value", so the button body opens the menu
                xPopup, xController = self.menu_controller(command, resource, True)
                self.assertEqual([uno_command], self.popup_commands(xPopup), command)
                # opening the menu: the controller builds the MenuBarManager, which makes the (still empty)
                # submenu of the item that has a menu controller of its own
                event = uno.createUnoStruct("com.sun.star.awt.MenuEvent")
                event.Source = xPopup
                xController.itemActivated(event)
                xSub = xPopup.getPopupMenu(xPopup.getItemId(0))
                self.assertIsNotNone(xSub, command)
                self.assertEqual([], self.popup_commands(xSub), command)
                # activating the submenu is what makes MenuBarManager create the registered menu controller of
                # the stock command and fill the submenu; do the same here, on that very submenu
                xDesktop = self.xContext.ServiceManager.createInstanceWithContext(
                    "com.sun.star.frame.Desktop", self.xContext)
                xFactory = self.xContext.ServiceManager.createInstanceWithContext(
                    "com.sun.star.frame.PopupMenuControllerFactory", self.xContext)
                self.assertTrue(xFactory.hasController(uno_command, WRITER_MODULE), uno_command)
                xSubController = xFactory.createInstanceWithArgumentsAndContext(
                    uno_command, mkPropertyValues({"Frame": xDesktop.getCurrentFrame(), "CommandURL": uno_command,
                                                   "ModuleIdentifier": WRITER_MODULE}), self.xContext)
                xSubController.setPopupMenu(xSub)
                xSubController.updatePopupMenu()
                commands = self.popup_commands(xSub)
                for name in names:
                    style = xStyles.getByName(name)
                    toggle = "false" if getattr(style, is_on) else "true"
                    self.assertIn("%s?PageStyle:string=%s&On:bool=%s" % (uno_command, style.DisplayName, toggle),
                                  commands, command + " " + name)
                texts = [xSub.getItemText(xSub.getItemId(pos)) for pos in range(xSub.getItemCount())]
                self.assertIn("Boost Insert Test", texts, command)

    def test_insert_dropdown_and_placeholder_labels_resolve(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            for command, label in (("InsertShapesMenu", "Shapes"), ("InsertHeaderMenu", "Header"),
                                   ("InsertFooterMenu", "Footer"), ("InsertPageNumberMenu", "Page Number"),
                                   ("InsertTextBoxMenu", "Text Box"), ("InsertQuickPartsMenu", "Quick Parts"),
                                   ("InsertObjectMenu", "Object"), ("InsertBlankPage", "Blank Page"),
                                   ("Insert3DModels", "3D Models"), ("InsertSmartArt", "SmartArt"),
                                   ("InsertScreenshot", "Screenshot")):
                self.assertEqual(label, self.command_label(".uno:" + command), command)

    def test_insert_commands_that_are_real_are_enabled(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            for name in ("TitlePageDialog", "InsertPagebreak", "InsertGraphic", "InsertBookmark",
                         "InsertReferenceField", "InsertAnnotation", "DrawText", "VerticalText", "EditGlossary",
                         "InsertField", "InsertDateField", "InsertObject", "InsertDoc", "PageNumberWizard",
                         "InsertPageNumberField", "InsertPageCountField", "HyperlinkDialog", "InsertTable"):
                self.assertTrue(self.dispatch_enabled(name), name)

    def check_sections_and_toolboxes(self, layout_file, section_count):
        src = Path(os.environ["TDOC"]).parents[3]
        layout = json.loads((src / "product" / "ui" / layout_file).read_text(encoding="utf-8"))
        prefix = layout["id_prefix"]
        with self.ui_test.create_doc_in_start_center("writer"):
            self.switch_to(OFFICE_UI)
            try:
                xWriterDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(section_count, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xWriterDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xWriterDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_design_sections_and_toolboxes(self):
        self.check_sections_and_toolboxes("writer_design.json", 2)

    def test_design_tab_is_visible_in_the_text_table_image_and_print_preview_contexts(self):
        with self.ui_test.create_doc_in_start_center("writer") as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Design")
            finally:
                self.switch_to("Default")

    def test_design_placeholders_are_disabled_and_inert(self):
        # 2 slots: the Themes/Fonts/Effects family and the Style Set/Paragraph Spacing/Set as Default family
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in DESIGN_SLOTS)
        self.assertEqual(6, len(names))
        with self.ui_test.create_doc_in_start_center("writer") as document:
            document.Text.String = "keep"
            document.setModified(False)
            self.assertTrue(self.dispatch_enabled("InsertPagebreak"))  # control: a real, enabled slot
            for name in names:
                self.assertFalse(self.dispatch_enabled(name), name)
                self.xUITest.executeCommand(".uno:" + name)  # must do nothing, not even a dialog
            self.assertEqual("keep", document.Text.String)
            self.assertFalse(document.isModified())

    def test_design_commands_that_are_real_are_enabled_and_the_labels_resolve(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            for name in ("ThemeDialog", "Watermark", "PageAreaDialog", "PageDialog"):
                self.assertTrue(self.dispatch_enabled(name), name)
            for url, label in ((".uno:PageAreaDialog", "Page Area..."),
                               (".uno:PageLayoutThemePart?Part:string=themes", "Themes"),
                               (".uno:PageLayoutThemePart?Part:string=fonts", "Fonts"),
                               (".uno:PageLayoutThemePart?Part:string=effects", "Effects"),
                               (".uno:DesignStyleSet?Action:string=gallery", "Style Set"),
                               (".uno:DesignStyleSet?Action:string=spacing", "Paragraph Spacing"),
                               (".uno:DesignStyleSet?Action:string=setdefault", "Set as Default")):
                self.assertEqual(label, self.command_label(url), url)

    def test_layout_sections_and_toolboxes(self):
        self.check_sections_and_toolboxes("writer_layout.json", 3)

    def test_layout_tab_is_visible_in_the_text_table_image_and_print_preview_contexts(self):
        with self.ui_test.create_doc_in_start_center("writer") as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Layout")
            finally:
                self.switch_to("Default")

    def test_layout_paragraph_spin_fields_render(self):
        # the controllers registered in swmodule.cxx:278-281 draw the four fields (stock pattern,
        # notebookbar.ui:5443-5447); an item that is only a button is a few dozen px wide, a spin field is wider
        with self.ui_test.create_doc_in_start_center("writer") as document:
            self.switch_to(OFFICE_UI)
            xWindow = document.CurrentController.Frame.ContainerWindow
            old = xWindow.getPosSize()
            try:
                xWindow.setPosSize(0, 0, 1920, 900, SIZE)
                xWriterDoc = self.xUITest.getTopFocusWindow()

                def spin_sizes():
                    sizes = {}
                    for name in ("LeftParaMargin", "RightParaMargin", "AboveSpacing", "BelowSpacing"):
                        xBox = xWriterDoc.getChild("bxLayout" + name)
                        items = [c for c in xBox.getChildren() if c.startswith("toolboxitem-")]
                        self.assertEqual(1, len(items), name)
                        state = get_state_as_dict(xBox.getChild(items[0]))
                        sizes[name] = (int(state["Width"]), int(state["Height"]))
                    return sizes

                sizes = self.settle(spin_sizes)
                for name, (width, height) in sizes.items():
                    self.assertGreaterEqual(width, 60, "%s is not a spin field: %s" % (name, sizes))
                    self.assertGreater(height, 0, name)
            finally:
                xWindow.setPosSize(old.X, old.Y, old.Width, old.Height, SIZE)
                self.switch_to("Default")

    def select_rectangle(self, document):
        """A rectangle shape in the text, selected: the context of the Arrange menus."""
        xShape = document.createInstance("com.sun.star.drawing.RectangleShape")
        xShape.Size = uno.createUnoStruct("com.sun.star.awt.Size", 3000, 2000)
        xShape.AnchorType = uno.Enum("com.sun.star.text.TextContentAnchorType", "AT_PARAGRAPH")
        document.DrawPage.add(xShape)
        document.CurrentController.select(xShape)
        return xShape

    def test_layout_dropdown_popups_list_their_items_through_the_real_controllers(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            expected = {
                ("LayoutBreaksMenu", "layout_breaks"): [
                    ".uno:InsertPagebreak", ".uno:InsertColumnBreak", ".uno:InsertLinebreak",
                    ".uno:InsertBreak", ".uno:InsertSection"],
                ("LayoutWrapTextMenu", "layout_wraptext"): [
                    ".uno:SetAnchorToChar", ".uno:WrapOn", ".uno:WrapContour", ".uno:WrapOff",
                    ".uno:WrapThroughTransparent", ".uno:WrapThrough", ".uno:ContourDialog", ".uno:TextWrap"],
                ("PageLayoutBringForwardMenu", "layout_bringforward"): [
                    ".uno:ObjectForwardOne", ".uno:BringToFront", ".uno:SetObjectToForeground"],
                ("PageLayoutSendBackwardMenu", "layout_sendbackward"): [
                    ".uno:ObjectBackOne", ".uno:SendToBack", ".uno:SetObjectToBackground"],
                ("PageLayoutAlignMenu", "layout_align"): [
                    ".uno:ObjectAlignLeft", ".uno:AlignCenter", ".uno:ObjectAlignRight", ".uno:AlignUp",
                    ".uno:AlignMiddle", ".uno:AlignDown"],
                ("PageLayoutGroupMenu", "layout_group"): [".uno:FormatGroup", ".uno:FormatUngroup"],
                ("PageLayoutRotateMenu", "layout_rotate"): [
                    ".uno:RotateRight", ".uno:RotateLeft", ".uno:FlipVertical", ".uno:FlipHorizontal",
                    ".uno:TransformDialog"]}
            for (command, resource), items in expected.items():
                xPopup = self.menu_controller(".uno:" + command, resource)
                self.assertEqual(items, self.popup_commands(xPopup), command)

    def test_layout_menus_group_their_items_with_separators(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            for command, resource, shape in (
                    ("LayoutBreaksMenu", "layout_breaks", [True, True, True, False, True, True]),
                    ("LayoutWrapTextMenu", "layout_wraptext", [True] * 6 + [False] + [True] * 2),
                    ("PageLayoutRotateMenu", "layout_rotate", [True] * 4 + [False, True])):
                xPopup = self.menu_controller(".uno:" + command, resource)
                got = [bool(xPopup.getCommand(xPopup.getItemId(pos))) for pos in range(xPopup.getItemCount())]
                self.assertEqual(shape, got, command)

    def test_layout_arrange_menus_list_their_items_with_a_shape_selected(self):
        with self.ui_test.create_doc_in_start_center("writer") as document:
            self.select_rectangle(document)
            for command, resource, enabled in (
                    ("LayoutWrapTextMenu", "layout_wraptext",
                     ["WrapOn", "WrapContour", "WrapOff", "WrapThroughTransparent", "WrapThrough", "TextWrap"]),
                    ("PageLayoutBringForwardMenu", "layout_bringforward",
                     ["ObjectForwardOne", "BringToFront"]),
                    ("PageLayoutSendBackwardMenu", "layout_sendbackward",
                     ["ObjectBackOne", "SendToBack"]),
                    ("PageLayoutAlignMenu", "layout_align",
                     ["ObjectAlignLeft", "AlignCenter", "ObjectAlignRight", "AlignUp", "AlignMiddle", "AlignDown"]),
                    # Group needs two shapes and Ungroup a group: both are listed, neither is enabled for one
                    ("PageLayoutGroupMenu", "layout_group", []),
                    ("PageLayoutRotateMenu", "layout_rotate", ["TransformDialog"])):
                xPopup = self.menu_controller(".uno:" + command, resource)
                listed = self.popup_commands(xPopup)
                self.assertTrue(listed, command)
                for name in enabled:
                    self.assertIn(".uno:" + name, listed, command)
                # the draw shell takes over the selection on idle; ask again until every item reports enabled
                xToolkit = self.xContext.ServiceManager.createInstance("com.sun.star.awt.Toolkit")
                state = {}
                deadline = time.time() + 10
                while time.time() < deadline:
                    xToolkit.processEventsToIdle()
                    state = {name: self.dispatch_enabled(name) for name in enabled}
                    if all(state.values()):
                        break
                self.assertEqual({name: True for name in enabled}, state, command + " with a shape selected")
            self.assertTrue(self.dispatch_enabled("AnchorMenu"))
            # In Front of / Behind Text toggle the layer of the shape (drawsh.sdi:285, :292): the one it is not in
            # is enabled
            self.assertNotEqual(self.dispatch_enabled("SetObjectToForeground"),
                                self.dispatch_enabled("SetObjectToBackground"))
            # Rotate Left/Right serve images only (sw/sdi/_grfsh.sdi:75, :89)
            self.assertFalse(self.dispatch_enabled("RotateLeft"))
            self.assertFalse(self.dispatch_enabled("RotateRight"))

    def test_layout_dropdown_and_new_label_commands_resolve_their_labels(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            for command, label in (("LayoutBreaksMenu", "Breaks"), ("LayoutWrapTextMenu", "Wrap Text"),
                                   ("PageLayoutBringForwardMenu", "Bring Forward"),
                                   ("PageLayoutSendBackwardMenu", "Send Backward"), ("PageLayoutAlignMenu", "Align"),
                                   ("PageLayoutGroupMenu", "Group"), ("PageLayoutRotateMenu", "Rotate"),
                                   ("LeftParaMargin", "Before Text Indent"), ("RightParaMargin", "After Text Indent"),
                                   ("AboveSpacing", "Above Paragraph Spacing"),
                                   ("BelowSpacing", "Below Paragraph Spacing")):
                self.assertEqual(label, self.command_label(".uno:" + command), command)

    def test_layout_commands_that_are_real_are_enabled(self):
        with self.ui_test.create_doc_in_start_center("writer"):
            for name in ("PageMargin", "Orientation", "AttributePageSize", "PageColumnType", "InsertPagebreak",
                         "InsertColumnBreak", "InsertLinebreak", "InsertBreak", "InsertSection",
                         "LineNumberingDialog", "Hyphenate", "Navigator"):
                self.assertTrue(self.dispatch_enabled(name), name)

# vim: set shiftwidth=4 softtabstop=4 expandtab:

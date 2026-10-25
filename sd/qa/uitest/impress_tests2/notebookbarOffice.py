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
from contextlib import contextmanager
from pathlib import Path

from uitest.framework import UITestCase
from uitest.uihelper.common import get_state_as_dict
from libreoffice.uno.propertyvalue import mkPropertyValues
from com.sun.star.accessibility.AccessibleRole import PAGE_TAB_LIST, DOCUMENT_PRESENTATION, DOCUMENT_TEXT, PARAGRAPH, PUSH_BUTTON, BUTTON_DROPDOWN
from com.sun.star.awt import Point
from com.sun.star.beans import PropertyValue
from com.sun.star.frame import XStatusListener

OFFICE_UI = "notebookbar_office.ui"
IMPRESS_MODULE = "com.sun.star.presentation.PresentationDocument"
HOME_SLOTS = (0, 1, 2, 3, 4)  # SID offsets of the Home placeholders: Section family, Convert to SmartArt,
# Regroup, the Shape Effects family, Replace Fonts
INSERT_SLOTS = (5, 6, 7, 8, 9)  # the Screenshot, 3D Models, SmartArt, Zoom (2 variants) and Screen Recording slots
RESET_LAYOUT = ".uno:AssignLayout?Reset:bool=true"
INSERT_ZOOM = ".uno:InsertZoom?Type:string="
DESIGN_SLOTS = (10,)  # SID offset of the Design placeholders: the PageLayoutThemePart family (3 variants)
THEME_PART = ".uno:PageLayoutThemePart?Part:string="
MOTION_SLOTS = (11, 12)  # SID offsets of the Transitions and Animations placeholders: the Preview family
# (2 variants) and Animation Painter
SLIDESHOW_SLOTS = (13, 14)  # SID offsets of the Slide Show placeholders: Record and the Option family (2 variants)
REVIEW_SLOTS = (15, 16, 17, 18)  # SID offsets of the Review placeholders: Check Accessibility, Translate, the
# Compare family (7 variants) and Hide Ink
VIEW_SLOTS = (19, 20, 21, 22)  # SID offsets of the View placeholders: Reading View (the ViewMode family), Arrange All,
# Cascade and Move Split
HELP_SLOTS = (23,)  # SID offset of the Help placeholder: Feedback
TRANSITION_DECK = "SdSlideTransitionDeck"
ANIMATION_DECK = "SdCustomAnimationDeck"
# a 1x1 PNG, the picture of the image context
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==")

# The pages of today's generated Impress office .ui (sd/uiconfig/simpress/ui/notebookbar_office.ui),
# in tab order: (tab label without its mnemonic, page id). Tasks that change the tabs update this list;
# I8a reaches PowerPoint's order (Help is last). Table .. 3D are the contextual tabs: they only show with their object
# or view.
TABS = [("File", "File"), ("Home", "Home Tab"), ("Insert", "Insert"), ("Design", "Design"),
        ("Transitions", "Layout"), ("Animations", "Animations"), ("Slide Show", "SlideShow"), ("Review", "Review"), ("View", "View"),
        ("Table", "Table"), ("Image", "Image"), ("Draw", "Draw"), ("Object", "Object"), ("Media", "Media"),
        ("Form", "Form"), ("Master", "Master"), ("Outline", "Outline"), ("3D", "3D"),
        ("Extension", "Extension"), ("Tools", "Tools"), ("Help", "Help")]
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

    def home_layout(self):
        src = Path(os.environ["TDOC"]).parents[3]
        return json.loads((src / "product" / "ui" / "impress_home.json").read_text(encoding="utf-8"))

    def test_home_sections_and_toolboxes(self):
        layout = self.home_layout()
        prefix = layout["id_prefix"]
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(7, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xImpressDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xImpressDoc.getChild("bx" + prefix + box["id"])
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
            if role not in (DOCUMENT_PRESENTATION, DOCUMENT_TEXT, PARAGRAPH):
                queue += [xAcc.getAccessibleChild(i).getAccessibleContext()
                          for i in range(xAcc.getAccessibleChildCount())]
        self.fail("no tab list with %d tabs in the accessibility tree" % len(TABS))

    def check_tab_is_shown(self, document, tab, contextual):
        """`tab` has a tab on screen; `contextual` (the tab of the selected object, or None) proves the context."""
        if contextual:
            self.wait_for(lambda: contextual in self.visible_tabs(document), contextual + " tab is not shown", 10)
        else:
            self.wait_for(lambda: tab in self.visible_tabs(document), tab + " tab is not shown", 10)
            self.assertFalse(CONTEXTUAL & set(self.visible_tabs(document)))
        self.assertIn(tab, self.visible_tabs(document))

    def check_home_tab_is_shown(self, document, contextual):
        self.check_tab_is_shown(document, "Home", contextual)

    def check_tab_in_every_context(self, document, tab):
        """`tab` shows with nothing selected, then with a text box, a shape, a table and an image selected."""
        self.check_tab_is_shown(document, tab, None)
        self.add_shape(document, "com.sun.star.drawing.TextShape", "text")
        self.wait_for(lambda: tab in self.visible_tabs(document), tab + " tab is not shown", 10)
        self.assertIn(tab, self.visible_tabs(document))
        self.add_shape(document, "com.sun.star.drawing.RectangleShape")
        self.check_tab_is_shown(document, tab, "Draw")
        self.xUITest.executeCommand(".uno:InsertTable?Columns:short=2&Rows:short=2")
        self.check_tab_is_shown(document, tab, "Table")
        with tempfile.TemporaryDirectory() as tmp:
            picture = Path(tmp) / "pixel.png"
            picture.write_bytes(PNG)
            xGraphic = self.add_shape(document, "com.sun.star.drawing.GraphicObjectShape")
            xGraphic.GraphicURL = picture.as_uri()
            document.CurrentController.select(xGraphic)
            self.check_tab_is_shown(document, tab, "Image")

    def add_shape(self, document, service, text=None):
        """A shape of `service` on the first slide, selected."""
        shape = document.createInstance(service)
        shape.Size = uno.createUnoStruct("com.sun.star.awt.Size", 6000, 3000)
        document.DrawPages[0].add(shape)
        shape.Position = Point(2000, 9000)
        if text is not None:
            shape.String = text
        document.CurrentController.select(shape)
        return shape

    def test_home_tab_is_visible_with_a_text_box_a_shape_a_table_and_an_image_selected(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_home_tab_is_shown(document, None)
                # a text box
                self.add_shape(document, "com.sun.star.drawing.TextShape", "text")
                self.wait_for(lambda: "Home" in self.visible_tabs(document), "Home tab is not shown", 10)
                self.assertIn("Home", self.visible_tabs(document))
                # a shape
                self.add_shape(document, "com.sun.star.drawing.RectangleShape")
                self.check_home_tab_is_shown(document, "Draw")
                # a table
                self.xUITest.executeCommand(".uno:InsertTable?Columns:short=2&Rows:short=2")
                self.check_home_tab_is_shown(document, "Table")
                # an image
                with tempfile.TemporaryDirectory() as tmp:
                    picture = Path(tmp) / "pixel.png"
                    picture.write_bytes(PNG)
                    xGraphic = self.add_shape(document, "com.sun.star.drawing.GraphicObjectShape")
                    xGraphic.GraphicURL = picture.as_uri()
                    document.CurrentController.select(xGraphic)
                    self.check_home_tab_is_shown(document, "Image")
            finally:
                self.switch_to("Default")

    def test_home_placeholders_are_disabled_and_inert(self):
        # 5 slots: the Section family (3 variants), Convert to SmartArt, Regroup, the Shape Effects family
        # (3 variants) and Replace Fonts
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in HOME_SLOTS)
        self.assertEqual(9, len(names))
        with self.impress_doc() as document:
            slide = document.DrawPages[0]
            slide.getByIndex(0).String = "keep"
            document.setModified(False)
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assert_disabled_and_inert(names)
            self.assertEqual(1, document.DrawPages.Count)
            self.assertEqual("keep", slide.getByIndex(0).String)
            self.assertFalse(document.isModified())

    def menu_controller(self, command, resource, with_controller=False):
        """The awt popup menu that the ribbon dropdown `command` builds through its real menu controller.

        `resource` is the popup file the ResourceMenuController reads (its "Value"); None for a controller
        without one (the window list). With `with_controller` the controller comes back too: (popup, controller)."""
        xDesktop = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.xContext)
        xFactory = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.PopupMenuControllerFactory", self.xContext)
        self.assertTrue(xFactory.hasController(command, IMPRESS_MODULE), command)
        args = {"Frame": xDesktop.getCurrentFrame(), "CommandURL": command, "ModuleIdentifier": IMPRESS_MODULE}
        if resource is not None:
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
        props = {p.Name: p.Value for p in xDescriptions.getByName(IMPRESS_MODULE).getByName(url)}
        return props["Label"].replace("~", "")

    def test_home_dropdown_popups_list_their_items_through_the_real_controllers(self):
        section = ".uno:HomeSection?Action:string="
        effect = ".uno:HomeShapeEffect?Effect:string="
        with self.impress_doc():
            expected = {
                ("HomeSectionMenu", "home_section"): [
                    ".uno:AddSlideSection", ".uno:RenameSlideSection", ".uno:RemoveSlideSection",
                    ".uno:RemoveSlideSectionAndSlides", ".uno:MoveSlideSectionUp", ".uno:MoveSlideSectionDown",
                    section + "removeall", section + "collapseall", section + "expandall"],
                ("HomeChangeCaseMenu", "home_changecase"): [
                    ".uno:ChangeCaseToSentenceCase", ".uno:ChangeCaseToLower", ".uno:ChangeCaseToUpper",
                    ".uno:ChangeCaseToTitleCase", ".uno:ChangeCaseToToggleCase"],
                ("HomeColumnsMenu", "home_columns"): [".uno:TextAttributes"],  # decision 14's fallback
                ("HomeTextDirectionMenu", "home_textdirection"): [
                    ".uno:TextdirectionLeftToRight", ".uno:TextdirectionTopToBottom", ".uno:ParaLeftToRight",
                    ".uno:ParaRightToLeft"],
                ("HomeAlignTextMenu", "home_aligntext"): [".uno:CellVertTop", ".uno:CellVertCenter",
                                                          ".uno:CellVertBottom", ".uno:TextAttributes"],
                ("InsertShapesMenu", "home_shapes"): [
                    ".uno:ShapesLineMenu", ".uno:BasicShapes", ".uno:SymbolShapes", ".uno:ArrowShapes",
                    ".uno:FlowChartShapes", ".uno:CalloutShapes", ".uno:StarShapes", ".uno:ArrowsToolbox",
                    ".uno:ConnectorToolbox", ".uno:Objects3DToolbox"],
                ("HomeArrangeMenu", "home_arrange"): [
                    ".uno:BringToFront", ".uno:SendToBack", ".uno:Forward", ".uno:Backward", ".uno:FormatGroup",
                    ".uno:FormatUngroup", ".uno:HomeRegroup", ".uno:ObjectAlignLeft", ".uno:AlignCenter",
                    ".uno:ObjectAlignRight", ".uno:AlignUp", ".uno:AlignMiddle", ".uno:AlignDown",
                    ".uno:DistributeSelection", ".uno:ToggleObjectRotateMode", ".uno:MirrorVert",
                    ".uno:MirrorHorz", ".uno:Navigator"],
                ("HomeShapeEffectsMenu", "home_shapeeffects"): [
                    effect + "preset", ".uno:FillShadow", effect + "reflection", ".uno:SidebarDeck.PropertyDeck",
                    effect + "bevel", ".uno:ExtrusionToggle"],
                ("HomeFindMenu", "home_find"): ["vnd.sun.star.findbar:FocusToFindbar", ".uno:SearchDialog"],
                ("HomeReplaceMenu", "home_replace"): [".uno:SearchDialog", ".uno:HomeReplaceFonts"],
                ("HomeSelectMenu", "home_select"): [".uno:SelectAll", ".uno:SelectObject", ".uno:Navigator"]}
            for (command, resource), items in expected.items():
                xPopup = self.menu_controller(".uno:" + command, resource)
                self.assertEqual(items, self.popup_commands(xPopup), command)

    def test_home_dropdown_and_new_label_commands_resolve_their_labels(self):
        section = "HomeSection?Action:string="
        effect = "HomeShapeEffect?Effect:string="
        with self.impress_doc():
            for command, label in (("HomeSectionMenu", "Section"), ("HomeChangeCaseMenu", "Change Case"),
                                   ("HomeColumnsMenu", "Columns"), ("HomeTextDirectionMenu", "Text Direction"),
                                   ("HomeAlignTextMenu", "Align Text"),
                                   ("AssignLayout?Reset:bool=true", "Reset Slide Layout"),
                                   (section + "removeall", "Remove All Sections"),
                                   (section + "collapseall", "Collapse All"), (section + "expandall", "Expand All"),
                                   ("HomeConvertToSmartArt", "Convert to SmartArt"),
                                   ("InsertShapesMenu", "Shapes"), ("HomeArrangeMenu", "Arrange"),
                                   ("HomeShapeEffectsMenu", "Shape Effects"), ("HomeFindMenu", "Find"),
                                   ("HomeReplaceMenu", "Replace"), ("HomeSelectMenu", "Select"),
                                   ("HomeRegroup", "Regroup"), (effect + "preset", "Preset"),
                                   (effect + "reflection", "Reflection"), (effect + "bevel", "Bevel"),
                                   ("HomeReplaceFonts", "Replace Fonts...")):
                self.assertEqual(label, self.command_label(".uno:" + command), command)
            for name in ("HomeConvertToSmartArt", section + "removeall", "HomeRegroup", effect + "bevel",
                         "HomeReplaceFonts"):
                self.assertFalse(self.dispatch_enabled(name), name)

    def test_home_commands_that_are_real_are_enabled(self):
        with self.impress_doc() as document:
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.add_shape(document, "com.sun.star.drawing.TextShape", "Hello world")
            for name in ("AddSlideSection", "TextAttributes", "InsertPage", "ImportFromFile", "AssignLayout"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)

    def test_home_ribbon_shows_powerpoints_labels(self):
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                labels = {"bxHomeNewSlide": "New Slide", "bxHomeReuseSlides": "Reuse Slides",
                          "bxHomeLayout": "Layout", "bxHomeReset": "Reset", "bxHomeSection": "Section",
                          "bxHomePaste": "Paste", "bxHomeFormatPaintbrush": "Format Painter",
                          "bxHomeTextDirection": "Text Direction", "bxHomeAlignText": "Align Text",
                          "bxHomeConvertToSmartArt": "Convert to SmartArt"}
                got = self.settle(lambda: {box: get_state_as_dict(
                    xImpressDoc.getChild(box).getChild("toolboxitem-1"))["Text"] for box in labels})
                self.assertEqual(labels, got)
            finally:
                self.switch_to("Default")

    def test_home_reset_puts_a_moved_title_placeholder_back(self):
        # design decision 13: .uno:AssignLayout?Reset:bool=true re-applies the slide's layout
        with self.impress_doc() as document:
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            slide = document.DrawPages[0]
            title = slide.getByIndex(0)
            self.assertEqual("com.sun.star.presentation.TitleTextShape", title.ShapeType)
            home = (title.Position.X, title.Position.Y)
            title.Position = Point(home[0] + 4000, home[1] + 3000)
            self.assertNotEqual(home, (title.Position.X, title.Position.Y))
            document.CurrentController.select(title)
            self.xUITest.executeCommand(RESET_LAYOUT)
            title = slide.getByIndex(0)
            self.assertEqual(home, self.settle(lambda: (slide.getByIndex(0).Position.X,
                                                        slide.getByIndex(0).Position.Y)))
            self.assertEqual(1, document.DrawPages.Count)

    def test_home_text_column_variants_do_not_reach_a_text_box(self):
        # design decision 14's gate FAILED: .uno:TextColumnsNumber?TextColumnsNumber:short=2 does not give a
        # text box two columns, because SDRATTR_TEXTCOLUMNS_NUMBER has slot id 0 in the svx item info
        # (svx/source/svdraw/svdattr.cxx:440), so a dispatched argument is never mapped to the pool item. The
        # sidebar sets the item itself. The fallback applies: the Columns menu keeps only More Columns... If
        # this test fails, the slot got a mapping: restore the three column items (design decision 14).
        with self.impress_doc() as document:
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            shape = self.add_shape(document, "com.sun.star.drawing.TextShape", "one two three four five six")
            self.assertIsNone(shape.TextColumns)
            self.xUITest.executeCommand(".uno:TextColumnsNumber?TextColumnsNumber:short=2")
            self.settle(lambda: shape.TextColumns is None)
            self.assertIsNone(shape.TextColumns)

    def toolbox_item(self, document, role, name):
        """The accessible context of the ribbon toolbox item of `role` named `name`."""
        xWindow = document.CurrentController.Frame.ContainerWindow
        xAcc = xWindow.getProperty("XAccessible").getAccessibleContext()
        while xAcc.getAccessibleParent() is not None:
            xAcc = xAcc.getAccessibleParent().getAccessibleContext()
        queue = [xAcc]
        while queue:
            xAcc = queue.pop(0)
            if xAcc.getAccessibleRole() == role and xAcc.getAccessibleName() == name:
                return xAcc
            if xAcc.getAccessibleRole() not in (DOCUMENT_PRESENTATION, DOCUMENT_TEXT, PARAGRAPH):
                queue += [xAcc.getAccessibleChild(i).getAccessibleContext()
                          for i in range(xAcc.getAccessibleChildCount())]
        return None

    def popup_buttons(self):
        """The names of the push buttons in every top window's accessible tree (a popup is a top window)."""
        xToolkit = self.xContext.ServiceManager.createInstance("com.sun.star.awt.Toolkit")
        names = []
        for i in range(xToolkit.getTopWindowCount()):
            xTop = xToolkit.getTopWindow(i)
            xAcc = xTop.getProperty("XAccessible") if xTop is not None else None
            queue = [xAcc.getAccessibleContext()] if xAcc is not None else []
            while queue:
                xCtx = queue.pop(0)
                if xCtx.getAccessibleRole() == PUSH_BUTTON:
                    names.append(xCtx.getAccessibleName())
                if xCtx.getAccessibleRole() not in (DOCUMENT_PRESENTATION, DOCUMENT_TEXT, PARAGRAPH):
                    queue += [xCtx.getAccessibleChild(c).getAccessibleContext()
                              for c in range(min(xCtx.getAccessibleChildCount(), 40))]
        return names

    def test_home_new_slide_and_layout_popups_are_the_layout_gallery_plus_one_button(self):
        # design decision 19: New Slide's popup is the layout gallery plus Duplicate Slide, Layout's the
        # gallery plus Reset Slide Layout (sd/source/ui/controller/slidelayoutcontroller.cxx)
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                for item, button in (("New Slide", "Duplicate"), ("Layout", "Reset Slide Layout")):
                    xItem = self.settle(lambda: self.toolbox_item(document, BUTTON_DROPDOWN, item))
                    self.assertIsNotNone(xItem, item)
                    self.assertEqual(2, xItem.getAccessibleActionCount(), item)  # click and toggle popup
                    xItem.doAccessibleAction(1)
                    try:
                        self.wait_for(lambda: any(n.startswith(button) for n in self.popup_buttons()),
                                      "the %s popup has no %s button" % (item, button))
                    finally:
                        xItem.doAccessibleAction(1)
            finally:
                self.switch_to("Default")

    def test_home_arrange_menu_lists_its_items_with_a_shape_selected(self):
        # the Arrange menu is built by its real controller; the items that act on one shape are enabled
        # (the dispatch status decides: a menu controller's popup keeps its disabled items), Regroup is a
        # placeholder and stays disabled
        with self.impress_doc() as document:
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.add_shape(document, "com.sun.star.drawing.RectangleShape")
            xPopup = self.menu_controller(".uno:HomeArrangeMenu", "home_arrange")
            items = self.popup_commands(xPopup)
            self.assertEqual(18, len(items))
            self.assertEqual(".uno:BringToFront", items[0])
            self.assertEqual(".uno:Navigator", items[-1])
            for name in ("SendToBack", "MirrorVert", "MirrorHorz", "ToggleObjectRotateMode", "Navigator"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)
            self.assertFalse(self.dispatch_enabled("HomeRegroup"))

    def test_home_find_menu_first_item_is_the_find_toolbar_and_select_all_selects(self):
        with self.impress_doc() as document:
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            xPopup = self.menu_controller(".uno:HomeFindMenu", "home_find")
            self.assertEqual("vnd.sun.star.findbar:FocusToFindbar", self.popup_commands(xPopup)[0])
            self.assertEqual("Find...", self.command_label("vnd.sun.star.findbar:FocusToFindbar"))
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("SearchDialog")))
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("SelectAll")))
            self.xUITest.executeCommand(".uno:SelectAll")
            self.assertGreater(self.settle(lambda: document.CurrentController.Selection.Count), 0)

    def test_home_shape_cells_open_their_stock_popups(self):
        # design decision 15: the shape sub-toolbar cells keep their stock popups, built by the
        # ToolbarAsMenuController of each command from its toolbar (Controller.xcu). The headless window
        # clips the ribbon before the Drawing section, so the cells' accessible items cannot be pressed
        # here (the fit is I2b's); the controllers are what the cells attach to.
        stock = {"ArrowsToolbox": "arrowsbar", "ConnectorToolbox": "connectorsbar", "BasicShapes": "basicshapes",
                 "SymbolShapes": "symbolshapes", "ArrowShapes": "arrowshapes", "FlowChartShapes": "flowchartshapes",
                 "CalloutShapes": "calloutshapes", "StarShapes": "starshapes", "LineToolbox": "linesbar",
                 "Objects3DToolbox": "3dobjectsbar"}
        with self.impress_doc():
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            for command, resource in stock.items():
                xPopup = self.menu_controller(".uno:" + command, resource)
                self.assertGreater(len(self.popup_commands(xPopup)), 2, command)

    def test_home_drawing_and_editing_ribbon_shows_powerpoints_labels(self):
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                labels = {"bxHomeArrange": "Arrange", "bxHomeQuickStyles": "Quick Styles",
                          "bxHomeShapeFill": "Shape Fill", "bxHomeShapeOutline": "Shape Outline",
                          "bxHomeShapeEffects": "Shape Effects", "bxHomeFind": "Find",
                          "bxHomeReplace": "Replace", "bxHomeSelect": "Select"}
                got = self.settle(lambda: {box: get_state_as_dict(
                    xImpressDoc.getChild(box).getChild("toolboxitem-1"))["Text"] for box in labels})
                self.assertEqual(labels, got)
            finally:
                self.switch_to("Default")

    def insert_layout(self):
        src = Path(os.environ["TDOC"]).parents[3]
        return json.loads((src / "product" / "ui" / "impress_insert.json").read_text(encoding="utf-8"))

    def test_insert_sections_and_toolboxes(self):
        layout = self.insert_layout()
        prefix = layout["id_prefix"]
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(9, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xImpressDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xImpressDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_insert_tab_is_visible_with_a_text_box_a_shape_a_table_and_an_image_selected(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Insert")
            finally:
                self.switch_to("Default")

    def test_insert_video_and_audio_have_distinct_widget_ids(self):
        # design decision 16: both buttons run .uno:InsertAVMedia, the widget commands tell them apart
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                xVideo = xImpressDoc.getChild("bxInsertVideo")
                xAudio = xImpressDoc.getChild("bxInsertAudio")
                got = self.settle(lambda: {"Video": get_state_as_dict(xVideo.getChild("toolboxitem-1"))["Text"],
                                           "Audio": get_state_as_dict(xAudio.getChild("toolboxitem-1"))["Text"]})
                self.assertEqual({"Video": "Video", "Audio": "Audio"}, got)
                self.assertEqual("1", get_state_as_dict(xVideo)["ItemCount"])
                self.assertEqual("1", get_state_as_dict(xAudio)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_insert_placeholders_are_disabled_and_inert(self):
        # 5 slots: Screenshot, 3D Models, SmartArt, the Zoom family (2 variants) and Screen Recording
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in INSERT_SLOTS)
        self.assertEqual(6, len(names))
        with self.impress_doc() as document:
            slide = document.DrawPages[0]
            slide.getByIndex(0).String = "keep"
            document.setModified(False)
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assert_disabled_and_inert(names)
            self.assertEqual(1, document.DrawPages.Count)
            self.assertEqual("keep", slide.getByIndex(0).String)
            self.assertFalse(document.isModified())

    def test_insert_dropdown_popups_list_their_items_through_the_real_controllers(self):
        with self.impress_doc() as document:
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            expected = {
                ("InsertZoomMenu", "insert_zoom"): [".uno:SummaryPage", INSERT_ZOOM + "section",
                                                    INSERT_ZOOM + "slide"],
                ("InsertTextBoxMenu", "insert_textbox"): [".uno:Text", ".uno:VerticalText"],
                # reused from Home (I2c)
                ("InsertShapesMenu", "home_shapes"): [
                    ".uno:ShapesLineMenu", ".uno:BasicShapes", ".uno:SymbolShapes", ".uno:ArrowShapes",
                    ".uno:FlowChartShapes", ".uno:CalloutShapes", ".uno:StarShapes", ".uno:ArrowsToolbox",
                    ".uno:ConnectorToolbox", ".uno:Objects3DToolbox"]}
            for (command, resource), items in expected.items():
                xPopup = self.menu_controller(".uno:" + command, resource)
                self.assertEqual(items, self.popup_commands(xPopup), command)
            # Summary Zoom is real (the Summary Slide command, enabled once the slide has a title), the two
            # other Zoom entries are placeholders; Text Box's two items are real
            self.assertFalse(self.dispatch_enabled("SummaryPage"))  # the title placeholder is still empty
            document.DrawPages[0].getByIndex(0).String = "Title"
            for name in ("SummaryPage", "Text", "VerticalText"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)
            for name in ("InsertZoom?Type:string=section", "InsertZoom?Type:string=slide"):
                self.assertFalse(self.dispatch_enabled(name), name)

    def test_insert_shapes_submenus_open(self):
        with self.impress_doc():
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            xPopup = self.menu_controller(".uno:InsertShapesMenu", "home_shapes")
            line = next(xPopup.getItemId(pos) for pos in range(xPopup.getItemCount())
                        if xPopup.getCommand(xPopup.getItemId(pos)) == ".uno:ShapesLineMenu")
            xSub = xPopup.getPopupMenu(line)
            self.assertIsNotNone(xSub, "Line has no submenu")
            self.assertEqual([".uno:Line", ".uno:Freeline_Unfilled", ".uno:Freeline", ".uno:Bezier_Unfilled",
                              ".uno:BezierFill", ".uno:Polygon_Unfilled", ".uno:Polygon_Diagonal_Unfilled",
                              ".uno:Polygon_Diagonal"], self.popup_commands(xSub))
            # the other nine entries are commands whose own controllers open a shape gallery or toolbar
            for name in ("BasicShapes", "SymbolShapes", "ArrowShapes", "FlowChartShapes", "CalloutShapes",
                         "StarShapes", "ArrowsToolbox", "ConnectorToolbox", "Objects3DToolbox"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)

    def test_insert_dropdown_and_placeholder_labels_resolve(self):
        with self.impress_doc():
            for command, label in (("InsertZoomMenu", "Zoom"), ("InsertTextBoxMenu", "Text Box"),
                                   ("InsertShapesMenu", "Shapes"), ("InsertScreenshot", "Screenshot"),
                                   ("Insert3DModels", "3D Models"), ("InsertSmartArt", "SmartArt"),
                                   ("InsertZoom?Type:string=section", "Section Zoom"),
                                   ("InsertZoom?Type:string=slide", "Slide Zoom"),
                                   ("InsertScreenRecording", "Screen Recording")):
                self.assertEqual(label, self.command_label(".uno:" + command), command)

    def test_insert_commands_that_are_real_are_enabled(self):
        with self.impress_doc() as document:
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            document.DrawPages[0].getByIndex(0).String = "Title"  # Summary Slide needs a titled slide
            self.add_shape(document, "com.sun.star.drawing.TextShape", "Hello world")
            for name in ("InsertPage", "ImportFromFile", "InsertTable", "InsertGraphic", "PhotoAlbumDialog",
                         "Gallery", "InsertObjectChart", "SummaryPage", "HyperlinkDialog", "AnimationEffects",
                         "InsertAnnotation", "Text", "VerticalText", "HeaderAndFooter", "FontworkGalleryFloater",
                         "InsertDateFieldVar", "InsertPageField", "InsertObject", "InsertMath", "InsertAVMedia"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)
            # Symbol (the character map) needs a text edit mode; selecting a text box is not enough

    def test_insert_ribbon_shows_powerpoints_labels(self):
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                labels = {"bxInsertNewSlide": "New Slide", "bxInsertReuseSlides": "Reuse Slides",
                          "bxInsertTable": "Table", "bxInsertPictures": "Pictures",
                          "bxInsertScreenshot": "Screenshot", "bxInsertPhotoAlbum": "Photo Album",
                          "bxInsertShapes": "Shapes", "bxInsertIcons": "Icons", "bxInsertModels3D": "3D Models",
                          "bxInsertZoom": "Zoom", "bxInsertLink": "Link", "bxInsertAction": "Action",
                          "bxInsertComment": "Comment", "bxInsertTextBox": "Text Box",
                          "bxInsertHeaderFooter": "Header & Footer", "bxInsertWordArt": "WordArt",
                          "bxInsertEquation": "Equation", "bxInsertSymbol": "Symbol",
                          "bxInsertVideo": "Video", "bxInsertAudio": "Audio",
                          "bxInsertScreenRecording": "Screen Recording"}
                got = self.settle(lambda: {box: get_state_as_dict(
                    xImpressDoc.getChild(box).getChild("toolboxitem-1"))["Text"] for box in labels})
                self.assertEqual(labels, got)
            finally:
                self.switch_to("Default")

    def design_layout(self):
        src = Path(os.environ["TDOC"]).parents[3]
        return json.loads((src / "product" / "ui" / "impress_design.json").read_text(encoding="utf-8"))

    def test_design_sections_and_toolboxes(self):
        layout = self.design_layout()
        prefix = layout["id_prefix"]
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(3, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xImpressDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xImpressDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_design_shows_before_the_layout_tab_which_becomes_transitions(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                labels = self.tab_labels(document, len(TABS))
                self.assertEqual(["Insert", "Design", "Transitions", "Animations", "Slide Show"], labels[2:7])
                self.check_tab_is_shown(document, "Design", None)
                shown = self.visible_tabs(document)
                self.assertLess(shown.index("Insert"), shown.index("Design"))
                self.assertLess(shown.index("Design"), shown.index("Transitions"))
            finally:
                self.switch_to("Default")

    def test_design_tab_is_visible_with_a_text_box_a_shape_a_table_and_an_image_selected(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Design")
            finally:
                self.switch_to("Default")

    def test_design_theme_colors_box_is_present(self):
        # the stock theme colors control (.uno:ThemeSelectorPanel) is the Variants box of the new page
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                xBox = xImpressDoc.getChild("bxDesignThemeColors")
                self.assertEqual("1", self.settle(lambda: get_state_as_dict(xBox)["ItemCount"]))
                self.assertEqual("true", get_state_as_dict(xBox)["Visible"])
                self.assertIsNotNone(xBox.getChild("toolboxitem-1"))
                self.assertEqual("Variants", self.settle(lambda: get_state_as_dict(
                    xImpressDoc.getChild("lbDesignVariants"))["Text"]))
            finally:
                self.switch_to("Default")

    def test_design_dropdown_popup_lists_its_items_through_the_real_controller(self):
        with self.impress_doc():
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            xPopup = self.menu_controller(".uno:DesignVariantsMenu", "design_variants")
            self.assertEqual([".uno:ThemeDialog", THEME_PART + "fonts", THEME_PART + "effects",
                              THEME_PART + "backgroundstyles"], self.popup_commands(xPopup))
            # Colors (the theme dialog) is real; the three theme parts are placeholders. The popup keeps
            # disabled items, so the enabled state comes from the dispatch status.
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("ThemeDialog")))
            for part in ("fonts", "effects", "backgroundstyles"):
                self.assertFalse(self.dispatch_enabled("PageLayoutThemePart?Part:string=" + part), part)

    def test_design_placeholders_are_disabled_and_inert(self):
        # 1 slot: the PageLayoutThemePart family (Fonts, Effects, Background Styles)
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in DESIGN_SLOTS)
        self.assertEqual(3, len(names))
        with self.impress_doc() as document:
            slide = document.DrawPages[0]
            slide.getByIndex(0).String = "keep"
            document.setModified(False)
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assert_disabled_and_inert(names)
            self.assertEqual(1, document.DrawPages.Count)
            self.assertEqual("keep", slide.getByIndex(0).String)
            self.assertFalse(document.isModified())

    def test_design_slide_size_opens_the_slide_properties_dialog(self):
        # .uno:SlideSetup targets .uno:PageSetup and has no dispatch of its own: the ribbon button runs
        # the real command, so the state and the dialog are the Slide Properties ones
        with self.impress_doc():
            props = {p.Name: p.Value for p in self.xContext.getValueByName(
                "/singletons/com.sun.star.frame.theUICommandDescription").getByName(IMPRESS_MODULE)
                .getByName(".uno:SlideSetup")}
            self.assertEqual(".uno:PageSetup", props["TargetURL"])
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("PageSetup")))
            with self.ui_test.execute_dialog_through_command(".uno:PageSetup", close_button="cancel") as xDialog:
                self.assertIsNotNone(xDialog.getChild("tabcontrol"))

    def test_design_dropdown_and_placeholder_labels_resolve(self):
        with self.impress_doc():
            for command, label in (("DesignVariantsMenu", "Variants"),
                                   ("PageLayoutThemePart?Part:string=fonts", "Fonts"),
                                   ("PageLayoutThemePart?Part:string=effects", "Effects"),
                                   ("PageLayoutThemePart?Part:string=backgroundstyles", "Background Styles")):
                self.assertEqual(label, self.command_label(".uno:" + command), command)

    def test_design_commands_that_are_real_are_enabled(self):
        with self.impress_doc():
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            for name in ("SidebarDeck.SdMasterPagesDeck", "SidebarDeck.PropertyDeck", "ThemeDialog", "PageSetup"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)

    def test_design_ribbon_shows_powerpoints_labels(self):
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                labels = {"bxDesignThemes": "Themes", "bxDesignSlideSize": "Slide Size",
                          "bxDesignFormatBackground": "Format Background"}
                got = self.settle(lambda: {box: get_state_as_dict(
                    xImpressDoc.getChild(box).getChild("toolboxitem-1"))["Text"] for box in labels})
                self.assertEqual(labels, got)
            finally:
                self.switch_to("Default")

    def motion_layout(self, name):
        src = Path(os.environ["TDOC"]).parents[3]
        return json.loads((src / "product" / "ui" / ("impress_%s.json" % name)).read_text(encoding="utf-8"))

    def check_sections_and_toolboxes(self, layout, sections):
        prefix = layout["id_prefix"]
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                self.assertEqual(sections, len(layout["sections"]))
                for section in layout["sections"]:
                    xLabel = xImpressDoc.getChild("lb" + prefix + section["name"])
                    self.assertEqual(section["caption"], get_state_as_dict(xLabel)["Text"])
                    for column in section["columns"]:
                        for box in column:
                            xBox = xImpressDoc.getChild("bx" + prefix + box["id"])
                            self.assertEqual(str(len(box["items"])), get_state_as_dict(xBox)["ItemCount"])
            finally:
                self.switch_to("Default")

    def test_transitions_sections_and_toolboxes(self):
        self.check_sections_and_toolboxes(self.motion_layout("transitions"), 3)

    def test_animations_sections_and_toolboxes(self):
        self.check_sections_and_toolboxes(self.motion_layout("animations"), 4)

    def test_transitions_and_animations_follow_design_in_tab_order(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                labels = self.tab_labels(document, len(TABS))
                self.assertEqual(["Insert", "Design", "Transitions", "Animations", "Slide Show", "Review", "View"],
                                 labels[2:9])
                self.assertNotIn("Layout", labels)
                shown = self.visible_tabs(document)
                self.assertLess(shown.index("Design"), shown.index("Transitions"))
                self.assertLess(shown.index("Transitions"), shown.index("Animations"))
                self.assertLess(shown.index("Animations"), shown.index("Slide Show"))
            finally:
                self.switch_to("Default")

    def test_transitions_tab_is_visible_with_a_text_box_a_shape_a_table_and_an_image_selected(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Transitions")
            finally:
                self.switch_to("Default")

    def test_animations_tab_is_visible_with_a_text_box_a_shape_a_table_and_an_image_selected(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Animations")
            finally:
                self.switch_to("Default")

    def deck(self, document, name):
        """The sidebar deck `name` (made visible first); isActive() is only safe with the sidebar shown."""
        sidebar = document.CurrentController.getSidebar()
        if not sidebar.isVisible():
            sidebar.setVisible(True)
        self.wait_for(sidebar.isVisible, "no sidebar", 10)
        return sidebar.getDecks().getByName(name)

    def deck_active(self, document, name):
        return self.settle(lambda: self.deck(document, name).isActive())

    def check_deck_controls(self, document, layout, deck_name, other_deck):
        """Every deck control of the page opens its deck and a second press keeps it open (decision 25).

        The headless window clips the ribbon, so the controls are not pressed: each one is looked up by its
        widget id (it is on the page) and its real URL is dispatched, which is what its press runs."""
        prefix = layout["id_prefix"]
        url = ".uno:SidebarDeck." + deck_name
        xImpressDoc = self.xUITest.getTopFocusWindow()
        controls = [(box, item) for section in layout["sections"] for column in section["columns"] for box in column
                    for item in box["items"] if item.get("action") == url]
        self.assertGreaterEqual(len(controls), 7)
        for box, item in controls:
            xBox = xImpressDoc.getChild("bx" + prefix + box["id"])
            self.assertEqual("1", get_state_as_dict(xBox)["ItemCount"], item["cmd"])
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("SidebarDeck." + deck_name)), item["cmd"])
            self.xUITest.executeCommand(".uno:SidebarDeck." + other_deck)  # start from the other deck
            self.wait_for(lambda: self.deck_active(document, other_deck), "no " + other_deck)
            self.assertFalse(self.deck_active(document, deck_name), item["cmd"])
            self.xUITest.executeCommand(url)
            self.wait_for(lambda: self.deck_active(document, deck_name), item["cmd"] + " did not open its deck")
            self.xUITest.executeCommand(url)  # a second press keeps it open
            self.assertTrue(self.deck_active(document, deck_name), item["cmd"] + " closed its deck")
            self.assertFalse(self.deck_active(document, other_deck), item["cmd"])

    def test_transitions_deck_controls_open_the_deck_and_a_second_press_keeps_it_open(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_deck_controls(document, self.motion_layout("transitions"), TRANSITION_DECK,
                                         ANIMATION_DECK)
            finally:
                self.switch_to("Default")

    def test_animations_deck_controls_open_the_deck_and_a_second_press_keeps_it_open(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_deck_controls(document, self.motion_layout("animations"), ANIMATION_DECK,
                                         TRANSITION_DECK)
            finally:
                self.switch_to("Default")

    def test_animation_pane_toggles_the_animation_deck(self):
        # the one exact control (decision 25): .uno:CustomAnimation shows the Animation deck, then hides it
        with self.impress_doc() as document:
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("CustomAnimation")))
            self.assertFalse(self.deck_active(document, ANIMATION_DECK))
            self.xUITest.executeCommand(".uno:CustomAnimation")
            self.wait_for(lambda: self.deck_active(document, ANIMATION_DECK), "the pane did not open the deck")
            self.xUITest.executeCommand(".uno:CustomAnimation")
            self.wait_for(lambda: not self.deck_active(document, ANIMATION_DECK), "the pane did not close the deck")

    def test_transitions_and_animations_placeholders_are_disabled_and_inert(self):
        # 2 slots: the Preview family (Transitions and Animations variants) and Animation Painter
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in MOTION_SLOTS)
        self.assertEqual(3, len(names))
        with self.impress_doc() as document:
            slide = document.DrawPages[0]
            slide.getByIndex(0).String = "keep"
            document.setModified(False)
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assert_disabled_and_inert(names)
            self.assertEqual(1, document.DrawPages.Count)
            self.assertEqual("keep", slide.getByIndex(0).String)
            self.assertFalse(document.isModified())

    def test_transitions_and_animations_labels_resolve(self):
        with self.impress_doc():
            for command, label in (("PreviewEffects?Target:string=transition", "Preview"),
                                   ("PreviewEffects?Target:string=animation", "Preview"),
                                   ("AnimationPainter", "Animation Painter")):
                self.assertEqual(label, self.command_label(".uno:" + command), command)

    def test_transitions_and_animations_commands_that_are_real_are_enabled(self):
        with self.impress_doc():
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            for name in ("SidebarDeck." + TRANSITION_DECK, "SidebarDeck." + ANIMATION_DECK, "CustomAnimation"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)

    def test_transitions_and_animations_ribbon_shows_powerpoints_labels(self):
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                labels = {"bxTransitionsPreview": "Preview", "bxTransitionsStyles": "Transition Styles",
                          "bxTransitionsEffectOptions": "Effect Options", "bxTransitionsSound": "Sound",
                          "bxTransitionsApplyToAll": "Apply To All", "bxTransitionsOnMouseClick": "On Mouse Click",
                          "bxAnimationsStyles": "Animation Styles", "bxAnimationsAddAnimation": "Add Animation",
                          "bxAnimationsPane": "Animation Pane", "bxAnimationsStart": "Start",
                          "bxAnimationsMoveEarlier": "Move Earlier"}
                got = self.settle(lambda: {box: get_state_as_dict(
                    xImpressDoc.getChild(box).getChild("toolboxitem-1"))["Text"] for box in labels})
                self.assertEqual(labels, got)
            finally:
                self.switch_to("Default")

    def test_slideshow_sections_and_toolboxes(self):
        self.check_sections_and_toolboxes(self.motion_layout("slideshow"), 3)

    def test_slideshow_tab_is_visible_with_a_text_box_a_shape_a_table_and_an_image_selected(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Slide Show")
            finally:
                self.switch_to("Default")

    def test_slideshow_has_no_dropdown_menu_to_build(self):
        # the design adds no dropdown to this tab: Custom Slide Show and Record only look like splits (the dialog,
        # and a placeholder), so no command of the page has a menu controller in Controller.xcu
        src = Path(os.environ["TDOC"]).parents[3]
        controllers = (src / "officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu").read_text(
            encoding="utf-8")
        layout = self.motion_layout("slideshow")
        urls = {item.get("action", ".uno:" + item["cmd"]) for section in layout["sections"]
                for column in section["columns"] for box in column for item in box["items"]}
        self.assertEqual(9, len(urls))
        for url in urls:
            self.assertNotIn('<value>%s</value>' % url, controllers, url)

    def test_slideshow_hide_slide_toggles_the_current_slide(self):
        # design decision 28, ruling 23: Hide Slide is a toggle, as PowerPoint's is. From Normal view it hides the
        # current slide and then reports checked and stays enabled; a second press shows the slide again
        # (SlsSlotManager.cxx, FuTemporary and GetMenuState). Show Slide (Slide > Show Slide in the menu bar) still
        # shows a hidden slide, and is disabled while the slide is shown.
        def hide_slide():
            status = self.dispatch_status("HideSlide")
            return status.enabled, bool(status.state)

        with self.impress_doc() as document:
            self.xUITest.executeCommand(".uno:InsertPage")
            self.wait_for(lambda: document.DrawPages.Count == 2, "no second slide")
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assertEqual((True, False), self.settle(hide_slide))
            slide = document.CurrentController.CurrentPage
            other = document.DrawPages[0] if slide.Number == 2 else document.DrawPages[1]
            self.assertTrue(slide.Visible)
            self.xUITest.executeCommand(".uno:HideSlide")
            self.wait_for(lambda: not slide.Visible, "Hide Slide did not hide the current slide")
            self.assertTrue(other.Visible)
            self.assertEqual((True, True), self.settle(hide_slide), "a hidden slide: Hide Slide enabled and checked")
            self.xUITest.executeCommand(".uno:HideSlide")  # the second press shows the slide again
            self.wait_for(lambda: slide.Visible, "a second Hide Slide did not show the slide again")
            self.assertTrue(other.Visible)
            self.assertEqual((True, False), self.settle(hide_slide))
            self.assertFalse(self.settle(lambda: self.dispatch_enabled("ShowSlide")))
            self.xUITest.executeCommand(".uno:HideSlide")
            self.wait_for(lambda: not slide.Visible, "Hide Slide did not hide the slide a second time")
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("ShowSlide")))
            self.xUITest.executeCommand(".uno:ShowSlide")
            self.wait_for(lambda: slide.Visible, "Show Slide did not show the slide again")
            self.assertTrue(other.Visible)
            self.assertEqual((True, False), self.settle(hide_slide))

    def test_slideshow_set_up_controls_open_the_set_up_slide_show_dialog(self):
        # Use Timings, Monitor and Use Presenter View each run .uno:PresentationDialog (decision 25). The headless
        # window clips the ribbon, so each box is looked up by id and the real URL is dispatched.
        layout = self.motion_layout("slideshow")
        controls = [(box["id"], item["cmd"]) for section in layout["sections"] for column in section["columns"]
                    for box in column for item in box["items"]
                    if item.get("action") == ".uno:PresentationDialog"]
        self.assertEqual(["UseTimings", "Monitor", "UsePresenterView"], [box for box, _ in controls])
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                self.assertTrue(self.settle(lambda: self.dispatch_enabled("PresentationDialog")))
                for box, cmd in controls:
                    xBox = xImpressDoc.getChild("bxSlideShow" + box)
                    self.assertEqual("1", get_state_as_dict(xBox)["ItemCount"], cmd)
                    with self.ui_test.execute_dialog_through_command(".uno:PresentationDialog",
                                                                     close_button="cancel") as xDialog:
                        self.assertIsNotNone(xDialog.getChild("manualslides"), cmd)  # Set Up Slide Show
            finally:
                self.switch_to("Default")

    def test_slideshow_start_buttons_are_enabled_without_starting_the_show(self):
        with self.impress_doc():
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            for name in ("Presentation", "PresentationCurrentSlide", "PresentationDialog", "CustomShowDialog",
                         "RehearseTimings", "HideSlide"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)

    def test_slideshow_placeholders_are_disabled_and_inert(self):
        # 2 slots: Record and the Option family (Play Narrations, Show Media Controls)
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in SLIDESHOW_SLOTS)
        self.assertEqual(3, len(names))
        with self.impress_doc() as document:
            slide = document.DrawPages[0]
            slide.getByIndex(0).String = "keep"
            document.setModified(False)
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assert_disabled_and_inert(names)
            self.assertEqual(1, document.DrawPages.Count)
            self.assertEqual("keep", slide.getByIndex(0).String)
            self.assertFalse(document.isModified())

    def test_slideshow_placeholder_labels_resolve(self):
        with self.impress_doc():
            for command, label in (("SlideShowRecord", "Record"),
                                   ("SlideShowOption?Option:string=narrations", "Play Narrations"),
                                   ("SlideShowOption?Option:string=mediacontrols", "Show Media Controls")):
                self.assertEqual(label, self.command_label(".uno:" + command), command)

    def test_slideshow_ribbon_shows_powerpoints_labels(self):
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                labels = {"bxSlideShowFromBeginning": "From Beginning",
                          "bxSlideShowFromCurrentSlide": "From Current Slide",
                          "bxSlideShowCustomSlideShow": "Custom Slide Show",
                          "bxSlideShowSetUpSlideShow": "Set Up Slide Show", "bxSlideShowHideSlide": "Hide Slide",
                          "bxSlideShowRehearseTimings": "Rehearse Timings", "bxSlideShowRecord": "Record",
                          "bxSlideShowPlayNarrations": "Play Narrations", "bxSlideShowUseTimings": "Use Timings",
                          "bxSlideShowShowMediaControls": "Show Media Controls", "bxSlideShowMonitor": "Monitor",
                          "bxSlideShowUsePresenterView": "Use Presenter View"}
                got = self.settle(lambda: {box: get_state_as_dict(
                    xImpressDoc.getChild(box).getChild("toolboxitem-1"))["Text"] for box in labels})
                self.assertEqual(labels, got)
            finally:
                self.switch_to("Default")

    def review_comments(self, slide):
        """The text of every comment on `slide`, in order."""
        xEnum = slide.createAnnotationEnumeration()
        texts = []
        while xEnum.hasMoreElements():
            texts.append(xEnum.nextElement().TextRange.String)
        return texts

    def add_comments(self, document, count):
        """`count` comments c1, c2, ... on the first slide; none is selected."""
        slide = document.DrawPages[0]
        for number in range(1, count + 1):
            comment = slide.createAndInsertAnnotation()
            comment.Author = "reviewer"
            comment.Position = uno.createUnoStruct("com.sun.star.geometry.RealPoint2D", 1.0 * number, 1.0)
            comment.TextRange.String = "c%d" % number
        self.assertEqual(["c%d" % n for n in range(1, count + 1)], self.review_comments(slide))
        return slide

    def test_review_sections_and_toolboxes(self):
        self.check_sections_and_toolboxes(self.motion_layout("review"), 6)

    def test_review_tab_is_visible_with_a_text_box_a_shape_a_table_and_an_image_selected(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Review")
            finally:
                self.switch_to("Default")

    def test_review_dropdown_popups_list_their_items_through_the_real_controllers(self):
        with self.impress_doc():
            expected = {
                ("ReviewLanguageMenu", "review_language"): [
                    ".uno:SetLanguageAllTextMenu", ".uno:Hyphenation", ".uno:ChineseConversion",
                    ".uno:HangulHanjaConversion", ".uno:MoreDictionaries"],
                ("ReviewDeleteCommentMenu", "review_deletecomment"): [
                    ".uno:DeleteAnnotation", ".uno:DeleteAllAnnotation"]}
            for (command, resource), items in expected.items():
                xPopup = self.menu_controller(".uno:" + command, resource)
                self.assertEqual(items, self.popup_commands(xPopup), command)

    def test_review_language_menu_first_item_opens_the_language_submenu_its_controller_builds(self):
        # decision 18: .uno:SetLanguageAllTextMenu keeps LanguageSelectionMenuController (Controller.xcu:155),
        # which fills the submenu with the languages of the document
        with self.impress_doc():
            xPopup = self.menu_controller(".uno:ReviewLanguageMenu", "review_language")
            first = xPopup.getItemId(0)
            self.assertEqual(".uno:SetLanguageAllTextMenu", xPopup.getCommand(first))
            # the awt popup has no submenu until the menu is activated on screen, so the controller of the item is
            # created by its own command, as the menu does when it opens the submenu
            xSub = self.menu_controller(".uno:SetLanguageAllTextMenu", "")
            languages = self.settle(lambda: xSub.getItemCount())
            self.assertGreater(languages, 0, "the language submenu is empty")

    def test_review_previous_and_next_move_between_the_comments_of_a_slide(self):
        # which comment is selected shows in what Delete removes (SID_DELETE_POSTIT deletes the selected one).
        # One document per probe: a delete leaves the removed comment selected, and Next from there would ask
        # a modal question about wrapping around. Next/Previous never go past the ends here for the same reason.
        def probe(moves, left):
            with self.impress_doc() as document:
                slide = self.add_comments(document, 3)
                self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
                self.assertTrue(self.settle(lambda: self.dispatch_enabled("NextAnnotation")))
                self.assertTrue(self.settle(lambda: self.dispatch_enabled("PreviousAnnotation")))
                self.assertFalse(self.dispatch_enabled("DeleteAnnotation"), "a comment is selected at the start")
                for move in moves:
                    self.xUITest.executeCommand(".uno:" + move)
                self.assertTrue(self.settle(lambda: self.dispatch_enabled("DeleteAnnotation")), moves)
                self.xUITest.executeCommand(".uno:DeleteAnnotation")
                self.wait_for(lambda: len(self.review_comments(slide)) == 2, "Delete did not remove a comment")
                self.assertEqual(left, self.review_comments(slide), moves)
        probe(["NextAnnotation"], ["c2", "c3"])  # none selected: Next selects the first
        probe(["NextAnnotation", "NextAnnotation"], ["c1", "c3"])  # Next moves on to the second
        probe(["PreviousAnnotation"], ["c1", "c2"])  # none selected: Previous selects the last
        probe(["NextAnnotation", "NextAnnotation", "PreviousAnnotation"], ["c2", "c3"])  # and back to the first

    def test_review_delete_menu_deletes_one_comment_then_all(self):
        with self.impress_doc() as document:
            slide = self.add_comments(document, 3)
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            xPopup = self.menu_controller(".uno:ReviewDeleteCommentMenu", "review_deletecomment")
            one, everything = self.popup_commands(xPopup)
            self.assertEqual((".uno:DeleteAnnotation", ".uno:DeleteAllAnnotation"), (one, everything))
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("NextAnnotation")))
            self.xUITest.executeCommand(".uno:NextAnnotation")  # selects c1
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("DeleteAnnotation")))
            self.xUITest.executeCommand(one)
            self.wait_for(lambda: len(self.review_comments(slide)) == 2, "the first item did not delete one comment")
            self.assertEqual(["c2", "c3"], self.review_comments(slide))
            self.assertTrue(self.settle(lambda: self.dispatch_enabled("DeleteAllAnnotation")))
            self.xUITest.executeCommand(everything)
            self.wait_for(lambda: self.review_comments(slide) == [], "the second item did not delete all comments")
            self.assertFalse(self.settle(lambda: self.dispatch_enabled("DeleteAllAnnotation")))

    def test_review_placeholders_are_disabled_and_inert(self):
        # 4 slots: Check Accessibility, Translate, the Compare family (7 variants) and Hide Ink
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in REVIEW_SLOTS)
        self.assertEqual(10, len(names))
        with self.impress_doc() as document:
            slide = document.DrawPages[0]
            slide.getByIndex(0).String = "keep"
            document.setModified(False)
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assert_disabled_and_inert(names)
            self.assertEqual(1, document.DrawPages.Count)
            self.assertEqual("keep", slide.getByIndex(0).String)
            self.assertFalse(document.isModified())

    def test_review_dropdown_and_placeholder_labels_resolve(self):
        compare = "ReviewCompare?Action:string="
        with self.impress_doc():
            for command, label in (("ReviewLanguageMenu", "Language"), ("ReviewDeleteCommentMenu", "Delete Comments"),
                                   ("ReviewCheckAccessibility", "Check Accessibility"),
                                   ("ReviewTranslate", "Translate"), ("ReviewHideInk", "Hide Ink"),
                                   (compare + "compare", "Compare"), (compare + "accept", "Accept"),
                                   (compare + "reject", "Reject"), (compare + "previous", "Previous"),
                                   (compare + "next", "Next"), (compare + "pane", "Reviewing Pane"),
                                   (compare + "endreview", "End Review")):
                self.assertEqual(label, self.command_label(".uno:" + command), command)

    def test_review_commands_that_are_real_are_enabled(self):
        with self.impress_doc():
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            # Thesaurus needs a text in edit mode (reported disabled with nothing selected)
            for name in ("SpellDialog", "InsertAnnotation", "ShowAnnotations", "Hyphenation", "MoreDictionaries"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)

    def test_review_ribbon_shows_powerpoints_labels(self):
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                labels = {"bxReviewSpelling": "Spelling", "bxReviewThesaurus": "Thesaurus",
                          "bxReviewCheckAccessibility": "Check Accessibility", "bxReviewTranslate": "Translate",
                          "bxReviewLanguage": "Language", "bxReviewNewComment": "New Comment",
                          "bxReviewDeleteComment": "Delete", "bxReviewCommentPrevious": "Previous",
                          "bxReviewCommentNext": "Next", "bxReviewShowComments": "Show Comments",
                          "bxReviewCompare": "Compare", "bxReviewAccept": "Accept", "bxReviewReject": "Reject",
                          "bxReviewComparePrevious": "Previous", "bxReviewCompareNext": "Next",
                          "bxReviewReviewingPane": "Reviewing Pane", "bxReviewEndReview": "End Review",
                          "bxReviewHideInk": "Hide Ink"}
                got = self.settle(lambda: {box: get_state_as_dict(
                    xImpressDoc.getChild(box).getChild("toolboxitem-1"))["Text"] for box in labels})
                self.assertEqual(labels, got)
            finally:
                self.switch_to("Default")

    def test_view_sections_and_toolboxes(self):
        self.check_sections_and_toolboxes(self.motion_layout("view"), 7)

    def test_help_sections_and_toolboxes(self):
        self.check_sections_and_toolboxes(self.motion_layout("help"), 1)

    def test_view_tab_is_visible_with_a_text_box_a_shape_a_table_and_an_image_selected(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "View")
            finally:
                self.switch_to("Default")

    def test_help_tab_is_visible_with_a_text_box_a_shape_a_table_and_an_image_selected(self):
        with self.impress_doc() as document:
            self.switch_to(OFFICE_UI)
            try:
                self.check_tab_in_every_context(document, "Help")
            finally:
                self.switch_to("Default")

    def experimental_mode(self):
        provider = self.xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.configuration.ConfigurationProvider", self.xContext)
        access = provider.createInstanceWithArguments(
            "com.sun.star.configuration.ConfigurationAccess",
            (PropertyValue(Name="nodepath", Value="/org.openoffice.Office.Common/Misc"),))
        return bool(access.getByName("ExperimentalMode"))

    def test_view_dropdown_popups_list_their_items_through_the_real_controllers(self):
        with self.impress_doc():
            xPopup = self.menu_controller(".uno:ViewColorGrayscaleMenu", "view_colorgrayscale")
            self.assertEqual([".uno:OutputQualityColor", ".uno:OutputQualityGrayscale",
                              ".uno:OutputQualityBlackWhite"], self.popup_commands(xPopup))
            # Macro Manager is flagged experimental (GenericCommands.xcu): the framework drops it from the menu
            # unless experimental mode is on, as it does in Calc, in Writer and in Tools > Macros
            expected = [".uno:RunMacro", ".uno:MacroRecorder", ".uno:BasicIDEAppear"]
            if self.experimental_mode():
                expected.insert(2, ".uno:MacroManager")
            xPopup = self.menu_controller(".uno:ViewMacrosMenu", "view_macros")
            self.assertEqual(expected, self.popup_commands(xPopup))

    def window_count(self, document):
        xEnum = document.getControllers()
        count = 0
        while xEnum.hasMoreElements():
            xEnum.nextElement()
            count += 1
        return count

    def test_view_switch_windows_lists_the_two_open_windows(self):
        # the framework's window list, registered under the new command and without a popup file, lists the open
        # windows when the dropdown opens. New Window gives a second window of the same Impress document.
        with self.impress_doc() as document:
            self.assertEqual(1, self.window_count(document))
            self.xUITest.executeCommand(".uno:NewWindow")
            try:
                self.wait_for(lambda: self.window_count(document) == 2, "New Window did not open a second window", 15)
                xPopup, xController = self.menu_controller(".uno:ViewSwitchWindowsMenu", None, with_controller=True)
                event = uno.createUnoStruct("com.sun.star.awt.MenuEvent")
                event.Source = xPopup
                xController.itemActivated(event)
                windows = [xPopup.getItemId(pos) for pos in range(xPopup.getItemCount())
                           if 4600 <= xPopup.getItemId(pos) <= 4699]
                texts = sorted(xPopup.getItemText(nId) for nId in windows)
                self.assertEqual(2, len(windows), texts)
                self.assertEqual(1, sum(1 for nId in windows if xPopup.isItemChecked(nId)), "the active window")
            finally:
                # close the second window only (the active one), so the document keeps its first window
                if self.window_count(document) == 2:
                    self.xUITest.executeCommand(".uno:CloseWin")
                    self.wait_for(lambda: self.window_count(document) == 1, "the second window did not close", 15)

    def test_view_buttons_switch_the_view_and_normal_brings_it_back(self):
        # Normal, Outline View, Slide Sorter and Notes Page: each command reports its view as its state
        with self.impress_doc() as document:
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            for name in ("OutlineMode", "DiaMode", "NotesMode"):
                self.xUITest.executeCommand(".uno:" + name)
                self.wait_for(lambda: self.dispatch_status(name).state is True, "no view for " + name, 10)
                self.assertTrue(self.settle(lambda: self.dispatch_status(name).state), name)
                self.assertFalse(self.dispatch_status("NormalMultiPaneGUI").state, name)
                self.xUITest.executeCommand(".uno:NormalMultiPaneGUI")
                self.wait_for(lambda: self.dispatch_status("NormalMultiPaneGUI").state is True,
                              "Normal did not bring the view back from " + name, 10)
                self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state), name)
                self.assertFalse(self.dispatch_status(name).state, name)

    def test_view_color_grayscale_switches_to_grayscale_and_back(self):
        with self.impress_doc():
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assertTrue(self.settle(lambda: self.dispatch_status("OutputQualityColor").state))
            self.xUITest.executeCommand(".uno:OutputQualityGrayscale")
            self.wait_for(lambda: self.dispatch_status("OutputQualityGrayscale").state is True,
                          "the view did not switch to grayscale", 10)
            self.assertFalse(self.dispatch_status("OutputQualityColor").state)
            self.xUITest.executeCommand(".uno:OutputQualityColor")
            self.wait_for(lambda: self.dispatch_status("OutputQualityColor").state is True,
                          "the view did not switch back to color", 10)
            self.assertFalse(self.dispatch_status("OutputQualityGrayscale").state)

    def test_view_and_help_placeholders_are_disabled_and_inert(self):
        # 5 URLs on 5 slots: Reading View (the ViewMode family), Arrange All, Cascade, Move Split and Feedback
        src = Path(os.environ["TDOC"]).parents[3]
        names = placeholder_urls(src, lambda e: e["offset"] in VIEW_SLOTS + HELP_SLOTS)
        self.assertEqual(5, len(names))
        with self.impress_doc() as document:
            slide = document.DrawPages[0]
            slide.getByIndex(0).String = "keep"
            document.setModified(False)
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            self.assert_disabled_and_inert(names)
            self.assertEqual(1, document.DrawPages.Count)
            self.assertEqual("keep", slide.getByIndex(0).String)
            self.assertFalse(document.isModified())

    def test_view_and_help_dropdown_and_placeholder_labels_resolve(self):
        with self.impress_doc():
            for url, label in ((".uno:ViewColorGrayscaleMenu", "Color/Grayscale"),
                               (".uno:ViewSwitchWindowsMenu", "Switch Windows"), (".uno:ViewMacrosMenu", "Macros"),
                               (".uno:ViewMode?Mode:string=reading", "Reading View"),
                               (".uno:ViewArrangeAll", "Arrange All"), (".uno:ViewCascade", "Cascade"),
                               (".uno:ViewSplit", "Move Split"), (".uno:HelpFeedback", "Feedback")):
                self.assertEqual(label, self.command_label(url), url)

    def test_view_and_help_commands_that_are_real_are_enabled(self):
        # Left out on purpose: MacroManager (hidden unless experimental mode is on)
        with self.impress_doc():
            self.assertTrue(self.settle(lambda: self.dispatch_status("NormalMultiPaneGUI").state))
            for name in ("NormalMultiPaneGUI", "OutlineMode", "DiaMode", "NotesMode", "SlideMasterPage",
                         "HandoutMode", "NotesMasterPage", "ShowRuler", "GridVisible", "HelplinesVisible",
                         "BottomPaneImpress", "Zoom", "ZoomPage", "OutputQualityColor", "OutputQualityGrayscale",
                         "OutputQualityBlackWhite", "NewWindow", "RunMacro", "MacroRecorder", "BasicIDEAppear",
                         "HelpIndex", "QuestionAnswers", "Documentation", "WhatsNew"):
                self.assertTrue(self.settle(lambda: self.dispatch_enabled(name)), name)

    def test_help_buttons_are_drawn_enabled_except_the_feedback_placeholder(self):
        # what the ribbon draws: the toolboxitem's Enabled. Nothing is pressed: the buttons open the help and a browser.
        layout = self.motion_layout("help")
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                drawn = {}
                for section in layout["sections"]:
                    for column in section["columns"]:
                        for box in column:
                            xBox = xImpressDoc.getChild("bx" + layout["id_prefix"] + box["id"])
                            drawn[box["items"][0]["cmd"]] = xBox.getChild("toolboxitem-1")
                self.assertEqual(5, len(drawn))
                self.wait_for(lambda: all((get_state_as_dict(x)["Enabled"] == "false") == (cmd == "HelpFeedback")
                                          for cmd, x in drawn.items()),
                              "Help buttons not drawn as designed: " + str(
                                  {c: get_state_as_dict(x)["Enabled"] for c, x in drawn.items()}))
            finally:
                self.switch_to("Default")

    def test_view_and_help_ribbon_shows_powerpoints_labels(self):
        with self.impress_doc():
            self.switch_to(OFFICE_UI)
            try:
                xImpressDoc = self.xUITest.getTopFocusWindow()
                # Arrange All, Cascade and Move Split are icon-only (design size I): no caption to read
                labels = {"bxViewNormal": "Normal", "bxViewOutlineView": "Outline View",
                          "bxViewSlideSorter": "Slide Sorter", "bxViewNotesPage": "Notes Page",
                          "bxViewReadingView": "Reading View", "bxViewSlideMaster": "Slide Master",
                          "bxViewHandoutMaster": "Handout Master", "bxViewNotesMaster": "Notes Master",
                          "bxViewRuler": "Ruler", "bxViewGridlines": "Gridlines", "bxViewGuides": "Guides",
                          "bxViewNotes": "Notes", "bxViewZoom": "Zoom", "bxViewFitToWindow": "Fit to Window",
                          "bxViewColorGrayscale": "Color/Grayscale", "bxViewNewWindow": "New Window",
                          "bxViewSwitchWindows": "Switch Windows", "bxViewMacros": "Macros",
                          "bxHelpHelp": "Help", "bxHelpContactSupport": "Contact Support",
                          "bxHelpFeedback": "Feedback", "bxHelpShowTraining": "Show Training",
                          "bxHelpWhatsNew": "What's New"}
                got = self.settle(lambda: {box: get_state_as_dict(
                    xImpressDoc.getChild(box).getChild("toolboxitem-1"))["Text"] for box in labels})
                self.assertEqual(labels, got)
            finally:
                self.switch_to("Default")

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

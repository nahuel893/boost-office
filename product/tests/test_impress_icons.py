# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Icon coverage of Impress's Home tab: every command of the generated page has an icon in both themes, at the
sizes the tab uses (the same contract as test_writer_icons.py has for Writer's tabs). The design folds this into
test_icons.py later."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from product.icons import build_theme as bt
from product.tests import test_icons as calc_icons
from product.tests.test_icons import LARGE_ICON_SIZE
from product.tests.test_writer_icons import image_commands
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
OFFICE = ROOT / "sd/uiconfig/simpress/ui/notebookbar_office.ui"


def tab_page(tab):
    text = OFFICE.read_text(encoding="utf-8")
    body = text.split(f"<!-- product:{tab}-begin -->")[1].split(f"<!-- product:{tab}-end -->")[0]
    return ET.fromstring("<root>" + body + "</root>")


class _ImpressTabIcons:
    TAB = "Home"
    SELF_DRAWN = frozenset()  # commands whose toolbox control paints its own widget, not a command image

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.zips = bt.build(bt.load_manifest(), Path(cls.tmp.name))["zips"]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def members(self, theme):
        with zipfile.ZipFile(self.zips[theme]) as z:
            names = set(z.namelist())
            links = {}
            if "links.txt" in names:
                for line in z.read("links.txt").decode().splitlines():
                    if line.strip():
                        alias, target = line.split()
                        links[alias] = target
        return names, links

    def missing(self):
        missing = []
        for box in tab_page(self.TAB).iter("object"):
            if box.get("class") != "sfxlo-NotebookbarToolBox":
                continue
            large = box.find("property[@name='icon_size']").text == LARGE_ICON_SIZE
            for button in box.findall("child/object"):
                icon = button.find("property[@name='icon_name']")
                if icon is not None:
                    wanted = [icon.text]
                else:
                    cmd = button.find("property[@name='action-name']").text.removeprefix(".uno:").lower()
                    if cmd in calc_icons.LIST_BOX_COMMANDS | self.SELF_DRAWN:
                        continue
                    wanted = [f"cmd/sc_{cmd}.png", f"cmd/lc_{cmd}.png"] + ([f"cmd/32/{cmd}.png"] if large else [])
                for theme in self.zips:
                    names, links = self.members(theme)
                    missing += [f"{theme}:{m}" for m in wanted if m not in names and links.get(m) not in names]
        return missing

    def test_the_page_has_a_button_for_every_layout_item(self):
        layout = json.loads((ROOT / f"product/ui/impress_{self.TAB.lower()}.json").read_text(encoding="utf-8"))
        items = sum(len(b["items"]) for s in layout["sections"] for b in g.boxes_of(s))
        buttons = sum(len(box.findall("child/object")) for box in tab_page(self.TAB).iter("object")
                      if box.get("class") == "sfxlo-NotebookbarToolBox")
        self.assertGreater(items, 0)
        self.assertEqual(items, buttons)

    def test_every_button_has_an_icon_in_both_themes(self):
        self.assertEqual(["boost", "boost_dark"], sorted(self.zips))
        self.assertEqual([], self.missing())

    def test_every_button_without_an_icon_name_has_a_command_image(self):
        # Impress's image manager looks a command up in DrawImpressCommands.xcu, then in the generic one:
        # a command in neither renders a blank button.
        listed = image_commands("DrawImpressCommands.xcu") | image_commands("GenericCommands.xcu")
        blank = []
        for button in tab_page(self.TAB).iter("object"):
            action = button.find("property[@name='action-name']")
            if action is None or button.find("property[@name='icon_name']") is not None:
                continue
            if action.text.removeprefix(".uno:").lower() in calc_icons.LIST_BOX_COMMANDS | self.SELF_DRAWN:
                continue
            if action.text not in listed:
                blank.append(action.text)
        self.assertEqual([], blank)

    def test_reset_and_quick_styles_name_their_own_icons(self):
        # `?` URLs and the deck opener have no command image: Reset must not reuse the Layout icon.
        icons = {}
        for button in tab_page(self.TAB).iter("object"):
            icon = button.find("property[@name='icon_name']")
            if icon is not None:
                icons[button.get("id")] = icon.text
        if self.TAB == "Home":
            self.assertEqual("cmd/sc_resetlayout.png", icons.get("btnHomeResetLayout"))
            self.assertEqual("cmd/32/sidebardeck.stylelistdeck.png", icons.get("btnHomeSidebarDeck.StyleListDeck"))


class ImpressHomeIconsTest(_ImpressTabIcons, unittest.TestCase):
    # The six default shape cells are popup controllers: each draws the image of its default sub-shape (the
    # sub-command the stock Drawing toolbar lists first), so those sub-command names are themed, not the cell's.
    SHAPE_CELL_DEFAULTS = ("basicshapes.diamond", "symbolshapes.smiley", "arrowshapes.left-right-arrow",
                           "flowchartshapes.flowchart-process", "calloutshapes.round-rectangular-callout",
                           "starshapes.star5")

    def test_the_default_shape_cells_have_boost_icons_in_both_themes(self):
        for theme in sorted(self.zips):
            names, links = self.members(theme)
            for cmd in self.SHAPE_CELL_DEFAULTS:
                for member in (f"cmd/sc_{cmd}.png", f"cmd/lc_{cmd}.png"):
                    self.assertTrue(member in names or links.get(member) in names, f"{theme}:{member}")

    def test_the_default_shape_cell_entries_are_plain_line_icons(self):
        entries = {e["name"]: e for e in bt.load_manifest()["icons"]}
        for cmd in self.SHAPE_CELL_DEFAULTS:
            self.assertIn(cmd, entries)
            self.assertNotIn("fill", entries[cmd], cmd)
            self.assertEqual(1, len(entries[cmd]["layers"]), cmd)


class ImpressInsertIconsTest(_ImpressTabIcons, unittest.TestCase):
    TAB = "Insert"

    def test_video_and_audio_have_their_own_icons(self):
        # The two buttons share `.uno:InsertAVMedia` as their action but are distinct widgets (decision 16): each
        # names an explicit icon, and the two differ.
        icons = {}
        for button in tab_page(self.TAB).iter("object"):
            icon = button.find("property[@name='icon_name']")
            if icon is not None:
                icons[button.get("id")] = icon.text
        self.assertNotIn(icons.get("btnInsertInsertVideo"), (None, icons.get("btnInsertInsertAudio")))
        self.assertIsNotNone(icons.get("btnInsertInsertAudio"))


class ImpressDesignIconsTest(_ImpressTabIcons, unittest.TestCase):
    TAB = "Design"
    # The theme colors box (`.uno:ThemeSelectorPanel`) is a stock control that draws its own swatches.
    SELF_DRAWN = frozenset({"themeselectorpanel"})

    def icon_names(self):
        icons = {}
        for button in tab_page(self.TAB).iter("object"):
            icon = button.find("property[@name='icon_name']")
            if icon is not None:
                icons[button.get("id")] = icon.text
        return icons

    def test_the_deck_openers_name_their_own_icons(self):
        # `.uno:SidebarDeck.*` has no command image bit (Quick Styles on Home does the same): Themes and Format
        # Background name a 32 px icon each, and the two differ.
        icons = self.icon_names()
        themes = icons.get("btnDesignSidebarDeck.SdMasterPagesDeck")
        background = icons.get("btnDesignSidebarDeck.PropertyDeck")
        self.assertEqual("cmd/32/sidebardeck.sdmasterpagesdeck.png", themes)
        self.assertEqual("cmd/32/sidebardeck.propertydeck.png", background)

    def test_the_variants_menu_items_have_icons_in_both_themes(self):
        # The popup's items draw their command image: the `?` placeholders look it up by the canonical name
        # CommandImageResolver derives from the URL (`:` and `?` escaped, lower case), so each needs an alias.
        popup = ROOT / "sd/uiconfig/simpress/popupmenu/design_variants.xml"
        urls = [e.get("{http://openoffice.org/2001/menu}id") for e in ET.parse(popup).iter()
                if e.get("{http://openoffice.org/2001/menu}id")]
        self.assertEqual(4, len(urls))
        missing = []
        for url in urls:
            name = url.removeprefix(".uno:").replace(":", "%3a").replace("?", "%3f").lower()
            for theme in self.zips:
                names, links = self.members(theme)
                for prefix in ("cmd/sc_", "cmd/lc_"):
                    member = f"{prefix}{name}.png"
                    if member not in names and links.get(member) not in names:
                        missing.append(f"{theme}:{member}")
        self.assertEqual([], missing)


class _DeckIcons(_ImpressTabIcons):
    """The Transitions and Animations controls that share one deck URL (or a `?` URL) name their own icons: a
    32 px icon for the large ones, a 16 px icon for the small ones, each different from the others."""
    LARGE = frozenset()
    SMALL = frozenset()

    def test_every_deck_control_names_its_own_icon(self):
        icons = {}
        for button in tab_page(self.TAB).iter("object"):
            icon = button.find("property[@name='icon_name']")
            if icon is not None:
                icons[button.get("id")] = icon.text
        self.assertEqual({f"btn{self.TAB}{c}" for c in self.LARGE | self.SMALL}, set(icons))
        for cmd in self.LARGE:
            self.assertRegex(icons[f"btn{self.TAB}{cmd}"], r"^cmd/32/[a-z]+\.png$")
        for cmd in self.SMALL:
            self.assertRegex(icons[f"btn{self.TAB}{cmd}"], r"^cmd/sc_[a-z]+\.png$")
        self.assertEqual(len(icons), len(set(icons.values())))


class ImpressTransitionsIconsTest(_DeckIcons, unittest.TestCase):
    TAB = "Transitions"
    LARGE = frozenset({"PreviewTransition", "TransitionStyles", "TransitionEffectOptions"})
    SMALL = frozenset({"TransitionSound", "TransitionDuration", "TransitionApplyToAll",
                       "TransitionOnMouseClick", "TransitionAfter"})


class ImpressAnimationsIconsTest(_DeckIcons, unittest.TestCase):
    TAB = "Animations"
    LARGE = frozenset({"PreviewAnimation", "AnimationStyles", "AnimationEffectOptions", "AddAnimation"})
    SMALL = frozenset({"AnimationTrigger", "AnimationStart", "AnimationDuration", "AnimationDelay",
                       "AnimationMoveEarlier", "AnimationMoveLater"})


class ImpressSlideShowIconsTest(_ImpressTabIcons, unittest.TestCase):
    TAB = "SlideShow"
    # The three controls that only open the Set Up Slide Show dialog and the two `?` variants share a URL with
    # another control: each names an explicit 16 px icon of its own.
    SMALL = frozenset({"PlayNarrations", "UseTimings", "ShowMediaControls", "Monitor", "UsePresenterView"})

    def test_the_shared_url_controls_name_their_own_icons(self):
        icons = {}
        for button in tab_page(self.TAB).iter("object"):
            icon = button.find("property[@name='icon_name']")
            if icon is not None:
                icons[button.get("id")] = icon.text
        self.assertEqual({f"btn{self.TAB}SlideShow{c}" for c in
                          ("PlayNarrations", "UseTimings", "ShowMediaControls", "Monitor", "PresenterView")},
                         set(icons))
        for icon in icons.values():
            self.assertRegex(icon, r"^cmd/sc_slideshow[a-z]+\.png$")
        self.assertEqual(len(icons), len(set(icons.values())))


class ImpressReviewIconsTest(_ImpressTabIcons, unittest.TestCase):
    TAB = "Review"
    # Check Accessibility, Previous and Next (the real comment commands) and the Compare family are the controls
    # without a command image of their own name: the `?` variants name an explicit icon (one per size), Previous
    # and Next reuse the comment-arrow icons Calc and Writer ship, and the placeholder Check Accessibility shares
    # Writer's accessibility icon through a link.
    EXPLICIT = {"btnReviewPreviousAnnotation": "cmd/32/reviewcommentprevious.png",
                "btnReviewNextAnnotation": "cmd/32/reviewcommentnext.png",
                "btnReviewReviewCompare": "cmd/sc_reviewcomparemenu.png", "btnReviewReviewCompareAccept": "cmd/sc_reviewacceptmenu.png",
                "btnReviewReviewCompareReject": "cmd/sc_reviewrejectmenu.png",
                "btnReviewReviewComparePrevious": "cmd/sc_reviewcomparemenu.png",
                "btnReviewReviewCompareNext": "cmd/sc_reviewcomparemenu.png",
                "btnReviewReviewComparePane": "cmd/sc_reviewcomparemenu.png",
                "btnReviewReviewCompareEndReview": "cmd/32/reviewcomparemenu.png"}

    def test_the_controls_without_a_command_image_name_their_icons(self):
        icons = {}
        for button in tab_page(self.TAB).iter("object"):
            icon = button.find("property[@name='icon_name']")
            if icon is not None:
                icons[button.get("id")] = icon.text
        self.assertEqual(self.EXPLICIT, icons)

    def test_check_accessibility_and_the_menu_commands_have_icons_in_both_themes(self):
        # Check Accessibility is the placeholder URL of the family slot (no zip member of its own name yet);
        # the dropdown commands and the two comment moves have their own members or links
        for theme in sorted(self.zips):
            names, links = self.members(theme)
            for member in ("cmd/sc_reviewcheckaccessibility.png", "cmd/lc_reviewcheckaccessibility.png",
                           "cmd/32/reviewcheckaccessibility.png", "cmd/sc_reviewlanguagemenu.png",
                           "cmd/32/reviewlanguagemenu.png", "cmd/sc_reviewdeletecommentmenu.png",
                           "cmd/32/reviewdeletecommentmenu.png"):
                self.assertTrue(member in names or links.get(member) in names, f"{theme}:{member}")


class ImpressViewIconsTest(_ImpressTabIcons, unittest.TestCase):
    TAB = "View"
    # The Reading View placeholder is a `?` URL: it names Writer's Read Mode icon (the same family) at 16 px.
    EXPLICIT = {"btnViewViewReadingView": "cmd/sc_viewmode_read.png"}

    def test_the_url_variant_names_its_icon(self):
        icons = {}
        for button in tab_page(self.TAB).iter("object"):
            icon = button.find("property[@name='icon_name']")
            if icon is not None:
                icons[button.get("id")] = icon.text
        self.assertEqual(self.EXPLICIT, icons)

    def test_the_views_the_dropdowns_and_the_placeholders_have_icons_in_both_themes(self):
        # the buttons draw a command image of their own name: the 16 px icons are what the small controls use,
        # the 32 px ones the large buttons. The items inside the Color/Grayscale and Macros menus keep the stock
        # images, as the menu items of every other tab and of Calc and Writer do.
        large = ("normalmultipanegui", "outlinemode", "bottompaneimpress", "zoom", "zoompage",
                 "viewcolorgrayscalemenu", "newwindow", "viewswitchwindowsmenu", "viewmacrosmenu")
        small = ("diamode", "notesmode", "slidemasterpage", "handoutmode", "notesmasterpage", "showruler",
                 "gridvisible", "helplinesvisible", "viewarrangeall", "viewcascade", "viewsplit")
        for theme in sorted(self.zips):
            names, links = self.members(theme)
            for member in [f"cmd/32/{c}.png" for c in large] + [f"cmd/sc_{c}.png" for c in small] \
                    + [f"cmd/lc_{c}.png" for c in small]:
                self.assertTrue(member in names or links.get(member) in names, f"{theme}:{member}")


class ImpressHelpIconsTest(_ImpressTabIcons, unittest.TestCase):
    TAB = "Help"

    def test_the_help_buttons_name_no_icon_and_use_the_command_images(self):
        # every Help button is a plain command: the image manager draws its image at 32 px (Feedback shares
        # Calc's and Writer's help-feedback icon)
        for button in tab_page(self.TAB).iter("object"):
            self.assertIsNone(button.find("property[@name='icon_name']"), button.get("id"))
        for theme in sorted(self.zips):
            names, links = self.members(theme)
            for command in ("helpindex", "questionanswers", "helpfeedback", "documentation", "whatsnew"):
                member = f"cmd/32/{command}.png"
                self.assertTrue(member in names or links.get(member) in names, f"{theme}:{member}")

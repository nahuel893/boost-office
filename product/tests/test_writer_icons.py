# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Icon coverage of Writer's Home, Insert, Design, Layout, References, Mailings, Review, View and Help tabs: every command of the generated page has an icon in both
themes, at the sizes the tab uses (the same contract as test_icons.py has for Calc's tabs)."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from product.icons import build_theme as bt
from product.tests import test_icons as calc_icons
from product.tests.test_icons import LARGE_ICON_SIZE
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
OFFICE = ROOT / "sw/uiconfig/swriter/ui/notebookbar_office.ui"
COMMANDS = ROOT / "officecfg/registry/data/org/openoffice/Office/UI"
OOR = "{http://openoffice.org/2001/registry}"


def image_commands(xcu):
    """The commands of a Commands.xcu whose Properties has the image bit (1). Only those are in the
    command image list (framework's uicommanddescription.cxx), so only those get their theme icon
    from the command; any other command shows a blank button unless the .ui names an icon."""
    commands = set()
    for node in ET.parse(COMMANDS / xcu).iter("node"):
        for prop in node.findall("prop"):
            if prop.get(OOR + "name") == "Properties" and int(prop.find("value").text) & 1:
                commands.add(node.get(OOR + "name"))
    return commands


def tab_page(tab):
    text = OFFICE.read_text(encoding="utf-8")
    body = text.split(f"<!-- product:{tab}-begin -->")[1].split(f"<!-- product:{tab}-end -->")[0]
    return ET.fromstring("<root>" + body + "</root>")


def home_page():
    return tab_page("Home")


class _WriterTabIcons:
    TAB = "Home"

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
                    if cmd in calc_icons.LIST_BOX_COMMANDS:
                        continue
                    wanted = [f"cmd/sc_{cmd}.png", f"cmd/lc_{cmd}.png"] + ([f"cmd/32/{cmd}.png"] if large else [])
                for theme in self.zips:
                    names, links = self.members(theme)
                    missing += [f"{theme}:{m}" for m in wanted if m not in names and links.get(m) not in names]
        return missing

    def test_the_page_has_a_button_for_every_layout_item(self):
        # the buttons of the page's toolboxes, against the items of the tab's layout file
        layout = json.loads((ROOT / f"product/ui/writer_{self.TAB.lower()}.json").read_text(encoding="utf-8"))
        items = sum(len(b["items"]) for s in layout["sections"] for b in g.boxes_of(s))
        buttons = sum(len(box.findall("child/object")) for box in tab_page(self.TAB).iter("object")
                      if box.get("class") == "sfxlo-NotebookbarToolBox")
        self.assertGreater(items, 0)
        self.assertEqual(items, buttons)

    def test_every_button_has_an_icon_in_both_themes(self):
        self.assertEqual(["boost", "boost_dark"], sorted(self.zips))
        self.assertEqual([], self.missing())

    def test_every_button_without_an_icon_name_has_a_command_image(self):
        # Writer's image manager looks a command up in Writer's command image list, then in the
        # generic one: a command in neither renders a blank button (Drop Caps, Show Notes, Labels).
        listed = image_commands("WriterCommands.xcu") | image_commands("GenericCommands.xcu")
        blank = []
        for button in tab_page(self.TAB).iter("object"):
            action = button.find("property[@name='action-name']")
            if action is None or button.find("property[@name='icon_name']") is not None:
                continue
            if action.text.removeprefix(".uno:").lower() in calc_icons.LIST_BOX_COMMANDS:
                continue
            if action.text not in listed:
                blank.append(action.text)
        self.assertEqual([], blank)


class WriterHomeIconsTest(_WriterTabIcons, unittest.TestCase):
    pass


class WriterInsertIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "Insert"


class WriterDesignIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "Design"


class WriterLayoutIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "Layout"


class WriterReferencesIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "References"


class WriterMailingsIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "Mailings"


class WriterReviewIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "Review"


class WriterViewIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "View"


class WriterHelpIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "Help"

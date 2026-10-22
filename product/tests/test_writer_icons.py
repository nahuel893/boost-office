# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Icon coverage of Writer's Home, Insert, Design, Layout and References tabs: every command of the generated page has an icon in both
themes, at the sizes the tab uses (the same contract as test_icons.py has for Calc's tabs)."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from product.icons import build_theme as bt
from product.tests import test_icons as calc_icons

ROOT = Path(__file__).resolve().parents[2]
OFFICE = ROOT / "sw/uiconfig/swriter/ui/notebookbar_office.ui"


def tab_page(tab):
    text = OFFICE.read_text(encoding="utf-8")
    body = text.split(f"<!-- product:{tab}-begin -->")[1].split(f"<!-- product:{tab}-end -->")[0]
    return ET.fromstring("<root>" + body + "</root>")


def home_page():
    return tab_page("Home")


class _WriterTabIcons:
    TAB = "Home"
    MIN_OBJECTS = 40

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
            large = box.find("property[@name='icon_size']").text == "5"
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

    def test_the_page_has_buttons(self):
        self.assertGreater(len(list(tab_page(self.TAB).iter("object"))), self.MIN_OBJECTS)

    def test_every_button_has_an_icon_in_both_themes(self):
        self.assertEqual(["boost", "boost_dark"], sorted(self.zips))
        self.assertEqual([], self.missing())


class WriterHomeIconsTest(_WriterTabIcons, unittest.TestCase):
    pass


class WriterInsertIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "Insert"
    MIN_OBJECTS = 20


class WriterDesignIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "Design"
    MIN_OBJECTS = 8


class WriterLayoutIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "Layout"
    MIN_OBJECTS = 20


class WriterReferencesIconsTest(_WriterTabIcons, unittest.TestCase):
    TAB = "References"
    MIN_OBJECTS = 15

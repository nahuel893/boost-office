# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from product.dev import profile

OOR = "{http://openoffice.org/2001/registry}"
APPEARANCE = "/org.openoffice.Office.Common/Appearance"
MISC = "/org.openoffice.Office.Common/Misc"
SCHEME = "/org.openoffice.Office.UI/ColorScheme"


def props(xml):
    root = ET.fromstring(xml)
    out = {}
    for item in root.findall("item"):
        prop = item.find("prop")
        out[(item.get(OOR + "path"), prop.get(OOR + "name"))] = prop.find("value").text
    return out


class ProfileTest(unittest.TestCase):

    def test_office_dark_with_theme(self):
        p = props(profile.render(profile.build_items(
            "office", "dark", icons="boost_dark", scheme="Boost Dark", tint=255)))
        self.assertEqual(p[(profile.CALC_APP, "Active")], "notebookbar_office.ui")
        self.assertEqual(p[(profile.TOOLBAR_MODE, "ActiveCalc")], "notebookbar_office.ui")
        self.assertEqual(p[(APPEARANCE, "ApplicationAppearance")], "2")
        self.assertEqual(p[(MISC, "SymbolStyle")], "boost_dark")
        self.assertEqual(p[(APPEARANCE, "LibreOfficeTheme")], "1")
        self.assertEqual(p[(SCHEME, "CurrentColorScheme")], "Boost Dark")
        self.assertEqual(p[(MISC, "NotebookbarColorTransparency")], "255")

    def test_baseline_has_no_theme_items(self):
        p = props(profile.render(profile.build_items("compact", "light")))
        self.assertEqual(p[(profile.CALC_APP, "Active")], "notebookbar_compact.ui")
        self.assertEqual(p[(APPEARANCE, "ApplicationAppearance")], "1")
        self.assertNotIn((APPEARANCE, "LibreOfficeTheme"), p)
        self.assertNotIn((MISC, "SymbolStyle"), p)
        self.assertNotIn((MISC, "NotebookbarColorTransparency"), p)

    def test_default_ui_sets_no_notebookbar_file(self):
        p = props(profile.render(profile.build_items("default", "light")))
        self.assertEqual(p[(profile.CALC_APP, "Active")], "Default")
        self.assertNotIn((profile.TOOLBAR_MODE, "ActiveCalc"), p)

    def test_write_creates_the_user_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = profile.write(Path(tmp), profile.build_items("tabbed", "light"))
            self.assertEqual(path, Path(tmp) / "user" / "registrymodifications.xcu")
            self.assertIn("<value>notebookbar.ui</value>", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

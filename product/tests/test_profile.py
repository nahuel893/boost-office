# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import contextlib
import io
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


class WriterProfileTest(unittest.TestCase):

    def test_writer_office_sets_the_writer_mode_and_file(self):
        p = props(profile.render(profile.build_items(
            "office", "light", icons="boost", scheme="Boost Light", tint=255, app="writer")))
        self.assertEqual(p[(profile.WRITER_APP, "Active")], "notebookbar_office.ui")
        self.assertEqual(p[(profile.TOOLBAR_MODE, "ActiveWriter")], "notebookbar_office.ui")
        self.assertEqual(p[(SCHEME, "CurrentColorScheme")], "Boost Light")

    def test_writer_writes_no_calc_mode(self):
        p = props(profile.render(profile.build_items("office", "dark", app="writer")))
        self.assertNotIn((profile.CALC_APP, "Active"), p)
        self.assertNotIn((profile.TOOLBAR_MODE, "ActiveCalc"), p)

    def test_writer_default_ui_sets_no_notebookbar_file(self):
        p = props(profile.render(profile.build_items("default", "light", app="writer")))
        self.assertEqual(p[(profile.WRITER_APP, "Active")], "Default")
        self.assertNotIn((profile.TOOLBAR_MODE, "ActiveWriter"), p)

    def test_the_writer_node_is_the_writer_application(self):
        self.assertEqual(profile.TOOLBAR_MODE + "/Applications/org.openoffice.Office.UI.ToolbarMode:"
                         "Application['Writer']", profile.WRITER_APP)

    def test_calc_is_the_default_app_and_its_output_is_unchanged(self):
        for ui in ("default", "compact", "tabbed", "office"):
            self.assertEqual(profile.render(profile.build_items(ui, "light", font="inter")),
                             profile.render(profile.build_items(ui, "light", font="inter", app="calc")), ui)

    def test_main_writes_the_writer_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                profile.main(["--app", "writer", "--ui", "office", "--appearance", "light", "--profile", tmp])
            p = props((Path(tmp) / "user/registrymodifications.xcu").read_text(encoding="utf-8"))
            self.assertEqual(p[(profile.WRITER_APP, "Active")], "notebookbar_office.ui")
            self.assertEqual(p[(profile.TOOLBAR_MODE, "ActiveWriter")], "notebookbar_office.ui")

    def test_unknown_app_is_refused(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            profile.main(["--app", "impress", "--ui", "office", "--appearance", "light", "--profile", "/nonexistent"])


if __name__ == "__main__":
    unittest.main()

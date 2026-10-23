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
            profile.main(["--app", "draw", "--ui", "office", "--appearance", "light", "--profile", "/nonexistent"])


IMPRESS_NEWDOC = "/org.openoffice.Office.Impress/Misc/NewDoc"


class ImpressProfileTest(unittest.TestCase):

    def test_impress_office_sets_the_impress_mode_and_file(self):
        p = props(profile.render(profile.build_items(
            "office", "light", icons="boost", scheme="Boost Light", tint=255, app="impress")))
        self.assertEqual(p[(profile.IMPRESS_APP, "Active")], "notebookbar_office.ui")
        self.assertEqual(p[(profile.TOOLBAR_MODE, "ActiveImpress")], "notebookbar_office.ui")
        self.assertEqual(p[(SCHEME, "CurrentColorScheme")], "Boost Light")

    def test_impress_writes_no_calc_or_writer_mode(self):
        p = props(profile.render(profile.build_items("office", "dark", app="impress")))
        for node, active in ((profile.CALC_APP, "ActiveCalc"), (profile.WRITER_APP, "ActiveWriter")):
            self.assertNotIn((node, "Active"), p)
            self.assertNotIn((profile.TOOLBAR_MODE, active), p)

    def test_impress_default_ui_sets_no_notebookbar_file(self):
        p = props(profile.render(profile.build_items("default", "light", app="impress")))
        self.assertEqual(p[(profile.IMPRESS_APP, "Active")], "Default")
        self.assertNotIn((profile.TOOLBAR_MODE, "ActiveImpress"), p)

    def test_the_impress_node_is_the_impress_application(self):
        self.assertEqual(profile.TOOLBAR_MODE + "/Applications/org.openoffice.Office.UI.ToolbarMode:"
                         "Application['Impress']", profile.IMPRESS_APP)

    def test_impress_turns_the_template_dialog_off_in_every_mode(self):
        # design decision 37: a new presentation opens without the template dialog
        for ui in ("default", "compact", "tabbed", "office"):
            p = props(profile.render(profile.build_items(ui, "light", app="impress")))
            self.assertEqual("false", p[(IMPRESS_NEWDOC, "AutoPilot")], ui)

    def test_calc_and_writer_get_no_template_dialog_item(self):
        for app in ("calc", "writer"):
            p = props(profile.render(profile.build_items("office", "light", app=app)))
            self.assertNotIn((IMPRESS_NEWDOC, "AutoPilot"), p, app)

    def test_the_template_dialog_item_is_the_impress_schema_property(self):
        # Misc/NewDoc/AutoPilot of org.openoffice.Office.Impress, a boolean that defaults to true
        schema = ET.parse(Path(__file__).resolve().parents[2]
                          / "officecfg/registry/schema/org/openoffice/Office/Impress.xcs")
        prop = schema.find("component/group[@{0}name='Misc']/group[@{0}name='NewDoc']"
                           "/prop[@{0}name='AutoPilot']".format(OOR))
        self.assertIsNotNone(prop)
        self.assertEqual("xs:boolean", prop.get(OOR + "type"))
        self.assertEqual("true", prop.findtext("value"))

    def test_main_writes_the_impress_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                profile.main(["--app", "impress", "--ui", "office", "--appearance", "light", "--profile", tmp])
            p = props((Path(tmp) / "user/registrymodifications.xcu").read_text(encoding="utf-8"))
            self.assertEqual(p[(profile.IMPRESS_APP, "Active")], "notebookbar_office.ui")
            self.assertEqual(p[(profile.TOOLBAR_MODE, "ActiveImpress")], "notebookbar_office.ui")
            self.assertEqual("false", p[(IMPRESS_NEWDOC, "AutoPilot")])


class MenuDefaultsTest(unittest.TestCase):

    def test_the_schema_shows_disabled_menu_entries_by_default(self):
        # T10: Office shows disabled entries greyed. The schema default already says so
        # (View/Menu/DontHideDisabledEntry), so a profile needs no override. The menu bar follows it
        # (framework's MenuBarManager), and so do the ribbon popups and context menus since W9d:
        # toolkit/source/awt/vclxmenu.cxx sets HideDisabledEntries on an awt PopupMenu::execute only
        # when this setting is false.
        schema = ET.parse(Path(__file__).resolve().parents[2]
                          / "officecfg/registry/schema/org/openoffice/Office/Common.xcs")
        props = [p for p in schema.iter("prop") if p.get(OOR + "name") == "DontHideDisabledEntry"]
        self.assertEqual(1, len(props))
        self.assertEqual("true", props[0].findtext("value"))


if __name__ == "__main__":
    unittest.main()

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Tabbed Office mode of Writer and Impress: their ToolbarMode nodes and the cui picker that offers it."""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
XCU = ROOT / "officecfg/registry/data/org/openoffice/Office/UI/ToolbarMode.xcu"
UITABPAGE = ROOT / "cui/source/dialogs/uitabpage.cxx"
UIPICKER = ROOT / "cui/source/dialogs/uipickerdlg.cxx"
OOR = "{http://openoffice.org/2001/registry}"


def modes(app):
    """The mode nodes of one application: {node name: {prop name: value text}}."""
    root = ET.parse(XCU).getroot()
    apps = root.find("node[@{0}name='Applications']".format(OOR))
    node = apps.find("node[@{0}name='{1}']/node[@{0}name='Modes']".format(OOR, app))
    out = {}
    for mode in node.findall("node"):
        out[mode.get(OOR + "name")] = {
            prop.get(OOR + "name"): " ".join(t.strip() for t in prop.find("value").itertext()).strip()
            for prop in mode.findall("prop")}
    return out


def function_body(text, signature):
    match = re.search(re.escape(signature) + r"[^{]*\{(.*?)\n\}", text, re.S)
    return match.group(1) if match else None


class WriterToolbarModeTest(unittest.TestCase):

    def test_writer_has_tabbed_office_at_menu_position_9(self):
        office = modes("Writer").get("TabbedOffice")
        self.assertIsNotNone(office, "Writer has no TabbedOffice mode")
        self.assertEqual("notebookbar_office.ui", office["CommandArg"])
        self.assertEqual("9", office["MenuPosition"])
        self.assertEqual("true", office["HasNotebookbar"])
        self.assertEqual("Tabbed Office", office["Label"])

    def test_the_writer_mode_is_a_copy_of_calcs(self):
        self.assertEqual(modes("Calc")["TabbedOffice"], modes("Writer").get("TabbedOffice"))

    def test_menu_position_9_is_free_in_writer_otherwise(self):
        positions = [m["MenuPosition"] for name, m in modes("Writer").items() if name != "TabbedOffice"]
        self.assertNotIn("9", positions)

    def test_draw_has_no_tabbed_office(self):
        # design decision 36: Draw shares sd but keeps its own notebookbar and no Tabbed Office mode
        self.assertNotIn("TabbedOffice", modes("Draw"))


class ImpressToolbarModeTest(unittest.TestCase):

    def test_impress_has_tabbed_office_at_menu_position_9(self):
        office = modes("Impress").get("TabbedOffice")
        self.assertIsNotNone(office, "Impress has no TabbedOffice mode")
        self.assertEqual("notebookbar_office.ui", office["CommandArg"])
        self.assertEqual("9", office["MenuPosition"])
        self.assertEqual("true", office["HasNotebookbar"])
        self.assertEqual("Tabbed Office", office["Label"])

    def test_the_impress_mode_is_a_copy_of_calcs(self):
        self.assertEqual(modes("Calc")["TabbedOffice"], modes("Impress").get("TabbedOffice"))

    def test_menu_position_9_is_free_in_impress_otherwise(self):
        positions = [m["MenuPosition"] for name, m in modes("Impress").items() if name != "TabbedOffice"]
        self.assertNotIn("9", positions)


class TabbedOfficePickerTest(unittest.TestCase):

    def setUp(self):
        self.tabpage = UITABPAGE.read_text(encoding="utf-8")
        self.picker = UIPICKER.read_text(encoding="utf-8")

    def test_one_helper_lists_calc_writer_and_impress_not_draw(self):
        body = function_body(self.tabpage, "bool UITabPage::HasTabbedOffice(std::u16string_view sApp)")
        self.assertIsNotNone(body, "no UITabPage::HasTabbedOffice helper")
        for app in ("Calc", "Writer", "Impress"):
            self.assertIn('u"%s"' % app, body, app)
        self.assertNotIn("Draw", body)

    def test_the_radio_button_and_the_mode_mapping_use_the_helper(self):
        self.assertIn("if (!HasTabbedOffice(sCurrentApp))", self.tabpage)
        mapping = function_body(self.tabpage, "OUString UITabPage::GetModeForApp(")
        self.assertIn("!HasTabbedOffice(sApp)", mapping)

    def test_the_calc_only_conditions_are_gone(self):
        self.assertNotIn('sCurrentApp != "Calc"', self.tabpage)
        self.assertNotIn('sApp != u"Calc"', self.tabpage)
        self.assertNotIn("only available in Calc", self.tabpage)
        self.assertNotIn("exists only for Calc", self.picker)
        # Apply to All maps every app through GetModeForApp, Calc included.
        self.assertNotIn("ActiveCalc::set(sCmd,", self.picker)
        self.assertNotIn('u"Calc/Active"_ustr, css::uno::Any(sCmd)', self.picker)
        for app in ("Writer", "Calc", "Impress", "Draw"):
            self.assertIn('GetModeForApp(sCmd, u"%s")' % app, self.picker, app)

    def test_the_preview_prefers_the_apps_own_picture(self):
        body = function_body(self.tabpage, "void UITabPage::UpdateImage(std::u16string_view sFileName)")
        self.assertIn("GetCurrentApp().toAsciiLowerCase()", body)
        # the per-app file is tried first; the shared one stays the fallback
        self.assertLess(body.index("toAsciiLowerCase"), body.index("aURL = aDir + sFileName;"))


if __name__ == "__main__":
    unittest.main()

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import contextlib
import io
import re
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
SETUP_PRODUCT = "/org.openoffice.Setup/Product"


def written(argv):
    """registrymodifications.xcu and the user/fonts names profile.main writes for `argv`."""
    with tempfile.TemporaryDirectory() as tmp:
        with contextlib.redirect_stdout(io.StringIO()):
            profile.main([*argv, "--profile", tmp])
        fonts = Path(tmp) / "user/fonts"
        return ((Path(tmp) / "user/registrymodifications.xcu").read_text(encoding="utf-8"),
                sorted(p.name for p in fonts.iterdir()) if fonts.exists() else [])


class LooksTest(unittest.TestCase):
    """The Boost light and dark looks: one table for profile.py, office.sh, shot-tab.sh and build_xcd.py."""

    # The flag lists office.sh and shot-tab.sh passed by hand before the table existed.
    HAND_FLAGS = {
        "light": ["--ui", "office", "--appearance", "light", "--icons", "boost", "--scheme", "Boost Light",
                  "--tint", "255", "--font", "inter"],
        "dark": ["--ui", "office", "--appearance", "dark", "--icons", "boost_dark", "--scheme", "Boost Dark",
                 "--tint", "255", "--font", "inter"],
    }

    def test_the_table_holds_the_reviewed_looks(self):
        self.assertEqual({"light", "dark"}, set(profile.LOOKS))
        self.assertEqual({"ui": "office", "appearance": "light", "icons": "boost", "scheme": "Boost Light",
                          "tint": 255, "font": "inter"}, profile.LOOKS["light"])
        self.assertEqual({"ui": "office", "appearance": "dark", "icons": "boost_dark", "scheme": "Boost Dark",
                          "tint": 255, "font": "inter"}, profile.LOOKS["dark"])

    def test_look_writes_what_the_hand_written_flags_wrote(self):
        for look, flags in self.HAND_FLAGS.items():
            for app in profile.APPS:
                self.assertEqual(written(["--app", app, *flags]), written(["--app", app, "--look", look]),
                                 (look, app))

    def test_a_flag_given_with_the_look_wins(self):
        xcu, fonts = written(["--look", "dark", "--font", "selawik", "--tint", "128"])
        p = props(xcu)
        self.assertEqual("Selawik", p[("/org.openoffice.VCL/VCLSettings/UIFont", "FamilyName")])
        self.assertEqual("128", p[(MISC, "NotebookbarColorTransparency")])
        self.assertEqual("boost_dark", p[(MISC, "SymbolStyle")])
        self.assertIn("selawk.ttf", fonts)

    def test_look_with_the_system_font_writes_no_font(self):
        xcu, fonts = written(["--look", "light", "--font", "system"])
        self.assertNotIn("UIFont", xcu)
        self.assertEqual([], fonts)
        self.assertEqual("Boost Light", props(xcu)[(SCHEME, "CurrentColorScheme")])

    def test_ui_and_appearance_are_required_without_a_look(self):
        for argv in (["--ui", "office"], ["--appearance", "light"], []):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                profile.main([*argv, "--profile", "/nonexistent"])

    def test_unknown_look_is_refused(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            profile.main(["--look", "sepia", "--profile", "/nonexistent"])


class FirstStartTest(unittest.TestCase):

    def test_every_profile_turns_the_welcome_dialog_off(self):
        # A fresh profile has no ooSetupLastVersion, so the welcome dialog opens over the first document
        # (sfx2/source/view/viewfrm.cxx:1705-1717) unless Setup/Product/WhatsNew is false. The dev profile
        # and boost.xcd carry it from the same list.
        for app in profile.APPS:
            for ui in ("default", "office"):
                p = props(profile.render(profile.build_items(ui, "light", app=app)))
                self.assertEqual("false", p[(SETUP_PRODUCT, "WhatsNew")], (app, ui))

    def test_whats_new_is_the_setup_schema_property(self):
        schema = ET.parse(Path(__file__).resolve().parents[2]
                          / "officecfg/registry/schema/org/openoffice/Setup.xcs")
        prop = schema.find("component/group[@{0}name='Product']/prop[@{0}name='WhatsNew']".format(OOR))
        self.assertIsNotNone(prop)
        self.assertEqual("xs:boolean", prop.get(OOR + "type"))


class ProductNameTest(unittest.TestCase):

    def test_every_profile_names_the_product_boost_office(self):
        # Setup/Product/ooName is %PRODUCTNAME of the UI strings, the window titles and the Options tree; the dev
        # profile and boost.xcd carry it from the same list.
        for app in profile.APPS:
            for ui in ("default", "office"):
                p = props(profile.render(profile.build_items(ui, "light", app=app)))
                self.assertEqual("Boost Office", p[(SETUP_PRODUCT, "ooName")], (app, ui))

    def test_every_profile_names_the_vendor(self):
        # Setup/Product/ooVendor is the About dialog's "This release was supplied by ..." (unotools
        # ConfigManager::getVendor); the build's own value is the login name of whoever configured it.
        for app in profile.APPS:
            p = props(profile.render(profile.build_items("office", "light", app=app)))
            self.assertEqual("the Boost Office project", p[(SETUP_PRODUCT, "ooVendor")], app)

    def test_oo_name_is_the_setup_schema_property(self):
        schema = ET.parse(Path(__file__).resolve().parents[2]
                          / "officecfg/registry/schema/org/openoffice/Setup.xcs")
        prop = schema.find("component/group[@{0}name='Product']/prop[@{0}name='ooName']".format(OOR))
        self.assertIsNotNone(prop)
        self.assertEqual("xs:string", prop.get(OOR + "type"))


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


START_CENTER = "/org.openoffice.Office.Common/Help/StartCenter"
PALETTE = Path(__file__).resolve().parents[2] / "product/themes/palette.json"


def palette_int(token, index):
    import json
    return str(int(json.loads(PALETTE.read_text(encoding="utf-8"))["tokens"][token][index].lstrip("#"), 16))


class StartCenterColorsTest(unittest.TestCase):
    """S2 (ruling 4): the Start Center's recent and template views paint the StartCenterThumbnails* colors
    (sfx2/source/control/recentdocsview.cxx, templatedefaultview.cxx UpdateColors), #666666 / #EEEEEE by
    default. A Boost scheme gives them its workspace and text colors, from palette.json."""

    def test_each_look_paints_the_views_in_its_schemes_workspace_and_text(self):
        for index, look in enumerate(("light", "dark")):
            for app in profile.APPS:
                p = props(profile.render(profile.build_items(**profile.LOOKS[look], app=app)))
                self.assertEqual(palette_int("workspace", index),
                                 p[(START_CENTER, "StartCenterThumbnailsBackgroundColor")], (look, app))
                self.assertEqual(palette_int("text", index),
                                 p[(START_CENTER, "StartCenterThumbnailsTextColor")], (look, app))

    def test_the_reviewed_values(self):
        light = props(profile.render(profile.build_items(**profile.LOOKS["light"])))
        dark = props(profile.render(profile.build_items(**profile.LOOKS["dark"])))
        self.assertEqual(str(0xFAFAFB), light[(START_CENTER, "StartCenterThumbnailsBackgroundColor")])
        self.assertEqual(str(0x242424), light[(START_CENTER, "StartCenterThumbnailsTextColor")])
        self.assertEqual(str(0x222226), dark[(START_CENTER, "StartCenterThumbnailsBackgroundColor")])
        self.assertEqual(str(0xF2F2F2), dark[(START_CENTER, "StartCenterThumbnailsTextColor")])

    def test_no_boost_scheme_keeps_the_stock_colors(self):
        for items in (profile.build_items("tabbed", "dark"),
                      profile.build_items("office", "light", scheme="Some Other Scheme")):
            self.assertNotIn(START_CENTER, profile.render(items))

    def test_the_colors_are_read_from_the_palette_not_copied(self):
        source = (Path(__file__).resolve().parents[2] / "product/dev/profile.py").read_text(encoding="utf-8")
        for value in ("FAFAFB", "222226", "242424", "F2F2F2", str(0xFAFAFB), str(0x222226)):
            self.assertNotIn(value, source.upper())
        import json
        from unittest import mock
        palette = json.loads(PALETTE.read_text(encoding="utf-8"))
        palette["tokens"]["workspace"] = ["#010203", "#040506"]
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "palette.json"
            other.write_text(json.dumps(palette), encoding="utf-8")
            with mock.patch.object(profile, "PALETTE", other):
                p = props(profile.render(profile.build_items(**profile.LOOKS["dark"])))
        self.assertEqual(str(0x040506), p[(START_CENTER, "StartCenterThumbnailsBackgroundColor")])

    def test_the_items_are_the_common_schema_properties(self):
        schema = ET.parse(Path(__file__).resolve().parents[2]
                          / "officecfg/registry/schema/org/openoffice/Office/Common.xcs")
        group = schema.find("component/group[@{0}name='Help']/group[@{0}name='StartCenter']".format(OOR))
        self.assertIsNotNone(group)
        for name in ("StartCenterThumbnailsBackgroundColor", "StartCenterThumbnailsTextColor"):
            prop = group.find("prop[@{0}name='{1}']".format(OOR, name))
            self.assertIsNotNone(prop, name)
            self.assertEqual("xs:int", prop.get(OOR + "type"), name)


class AllAppsTest(unittest.TestCase):
    """S2 (ruling 6): office.sh start's profile carries the look of every app the Start Center opens,
    as the installed boost.xcd layer does."""

    def test_all_writes_the_items_of_every_app_once(self):
        xcu, _ = written(["--app", "all", "--look", "light", "--font", "system"])
        p = props(xcu)
        union = {}
        for app in profile.APPS:
            for path, name, value in profile.build_items(**{**profile.LOOKS["light"], "font": "system"}, app=app):
                union[(path, name)] = value
        self.assertEqual(union, p)
        self.assertEqual(len(union), len(ET.fromstring(xcu).findall("item")), "each item once")
        for node in (profile.CALC_APP, profile.WRITER_APP, profile.IMPRESS_APP):
            self.assertEqual("notebookbar_office.ui", p[(node, "Active")])
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

    def test_awt_popups_ask_native_backends_to_show_disabled_entries(self):
        # I4c: not adding HideDisabledEntries is enough for vcl's own menus, but gtk3's native popups
        # (vcl/unx/gtk3/gtksalmenu.cxx, GtkSalMenu::Update) hide disabled entries unless the menu has
        # AlwaysShowDisabledEntries. So VCLXMenu::execute sets that flag when the setting is true and
        # the popup was not asked to hide them (controlmenucontroller.cxx's hideDisabledEntries(true)
        # must keep working, and AlwaysShowDisabledEntries would override it), before it executes.
        source = (Path(__file__).resolve().parents[2] / "toolkit/source/awt/vclxmenu.cxx").read_text(
            encoding="utf-8")
        match = re.search(r"sal_Int16 VCLXMenu::execute\([^{]*\{(.*?)\n\}", source, re.S)
        self.assertIsNotNone(match, "no VCLXMenu::execute")
        code = " ".join(re.sub(r"//[^\n]*", "", match.group(1)).split())
        self.assertRegex(
            code,
            r"if \(!DontHideDisabledEntry::get\(\)\) [^;]*\| MenuFlags::HideDisabledEntries\); "
            r"else if \(!\([^;]*& MenuFlags::HideDisabledEntries\)\) "
            r"[^;]*\| MenuFlags::AlwaysShowDisabledEntries\);",
            "the setting false hides disabled entries; true without a hide flag always shows them")
        self.assertEqual(1, code.count("MenuFlags::AlwaysShowDisabledEntries"),
                         "AlwaysShowDisabledEntries is set only in that branch")
        self.assertLess(code.index("MenuFlags::AlwaysShowDisabledEntries"), code.index("->Execute("),
                        "the flag is set before the popup executes")

    def test_native_submenus_inherit_the_rule_to_show_disabled_entries(self):
        # I9b: gtk3 opens a submenu natively and reads that submenu's own flags (GtkSalMenu::Activate,
        # then GtkSalMenu::Update), so the flag VCLXMenu::execute sets on the top popup did not reach its
        # submenus (Impress Home > Arrange > Distribute Selection showed only "[No selection possible]").
        # Menu::HandleMenuActivateEvent, which every native backend calls on the top menu for each submenu
        # it opens, passes AlwaysShowDisabledEntries on after the submenu's Activate, unless the submenu
        # was asked to hide disabled entries.
        source = (Path(__file__).resolve().parents[2] / "vcl/source/window/menu.cxx").read_text(encoding="utf-8")
        match = re.search(r"bool Menu::HandleMenuActivateEvent\(Menu\* pMenu\)\s*\{(.*?)\n\}", source, re.S)
        self.assertIsNotNone(match, "no Menu::HandleMenuActivateEvent")
        code = " ".join(re.sub(r"//[^\n]*", "", match.group(1)).split())
        self.assertRegex(
            code,
            r"if \(\(nMenuFlags & MenuFlags::AlwaysShowDisabledEntries\) "
            r"&& !\(pMenu->nMenuFlags & MenuFlags::HideDisabledEntries\)\) "
            r"pMenu->nMenuFlags \|= MenuFlags::AlwaysShowDisabledEntries;")
        self.assertLess(code.index("pMenu->Activate();"), code.index("MenuFlags::AlwaysShowDisabledEntries"),
                        "the flag is passed on after the submenu's Activate, which may ask to hide entries")

    def test_custom_themes_draw_disabled_menu_entries_without_an_outline(self):
        # I9b: the upstream gtk3 rule "menu menuitem:disabled" (vcl/unx/gtk3/custom-theme.cxx) drew a left
        # and a right border in the menu border color, which adw-gtk3's rounded menu items turned into a
        # faint outline around every greyed entry. Office draws plain grey text: the rule keeps its colors
        # and draws no border.
        source = (Path(__file__).resolve().parents[2] / "vcl/unx/gtk3/custom-theme.cxx").read_text(
            encoding="utf-8")
        rules = re.findall(r'"menu menuitem:disabled \{"(.*?)"\}"', source, re.S)
        self.assertEqual(1, len(rules), "one menu menuitem:disabled rule")
        self.assertIn("color: #\" + aThemeColors.GetDisabledTextColor()", rules[0])
        self.assertIn("background-color: #\" + aThemeColors.GetMenuColor()", rules[0])
        self.assertNotIn("border", rules[0])


if __name__ == "__main__":
    unittest.main()

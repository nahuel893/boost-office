# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import contextlib
import io
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from xml.etree import ElementTree as ET

from product.dev import profile
from product.icons import build_theme
from product.install import build_xcd
from product.themes import build_schemes

ROOT = Path(__file__).resolve().parents[2]
OOR = "{http://openoffice.org/2001/registry}"


def parse(theme):
    return ET.fromstring(build_xcd.render(theme))


def components(root):
    return {(c.get(OOR + "package"), c.get(OOR + "name")): c for c in root.findall(OOR + "component-data")}


def node_at(root, path):
    """The node at a registrymodifications-style `path` (as profile.py writes it)."""
    head, *segments = path.strip("/").split("/")
    package, name = head.rsplit(".", 1)
    node = components(root)[(package, name)]
    for segment in segments:
        match = re.fullmatch(r"[^\[]+\['([^']*)'\]", segment)
        wanted = match.group(1) if match else segment
        found = [n for n in node.findall("node") if n.get(OOR + "name") == wanted]
        if len(found) != 1:
            raise KeyError(f"{path}: {len(found)} nodes named {wanted!r}")
        node = found[0]
    return node


def lookup(root, path, prop):
    """The value of `prop` at `path`."""
    found = [p for p in node_at(root, path).findall("prop") if p.get(OOR + "name") == prop]
    if len(found) != 1:
        raise KeyError(f"{path}/{prop}: {len(found)} props")
    return found[0].findtext("value")


class BuildXcdTest(unittest.TestCase):

    def test_output_parses_and_depends_on_main(self):
        for theme in build_xcd.THEMES:
            text = build_xcd.render(theme)
            self.assertTrue(text.startswith('<?xml version="1.0" encoding="UTF-8"?>'), theme)
            root = ET.fromstring(text)
            self.assertEqual(root.tag, OOR + "data", theme)
            self.assertEqual(root[0].tag, "dependency", theme)
            self.assertEqual(root[0].get("file"), "main", theme)
            # the dependencies come first (configmgr/source/xcdparser.cxx:69-118)
            self.assertEqual([c.tag for c in root].count("dependency"), 1, theme)

    def test_one_component_per_package_and_name(self):
        for theme in build_xcd.THEMES:
            root = parse(theme)
            keys = [(c.get(OOR + "package"), c.get(OOR + "name")) for c in root.findall(OOR + "component-data")]
            self.assertEqual(len(keys), len(set(keys)), theme)
            self.assertEqual(set(keys), {
                ("org.openoffice.Office.UI", "ToolbarMode"), ("org.openoffice.Office", "Common"),
                ("org.openoffice.Office", "UI"), ("org.openoffice", "VCL"),
                ("org.openoffice.Office", "Impress"), ("org.openoffice", "Setup"),
            }, theme)

    def test_every_profile_item_of_the_three_apps_is_in_the_layer(self):
        # The dev profile and the layer cannot drift: each item profile.py writes for the Boost look of
        # Calc, Writer or Impress has the same value in boost.xcd.
        for theme in build_xcd.THEMES:
            root = parse(theme)
            for app in profile.APPS:
                items = profile.build_items(**build_xcd.preset(theme), app=app)
                self.assertGreater(len(items), 8)
                for path, prop, value in items:
                    self.assertEqual(lookup(root, path, prop), value, (theme, app, path, prop))

    def test_boost_look_values(self):
        expect = {"light": ("1", "boost", "Boost Light"), "dark": ("2", "boost_dark", "Boost Dark")}
        for theme, (appearance, icons, scheme) in expect.items():
            root = parse(theme)
            for app in ("Calc", "Writer", "Impress"):
                self.assertEqual(lookup(root, profile.APPLICATION % app, "Active"), "notebookbar_office.ui")
                self.assertEqual(lookup(root, profile.TOOLBAR_MODE, "Active" + app), "notebookbar_office.ui")
            self.assertEqual(lookup(root, profile.APPEARANCE, "ApplicationAppearance"), appearance)
            self.assertEqual(lookup(root, profile.APPEARANCE, "LibreOfficeTheme"), "1")
            self.assertEqual(lookup(root, profile.MISC, "SymbolStyle"), icons)
            self.assertEqual(lookup(root, "/org.openoffice.Office.UI/ColorScheme", "CurrentColorScheme"), scheme)
            self.assertEqual(lookup(root, profile.MISC, "NotebookbarColorTransparency"), "255")
            self.assertEqual(lookup(root, profile.UI_FONT, "FamilyName"), "Inter")
            self.assertEqual(lookup(root, profile.MISC, "FirstRun"), "false")
            self.assertEqual(lookup(root, profile.MISC, "ShowTipOfTheDay"), "false")
            self.assertEqual(lookup(root, profile.IMPRESS_NEWDOC, "AutoPilot"), "false")

    def test_first_start_welcome_dialog_is_off(self):
        # A fresh profile has no ooSetupLastVersion, so the welcome dialog opens over the document
        # (sfx2/source/view/viewfrm.cxx:1705-1717) unless Setup/Product/WhatsNew is false.
        for theme in build_xcd.THEMES:
            self.assertEqual(lookup(parse(theme), "/org.openoffice.Setup/Product", "WhatsNew"), "false")

    def test_presets_are_the_shared_looks(self):
        # One table (profile.LOOKS) for the dev launchers and the layer: nothing is copied by hand.
        for theme in build_xcd.THEMES:
            self.assertEqual(build_xcd.preset(theme), profile.LOOKS[theme], theme)
        source = (ROOT / "product/install/build_xcd.py").read_text(encoding="utf-8")
        self.assertNotIn("255", source)
        self.assertNotRegex(source, r"(?m)^import ast|ast\.")

    def test_each_look_names_a_built_icon_theme_and_a_palette_scheme(self):
        palette = build_schemes.load_palette()
        for theme in build_xcd.THEMES:
            look = profile.LOOKS[theme]
            self.assertEqual(build_theme.THEMES[look["icons"]], theme, theme)
            self.assertEqual(palette["schemes"][build_xcd.THEMES.index(theme)], look["scheme"], theme)

    def test_a_look_that_disagrees_with_the_icon_themes_or_the_palette_is_refused(self):
        palette = build_schemes.load_palette()
        wrong = {**profile.LOOKS["light"], "icons": "boost_dark"}
        with mock.patch.dict(profile.LOOKS, {"light": wrong}), self.assertRaises(ValueError):
            build_xcd.preset("light", palette)
        wrong = {**profile.LOOKS["dark"], "scheme": "Boost Light"}
        with mock.patch.dict(profile.LOOKS, {"dark": wrong}), self.assertRaises(ValueError):
            build_xcd.preset("dark", palette)

    def test_the_icon_themes_are_readable_without_pillow(self):
        # build_xcd.py imports build_theme.THEMES; Pillow is needed only where icons are drawn.
        code = ("import sys; sys.modules['PIL'] = None; sys.path.insert(0, sys.argv[1]); "
                "from product.icons import build_theme; from product.install import build_xcd; "
                "print(sorted(build_theme.THEMES)); build_xcd.render('light')")
        out = subprocess.run([sys.executable, "-I", "-c", code, str(ROOT)], capture_output=True, text=True,
                             check=False, timeout=60)
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertEqual("['boost', 'boost_dark']", out.stdout.strip())

    def test_both_color_schemes_and_the_tab_accents_come_from_build_schemes(self):
        palette = build_schemes.load_palette()
        wanted = ET.fromstring(build_schemes.xcu(palette))   # one oor:component-data, UI
        self.assertEqual((wanted.get(OOR + "package"), wanted.get(OOR + "name")), ("org.openoffice.Office", "UI"))
        accents = build_schemes.tab_accent_values(palette)
        for theme in build_xcd.THEMES:
            root = parse(theme)
            schemes = node_at(root, "/org.openoffice.Office.UI/ColorScheme/ColorSchemes")
            got = {n.get(OOR + "name"): n for n in schemes.findall("node")}
            self.assertEqual(sorted(got), sorted(palette["schemes"]), theme)
            for scheme in wanted.iter("node"):
                if scheme.get(OOR + "op") != "replace":
                    continue
                name = scheme.get(OOR + "name")
                self.assertEqual(got[name].get(OOR + "op"), "replace", (theme, name))
                for role in scheme.findall("node"):
                    path = f"/org.openoffice.Office.UI/ColorScheme/ColorSchemes/{name}/{role.get(OOR + 'name')}"
                    self.assertEqual(lookup(root, path, "Color"), role.findtext("prop/value"), (theme, path))
            for app, (light, dark) in accents.items():
                path = profile.APPLICATION % app
                self.assertEqual(lookup(root, path, "AccentColor"), str(int(light.lstrip("#"), 16)), (theme, app))
                self.assertEqual(lookup(root, path, "AccentColorDark"), str(int(dark.lstrip("#"), 16)), (theme, app))

    def test_impress_accent_is_orange(self):
        self.assertEqual(lookup(parse("light"), profile.APPLICATION % "Impress", "AccentColor"),
                         str(0xC43E1C))

    def test_cli_writes_the_file_or_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "registry" / "boost.xcd"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(build_xcd.main(["--theme", "dark", "--out", str(out)]), 0)
            self.assertEqual(out.read_text(encoding="utf-8"), build_xcd.render("dark"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(build_xcd.main(["--theme", "light"]), 0)
        self.assertEqual(buf.getvalue(), build_xcd.render("light"))

    def test_default_theme_is_light(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            build_xcd.main([])
        self.assertEqual(buf.getvalue(), build_xcd.render("light"))

    def test_unknown_theme_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            build_xcd.main(["--theme", "blue"])


if __name__ == "__main__":
    unittest.main()

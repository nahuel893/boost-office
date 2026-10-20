# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The UI font trial: bundled fonts, the profile item the gtk3 plugin reads, and shot-tab's switch."""
import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from product.dev import profile

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "product/fonts"
VCL_XCS = ROOT / "officecfg/registry/schema/org/openoffice/VCL.xcs"
OOR = "{http://openoffice.org/2001/registry}"
UI_FONT_PATH = "/org.openoffice.VCL/VCLSettings/UIFont"
LOOK = dict(icons="boost", scheme="Boost Light", tint=255)


def props(xml):
    root = ET.fromstring(xml)
    return {(item.get(OOR + "path"), item.find("prop").get(OOR + "name")): item.find("prop/value").text
            for item in root.findall("item")}


class BundledFontsTest(unittest.TestCase):

    def test_selawik_has_its_five_static_fonts_license_and_readme(self):
        names = sorted(p.name for p in (FONTS / "selawik").iterdir())
        self.assertEqual(["OFL.txt", "README.md", "selawk.ttf", "selawkb.ttf", "selawkl.ttf",
                          "selawksb.ttf", "selawksl.ttf"], names)

    def test_inter_has_four_static_weights_license_and_readme(self):
        names = sorted(p.name for p in (FONTS / "inter").iterdir())
        self.assertEqual(["Inter-Bold.ttf", "Inter-Medium.ttf", "Inter-Regular.ttf",
                          "Inter-SemiBold.ttf", "OFL.txt", "README.md"], names)

    def test_licenses_are_the_sil_ofl(self):
        for font in ("selawik", "inter"):
            text = (FONTS / font / "OFL.txt").read_text(encoding="utf-8")
            self.assertIn("SIL OPEN FONT LICENSE Version 1.1", text, font)


class ProfileFontTest(unittest.TestCase):

    def test_inter_and_selawik_set_the_vcl_ui_font_family(self):
        for font, family in (("inter", "Inter"), ("selawik", "Selawik")):
            p = props(profile.render(profile.build_items("office", "light", font=font, **LOOK)))
            self.assertEqual(family, p[(UI_FONT_PATH, "FamilyName")], font)

    def test_system_writes_exactly_what_no_font_writes(self):
        without = profile.render(profile.build_items("office", "light", **LOOK))
        system = profile.render(profile.build_items("office", "light", font="system", **LOOK))
        self.assertEqual(without, system)
        self.assertNotIn("UIFont", system)

    def test_the_item_path_exists_in_the_vcl_schema(self):
        root = ET.parse(VCL_XCS).getroot()
        settings = root.find("component/group[@{0}name='VCLSettings']".format(OOR))
        prop = settings.find("group[@{0}name='UIFont']/prop[@{0}name='FamilyName']".format(OOR))
        self.assertIsNotNone(prop)
        self.assertEqual("xs:string", prop.get(OOR + "type"))
        self.assertIsNone(prop.find("value").text)   # empty default: the desktop's font

    def test_main_copies_the_chosen_fonts_into_the_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                profile.main(["--ui", "office", "--appearance", "light", "--font", "inter", "--profile", tmp])
            fonts = sorted(p.name for p in (Path(tmp) / "user/fonts").iterdir())
            self.assertEqual(["Inter-Bold.ttf", "Inter-Medium.ttf", "Inter-Regular.ttf", "Inter-SemiBold.ttf"], fonts)
            xcu = (Path(tmp) / "user/registrymodifications.xcu").read_text(encoding="utf-8")
            self.assertEqual("Inter", props(xcu)[(UI_FONT_PATH, "FamilyName")])

    def test_main_with_system_font_copies_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                profile.main(["--ui", "office", "--appearance", "light", "--font", "system", "--profile", tmp])
            self.assertFalse((Path(tmp) / "user/fonts").exists())

    def test_unknown_font_is_refused(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            profile.main(["--ui", "office", "--appearance", "light", "--font", "comic", "--profile", "/nonexistent"])


class ShotTabFontTest(unittest.TestCase):

    def test_unknown_shot_font_is_refused_before_anything_starts(self):
        env = dict(os.environ, SHOT_FONT="comic", LO_PROFILE="/nonexistent/profile")
        out = subprocess.run(["bash", str(ROOT / "product/dev/shot-tab.sh"), "light", "Home", "/nonexistent/x.png"],
                             capture_output=True, text=True, env=env, check=False, timeout=30)
        self.assertEqual(2, out.returncode, out.stderr)
        self.assertIn("SHOT_FONT", out.stderr)

    def test_shot_font_defaults_to_inter_in_the_script(self):
        # The script needs a private sway to get past its argument checks, so the default cannot be
        # observed by running it. This pins the one line that sets it (and the usage comment).
        text = (ROOT / "product/dev/shot-tab.sh").read_text(encoding="utf-8")
        self.assertIn('font="${SHOT_FONT:-inter}"', text)
        self.assertNotIn("SHOT_FONT:-system", text)
        self.assertIn("(default inter,", text)


if __name__ == "__main__":
    unittest.main()

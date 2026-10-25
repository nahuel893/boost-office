# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from product.themes import build_schemes as bs

# Spec §4.3: role -> (light, dark). On 2026-10-20 the user asked for a white light theme, so the
# light surfaces moved from soft green to white and neutral greys; the accents stay green.
SPEC = {
    "WindowColor": ("#FFFFFF", "#2B2B2B"), "WindowTextColor": ("#242424", "#F2F2F2"),
    "BaseColor": ("#FFFFFF", "#1F1F1F"), "FieldColor": ("#FFFFFF", "#1F1F1F"),
    "FaceColor": ("#E0E0E0", "#454545"), "ShadowColor": ("#828282", "#7A7A7A"),
    "SeparatorColor": ("#9E9E9E", "#6A6A6A"), "ButtonColor": ("#FFFFFF", "#2B2B2B"),
    "ButtonTextColor": ("#242424", "#F2F2F2"), "AccentColor": ("#CFE8D7", "#1E4D2E"),
    "DisabledColor": ("#F0F0F0", "#383838"), "DisabledTextColor": ("#A6A6A6", "#6E6E6E"),
    "ActiveColor": ("#1B7A3E", "#5CC27E"), "ActiveTextColor": ("#FFFFFF", "#1F1F1F"),
    "ActiveBorderColor": ("#1B7A3E", "#5CC27E"), "InactiveColor": ("#FFFFFF", "#2B2B2B"),
    "InactiveTextColor": ("#A6A6A6", "#6E6E6E"), "InactiveBorderColor": ("#9E9E9E", "#6A6A6A"),
    "MenuBarColor": ("#FFFFFF", "#2B2B2B"), "MenuBarTextColor": ("#242424", "#F2F2F2"),
    "MenuBarHighlightColor": ("#F0F0F0", "#383838"), "MenuBarHighlightTextColor": ("#242424", "#F2F2F2"),
    "MenuColor": ("#FFFFFF", "#2B2B2B"), "MenuTextColor": ("#242424", "#F2F2F2"),
    "MenuHighlightColor": ("#F0F0F0", "#383838"), "MenuHighlightTextColor": ("#242424", "#F2F2F2"),
    "MenuBorderColor": ("#9E9E9E", "#6A6A6A"),
}
TEXT_PAIRS = [  # (foreground role, background role) that carry text
    ("WindowTextColor", "WindowColor"), ("WindowTextColor", "BaseColor"),
    ("ButtonTextColor", "ButtonColor"), ("WindowTextColor", "AccentColor"),
    ("ActiveTextColor", "ActiveColor"), ("MenuBarTextColor", "MenuBarColor"),
    ("MenuBarHighlightTextColor", "MenuBarHighlightColor"), ("MenuTextColor", "MenuColor"),
    ("MenuHighlightTextColor", "MenuHighlightColor"),
]
OOR = "{http://openoffice.org/2001/registry}"
# Design 3.4 (approved 2026-10-20): one tab accent per app, as ToolbarMode Applications/<App> AccentColor
# (light) and AccentColorDark. Word's brand blue for Writer; Calc keeps its green. The dark blue applies
# accent.calc's light-to-dark step (same hue, +0.269 lightness, saturation x0.713) to #185ABD.
APP_ACCENTS = {"Writer": ("#185ABD", "#83A6DB"), "Calc": ("#1B7A3E", "#5CC27E"),
               "Impress": ("#C43E1C", "#FF8F6B")}


class SchemesTest(unittest.TestCase):

    def setUp(self):
        self.palette = bs.load_palette()
        self.values = bs.scheme_values(self.palette)

    def test_all_27_roles_match_the_spec(self):
        self.assertEqual(27, len(SPEC))
        for index, scheme in enumerate(("Boost Light", "Boost Dark")):
            self.assertEqual({role: pair[index] for role, pair in SPEC.items()}, self.values[scheme])

    def test_text_roles_meet_wcag_aa(self):
        for scheme, roles in self.values.items():
            for fg, bg in TEXT_PAIRS:
                ratio = bs.contrast(roles[fg], roles[bg])
                self.assertGreaterEqual(ratio, 4.5, f"{scheme}: {fg} on {bg} = {ratio:.2f}")

    def test_field_border_meets_3_to_1(self):
        for scheme, roles in self.values.items():
            self.assertGreaterEqual(bs.contrast(roles["ShadowColor"], roles["WindowColor"]), 3.0, scheme)

    def test_xcu_stores_colors_as_ints_under_color_schemes(self):
        def child(node, name):
            return next(c for c in node if c.get(OOR + "name") == name)
        root = ET.fromstring(bs.xcu(self.palette))
        self.assertEqual("UI", root.get(OOR + "name"))
        light = child(child(child(root, "ColorScheme"), "ColorSchemes"), "Boost Light")
        self.assertEqual(str(0xFFFFFF), child(light, "WindowColor").find("prop/value").text)

    def test_calc_cell_focus_is_the_calc_green_with_ui_contrast(self):
        def child(node, name):
            return next(c for c in node if c.get(OOR + "name") == name)
        root = ET.fromstring(bs.xcu(self.palette))
        schemes = child(child(root, "ColorScheme"), "ColorSchemes")
        for scheme, expected in (("Boost Light", 0x1B7A3E), ("Boost Dark", 0x5CC27E)):
            node = child(child(schemes, scheme), "CalcCellFocus")
            self.assertEqual(str(expected), node.find("prop/value").text, scheme)
        self.assertEqual(27, len(self.values["Boost Light"]))
        self.assertGreaterEqual(bs.contrast("#1B7A3E", "#FFFFFF"), 3.0)

    def test_extension_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            oxt = bs.build(self.palette, Path(tmp) / "boost-schemes.oxt")
            with zipfile.ZipFile(oxt) as z:
                self.assertEqual({"description.xml", "META-INF/manifest.xml", "ColorSchemes.xcu",
                                  "ToolbarMode.xcu"}, set(z.namelist()))
                self.assertIn("org.boost.colorschemes", z.read("description.xml").decode())
                manifest = z.read("META-INF/manifest.xml").decode()
                for xcu in ("ColorSchemes.xcu", "ToolbarMode.xcu"):
                    self.assertIn(f'manifest:full-path="{xcu}"', manifest)

    def test_writer_accent_is_word_blue_with_ui_contrast(self):
        self.assertEqual(list(APP_ACCENTS["Writer"]), self.palette["tokens"]["accent.writer"])
        self.assertEqual(list(APP_ACCENTS["Calc"]), self.palette["tokens"]["accent.calc"])
        light, dark = APP_ACCENTS["Writer"]
        self.assertGreaterEqual(bs.contrast(light, SPEC["WindowColor"][0]), 3.0)
        self.assertGreaterEqual(bs.contrast(dark, SPEC["WindowColor"][1]), 3.0)

    def test_impress_accent_is_powerpoint_orange_with_ui_contrast(self):
        self.assertEqual(list(APP_ACCENTS["Impress"]), self.palette["tokens"]["accent.impress"])
        self.assertEqual("accent.impress", self.palette["tab_accents"]["Impress"])
        light, dark = APP_ACCENTS["Impress"]
        self.assertGreaterEqual(bs.contrast(light, SPEC["WindowColor"][0]), 3.0)
        self.assertGreaterEqual(bs.contrast(dark, SPEC["WindowColor"][1]), 3.0)

    def test_extension_carries_one_tab_accent_per_app_in_both_themes(self):
        def child(node, name):
            return next(c for c in node if c.get(OOR + "name") == name)
        with tempfile.TemporaryDirectory() as tmp:
            oxt = bs.build(self.palette, Path(tmp) / "boost-schemes.oxt")
            with zipfile.ZipFile(oxt) as z:
                root = ET.fromstring(z.read("ToolbarMode.xcu"))
        self.assertEqual(("ToolbarMode", "org.openoffice.Office.UI"),
                         (root.get(OOR + "name"), root.get(OOR + "package")))
        apps = child(root, "Applications")
        self.assertEqual(set(APP_ACCENTS), {node.get(OOR + "name") for node in apps})
        for app, (light, dark) in APP_ACCENTS.items():
            node = child(apps, app)
            # Modify the app's existing node, never replace it: its Modes come from the stock ToolbarMode.xcu.
            self.assertIsNone(node.get(OOR + "op"), app)
            for prop, color in (("AccentColor", light), ("AccentColorDark", dark)):
                self.assertEqual(str(int(color.lstrip("#"), 16)), child(node, prop).find("value").text,
                                 f"{app} {prop}")

    def test_the_workspace_is_the_reviewed_app_background(self):
        # Without AppBackground the workspace around Writer's page takes the desktop's GTK window color
        # (svtools/source/config/colorcfg.cxx:599-600; G0 saw #131317 under a dark GTK theme in light).
        # These are the colors the ribbons were reviewed with (the dev launcher forced adw-gtk3).
        def child(node, name):
            return next(c for c in node if c.get(OOR + "name") == name)
        documents = bs.document_values(self.palette)
        schemes = child(child(ET.fromstring(bs.xcu(self.palette)), "ColorScheme"), "ColorSchemes")
        for scheme, expected in (("Boost Light", "#FAFAFB"), ("Boost Dark", "#222226")):
            self.assertEqual(expected, documents[scheme]["AppBackground"], scheme)
            node = child(child(schemes, scheme), "AppBackground")
            self.assertEqual(str(int(expected.lstrip("#"), 16)), node.find("prop/value").text, scheme)

    def test_the_global_accent_roles_stay_calc_green(self):
        # Check boxes, focus rings, progress bars and the selection tint stay global (design 3.4).
        for index, scheme in enumerate(("Boost Light", "Boost Dark")):
            self.assertEqual(APP_ACCENTS["Calc"][index], self.values[scheme]["ActiveColor"])
            self.assertEqual(APP_ACCENTS["Calc"][index], self.values[scheme]["ActiveBorderColor"])


if __name__ == "__main__":
    unittest.main()

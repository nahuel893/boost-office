# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from product.themes import build_schemes as bs

# Spec §4.3, verbatim: role -> (light, dark)
SPEC = {
    "WindowColor": ("#E4F2E8", "#2B2B2B"), "WindowTextColor": ("#242424", "#F2F2F2"),
    "BaseColor": ("#FFFFFF", "#1F1F1F"), "FieldColor": ("#FFFFFF", "#1F1F1F"),
    "FaceColor": ("#C3DECB", "#454545"), "ShadowColor": ("#828282", "#7A7A7A"),
    "SeparatorColor": ("#9E9E9E", "#6A6A6A"), "ButtonColor": ("#E4F2E8", "#2B2B2B"),
    "ButtonTextColor": ("#242424", "#F2F2F2"), "AccentColor": ("#CFE8D7", "#1E4D2E"),
    "DisabledColor": ("#D3E8DA", "#383838"), "DisabledTextColor": ("#A6A6A6", "#6E6E6E"),
    "ActiveColor": ("#1B7A3E", "#5CC27E"), "ActiveTextColor": ("#FFFFFF", "#1F1F1F"),
    "ActiveBorderColor": ("#1B7A3E", "#5CC27E"), "InactiveColor": ("#E4F2E8", "#2B2B2B"),
    "InactiveTextColor": ("#A6A6A6", "#6E6E6E"), "InactiveBorderColor": ("#9E9E9E", "#6A6A6A"),
    "MenuBarColor": ("#E4F2E8", "#2B2B2B"), "MenuBarTextColor": ("#242424", "#F2F2F2"),
    "MenuBarHighlightColor": ("#D3E8DA", "#383838"), "MenuBarHighlightTextColor": ("#242424", "#F2F2F2"),
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
        self.assertEqual(str(0xE4F2E8), child(light, "WindowColor").find("prop/value").text)

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
                self.assertEqual({"description.xml", "META-INF/manifest.xml", "ColorSchemes.xcu"},
                                 set(z.namelist()))
                self.assertIn("org.boost.colorschemes", z.read("description.xml").decode())


if __name__ == "__main__":
    unittest.main()

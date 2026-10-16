# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

from product.icons import build_theme as bt

ROOT = Path(__file__).resolve().parents[2]
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
# Rendered by toolbar controllers as list boxes; they show no icon.
LIST_BOX_COMMANDS = {"charfontname", "fontheight", "numberformattype", "styleapply"}
EXPECTED_SIZE = {"cmd/sc_": 16, "cmd/lc_": 24, "cmd/32/": 32}


def tab_page(tab):
    text = OFFICE.read_text(encoding="utf-8")
    body = text.split(f"<!-- product:{tab}-begin -->")[1].split(f"<!-- product:{tab}-end -->")[0]
    return ET.fromstring("<root>" + body + "</root>")


def home_page():
    return tab_page("Home")


class IconThemeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.result = bt.build(bt.load_manifest(), Path(cls.tmp.name))
        cls.zips = cls.result["zips"]

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

    def has(self, theme, member):
        names, links = self.members(theme)
        return member in names or links.get(member) in names

    def image(self, theme, member):
        with zipfile.ZipFile(self.zips[theme]) as z, z.open(member) as f:
            return Image.open(f).convert("RGBA").copy()

    def test_every_home_button_has_an_icon(self):
        self.assertEqual([], self.missing_icons(home_page()))

    def test_every_data_button_has_an_icon(self):
        page = tab_page("Data")
        self.assertGreater(len(list(page.iter("object"))), 30)
        self.assertEqual([], self.missing_icons(page))

    def test_every_insert_button_has_an_icon(self):
        page = tab_page("Insert")
        self.assertGreater(len(list(page.iter("object"))), 40)
        self.assertEqual([], self.missing_icons(page))

    def test_every_page_layout_button_has_an_icon(self):
        page = tab_page("PageLayout")
        self.assertGreater(len(list(page.iter("object"))), 25)
        self.assertEqual([], self.missing_icons(page))

    def test_insert_url_variants_use_plain_icon_names_of_the_right_size(self):
        self.check_url_variant_icons("Insert")

    def test_page_layout_url_variants_use_plain_icon_names_of_the_right_size(self):
        self.check_url_variant_icons("PageLayout")

    def check_url_variant_icons(self, tab):
        # json "icon" key: cmd/sc_<base>_<value>.png for small, cmd/32/<base>_<value>.png for large buttons
        variants = 0
        for box in tab_page(tab).iter("object"):
            if box.get("class") != "sfxlo-NotebookbarToolBox":
                continue
            large = box.find("property[@name='icon_size']").text == "5"
            for button in box.findall("child/object"):
                icon = button.find("property[@name='icon_name']")
                action = button.find("property[@name='action-name']").text
                if "?" not in action:
                    self.assertIsNone(icon, action)
                    continue
                variants += 1
                self.assertRegex(icon.text, r"^cmd/32/[a-z0-9_]+\.png$" if large else r"^cmd/sc_[a-z0-9_]+\.png$", action)
                for theme in self.zips:
                    self.assertTrue(self.has(theme, icon.text), f"{theme}:{icon.text}")
                    self.assertTrue(self.has(theme, icon.text.replace("cmd/32/", "cmd/lc_").replace("cmd/sc_", "cmd/lc_")))
        self.assertGreater(variants, 0)

    def missing_icons(self, page):
        missing = []
        for box in page.iter("object"):
            if box.get("class") != "sfxlo-NotebookbarToolBox":
                continue
            large = box.find("property[@name='icon_size']").text == "5"
            for button in box.findall("child/object"):
                icon = button.find("property[@name='icon_name']")
                if icon is not None:
                    wanted = [icon.text]
                else:
                    cmd = button.find("property[@name='action-name']").text.removeprefix(".uno:").lower()
                    if cmd in LIST_BOX_COMMANDS:
                        continue
                    wanted = [f"cmd/sc_{cmd}.png", f"cmd/lc_{cmd}.png"] + ([f"cmd/32/{cmd}.png"] if large else [])
                for theme in self.zips:
                    missing += [f"{theme}:{m}" for m in wanted if not self.has(theme, m)]
        return missing

    def test_png_sizes(self):
        for theme in self.zips:
            names, _ = self.members(theme)
            for member in names:
                for prefix, size in EXPECTED_SIZE.items():
                    if member.startswith(prefix) and member.endswith(".png"):
                        self.assertEqual((size, size), self.image(theme, member).size, f"{theme}:{member}")

    def test_color_buttons_keep_the_stripe_band_empty(self):
        # svx/source/tbxctrls/tbxcolorupdate.cxx:266-274 paints rows H - H/4 .. H-1.
        for theme in self.zips:
            for name in ("color", "backgroundcolor"):
                for member, size in ((f"cmd/sc_{name}.png", 16), (f"cmd/lc_{name}.png", 24)):
                    band = self.image(theme, member).crop((0, size - size // 4, size, size))
                    self.assertEqual(0, band.getextrema()[3][1], f"{theme}:{member}")

    def test_dark_theme_has_no_light_theme_line_color(self):
        names, _ = self.members("boost_dark")
        for member in sorted(n for n in names if n.endswith(".png")):
            for r, g, b, a in self.image("boost_dark", member).get_flattened_data():
                if a > 128 and max(abs(r - 0x42), abs(g - 0x42), abs(b - 0x42)) < 24:
                    self.fail(f"boost_dark:{member} has light-theme line pixels")

    def test_license_and_links(self):
        for theme in self.zips:
            names, links = self.members(theme)
            self.assertIn("LICENSE.fluent.txt", names)
            with zipfile.ZipFile(self.zips[theme]) as z:
                self.assertTrue(z.read("LICENSE.fluent.txt").decode().startswith("MIT License"))
            for alias, target in links.items():
                self.assertIn(target, names, f"{theme}: {alias} -> {target}")

    def test_filled_icons_use_their_fill_color(self):
        # Office-like fills: the paper of "paste" carries the yellow fill.
        for theme, fill in (("boost", "F5C96A"), ("boost_dark", "B08A3A")):
            target = tuple(int(fill[i:i + 2], 16) for i in (0, 2, 4))
            pixels = self.image(theme, "cmd/lc_paste.png").get_flattened_data()
            close = [p for p in pixels if p[3] > 200 and max(abs(p[i] - target[i]) for i in range(3)) < 20]
            self.assertGreater(len(close), 40, f"{theme}: paste fill missing")

    def test_badges_use_their_accent(self):
        # (icon, accent hex in light, accent hex in dark)
        cases = [("insertcell", "107C10", "54B054"), ("deletecell", "C50F1F", "E9737B"),
                 ("conditionalformatmenu", "AD6800", "F2B230"), ("sortfiltermenu", "0F6CBD", "479EF5")]
        for name, light, dark in cases:
            for theme, accent in (("boost", light), ("boost_dark", dark)):
                target = tuple(int(accent[i:i + 2], 16) for i in (0, 2, 4))
                pixels = self.image(theme, f"cmd/lc_{name}.png").get_flattened_data()
                close = [p for p in pixels if p[3] > 200 and max(abs(p[i] - target[i]) for i in range(3)) < 20]
                self.assertTrue(close, f"{theme}:{name} has no {accent} pixels")

    def test_16px_icons_use_crisp_sources(self):
        # 16 px slots use the 20 px design trimmed 1:1, or native 16; never a blurry 24 -> 16.
        self.assertEqual([], self.result["scaled_16"])

    def test_trim_never_clips_vendored_ink(self):
        # The 20 px design is trimmed by `pad` px per side for 16 px slots; the trimmed ring must be empty.
        sources = bt.Sources()
        for entry in bt.load_manifest()["icons"]:
            if entry.get("stripe"):
                continue
            base = next(layer for layer in entry["layers"] if "glyph" in layer)
            for layer in entry["layers"]:
                if "glyph" not in layer or layer.get("custom"):
                    continue
                also = ("filled",) if entry.get("fill") and layer is base else ()
                _, src, pad = sources.load(entry["name"], layer, 16, False, also=also)
                if src != 20:
                    continue
                styles = {layer.get("style", "regular"), *also}
                for style in styles:
                    path = bt.FLUENT / f"{layer['glyph']}_20_{style}.svg"
                    self.assertEqual(0, bt.ring_ink(path, pad), f"{path.name} loses ink at pad {pad}")
            if entry.get("fill"):
                _, src, pad = sources.load(entry["name"], dict(base, style="filled"), 16, False, also=("regular",))
                _, src2, pad2 = sources.load(entry["name"], base, 16, False, also=("filled",))
                self.assertEqual((src, pad), (src2, pad2), f"{entry['name']}: fill and outline not registered")

    def test_custom_glyph_has_a_native_16px_drawing(self):
        self.assertTrue((bt.CUSTOM / "thousands_16.svg").exists())
        _, src, pad = bt.Sources().load("numberformatdecimal", {"glyph": "thousands", "custom": True}, 16)
        self.assertEqual((16, 0), (src, pad))

    def test_data_icons_that_reviews_found_ambiguous_use_distinct_glyphs(self):
        # Reapply must not read as Reset Filter at 16 px; Consolidate must not read as the ">>" chevron.
        icons = {e["name"]: e for e in bt.load_manifest()["icons"]}
        glyphs = lambda name: [layer["glyph"] for layer in icons[name]["layers"]]
        self.assertEqual(["filter_sync"], glyphs("datafilterreapply"))
        self.assertNotEqual(glyphs("datafilterreapply"), glyphs("datafilterremovefilter"))
        self.assertNotIn("merge", glyphs("dataconsolidate"))

    def test_vendored_glyphs_exist(self):
        for entry in bt.load_manifest()["icons"]:
            for layer in entry["layers"]:
                if "glyph" in layer and not layer.get("custom"):
                    path = bt.FLUENT / f"{layer['glyph']}_24_{layer.get('style', 'regular')}.svg"
                    self.assertTrue(path.exists(), path)


if __name__ == "__main__":
    unittest.main()

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
# (glyph, custom, scanline across straight strokes, outer runs only): "row" crosses vertical strokes
# at y = pos * size, "col" crosses horizontal strokes at x = pos * size. The rings of "thousands"
# touch each other, so only its outermost sides are single strokes.
STROKE_PROBES = [("table", False, "row", 0.5, False), ("text_align_left", False, "col", 1 / 3, False),
                 ("thousands", True, "row", 11 / 24, True)]


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

    def test_every_formulas_button_has_an_icon(self):
        page = tab_page("Formulas")
        self.assertGreater(len(list(page.iter("object"))), 25)
        self.assertEqual([], self.missing_icons(page))

    def test_every_review_button_has_an_icon(self):
        page = tab_page("Review")
        self.assertGreater(len(list(page.iter("object"))), 12)
        self.assertEqual([], self.missing_icons(page))

    def test_every_view_button_has_an_icon(self):
        page = tab_page("View")
        self.assertGreater(len(list(page.iter("object"))), 20)
        self.assertEqual([], self.missing_icons(page))

    def test_every_help_button_has_an_icon(self):
        page = tab_page("Help")
        self.assertEqual(7, sum(1 for o in page.iter("object") if o.get("class") == "GtkToolButton"))
        self.assertEqual([], self.missing_icons(page))

    def test_insert_url_variants_use_plain_icon_names_of_the_right_size(self):
        self.check_url_variant_icons("Insert")

    def test_page_layout_url_variants_use_plain_icon_names_of_the_right_size(self):
        self.check_url_variant_icons("PageLayout")

    def test_formulas_url_variants_use_plain_icon_names_of_the_right_size(self):
        self.check_url_variant_icons("Formulas")

    def test_review_url_variants_use_plain_icon_names_of_the_right_size(self):
        self.check_url_variant_icons("Review")

    def test_view_url_variants_use_plain_icon_names_of_the_right_size(self):
        self.check_url_variant_icons("View")

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

    def render(self, entry, size, mode="light"):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "icon.png"
            bt.render_png(bt.compose(entry, bt.load_manifest()["palette"][mode], size, bt.Sources()), size, out)
            return Image.open(out).convert("RGBA").copy()

    def stroke_widths(self, glyph, custom, axis, pos, outer, size, mode):
        """Alpha coverage, in px, of each ink run along one scanline of a single-glyph icon."""
        layer = {"glyph": glyph, "custom": True} if custom else {"glyph": glyph}
        alpha = self.render({"name": "probe", "layers": [layer]}, size, mode).getchannel("A")
        at = int(pos * size)
        line = [alpha.getpixel((at, i) if axis == "col" else (i, at)) for i in range(size)] + [0]
        runs, ink = [], 0
        for a in line:
            if a:
                ink += a
            elif ink:
                runs.append(ink / 255)
                ink = 0
        self.assertGreaterEqual(len(runs), 3, f"{mode}:{glyph}@{size}")
        return [runs[0], runs[-1]] if outer else runs

    def test_outlines_are_about_one_pixel_at_24_and_32(self):
        # Office-like hairlines: Fluent's regular strokes are 1.5 px at 24 and 2 px at 32.
        for mode in ("light", "dark"):
            for size in (24, 32):
                for probe in STROKE_PROBES:
                    widths = self.stroke_widths(*probe, size, mode)
                    for width in widths:
                        self.assertGreaterEqual(width, 0.75, f"{mode}:{probe[0]}@{size} {widths}")
                        self.assertLessEqual(width, 1.1, f"{mode}:{probe[0]}@{size} {widths}")

    def test_16px_outlines_are_no_heavier_than_before(self):
        # Before the thinning every probe measured 1.0 px at 16 (20 px design trimmed 1:1, native 16 px).
        for mode in ("light", "dark"):
            for probe in STROKE_PROBES:
                widths = self.stroke_widths(*probe, 16, mode)
                self.assertLessEqual(max(widths), 1.02, f"{mode}:{probe[0]} {widths}")

    def test_thin_outlines_keep_dots_and_stay_registered(self):
        # Thinning must not erase small dots, and neither the soft fill nor a highlight band
        # may peek out past the thinned outline.
        bbox = lambda img: img.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
        band = {"rect": [0.125, 0.125, 0.75, 0.25], "opacity": 0.35}
        for size in (24, 32):
            dots = self.render({"name": "probe", "layers": [{"glyph": "more_horizontal"}]}, size).getchannel("A")
            for third in range(3):
                cells = dots.crop((third * size // 3, 0, (third + 1) * size // 3, size))
                self.assertGreater(cells.getextrema()[1], 200, f"more_horizontal@{size}: dot {third} faded")
            for glyph in ("copy", "clipboard_paste", "table"):
                outline = bbox(self.render({"name": "probe", "layers": [{"glyph": glyph}]}, size))
                filled = {"name": "probe", "fill": {"color": "fill_blue"}, "layers": [{"glyph": glyph}]}
                self.assertEqual(outline, bbox(self.render(filled, size)), f"fill {glyph}@{size}")
                banded = {"name": "probe", "layers": [{"glyph": glyph}, band]}
                self.assertEqual(outline, bbox(self.render(banded, size)), f"band {glyph}@{size}")

    def test_cells_are_filled_up_to_their_thin_lines(self):
        # Fluent's filled table has 6/8/6 px columns, the outline 5/6/5 px cells: the fill must
        # still reach every thin line, with no transparent or white sliver beside it.
        entry = next(e for e in bt.load_manifest()["icons"] if e["name"] == "insertcell")
        for mode in ("light", "dark"):
            for size in (24, 32):
                icon = self.render(entry, size, mode)
                lo, hi = round(size * 0.19), size // 2  # top-left cells, clear of the badge
                for y in range(lo, hi):
                    for x in range(lo, hi):
                        r, g, b, a = icon.getpixel((x, y))
                        self.assertGreaterEqual(a, 250, f"{mode}:insertcell@{size} gap at {x},{y}")
                        self.assertLess(min(r, g, b), 240, f"{mode}:insertcell@{size} white at {x},{y}")

    def test_inner_lines_match_the_border(self):
        for mode in ("light", "dark"):
            for size in (24, 32):
                frame_left, *inner, frame_right = self.stroke_widths("table", False, "row", 0.5, False, size, mode)
                self.assertEqual(2, len(inner), f"{mode}:table@{size} inner lines")
                for width in inner:
                    self.assertAlmostEqual(width, frame_left, delta=0.1, msg=f"{mode}:table@{size}")
                    self.assertAlmostEqual(width, frame_right, delta=0.1, msg=f"{mode}:table@{size}")

    def test_vendored_glyphs_exist(self):
        for entry in bt.load_manifest()["icons"]:
            for layer in entry["layers"]:
                if "glyph" in layer and not layer.get("custom"):
                    path = bt.FLUENT / f"{layer['glyph']}_24_{layer.get('style', 'regular')}.svg"
                    self.assertTrue(path.exists(), path)


if __name__ == "__main__":
    unittest.main()

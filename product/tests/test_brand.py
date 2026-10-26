# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""product/brand: the Boost splash and shell logo sources, build_brand.py's PNGs (stock pixel sizes, refused
otherwise) and the sofficerc progress-bar keys it writes."""
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

from product.brand import build_brand

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "product/brand"
STOCK = ROOT / "icon-themes/colibre"
SCRIPT = BRAND / "build_brand.py"
PALETTE = json.loads((ROOT / "product/themes/palette.json").read_text(encoding="utf-8"))
SVG = "{http://www.w3.org/2000/svg}"
STOCK_SOFFICERC = """[Bootstrap]
CrashDumpEnable=true
Logo=1
NativeProgress=false
ProgressBarColor=0,0,0
ProgressFrameColor=102,102,102
ProgressPosition=30,145
ProgressSize=385,8
ProgressPositionHigh=30,200
ProgressSizeHigh=650,12
ProgressTextBaseline=170
ProgressTextColor=0,0,0
URE_BOOTSTRAP=${ORIGIN}/fundamentalrc
"""


def light(token):
    return PALETTE["tokens"][token][0].upper()


def dark(token):
    return PALETTE["tokens"][token][1].upper()


def rgb(token):
    value = int(light(token).lstrip("#"), 16)
    return f"{value >> 16},{(value >> 8) & 255},{value & 255}"


def fills(path):
    return {el.get("fill").upper() for el in ET.parse(path).iter() if el.get("fill") not in (None, "none")}


def texts(path):
    return [el for el in ET.parse(path).iter(SVG + "text")]


def png(path, width, height):
    """A tiny valid PNG of the given size."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    raw = b"".join(b"\0" + b"\0" * (width * 3) for _ in range(height))
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class SourcesTest(unittest.TestCase):

    def test_the_shell_logos_keep_the_stock_sizes(self):
        self.assertEqual(sorted(build_brand.SHELL_LOGOS), sorted(p.name for p in (BRAND / "shell").iterdir()))
        for name in build_brand.SHELL_LOGOS:
            mine = ET.parse(BRAND / "shell" / name).getroot()
            stock = ET.parse(STOCK / "brand/shell" / name).getroot()
            for attr in ("width", "height", "viewBox"):
                self.assertEqual(stock.get(attr), mine.get(attr), f"{name} {attr}")

    def test_the_splash_sources_have_the_stock_pixel_sizes(self):
        for png_name, (svg_name, size) in build_brand.SPLASHES.items():
            self.assertEqual(size, build_brand.png_size(STOCK / "brand_dev" / png_name), png_name)
            self.assertEqual(size, build_brand.svg_size(BRAND / svg_name), svg_name)

    def test_the_brand_is_boost_office_in_inter_with_the_palette_colors(self):
        accents = {light("accent.writer"), light("accent.calc"), light("accent.impress")}
        for name in ("intro.svg", "intro-highres.svg", "shell/logo.svg", "shell/logo-sc.svg"):
            self.assertEqual(["Boost", "Office"], [t.text for t in texts(BRAND / name)], name)
            self.assertEqual({"Inter"}, {t.get("font-family") for t in texts(BRAND / name)}, name)
            self.assertLessEqual(accents | {light("text")}, fills(BRAND / name), name)
        for name in ("intro.svg", "intro-highres.svg"):
            self.assertIn(light("workspace"), fills(BRAND / name), name)
        for name in ("shell/logo_inverted.svg", "shell/logo-sc_inverted.svg"):
            self.assertEqual(["Boost", "Office"], [t.text for t in texts(BRAND / name)], name)
            self.assertEqual({dark("text"), dark("accent.writer"), dark("accent.calc"), dark("accent.impress")},
                             fills(BRAND / name), name)
        self.assertEqual(accents, fills(BRAND / "shell/about.svg"))
        for path in [*BRAND.glob("*.svg"), *(BRAND / "shell").glob("*.svg")]:
            text = path.read_text(encoding="utf-8")
            for word in ("LibreOffice", "Development"):
                self.assertNotIn(word, text, path)

    def test_the_progress_bar_lies_inside_each_splash(self):
        for svg_name, (width, height) in build_brand.SPLASHES.values():
            x, y, w, h = build_brand.progress(BRAND / svg_name)
            self.assertTrue(0 < x and x + w < width and 0 < y and y + h < height, svg_name)


class SofficercTest(unittest.TestCase):

    def test_the_keys_fit_the_splash_and_use_the_palette(self):
        keys = build_brand.sofficerc_keys()
        x, y, w, h = build_brand.progress(BRAND / "intro.svg")
        hx, hy, hw, hh = build_brand.progress(BRAND / "intro-highres.svg")
        self.assertEqual({
            "ProgressBarColor": rgb("text.secondary"), "ProgressFrameColor": rgb("surface.pressed"),
            "ProgressTextColor": rgb("text.secondary"), "ProgressPosition": f"{x},{y}", "ProgressSize": f"{w},{h}",
            "ProgressPositionHigh": f"{hx},{hy}", "ProgressSizeHigh": f"{hw},{hh}",
            "ProgressTextBaseline": str(y + h + 16), "Logo": "1", "NativeProgress": "false",
        }, keys)
        self.assertLess(y + h + 16, build_brand.SPLASHES["intro.png"][1][1])

    def test_edit_replaces_the_keys_and_keeps_every_other_line(self):
        keys = build_brand.sofficerc_keys()
        edited = build_brand.edit_sofficerc(STOCK_SOFFICERC, keys)
        lines = edited.splitlines()
        self.assertEqual("[Bootstrap]", lines[0])
        for line in ("CrashDumpEnable=true", "URE_BOOTSTRAP=${ORIGIN}/fundamentalrc"):
            self.assertIn(line, lines)
        for key, value in keys.items():
            self.assertEqual([f"{key}={value}"], [ln for ln in lines if ln.startswith(key + "=")], key)
        self.assertEqual(edited, build_brand.edit_sofficerc(edited, keys))

    def test_missing_keys_are_added_to_the_bootstrap_section(self):
        edited = build_brand.edit_sofficerc("[Bootstrap]\nURE_BOOTSTRAP=x\n[Other]\nA=b\n", {"Logo": "1"})
        self.assertEqual("[Bootstrap]\nURE_BOOTSTRAP=x\nLogo=1\n[Other]\nA=b\n", edited)

    def test_the_command_edits_a_file_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = Path(tmp) / "sofficerc"
            rc.write_text(STOCK_SOFFICERC, encoding="utf-8")
            out = subprocess.run(["python3", "-I", str(SCRIPT), "sofficerc", str(rc)], capture_output=True,
                                 text=True, check=False)
            self.assertEqual(0, out.returncode, out.stderr)
            self.assertEqual(build_brand.edit_sofficerc(STOCK_SOFFICERC, build_brand.sofficerc_keys()),
                             rc.read_text(encoding="utf-8"))

    def test_a_file_without_a_bootstrap_section_is_refused(self):
        with self.assertRaises(ValueError):
            build_brand.edit_sofficerc("A=b\n", {"Logo": "1"})


class BuildTest(unittest.TestCase):

    def test_check_refuses_a_wrong_size_and_a_missing_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for png_name, (_svg, (width, height)) in build_brand.SPLASHES.items():
                png(out / png_name, width, height)
            build_brand.check(out)
            png(out / "intro.png", 640, 199)
            with self.assertRaisesRegex(ValueError, "640 x 199"):
                build_brand.check(out)
            (out / "intro.png").unlink()
            with self.assertRaisesRegex(ValueError, "intro.png"):
                build_brand.check(out)

    @unittest.skipUnless(shutil.which("rsvg-convert"), "rsvg-convert is not installed")
    def test_build_renders_the_stock_sizes_with_inter(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            run = subprocess.run(["python3", "-I", str(SCRIPT), "build", "--out", str(out)], capture_output=True,
                                 text=True, check=False, timeout=120)
            self.assertEqual(0, run.returncode, run.stderr)
            self.assertEqual(sorted(build_brand.SPLASHES), sorted(p.name for p in out.iterdir()))
            for png_name, (_svg, size) in build_brand.SPLASHES.items():
                self.assertEqual(size, build_brand.png_size(out / png_name), png_name)


if __name__ == "__main__":
    unittest.main()

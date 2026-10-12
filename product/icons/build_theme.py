#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Build the partial "boost" icon themes from vendored Fluent SVGs and a manifest."""
import argparse
import functools
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
FLUENT = HERE / "fluent"
CUSTOM = HERE / "custom"
OVERRIDES = HERE / "overrides"
MANIFEST = HERE / "manifest.json"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

# target size -> source sizes to try, best first
# For 16 px slots the 20 px design is preferred and its 2 px padding is trimmed,
# so it renders 1:1 (pixel-crisp) and fills the slot like Excel's small icons;
# native Fluent 16 px glyphs only fill 14 px and looked undersized next to B/I/U.
SOURCE_SIZES = {16: [20, 16, 24], 24: [24, 20, 28], 32: [32, 28, 24]}
FILE_PREFIX = {16: "cmd/sc_", 24: "cmd/lc_", 32: "cmd/32/"}
THEMES = {"boost": "light", "boost_dark": "dark"}


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def inner_markup(path):
    root = ET.parse(path).getroot()
    return "".join(ET.tostring(child, encoding="unicode") for child in root)


@functools.lru_cache(maxsize=None)
def ring_ink(path, pad):
    """Count visible pixels (alpha > 40) in the outer `pad` px ring of a 20 px glyph."""
    if pad == 0:
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "g.png"
        subprocess.run(["rsvg-convert", "-w", "20", "-h", "20", "-f", "png", "-o", str(png), str(path)], check=True)
        alpha = Image.open(png).convert("RGBA").getchannel("A")
    size = alpha.width
    return sum(1 for i, a in enumerate(alpha.get_flattened_data())
               if a > 40 and min(i % size, i // size, size - 1 - i % size, size - 1 - i // size) < pad)


class Sources:
    """Find glyph SVGs; remember which 16 px icons had to be scaled from 20 px."""

    def __init__(self):
        self.scaled_16 = []

    def load(self, icon, layer, size, stripe=False, also=()):
        """Return (markup, source size, padding to trim) for one glyph layer."""
        glyph, style = layer["glyph"], layer.get("style", "regular")
        if layer.get("custom"):
            # Custom glyphs are drawn on the 24 px grid with 2 px padding.
            native = CUSTOM / f"{glyph}_{size}.svg"
            if native.exists():
                return inner_markup(native), size, 0
            if size == 16:
                self.scaled_16.append(f"{icon}:{glyph}")
            return inner_markup(CUSTOM / f"{glyph}.svg"), 24, (2 if size == 16 else 0)
        order = SOURCE_SIZES[size]
        if size == 16 and stripe:
            order = [16, 20, 24]  # color buttons keep native 16 so the stripe band stays free
        for src in order:
            for base in (OVERRIDES, FLUENT):
                path = base / f"{glyph}_{src}_{style}.svg"
                if path.exists():
                    if size == 16 and src not in (16, 20):
                        self.scaled_16.append(f"{icon}:{glyph}")
                    pad = 0
                    if size == 16 and src == 20 and not stripe:
                        # Trim only the padding that is really empty, for every style that must register.
                        paths = [base / f"{glyph}_20_{s}.svg" for s in {style, *also}]
                        paths = [p if p.exists() else FLUENT / p.name for p in paths]
                        pad = next(n for n in (2, 1, 0) if all(ring_ink(p, n) == 0 for p in paths))
                    return inner_markup(path), src, pad
        raise FileNotFoundError(f"{glyph} ({style}) has no source for {size} px")


def compose(entry, colors, size, sources):
    s = size
    defs, body = [], []
    fill = entry.get("fill")
    if fill:
        # Soft color under the outline, like Office's filled icons: the base
        # glyph's Fluent "filled" silhouette in the fill color. Shapes that the
        # filled variant leaves open stay unfilled, which keeps a touch of white.
        base = next(layer for layer in entry["layers"] if "glyph" in layer)
        silhouette = dict(base, style="filled")
        inner, src, pad = sources.load(entry["name"], silhouette, s, bool(entry.get("stripe")), also=("regular",))
        k = s / (src - 2 * pad) * base.get("scale", 1)
        dx, dy = base.get("dx", 0) * s - pad * k, base.get("dy", 0) * s - pad * k
        body.append(f'<g transform="translate({dx:g} {dy:g}) scale({k:g})" '
                    f'fill="{colors[fill["color"]]}">{inner}</g>')
    for index, layer in enumerate(entry["layers"]):
        color = colors[layer.get("color", "line")]
        scale = layer.get("scale", 1)
        dx, dy = layer.get("dx", 0) * s, layer.get("dy", 0) * s
        if "rect" in layer:
            x, y, w, h = (v * s for v in layer["rect"])
            markup = (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{color}" '
                      f'fill-opacity="{layer.get("opacity", 1)}"/>')
        else:
            also = ("filled",) if fill and layer is base else ()
            inner, src, pad = sources.load(entry["name"], layer, s, bool(entry.get("stripe")), also=also)
            k = s / (src - 2 * pad) * scale
            markup = (f'<g transform="translate({dx - pad * k:g} {dy - pad * k:g}) scale({k:g})" '
                      f'fill="{color}" color="{color}">{inner}</g>')
        if layer.get("knockout"):
            # Cut a gap behind the badge so it stays legible over the base glyph.
            cx, cy, r = dx + scale * s / 2, dy + scale * s / 2, scale * s / 2
            defs.append(f'<mask id="k{index}"><rect width="{s}" height="{s}" fill="#fff"/>'
                        f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="#000"/></mask>')
            body = [f'<g mask="url(#k{index})">{"".join(body)}</g>']
        body.append(markup)
    content = "".join(body)
    stripe = entry.get("stripe")
    if stripe:
        # LibreOffice paints the chosen color over the bottom quarter
        # (svx/source/tbxctrls/tbxcolorupdate.cxx:266-274): keep it empty.
        # "scale" shrinks the art toward the top; "keep" cuts it below that fraction
        # (text_color uses keep 0.6 to drop Fluent's own color bar).
        opts = {"scale": 0.8, "keep": 0.75}
        if isinstance(stripe, dict):
            opts.update(stripe)
        height = min(round(s * opts["keep"]), s - s // 4)
        k = opts["scale"]
        defs.append(f'<clipPath id="top"><rect width="{s}" height="{height}"/></clipPath>')
        content = (f'<g clip-path="url(#top)"><g transform="translate({s * (1 - k) / 2:g} 0) scale({k:g})">'
                   f'{content}</g></g>')
    return (f'<svg xmlns="{SVG_NS}" width="{s}" height="{s}" viewBox="0 0 {s} {s}">'
            f'<defs>{"".join(defs)}</defs>{content}</svg>')


def render_png(svg_text, size, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False, encoding="utf-8") as f:
        f.write(svg_text)
        tmp = Path(f.name)
    try:
        subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-f", "png",
                        "-o", str(out), str(tmp)], check=True)
    finally:
        tmp.unlink()


def build(manifest, out):
    out = Path(out)
    sources = Sources()
    zips = {}
    for theme, mode in THEMES.items():
        colors = manifest["palette"][mode]
        root = out / theme
        if root.exists():
            shutil.rmtree(root)
        links = []
        for entry in manifest["icons"]:
            sizes = [16, 24] + ([32] if entry.get("large") else [])
            for size in sizes:
                target = f"{FILE_PREFIX[size]}{entry['name']}.png"
                render_png(compose(entry, colors, size, sources), size, root / target)
                for alias in entry.get("aliases", []):
                    links.append(f"{FILE_PREFIX[size]}{alias}.png {target}")
        (root / "links.txt").write_text("\n".join(links) + "\n", encoding="utf-8")
        shutil.copyfile(FLUENT / "LICENSE", root / "LICENSE.fluent.txt")
        zip_path = out / f"images_{theme}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    z.write(path, path.relative_to(root).as_posix())
        zips[theme] = zip_path
    return {"zips": zips, "scaled_16": sorted(set(sources.scaled_16))}


def vendor(manifest, src_dir, license_file):
    FLUENT.mkdir(parents=True, exist_ok=True)
    count = 0
    for entry in manifest["icons"]:
        for layer in entry["layers"]:
            if "glyph" not in layer or layer.get("custom"):
                continue
            styles = {layer.get("style", "regular")}
            if entry.get("fill"):
                styles.add("filled")  # silhouette drawn under the outline
            for style in sorted(styles):
                for size in (16, 20, 24, 28, 32):
                    path = Path(src_dir) / f"{layer['glyph']}_{size}_{style}.svg"
                    if path.exists():
                        shutil.copyfile(path, FLUENT / path.name)
                        count += 1
    shutil.copyfile(license_file, FLUENT / "LICENSE")
    return count


def sheet(zips, out):
    """Contact sheet: every icon at 16/24/32 in light and dark, upscaled 2x."""
    rows = []
    for theme, zip_path in zips.items():
        with zipfile.ZipFile(zip_path) as z:
            names = sorted(n for n in z.namelist() if n.startswith("cmd/lc_"))
            for lc in names:
                name = lc.removeprefix("cmd/lc_").removesuffix(".png")
                cells = []
                for member in (f"cmd/sc_{name}.png", lc, f"cmd/32/{name}.png"):
                    if member in z.namelist():
                        with z.open(member) as f:
                            img = Image.open(f).convert("RGBA")
                            cells.append(img.resize((img.width * 2, img.height * 2), Image.NEAREST))
                rows.append((theme, name, cells))
    width, row_h = 520, 72
    canvas = Image.new("RGBA", (width * 2, row_h * ((len(rows) + 1) // 2)), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (theme, name, cells) in enumerate(rows):
        x0, y0 = (i % 2) * width, (i // 2) * row_h
        bg = "#E4F2E8" if theme == "boost" else "#2B2B2B"
        draw.rectangle([x0, y0, x0 + width - 4, y0 + row_h - 4], fill=bg)
        draw.text((x0 + 6, y0 + 6), f"{theme}: {name}", fill="#888888")
        x = x0 + 220
        for cell in cells:
            canvas.alpha_composite(cell, (x, y0 + 4))
            x += cell.width + 12
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("vendor")
    v.add_argument("--from", dest="src", required=True, type=Path)
    v.add_argument("--license", required=True, type=Path)
    b = sub.add_parser("build")
    b.add_argument("--out", type=Path, default=HERE / "out")
    i = sub.add_parser("install")
    i.add_argument("--instdir", type=Path, required=True)
    i.add_argument("--out", type=Path, default=HERE / "out")
    s = sub.add_parser("sheet")
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--build", type=Path, default=HERE / "out")
    args = ap.parse_args(argv)
    manifest = load_manifest()
    if args.cmd == "vendor":
        print(f"vendored {vendor(manifest, args.src, args.license)} files into {FLUENT}")
    elif args.cmd == "build":
        result = build(manifest, args.out)
        print("\n".join(str(p) for p in result["zips"].values()))
        if result["scaled_16"]:
            print("16 px rendered from a 24 px source (blurry):", ", ".join(result["scaled_16"]))
    elif args.cmd == "install":
        for theme in THEMES:
            dest = args.instdir / "share" / "config" / f"images_{theme}.zip"
            shutil.copyfile(args.out / f"images_{theme}.zip", dest)
            print(dest)
    elif args.cmd == "sheet":
        zips = {t: args.build / f"images_{t}.zip" for t in THEMES}
        print(sheet(zips, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

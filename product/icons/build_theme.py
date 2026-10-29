#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Build the partial "boost" icon themes from vendored Fluent SVGs and a manifest."""
import argparse
import base64
import functools
import io
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

# Pillow is imported only in the functions that draw (ring_ink, filled_cells, render_png, sheet), so that
# THEMES can be read without it (product/install/build_xcd.py imports this module).

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
# Office's ribbon icons have hairline outlines; Fluent's regular strokes are heavier on big
# buttons. Regular layers are thinned to TARGET_WEIGHT px; REGULAR_WEIGHT is Fluent's stroke
# per design size (custom glyphs use the same weights on their grid). 16 px slots already
# render 1 px or less and stay as they are.
TARGET_WEIGHT = 1.0
REGULAR_WEIGHT = {16: 1.0, 20: 1.0, 24: 1.5, 28: 1.5, 32: 2.0}
# Thinned icons render at 8x and are box-filtered down: at 1x the erosion mask's partial
# coverage multiplies the glyph's and leaves faint ghosts beside edges, and librsvg rounds
# feMorphology radii up to whole device pixels (0.25 and 0.5 px are 2 and 4 at 8x).
OVERSAMPLE = 8


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
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "g.png"
        subprocess.run(["rsvg-convert", "-w", "20", "-h", "20", "-f", "png", "-o", str(png), str(path)], check=True)
        alpha = Image.open(png).convert("RGBA").getchannel("A")
    size = alpha.width
    return sum(1 for i, a in enumerate(alpha.get_flattened_data())
               if a > 40 and min(i % size, i // size, size - 1 - i % size, size - 1 - i // size) < pad)


class SeedError(ValueError):
    """A fill seed that does not pick a closed part of the glyph."""


@functools.lru_cache(maxsize=None)
def filled_cells(outline, transform, size, seeds, bridge, reach, scale=4):
    """PNG data URI masking the cells of the outline that hold the seed points ((x, y) in px at
    `size`): one element of the icon (a clipboard's board, a page, the rings of the scissors).
    A cell is the outline's free space around the seed, closed on every side. Fluent leaves a
    gap of about one design unit where one object overlaps another (the clipboard stops short
    of its page), so a cell that is open only through gaps narrower than 2 * `bridge` px counts
    as closed: the flood then runs with the outline grown by `bridge` and is grown back by as
    much. The mask also covers the outline ink within `reach` px of the cells, so the fill
    reaches under the line and a thinned line leaves no sliver of white beside it.
    Raises SeedError(index, reason) for a seed on the line or in an open part."""
    from PIL import Image, ImageChops, ImageFilter

    svg = (f'<svg xmlns="{SVG_NS}" width="{size * scale}" height="{size * scale}" '
           f'viewBox="0 0 {size} {size}"><g transform="{transform}">{outline}</g></svg>')
    png = subprocess.run(["rsvg-convert", "-f", "png"], input=svg.encode(), capture_output=True, check=True).stdout
    n = size * scale
    ink = Image.open(io.BytesIO(png)).convert("RGBA").getchannel("A").point(lambda a: 255 if a >= 128 else 0)

    def grown(img, px):
        r = round(px * scale)
        return img.filter(ImageFilter.MaxFilter(2 * r + 1)) if r else img

    def cell(walls, start):
        """The 4-connected free pixels around `start`, and whether they stay off the image border."""
        free = [a == 0 for a in walls.get_flattened_data()]
        free[start], stack, region, closed = False, [start], [], True
        while stack:
            i = stack.pop()
            region.append(i)
            x, y = i % n, i // n
            closed &= 0 < x < n - 1 and 0 < y < n - 1
            for j in (i - 1 if x else -1, i + 1 if x < n - 1 else -1, i - n, i + n):
                if 0 <= j < n * n and free[j]:
                    free[j] = False
                    stack.append(j)
        return region, closed

    cells = bytearray(n * n)
    for index, (x, y) in enumerate(seeds):
        start = min(max(int(y * scale), 0), n - 1) * n + min(max(int(x * scale), 0), n - 1)
        if ink.getpixel((start % n, start // n)):
            raise SeedError(index, "lands on the outline")
        region, closed = cell(ink, start)
        if not closed and bridge:
            walls = grown(ink, bridge)
            if not walls.getpixel((start % n, start // n)):
                region, closed = cell(walls, start)
        if not closed:
            raise SeedError(index, "is not inside a closed part of the glyph")
        for i in region:
            cells[i] = 255
    mask = Image.frombytes("L", (n, n), bytes(cells))
    free = ImageChops.invert(ink)
    for _ in range(round(bridge * scale)):  # grow back what the bridge took, never across a line
        mask = ImageChops.darker(mask.filter(ImageFilter.MaxFilter(3)), free)
    mask = ImageChops.darker(grown(mask, reach), ImageChops.lighter(mask, ink))
    buf = io.BytesIO()
    mask.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


class Sources:
    """Find glyph SVGs; remember which 16 px icons had to be scaled from 20 px."""

    def __init__(self):
        self.scaled_16 = []

    def load(self, icon, layer, size, stripe=False):
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
                        # Trim only the padding that is really empty.
                        pad = next(n for n in (2, 1, 0) if ring_ink(path, n) == 0)
                    return inner_markup(path), src, pad
        raise FileNotFoundError(f"{glyph} ({style}) has no source for {size} px")


def thinning(layer, src, k):
    """Erosion in rendered px that brings a regular layer drawn at scale k down to TARGET_WEIGHT."""
    if layer.get("style", "regular") != "regular":
        return 0.0
    return max(0.0, (REGULAR_WEIGHT[src] * k - TARGET_WEIGHT) / 2)


def anchored(thin):
    """True when thinning removes a whole pixel per stroke (2 px -> 1 px at 32). The art then
    moves up-left by `thin`, so strokes that sat on the pixel grid keep their top/left edge and
    stay crisp. A fractional loss (1.5 px -> 1 px at 24) stays centred: Fluent puts the
    half-pixel edge on either side, so no shift could align every stroke."""
    return bool(thin) and abs(2 * thin - round(2 * thin)) < 1e-6


def placed(inner, x, y, k, paint, thin, mask_id, defs):
    """Glyph markup at (x, y) scaled by k; thin > 0 erodes every edge by `thin` px through a
    round mask over the outline's contours."""
    if anchored(thin):
        x, y = x - thin, y - thin
    transform = f'translate({x:g} {y:g}) scale({k:g})'
    markup = f'<g transform="{transform}" {paint}>{inner}</g>'
    if not thin:
        return markup
    defs.append(f'<mask id="{mask_id}"><rect x="-50%" y="-50%" width="200%" height="200%" fill="#fff"/>'
                f'<g transform="{transform}" fill="none" color="#fff" stroke="#000" '
                f'stroke-width="{2 * thin / k:g}" stroke-linejoin="round">{inner}</g></mask>')
    return f'<g mask="url(#{mask_id})">{markup}</g>'


def compose(entry, colors, size, sources):
    s = size
    defs, body = [], []
    stripe = entry.get("stripe")
    # LibreOffice paints the chosen color over the bottom quarter
    # (svx/source/tbxctrls/tbxcolorupdate.cxx:266-274): keep it empty.
    # "scale" shrinks the art toward the top; "keep" cuts it below that fraction
    # (text_color uses keep 0.6 to drop Fluent's own color bar).
    opts = {"scale": 0.8, "keep": 0.75}
    if isinstance(stripe, dict):
        opts.update(stripe)
    zoom = opts["scale"] if stripe else 1  # applied to the whole art after the layers
    thinned, base_thin = False, 0.0
    base = next((layer for layer in entry["layers"] if "glyph" in layer), None)
    fill = entry.get("fill")
    if fill:
        # One element in a soft tint under the outline, as Microsoft 365's ribbon icons do: the
        # cells of the base glyph that hold the seed points. Seeds are in the 24 px design's
        # units and scale to the source drawn at this size.
        inner, src, pad = sources.load(entry["name"], base, s, bool(stripe))
        k = s / (src - 2 * pad) * base.get("scale", 1)
        thin = thinning(base, src, k * zoom) / zoom
        x, y = base.get("dx", 0) * s - pad * k, base.get("dy", 0) * s - pad * k
        unit = src / 24 * k  # rendered px per 24 px design unit
        seeds = tuple((x + px * unit, y + py * unit) for px, py in fill["at"])
        # Unthinned, the fill reaches the middle of the line, which covers its edge; thinned,
        # it reaches the line's outer edge and is eroded with the line, so both end together.
        weight = REGULAR_WEIGHT[src] * k
        try:
            cells = filled_cells(inner, f'translate({x:g} {y:g}) scale({k:g})', s, seeds, unit,
                                 weight if thin else weight / 2)
        except SeedError as error:
            index, reason = error.args
            raise SeedError(f'{entry["name"]}: fill seed {fill["at"][index]} {reason} at {s} px') from None
        defs.append(f'<mask id="fc"><image href="{cells}" width="{s}" height="{s}"/></mask>')
        markup = f'<rect width="{s}" height="{s}" fill="{colors[fill["color"]]}" mask="url(#fc)"/>'
        if thin:
            thinned = True
            shift = thin if anchored(thin) else 0
            defs.append(f'<filter id="tf"><feMorphology operator="erode" radius="{thin:g}"/></filter>')
            markup = f'<g transform="translate({-shift:g} {-shift:g})"><g filter="url(#tf)">{markup}</g></g>'
        body.append(markup)
    for index, layer in enumerate(entry["layers"]):
        color = colors[layer.get("color", "line")]
        scale = layer.get("scale", 1)
        dx, dy = layer.get("dx", 0) * s, layer.get("dy", 0) * s
        if "rect" in layer:
            # Highlight bands sit on the base glyph's frame, so they follow its thinning.
            x, y, w, h = (v * s for v in layer["rect"])
            if not anchored(base_thin):
                x, y = x + base_thin, y + base_thin
            w, h = w - 2 * base_thin, h - 2 * base_thin
            markup = (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{color}" '
                      f'fill-opacity="{layer.get("opacity", 1)}"/>')
        else:
            inner, src, pad = sources.load(entry["name"], layer, s, bool(stripe))
            k = s / (src - 2 * pad) * scale
            thin = thinning(layer, src, k * zoom) / zoom
            thinned |= thin > 0
            base_thin = thin if layer is base else base_thin
            markup = placed(inner, dx - pad * k, dy - pad * k, k, f'fill="{color}" color="{color}"',
                            thin, f"t{index}", defs)
        if layer.get("knockout"):
            # Cut a gap behind the badge so it stays legible over the base glyph.
            cx, cy, r = dx + scale * s / 2, dy + scale * s / 2, scale * s / 2
            defs.append(f'<mask id="k{index}"><rect width="{s}" height="{s}" fill="#fff"/>'
                        f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="#000"/></mask>')
            body = [f'<g mask="url(#k{index})">{"".join(body)}</g>']
        body.append(markup)
    content = "".join(body)
    if stripe:
        height = min(round(s * opts["keep"]), s - s // 4)
        defs.append(f'<clipPath id="top"><rect width="{s}" height="{height}"/></clipPath>')
        content = (f'<g clip-path="url(#top)"><g transform="translate({s * (1 - zoom) / 2:g} 0) scale({zoom:g})">'
                   f'{content}</g></g>')
    px = s * (OVERSAMPLE if thinned else 1)
    return (f'<svg xmlns="{SVG_NS}" width="{px}" height="{px}" viewBox="0 0 {s} {s}">'
            f'<defs>{"".join(defs)}</defs>{content}</svg>')


def render_png(svg_text, size, out):
    """Render at the SVG's own pixel size, box-filtered down to `size` when it is oversampled."""
    from PIL import Image
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False, encoding="utf-8") as f:
        f.write(svg_text)
        tmp = Path(f.name)
    try:
        subprocess.run(["rsvg-convert", "-f", "png", "-o", str(out), str(tmp)], check=True)
    finally:
        tmp.unlink()
    with Image.open(out) as img:
        if img.size == (size, size):
            return
        small = img.convert("RGBA").resize((size, size), Image.BOX)
    small.save(out)


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
            style = layer.get("style", "regular")
            for size in (16, 20, 24, 28, 32):
                path = Path(src_dir) / f"{layer['glyph']}_{size}_{style}.svg"
                if path.exists():
                    shutil.copyfile(path, FLUENT / path.name)
                    count += 1
    shutil.copyfile(license_file, FLUENT / "LICENSE")
    return count


def sheet(zips, out):
    """Contact sheet: every icon at 16/24/32 in light and dark, upscaled 2x."""
    from PIL import Image, ImageDraw
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
        try:
            result = build(manifest, args.out)
        except SeedError as error:
            sys.exit(f"build_theme.py build: {error}")
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

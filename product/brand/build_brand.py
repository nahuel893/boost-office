#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Boost brand overlay of an installed tree: the splash PNGs and the sofficerc keys that fit them.

  build [--out DIR]   render intro.png and intro-highres.png from intro.svg and intro-highres.svg with rsvg-convert,
                      in Inter from product/fonts/inter (a private fontconfig that holds only those fonts), and refuse
                      a PNG that is not the stock pixel size (default --out: product/brand/out)
  check [--out DIR]   only the size check of the PNGs already in --out
  sofficerc FILE      set the splash keys of an installed program/sofficerc: the progress bar where each splash's
                      #progress rectangle is, in palette.json's light colors

install.sh copies the PNGs and shell/*.svg (the About dialog and Start Center logos, used as they are) over the
installed tree and runs `sofficerc` on its copy; make-release.sh puts prebuilt PNGs into the release archive.
"""
import argparse
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
PALETTE = HERE.parent / "themes" / "palette.json"
FONTS = HERE.parent / "fonts" / "inter"
OUT = HERE / "out"
# The files of <prefix>/program/shell this overlay replaces (donate1.png and donate2.png stay stock).
SHELL_LOGOS = ("about.svg", "logo.svg", "logo_inverted.svg", "logo-sc.svg", "logo-sc_inverted.svg")
# splash PNG -> (its SVG source, the stock pixel size: icon-themes/colibre/brand_dev and brand).
SPLASHES = {"intro.png": ("intro.svg", (644, 199)), "intro-highres.png": ("intro-highres.svg", (990, 254))}
# The VCL splash (desktop/source/splash/splash.cxx) reads ProgressPosition and ProgressSize and draws the status
# text at ProgressTextBaseline; oosplash (desktop/unx/source/splashx.c) reads the *High keys with
# intro-highres.png on a HiDPI screen.
TEXT_GAP = 16
SVG = "{http://www.w3.org/2000/svg}"


def png_size(path):
    """(width, height) from a PNG's IHDR chunk."""
    with open(path, "rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])


def svg_size(path):
    root = ET.parse(path).getroot()
    return int(root.get("width")), int(root.get("height"))


def progress(path):
    """(x, y, width, height) of the splash's #progress rectangle, where the splash draws its progress bar."""
    for el in ET.parse(path).iter(SVG + "rect"):
        if el.get("id") == "progress":
            return tuple(int(el.get(attr)) for attr in ("x", "y", "width", "height"))
    raise ValueError(f"{path} has no rect id=progress")


def _rgb(color):
    value = int(color.lstrip("#"), 16)
    return f"{value >> 16},{(value >> 8) & 255},{value & 255}"


def sofficerc_keys(palette=None):
    """The [Bootstrap] keys of the Boost splash: a neutral progress bar (palette.json light colors) placed where
    each splash source has its #progress rectangle."""
    palette = palette or json.loads(PALETTE.read_text(encoding="utf-8"))
    color = {token: _rgb(values[0]) for token, values in palette["tokens"].items()}
    x, y, w, h = progress(HERE / SPLASHES["intro.png"][0])
    hx, hy, hw, hh = progress(HERE / SPLASHES["intro-highres.png"][0])
    return {
        "Logo": "1",
        "NativeProgress": "false",
        "ProgressBarColor": color["text.secondary"],
        "ProgressFrameColor": color["surface.pressed"],
        "ProgressTextColor": color["text.secondary"],
        "ProgressPosition": f"{x},{y}",
        "ProgressSize": f"{w},{h}",
        "ProgressPositionHigh": f"{hx},{hy}",
        "ProgressSizeHigh": f"{hw},{hh}",
        "ProgressTextBaseline": str(y + h + TEXT_GAP),
    }


def edit_sofficerc(text, keys):
    """text with each key set in its [Bootstrap] section: a key that is there is replaced where it is, a missing
    one is added at the end of the section; every other line stays."""
    lines = text.splitlines()
    try:
        start = lines.index("[Bootstrap]")
    except ValueError:
        raise ValueError("sofficerc has no [Bootstrap] section") from None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))
    todo = dict(keys)
    for i in range(start + 1, end):
        key = lines[i].split("=", 1)[0]
        if "=" in lines[i] and key in todo:
            lines[i] = f"{key}={todo.pop(key)}"
    lines[end:end] = [f"{key}={value}" for key, value in todo.items()]
    return "\n".join(lines) + "\n"


def check(out):
    """Refuse a missing splash PNG or one that is not the stock pixel size."""
    for name, (_svg, size) in SPLASHES.items():
        path = Path(out) / name
        if not path.is_file():
            raise ValueError(f"{path} is missing: run build_brand.py build")
        got = png_size(path)
        if tuple(got) != size:
            raise ValueError(f"{path} is {got[0]} x {got[1]}, not the stock {size[0]} x {size[1]}")


def build(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        conf = Path(tmp) / "fonts.conf"
        conf.write_text('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
                        f"<fontconfig><dir>{escape(str(FONTS))}</dir>"
                        f"<cachedir>{escape(tmp)}/cache</cachedir></fontconfig>\n", encoding="utf-8")
        env = {**os.environ, "FONTCONFIG_FILE": str(conf), "XDG_CACHE_HOME": tmp}
        for name, (svg, (width, height)) in SPLASHES.items():
            if svg_size(HERE / svg) != (width, height):
                raise ValueError(f"{HERE / svg} is {svg_size(HERE / svg)}, not the stock {width} x {height}")
            part = out / (name + ".part")
            subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height), "-f", "png", "-o", str(part),
                            str(HERE / svg)], check=True, env=env)
            part.replace(out / name)
    check(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("build", "check"):
        sub.add_parser(name).add_argument("--out", type=Path, default=OUT)
    sub.add_parser("sofficerc").add_argument("file", type=Path)
    args = ap.parse_args(argv)
    try:
        if args.command == "build":
            build(args.out)
        elif args.command == "check":
            check(args.out)
        else:
            args.file.write_text(edit_sofficerc(args.file.read_text(encoding="utf-8"), sofficerc_keys()),
                                 encoding="utf-8")
    except (ValueError, OSError, subprocess.CalledProcessError) as err:
        print(f"build_brand.py: {err}", file=sys.stderr)
        return 1
    if args.command != "sofficerc":
        for name in SPLASHES:
            print(args.out / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Build the "Boost Light"/"Boost Dark" ColorSchemes as a configuration-only extension."""
import argparse
import json
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

HERE = Path(__file__).resolve().parent
PALETTE = HERE / "palette.json"
IDENTIFIER = "org.boost.colorschemes"

DESCRIPTION = f"""<?xml version="1.0" encoding="UTF-8"?>
<description xmlns="http://openoffice.org/extensions/description/2006"
             xmlns:xlink="http://www.w3.org/1999/xlink">
  <identifier value="{IDENTIFIER}"/>
  <version value="0.1.0"/>
  <display-name><name lang="en">Boost color schemes</name></display-name>
</description>
"""
MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="http://openoffice.org/2001/manifest">
  <manifest:file-entry manifest:media-type="application/vnd.sun.star.configuration-data"
                       manifest:full-path="ColorSchemes.xcu"/>
</manifest:manifest>
"""


def load_palette():
    return json.loads(PALETTE.read_text(encoding="utf-8"))


def scheme_values(palette):
    return {scheme: {role: palette["tokens"][token][index] for role, token in palette["roles"].items()}
            for index, scheme in enumerate(palette["schemes"])}


def document_values(palette):
    return {scheme: {role: palette["tokens"][token][index] for role, token in palette.get("document", {}).items()}
            for index, scheme in enumerate(palette["schemes"])}


def _luminance(hex_color):
    channels = [int(hex_color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def xcu(palette):
    # Same place as the built-in schemes: officecfg/.../Office/UI.xcu:135-142.
    # Colors are xs:int (UI.xcs:53).
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<oor:component-data xmlns:oor="http://openoffice.org/2001/registry"'
             ' xmlns:xs="http://www.w3.org/2001/XMLSchema" oor:name="UI" oor:package="org.openoffice.Office">',
             '  <node oor:name="ColorScheme">',
             '    <node oor:name="ColorSchemes">']
    documents = document_values(palette)
    for scheme, roles in scheme_values(palette).items():
        lines.append(f'      <node oor:name={quoteattr(scheme)} oor:op="replace">')
        roles = {**roles, **documents[scheme]}
        for role, color in roles.items():
            lines.append(f'        <node oor:name="{role}"><prop oor:name="Color">'
                         f'<value>{int(color.lstrip("#"), 16)}</value></prop></node>')
        lines.append("      </node>")
    lines += ["    </node>", "  </node>", "</oor:component-data>"]
    return "\n".join(lines) + "\n"


def build(palette, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("description.xml", DESCRIPTION)
        z.writestr("META-INF/manifest.xml", MANIFEST)
        z.writestr("ColorSchemes.xcu", xcu(palette))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=HERE / "out" / "boost-schemes.oxt")
    args = ap.parse_args(argv)
    print(build(load_palette(), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "vcl/unx/gtk3/custom-theme.cxx"
PALETTE = ROOT / "product/themes/palette.json"
# The styles gallery's frame in the reviewed shots (writer-ribbon-tabs-light.png / -dark.png, x 842, y 90).
REVIEWED_FRAME = ("#DADADB", "#414144")


def rules(source):
    """(selectors, body) of each CSS rule written as C++ string literals in CreateStyleString."""
    out = []
    for match in re.finditer(r'((?:"[^"\n]*,"\s*)*)"([^"\n]*?) ?\{"(.*?)"\}"', source, re.S):
        selectors = re.findall(r'"([^"\n]*),"', match.group(1)) + [match.group(2)]
        out.append(([s.strip() for s in selectors], match.group(3)))
    return out


class FrameBorderTest(unittest.TestCase):

    def setUp(self):
        self.rules = rules(SOURCE.read_text(encoding="utf-8"))

    def test_framed_boxes_take_the_face_color_of_the_scheme(self):
        # G1b (ruling 18): GTK draws the edge of a framed box (a GtkFrame's "frame > border", a scrolled
        # window with a shadow, as the Writer styles gallery, and vcl's native Frame, all ".frame") with the
        # desktop theme's own window colors: #151519 under the user's dark gtk.css in the light look,
        # #DADADB in the reviewed shots. The custom theme now gives it the scheme's FaceColor.
        framed = [(sel, body) for sel, body in self.rules
                  if "frame > border" in sel and "border-color" in body]
        self.assertEqual(1, len(framed), "one rule colors the frame borders")
        selectors, body = framed[0]
        self.assertEqual(["frame > border", ".frame:not(header)"], selectors)
        self.assertIn('border-color: #" + aThemeColors.GetFaceColor().AsRGBHexString() + ";', body)

    def test_the_tab_strip_keeps_its_own_border_color(self):
        # vcl's native notebook header is "notebook > header.frame.top" (salnativewidgets-gtk.cxx,
        # GtkControlPart::NotebookHeader): a bare ".frame" would outrank "notebook > header" and recolor
        # the ribbon's tab strip.
        for selectors, body in self.rules:
            if "border-color" in body:
                self.assertNotIn(".frame", selectors, body)
        header = [body for sel, body in self.rules if "notebook > header" in sel and "border-color" in body]
        self.assertEqual(1, len(header))
        self.assertIn("aNotebookBorderColor", header[0])

    def test_the_face_color_is_the_scheme_color_nearest_the_reviewed_frame(self):
        palette = json.loads(PALETTE.read_text(encoding="utf-8"))
        face = palette["tokens"][palette["roles"]["FaceColor"]]

        def distance(a, b):
            return max(abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) for i in (1, 3, 5))

        for index, reviewed in enumerate(REVIEWED_FRAME):
            values = {role: palette["tokens"][token][index] for role, token in palette["roles"].items()}
            nearest = min(values.values(), key=lambda value: distance(value, reviewed))
            self.assertEqual(nearest, face[index], (reviewed, values))
            self.assertLessEqual(distance(face[index], reviewed), 6)


if __name__ == "__main__":
    unittest.main()

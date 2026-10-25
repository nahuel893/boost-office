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


class StartCenterRulesTest(unittest.TestCase):
    """S2 (ruling 5): the gtk3 custom theme draws the Start Center's tiles (class boost-tile, plus
    boost-tile-<app>) as cards with the app accent as a bottom strip, and its navigation entries (boost-nav)
    flat with a filled neutral selected state, as Office's Home screen does."""

    def setUp(self):
        self.source = SOURCE.read_text(encoding="utf-8")
        self.rules = rules(self.source)

    def rule(self, *selectors):
        found = [body for sel, body in self.rules if sel == list(selectors)]
        self.assertEqual(1, len(found), selectors)
        return found[0]

    def test_tiles_are_cards_with_a_neutral_bottom_strip(self):
        body = self.rule("button.boost-tile")
        self.assertIn('background-color: #" + aThemeColors.GetButtonColor().AsRGBHexString() + ";', body)
        self.assertIn('border: 1px solid #" + aThemeColors.GetFaceColor().AsRGBHexString() + ";', body)
        self.assertIn("border-radius: 4px;", body)
        self.assertIn('box-shadow: inset 0 -4px 0 #" + aThemeColors.GetSeparatorColor().AsRGBHexString() + ";',
                      body)
        hover = self.rule("button.boost-tile:hover")
        self.assertIn('background-color: #" + aThemeColors.GetMenuBarHighlightColor().AsRGBHexString()', hover)

    def test_writer_calc_and_impress_tiles_take_their_tab_accent(self):
        palette = json.loads(PALETTE.read_text(encoding="utf-8"))
        self.assertEqual({"Writer", "Calc", "Impress"}, set(palette["tab_accents"]))
        for app in palette["tab_accents"]:
            body = self.rule("button.boost-tile-" + app.lower())
            self.assertIn('box-shadow: inset 0 -4px 0 #" + lcl_getAppAccentColor(u"%s"_ustr, bDark, '
                          'aThemeColors.GetSeparatorColor()).AsRGBHexString() + ";' % app, body)
        for app in ("draw", "math", "base"):
            self.assertFalse([sel for sel, _ in self.rules if "button.boost-tile-" + app in sel], app)

    def test_the_accent_is_the_toolbarmode_tab_accent_of_the_app(self):
        # The values come from palette.json tab_accents through ToolbarMode Applications/<App> AccentColor and
        # AccentColorDark (product/themes/build_schemes.py, in the scheme extension and boost.xcd), which the
        # notebookbar tab underline reads too (sfx2/source/notebookbar/NotebookbarTabControl.cxx).
        body = re.search(r"Color lcl_getAppAccentColor\(.*?\n\}", self.source, re.S)
        self.assertIsNotNone(body, "no lcl_getAppAccentColor")
        body = body.group(0)
        self.assertIn('"org.openoffice.Office.UI.ToolbarMode/Applications/"', body)
        self.assertIn('bDark ? u"AccentColorDark"_ustr : u"AccentColor"_ustr', body)
        self.assertIn("return rNeutral;", body)
        self.assertIn("const bool bDark = aThemeColors.GetBaseColor().IsDark();", self.source)

    def test_nav_entries_are_flat_with_a_filled_selected_state(self):
        base = self.rule("button.boost-nav")
        self.assertIn("border: 1px solid transparent;", base)
        self.assertIn("box-shadow: none;", base)
        hover = self.rule("button.boost-nav:hover")
        self.assertIn('background-color: #" + aThemeColors.GetMenuBarHighlightColor().AsRGBHexString()', hover)
        checked = self.rule("button.boost-nav:checked", "button.boost-nav:checked:hover")
        self.assertIn('background-color: #" + aThemeColors.GetFaceColor().AsRGBHexString() + ";', checked)
        # "button.flat:hover" draws a SeparatorColor border (the #9E9E9E outline around Home in the S1 shot)
        for body in (hover, checked):
            self.assertIn("border-color: transparent;", body)

    def test_the_start_center_rules_come_after_the_generic_button_rules(self):
        # Same specificity as "button.flat:hover" and "button.flat:checked:hover": the later rule wins.
        last_generic = max(self.source.index('"button.flat:hover {"'),
                           self.source.index('"button.flat:checked:hover {"'))
        self.assertGreater(self.source.index('"button.boost-nav {"'), last_generic)
        self.assertGreater(self.source.index('"button.boost-tile {"'), last_generic)


if __name__ == "__main__":
    unittest.main()

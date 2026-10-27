# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""C1 (product/odd/tasks/ribbon-card.md): under gtk3 the Tabbed Office ribbon is a rounded card on a slightly
darker window background, as Microsoft 365 draws it. The tab names stay on the window background.

Layers: palette.json gives the window color (token "chrome", scheme role InactiveColor, which vcl stores
but draws nothing with); custom-theme.cxx turns it into two CSS nodes, "notebook.boost-ribbon" (the window
around the card) and "notebook.boost-ribbon > stack" (the card); salnativewidgets-gtk.cxx draws vcl's tab
controls with them, header included (TabPaneWithHeader); NotebookbarTabControl.cxx drops the 6 px margin of
its box so the window color reaches the window's edges."""
import json
import re
import unittest
from pathlib import Path

from product.tests.test_custom_theme import rules

ROOT = Path(__file__).resolve().parents[2]
PALETTE = ROOT / "product/themes/palette.json"
THEME = ROOT / "vcl/unx/gtk3/custom-theme.cxx"
NATIVE = ROOT / "vcl/unx/gtk3/salnativewidgets-gtk.cxx"
TABCONTROL = ROOT / "sfx2/source/notebookbar/NotebookbarTabControl.cxx"
# Ruling 2: the window/tab-row background, light and dark; the card keeps the ribbon's color (WindowColor).
CHROME = ("#F0F0F0", "#1F1F1F")


def channels(color):
    return [int(color[i:i + 2], 16) for i in (1, 3, 5)]


def function(source, signature):
    match = re.search(re.escape(signature) + r".*?\n\}", source, re.S)
    assert match, signature
    return match.group(0)


class PaletteTest(unittest.TestCase):

    def setUp(self):
        self.palette = json.loads(PALETTE.read_text(encoding="utf-8"))

    def test_the_window_color_is_its_own_token_in_the_inactive_color_role(self):
        self.assertEqual(list(CHROME), self.palette["tokens"]["chrome"])
        self.assertEqual("chrome", self.palette["roles"]["InactiveColor"])

    def test_no_older_token_has_both_window_colors(self):
        # The light gray (surface.hover, #F0F0F0) is lighter than the card in dark (#383838 > #2B2B2B);
        # the dark one (field, #1F1F1F) is white in light: one token, as ruling 2 allows.
        others = [values for token, values in self.palette["tokens"].items() if token != "chrome"]
        self.assertNotIn(list(CHROME), others)

    def test_the_window_is_a_quiet_neutral_step_darker_than_the_card(self):
        card = self.palette["tokens"][self.palette["roles"]["WindowColor"]]
        for window, surface in zip(self.palette["tokens"]["chrome"], card):
            r, g, b = channels(window)
            self.assertTrue(r == g == b, window)
            step = channels(surface)[0] - r
            self.assertTrue(8 <= step <= 20, (window, surface))


class CustomThemeTest(unittest.TestCase):

    def setUp(self):
        self.source = THEME.read_text(encoding="utf-8")
        self.rules = rules(self.source)

    def rule(self, *selectors):
        found = [body for sel, body in self.rules if sel == list(selectors)]
        self.assertEqual(1, len(found), selectors)
        return found[0]

    def test_the_window_color_is_the_schemes_inactive_color(self):
        body = function(self.source, "std::optional<Color> lcl_getSchemeColor(")
        self.assertIn('u"org.openoffice.Office.UI/ColorScheme"_ustr', body)
        self.assertIn('u"CurrentColorScheme"_ustr', body)
        self.assertIn('openNode(u"ColorSchemes"_ustr)', body)
        self.assertIn('getNodeValue(u"Color"_ustr)', body)
        self.assertIn('lcl_getSchemeColor(u"InactiveColor")', self.source)

    def test_the_window_around_the_card(self):
        body = self.rule("notebook.boost-ribbon")
        self.assertIn('background-color: #" + oRibbonWindow->AsRGBHexString() + ";', body)

    def test_the_card(self):
        body = self.rule("notebook.boost-ribbon > stack")
        self.assertIn('background-color: #" + aThemeColors.GetWindowColor().AsRGBHexString() + ";', body)
        self.assertIn('border: 1px solid #" + aThemeColors.GetFaceColor().AsRGBHexString() + ";', body)
        self.assertIn("border-radius: 8px;", body)
        margin = re.search(r"margin: (\d+)px (\d+)px (\d+)px (\d+)px;", body)
        self.assertIsNotNone(margin, body)
        top, right, bottom, left = map(int, margin.groups())
        self.assertEqual(right, left)
        for side in (right, bottom):
            self.assertTrue(4 <= side <= 6, margin.group(0))

    def test_the_tab_names_sit_on_the_window_color(self):
        # The selected tab keeps only its accent underline (the generic tab:checked rule's box-shadow); a
        # hovered tab takes the face color, visible on the window color in both looks.
        checked = self.rule("notebook.boost-ribbon > header tab:checked",
                            "notebook.boost-ribbon > header tab:checked:hover")
        self.assertIn("background-color: transparent;", checked)
        self.assertNotIn("box-shadow", checked)
        hover = self.rule("notebook.boost-ribbon > header tab:hover")
        self.assertIn('background-color: #" + aThemeColors.GetFaceColor().AsRGBHexString() + ";', hover)

    def test_the_card_rules_come_only_with_a_window_color_and_after_the_notebook_rules(self):
        start = self.source.index('"notebook.boost-ribbon {"')
        guard = self.source.rindex("if (oRibbonWindow)", 0, start)
        self.assertGreater(guard, self.source.index('"notebook > stack:not(:only-child) {"'))
        self.assertGreater(guard, self.source.index('"tabbox > tab:checked:hover, notebook > header tab:checked:hover {"'))


class NativeDrawingTest(unittest.TestCase):

    def setUp(self):
        self.source = NATIVE.read_text(encoding="utf-8")

    def test_the_ribbon_nodes(self):
        body = function(self.source, "const RibbonStyles* lcl_getRibbonStyles(")
        self.assertIn('"notebook", { "boost-ribbon" }', body)
        self.assertIn('"stack", {}', body)
        for node in ('"header", { "frame", "top" }', '"tabs", { "top" }', '"tab", { "top" }'):
            self.assertIn(node, body)
        # the card draws only when the custom theme gives it a margin: no Boost scheme, no card
        self.assertIn("ThemeColors::VclPluginCanUseThemeColors()", body)
        self.assertIn("margin.left > 0", body)

    def test_tab_controls_draw_their_header_with_the_pane_under_the_card_look(self):
        supported = function(self.source, "bool GtkSalGraphics::isNativeControlSupported(")
        self.assertIn("nPart == ControlPart::TabPaneWithHeader", supported)
        self.assertIn("lcl_getRibbonStyles(mpWindowStyle) != nullptr", supported)

    def test_the_pane_paints_the_window_then_the_card_under_the_tab_names(self):
        draw = function(self.source, "bool GtkSalGraphics::drawNativeControl(")
        self.assertIn("renderType = RenderType::RibbonPane;", draw)
        pane = draw[draw.index("case RenderType::RibbonPane:"):]
        pane = pane[:pane.index("break;")]
        self.assertIn("gtk_render_background(pRibbon->mpWindow, cr, nX, nY, nWidth, nHeight);", pane)
        self.assertIn("m_aTabHeaderRect.Bottom()", pane)
        self.assertIn("render_common(pRibbon->mpCard, cr, aCard, flags);", pane)
        self.assertLess(pane.index("gtk_render_background"), pane.index("render_common"))

    def test_the_ribbon_tabs_use_the_ribbon_tab_node(self):
        draw = function(self.source, "bool GtkSalGraphics::drawNativeControl(")
        tab = draw[draw.index("case RenderType::TabItem:"):]
        tab = tab[:tab.index("break;")]
        self.assertIn("pRibbon ? pRibbon->mpTab : mpNotebookHeaderTabsTabStyle", tab)


class NotebookbarTabControlTest(unittest.TestCase):

    def test_the_box_margin_and_the_button_box_go_when_gtk3_draws_the_card(self):
        source = TABCONTROL.read_text(encoding="utf-8")
        body = function(source, "void NotebookbarTabControl::ImplUpdateCardLook()")
        self.assertIn('Application::GetToolkitName() != u"gtk3"', body)
        self.assertIn("IsNativeControlSupported(ControlType::TabPane, ControlPart::TabPaneWithHeader)", body)
        for side in ("margin-start", "margin-end", "margin-top", "margin-bottom"):
            self.assertIn(f'u"{side}"_ustr', body)
        # the menu button at the end of the tab names: flat, not a white button box on the window color
        self.assertIn("pOpenMenu->SetStyle(pOpenMenu->GetStyle() | WB_FLATBUTTON);", body)
        self.assertIn("ImplUpdateCardLook();", function(source, "void NotebookbarTabControl::StateChanged("))


if __name__ == "__main__":
    unittest.main()

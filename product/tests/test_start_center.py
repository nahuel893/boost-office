# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Boost Start Center (feature start-center, rulings 1-3): the layout of sfx2/uiconfig/ui/startcenter.ui,
no donation UI in it or in BackingWindow, the greeting, and the welcome text of the recent documents view."""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "sfx2/uiconfig/ui/startcenter.ui"
CXX = ROOT / "sfx2/source/dialog/backingwindow.cxx"
HXX = ROOT / "sfx2/source/dialog/backingwindow.hxx"
RECENT = ROOT / "sfx2/source/control/recentdocsview.cxx"
STRINGS = ROOT / "include/sfx2/strings.hrc"
DIALOGS_TEST = ROOT / "sfx2/qa/unit/data/sfx2-dialogs-test.txt"
RECENT_HXX = ROOT / "sfx2/inc/recentdocsview.hxx"
SUPPR = ROOT / "solenv/sanitizers/ui/sfx.suppr"

NAV = [("open_recent", "Home"), ("templates_all", "New"), ("open_all", "Open"), ("open_remote", "Open Remote")]
TILES = [("writer_all", "Blank document", "res/odt_48_8.png"),
         ("calc_all", "Blank workbook", "res/ods_48_8.png"),
         ("impress_all", "Blank presentation", "res/odp_48_8.png"),
         ("draw_all", "Drawing", "res/odg_48_8.png"),
         ("math_all", "Formula", "res/odf_48_8.png"),
         ("database_all", "Database", "res/odb_48_8.png")]
DONATION_IDS = ["donate", "donate_image", "gdDonation", "imgDonationLeft", "imgDonationRight", "btnDonateLink",
                "lbDonateTitle", "lbDonateText"]


def ui_root():
    return ET.parse(UI).getroot()


def by_id(root, wid):
    return root.find(".//object[@id='%s']" % wid)


def prop(obj, name):
    return obj.findtext("property[@name='%s']" % name)


def children(obj):
    """The direct child objects of a container, in packing order (document order when unpositioned)."""
    kids = []
    for i, child in enumerate(obj.findall("child")):
        kid = child.find("object")
        if child.get("type") is not None or kid is None:
            continue
        pos = child.findtext("packing/property[@name='position']")
        kids.append((int(pos) if pos is not None else i, i, kid))
    return [kid for _, _, kid in sorted(kids, key=lambda t: t[:2])]


def label_text(obj):
    return (prop(obj, "label") or "").replace("_", "")


def ancestors(root, wid):
    parents = {c: p for p in root.iter() for c in p}
    node, out = by_id(root, wid), []
    while node is not None:
        node = parents.get(node)
        if node is not None and node.tag == "object":
            out.append(node.get("id"))
    return out


class StartCenterUi(unittest.TestCase):

    def setUp(self):
        self.root = ui_root()

    def test_parses_and_stays_in_the_dialogs_test(self):
        self.assertEqual("interface", self.root.tag)
        self.assertIsNotNone(by_id(self.root, "StartCenter"))
        self.assertIn("sfx/ui/startcenter.ui", DIALOGS_TEST.read_text(encoding="utf-8").split())

    def test_ids_are_unique(self):
        ids = [o.get("id") for o in self.root.iter("object") if o.get("id")]
        self.assertEqual(len(ids), len(set(ids)), [i for i in ids if ids.count(i) > 1])

    def test_brand_text_replaces_the_logo_and_the_frame_title(self):
        brand = by_id(self.root, "brand_label")
        self.assertIsNotNone(brand)
        self.assertEqual("Boost Office", prop(brand, "label"))
        weights = [a.get("value") for a in brand.findall("attributes/attribute[@name='weight']")]
        self.assertEqual(["bold"], weights)
        self.assertIsNone(by_id(self.root, "daBrand"))
        self.assertIsNone(by_id(self.root, "label1"))
        self.assertNotIn(">Application<", UI.read_text(encoding="utf-8"))
        # first in the navigation column
        self.assertEqual("brand_label", children(by_id(self.root, "all_buttons_box"))[0].get("id"))

    def test_navigation_entries_in_order(self):
        nav = [k for k in children(by_id(self.root, "buttons_box")) if k.get("id") in dict(NAV)]
        self.assertEqual([n for n, _ in NAV], [k.get("id") for k in nav])
        for obj, (_, caption) in zip(nav, NAV):
            self.assertEqual(caption, label_text(obj), obj.get("id"))
        self.assertEqual("GtkToggleButton", by_id(self.root, "open_recent").get("class"))
        self.assertEqual("GtkToggleButton", by_id(self.root, "templates_all").get("class"))

    def test_help_and_extensions_at_the_bottom_of_the_column(self):
        column = [k.get("id") for k in children(by_id(self.root, "all_buttons_box"))]
        self.assertLess(column.index("buttons_box"), column.index("small_buttons_box"))
        self.assertEqual("small_buttons_box", column[-1])
        self.assertEqual(["help", "extensions"],
                         [k.get("id") for k in children(by_id(self.root, "small_buttons_box"))])
        self.assertEqual("True", prop(by_id(self.root, "buttons_box"), "vexpand"))

    def test_right_pane_order(self):
        pane = [k.get("id") for k in children(by_id(self.root, "box2"))]
        for earlier, later in (("greeting", "tiles_box"), ("tiles_box", "actions"), ("actions", "scrollrecent"),
                               ("actions", "scrolllocal")):
            self.assertLess(pane.index(earlier), pane.index(later), (earlier, later))
        self.assertIn("section_label", [k.get("id") for k in children(by_id(self.root, "actions"))])
        self.assertIn("box2", ancestors(self.root, "greeting"))

    def test_tile_row(self):
        row = children(by_id(self.root, "tiles_box"))
        self.assertEqual([t for t, _, _ in TILES], [k.get("id") for k in row])
        for obj, (wid, caption, icon) in zip(row, TILES):
            self.assertEqual(caption, label_text(obj), wid)
            self.assertEqual("top", prop(obj, "image-position"), wid)
            self.assertEqual("True", prop(obj, "always-show-image"), wid)
            image = by_id(self.root, prop(obj, "image"))
            self.assertEqual(icon, prop(image, "icon-name"), wid)
        # one minimum tile size; a long caption may widen its tile so the row still fits a 1024 px screen
        self.assertEqual({"112"}, {prop(k, "width-request") for k in row})
        self.assertNotEqual("True", prop(by_id(self.root, "tiles_box"), "homogeneous"))

    def test_views_and_controls_kept(self):
        for wid in ("all_recent", "local_view", "scrollrecent", "scrolllocal", "cbFilter", "mbActions", "lbFilter",
                    "althelplabel", "localmenu", "clearmenu", "clear_all", "clear_unavailable",
                    "all_recent_label", "local_view_label"):
            self.assertIsNotNone(by_id(self.root, wid), wid)

    def test_no_donation_widgets(self):
        for wid in DONATION_IDS:
            self.assertIsNone(by_id(self.root, wid), wid)
        text = UI.read_text(encoding="utf-8")
        self.assertNotIn("donate", text.lower())

    def test_every_welded_id_exists(self):
        src = CXX.read_text(encoding="utf-8")
        ids = set(re.findall(r'weld_\w+\(u"(\w+)"_ustr', src))
        ids |= set(re.findall(r'CustomWeld\(\*m_xBuilder, u"(\w+)"_ustr', src))
        self.assertGreater(len(ids), 20)
        for wid in sorted(ids):
            self.assertIsNotNone(by_id(self.root, wid), wid)


class BackingWindowSource(unittest.TestCase):

    def test_no_donation_code(self):
        for path in (CXX, HXX):
            src = path.read_text(encoding="utf-8")
            for word in ("Donat", "donat", "ShowDonation", "BMP_DONATE", "SID_DONATION", "BrandImage",
                         "VolunteerURL", "loadBrandSvg"):
                self.assertNotIn(word, src, "%s in %s" % (word, path.name))

    def test_extensions_button_opens_the_extensions_site(self):
        src = CXX.read_text(encoding="utf-8")
        self.assertIn("ExtensionsURL", src)

    def test_greeting_by_local_time(self):
        src = CXX.read_text(encoding="utf-8")
        body = re.search(r"OUString BackingWindow::greetingForHour\(int nHour\)\n\{(.*?)\n\}", src, re.S)
        self.assertTrue(body, "no BackingWindow::greetingForHour")
        body = body.group(1)
        self.assertRegex(body, r"nHour < 12\)\s*return SfxResId\(STR_START_GREETING_MORNING\)")
        self.assertRegex(body, r"nHour < 18\)\s*return SfxResId\(STR_START_GREETING_AFTERNOON\)")
        self.assertRegex(body, r"return SfxResId\(STR_START_GREETING_EVENING\)")
        self.assertIn("tools::Time", src)
        self.assertIn('weld_label(u"greeting"_ustr)', src)

    def test_heading_follows_the_nav_toggles(self):
        src = CXX.read_text(encoding="utf-8")
        toggle = re.search(r"IMPL_LINK\( BackingWindow, ToggleHdl.*?\n\}", src, re.S).group(0)
        self.assertIn("STR_START_RECENT", toggle)
        self.assertIn("STR_START_TEMPLATES", toggle)
        self.assertIn('weld_label(u"section_label"_ustr)', src)


class StartCenterStrings(unittest.TestCase):

    def define(self, name):
        m = re.search(r'#define %s\s+NC_\("%s", "(.*)"\)' % (name, name), STRINGS.read_text(encoding="utf-8"))
        self.assertTrue(m, name)
        return m.group(1)

    def test_greetings_and_headings(self):
        self.assertEqual("Good morning", self.define("STR_START_GREETING_MORNING"))
        self.assertEqual("Good afternoon", self.define("STR_START_GREETING_AFTERNOON"))
        self.assertEqual("Good evening", self.define("STR_START_GREETING_EVENING"))
        self.assertEqual("Recent", self.define("STR_START_RECENT"))
        self.assertEqual("Templates", self.define("STR_START_TEMPLATES"))

    def test_welcome_text(self):
        self.assertEqual("Welcome to Boost Office", self.define("STR_WELCOME_LINE1"))
        self.assertEqual("Drop a document here or create a new one above.", self.define("STR_WELCOME_LINE2"))

    def test_recent_view_draws_no_logo(self):
        src = RECENT.read_text(encoding="utf-8")
        self.assertIn("STR_WELCOME_LINE1", src)
        self.assertNotIn("GetApplicationLogo", src)


def style_classes(obj):
    return [c.get("name") for c in obj.findall("style/class")]


class StartCenterStyle(unittest.TestCase):
    """S2 (rulings 4, 5): the CSS classes the gtk3 custom theme draws the tile accents and the selected
    navigation entry with, and the workspace color of the content pane."""

    def setUp(self):
        self.root = ui_root()

    def test_every_tile_is_a_boost_tile_with_its_app(self):
        for wid, app in (("writer_all", "writer"), ("calc_all", "calc"), ("impress_all", "impress"),
                         ("draw_all", "draw"), ("math_all", "math"), ("database_all", "base")):
            self.assertEqual(["boost-tile", "boost-tile-" + app], style_classes(by_id(self.root, wid)), wid)

    def test_every_nav_entry_is_a_boost_nav_entry(self):
        for wid, _ in NAV:
            self.assertEqual(["boost-nav"], style_classes(by_id(self.root, wid)), wid)
        for wid in ("help", "extensions"):
            self.assertEqual(["boost-nav"], style_classes(by_id(self.root, wid)), wid)

    def test_the_content_pane_and_the_window_take_the_workspace_color(self):
        # The scheme's WindowColor (surface, #FFFFFF / #2B2B2B) is what GetWindowColor() and the gtk3 theme's
        # ".background" give; the workspace is the scheme's AppBackground (palette "document" role), which
        # svtools::ColorConfig reads from the active scheme.
        src = CXX.read_text(encoding="utf-8")
        body = re.search(r"void BackingWindow::ApplyStyleSettings\(\)\n\{(.*?)\n\}", src, re.S).group(1)
        self.assertIn("svtools::ColorConfig().GetColorValue(svtools::APPBACKGROUND).nColor", body)
        self.assertIn("m_xContainer->set_background(aWorkspace);", body)
        self.assertIn("SetBackground(aWorkspace);", body)
        self.assertIn("mxAllButtonsBox->set_background(aNavBackground);", body)
        self.assertIn("mxSmallButtonsBox->set_background(aNavBackground);", body)
        self.assertIn("rStyleSettings.GetWindowColor()", body)


class StartCenterCleanup(unittest.TestCase):

    def test_no_unused_welcome_image(self):
        self.assertNotIn("maWelcomeImage", RECENT_HXX.read_text(encoding="utf-8"))
        self.assertNotIn("maWelcomeImage", RECENT.read_text(encoding="utf-8"))

    def test_every_start_center_suppression_names_an_existing_id(self):
        root = ui_root()
        lines = [line for line in SUPPR.read_text(encoding="utf-8").splitlines()
                 if line.startswith("sfx2/uiconfig/ui/startcenter.ui:")]
        self.assertGreater(len(lines), 0)
        for line in lines:
            wid = re.search(r"@id='([^']+)'", line).group(1)
            self.assertIsNotNone(by_id(root, wid), line)


if __name__ == "__main__":
    unittest.main()

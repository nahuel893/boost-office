# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import unittest
from pathlib import Path

from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_home.json"
UPSTREAM = ROOT / "sc/uiconfig/scalc/ui/notebookbar.ui"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
SECTIONS = ["Undo", "Clipboard", "Font", "Alignment", "Number", "Styles", "Cells", "Editing"]


class CalcHomeUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))

    def test_sections_follow_annex_1(self):
        self.assertEqual(SECTIONS, [s["name"] for s in self.layout["sections"]])

    def test_office_ui_is_upstream_plus_home_layout(self):
        # Only the Home page may differ from upstream notebookbar.ui; this also
        # proves the file can be regenerated after re-copying a newer upstream.
        expected = g.splice(UPSTREAM.read_text(encoding="utf-8"), self.layout, g.emit_page(self.layout))
        self.assertEqual(expected, OFFICE.read_text(encoding="utf-8"))

    def test_no_italic_captions_on_home(self):
        text = OFFICE.read_text(encoding="utf-8")
        page = text.split("<!-- product:Home-begin -->")[1].split("<!-- product:Home-end -->")[0]
        self.assertNotIn('name="style" value="italic"', page)


if __name__ == "__main__":
    unittest.main()

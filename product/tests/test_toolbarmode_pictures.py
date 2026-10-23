# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Tabbed Office preview pictures of the View > User Interface dialog (cui UITabPage::UpdateImage)."""
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PICTURES = ROOT / "extras/source/toolbarmode"
MAKEFILE = ROOT / "vcl/Package_toolbarmode.mk"


class ToolbarmodePicturesTest(unittest.TestCase):

    def test_pictures_are_321_by_125_pngs(self):
        for name in ("notebookbar_office.png", "notebookbar_office_writer.png"):
            path = PICTURES / name
            self.assertTrue(path.is_file(), name)
            with Image.open(path) as im:
                self.assertEqual("PNG", im.format, name)
                self.assertEqual((321, 125), im.size, name)

    def test_writer_picture_differs_from_the_shared_one(self):
        with Image.open(PICTURES / "notebookbar_office.png") as a, \
                Image.open(PICTURES / "notebookbar_office_writer.png") as b:
            self.assertNotEqual(a.convert("RGB").tobytes(), b.convert("RGB").tobytes())

    def test_writer_picture_is_packaged(self):
        files = [line.strip().rstrip("\\").strip() for line in MAKEFILE.read_text(encoding="utf-8").splitlines()]
        self.assertIn("notebookbar_office_writer.png", files)
        self.assertIn("notebookbar_office.png", files)


if __name__ == "__main__":
    unittest.main()

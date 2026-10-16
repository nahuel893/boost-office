# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The per-tab test modules walk a section's toolboxes the way the generator does: footer included."""
import importlib
import unittest

TAB_MODULES = ["insert", "formulas", "pagelayout", "review", "view", "help"]
SECTION = {"name": "S", "columns": [[{"id": "A", "items": [{"cmd": "One"}]}],
                                    [{"id": "B", "items": [{"cmd": "Two"}]}]],
           "footer": {"id": "F", "items": [{"cmd": "Footer"}]}}


class FooterIsNotSkippedTest(unittest.TestCase):

    def test_every_tab_test_module_sees_the_footer_items(self):
        for name in TAB_MODULES:
            module = importlib.import_module("product.tests.test_calc_%s_ui" % name)
            test = next(v for v in vars(module).values()
                        if isinstance(v, type) and issubclass(v, unittest.TestCase)
                        and "boxes" in vars(v))
            ids = [b["id"] for b in test.boxes(test("setUp"), SECTION)]
            self.assertEqual(["A", "B", "F"], ids, name)
            items = [i["cmd"] for b in test.boxes(test("setUp"), SECTION) for i in b["items"]]
            self.assertIn("Footer", items, name)


if __name__ == "__main__":
    unittest.main()

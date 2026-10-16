# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The placeholder registry helpers: an entry flagged "implemented" is no placeholder any more."""
import json
import tempfile
import unittest
from pathlib import Path

from product.tests import placeholders


class ImplementedEntriesTest(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.copy = Path(tmp.name) / "placeholders.json"
        entries = placeholders.load_all()
        # one plain slot and one family slot become implemented in the temporary copy
        self.plain = next(e for e in entries if "variants" not in e and "label" in e)
        self.family = next(e for e in entries if "variants" in e and "variant_labels" in e)
        for entry in entries:
            if entry in (self.plain, self.family):
                entry["implemented"] = True
        self.copy.write_text(json.dumps(entries), encoding="utf-8")

    def test_the_real_registry_has_no_implemented_entry_unless_flagged(self):
        self.assertEqual(placeholders.load_all(), placeholders.load_all(placeholders.REGISTRY))
        self.assertEqual(len(placeholders.load_all()),
                         len(placeholders.load()) + len(placeholders.implemented()))

    def test_load_keeps_only_the_placeholders_but_load_all_keeps_every_slot(self):
        self.assertEqual(len(placeholders.load_all(self.copy)) - 2, len(placeholders.load(self.copy)))
        self.assertNotIn(self.plain["slot"], [e["slot"] for e in placeholders.load(self.copy)])
        self.assertIn(self.plain["slot"], [e["slot"] for e in placeholders.load_all(self.copy)])

    def test_labels_exclude_the_implemented_entries(self):
        base = ".uno:" + self.plain["command"]
        self.assertIn(base, placeholders.labels_by_url())
        self.assertNotIn(base, placeholders.labels_by_url(self.copy))
        self.assertNotIn(self.plain["command"], placeholders.labelled(self.copy))
        family_base = ".uno:" + self.family["command"]
        self.assertTrue([u for u in placeholders.labels_by_url() if u.startswith(family_base)])
        self.assertEqual([], [u for u in placeholders.labels_by_url(self.copy) if u.startswith(family_base)])

    def test_urls_of_an_implemented_family_are_dropped_from_a_label_table(self):
        table = {".uno:" + self.plain["command"]: "x",
                 **{u: "y" for u in placeholders.urls(self.family)}, ".uno:Other": "z"}
        self.assertEqual({".uno:Other": "z"}, placeholders.drop_implemented(table, self.copy))
        self.assertEqual(table, placeholders.drop_implemented(table))

    def test_every_placeholder_url_counts_one_per_variant(self):
        total = sum(len(placeholders.urls(e)) for e in placeholders.load())
        self.assertEqual(total, len(placeholders.all_urls()))
        self.assertEqual(total - len(placeholders.urls(self.plain)) - len(placeholders.urls(self.family)),
                         len(placeholders.all_urls(self.copy)))


if __name__ == "__main__":
    unittest.main()

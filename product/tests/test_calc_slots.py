# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Every placeholder slot of the ribbon tabs: sc.hrc, scalc.sdi, cellsh.sdi, cellsh.cxx."""
import re
import unittest
from pathlib import Path

from product.tests import placeholders

ROOT = Path(__file__).resolve().parents[2]
HRC = ROOT / "sc/inc/sc.hrc"
FORK_FIRST, FORK_LAST = 380, 424      # reserved for this fork; +424 is the last Calc slot id
DATA_LAST, SLICE_FIRST, SLICE_LAST = 388, 389, 421


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def hrc_offsets():
    return {m.group(1): int(m.group(2)) for m in re.finditer(
        r"#define\s+(\w+)\s+(?:TypedWhichId<\w+>)?\(SID_NEW_SLOTS\s*\+\s*(\d+)\)", read("sc/inc/sc.hrc"))}


class PlaceholderSlotsTest(unittest.TestCase):

    def setUp(self):
        self.entries = placeholders.load()
        self.offsets = hrc_offsets()

    def test_registry_covers_data_and_the_whole_slice_without_gaps(self):
        offsets = [e["offset"] for e in self.entries]
        self.assertEqual(list(range(FORK_FIRST, SLICE_LAST + 1)), offsets)
        self.assertEqual(len({e["slot"] for e in self.entries}), len(self.entries))
        self.assertEqual(len({e["command"] for e in self.entries}), len(self.entries))

    def test_registry_variants_are_well_formed(self):
        for entry in self.entries:
            variants = entry.get("variants", [])
            self.assertEqual(len(variants), len(set(variants)), entry["command"])
            for variant in variants:
                self.assertRegex(variant, r"^\w+:(string|long|boolean)=[\w.-]+$", entry["command"])

    def test_every_slot_is_defined_in_sc_hrc_inside_the_fork_block(self):
        for entry in self.entries:
            self.assertEqual(entry["offset"], self.offsets.get(entry["slot"]), entry["slot"])
            self.assertTrue(FORK_FIRST <= entry["offset"] <= FORK_LAST, entry["slot"])

    def test_the_fork_block_has_no_gaps_and_no_duplicates(self):
        fork = sorted(v for v in self.offsets.values() if v >= FORK_FIRST)
        self.assertEqual(list(range(FORK_FIRST, FORK_FIRST + len(fork))), fork)
        values = list(self.offsets.values())
        self.assertEqual(len(values), len(set(values)), "duplicate SID_NEW_SLOTS offsets")
        self.assertLessEqual(max(values), FORK_LAST)

    def test_the_functional_slots_of_later_tasks_are_not_taken_yet(self):
        self.assertNotIn(15, self.offsets.values())
        self.assertNotIn(16, self.offsets.values())

    def test_sc_hrc_comment_describes_the_fork_block(self):
        text = re.sub(r"\s*//\s*", " ", read("sc/inc/sc.hrc"))
        self.assertIn("SID_NEW_SLOTS+380..+424 reserved for this fork (Data +380..+388, remaining tabs"
                      " +389..+421, spare +422..+424); +424 is the last Calc slot id", text)

    def test_every_slot_has_a_scalc_sdi_entry_hidden_from_customize_and_writable(self):
        sdi = read("sc/sdi/scalc.sdi")
        for entry in self.entries:
            m = re.search(r"SfxVoidItem " + entry["command"] + " " + entry["slot"] + r"\n\(\)\n\[(.*?)\n\]",
                          sdi, re.S)
            self.assertIsNotNone(m, entry["command"])
            self.assertIn("ReadOnlyDoc = FALSE", m.group(1), entry["command"])
            for flag in ("MenuConfig", "ToolBoxConfig", "AccelConfig"):
                self.assertIn(flag + " = FALSE", m.group(1), entry["command"] + " " + flag)

    def test_every_slot_has_a_state_method_and_no_execute_method(self):
        cell = read("sc/sdi/cellsh.sdi")
        for entry in self.entries:
            row = re.search(r"^\s*" + entry["slot"] + r"\s*\[(.*)\]", cell, re.M)
            self.assertIsNotNone(row, entry["slot"])
            self.assertIn("StateMethod = GetState", row.group(1), entry["slot"])
            self.assertNotIn("ExecMethod", row.group(1), entry["slot"])

    def test_every_slot_is_in_the_always_disabled_list_and_has_no_execute_path(self):
        files = {p: p.read_text(encoding="utf-8") for p in (ROOT / "sc/source/ui/view").glob("cellsh*.cxx")}
        for entry in self.entries:
            hits = []
            for path, text in files.items():
                for m in re.finditer(r"((?:\s*case \w+:\n)+)(.*?)break;", text, re.S):
                    if entry["slot"] in re.findall(r"case (\w+):", m.group(1)):
                        hits.append((path.name, m.group(2)))
            self.assertEqual(["cellsh.cxx"], [name for name, _ in hits], entry["slot"])
            self.assertIn("rSet.DisableItem( nWhich );", hits[0][1], entry["slot"])
            for path, text in files.items():
                self.assertEqual(1 if path.name == "cellsh.cxx" else 0,
                                 len(re.findall(r"\b" + entry["slot"] + r"\b", text)), (path.name, entry["slot"]))

    def test_no_slot_is_referenced_by_any_other_source(self):
        # Beyond sc.hrc, scalc.sdi, cellsh.sdi and the cellsh.cxx case list nothing may use a
        # placeholder slot: an Execute or another GetState would make it a real command.
        allowed = {HRC, ROOT / "sc/sdi/scalc.sdi", ROOT / "sc/sdi/cellsh.sdi",
                   ROOT / "sc/source/ui/view/cellsh.cxx"}
        names = [e["slot"] for e in self.entries]
        pattern = re.compile(r"\b(" + "|".join(map(re.escape, names)) + r")\b")
        for path in list((ROOT / "sc").rglob("*.cxx")) + list((ROOT / "sc").rglob("*.hxx")) \
                + list((ROOT / "sc").rglob("*.sdi")) + list((ROOT / "sc").rglob("*.hrc")):
            if path in allowed or ".git" in path.parts:
                continue
            self.assertIsNone(pattern.search(path.read_text(encoding="utf-8", errors="replace")), str(path))


if __name__ == "__main__":
    unittest.main()

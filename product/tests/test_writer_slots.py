# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Every placeholder slot of the Writer ribbon: cmdid.h, swriter.sdi, viewsh.sdi, viewstat.cxx."""
import re
import unittest
from pathlib import Path

from product.tests import placeholders

ROOT = Path(__file__).resolve().parents[2]
CMDID = ROOT / "sw/inc/cmdid.h"
SDI = ROOT / "sw/sdi/swriter.sdi"
VIEW_SDI = ROOT / "sw/sdi/viewsh.sdi"
VIEWSTAT = ROOT / "sw/source/uibase/uiview/viewstat.cxx"
REGISTRY = placeholders.registry("writer")
FN_BOOST = 25900                      # SID_SW_START + 5900: the fork block, ids 25900..25999
BLOCK_SIZE, SLOT_COUNT, URL_COUNT = 100, 24, 48
# design 3.3: the headers whose #defines share the Writer id range (SID_SW_START .. SID_SC_START - 1)
ID_HEADERS = ["include/svl/solar.hrc", "include/sfx2/sfxsids.hrc", "include/svx/svxids.hrc",
              "include/editeng/editids.hrc", "sw/inc/cmdid.h"]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def boost_offsets():
    """FN_BOOST_* name -> offset, from the "(FN_BOOST + n)" defines of cmdid.h."""
    return {m.group(1): int(m.group(2)) for m in re.finditer(
        r"^#define\s+(FN_BOOST_\w+)\s+\(FN_BOOST\s*\+\s*(\d+)\)", read(CMDID), re.M)}


TOKEN = re.compile(r"0[xX][0-9a-fA-F]+|\d+[uUlL]*|[A-Za-z_]\w*|<<|>>|[-+*/()|&~]|\S")


def define_values():
    """Evaluate every object-like #define of the id headers and the sw .hrc files.

    Returns [(name, value, file)] for each define that evaluates to an integer; a name that
    resolves to a string or to something unknown is skipped. "TypedWhichId<T>(expr)" counts as
    expr. Defines are resolved again until nothing changes, so the file order does not matter.
    """
    files = [ROOT / p for p in ID_HEADERS] + sorted((ROOT / "sw").rglob("*.hrc"))
    raw = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace").replace("\\\n", " ")
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        for m in re.finditer(r"^[ \t]*#[ \t]*define[ \t]+(\w+)(?!\()[ \t]+(.+)$", text, re.M):
            expr = re.sub(r"TypedWhichId<[^>]*>", "", m.group(2).split("//")[0]).strip()
            raw.append((m.group(1), expr, path.relative_to(ROOT).as_posix()))
    known, values, pending = {}, {}, list(range(len(raw)))
    while pending:
        left = []
        for i in pending:
            name, expr, _ = raw[i]
            value = evaluate(expr, known)
            if value is None:
                left.append(i)
                continue
            values[i] = value
            known.setdefault(name, value)
        if len(left) == len(pending):
            break
        pending = left
    return [(raw[i][0], values[i], raw[i][2]) for i in sorted(values)]


def evaluate(expr, known):
    """The integer value of a C constant expression, or None if a name is unknown."""
    out = []
    for token in TOKEN.findall(expr):
        if token[0].isdigit():
            out.append(str(int(token.rstrip("uUlL"), 0)))
        elif token[0].isalpha() or token[0] == "_":
            if token not in known:
                return None
            out.append(str(known[token]))
        elif token in ("<<", ">>", "+", "-", "*", "(", ")", "|", "&", "~"):
            out.append(token)
        elif token == "/":
            out.append("//")
        else:
            return None
    if not out:
        return None
    try:
        value = eval(" ".join(out), {"__builtins__": {}})   # digits and operators only
    except (SyntaxError, TypeError, ZeroDivisionError):
        return None
    return value if isinstance(value, int) else None


class WriterPlaceholderSlotsTest(unittest.TestCase):

    def setUp(self):
        self.all_entries = placeholders.load_all(REGISTRY)   # every slot of the fork block
        self.entries = placeholders.load(REGISTRY)           # the placeholders: not flagged "implemented"
        self.offsets = boost_offsets()

    def test_registry_has_no_duplicates_and_stays_inside_the_block(self):
        # an implemented entry stays in the registry ("implemented": true), so the registry
        # keeps every slot of the block
        offsets = [e["offset"] for e in self.all_entries]
        self.assertEqual(list(range(SLOT_COUNT)), offsets)
        self.assertEqual(len({e["slot"] for e in self.all_entries}), len(self.all_entries))
        self.assertEqual(len({e["command"] for e in self.all_entries}), len(self.all_entries))
        self.assertTrue(all(e["slot"].startswith("FN_BOOST_") for e in self.all_entries))

    def test_registry_variants_and_labels_are_well_formed(self):
        # design section 5: 48 entries on 24 slots; a plain slot has a label, a family slot one per variant
        self.assertEqual(URL_COUNT, sum(len(placeholders.urls(e)) for e in self.all_entries))
        for entry in self.all_entries:
            variants = entry.get("variants", [])
            self.assertEqual(len(variants), len(set(variants)), entry["command"])
            for variant in variants:
                self.assertRegex(variant, r"^\w+:string=[\w.-]+$", entry["command"])
            if variants:
                self.assertNotIn("label", entry, entry["command"])
                self.assertEqual(variants, list(entry["variant_labels"]), entry["command"])
            else:
                self.assertTrue(entry["label"], entry["command"])
                self.assertNotIn("variant_labels", entry, entry["command"])

    def test_fn_boost_opens_the_fork_block_after_fn_pagebreak(self):
        text = read(CMDID)
        self.assertRegex(text, r"#define FN_PAGEBREAK\s+\(SID_SW_START \+ 2610\)\n"
                               r"(?://[^\n]*\n)*#define FN_BOOST\s+\(SID_SW_START \+ 5900\)")

    def test_every_slot_is_defined_in_cmdid_h_inside_the_fork_block(self):
        for entry in self.all_entries:
            self.assertEqual(entry["offset"], self.offsets.get(entry["slot"]), entry["slot"])
            self.assertTrue(0 <= entry["offset"] < BLOCK_SIZE, entry["slot"])

    def test_the_fork_block_has_no_gaps_and_no_duplicates(self):
        defines = re.findall(r"^#define\s+(FN_BOOST_\w+)\s", read(CMDID), re.M)
        self.assertEqual(len(defines), len(set(defines)), "FN_BOOST_* defined twice")
        self.assertEqual({e["slot"] for e in self.all_entries}, set(defines))
        self.assertEqual(list(range(len(self.offsets))), sorted(self.offsets.values()))

    def test_the_evaluated_ids_match_the_known_values(self):
        values = {name: value for name, value, _ in define_values()}
        self.assertEqual(20000, values["SID_SW_START"])
        self.assertEqual(26000, values["SID_SC_START"])
        self.assertEqual(22610, values["FN_PAGEBREAK"])
        self.assertEqual(FN_BOOST, values["FN_BOOST"])
        # the evaluator must see the whole Writer range, not a handful of ids (design 3.3: 737)
        in_range = {(n, v) for n, v, _ in define_values() if 20000 <= v < 26000}
        self.assertGreater(len(in_range), 700)

    def test_no_other_define_falls_in_the_fork_block(self):
        names = {"FN_BOOST"} | {e["slot"] for e in self.all_entries}
        found = {}
        for name, value, path in define_values():
            if FN_BOOST <= value < FN_BOOST + BLOCK_SIZE:
                found.setdefault(name, set()).add(value)
                self.assertIn(name, names, "%s = %d in %s" % (name, value, path))
        expected = {e["slot"]: {FN_BOOST + e["offset"]} for e in self.all_entries}
        expected["FN_BOOST"] = {FN_BOOST}
        self.assertEqual(expected, found)

    def test_every_slot_has_a_swriter_sdi_entry_hidden_from_customize_and_writable(self):
        sdi = SDI.read_text(encoding="utf-8")
        for entry in self.entries:
            m = re.search(r"^SfxVoidItem " + entry["command"] + " " + entry["slot"] + r"\n\(\)\n\[(.*?)\n\]",
                          sdi, re.S | re.M)
            self.assertIsNotNone(m, entry["command"])
            self.assertIn("ReadOnlyDoc = FALSE", m.group(1), entry["command"])
            for flag in ("MenuConfig", "ToolBoxConfig", "AccelConfig"):
                self.assertIn(flag + " = FALSE", m.group(1), entry["command"] + " " + flag)
            self.assertEqual(1, len(re.findall(r"\b" + entry["command"] + r"\b", sdi)), entry["command"])

    def test_every_slot_has_a_state_method_and_no_execute_method_in_text_edit_view(self):
        view = VIEW_SDI.read_text(encoding="utf-8")
        text_edit_view = re.search(r"^interface TextEditView : BaseTextEditView\n\{(.*?)\n\}", view, re.S | re.M)
        self.assertIsNotNone(text_edit_view)
        for entry in self.entries:
            row = re.search(r"^\s*" + entry["slot"] + r"\s*\[([^\]]*)\]", text_edit_view.group(1), re.M)
            self.assertIsNotNone(row, entry["slot"])
            self.assertIn("StateMethod = GetState ;", row.group(1), entry["slot"])
            self.assertNotIn("ExecMethod", row.group(1), entry["slot"])
            self.assertEqual(1, len(re.findall(r"\b" + entry["slot"] + r"\b", view)), entry["slot"])

    def test_every_slot_is_in_the_always_disabled_group_of_swview_getstate(self):
        text = VIEWSTAT.read_text(encoding="utf-8")
        get_state = re.search(r"^void SwView::GetState\(SfxItemSet &rSet\)\n\{(.*?)^\}", text, re.S | re.M)
        self.assertIsNotNone(get_state)
        for entry in self.entries:
            hits = [m.group(2) for m in re.finditer(r"((?:\s*case \w+:\n)+)(.*?)break;", get_state.group(1), re.S)
                    if entry["slot"] in re.findall(r"case (\w+):", m.group(1))]
            self.assertEqual(1, len(hits), entry["slot"])
            self.assertEqual("rSet.DisableItem(nWhich);", hits[0].strip(), entry["slot"])
            self.assertEqual(1, len(re.findall(r"\b" + entry["slot"] + r"\b", text)), entry["slot"])

    def test_no_slot_is_referenced_by_any_other_source(self):
        # Beyond cmdid.h, swriter.sdi, viewsh.sdi and the viewstat.cxx case group nothing may use a
        # placeholder slot: an Execute or another GetState would make it a real command.
        allowed = {CMDID, SDI, VIEW_SDI, VIEWSTAT}
        names = ["FN_BOOST"] + [e["slot"] for e in self.entries]
        pattern = re.compile(r"\b(" + "|".join(map(re.escape, names)) + r")\b")
        for suffix in ("*.cxx", "*.hxx", "*.h", "*.sdi", "*.hrc"):
            for path in (ROOT / "sw").rglob(suffix):
                if path in allowed or ".git" in path.parts:
                    continue
                self.assertIsNone(pattern.search(path.read_text(encoding="utf-8", errors="replace")), str(path))


if __name__ == "__main__":
    unittest.main()

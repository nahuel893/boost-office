# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Every placeholder slot of the Impress ribbon: app.hrc, sdraw.sdi, ViewShellBase.sdi, ViewShellBase.cxx."""
import re
import unittest
from pathlib import Path

from product.tests import placeholders
from product.tests.test_writer_slots import evaluate

ROOT = Path(__file__).resolve().parents[2]
APP_HRC = ROOT / "sd/inc/app.hrc"
SDI = ROOT / "sd/sdi/sdraw.sdi"
VIEW_SDI = ROOT / "sd/sdi/ViewShellBase.sdi"
VIEW_CXX = ROOT / "sd/source/ui/view/ViewShellBase.cxx"
REGISTRY = placeholders.registry("impress")
SID_BOOST = 27900                     # SID_SD_START + 900: the fork block, ids 27900..27999
BLOCK_SIZE, SLOT_COUNT, URL_COUNT = 100, 24, 39
# design 3.3: the headers whose #defines share the sd id range (SID_SD_START .. 27999); every sd .hrc
# file is added to them
ID_HEADERS = ["include/svl/solar.hrc", "include/sfx2/sfxsids.hrc", "include/svx/svxids.hrc",
              "include/editeng/editids.hrc"]
# the slot files sdslots.sdi and sdgslots.sdi import, where a command name must not repeat
SLOT_FILES = [ROOT / "sfx2/sdi/sfx.sdi", ROOT / "svx/sdi/svx.sdi"] + sorted((ROOT / "sd/sdi").glob("*.sdi"))


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def boost_offsets():
    """SID_BOOST_* name -> offset, from the "(SID_BOOST+n)" defines of app.hrc."""
    return {m.group(1): int(m.group(2)) for m in re.finditer(
        r"^#define\s+(SID_BOOST_\w+)\s+\(SID_BOOST\s*\+\s*(\d+)\)", read(APP_HRC), re.M)}


def define_values():
    """Evaluate every object-like #define of the id headers and the sd .hrc files.

    Returns [(name, value, file)] for each define that evaluates to an integer, as
    test_writer_slots.define_values does for sw: comments and "TypedWhichId<T>" are stripped, and
    the defines are resolved again until nothing changes.
    """
    files = [ROOT / p for p in ID_HEADERS] + sorted((ROOT / "sd").rglob("*.hrc"))
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
            value = evaluate(raw[i][1], known)
            if value is None:
                left.append(i)
                continue
            values[i] = value
            known.setdefault(raw[i][0], value)
        if len(left) == len(pending):
            break
        pending = left
    return [(raw[i][0], values[i], raw[i][2]) for i in sorted(values)]


class ImpressPlaceholderSlotsTest(unittest.TestCase):

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
        self.assertTrue(all(e["slot"].startswith("SID_BOOST_") for e in self.all_entries))

    def test_registry_variants_and_labels_are_well_formed(self):
        # design section 5: 39 entries on 24 slots. The tab tasks add the labels: a plain slot gets
        # "label", a family slot "variant_labels" keyed in variant order.
        self.assertEqual(URL_COUNT, sum(len(placeholders.urls(e)) for e in self.all_entries))
        for entry in self.all_entries:
            variants = entry.get("variants", [])
            self.assertEqual(len(variants), len(set(variants)), entry["command"])
            for variant in variants:
                self.assertRegex(variant, r"^\w+:string=[\w.-]+$", entry["command"])
            if variants:
                self.assertNotIn("label", entry, entry["command"])
                if "variant_labels" in entry:
                    self.assertEqual(variants, list(entry["variant_labels"]), entry["command"])
            else:
                self.assertNotIn("variant_labels", entry, entry["command"])
                if "label" in entry:
                    self.assertTrue(entry["label"], entry["command"])

    def test_sid_boost_opens_the_fork_block_after_the_last_sd_define(self):
        # blank lines and comments may sit between them; the file text is not printed on failure
        found = re.search(r"#define SID_REMOVE_SLIDE_SECTION_AND_SLIDES \(SID_SD_START\+458\)\n"
                          r"(?:\n|//[^\n]*\n)*#define SID_BOOST\s+\(SID_SD_START\+900\)\n", read(APP_HRC))
        self.assertIsNotNone(found, "SID_BOOST (SID_SD_START+900) does not follow the last sd define")

    def test_every_slot_is_defined_in_app_hrc_inside_the_fork_block(self):
        for entry in self.all_entries:
            self.assertEqual(entry["offset"], self.offsets.get(entry["slot"]), entry["slot"])
            self.assertTrue(0 <= entry["offset"] < BLOCK_SIZE, entry["slot"])

    def test_the_fork_block_has_no_gaps_and_no_duplicates(self):
        defines = re.findall(r"^#define\s+(SID_BOOST_\w+)\s", read(APP_HRC), re.M)
        self.assertEqual(len(defines), len(set(defines)), "SID_BOOST_* defined twice")
        self.assertEqual({e["slot"] for e in self.all_entries}, set(defines))
        self.assertEqual(list(range(len(self.offsets))), sorted(self.offsets.values()))

    def test_the_evaluated_ids_match_the_known_values(self):
        values = {name: value for name, value, _ in define_values()}
        self.assertEqual(27000, values["SID_SD_START"])
        self.assertEqual(27458, values["SID_REMOVE_SLIDE_SECTION_AND_SLIDES"])
        self.assertEqual(SID_BOOST, values["SID_BOOST"])
        # the evaluator must see the whole sd range, not a handful of ids (312 defines before I1)
        in_range = {(n, v) for n, v, _ in define_values() if 27000 <= v < 28000}
        self.assertGreater(len(in_range), 300)

    def test_no_other_define_falls_in_the_fork_block(self):
        names = {"SID_BOOST"} | {e["slot"] for e in self.all_entries}
        found = {}
        for name, value, path in define_values():
            if SID_BOOST <= value < SID_BOOST + BLOCK_SIZE:
                found.setdefault(name, set()).add(value)
                self.assertIn(name, names, "%s = %d in %s" % (name, value, path))
        expected = {e["slot"]: {SID_BOOST + e["offset"]} for e in self.all_entries}
        expected["SID_BOOST"] = {SID_BOOST}
        self.assertEqual(expected, found)

    def test_every_slot_has_an_sdraw_sdi_entry_hidden_from_customize_and_writable(self):
        sdi = SDI.read_text(encoding="utf-8")
        for entry in self.entries:
            m = re.search(r"^SfxVoidItem " + entry["command"] + " " + entry["slot"] + r"\n\(\)\n\[(.*?)\n\]",
                          sdi, re.S | re.M)
            self.assertIsNotNone(m, entry["command"])
            for flag in ("AutoUpdate", "ReadOnlyDoc", "MenuConfig", "ToolBoxConfig", "AccelConfig"):
                self.assertIn(flag + " = FALSE", m.group(1), entry["command"] + " " + flag)
            self.assertRegex(m.group(1), r"\n    GroupId = SfxGroupId::\w+;$", entry["command"])
            # the command name is new to every slot file Impress and Draw import
            for path in SLOT_FILES:
                count = len(re.findall(r"\b" + entry["command"] + r"\b", path.read_text(encoding="utf-8")))
                self.assertEqual(1 if path == SDI else 0, count, entry["command"] + " in " + path.name)

    def test_every_slot_has_a_state_method_and_no_execute_method_in_view_shell_base_view(self):
        view = VIEW_SDI.read_text(encoding="utf-8")
        base_view = re.search(r"^interface ViewShellBaseView\n\{(.*?)\n\}", view, re.S | re.M)
        self.assertIsNotNone(base_view)
        for entry in self.entries:
            row = re.search(r"^\s*" + entry["slot"] + r"\s*\[([^\]]*)\]", base_view.group(1), re.M)
            self.assertIsNotNone(row, entry["slot"])
            self.assertRegex(row.group(1), r"StateMethod = GetState ;", entry["slot"])
            self.assertNotIn("ExecMethod", row.group(1), entry["slot"])
            self.assertEqual(1, len(re.findall(r"\b" + entry["slot"] + r"\b", view)), entry["slot"])

    def get_state(self):
        text = VIEW_CXX.read_text(encoding="utf-8")
        get_state = re.search(r"^void ViewShellBase::GetState \(SfxItemSet& rSet\)\n\{(.*?)^\}", text, re.S | re.M)
        self.assertIsNotNone(get_state)
        return text, get_state.group(1)

    def test_every_slot_is_in_the_always_disabled_group_of_view_shell_base_get_state(self):
        text, body = self.get_state()
        for entry in self.entries:
            hits = [m.group(2) for m in re.finditer(r"((?:\s*case \w+:\n)+)(.*?)break;", body, re.S)
                    if entry["slot"] in re.findall(r"case (\w+):", m.group(1))]
            self.assertEqual(1, len(hits), entry["slot"])
            self.assertEqual("rSet.DisableItem(nWhich);", hits[0].strip(), entry["slot"])
            self.assertEqual(1, len(re.findall(r"\b" + entry["slot"] + r"\b", text)), entry["slot"])

    def test_the_disabled_group_comes_last_and_nothing_can_skip_it(self):
        # Implementation::GetSlotState puts a SfxBoolItem for every slot of the set, which replaces a
        # disabled entry: a group before it leaves the slots enabled (I1's UITest showed it). So the
        # group comes after both calls, and GetState has no return that could skip it.
        _, body = self.get_state()
        first = min(body.index("case " + e["slot"] + ":") for e in self.entries)
        self.assertGreater(first, body.index("mpImpl->GetSlotState(rSet);"))
        self.assertGreater(first, body.index("FuBullet::GetSlotState("))
        self.assertNotRegex(body, r"\breturn\b")

    def test_draw_does_not_serve_the_slots(self):
        # sdraw.sdi is shared, so Draw knows the declarations; ViewShellBaseView, the only interface
        # that lists the slots, is in Impress's slot file and not in Draw's (design 3.3)
        self.assertIn('include "ViewShellBase.sdi"', read("sd/sdi/sdslots.sdi"))
        self.assertNotIn("ViewShellBase.sdi", read("sd/sdi/sdgslots.sdi"))

    def test_no_slot_is_referenced_by_any_other_source(self):
        # Beyond app.hrc, sdraw.sdi, ViewShellBase.sdi and the ViewShellBase.cxx case group nothing
        # may use a placeholder slot: an Execute or another GetState would make it a real command.
        allowed = {APP_HRC, SDI, VIEW_SDI, VIEW_CXX}
        names = ["SID_BOOST"] + [e["slot"] for e in self.entries]
        pattern = re.compile(r"\b(" + "|".join(map(re.escape, names)) + r")\b")
        for suffix in ("*.cxx", "*.hxx", "*.h", "*.sdi", "*.hrc"):
            for path in (ROOT / "sd").rglob(suffix):
                if path in allowed or ".git" in path.parts:
                    continue
                self.assertIsNone(pattern.search(path.read_text(encoding="utf-8", errors="replace")), str(path))


def function_body(source, signature):
    """The body of the C++ function whose definition starts with `signature`, comments removed and
    whitespace collapsed."""
    match = re.search(re.escape(signature) + r"[^{]*\{(.*?)\n\}", source, re.S)
    return match and " ".join(re.sub(r"//[^\n]*", "", match.group(1)).split())


class ImpressToolBarsTest(unittest.TestCase):
    # I9b, I9c (ruling 24): PowerPoint has no toolbar under its ribbon, and Calc and Writer show none under
    # theirs (sfx2's SfxWorkWindow destroys every object bar while a notebookbar is active, Edit Points
    # included). sd's toolbars are no object bars: its ToolBarManager requests them by name (Drawing, Text
    # Formatting, image, media, Edit Points, glue points, table, options, outline, slide sorter, master view,
    # ...), and the layout manager also creates the Drawing toolbar from its window state. So under an
    # Impress notebookbar sd requests none of them and destroys the Drawing toolbar on each update; the
    # toolbar shells stay (they serve the slots); Draw and the other UI modes keep every toolbar.
    source = read("sd/source/ui/view/ToolBarManager.cxx")

    def test_only_impress_under_a_notebookbar_hides_the_toolbars(self):
        body = function_body(self.source, "bool ToolBarManager::Implementation::AreToolBarsHidden")
        self.assertIsNotNone(body, "no AreToolBarsHidden")
        self.assertIn("GetDocumentType() == DocumentType::Impress", body)
        self.assertIn("sfx2::SfxNotebookBar::IsActive()", body, "a notebookbar mode, not the single toolbar")
        self.assertNotIn("IsDrawingToolBarHidden", self.source, "one rule for every toolbar, not one toolbar")

    def test_no_toolbar_is_requested_while_hidden(self):
        add = function_body(self.source, "void ToolBarManager::Implementation::AddToolBar")
        self.assertRegex(add, r"^::osl::MutexGuard aGuard\(maMutex\); "
                              r"if \(CheckPlugInMode\(rsToolBarName\) && !AreToolBarsHidden\(\)\) \{ "
                              r"maToolBarList\.AddToolBar\(eGroup,rsToolBarName\);")
        # every request reaches the layout manager through that one list: the rules, SetToolBar and the
        # callers outside (fuediglu.cxx, drviews1.cxx, fucon*.cxx) all call Implementation::AddToolBar
        self.assertEqual(self.source.count("maToolBarList.AddToolBar("), 1)
        self.assertEqual(self.source.count("requestElement("), 1)
        others = [p for p in (ROOT / "sd/source").rglob("*.cxx")
                  if p.name != "ToolBarManager.cxx" and "requestElement(" in p.read_text(errors="replace")]
        self.assertEqual(others, [])

    def test_the_toolbar_shells_stay_so_their_slots_work(self):
        shell = function_body(self.source, "void ToolBarManager::Implementation::AddToolBarShell")
        self.assertIn("maToolBarShellList.AddShellId(eGroup,nToolBarId);", shell)
        self.assertNotIn("AreToolBarsHidden", shell)

    def test_the_drawing_toolbar_the_layout_manager_creates_is_destroyed_while_hidden(self):
        pre = function_body(self.source, "void ToolBarManager::Implementation::PreUpdate")
        self.assertIn("if (AreToolBarsHidden()) mxLayouter->destroyElement(GetToolBarResourceName(msToolBar));",
                      pre)


if __name__ == "__main__":
    unittest.main()

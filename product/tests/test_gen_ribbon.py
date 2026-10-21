# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import contextlib
import copy
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from product.tests import office
from product.ui import gen_ribbon as g

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<interface domain="sc">
  <object class="GtkMenu" id="Menu Home">
    <property name="visible">True</property>
    <child>
      <object class="GtkMenuItem" id="MenuHome-Old">
        <property name="visible">True</property>
      </object>
    </child>
  </object>
  <object class="GtkBox" id="Root">
    <child>
      <object class="sfxlo-PriorityHBox" id="phbHome">
        <property name="visible">True</property>
        <child>
          <object class="GtkToolButton" id="btnHomeOld">
            <property name="action-name">.uno:Old</property>
          </object>
        </child>
      </object>
      <packing>
        <property name="position">1</property>
      </packing>
    </child>
    <child>
      <object class="GtkLabel" id="keepMe">
        <property name="label">x</property>
      </object>
    </child>
  </object>
</interface>
"""

LAYOUT = {
    "page": "phbHome", "id_prefix": "Home", "context": "TabbedCalc",
    "remove_objects": ["Menu Home"],
    "sections": [
        {"name": "Clipboard", "caption": "Clipboard", "rows": 3, "columns": [
            [{"id": "Paste", "style": "large", "items": [{"cmd": "Paste", "kind": "split"}]}],
            [{"id": "Cut", "style": "small-label", "items": [{"cmd": "Cut"}]},
             {"id": "Copy", "style": "small-label", "items": [{"cmd": "Copy"}]}]]},
        {"name": "Font", "caption": "Font", "rows": 2, "columns": [
            [{"id": "FormatRow", "style": "small", "items": [{"cmd": "Bold"}, {"cmd": "Italic"}]}]]},
    ],
}


def generate(text=FIXTURE, layout=LAYOUT):
    return g.splice(text, layout, g.emit_page(layout))


def placed(root, obj_id):
    """Return (object element, packing element) for the <child> holding obj_id."""
    for child in root.iter("child"):
        obj = child.find("object")
        if obj is not None and obj.get("id") == obj_id:
            return obj, child.find("packing")
    raise AssertionError(f"{obj_id} not found")


def outputs(name):
    """The repository-relative files the generator writes for one app."""
    app = g.APPS[name]
    return [rel for rel in (app.office, app.suppr, app.false) if rel]


def copy_inputs(root, name):
    """Copy what the generator reads for one app into a scratch source tree."""
    app = g.APPS[name]
    for rel in [app.upstream] + [rel for rel in outputs(name) if rel != app.office]:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(office.ROOT / rel, root / rel)
    (root / "product/ui").mkdir(parents=True, exist_ok=True)
    for path in office.UI_DIR.glob(app.prefix + "_*.json"):
        shutil.copy(path, root / "product/ui" / path.name)


def section_grid_rule(grid):
    """(grid id, broken rules) of a section grid; no broken rule means the caption sits on the
    section's bottom edge.

    VclGrid splits extra height evenly between its expanding rows and drops the remainder, so
    a caption under several expanding rows ends a few pixels above the bottom. The rule: two
    rows, the toolboxes' grid alone on row 0 and the only child that expands vertically, the
    caption on row 1, the separator spanning both."""
    broken = []
    cells = {}
    for child in grid.findall("child"):
        obj = child.find("object")
        attach = tuple(int(child.findtext(f"packing/property[@name='{n}']", "0"))
                       for n in ("left-attach", "top-attach"))
        span = int(child.findtext("packing/property[@name='height']", "1"))
        vexpand = obj.findtext("property[@name='vexpand']") == "True"
        cells[obj.get("class")] = (attach, span, vexpand)
    if set(cells) != {"GtkGrid", "GtkLabel", "GtkSeparator"} or len(grid.findall("child")) != 3:
        broken.append(f"children {sorted(cells)}")
    else:
        if cells["GtkGrid"] != ((0, 0), 1, True):
            broken.append(f"toolbox grid {cells['GtkGrid']}")
        if cells["GtkLabel"] != ((0, 1), 1, False):
            broken.append(f"caption {cells['GtkLabel']}")
        if cells["GtkSeparator"] != ((1, 0), 2, False):
            broken.append(f"separator {cells['GtkSeparator']}")
    return grid.get("id"), broken


class GenRibbonTest(unittest.TestCase):

    def test_output_is_well_formed_xml(self):
        ET.fromstring(generate())

    def test_old_page_content_and_removed_objects_are_gone(self):
        out = generate()
        self.assertNotIn("btnHomeOld", out)
        self.assertNotIn('id="Menu Home"', out)
        self.assertNotIn("MenuHome-Old", out)

    def test_lines_outside_the_page_are_unchanged(self):
        out = generate()
        self.assertTrue(out.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<interface domain="sc">\n'))
        tail = FIXTURE[FIXTURE.index("      <packing>\n        <property name=\"position\">1</property>"):]
        self.assertTrue(out.endswith(tail))

    def test_sections_have_caption_relation_and_priority(self):
        root = ET.fromstring(generate())
        grid = root.find(".//object[@id='gdHomeClipboard']")
        self.assertEqual("lbHomeClipboard", grid.find("accessibility/relation").get("target"))
        label = root.find(".//object[@id='lbHomeClipboard']")
        text = label.find("property[@name='label']")
        self.assertEqual("Clipboard", text.text)
        self.assertEqual("TabbedCalc|labelHomeClipboard", text.get("context"))
        self.assertIsNone(label.find("attributes/attribute[@name='style']"))
        self.assertEqual("0.9", label.find("attributes/attribute[@name='scale']").get("value"))
        self.assertEqual("priority-2", root.find(".//object[@id='obHomeClipboard']/style/class").get("name"))
        self.assertEqual("priority-1", root.find(".//object[@id='obHomeFont']/style/class").get("name"))

    def test_large_toolbox_spans_all_rows_at_32px(self):
        obj, packing = placed(ET.fromstring(generate()), "bxHomePaste")
        self.assertEqual("5", obj.find("property[@name='icon_size']").text)
        self.assertEqual("both", obj.find("property[@name='toolbar-style']").text)
        self.assertEqual("3", packing.find("property[@name='height']").text)
        button = obj.find("child/object")
        self.assertEqual("GtkMenuToolButton", button.get("class"))
        self.assertEqual("btnHomePaste", button.get("id"))
        self.assertEqual(".uno:Paste", button.find("property[@name='action-name']").text)

    def test_small_toolboxes_stack_in_rows_at_16px(self):
        root = ET.fromstring(generate())
        got = {}
        for box_id in ("bxHomeCut", "bxHomeCopy"):
            obj, packing = placed(root, box_id)
            got[box_id] = (packing.find("property[@name='left-attach']").text,
                           packing.find("property[@name='top-attach']").text,
                           obj.find("property[@name='icon_size']").text,
                           obj.find("property[@name='toolbar-style']").text)
        self.assertEqual({"bxHomeCut": ("1", "0", "1", "both-horiz"),
                          "bxHomeCopy": ("1", "1", "1", "both-horiz")}, got)

    def test_caption_and_separator_positions(self):
        # the section grid: the toolboxes' grid on row 0, the caption under it, the separator on
        # the right spanning both rows
        root = ET.fromstring(generate())
        grid = root.find(".//object[@id='gdHomeClipboard']")
        self.assertEqual(section_grid_rule(grid), (grid.get("id"), []))
        _, packing = placed(root, "lbHomeClipboard")
        self.assertEqual(("0", "1"), tuple(packing.find(f"property[@name='{n}']").text
                                           for n in ("left-attach", "top-attach")))
        sep_child = [c for c in grid.findall("child") if c.find("object").get("class") == "GtkSeparator"][0]
        self.assertEqual(("1", "0", "2"), tuple(sep_child.find(f"packing/property[@name='{n}']").text
                                                for n in ("left-attach", "top-attach", "height")))

    def test_toolboxes_are_in_the_section_content_grid(self):
        root = ET.fromstring(generate())
        content = root.find(".//object[@id='gcHomeClipboard']")
        self.assertEqual({"bxHomePaste", "bxHomeCut", "bxHomeCopy"},
                         {c.find("object").get("id") for c in content.findall("child")})
        self.assertIn("gcHomeClipboard", list(g.ids_of(LAYOUT)))

    def test_page_box_fills_the_page_height(self):
        # so every section of every page is as tall as the tallest page (the ribbon's height)
        page = ET.fromstring(generate()).find(".//object[@id='pmhbHome']")
        self.assertEqual(["fill"], [p.text for p in page.findall("property[@name='valign']")])

    def test_splice_is_idempotent(self):
        once = generate()
        self.assertEqual(once, generate(once))

    def test_optional_label_and_icon(self):
        layout = copy.deepcopy(LAYOUT)
        layout["sections"][0]["columns"][0][0]["items"][0] = {
            "cmd": "InsertMenu", "action": "private:resource/popupmenu/home_insert",
            "label": "Insert", "icon": "cmd/lc_insertcell.png"}
        button = ET.fromstring(generate(layout=layout)).find(".//object[@id='btnHomeInsertMenu']")
        self.assertEqual("private:resource/popupmenu/home_insert", button.find("property[@name='action-name']").text)
        self.assertEqual("Insert", button.find("property[@name='label']").text)
        self.assertEqual("TabbedCalc|btnHomeInsertMenu", button.find("property[@name='label']").get("context"))
        self.assertEqual("cmd/lc_insertcell.png", button.find("property[@name='icon_name']").text)

    def test_rejects_large_toolbox_sharing_a_column(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][0]["columns"][0].append({"id": "X", "style": "small", "items": [{"cmd": "X"}]})
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_rejects_too_many_toolboxes_for_the_rows(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][1]["columns"][0] += [
            {"id": "A", "style": "small", "items": [{"cmd": "A"}]},
            {"id": "B", "style": "small", "items": [{"cmd": "B"}]}]
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_small_toolbox_can_start_on_a_later_row(self):
        layout = copy.deepcopy(LAYOUT)
        layout["sections"][1]["columns"][0][0]["row"] = 1
        _, packing = placed(ET.fromstring(generate(layout=layout)), "bxHomeFormatRow")
        self.assertEqual("1", packing.find("property[@name='top-attach']").text)

    def test_small_toolbox_can_align_to_the_bottom_of_its_row(self):
        layout = copy.deepcopy(LAYOUT)
        layout["sections"][1]["columns"][0][0]["valign"] = "end"
        obj, _ = placed(ET.fromstring(generate(layout=layout)), "bxHomeFormatRow")
        self.assertEqual(["end"], [p.text for p in obj.findall("property[@name='valign']")])

    def test_rejects_unknown_valign(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][1]["columns"][0][0]["valign"] = "bottom"
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_rejects_row_outside_the_section(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][1]["columns"][0][0]["row"] = 2
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_rejects_toolboxes_sharing_a_row(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][0]["columns"][1][1]["row"] = 0
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_rejects_duplicate_ids(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][1]["columns"][0][0]["items"].append({"cmd": "Bold"})
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def footer_layout(self):
        layout = copy.deepcopy(LAYOUT)
        layout["sections"][0]["footer"] = {
            "id": "StyleList", "style": "small", "valign": "end", "items": [{"cmd": "StyleApply"}]}
        # Cut and Copy would collide with the footer row; keep one column box.
        layout["sections"][0]["columns"][1].pop()
        return layout

    def test_footer_spans_all_columns_on_the_last_row(self):
        obj, packing = placed(ET.fromstring(generate(layout=self.footer_layout())), "bxHomeStyleList")
        self.assertEqual(("0", "2", "2"), tuple(packing.find(f"property[@name='{n}']").text
                                                for n in ("left-attach", "top-attach", "width")))
        self.assertEqual(["end"], [p.text for p in obj.findall("property[@name='valign']")])

    def test_footer_shortens_large_toolboxes_by_one_row(self):
        _, packing = placed(ET.fromstring(generate(layout=self.footer_layout())), "bxHomePaste")
        self.assertEqual("2", packing.find("property[@name='height']").text)

    def test_footer_ids_are_generated(self):
        self.assertIn("btnHomeStyleApply", list(g.ids_of(self.footer_layout())))
        self.assertIn("bxHomeStyleList", list(g.ids_of(self.footer_layout())))

    def test_rejects_column_box_on_the_footer_row(self):
        bad = self.footer_layout()
        bad["sections"][0]["columns"][1][0]["row"] = 2
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_rejects_footer_with_a_row(self):
        bad = self.footer_layout()
        bad["sections"][0]["footer"]["row"] = 1
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_rejects_footer_duplicate_of_a_column_box(self):
        bad = self.footer_layout()
        bad["sections"][0]["footer"]["id"] = "Cut"
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def medium_layout(self):
        layout = copy.deepcopy(LAYOUT)
        layout["sections"][0]["columns"][0][0]["style"] = "medium"
        return layout

    def test_medium_toolbox_is_24px_and_spans_like_a_large_one(self):
        obj, packing = placed(ET.fromstring(generate(layout=self.medium_layout())), "bxHomePaste")
        self.assertEqual("3", obj.find("property[@name='icon_size']").text)
        self.assertEqual("both", obj.find("property[@name='toolbar-style']").text)
        self.assertEqual("center", obj.find("property[@name='valign']").text)
        self.assertEqual("3", packing.find("property[@name='height']").text)

    def test_medium_toolbox_spans_rows_above_a_footer(self):
        layout = self.medium_layout()
        layout["sections"][0]["footer"] = {
            "id": "StyleList", "style": "small", "items": [{"cmd": "StyleApply"}]}
        layout["sections"][0]["columns"][1].pop()
        _, packing = placed(ET.fromstring(generate(layout=layout)), "bxHomePaste")
        self.assertEqual("2", packing.find("property[@name='height']").text)

    def test_rejects_medium_toolbox_sharing_a_column(self):
        bad = self.medium_layout()
        bad["sections"][0]["columns"][0].append({"id": "X", "style": "small", "items": [{"cmd": "X"}]})
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_rejects_medium_footer(self):
        bad = self.footer_layout()
        bad["sections"][0]["footer"]["style"] = "medium"
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def expand_layout(self):
        layout = copy.deepcopy(LAYOUT)
        layout["sections"][1]["columns"][0][0]["expand"] = True
        return layout

    def test_an_expanding_toolbox_gets_the_free_width_through_every_container(self):
        # VCL does not pass hexpand up to the parents: a VclHBox only grows a child that has expand
        # or hexpand itself, a VclGrid only grows a column with an hexpand child, and a ToolBox
        # only grows an item window whose packing has expand (vcl/source/window/layout.cxx,
        # vcl/source/window/toolbox.cxx ToolBox::Resize). So the section's optional box, both grids
        # and the toolbox expand, and so do the toolbox's items.
        root = ET.fromstring(generate(layout=self.expand_layout()))
        expanding = {obj.get("id") for obj in root.iter("object")
                     if [p.text for p in obj.findall("property[@name='hexpand']")] == ["True"]}
        self.assertEqual({"obHomeFont", "gdHomeFont", "gcHomeFont", "bxHomeFormatRow"}, expanding)
        for wid in ("btnHomeBold", "btnHomeItalic"):
            _, packing = placed(root, wid)
            self.assertEqual("True", packing.find("property[@name='expand']").text, wid)

    def test_nothing_expands_by_default(self):
        out = generate()
        self.assertNotIn('name="hexpand"', out)
        root = ET.fromstring(out)
        items = [c.find("packing/property[@name='expand']").text for c in root.iter("child")
                 if c.find("object").get("class") in g.BUTTON_CLASS.values()]
        self.assertEqual(["False"] * 5, items)  # Paste, Cut, Copy, Bold, Italic

    def test_rejects_expand_that_is_not_a_boolean(self):
        bad = self.expand_layout()
        bad["sections"][1]["columns"][0][0]["expand"] = "true"
        with self.assertRaises(g.LayoutError):
            g.emit_page(bad)

    def test_suppr_sync(self):
        ui = generate()
        suppr = "\n".join([
            "other.ui://GtkToolButton[@id='btnHomeOld'] button-no-label",
            "x.ui://GtkToolButton[@id='btnHomeOld'] button-no-label",
            "x.ui://GtkMenuItem[@id='MenuHome-Old'] button-no-label",
            "x.ui://GtkLabel[@id='keepMe'] orphan-label",
        ]) + "\n"
        out = g.sync_suppr(suppr, "x.ui", ui).splitlines()
        self.assertIn("other.ui://GtkToolButton[@id='btnHomeOld'] button-no-label", out)
        self.assertNotIn("x.ui://GtkToolButton[@id='btnHomeOld'] button-no-label", out)
        self.assertNotIn("x.ui://GtkMenuItem[@id='MenuHome-Old'] button-no-label", out)
        self.assertIn("x.ui://GtkLabel[@id='keepMe'] orphan-label", out)
        self.assertIn("x.ui://GtkMenuToolButton[@id='btnHomePaste'] button-no-label", out)
        self.assertIn("x.ui://GtkToolButton[@id='btnHomeBold'] button-no-label", out)
        self.assertEqual(len(out), len(set(out)))

    def test_false_positive_sync_drops_gone_widgets_and_adds_nothing(self):
        ui = generate()
        false = "\n".join([
            "other.ui://GtkMenuItem[@id='MenuHome-Old'] button-no-label",
            "x.ui://GtkMenuItem[@id='MenuHome-Old'] button-no-label",
            "x.ui://GtkLabel[@id='keepMe'] orphan-label",
            "x.ui://GtkLabel[@id='keepMe'] orphan-label",
        ]) + "\n"
        self.assertEqual("other.ui://GtkMenuItem[@id='MenuHome-Old'] button-no-label\n"
                         "x.ui://GtkLabel[@id='keepMe'] orphan-label\n", g.sync_false(false, "x.ui", ui))


class CaptionBaselineTest(unittest.TestCase):
    """Every generated page of the office .ui puts its captions on one baseline (T8a)."""

    def test_every_generated_page_fills_the_page_height(self):
        # the tab page (upstream phbLayout was centered) and the generated box in it
        root = ET.parse(office.OFFICE).getroot()
        wrong = {}
        for layout in office.page_layouts():
            for wid, allowed in ((layout["page"], ([], ["fill"])), ("pmhb" + layout["id_prefix"], (["fill"],))):
                valign = [p.text for p in root.find(f".//object[@id='{wid}']").findall("property[@name='valign']")]
                if valign not in allowed:
                    wrong[wid] = valign
        self.assertEqual({}, wrong)

    def test_the_upstream_extension_and_tools_pages_fill_their_tab_page_too(self):
        # not generated, but visible tabs: upstream centers their box, which would put their
        # captions on another baseline than every other tab's (applied by calc_tabs.json)
        root = ET.parse(office.OFFICE).getroot()
        for wid in ("pmhbExtension", "pmhbTools"):
            valign = [p.text for p in root.find(f".//object[@id='{wid}']").findall("property[@name='valign']")]
            self.assertEqual(["fill"], valign, wid)

    def test_every_generated_section_has_its_caption_on_the_bottom_edge(self):
        root = ET.parse(office.OFFICE).getroot()
        layouts = office.page_layouts()
        self.assertEqual({"Home", "Insert", "PageLayout", "Formulas", "Data", "Review", "View", "Help"},
                         {layout["id_prefix"] for layout in layouts})
        broken = []
        for layout in layouts:
            for section in layout["sections"]:
                grid = root.find(f".//object[@id='gd{layout['id_prefix']}{section['name']}']")
                wid, rules = section_grid_rule(grid)
                if rules:
                    broken.append((wid, rules))
        self.assertEqual([], broken)


class RegenerateAllTest(unittest.TestCase):
    """One call applies the tab operations and regenerates every page (T-F1)."""

    def test_regenerate_all_rebuilds_the_committed_office_ui(self):
        upstream = office.UPSTREAM.read_text(encoding="utf-8")
        tabs = json.loads(office.TABS.read_text(encoding="utf-8"))
        text = g.regenerate_all(upstream, tabs, g.page_layouts(office.UI_DIR))
        self.assertEqual(office.OFFICE.read_text(encoding="utf-8"), text)
        self.assertEqual(text, g.regenerate_all(text, tabs, g.page_layouts(office.UI_DIR)))  # idempotent

    def test_page_layouts_skip_the_tab_operations_file(self):
        ids = [layout["id_prefix"] for layout in g.page_layouts(office.UI_DIR)]
        self.assertEqual(sorted(ids), ids)  # calc_<tab>.json in file-name order
        self.assertIn("Home", ids)
        self.assertEqual(len(ids), len(list(office.UI_DIR.glob("calc_*.json"))) - 1)

    def test_page_layouts_read_only_the_files_of_their_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("calc_home", "calc_tabs", "writer_home", "writer_tabs"):
                (Path(tmp) / (name + ".json")).write_text(json.dumps({"id_prefix": name}), encoding="utf-8")
            self.assertEqual([{"id_prefix": "calc_home"}], g.page_layouts(tmp))
            self.assertEqual([{"id_prefix": "writer_home"}], g.page_layouts(tmp, "writer"))

    def test_all_mode_rewrites_every_app_from_upstream(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in g.APPS:
                copy_inputs(root, name)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(0, g.main(["--all", "--root", str(root)]))
            self.assertEqual({"calc", "writer"}, set(g.APPS))
            for name in g.APPS:
                for rel in outputs(name):
                    with self.subTest(rel):
                        self.assertEqual((office.ROOT / rel).read_text(encoding="utf-8"),
                                         (root / rel).read_text(encoding="utf-8"))
                self.assertIn(g.APPS[name].office, out.getvalue())

    def test_app_mode_rewrites_that_app_alone(self):
        # Calc's run must give Calc's committed bytes whatever else the generator learns
        for name in g.APPS:
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                copy_inputs(root, name)
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(0, g.main(["--app", name, "--root", str(root)]))
                for rel in outputs(name):
                    self.assertEqual((office.ROOT / rel).read_bytes(), (root / rel).read_bytes(), rel)
                others = [g.APPS[other].office for other in g.APPS if other != name]
                self.assertEqual([], [rel for rel in others if (root / rel).exists()])

    def test_an_unknown_app_is_an_error(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as raised:
            g.main(["--app", "impress"])
        self.assertEqual(2, raised.exception.code)
        self.assertIn("argument --app: invalid choice: 'impress'", err.getvalue())

    def test_the_calc_names_of_the_test_tooling_are_the_calc_app(self):
        calc = office.app("calc")
        self.assertEqual((calc.upstream, calc.office, calc.tabs), (office.UPSTREAM, office.OFFICE, office.TABS))
        self.assertEqual(office.ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui", office.OFFICE)
        self.assertIsNone(calc.false)  # scalc.false has no notebookbar line to keep in sync
        self.assertEqual(office.expected_office_ui("calc"), office.expected_office_ui())


class ItemUrlTest(unittest.TestCase):

    def test_plain_item_is_its_uno_command(self):
        item = {"cmd": "Bold"}
        self.assertEqual(".uno:Bold", g.item_url(item))
        self.assertEqual(".uno:Bold", g.item_command(item))

    def test_url_variant_has_a_full_url_and_a_base_command(self):
        item = {"cmd": "InsertChartMap", "action": ".uno:InsertChartType?Type:string=map"}
        self.assertEqual(".uno:InsertChartType?Type:string=map", g.item_url(item))
        self.assertEqual(".uno:InsertChartType", g.item_command(item))

    def test_variant_action_is_what_the_button_runs(self):
        layout = copy.deepcopy(LAYOUT)
        layout["sections"][0]["columns"][0][0]["items"][0]["action"] = ".uno:Paste?Mode:string=x"
        text = "\n".join(g.emit_page(layout))
        self.assertIn('<property name="action-name">.uno:Paste?Mode:string=x</property>', text)


if __name__ == "__main__":
    unittest.main()

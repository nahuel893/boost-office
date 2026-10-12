# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import copy
import unittest
from xml.etree import ElementTree as ET

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
        root = ET.fromstring(generate())
        _, packing = placed(root, "lbHomeClipboard")
        self.assertEqual(("0", "3", "2"), tuple(packing.find(f"property[@name='{n}']").text
                                                for n in ("left-attach", "top-attach", "width")))
        grid = root.find(".//object[@id='gdHomeClipboard']")
        sep_child = [c for c in grid.findall("child") if c.find("object").get("class") == "GtkSeparator"][0]
        self.assertEqual(("2", "0", "4"), tuple(sep_child.find(f"packing/property[@name='{n}']").text
                                                for n in ("left-attach", "top-attach", "height")))

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

    def test_rejects_duplicate_ids(self):
        bad = copy.deepcopy(LAYOUT)
        bad["sections"][1]["columns"][0][0]["items"].append({"cmd": "Bold"})
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


if __name__ == "__main__":
    unittest.main()

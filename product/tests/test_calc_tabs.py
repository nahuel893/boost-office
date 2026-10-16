# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import unittest
import xml.etree.ElementTree as ET

from product.tests import office
from product.ui import gen_ribbon as g

# visible tabs in Excel's order; Extension and Tools stay where upstream has them (Excel's
# Developer), Help is last. The contextual tabs sit between View and Extension.
CONTEXTUAL = ["phbImage", "phbDraw", "phbObject", "phbMedia", "phbPrint", "phbForm"]
PAGES = ["phbFile", "phbHome", "phbInsert", "phbLayout", "phbFunctions", "phbData", "phbReview",
         "phbView"] + CONTEXTUAL + ["phbExtension", "phbTools", "phbHelp"]
LABELS = {"FileLabel": "~File", "HomeLabel": "~Home", "InsertLabel": "~Insert",
          "LayoutLabel": "Page ~Layout", "FunctionsLabel1": "For~mulas", "DataLabel": "~Data",
          "ReviewLabel": "~Review", "ViewLabel": "~View", "DevLabel": "~Tools", "HelpLabel": "Hel~p"}
# phbInsert has a generated page since T2a, like phbHome and phbData; phbReview since T5a
UNTOUCHED = CONTEXTUAL + ["phbFile", "phbExtension", "phbTools"]


def tab_children():
    """(page ids, tab label {id: text}, packing position {id: n}) of the notebookbar tab control."""
    root = ET.parse(office.OFFICE).getroot()
    control = next(o for o in root.iter("object") if o.get("id") == "ContextContainer")
    pages, labels, positions = [], {}, {}
    for child in control.findall("child"):
        obj = child.find("object")
        position = child.find("packing/property[@name='position']")
        if child.get("type") == "tab":
            labels[obj.get("id")] = obj.findtext("property[@name='label']")
        else:
            pages.append(obj.get("id"))
        if position is not None:
            positions[obj.get("id")] = int(position.text)
    return pages, labels, positions


class CalcTabsTest(unittest.TestCase):

    def setUp(self):
        self.tabs = json.loads(office.TABS.read_text(encoding="utf-8"))
        self.upstream = office.UPSTREAM.read_text(encoding="utf-8")
        self.office = office.OFFICE.read_text(encoding="utf-8")

    def test_office_ui_is_upstream_plus_tab_operations_plus_generated_pages(self):
        self.assertEqual(office.expected_office_ui(), self.office)

    def test_tab_order(self):
        pages, _labels, _positions = tab_children()
        self.assertEqual(PAGES, pages)

    def test_tab_labels(self):
        _pages, labels, _positions = tab_children()
        for label_id, text in LABELS.items():
            self.assertEqual(text, labels[label_id], label_id)

    def test_labels_keep_their_translation_context(self):
        self.assertIn('context="TabbedCalc|LayoutTabLabel">Page ~Layout<', self.office)
        self.assertIn('context="TabbedCalc|FunctionsTabLabel">For~mulas<', self.office)
        self.assertIn('context="TabbedCalc|HelpTabLabel">Hel~p<', self.office)

    def test_functions_and_data_swapped_their_positions(self):
        _pages, _labels, positions = tab_children()
        self.assertEqual((4, 4), (positions["phbFunctions"], positions["FunctionsLabel1"]))
        self.assertEqual((5, 5), (positions["phbData"], positions["DataLabel"]))
        self.assertEqual((16, 16), (positions["phbHelp"], positions["HelpLabel"]))

    def test_help_page_is_a_generated_page_with_markers_and_its_buttons(self):
        self.assertEqual(1, self.office.count("<!-- product:Help-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Help-end -->"))
        lines = self.office.split("\n")
        first, last = g.find_object(lines, "phbHelp")
        page = "\n".join(lines[first:last + 1])
        self.assertIn('class="sfxlo-PriorityMergedHBox" id="pmhbHelp"', page)
        self.assertEqual(7, page.count("sfxlo-NotebookbarToolBox"))  # filled by T7
        first, last = g.find_object(lines, "HelpLabel")
        label = "\n".join(lines[first:last + 1])
        self.assertIn('<property name="use-underline">True</property>', label)

    def test_every_other_tab_is_byte_identical_to_upstream(self):
        up, mine = self.upstream.split("\n"), self.office.split("\n")
        for page in UNTOUCHED:
            a, b = g.child_span(up, page), g.child_span(mine, page)
            self.assertEqual(up[a[0]:a[1] + 1], mine[b[0]:b[1] + 1], page)
        for label in ("FileLabel", "ExtensionLabel", "DevLabel", "ReviewLabel", "ViewLabel"):
            a, b = g.child_span(up, label), g.child_span(mine, label)
            self.assertEqual(up[a[0]:a[1] + 1], mine[b[0]:b[1] + 1], label)

    def test_the_operations_can_be_applied_twice(self):
        once = g.apply_tabs(self.upstream, self.tabs)
        self.assertEqual(once, g.apply_tabs(once, self.tabs))
        self.assertEqual(self.office, g.apply_tabs(self.office, self.tabs))

    def test_relabel_refuses_an_unexpected_text(self):
        with self.assertRaises(g.LayoutError):
            g.apply_tabs(self.upstream, {"relabel": [{"id": "LayoutLabel", "from": "~Nope", "to": "x"}]})


if __name__ == "__main__":
    unittest.main()

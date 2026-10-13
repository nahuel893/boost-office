# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_data.json"
HOME_LAYOUT = ROOT / "product/ui/calc_home.json"
UPSTREAM = ROOT / "sc/uiconfig/scalc/ui/notebookbar.ui"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
SUPPR = ROOT / "solenv/sanitizers/ui/modules/scalc.suppr"
UI_DIR = ROOT / "officecfg/registry/data/org/openoffice/Office/UI"
CONTROLLER_XCU = UI_DIR / "Controller.xcu"
POPUPMENU = ROOT / "sc/uiconfig/scalc/popupmenu"
OOR = "{http://openoffice.org/2001/registry}"
SECTIONS = ["Sources", "Transform", "Connections", "SortFilter", "Tools", "Forecast", "Outline", "Analyze"]
CAPTIONS = ["Get External Data", "Get & Transform", "Connections", "Sort & Filter", "Data Tools",
            "Forecast", "Outline", "Analyze"]
PLACEHOLDERS = {
    "DataFromDatabase": "From Database", "DataRecentSources": "Recent Sources",
    "DataConnections": "Connections", "DataConnectionProperties": "Properties",
    "DataFilterReapply": "Reapply", "DataFlashFill": "Flash Fill",
    "DataRelationships": "Relationships", "DataManageModel": "Manage Data Model",
    "DataForecastSheet": "Forecast Sheet",
}
MENUS = {
    "DataOtherSourcesMenu": ("Other Sources", "data_othersources"),
    "DataWhatIfMenu": ("What-If Analysis", "data_whatif"),
    "DataStatisticsMenu": ("Statistics", "statisticsmenu"),
}


def commands_xcu():
    """Label (and node names) of every command in the *Commands.xcu files."""
    labels = {}
    for path in UI_DIR.glob("*Commands.xcu"):
        for node in ET.parse(path).iter("node"):
            name = node.get(OOR + "name")
            if name and name.startswith(".uno:"):
                for prop in node.findall("prop"):
                    if prop.get(OOR + "name") == "Label":
                        labels[name] = prop.findtext("value")
    return labels


def controller_nodes():
    nodes = {}
    for node in ET.parse(CONTROLLER_XCU).iter("node"):
        props = {p.get(OOR + "name"): p.findtext("value") for p in node.findall("prop")}
        if "Command" in props:
            nodes[node.get(OOR + "name")] = props
    return nodes


class CalcDataUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.home = json.loads(HOME_LAYOUT.read_text(encoding="utf-8"))

    def items(self):
        return [i for s in self.layout["sections"] for c in s["columns"] for b in c
                for i in b["items"] + []] + [i for s in self.layout["sections"]
                                             for i in s.get("footer", {}).get("items", [])]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("phbData", self.layout["page"])
        self.assertEqual("Data", self.layout["id_prefix"])
        self.assertEqual("TabbedCalc", self.layout["context"])
        self.assertEqual(SECTIONS, [s["name"] for s in self.layout["sections"]])
        self.assertEqual(CAPTIONS, [s["caption"] for s in self.layout["sections"]])

    def test_old_data_menu_is_removed(self):
        self.assertIn("Menu Data", self.layout["remove_objects"])
        text = OFFICE.read_text(encoding="utf-8")
        self.assertNotIn('id="Menu Data"', text)
        self.assertNotIn('id="Data-Menu"', text)

    def test_office_ui_is_upstream_plus_home_and_data(self):
        text = UPSTREAM.read_text(encoding="utf-8")
        for layout in (self.home, self.layout):
            text = g.splice(text, layout, g.emit_page(layout))
        self.assertEqual(text, OFFICE.read_text(encoding="utf-8"))

    def test_refresh_group_ungroup_are_plain_buttons_for_now(self):
        by_cmd = {i["cmd"]: i for i in self.items()}
        for cmd in ("DataAreaRefresh", "Group", "Ungroup"):
            self.assertEqual("button", by_cmd[cmd].get("kind", "button"), cmd)

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu()
        for item in self.items():
            self.assertIn(".uno:" + item["cmd"], labels, item["cmd"])

    def test_placeholders_are_label_only(self):
        labels, nodes = commands_xcu(), controller_nodes()
        sdi = "".join(p.read_text(encoding="utf-8", errors="replace")
                      for p in (ROOT / "sc/sdi").glob("*.sdi"))
        used = {i["cmd"] for i in self.items()}
        controlled = {v["Command"] for v in nodes.values()}
        for cmd, label in PLACEHOLDERS.items():
            self.assertIn(cmd, used)
            self.assertEqual(label, labels[".uno:" + cmd], cmd)
            self.assertNotIn(".uno:" + cmd, controlled, cmd)
            self.assertIsNone(re.search(r"\b" + cmd + r"\b", sdi), cmd)

    def test_placeholders_have_a_not_available_tooltip(self):
        tree = ET.parse(UI_DIR / "CalcCommands.xcu")
        tips = {}
        for node in tree.iter("node"):
            for prop in node.findall("prop"):
                if prop.get(OOR + "name") == "TooltipLabel":
                    tips[node.get(OOR + "name")] = prop.findtext("value")
        for cmd, label in PLACEHOLDERS.items():
            self.assertEqual(label + " (not available yet)", tips[".uno:" + cmd], cmd)

    def test_dropdown_commands_have_popup_and_toolbar_controllers(self):
        labels, nodes = commands_xcu(), controller_nodes()
        for cmd, (label, resource) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd]
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in ours}
            popup = kinds["ResourceMenuController"]
            self.assertEqual(resource, popup["Value"])
            self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", popup["Module"])
            toolbar = kinds["GenericPopupToolbarController"]
            self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", toolbar["Module"])
            self.assertNotIn("Value", toolbar)

    def test_statistics_menu_command_keeps_no_new_toolbar_controller(self):
        ours = [v for v in controller_nodes().values() if v["Command"] == ".uno:StatisticsMenu"]
        self.assertEqual(["ResourceMenuController"], [v["Controller"].rsplit(".", 1)[1] for v in ours])

    def test_menu_files_exist_and_are_registered(self):
        mk = (ROOT / "sc/UIConfig_scalc.mk").read_text(encoding="utf-8")
        for resource in ("data_othersources", "data_whatif"):
            self.assertTrue((POPUPMENU / (resource + ".xml")).exists(), resource)
            self.assertIn("sc/uiconfig/scalc/popupmenu/" + resource + " ", mk)

    def test_menu_contents(self):
        def ids(name):
            return [e.get("{http://openoffice.org/2001/menu}id") for e in
                    ET.parse(POPUPMENU / (name + ".xml")).iter("{http://openoffice.org/2001/menu}menuitem")]
        self.assertEqual([".uno:ManageXMLSource", ".uno:DataStreams"], ids("data_othersources"))
        self.assertEqual([".uno:ScenarioManager", ".uno:GoalSeekDialog",
                          ".uno:TableOperationDialog", ".uno:SolverDialog"], ids("data_whatif"))
        self.assertEqual(13, len(ids("statisticsmenu")))

    def test_suppr_keeps_home_and_data_entries(self):
        suppr = SUPPR.read_text(encoding="utf-8")
        prefix = "sc/uiconfig/scalc/ui/notebookbar_office.ui:"
        for layout in (self.home, self.layout):
            for wid in g.ids_of(layout):
                if wid.startswith("btn"):
                    self.assertRegex(suppr, re.escape(prefix) + r"//Gtk(Menu)?ToolButton\[@id='"
                                     + re.escape(wid) + r"'\] button-no-label")

    def test_regenerating_either_page_keeps_both_suppr_entries(self):
        ui = OFFICE.read_text(encoding="utf-8")
        suppr = SUPPR.read_text(encoding="utf-8")
        for layout in (self.home, self.layout):
            regenerated = g.splice(ui, layout, g.emit_page(layout))
            self.assertEqual(ui, regenerated)
            self.assertEqual(suppr, g.sync_suppr(suppr, "sc/uiconfig/scalc/ui/notebookbar_office.ui", regenerated))


if __name__ == "__main__":
    unittest.main()

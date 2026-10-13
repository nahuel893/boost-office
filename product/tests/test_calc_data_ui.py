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
SPLITS = {  # command: (label, body command, popup resource, popup items, icon)
    "DataRefresh": ("Refresh", "DataAreaRefresh", "data_refresh",
                    [".uno:DataAreaRefresh", ".uno:DataProviderRefresh", ".uno:RecalcPivotTable",
                     ".uno:CalculateHard"], "cmd/32/dataarearefresh.png"),
    "DataGroup": ("Group", "Group", "data_group", [".uno:Group", ".uno:AutoOutline"],
                  "cmd/sc_group.png"),
    "DataUngroup": ("Ungroup", "Ungroup", "data_ungroup", [".uno:Ungroup", ".uno:ClearOutline"],
                    "cmd/sc_ungroup.png"),
}
# split slot -> slot it mirrors (every invalidation of the original must also hit the new one)
SPLIT_SLOTS = {"FID_DATA_REFRESH": "SID_REFRESH_DBAREA", "FID_DATA_GROUP": "SID_OUTLINE_MAKE",
               "FID_DATA_UNGROUP": "SID_OUTLINE_REMOVE"}
PLACEHOLDER_SLOTS = {
    "DataFromDatabase": "FID_DATA_FROM_DATABASE", "DataRecentSources": "FID_DATA_RECENT_SOURCES",
    "DataConnections": "FID_DATA_CONNECTIONS", "DataConnectionProperties": "FID_DATA_CONN_PROPS",
    "DataFilterReapply": "FID_DATA_FILTER_REAPPLY", "DataFlashFill": "FID_DATA_FLASH_FILL",
    "DataRelationships": "FID_DATA_RELATIONSHIPS", "DataManageModel": "FID_DATA_MANAGE_MODEL",
    "DataForecastSheet": "FID_DATA_FORECAST_SHEET",
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

    def test_width_savers_are_icon_only_small_buttons(self):
        # Excel's A-Z / Z-A buttons carry no label; the tooltip keeps the name. EditLinks
        # ("Links to External Files") is the widest label on the page, so it is icon-only too.
        # Together they let all 8 sections fit at 1920 px.
        boxes = {b["id"]: b for s in self.layout["sections"] for c in s["columns"] for b in c}
        for box_id in ("SortAscending", "SortDescending", "Shuffle", "EditLinks"):
            self.assertEqual("small", boxes[box_id]["style"], box_id)

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

    def test_refresh_group_ungroup_are_split_buttons_on_new_commands(self):
        by_cmd = {i["cmd"]: i for i in self.items()}
        for cmd, (_label, body, _res, _items, _icon) in SPLITS.items():
            self.assertEqual("split", by_cmd[cmd].get("kind"), cmd)
            self.assertNotIn("icon", by_cmd[cmd], "icon resolves from the boost theme by command name: " + cmd)
            self.assertNotIn(body, by_cmd, "the old command must leave the page: " + body)

    def test_split_commands_have_labels_and_body_toolbar_controller(self):
        labels, nodes = commands_xcu(), controller_nodes()
        for cmd, (label, _body, resource, _items, _icon) in SPLITS.items():
            self.assertEqual(label, labels[".uno:" + cmd])
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd]
            self.assertEqual(1, len(ours), cmd)
            self.assertTrue(ours[0]["Controller"].endswith("GenericPopupToolbarController"), cmd)
            self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", ours[0]["Module"])
            self.assertEqual(".uno:" + cmd + "Menu", ours[0]["Value"], cmd)

    def test_split_popup_commands_have_menu_controllers_and_labels(self):
        labels, nodes = commands_xcu(), controller_nodes()
        for cmd, (label, _body, resource, _items, _icon) in SPLITS.items():
            self.assertIn(".uno:" + cmd + "Menu", labels)
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd + "Menu"]
            self.assertEqual(1, len(ours), cmd)
            self.assertTrue(ours[0]["Controller"].endswith("ResourceMenuController"), cmd)
            self.assertEqual(resource, ours[0]["Value"])
            self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", ours[0]["Module"])

    def test_no_controller_is_registered_on_the_original_commands(self):
        controlled = {v["Command"] for v in controller_nodes().values()}
        for _label, body, *_rest in SPLITS.values():
            self.assertNotIn(".uno:" + body, controlled, body)

    def test_split_popup_menu_files_exact(self):
        mk = (ROOT / "sc/UIConfig_scalc.mk").read_text(encoding="utf-8")
        for _label, _body, resource, items, _icon in SPLITS.values():
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("sc/uiconfig/scalc/popupmenu/" + resource + " ", mk)
            ids = [e.get("{http://openoffice.org/2001/menu}id") for e in
                   ET.parse(path).iter("{http://openoffice.org/2001/menu}menuitem")]
            self.assertEqual(items, ids, resource)

    def sc_hrc_ids(self):
        text = (ROOT / "sc/inc/sc.hrc").read_text(encoding="utf-8")
        return {m.group(1): int(m.group(2)) for m in re.finditer(
            r"#define\s+(\w+)\s+(?:TypedWhichId<\w+>)?\(SID_NEW_SLOTS\s*\+\s*(\d+)\)", text)}

    def test_new_slot_ids_continue_after_merge_center_without_collision(self):
        ids = self.sc_hrc_ids()
        mine = list(SPLIT_SLOTS) + list(PLACEHOLDER_SLOTS.values())
        for name in mine:
            self.assertIn(name, ids)
            self.assertGreater(ids[name], ids["FID_HOME_MERGE_CENTER"])
        values = list(ids.values())
        self.assertEqual(len(values), len(set(values)), "duplicate SID_NEW_SLOTS offsets")
        self.assertLess(max(ids[n] for n in mine), 400)  # SID_SC_START range ends at +999

    def sdi_text(self):
        return "".join(p.read_text(encoding="utf-8", errors="replace")
                       for p in ROOT.glob("*/sdi/*.sdi"))

    def test_split_body_slots_reuse_original_state_and_exec_paths(self):
        sdi = self.sdi_text()
        cell = (ROOT / "sc/sdi/cellsh.sdi").read_text(encoding="utf-8")
        for slot, orig in SPLIT_SLOTS.items():
            line = re.search(r"^\s*" + orig + r"\s*\[(.*)\]", cell, re.M)
            mine = re.search(r"^\s*" + slot + r"\s*\[(.*)\]", cell, re.M)
            self.assertIsNotNone(mine, slot)
            self.assertEqual(line.group(1).strip(), mine.group(1).strip(), slot)
        for cmd in SPLITS:
            self.assertRegex(sdi, r"SfxVoidItem " + cmd + r" FID_", cmd)

    def test_every_invalidation_of_an_original_slot_also_hits_its_split_slot(self):
        for slot, orig in SPLIT_SLOTS.items():
            for path in (ROOT / "sc/source").rglob("*.cxx"):
                text = path.read_text(encoding="utf-8", errors="replace")
                n_orig = len(re.findall(r"Invalidate\s*\(\s*" + orig + r"\b", text))
                n_new = len(re.findall(r"Invalidate\s*\(\s*" + slot + r"\b", text))
                self.assertGreaterEqual(n_new, n_orig, f"{slot} not mirrored in {path}")

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu()
        for item in self.items():
            self.assertIn(".uno:" + item["cmd"], labels, item["cmd"])

    def test_placeholders_have_labels_and_an_always_disabled_slot(self):
        labels, nodes = commands_xcu(), controller_nodes()
        sdi = self.sdi_text()
        cell = (ROOT / "sc/sdi/cellsh.sdi").read_text(encoding="utf-8")
        state = (ROOT / "sc/source/ui/view/cellsh.cxx").read_text(encoding="utf-8")
        used = {i["cmd"] for i in self.items()}
        controlled = {v["Command"] for v in nodes.values()}
        for cmd, label in PLACEHOLDERS.items():
            slot = PLACEHOLDER_SLOTS[cmd]
            self.assertIn(cmd, used)
            self.assertEqual(label, labels[".uno:" + cmd], cmd)
            self.assertNotIn(".uno:" + cmd, controlled, cmd)
            self.assertRegex(sdi, r"SfxVoidItem " + cmd + " " + slot + r"\b", cmd)
            row = re.search(r"^\s*" + slot + r"\s*\[(.*)\]", cell, re.M)
            self.assertIsNotNone(row, cmd)
            self.assertNotIn("ExecMethod", row.group(1), cmd)  # scaffold: state only
            self.assertIn("case " + slot + ":", state, cmd)

    def test_placeholder_slots_are_disabled_in_get_state_and_ignored_in_execute(self):
        state = (ROOT / "sc/source/ui/view/cellsh.cxx").read_text(encoding="utf-8")
        exe = (ROOT / "sc/source/ui/view/cellsh3.cxx").read_text(encoding="utf-8")
        block = state[state.index("case " + PLACEHOLDER_SLOTS["DataFromDatabase"] + ":"):]
        block = block[:block.index("break;")]
        for slot in PLACEHOLDER_SLOTS.values():
            self.assertIn("case " + slot + ":", block, slot)
        self.assertIn("rSet.DisableItem( nWhich )", block)
        for slot in PLACEHOLDER_SLOTS.values():
            self.assertNotIn(slot, exe, slot)

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

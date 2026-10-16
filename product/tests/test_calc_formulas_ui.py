# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The Formulas tab: layout vs product/docs/design/calc-formulas-tab-layout.txt, labels, menus,
the function-category menu controller (C++, T4c) and the AutoSum split."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from product.tests import office, placeholders
from product.tests.commands import commands_xcu, controller_nodes, flagged_commands, tooltips
from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "product/ui/calc_formulas.json"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
SUPPR = ROOT / "solenv/sanitizers/ui/modules/scalc.suppr"
POPUPMENU = ROOT / "sc/uiconfig/scalc/popupmenu"
MENU = "{http://openoffice.org/2001/menu}"
PYTHON = ".uno:FormulasPython?Action:string="
AUTOSUM = ".uno:AutoSum?Function:string="
SEP = "-"  # a separator in a menu item list
MENUBARMANAGER = ROOT / "framework/source/uielement/menubarmanager.cxx"


def run_single_bool_argument(urls):
    """Compile getSingleBoolArgument out of menubarmanager.cxx and run it on each URL: "true" or
    "false" for a single boolean argument, "none" when the URL is no such variant."""
    compiler = shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        raise unittest.SkipTest("no C++ compiler")
    src = MENUBARMANAGER.read_text(encoding="utf-8")
    start = src.index("bool getSingleBoolArgument(")
    function = src[start:src.index("\n}\n", start) + 3]
    program = "\n".join([
        "#include <cstdio>", "#include <cstring>", "#include <string>", "#include <string_view>",
        function,
        "int main(int argc, char** argv)",
        "{",
        "    for (int i = 1; i < argc; ++i)",
        "    {",
        "        const std::u16string aURL(argv[i], argv[i] + std::strlen(argv[i]));",
        "        bool bValue = false;",
        "        const bool bMatch = getSingleBoolArgument(aURL, bValue);",
        '        std::printf("%s\\n", !bMatch ? "none" : bValue ? "true" : "false");',
        "    }",
        "}",
    ])
    with tempfile.TemporaryDirectory() as tmp:
        source, exe = Path(tmp) / "rule.cxx", Path(tmp) / "rule"
        source.write_text(program, encoding="utf-8")
        subprocess.run([compiler, "-std=c++20", "-o", str(exe), str(source)], check=True,
                       capture_output=True)
        out = subprocess.run([str(exe), *urls], check=True, capture_output=True, text=True).stdout
    return out.splitlines()

CATEGORY_MENUS = ["FormulasRecentlyUsedMenu", "FormulasFinancialMenu", "FormulasLogicalMenu",
                  "FormulasTextMenu", "FormulasDateTimeMenu", "FormulasLookupMenu",
                  "FormulasMathMenu", "FormulasMoreFunctionsMenu"]
# section -> (caption, [(style, [url, ...]) per toolbox in document order])
DESIGN = {
    "FunctionLibrary": ("Function Library",
                        [("large", [".uno:FunctionDialog"]), ("large", [".uno:FormulasAutoSum"])]
                        + [("large", [".uno:" + m]) for m in CATEGORY_MENUS]),
    "Python": ("Python", [("large", [PYTHON + "insert"]), ("small-label", [PYTHON + "reset"]),
                          ("small-label", [PYTHON + "editor"]), ("small-label", [PYTHON + "init"])]),
    "DefinedNames": ("Defined Names", [
        ("large", [".uno:DefineName"]), ("small-label", [".uno:AddName"]),
        ("small-label", [".uno:FormulasUseInFormulaMenu"]), ("small-label", [".uno:CreateNames"])]),
    "Auditing": ("Formula Auditing", [
        ("small-label", [".uno:ShowPrecedents"]), ("small-label", [".uno:ShowDependents"]),
        ("small-label", [".uno:FormulasRemoveArrowsMenu"]), ("small", [".uno:ToggleFormula"]),
        ("small", [".uno:FormulasErrorCheckingMenu"]), ("small", [".uno:FormulasEvaluateFormula"]),
        ("large", [".uno:FormulasWatchWindow"])]),
    "Calculation": ("Calculation", [
        ("large", [".uno:FormulasCalcOptionsMenu"]), ("small", [".uno:Calculate"]),
        ("small", [".uno:FormulasCalculateSheet"])]),
}
SHAPES = {"FunctionLibrary": [1] * 10, "Python": [1, 3], "DefinedNames": [1, 3],
          "Auditing": [3, 3, 1], "Calculation": [1, 2]}
MENUS = {  # popup command: (label, popup resource, popup items in order); None: built by C++
    "FormulasAutoSumMenu": ("AutoSum", "formulas_autosum",
                            [".uno:AutoSum", AUTOSUM + "average", AUTOSUM + "count", AUTOSUM + "max",
                             AUTOSUM + "min", SEP, ".uno:FunctionDialog"]),
    "FormulasRecentlyUsedMenu": ("Recently Used", None, None),
    "FormulasFinancialMenu": ("Financial", None, None),
    "FormulasLogicalMenu": ("Logical", None, None),
    "FormulasTextMenu": ("Text", None, None),
    "FormulasDateTimeMenu": ("Date & Time", None, None),
    "FormulasLookupMenu": ("Lookup & Reference", None, None),
    "FormulasMathMenu": ("Math & Trig", None, None),
    "FormulasMoreFunctionsMenu": ("More Functions", None, None),
    "FormulasUseInFormulaMenu": ("Use in Formula", "formulas_useinformula", [".uno:InsertName"]),
    "FormulasRemoveArrowsMenu": ("Remove Arrows", "formulas_removearrows",
                                 [".uno:ClearArrows", ".uno:ClearArrowPrecedents",
                                  ".uno:ClearArrowDependents"]),
    "FormulasErrorCheckingMenu": ("Error Checking", "formulas_errorchecking",
                                  [".uno:FormulasErrorChecking", ".uno:ShowErrors"]),
    "FormulasCalcOptionsMenu": ("Calculation Options", "formulas_calcoptions",
                                [".uno:AutomaticCalculation?AutomaticCalculation:bool=true",
                                 ".uno:AutomaticCalculation?AutomaticCalculation:bool=false"]),
}
SPLIT_BODY = {"FormulasAutoSum": "FormulasAutoSumMenu"}
PLACEHOLDER_LABELS = {
    PYTHON + "insert": "Insert Python", PYTHON + "reset": "Reset", PYTHON + "editor": "Editor",
    PYTHON + "init": "Initialization", ".uno:FormulasErrorChecking": "Error Checking",
    ".uno:FormulasEvaluateFormula": "Evaluate Formula", ".uno:FormulasWatchWindow": "Watch Window",
    ".uno:FormulasCalculateSheet": "Calculate Sheet"}
PLACEHOLDER_LABELS = placeholders.drop_implemented(PLACEHOLDER_LABELS)  # implemented ones are no placeholder
FORMULAS_SLOTS = range(403, 408)
VARIANT_LABELS = {AUTOSUM + "average": "Average", AUTOSUM + "count": "Count Numbers",
                  AUTOSUM + "max": "Max", AUTOSUM + "min": "Min"}
# T4c: one C++ popup menu controller fills the eight Function Library menus (design: "Menu of
# .uno:Formulas*Menu"). Category ids of sc/inc/scfuncs.hxx; 0 is the recently used list.
FUNCTION_MENU_CONTROLLER = "com.sun.star.comp.Calc.FunctionMenuController"
FUNCTION_MENU_SOURCE = "sc/source/ui/unoobj/funcmenucontroller.cxx"
DESIGN_CATEGORIES = {"FormulasRecentlyUsedMenu": 0, "FormulasFinancialMenu": 3, "FormulasLogicalMenu": 5,
                     "FormulasTextMenu": 10, "FormulasDateTimeMenu": 2, "FormulasLookupMenu": 9,
                     "FormulasMathMenu": 6}
# More Functions: (submenu command, label, category) in the design's order
MORE_FUNCTIONS = [("FormulasStatisticalMenu", "Statistical", 8), ("FormulasEngineeringMenu", "Engineering", 11),
                  ("FormulasInformationMenu", "Information", 4), ("FormulasDatabaseMenu", "Database", 1),
                  ("FormulasArrayMenu", "Array", 7)]
STATIC_CATEGORY_POPUPS = ["formulas_recentlyused", "formulas_financial", "formulas_logical", "formulas_text",
                          "formulas_datetime", "formulas_lookup", "formulas_math", "formulas_morefunctions"]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def sdi_row(path, slot):
    match = re.search(r"^\s*" + slot + r"\s*\[(.*)\]", read(path), re.M)
    return match.group(1).strip() if match else None


class CalcFormulasUiTest(unittest.TestCase):

    def setUp(self):
        self.layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
        self.office = OFFICE.read_text(encoding="utf-8")

    def boxes(self, section):
        return list(g.boxes_of(section))  # the columns' toolboxes, then the footer

    def items(self):
        return [i for s in self.layout["sections"] for b in self.boxes(s) for i in b["items"]]

    def test_page_and_sections_follow_the_design(self):
        self.assertEqual("phbFunctions", self.layout["page"])
        self.assertEqual("Formulas", self.layout["id_prefix"])
        self.assertEqual("TabbedCalc", self.layout["context"])
        self.assertEqual([], self.layout["remove_objects"])
        self.assertEqual(list(DESIGN), [s["name"] for s in self.layout["sections"]])
        for section in self.layout["sections"]:
            self.assertEqual(DESIGN[section["name"]][0], section["caption"])
            self.assertEqual(3, section["rows"], section["name"])

    def test_every_control_is_there_in_order_with_its_size(self):
        for section in self.layout["sections"]:
            got = [(b["style"], [g.item_url(i) for i in b["items"]]) for b in self.boxes(section)]
            self.assertEqual(DESIGN[section["name"]][1], got, section["name"])

    def test_the_sections_have_the_design_column_shape(self):
        shapes = {s["name"]: [len(c) for c in s["columns"]] for s in self.layout["sections"]}
        self.assertEqual(SHAPES, shapes)

    def test_the_menu_commands_and_the_split_body_are_menu_buttons_the_rest_plain(self):
        for item in self.items():
            expected = "split" if item["cmd"] in MENUS or item["cmd"] in SPLIT_BODY else "button"
            self.assertEqual(expected, item.get("kind", "button"), item["cmd"])
        # 12 menu commands on the ribbon (the AutoSum menu hangs on the split body)
        self.assertEqual(12 + 1, len([i for i in self.items() if i.get("kind") == "split"]))

    def test_url_variants_carry_a_short_id_the_url_as_action_and_a_plain_icon_name(self):
        variants = [(b["style"], i) for s in self.layout["sections"] for b in self.boxes(s)
                    for i in b["items"] if "action" in i]
        self.assertEqual(4, len(variants))
        for style, item in variants:
            self.assertRegex(item["cmd"], r"^[A-Za-z0-9]+$")
            base, value = re.match(r"\.uno:(\w+)\?\w+:\w+=(\w+)$", item["action"]).groups()
            prefix = "cmd/32/" if style == "large" else "cmd/sc_"
            self.assertEqual("%s%s_%s.png" % (prefix, base.lower(), value), item["icon"], item["cmd"])
        self.assertEqual(len(variants), len({i["cmd"] for _s, i in variants}))

    def test_the_old_functions_page_children_are_gone(self):
        for old in ("btnFunctionsAutoSum", "btnFunctionsSolverDialog", "btnFunctionsGoalSeekDialog",
                    "btnFunctionsShowInvalid", "btnFunctionsFTestDialog", 'id="Functions-',
                    "btnFunctionsAuditingFillMode"):
            self.assertNotIn(old, self.office)
        self.assertEqual(1, self.office.count("<!-- product:Formulas-begin -->"))
        self.assertEqual(1, self.office.count("<!-- product:Formulas-end -->"))
        lines = self.office.split("\n")
        first, last = g.find_object(lines, "phbFunctions")
        self.assertIn('id="pmhbFormulas"', "\n".join(lines[first:last + 1]))

    def test_office_ui_is_upstream_plus_tabs_and_every_generated_page(self):
        self.assertIn("Formulas", {layout["id_prefix"] for layout in office.page_layouts()})
        self.assertEqual(office.expected_office_ui(), self.office)

    def test_no_widget_id_is_used_twice_in_the_whole_ui(self):
        ids = re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office)
        self.assertEqual([], sorted({i for i in ids if ids.count(i) > 1}))

    def test_every_command_in_the_layout_has_a_label(self):
        labels = commands_xcu()
        for item in self.items():
            self.assertIn(g.item_url(item), labels, item["cmd"])

    def test_every_new_command_has_the_image_flag(self):
        flagged = flagged_commands()
        for item in self.items():
            if "icon" not in item:
                self.assertIn(g.item_url(item), flagged, item["cmd"] + " is left out of the image list")
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, flagged, url)

    def test_create_names_has_the_image_flag_so_an_icon_can_show(self):
        self.assertIn(".uno:CreateNames", flagged_commands())

    def test_placeholder_labels_and_tooltips_follow_excel(self):
        labels, tips = commands_xcu(), tooltips()
        for url, label in PLACEHOLDER_LABELS.items():
            self.assertEqual(label, labels[url], url)
            self.assertEqual(label + " (not available yet)", tips[url], url)

    def test_the_registry_labels_every_formulas_slot_and_variant(self):
        by_url = placeholders.labels_by_url()
        self.assertEqual(PLACEHOLDER_LABELS, {u: l for u, l in by_url.items()
                                              if u.startswith(".uno:Formulas")})
        for entry in placeholders.load():
            if entry["offset"] in FORMULAS_SLOTS and "variants" in entry:
                self.assertEqual(entry["variants"], list(entry["variant_labels"]), entry["command"])

    def test_every_formulas_placeholder_button_is_on_the_page_without_a_controller(self):
        controlled = {v["Command"] for v in controller_nodes().values()}
        used = {g.item_url(i) for i in self.items()}
        in_menus = {url for _l, _r, items in MENUS.values() for url in items or []}
        for url in PLACEHOLDER_LABELS:
            self.assertIn(url, used | in_menus, url)
            self.assertNotIn(url, controlled, url)
        # Error Checking is a placeholder item inside a menu, the other seven are ribbon buttons
        self.assertEqual({".uno:FormulasErrorChecking"}, set(PLACEHOLDER_LABELS) - used)

    def test_menu_variants_have_labels(self):
        labels = commands_xcu()
        for url, label in VARIANT_LABELS.items():
            self.assertEqual(label, labels[url], url)

    def test_the_new_commands_have_labels_and_the_image_flag(self):
        labels, flagged = commands_xcu(), flagged_commands()
        for cmd, (label, _resource, _items) in MENUS.items():
            self.assertEqual(label, labels[".uno:" + cmd], cmd)
            self.assertIn(".uno:" + cmd, flagged, cmd)
        self.assertEqual("AutoSum", labels[".uno:FormulasAutoSum"])
        self.assertIn(".uno:FormulasAutoSum", flagged)

    def test_the_menu_commands_have_popup_and_toolbar_controllers(self):
        nodes = controller_nodes()
        self.assertEqual(13, len(MENUS))
        for cmd, (_label, resource, _items) in MENUS.items():
            ours = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd]
            kinds = {v["Controller"].rsplit(".", 1)[1]: v for v in ours}
            popup = "ResourceMenuController" if resource else "FunctionMenuController"
            expected = {popup}
            if cmd != "FormulasAutoSumMenu":  # the AutoSum arrow is the body's controller
                expected.add("GenericPopupToolbarController")
            self.assertEqual(expected, set(kinds), cmd)
            self.assertEqual(resource, kinds[popup].get("Value"), cmd)
            for kind in kinds.values():
                self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", kind["Module"])
            if "GenericPopupToolbarController" in kinds:
                self.assertNotIn("Value", kinds["GenericPopupToolbarController"])

    def test_the_autosum_body_has_a_toolbar_controller_opening_its_menu(self):
        ours = [v for v in controller_nodes().values() if v["Command"] == ".uno:FormulasAutoSum"]
        self.assertEqual(1, len(ours))
        self.assertTrue(ours[0]["Controller"].endswith("GenericPopupToolbarController"))
        self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", ours[0]["Module"])
        self.assertEqual(".uno:FormulasAutoSumMenu", ours[0]["Value"])

    def test_no_controller_is_registered_on_the_original_autosum(self):
        controlled = {v["Command"] for v in controller_nodes().values()}
        self.assertNotIn(".uno:AutoSum", controlled)

    def menu_ids(self, element):
        out = []
        for e in element:
            if e.tag in (MENU + "menuitem", MENU + "menu"):
                out.append(e.get(MENU + "id"))
            elif e.tag == MENU + "menuseparator":
                out.append(SEP)
        return out

    def test_popup_files_exist_are_registered_and_list_the_design_items(self):
        mk = read("sc/UIConfig_scalc.mk")
        for _label, resource, items in MENUS.values():
            if resource is None:
                continue
            path = POPUPMENU / (resource + ".xml")
            self.assertTrue(path.exists(), resource)
            self.assertIn("sc/uiconfig/scalc/popupmenu/" + resource + " \\", mk)
            self.assertEqual(items, self.menu_ids(ET.parse(path).getroot()), resource)

    def test_every_formulas_popup_file_is_one_of_the_design_menus(self):
        files = {p.stem for p in POPUPMENU.glob("formulas_*.xml")}
        self.assertEqual({r for _l, r, _i in MENUS.values() if r}, files)

    def test_every_popup_item_is_a_known_command(self):
        labels = commands_xcu()
        for _label, _resource, items in MENUS.values():
            for url in items or []:
                if url != SEP:
                    self.assertIn(url, labels, url)

    def test_calculation_options_offers_automatic_and_manual_as_variants_of_one_slot(self):
        # risk R9: both are URL variants of .uno:AutomaticCalculation; MenuBarManager::statusChanged
        # checks only the one whose argument equals the slot's boolean (see test_framework_menu_rule).
        auto = ".uno:AutomaticCalculation?AutomaticCalculation:bool="
        self.assertEqual([auto + "true", auto + "false"], MENUS["FormulasCalcOptionsMenu"][2])
        labels = commands_xcu()
        self.assertEqual("Automatic", labels[auto + "true"])
        self.assertEqual("Manual", labels[auto + "false"])
        self.assertEqual("Auto~Calculate", labels[".uno:AutomaticCalculation"])
        self.assertIn(".uno:AutomaticCalculation", flagged_commands())

    def test_framework_menu_rule_checks_a_single_bool_argument_item_only_when_state_equals_it(self):
        src = MENUBARMANAGER.read_text(encoding="utf-8")
        self.assertIn("getSingleBoolArgument( menuItemHandler->aParsedItemURL, bArgument )", src)
        self.assertIn("bCheckmark = ( bCheckmark == bArgument );", src)
        self.assertLess(src.index("bCheckmark = ( bCheckmark == bArgument );"),
                        src.index("m_pVCLMenu->CheckItem( menuItemHandler->nItemId, bCheckmark );"))

    def test_framework_menu_rule_reads_the_bool_type_from_the_arguments_type_segment(self):
        # T8a: getSingleBoolArgument, compiled from the source as it is and run on URLs. The type
        # is what "Name:type=value" has between the first ':' and the first '=' (as sfx2's
        # SfxDispatchController_Impl::addParametersToArgs reads it), so a string value that
        # contains ":bool=true" is no boolean variant.
        cases = {
            ".uno:Orientation?isLandscape:bool=true": "true",
            ".uno:Orientation?isLandscape:bool=false": "false",
            ".uno:AutomaticCalculation?AutomaticCalculation:bool=false": "false",
            ".uno:X?Name:string=a:bool=true": "none",
            ".uno:X?Name:string=:bool=false": "none",
            ".uno:X?Name:string=bool=true": "none",
            ".uno:X?:bool=true": "none",
            ".uno:X?Name:boolean=true": "none",
            ".uno:X?Name:bool=yes": "none",
            ".uno:X?A:bool=true&B:bool=false": "none",
            ".uno:X?Name:short=1": "none",
            ".uno:X": "none",
        }
        self.assertEqual(cases, dict(zip(cases, run_single_bool_argument(list(cases)))))

    def test_suppr_has_an_entry_for_every_button(self):
        suppr = SUPPR.read_text(encoding="utf-8")
        prefix = "sc/uiconfig/scalc/ui/notebookbar_office.ui:"
        for wid in g.ids_of(self.layout):
            if wid.startswith("btn"):
                self.assertRegex(suppr, re.escape(prefix) + r"//Gtk(Menu)?ToolButton\[@id='"
                                 + re.escape(wid) + r"'\] button-no-label")

    def test_suppr_has_no_entry_for_the_removed_upstream_widgets(self):
        suppr = SUPPR.read_text(encoding="utf-8")
        present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', self.office))
        prefix = "sc/uiconfig/scalc/ui/notebookbar_office.ui:"
        for line in suppr.splitlines():
            match = re.search(r"@id='([^']+)'", line)
            if line.startswith(prefix) and match:
                self.assertIn(match.group(1), present, line)

    def test_regenerating_the_page_changes_nothing(self):
        regenerated = g.splice(self.office, self.layout, g.emit_page(self.layout))
        self.assertEqual(self.office, regenerated)
        suppr = SUPPR.read_text(encoding="utf-8")
        self.assertEqual(suppr, g.sync_suppr(suppr, "sc/uiconfig/scalc/ui/notebookbar_office.ui", regenerated))


class FunctionMenuControllerTest(unittest.TestCase):
    """The eight Function Library menus come from one sc popup menu controller (T4c)."""

    def source(self):
        return read(FUNCTION_MENU_SOURCE)

    def category_ids(self):
        return {m.group(1): int(m.group(2))
                for m in re.finditer(r"#define\s+(ID_FUNCTION_GRP_\w+)\s+(\d+)", read("sc/inc/scfuncs.hxx"))}

    def test_the_eight_category_menus_have_the_function_menu_controller_and_no_resource(self):
        nodes = controller_nodes()
        for cmd in CATEGORY_MENUS:
            popups = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd
                      and not v["Controller"].endswith("ToolbarController")]
            self.assertEqual(1, len(popups), cmd)
            self.assertEqual(FUNCTION_MENU_CONTROLLER, popups[0]["Controller"], cmd)
            self.assertEqual("com.sun.star.sheet.SpreadsheetDocument", popups[0]["Module"], cmd)
            self.assertNotIn("Value", popups[0], cmd)
        users = {v["Command"] for v in nodes.values() if v["Controller"] == FUNCTION_MENU_CONTROLLER}
        self.assertEqual({".uno:" + cmd for cmd in CATEGORY_MENUS}, users)

    def test_the_dropdowns_keep_their_toolbar_controllers(self):
        nodes = controller_nodes()
        for cmd in CATEGORY_MENUS:
            tools = [v for v in nodes.values() if v["Command"] == ".uno:" + cmd
                     and v["Controller"].endswith("GenericPopupToolbarController")]
            self.assertEqual(1, len(tools), cmd)
            self.assertNotIn("Value", tools[0], cmd)

    def test_the_controller_is_an_sc_uno_component_with_a_constructor(self):
        component = ET.parse(ROOT / "sc/util/sc.component").getroot()
        ns = "{http://openoffice.org/2010/uno-components}"
        impls = [i for i in component.iter(ns + "implementation") if i.get("name") == FUNCTION_MENU_CONTROLLER]
        self.assertEqual(1, len(impls))
        self.assertEqual("Calc_FunctionMenuController_get_implementation", impls[0].get("constructor"))
        self.assertEqual(["com.sun.star.frame.PopupMenuController"],
                         [s.get("name") for s in impls[0].iter(ns + "service")])
        self.assertRegex(self.source(), r'extern "C" SAL_DLLPUBLIC_EXPORT css::uno::XInterface\*\s*'
                                        r"Calc_FunctionMenuController_get_implementation\(")
        self.assertIn('u"' + FUNCTION_MENU_CONTROLLER + '"_ustr', self.source())
        self.assertIn("    sc/source/ui/unoobj/funcmenucontroller \\\n", read("sc/Library_sc.mk"))

    def test_the_base_class_is_exported_even_when_the_libraries_are_merged(self):
        # Release builds enable mergelibs (distro-configs): svt goes into the merged library, sc does
        # not, so libsclo links against the base class only if it is exported unconditionally.
        merged = read("solenv/gbuild/extensions/pre_MergedLibsList.mk")
        self.assertRegex(merged, r"(?m)^\s+svt \\$")
        self.assertNotRegex(merged, r"(?m)^\s+sc \\$")
        header = read("include/svtools/popupmenucontrollerbase.hxx")
        self.assertRegex(header, r"\bclass SVT_DLLPUBLIC PopupMenuControllerBase\b")
        self.assertNotRegex(header, r"UNLESS_MERGELIBS\(\s*SVT_DLLPUBLIC\s*\)\s*PopupMenuControllerBase")
        self.assertIn("#include <svtools/popupmenucontrollerbase.hxx>", self.source())

    def test_the_controller_derives_the_category_of_each_menu_from_its_command_as_designed(self):
        ids = self.category_ids()
        table = {m.group(1): m.group(2) for m in re.finditer(
            r'\{\s*u"\.uno:(\w+)",\s*(ID_FUNCTION_GRP_\w+|RECENTLY_USED)\s*\}', self.source())}
        found = {cmd: 0 if name == "RECENTLY_USED" else ids[name] for cmd, name in table.items()}
        expected = dict(DESIGN_CATEGORIES, **{cmd: cat for cmd, _label, cat in MORE_FUNCTIONS})
        self.assertEqual(expected, found)
        self.assertNotIn(0, ids.values())  # RECENTLY_USED cannot clash with a category

    def test_more_functions_lists_the_five_design_submenus_in_order_with_labels(self):
        match = re.search(r"MORE_FUNCTIONS_SUBMENUS\[\]\s*=\s*\{([^}]*)\}", self.source())
        self.assertIsNotNone(match)
        self.assertEqual([cmd for cmd, _l, _c in MORE_FUNCTIONS], re.findall(r'u"\.uno:(\w+)"', match.group(1)))
        self.assertIn('MORE_FUNCTIONS = u".uno:FormulasMoreFunctionsMenu"', self.source())
        labels = commands_xcu()
        for cmd, label, _cat in MORE_FUNCTIONS:
            self.assertEqual(label, labels[".uno:" + cmd], cmd)

    def test_every_function_item_inserts_the_function_by_name_from_the_all_category(self):
        # SID_INS_FUNCTION (cellsh1.cxx) looks the upper-case name up in category 0, all functions
        src = self.source()
        self.assertRegex(src, r'"\.uno:InsertFunction\?FunctionName:string="\s*\+\s*aName\s*\+\s*'
                              r'"&FunctionCategory:short=0"')
        self.assertIn('FUNCTION_DIALOG = u".uno:FunctionDialog"_ustr', src)

    def test_the_static_category_popups_are_gone(self):
        mk = read("sc/UIConfig_scalc.mk")
        for resource in STATIC_CATEGORY_POPUPS:
            self.assertFalse((POPUPMENU / (resource + ".xml")).exists(), resource)
            self.assertNotIn("popupmenu/" + resource + " ", mk, resource)
        self.assertNotIn("formulas_", read("officecfg/registry/data/org/openoffice/Office/UI/Controller.xcu")
                         .split("FormulasMoreFunctionsMenuPopup")[1].split("</node>")[0])


class AutoSumSplitTest(unittest.TestCase):
    """.uno:FormulasAutoSum mirrors .uno:AutoSum (state, execute, invalidation)."""

    SLOT, ORIGINAL = "FID_FORMULAS_AUTOSUM", "SID_AUTO_SUM"

    def test_the_slot_is_sid_new_slots_plus_15_in_the_gap_next_to_the_data_split_bodies(self):
        text = read("sc/inc/sc.hrc")
        self.assertRegex(text, r"#define\s+" + self.SLOT + r"\s+\(SID_NEW_SLOTS\+15\)")
        self.assertEqual(1, len(re.findall(r"SID_NEW_SLOTS\s*\+\s*15\b", text)))

    def test_the_slot_has_a_scalc_sdi_entry_with_the_originals_flags(self):
        sdi = read("sc/sdi/scalc.sdi")
        mine = re.search(r"SfxVoidItem FormulasAutoSum " + self.SLOT + r"\n\(\)\n\[(.*?)\n\]", sdi, re.S)
        orig = re.search(r"SfxVoidItem AutoSum " + self.ORIGINAL + r"\n\(.*?\)\n\[(.*?)\n\]", sdi, re.S)
        self.assertIsNotNone(mine)
        self.assertEqual(orig.group(1), mine.group(1))  # same flags, same group, same toolbox config
        self.assertIn("ToolBoxConfig = TRUE", mine.group(1))

    def test_the_slot_reuses_the_originals_execute_method_and_has_no_state_method(self):
        original = sdi_row("sc/sdi/cellsh.sdi", self.ORIGINAL)
        self.assertEqual("ExecMethod = ExecuteEdit;", original)
        self.assertEqual(original, sdi_row("sc/sdi/cellsh.sdi", self.SLOT))

    def test_the_slot_sits_in_the_same_interface_as_the_original_so_every_shell_treats_both_alike(self):
        # Neither slot has a state method: the dispatcher alone decides, from the shells that
        # declare the slot. Declared in the same sdi interface, both follow the same shells.
        text = read("sc/sdi/cellsh.sdi")
        a, b = text.index(self.ORIGINAL), text.index(self.SLOT)
        self.assertEqual(text[:a].count("interface "), text[:b].count("interface "))
        self.assertEqual(1, len(re.findall(r"\b" + self.ORIGINAL + r"\b", text)))
        for path in ROOT.glob("*/sdi/*.sdi"):
            if path.name in ("cellsh.sdi", "scalc.sdi"):
                continue
            body = path.read_text(encoding="utf-8", errors="replace")
            self.assertEqual(len(re.findall(r"\b" + self.ORIGINAL + r"\b", body)),
                             len(re.findall(r"\b" + self.SLOT + r"\b", body)), str(path))

    def test_execute_shares_the_originals_case(self):
        text = read("sc/source/ui/view/cellsh1.cxx")
        groups = [re.findall(r"case (\w+):", m.group(0))
                  for m in re.finditer(r"(?:\s*case \w+:\s*\n)+", text)]
        groups = [g_ for g_ in groups if self.ORIGINAL in g_]
        self.assertEqual(1, len(groups))
        self.assertIn(self.SLOT, groups[0])

    def test_every_source_that_names_the_original_names_the_body_as_often(self):
        # (nothing invalidates SID_AUTO_SUM today; the rule keeps it that way for the mirror)
        for path in list((ROOT / "sc").rglob("*.cxx")) + list((ROOT / "sc").rglob("*.hxx")):
            text = path.read_text(encoding="utf-8", errors="replace")
            # (the original's argument item is read by its id, SID_AUTO_SUM, in cellsh1.cxx: not a use)
            self.assertGreaterEqual(len(re.findall(r"case\s+" + self.SLOT + r"\b", text)),
                                    len(re.findall(r"case\s+" + self.ORIGINAL + r"\b", text)), str(path))
            self.assertGreaterEqual(len(re.findall(r"Invalidate[^;]*\b" + self.SLOT + r"\b", text)),
                                    len(re.findall(r"Invalidate[^;]*\b" + self.ORIGINAL + r"\b", text)),
                                    str(path))
        for path in (ROOT / "sc/source").rglob("*.cxx"):
            text = path.read_text(encoding="utf-8", errors="replace")
            n_orig = len(re.findall(r"Invalidate\s*\(\s*" + self.ORIGINAL + r"\b", text))
            n_new = len(re.findall(r"Invalidate\s*\(\s*" + self.SLOT + r"\b", text))
            self.assertGreaterEqual(n_new, n_orig, f"{self.SLOT} not mirrored in {path}")

    def test_the_slot_is_a_functional_slot_not_a_placeholder(self):
        self.assertNotIn(self.SLOT, [e["slot"] for e in placeholders.load_all()])
        self.assertNotIn("FormulasAutoSum", [e["command"] for e in placeholders.load_all()])


if __name__ == "__main__":
    unittest.main()

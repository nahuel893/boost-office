#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Generate a notebookbar tab page from a JSON layout and splice it into a .ui file.

Only the children of the tab page box are rewritten. Every other line of the
.ui file stays byte-identical, so the file can still be diffed against the
upstream notebookbar.ui it was copied from.

Toolboxes in a column fill rows from the top. A toolbox may set "row" to start
lower (the next ones follow it) and "valign" (fill/start/center/end) to sit at
one edge of its row, e.g. a combo box at the bottom of a section.

VclGrid drops a row in which no toolbox starts, and a large toolbox expands the
rows it spans. So in a section with a large toolbox and a row no toolbox starts
in, a column of two small toolboxes would spread over the whole height. There
each column of small toolboxes becomes one vertical box at the top of the
section ("col" + prefix + section + column index), its toolboxes as far apart
as the grid's rows: Word keeps two small buttons in the top two rows.

A section may also have a "footer": one toolbox (same schema, but no "row")
that spans every column on the last row above the caption. Large and medium
toolboxes then span one row fewer, and column toolboxes must fit in the rows above it.

A toolbox may set "expand": true to take the width the page leaves free, like Word's Styles
gallery. That width is not part of the page's natural width, so the toolbox gives it back before
any group collapses when the window narrows (PriorityMergedHBox collapses groups only once the
page is narrower than their natural widths). VCL hands extra width only to a child that expands
itself, so the section's optional box, both grids and the toolbox get hexpand, and the items get
the packing expand (ToolBox::Resize shares the extra width out across them).

An item's "office_label" (Word's or Excel's label) becomes its button's label, unless LibreOffice
already shows that text for the command; an explicit "label" wins. Only the ribbon changes: menus,
help and tooltips keep reading the command's own label from <App>Commands.xcu.
"""
import argparse
import functools
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple
from xml.sax.saxutils import escape

# style -> (toolbar-style, icon_size); icon_size 5 = 32 px, 3 = 24 px, 1 = 16 px
# (sfx2/source/sidebar/SidebarToolBox.cxx:318-327)
STYLES = {
    "large": ("both", 5),
    "medium": ("both", 3),
    "small": ("icons", 1),
    "small-label": ("both-horiz", 1),
}
BUTTON_CLASS = {"button": "GtkToolButton", "split": "GtkMenuToolButton"}
SUPPRESSED_CLASSES = ("GtkToolButton", "GtkMenuToolButton")
# Styles that fill the section height: alone in their column, label below.
LARGE_LIKE = ("large", "medium")
INDENT = "  "
ROOT = Path(__file__).resolve().parents[2]
OBJECT_OPEN = re.compile(r"<object\b")
COMMANDS_DIR = "officecfg/registry/data/org/openoffice/Office/UI"
GENERIC_COMMANDS = "GenericCommands.xcu"
OOR = "{http://openoffice.org/2001/registry}"


class App(NamedTuple):
    """The files of one app's ribbon. Paths are relative to the source tree, file names to product/ui."""
    upstream: str  # the stock notebookbar.ui, never written
    office: str  # notebookbar_office.ui: upstream + tab operations + every generated page
    suppr: str  # gla11y suppressions, kept in sync with the office .ui
    false: str | None  # gla11y false positives, kept in sync too; None: no line for the office .ui
    prefix: str  # the page layouts are product/ui/<prefix>_<tab>.json
    tabs: str  # the tab operations
    context: str  # the translation context of the app's page layouts
    commands: str  # the app's own command labels in COMMANDS_DIR, read before GENERIC_COMMANDS


APPS = {
    "calc": App("sc/uiconfig/scalc/ui/notebookbar.ui", "sc/uiconfig/scalc/ui/notebookbar_office.ui",
                "solenv/sanitizers/ui/modules/scalc.suppr", None, "calc", "calc_tabs.json",
                "TabbedCalc", "CalcCommands.xcu"),
    "writer": App("sw/uiconfig/swriter/ui/notebookbar.ui", "sw/uiconfig/swriter/ui/notebookbar_office.ui",
                  "solenv/sanitizers/ui/modules/swriter.suppr", "solenv/sanitizers/ui/modules/swriter.false",
                  "writer", "writer_tabs.json", "TabbedWriter", "WriterCommands.xcu"),
}


class LayoutError(ValueError):
    pass


def item_url(item):
    """The command URL of a layout item: its "action", else .uno:<cmd>."""
    return item.get("action", ".uno:" + item["cmd"])


def item_command(item):
    """The base command of a layout item: its URL without the "?Arg:type=value" part."""
    return item_url(item).split("?", 1)[0]


@functools.cache
def shown_labels(root, app):
    """Command URL -> the text a ribbon button of the app shows for it when the .ui sets no label.

    That is the command's "Name": its Label without trailing dots and "~" (framework's
    uicommanddescription.cxx). The app's own file wins over the generic one, node by node, and a URL
    with arguments is a node of its own (vcl's CommandInfoProvider has no fallback to the base command).
    """
    found = {}
    for file in (APPS[app].commands, GENERIC_COMMANDS):
        here = {}
        for node in ET.parse(Path(root) / COMMANDS_DIR / file).iter("node"):
            name = node.get(OOR + "name")
            if name and name.startswith(".uno:") and name not in here:
                label = next((p.findtext("value") or "" for p in node.findall("prop")
                              if p.get(OOR + "name") == "Label"), "")
                here[name] = label.rstrip(".").replace("~", "")
        for name, label in here.items():
            found.setdefault(name, label)
    return found


def app_of(layout):
    """The app a page layout belongs to, by its translation context."""
    for name, spec in APPS.items():
        if spec.context == layout.get("context"):
            return name
    raise LayoutError(f"no app has the context {layout.get('context')!r}")


def item_label(layout, item, root=ROOT):
    """The label property of an item's button, or None to keep the command's own label.

    An explicit "label" wins. Otherwise the "office_label", unless LibreOffice already shows that
    text for the command (a placeholder's command label is already its Office label).
    """
    if "label" in item:
        return item["label"]
    office = item.get("office_label")
    if office is None or office == shown_labels(str(root), app_of(layout)).get(item_url(item)):
        return None
    return office


def boxes_of(section):
    """Every toolbox of a section: the column ones, then the footer if any."""
    for column in section["columns"]:
        yield from column
    if "footer" in section:
        yield section["footer"]


def ids_of(layout):
    """Yield every widget id the layout creates, in document order."""
    p = layout["id_prefix"]
    yield "pmhb" + p
    for section in layout["sections"]:
        name = section["name"]
        yield from ("ob" + p + name, "gd" + p + name, "gc" + p + name, "lb" + p + name)
        for col in stacked_columns(section):
            yield f"col{p}{name}{col}"
        for box in boxes_of(section):
            yield "bx" + p + box["id"]
            for item in box["items"]:
                yield "btn" + p + item["cmd"]


def rows_of(column):
    """Row of each toolbox: an explicit "row", else the row after the previous one."""
    rows, row = [], -1
    for box in column:
        row = box.get("row", row + 1)
        rows.append(row)
    return rows


def is_large_column(column):
    return any(box["style"] in LARGE_LIKE for box in column)


def stacked_columns(section):
    """Indexes of the columns of small toolboxes that become one vertical box at the section's top.

    Only in a section with a large toolbox, which expands the rows it spans, and a row in which no
    toolbox starts, which VclGrid drops: the rows left then share the whole height, and a column of
    two small toolboxes would spread over it (W7b). Elsewhere every column stays in the grid.
    """
    rows = section["rows"] - ("footer" in section)
    starts = set()
    for column in section["columns"]:
        starts.update([0] if is_large_column(column) else rows_of(column))
    columns = section["columns"]
    if not any(is_large_column(c) for c in columns) or starts >= set(range(rows)):
        return []
    return [col for col, column in enumerate(columns) if not is_large_column(column)]


def validate(layout):
    seen = set()
    for wid in ids_of(layout):
        if wid in seen:
            raise LayoutError(f"duplicate id {wid}")
        seen.add(wid)
    for section in layout["sections"]:
        name, rows = section["name"], section["rows"]
        footer = section.get("footer")
        if footer is not None:
            if "row" in footer:
                raise LayoutError(f"{name}: the footer cannot set a row")
            if rows < 2:
                raise LayoutError(f"{name}: a footer needs at least 2 rows")
            rows -= 1  # column toolboxes only get the rows above the footer
        for column in section["columns"]:
            styles = [box["style"] for box in column]
            for style in styles:
                if style not in STYLES:
                    raise LayoutError(f"{name}: unknown style {style}")
            if any(style in LARGE_LIKE for style in styles) and len(column) != 1:
                raise LayoutError(f"{name}: a large or medium toolbox must be alone in its column")
            if len(column) > rows:
                raise LayoutError(f"{name}: {len(column)} toolboxes in a column of {rows} rows")
            placed = rows_of(column)
            if placed != sorted(set(placed)) or any(not 0 <= r < rows for r in placed):
                raise LayoutError(f"{name}: toolbox rows {placed} do not fit {rows} rows in order")
        for col in stacked_columns(section):
            placed = rows_of(section["columns"][col])
            if placed != list(range(len(placed))):
                raise LayoutError(f"{name}: column {col} is stacked at the top, so its rows "
                                  f"{placed} must be {list(range(len(placed)))}")
        for box in boxes_of(section):
            if box is footer and box["style"] not in set(STYLES) - set(LARGE_LIKE):
                raise LayoutError(f"{name}: the footer must be a small toolbox")
            if box.get("valign", "fill") not in ("fill", "start", "center", "end"):
                raise LayoutError(f"{name}: unknown valign {box['valign']}")
            if not isinstance(box.get("expand", False), bool):
                raise LayoutError(f"{name}: expand must be true or false, not {box['expand']!r}")
            for item in box["items"]:
                if item.get("kind", "button") not in BUTTON_CLASS:
                    raise LayoutError(f"{name}: unknown kind {item.get('kind')}")


class Writer:
    def __init__(self):
        self.lines = []
        self.level = 0

    def line(self, text):
        self.lines.append(INDENT * self.level + text)

    def open(self, text):
        self.line(text)
        self.level += 1

    def close(self, text):
        self.level -= 1
        self.line(text)

    def prop(self, name, value, extra=""):
        self.line(f'<property name="{name}"{extra}>{escape(str(value))}</property>')

    def packing(self, **props):
        self.open("<packing>")
        for name, value in props.items():
            self.prop(name.replace("_", "-"), value)
        self.close("</packing>")


def emit_item(w, layout, box_style, item, expand=False, root=ROOT):
    p, ctx = layout["id_prefix"], layout["context"]
    kind = item.get("kind", "button")
    wid = f"btn{p}{item['cmd']}"
    w.open("<child>")
    w.open(f'<object class="{BUTTON_CLASS[kind]}" id="{wid}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    label = item_label(layout, item, root)
    if label is not None:
        w.prop("label", label, f' translatable="yes" context="{ctx}|{wid}"')
    w.prop("action-name", item_url(item))
    if "icon" in item:
        w.prop("icon_name", item["icon"])
    w.close("</object>")
    homogeneous = "False" if box_style in LARGE_LIKE or kind == "split" else "True"
    w.packing(expand=str(expand), homogeneous=homogeneous)
    w.close("</child>")


def emit_box(w, layout, box, col, row, large_rows, width=1, root=ROOT, packing=None):
    """A toolbox in the section's content grid, or with packing (a dict) in another container."""
    p = layout["id_prefix"]
    toolbar_style, icon_size = STYLES[box["style"]]
    large = box["style"] in LARGE_LIKE
    w.open("<child>")
    w.open(f'<object class="sfxlo-NotebookbarToolBox" id="bx{p}{box["id"]}">')
    w.prop("visible", "True")
    w.prop("can-focus", "True")
    if box.get("expand"):
        w.prop("hexpand", "True")
    if large:
        w.prop("valign", box.get("valign", "center"))
        w.prop("vexpand", "True")
    elif "valign" in box:
        w.prop("valign", box["valign"])
    w.prop("toolbar-style", toolbar_style)
    w.prop("show-arrow", "False")
    w.prop("icon_size", icon_size)
    for item in box["items"]:
        emit_item(w, layout, box["style"], item, box.get("expand", False), root)
    w.close("</object>")
    if packing is not None:
        w.packing(**packing)
    elif large:
        w.packing(left_attach=col, top_attach=0, height=large_rows)
    elif width > 1:
        w.packing(left_attach=col, top_attach=row, width=width)
    else:
        w.packing(left_attach=col, top_attach=row)
    w.close("</child>")


def emit_stack(w, layout, section, col, large_rows, root=ROOT):
    """A column of small toolboxes as one vertical box at the top of the section (stacked_columns).

    Its spacing is the content grid's row spacing, so its toolboxes sit where the grid's rows put
    the toolboxes of a column that uses every row."""
    p, column = layout["id_prefix"], section["columns"][col]
    w.open("<child>")
    w.open(f'<object class="GtkBox" id="col{p}{section["name"]}{col}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    if any(box.get("expand") for box in column):
        w.prop("hexpand", "True")
    w.prop("valign", "start")
    w.prop("orientation", "vertical")
    w.prop("spacing", 3)
    for position, box in enumerate(column):
        emit_box(w, layout, box, col, position, large_rows, root=root,
                 packing={"expand": "False", "fill": "True", "position": position})
    w.close("</object>")
    w.packing(left_attach=col, top_attach=0, height=large_rows)
    w.close("</child>")


def emit_section(w, layout, section, position, priority, root=ROOT):
    """A section: its grid holds the toolboxes' grid, the caption under it and the separator.

    The page box fills the page, so every section is as tall as the tallest page. The toolboxes'
    grid is the only child that expands vertically: it takes all the extra height and the caption
    ends on the section's bottom edge, on every section of every page. (VclGrid splits extra
    height evenly between expanding rows and drops the remainder, so a caption under several
    expanding rows ended up to 3 px higher than its neighbours.)
    """
    p, ctx, name = layout["id_prefix"], layout["context"], section["name"]
    rows, ncols = section["rows"], len(section["columns"])
    expand = any(box.get("expand") for box in boxes_of(section))
    w.open("<child>")
    w.open(f'<object class="VclOptionalBox" id="ob{p}{name}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    if expand:
        w.prop("hexpand", "True")
    w.open("<child>")
    w.line("<!-- n-columns=2 n-rows=2 -->")
    w.open(f'<object class="GtkGrid" id="gd{p}{name}">')
    for prop_name, value in (("visible", "True"), ("can-focus", "False"),
                             ("margin-start", 6), ("margin-end", 3), ("margin-top", 6),
                             ("margin-bottom", 6), ("row-spacing", 3), ("column-spacing", 3)):
        w.prop(prop_name, value)
    if expand:
        w.prop("hexpand", "True")
    w.open("<child>")
    w.line(f"<!-- n-columns={ncols} n-rows={rows} -->")
    w.open(f'<object class="GtkGrid" id="gc{p}{name}">')
    for prop_name, value in (("visible", "True"), ("can-focus", "False"), ("vexpand", "True"),
                             ("row-spacing", 3), ("column-spacing", 3)):
        w.prop(prop_name, value)
    if expand:
        w.prop("hexpand", "True")
    stacked = stacked_columns(section)
    for col, column in enumerate(section["columns"]):
        if col in stacked:
            emit_stack(w, layout, section, col, rows - ("footer" in section), root)
            continue
        for row, box in zip(rows_of(column), column):
            emit_box(w, layout, box, col, row, rows - ("footer" in section), root=root)
    if "footer" in section:
        emit_box(w, layout, section["footer"], 0, rows - 1, rows - 1, ncols, root)
    w.close("</object>")
    w.packing(left_attach=0, top_attach=0)
    w.close("</child>")
    w.open("<child>")
    w.open(f'<object class="GtkLabel" id="lb{p}{name}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("valign", "end")
    w.prop("label", section["caption"], f' translatable="yes" context="{ctx}|label{p}{name}"')
    w.open("<attributes>")
    w.line('<attribute name="scale" value="0.9"/>')
    w.close("</attributes>")
    w.close("</object>")
    w.packing(left_attach=0, top_attach=1)
    w.close("</child>")
    w.open("<child>")
    w.open('<object class="GtkSeparator">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("orientation", "vertical")
    w.close("</object>")
    w.packing(left_attach=1, top_attach=0, height=2)
    w.close("</child>")
    w.open("<accessibility>")
    w.line(f'<relation type="labelled-by" target="lb{p}{name}"/>')
    w.close("</accessibility>")
    w.close("</object>")
    w.packing(expand="False", fill="True", position=0)
    w.close("</child>")
    w.open("<style>")
    w.line(f'<class name="priority-{priority}"/>')
    w.close("</style>")
    w.close("</object>")
    w.packing(expand="False", fill="True", position=position)
    w.close("</child>")


def emit_page(layout, root=ROOT):
    validate(layout)
    p = layout["id_prefix"]
    sections = layout["sections"]
    w = Writer()
    w.open("<child>")
    w.open(f'<object class="sfxlo-PriorityMergedHBox" id="pmhb{p}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("valign", "fill")  # the tab page is as tall as the tallest page: so is every section
    for position, section in enumerate(sections):
        # The leftmost section has the highest priority, so it collapses last.
        emit_section(w, layout, section, position, len(sections) - position, root)
    w.close("</object>")
    w.packing(expand="True", fill="True", position=0)
    w.close("</child>")
    return w.lines


def find_object(lines, obj_id):
    """Return (first, last) line indexes, inclusive, of the <object> with this id."""
    marker = f'id="{obj_id}"'
    first = next((i for i, text in enumerate(lines) if "<object" in text and marker in text), None)
    if first is None:
        raise LayoutError(f"object {obj_id!r} not found")
    depth = 0
    for i in range(first, len(lines)):
        depth += len(OBJECT_OPEN.findall(lines[i])) - lines[i].count("</object>")
        if depth == 0:
            return first, i
    raise LayoutError(f"object {obj_id!r} is not closed")


def splice(ui_text, layout, generated):
    tab = layout["id_prefix"]
    begin, end = f"<!-- product:{tab}-begin -->", f"<!-- product:{tab}-end -->"
    lines = ui_text.split("\n")
    if any(begin in text for text in lines):
        first = next(i for i, text in enumerate(lines) if begin in text)
        last = next(i for i, text in enumerate(lines) if end in text)
    else:
        start, stop = find_object(lines, layout["page"])
        first = next((i for i in range(start + 1, stop) if lines[i].lstrip().startswith("<child")), None)
        if first is None or lines[stop - 1].strip() != "</child>":
            raise LayoutError(f"{layout['page']} must end with its <child> elements")
        last = stop - 1
    indent = lines[first][: len(lines[first]) - len(lines[first].lstrip())]
    lines[first:last + 1] = [indent + begin] + [indent + text for text in generated] + [indent + end]
    for obj_id in layout.get("remove_objects", []):
        try:
            a, b = find_object(lines, obj_id)
        except LayoutError:
            continue
        del lines[a:b + 1]
    return "\n".join(lines)


def child_span(lines, obj_id):
    """(first, last) line indexes, inclusive, of the <child> element that wraps this object."""
    first, last = find_object(lines, obj_id)
    start = first - 1
    if not lines[start].lstrip().startswith("<child"):
        raise LayoutError(f"object {obj_id!r} is not wrapped in a <child>")
    indent = lines[start][: len(lines[start]) - len(lines[start].lstrip())]
    end = next(i for i in range(last + 1, len(lines)) if lines[i] == indent + "</child>")
    return start, end


def set_position(lines, obj_id, position):
    """Set the packing "position" of the <child> that wraps this object (its own, not nested)."""
    start, end = child_span(lines, obj_id)
    indent = lines[start][: len(lines[start]) - len(lines[start].lstrip())] + INDENT * 2
    wanted = indent + '<property name="position">'
    for i in range(end - 1, start, -1):
        if lines[i].startswith(wanted):
            lines[i] = f'{wanted}{position}</property>'
            return
    raise LayoutError(f"{obj_id!r} has no packing position")


def relabel(lines, obj_id, old, new):
    """Change the text of a label. Already changed counts as done, so the operation can be re-run."""
    first, last = find_object(lines, obj_id)
    for i in range(first, last + 1):
        if '<property name="label"' in lines[i]:
            if f">{escape(new)}</property>" in lines[i]:
                return
            if f">{escape(old)}</property>" not in lines[i]:
                raise LayoutError(f"{obj_id!r} reads neither {old!r} nor {new!r}")
            lines[i] = lines[i].replace(f">{escape(old)}</property>", f">{escape(new)}</property>")
            return
    raise LayoutError(f"{obj_id!r} has no label")


def set_property(lines, obj_id, name, old, new):
    """Change one of an object's own properties (not a nested object's). Already changed counts
    as done, so the operation can be re-run."""
    first, last = find_object(lines, obj_id)
    indent = lines[first][: len(lines[first]) - len(lines[first].lstrip())] + INDENT
    prefix = f'{indent}<property name="{name}">'
    for i in range(first + 1, last):
        if lines[i].startswith(prefix):
            if lines[i] == f"{prefix}{escape(new)}</property>":
                return
            if lines[i] != f"{prefix}{escape(old)}</property>":
                raise LayoutError(f"{obj_id!r} {name} is neither {old!r} nor {new!r}")
            lines[i] = f"{prefix}{escape(new)}</property>"
            return
    raise LayoutError(f"{obj_id!r} has no {name} property")


ITALIC = '<attribute name="style" value="italic"/>'


def plain_captions(lines):
    """Drop the italic style of every label's attributes: LibreOffice's stock pages (File, Tools,
    Extension, the contextual tabs) set their section captions in italic, the generated sections
    use the plain 0.9 scale. One default for every app, so every page of the ribbon reads as one
    design, as in Office. Already plain counts as done, so the operation can be re-run."""
    return [line for line in lines if line.strip() != ITALIC]


def move_pair_before(lines, page, tab, before):
    """Move a tab page and its tab label (adjacent children) in front of another page."""
    a, b = child_span(lines, page)[0], child_span(lines, tab)[1]
    target = child_span(lines, before)[0]
    if a < target:
        return  # already in front
    block = lines[a:b + 1]
    del lines[a:b + 1]
    lines[target:target] = block


def page_lines(add, tab_indent):
    """The lines of a new, empty tab page and its tab label; Home/Data-style markers inside."""
    prefix = add["prefix"]
    w = Writer()
    w.level = 0
    w.open("<child>")
    w.open(f'<object class="sfxlo-PriorityHBox" id="{add["page"]}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("spacing", 6)
    w.line(f"<!-- product:{prefix}-begin -->")
    w.lines += [INDENT * w.level + text for text in emit_page({"id_prefix": prefix, "sections": []})]
    w.line(f"<!-- product:{prefix}-end -->")
    w.close("</object>")
    w.packing(position=add["position"])
    w.close("</child>")
    w.open('<child type="tab">')
    w.open(f'<object class="GtkLabel" id="{add["tab_id"]}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("label", add["label"], f' translatable="yes" context="{add["context"]}"')
    w.prop("use-underline", "True")
    w.close("</object>")
    w.packing(position=add["position"], tab_fill="False")
    w.close("</child>")
    return [tab_indent + text for text in w.lines]


def apply_tabs(ui_text, tabs):
    """Apply the tab operations of an app's tabs file (calc_tabs.json, ...): relabel, page
    properties, move, positions, add pages. Every app first gets plain captions on its stock pages.

    Each operation can be applied twice. Run it on the upstream notebookbar.ui, before the
    generated pages are spliced in.
    """
    lines = plain_captions(ui_text.split("\n"))
    for op in tabs.get("relabel", []):
        relabel(lines, op["id"], op["from"], op["to"])
    for op in tabs.get("properties", []):
        set_property(lines, op["id"], op["name"], op["from"], op["to"])
    for op in tabs.get("move", []):
        move_pair_before(lines, op["page"], op["tab"], op["before"])
    for obj_id, position in tabs.get("positions", {}).items():
        set_position(lines, obj_id, position)
    for add in tabs.get("add_pages", []):
        if any(f'id="{add["page"]}"' in text for text in lines):
            continue
        _, end = child_span(lines, add["after_tab"])
        indent = lines[end][: len(lines[end]) - len(lines[end].lstrip())]
        lines[end + 1:end + 1] = page_lines(add, indent)
    return "\n".join(lines)


def page_layouts(ui_dir, app="calc"):
    """Every page layout <prefix>_<tab>.json of an app, in file-name order (its tabs file is not one)."""
    spec = APPS[app]
    return [json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(Path(ui_dir).glob(spec.prefix + "_*.json")) if path.name != spec.tabs]


def regenerate_all(upstream_text, tabs, layouts, root=ROOT):
    """The office .ui: the upstream one, the tab operations, then every generated page spliced in.
    The command labels come from the source tree at root."""
    text = apply_tabs(upstream_text, tabs)
    for layout in layouts:
        text = splice(text, layout, emit_page(layout, root))
    return text


def kept_lines(text, ui_rel_path, ui_text):
    """The lines of a gla11y file without the .ui's duplicates and the lines whose id is gone from
    the .ui; other files' lines stay as they are. Returns the lines and the .ui's lines kept."""
    present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', ui_text))
    prefix = ui_rel_path + ":"
    id_in_line = re.compile(r"@id='([^']+)'")
    out, existing = [], set()
    for line in text.splitlines():
        if line.startswith(prefix):
            match = id_in_line.search(line)
            if match and match.group(1) not in present:
                continue
            if line in existing:
                continue
            existing.add(line)
        out.append(line)
    return out, existing


def sync_suppr(suppr_text, ui_rel_path, ui_text):
    """Drop suppressions for ids gone from the .ui; add button-no-label for new tool buttons."""
    prefix = ui_rel_path + ":"
    out, existing = kept_lines(suppr_text, ui_rel_path, ui_text)
    for cls, wid in re.findall(r'<object class="(GtkToolButton|GtkMenuToolButton)" id="([^"]+)"', ui_text):
        line = f"{prefix}//{cls}[@id='{wid}'] button-no-label"
        if line not in existing:
            out.append(line)
            existing.add(line)
    return "\n".join(out) + "\n"


def sync_false(false_text, ui_rel_path, ui_text):
    """Drop false positives for ids gone from the .ui. New widgets get suppressions, not these."""
    return "\n".join(kept_lines(false_text, ui_rel_path, ui_text)[0]) + "\n"


def regenerate_app(root, name):
    """Rebuild an app's notebookbar_office.ui from its upstream .ui, tabs file and page layouts,
    then bring its suppressions (and false positives, if it has them) in line with it."""
    root, spec = Path(root), APPS[name]
    ui_dir = root / "product/ui"
    layouts = page_layouts(ui_dir, name)
    text = regenerate_all((root / spec.upstream).read_text(encoding="utf-8"),
                          json.loads((ui_dir / spec.tabs).read_text(encoding="utf-8")), layouts, root)
    (root / spec.office).write_text(text, encoding="utf-8")
    for rel, sync in ((spec.suppr, sync_suppr), (spec.false, sync_false)):
        if rel:
            path = root / rel
            path.write_text(sync(path.read_text(encoding="utf-8"), spec.office, text), encoding="utf-8")
    print(f"{spec.office}: {len(layouts)} generated pages")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    whole = ap.add_mutually_exclusive_group()
    whole.add_argument("--all", action="store_true",
                       help="rebuild every app's office .ui from upstream: tab operations, then every page")
    whole.add_argument("--app", choices=APPS, help="rebuild one app's office .ui the same way")
    ap.add_argument("--root", type=Path, default=ROOT, help="with --all or --app: the source tree (default: this one)")
    ap.add_argument("--layout", type=Path)
    ap.add_argument("--ui", help="repository-relative path of the .ui file")
    ap.add_argument("--suppr", type=Path)
    ap.add_argument("--tabs", type=Path, help="<app>_tabs.json: apply the tab order, label and page operations first")
    args = ap.parse_args(argv)
    if args.all or args.app:
        for name in APPS if args.all else [args.app]:
            regenerate_app(args.root, name)
        return 0
    if not (args.layout and args.ui and args.suppr):
        ap.error("--layout, --ui and --suppr are required without --all or --app")
    layout = json.loads(args.layout.read_text(encoding="utf-8"))
    ui_path = Path(args.ui)
    ui_text = ui_path.read_text(encoding="utf-8")
    if args.tabs:
        ui_text = apply_tabs(ui_text, json.loads(args.tabs.read_text(encoding="utf-8")))
    ui_text = splice(ui_text, layout, emit_page(layout))
    ui_path.write_text(ui_text, encoding="utf-8")
    args.suppr.write_text(sync_suppr(args.suppr.read_text(encoding="utf-8"), args.ui, ui_text),
                          encoding="utf-8")
    print(f"{args.ui}: {len(list(ids_of(layout)))} generated ids")
    return 0


if __name__ == "__main__":
    sys.exit(main())

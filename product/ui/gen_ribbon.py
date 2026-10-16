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

A section may also have a "footer": one toolbox (same schema, but no "row")
that spans every column on the last row above the caption. Large and medium
toolboxes then span one row fewer, and column toolboxes must fit in the rows above it.
"""
import argparse
import json
import re
import sys
from pathlib import Path
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
OBJECT_OPEN = re.compile(r"<object\b")


class LayoutError(ValueError):
    pass


def item_url(item):
    """The command URL of a layout item: its "action", else .uno:<cmd>."""
    return item.get("action", ".uno:" + item["cmd"])


def item_command(item):
    """The base command of a layout item: its URL without the "?Arg:type=value" part."""
    return item_url(item).split("?", 1)[0]


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
        yield from ("ob" + p + name, "gd" + p + name, "lb" + p + name)
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
        for box in boxes_of(section):
            if box is footer and box["style"] not in set(STYLES) - set(LARGE_LIKE):
                raise LayoutError(f"{name}: the footer must be a small toolbox")
            if box.get("valign", "fill") not in ("fill", "start", "center", "end"):
                raise LayoutError(f"{name}: unknown valign {box['valign']}")
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


def emit_item(w, layout, box_style, item):
    p, ctx = layout["id_prefix"], layout["context"]
    kind = item.get("kind", "button")
    wid = f"btn{p}{item['cmd']}"
    w.open("<child>")
    w.open(f'<object class="{BUTTON_CLASS[kind]}" id="{wid}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    if "label" in item:
        w.prop("label", item["label"], f' translatable="yes" context="{ctx}|{wid}"')
    w.prop("action-name", item_url(item))
    if "icon" in item:
        w.prop("icon_name", item["icon"])
    w.close("</object>")
    homogeneous = "False" if box_style in LARGE_LIKE or kind == "split" else "True"
    w.packing(expand="False", homogeneous=homogeneous)
    w.close("</child>")


def emit_box(w, layout, box, col, row, large_rows, width=1):
    p = layout["id_prefix"]
    toolbar_style, icon_size = STYLES[box["style"]]
    large = box["style"] in LARGE_LIKE
    w.open("<child>")
    w.open(f'<object class="sfxlo-NotebookbarToolBox" id="bx{p}{box["id"]}">')
    w.prop("visible", "True")
    w.prop("can-focus", "True")
    if large:
        w.prop("valign", box.get("valign", "center"))
        w.prop("vexpand", "True")
    elif "valign" in box:
        w.prop("valign", box["valign"])
    w.prop("toolbar-style", toolbar_style)
    w.prop("show-arrow", "False")
    w.prop("icon_size", icon_size)
    for item in box["items"]:
        emit_item(w, layout, box["style"], item)
    w.close("</object>")
    if large:
        w.packing(left_attach=col, top_attach=0, height=large_rows)
    elif width > 1:
        w.packing(left_attach=col, top_attach=row, width=width)
    else:
        w.packing(left_attach=col, top_attach=row)
    w.close("</child>")


def emit_section(w, layout, section, position, priority):
    p, ctx, name = layout["id_prefix"], layout["context"], section["name"]
    rows, ncols = section["rows"], len(section["columns"])
    w.open("<child>")
    w.open(f'<object class="VclOptionalBox" id="ob{p}{name}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.open("<child>")
    w.line(f"<!-- n-columns={ncols + 1} n-rows={rows + 1} -->")
    w.open(f'<object class="GtkGrid" id="gd{p}{name}">')
    for prop_name, value in (("visible", "True"), ("can-focus", "False"),
                             ("margin-start", 6), ("margin-end", 3), ("margin-top", 6),
                             ("margin-bottom", 6), ("row-spacing", 3), ("column-spacing", 3)):
        w.prop(prop_name, value)
    w.open("<child>")
    w.open(f'<object class="GtkLabel" id="lb{p}{name}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("valign", "end")
    w.prop("vexpand", "True")
    w.prop("label", section["caption"], f' translatable="yes" context="{ctx}|label{p}{name}"')
    w.open("<attributes>")
    w.line('<attribute name="scale" value="0.9"/>')
    w.close("</attributes>")
    w.close("</object>")
    w.packing(left_attach=0, top_attach=rows, width=ncols)
    w.close("</child>")
    for col, column in enumerate(section["columns"]):
        for row, box in zip(rows_of(column), column):
            emit_box(w, layout, box, col, row, rows - ("footer" in section))
    if "footer" in section:
        emit_box(w, layout, section["footer"], 0, rows - 1, rows - 1, ncols)
    w.open("<child>")
    w.open('<object class="GtkSeparator">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("orientation", "vertical")
    w.close("</object>")
    w.packing(left_attach=ncols, top_attach=0, height=rows + 1)
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


def emit_page(layout):
    validate(layout)
    p = layout["id_prefix"]
    sections = layout["sections"]
    w = Writer()
    w.open("<child>")
    w.open(f'<object class="sfxlo-PriorityMergedHBox" id="pmhb{p}">')
    w.prop("visible", "True")
    w.prop("can-focus", "False")
    w.prop("valign", "center")
    for position, section in enumerate(sections):
        # The leftmost section has the highest priority, so it collapses last.
        emit_section(w, layout, section, position, len(sections) - position)
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


def sync_suppr(suppr_text, ui_rel_path, ui_text):
    """Drop suppressions for ids gone from the .ui; add button-no-label for new tool buttons."""
    present = set(re.findall(r'<object class="[^"]+" id="([^"]+)"', ui_text))
    prefix = ui_rel_path + ":"
    id_in_line = re.compile(r"@id='([^']+)'")
    out, existing = [], set()
    for line in suppr_text.splitlines():
        if line.startswith(prefix):
            match = id_in_line.search(line)
            if match and match.group(1) not in present:
                continue
            if line in existing:
                continue
            existing.add(line)
        out.append(line)
    for cls, wid in re.findall(r'<object class="(GtkToolButton|GtkMenuToolButton)" id="([^"]+)"', ui_text):
        line = f"{prefix}//{cls}[@id='{wid}'] button-no-label"
        if line not in existing:
            out.append(line)
            existing.add(line)
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--layout", required=True, type=Path)
    ap.add_argument("--ui", required=True, help="repository-relative path of the .ui file")
    ap.add_argument("--suppr", required=True, type=Path)
    args = ap.parse_args(argv)
    layout = json.loads(args.layout.read_text(encoding="utf-8"))
    ui_path = Path(args.ui)
    ui_text = splice(ui_path.read_text(encoding="utf-8"), layout, emit_page(layout))
    ui_path.write_text(ui_text, encoding="utf-8")
    args.suppr.write_text(sync_suppr(args.suppr.read_text(encoding="utf-8"), args.ui, ui_text),
                          encoding="utf-8")
    print(f"{args.ui}: {len(list(ids_of(layout)))} generated ids")
    return 0


if __name__ == "__main__":
    sys.exit(main())

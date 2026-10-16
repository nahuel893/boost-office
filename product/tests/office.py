# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Rebuild notebookbar_office.ui from upstream: tab operations, then every generated page."""
import json
from pathlib import Path

from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "sc/uiconfig/scalc/ui/notebookbar.ui"
OFFICE = ROOT / "sc/uiconfig/scalc/ui/notebookbar_office.ui"
UI_DIR = ROOT / "product/ui"
TABS = UI_DIR / "calc_tabs.json"


def page_layouts():
    """Every product/ui/calc_<tab>.json page layout (calc_tabs.json is not one)."""
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(UI_DIR.glob("calc_*.json")) if p != TABS]


def expected_office_ui():
    text = g.apply_tabs(UPSTREAM.read_text(encoding="utf-8"), json.loads(TABS.read_text(encoding="utf-8")))
    for layout in page_layouts():
        text = g.splice(text, layout, g.emit_page(layout))
    return text

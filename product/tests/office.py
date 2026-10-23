# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Rebuild an app's notebookbar_office.ui from upstream: tab operations, then every generated page.

app(name) gives the files of one app of gen_ribbon.APPS as absolute paths. UPSTREAM, OFFICE and
TABS are Calc's, kept for the Calc test modules.
"""
import json
from pathlib import Path
from types import SimpleNamespace

from product.ui import gen_ribbon as g

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "product/ui"


def app(name):
    """One app's ribbon files: upstream, office, suppr, false (None when the app has none), tabs."""
    spec = g.APPS[name]
    return SimpleNamespace(name=name, upstream=ROOT / spec.upstream, office=ROOT / spec.office,
                           suppr=ROOT / spec.suppr, false=ROOT / spec.false if spec.false else None,
                           tabs=UI_DIR / spec.tabs)


UPSTREAM, OFFICE, TABS = app("calc").upstream, app("calc").office, app("calc").tabs


def page_layouts(name="calc"):
    """Every product/ui/<app>_<tab>.json page layout (the app's tabs file is not one)."""
    return g.page_layouts(UI_DIR, name)


def expected_office_ui(name="calc"):
    """What `gen_ribbon.py --all` writes for an app: upstream + tab operations + every generated page."""
    files = app(name)
    return g.regenerate_all(files.upstream.read_text(encoding="utf-8"),
                            json.loads(files.tabs.read_text(encoding="utf-8")), page_layouts(name))


def office_labels(layout):
    """URL -> office_label of every ribbon item in one page layout that carries one."""
    return {g.item_url(i): i["office_label"] for s in layout["sections"] for b in g.boxes_of(s)
            for i in b["items"] if "office_label" in i}

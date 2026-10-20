# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The registry of ribbon placeholders, one file per app, read by every product test.

placeholders.json lists each placeholder slot once: slot name, SID_NEW_SLOTS offset, base
command, URL variants for a family slot ("Arg:type=value", one per button) and, once a tab
task has put its button on a page, the label. The UITests read the same JSON file.

To implement a placeholder, keep its entry here and add "implemented": true (see
product/docs/calc-data-redesign.md). load(), labelled(), labels_by_url() and all_urls() then leave
it out, so every "is a placeholder" check (disabled, inert, tooltip, always-disabled) skips it;
load_all() still lists every slot of the fork block, implemented or not.

Each app has its own registry file, given by registry(app); every function takes it as "path".
The default is Calc's, placeholders.json.
"""
import json
from pathlib import Path

REGISTRY = Path(__file__).with_name("placeholders.json")
REGISTRIES = {"calc": REGISTRY, "writer": REGISTRY.with_name("placeholders_writer.json")}


def registry(app):
    """The registry file of one app's placeholders."""
    return REGISTRIES[app]


def load_all(path=REGISTRY):
    """Every registry entry, implemented or not."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load(path=REGISTRY):
    """The placeholders: entries that are not flagged "implemented"."""
    return [e for e in load_all(path) if not e.get("implemented")]


def implemented(path=REGISTRY):
    return [e for e in load_all(path) if e.get("implemented")]


def urls(entry):
    """Every command URL the slot answers to: the base command, or one per variant."""
    base = ".uno:" + entry["command"]
    return [base + "?" + variant for variant in entry.get("variants", [])] or [base]


def all_urls(path=REGISTRY):
    """Every command URL of every placeholder (implemented entries excluded)."""
    return [url for entry in load(path) for url in urls(entry)]


def drop_implemented(table, path=REGISTRY):
    """A URL -> label table without the URLs of implemented entries (they are no placeholder)."""
    gone = {url for entry in implemented(path) for url in urls(entry)}
    return {url: label for url, label in table.items() if url not in gone}


def labelled(path=REGISTRY):
    """Placeholders whose button is already on a page: base command -> label."""
    return {e["command"]: e["label"] for e in load(path) if "label" in e}


def labels_by_url(path=REGISTRY):
    """Label of every placeholder button that is on a page: ".uno:Base[?Arg:type=value]" -> label.

    A plain slot has one "label"; a family slot has a "variant_labels" map, one label per variant.
    """
    out = {}
    for entry in load(path):
        base = ".uno:" + entry["command"]
        if "label" in entry:
            out[base] = entry["label"]
        for variant, label in entry.get("variant_labels", {}).items():
            out[base + "?" + variant] = label
    return out

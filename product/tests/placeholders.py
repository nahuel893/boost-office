# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The one registry of ribbon placeholders, read by every product test.

placeholders.json lists each placeholder slot once: slot name, SID_NEW_SLOTS offset, base
command, URL variants for a family slot ("Arg:type=value", one per button) and, once a tab
task has put its button on a page, the label. The UITests read the same JSON file.

To implement a placeholder, remove its entry here (see product/docs/calc-data-redesign.md).
"""
import json
from pathlib import Path

REGISTRY = Path(__file__).with_name("placeholders.json")


def load():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def urls(entry):
    """Every command URL the slot answers to: the base command, or one per variant."""
    base = ".uno:" + entry["command"]
    return [base + "?" + variant for variant in entry.get("variants", [])] or [base]


def labelled():
    """Placeholders whose button is already on a page: base command -> label."""
    return {e["command"]: e["label"] for e in load() if "label" in e}


def labels_by_url():
    """Label of every placeholder button that is on a page: ".uno:Base[?Arg:type=value]" -> label.

    A plain slot has one "label"; a family slot has a "variant_labels" map, one label per variant.
    """
    out = {}
    for entry in load():
        base = ".uno:" + entry["command"]
        if "label" in entry:
            out[base] = entry["label"]
        for variant, label in entry.get("variant_labels", {}).items():
            out[base + "?" + variant] = label
    return out

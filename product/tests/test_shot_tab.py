# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""product/dev/shot-tab.sh: argument handling, the tab list and the tab finder, without a build or a display."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "product/dev/shot-tab.sh"
TEXT = SCRIPT.read_text(encoding="utf-8")


def heredoc(marker_line):
    """The body of the python heredoc whose command line contains marker_line."""
    m = re.search(re.escape(marker_line) + r".*?<<'PYEOF'\n(.*?)\nPYEOF\n", TEXT, re.S)
    assert m, marker_line
    return m.group(1)


def run_python(body, *args):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "body.py"
        src.write_text(body, encoding="utf-8")
        return subprocess.run(["python3", "-I", str(src), *args], capture_output=True, text=True, timeout=60)


def tab_bar(path, width, labels, pill, x_first=212, label_w=40, gap=21):
    """A light tab bar: dark label blobs on y 19..28 and, under the selected tab, the pill's side
    strokes at y 33..36 (the part of the real active-tab pill that reaches the label rows' neighbourhood)."""
    im = Image.new("RGB", (width, 60), (235, 235, 235))
    d = ImageDraw.Draw(im)
    x, spans = x_first, []
    for label in labels:
        w = label_w + 5 * len(label.split()) - 5
        # a label is two ink words when it has a space, one otherwise
        for i, _word in enumerate(label.split()):
            wx = x + i * (label_w // 2 + 5)
            d.rectangle([wx, 19, wx + (label_w // 2 if " " in label else label_w) - 1, 28], fill=(20, 20, 20))
        spans.append((x, x + w))
        x += w + gap
    if pill is not None:
        l, r = spans[pill]
        d.rectangle([l - 8, 33, l - 7, 36], fill=(20, 20, 20))
        d.rectangle([r + 8, 33, r + 9, 36], fill=(20, 20, 20))
    im.save(path)
    return spans


class ShotTabArguments(unittest.TestCase):

    def run_script(self, *args):
        return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, timeout=30)

    def test_rejects_unknown_app(self):
        r = self.run_script("--app", "impress", "light", "Home", "/dev/null")
        self.assertEqual(2, r.returncode)
        self.assertIn("--app must be calc|writer", r.stderr)

    def test_rejects_unknown_theme(self):
        r = self.run_script("sepia", "Home", "/dev/null")
        self.assertEqual(2, r.returncode)
        self.assertIn("theme must be light or dark", r.stderr)

    def test_rejects_unknown_width(self):
        r = self.run_script("--app", "writer", "light", "Home", "/dev/null", "1280")
        self.assertEqual(2, r.returncode)
        self.assertIn("width: 1920|1600|1366", r.stderr)


class ShotTabTabList(unittest.TestCase):

    def test_default_lists(self):
        calc = re.search(r'^calc_tabs="(.*)"$', TEXT, re.M).group(1).split(",")
        writer = re.search(r'^writer_tabs="(.*)"$', TEXT, re.M).group(1).split(",")
        self.assertEqual(["File", "Home", "Insert", "Page Layout", "Formulas", "Data", "Review", "View",
                          "Extension", "Tools", "Help"], calc)
        self.assertEqual(["File", "Home", "Insert", "Design", "Layout", "References", "Mailings", "Review",
                          "View", "Extension", "Tools", "Help"], writer)

    def test_writer_filter_keeps_help(self):
        body = heredoc("tabs=$(python3 -I -")
        order = "File,Home,Insert,Design,Layout,References,Mailings,Review,View,Extension,Tools,Help"
        names = order.split(",")
        tabs = "".join(
            "<child type='tab'><object class='GtkBox'><property name='label'>%s</property></object></child>"
            % ("~" + n if n != "Help" else "H~elp") for n in names)
        with tempfile.TemporaryDirectory() as tmp:
            ui = Path(tmp) / "n.ui"
            ui.write_text("<interface><object id='ContextContainer'>%s</object></interface>" % tabs,
                          encoding="utf-8")
            r = run_python(body, str(ui), order)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual(order, r.stdout.strip())


class ShotTabFinder(unittest.TestCase):
    FINDER = heredoc("pos=$(python3 -I -")
    WRITER = "File,Home,Insert,Design,Layout,References,Mailings,Review,View,Extension,Tools,Help".split(",")

    def find(self, width, labels, pill, tab, x0=217):
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "bar.png"
            spans = tab_bar(png, width, labels, pill)
            r = run_python(self.FINDER, str(png), tab, ",".join(labels), str(x0))
        return r, spans

    def test_finds_every_writer_tab_at_1366_with_the_pill_under_home(self):
        for i, name in enumerate(self.WRITER):
            r, spans = self.find(1366, self.WRITER, 1, name)
            self.assertEqual(0, r.returncode, "%s: %s" % (name, r.stderr))
            x, y = map(int, r.stdout.split())
            left, right = spans[i]
            self.assertTrue(left <= x <= right, "%s: x=%d not in %s" % (name, x, spans[i]))
            self.assertEqual(25, y)

    def test_finds_help_when_it_is_selected(self):
        r, spans = self.find(1366, self.WRITER, 11, "Help")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertTrue(spans[11][0] <= int(r.stdout.split()[0]) <= spans[11][1])

    def test_two_word_label(self):
        calc = "File,Home,Insert,Page Layout,Formulas,Data,Review,View,Extension,Tools,Help".split(",")
        r, spans = self.find(1920, calc, 2, "Page Layout", x0=225)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertTrue(spans[3][0] <= int(r.stdout.split()[0]) <= spans[3][1])


class ShotTabClick(unittest.TestCase):

    def test_pointer_click_moves_before_it_presses(self):
        """A SHOT_AFTER click must enter the surface first: the client's click does two moves, then presses."""
        body = re.search(r'elif f\[0\] == "click":\n(.*?)\n    elif', TEXT, re.S).group(1)
        self.assertLessEqual(body.index("move("), body.index("button(True)"))
        self.assertGreaterEqual(body.count("move("), 2)


if __name__ == "__main__":
    unittest.main()

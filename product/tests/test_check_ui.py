# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""product/dev/check-ui.sh prints each file's own gla11y report, with a fake gla11y and lint-ui.py."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "product/dev/check-ui.sh"
# Writes "report of <file>" to the -o report, except for a file named bad.ui: then it fails
# before writing anything, as gla11y does when it cannot parse a file.
FAKE_GLA11Y = """import sys
args = sys.argv[1:]
ui = args[-1]
if ui.endswith("bad.ui"):
    sys.exit(1)
with open(args[args.index("-o") + 1], "w") as report:
    report.write("report of %s\\n" % ui)
"""


class CheckUiTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "product/dev").mkdir(parents=True)
        shutil.copy(SCRIPT, self.tmp / "product/dev/check-ui.sh")
        (self.tmp / "bin").mkdir()
        (self.tmp / "bin/gla11y").write_text(FAKE_GLA11Y, encoding="utf-8")
        (self.tmp / "bin/lint-ui.py").write_text("", encoding="utf-8")

    def run_script(self, *files):
        return subprocess.run(["bash", str(self.tmp / "product/dev/check-ui.sh"), *files],
                              capture_output=True, text=True, check=False, timeout=30)

    def test_a_failed_run_never_reprints_the_previous_report(self):
        good = "sc/uiconfig/scalc/ui/good.ui"
        out = self.run_script(good, "sw/uiconfig/swriter/ui/bad.ui")
        self.assertEqual(1, out.returncode)
        self.assertEqual(1, out.stdout.count("report of " + good), out.stdout)

    def test_each_file_prints_its_own_report(self):
        files = ["sc/uiconfig/scalc/ui/a.ui", "sw/uiconfig/swriter/ui/b.ui"]
        out = self.run_script(*files)
        self.assertEqual(0, out.returncode, out.stderr)
        for ui in files:
            self.assertEqual(1, out.stdout.count("report of " + ui), out.stdout)


if __name__ == "__main__":
    unittest.main()

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""product/dev/uitest.sh picks the UITest target and its log by app, with a fake lo-make.sh."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "product/dev/uitest.sh"
# Records its arguments, one call per line; fails when FAKE_MAKE_STATUS says so.
FAKE_MAKE = """#!/usr/bin/env bash
echo "$*" >> "$(dirname "$0")/make.log"
exit "${FAKE_MAKE_STATUS:-0}"
"""


class UitestScriptTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        dev = self.tmp / "product/dev"
        dev.mkdir(parents=True)
        shutil.copy(SCRIPT, dev / "uitest.sh")
        (dev / "lo-make.sh").write_text(FAKE_MAKE, encoding="utf-8")
        (dev / "lo-make.sh").chmod(0o755)
        for target in ("calc_tests", "writer_tests8"):
            log = self.tmp / "workdir/UITest" / target / "done.log"
            log.parent.mkdir(parents=True)
            log.write_text("log of %s\n" % target, encoding="utf-8")

    def run_script(self, *args, status=0):
        env = dict(os.environ, FAKE_MAKE_STATUS=str(status))
        return subprocess.run(["bash", str(self.tmp / "product/dev/uitest.sh"), *args],
                              capture_output=True, text=True, env=env, check=False, timeout=30)

    def make_calls(self):
        log = self.tmp / "product/dev/make.log"
        return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    def test_without_app_it_runs_calc(self):
        out = self.run_script("notebookbarOffice.NotebookbarOffice.test_a", "m.C.test_b")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertEqual(["UITest_calc_tests UITEST_TEST_NAME=notebookbarOffice.NotebookbarOffice.test_a",
                          "UITest_calc_tests UITEST_TEST_NAME=m.C.test_b"], self.make_calls())

    def test_app_writer_runs_writer_tests8(self):
        out = self.run_script("--app", "writer", "notebookbarOffice.NotebookbarOffice.test_a")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertEqual(["UITest_writer_tests8 UITEST_TEST_NAME=notebookbarOffice.NotebookbarOffice.test_a"],
                         self.make_calls())

    def test_app_calc_is_the_default_target(self):
        self.run_script("--app", "calc", "m.C.test_a")
        self.assertEqual(["UITest_calc_tests UITEST_TEST_NAME=m.C.test_a"], self.make_calls())

    def test_a_failure_shows_the_apps_own_log(self):
        out = self.run_script("--app", "writer", "m.C.test_a", status=1)
        self.assertEqual(1, out.returncode)
        self.assertIn("log of writer_tests8", out.stdout)
        self.assertNotIn("log of calc_tests", out.stdout)
        out = self.run_script("m.C.test_a", status=1)
        self.assertIn("log of calc_tests", out.stdout)

    def test_unknown_app_is_rejected_before_any_build(self):
        for args in (("--app", "impress", "m.C.test_a"), ("--app",)):
            out = self.run_script(*args)
            self.assertEqual(2, out.returncode, args)
            self.assertIn("usage", out.stderr.lower(), args)
        self.assertEqual([], self.make_calls())


if __name__ == "__main__":
    unittest.main()

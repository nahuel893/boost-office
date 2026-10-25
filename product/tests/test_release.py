# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""product/release/make-release.sh with a tiny fake instdir and fake icon zips: the archive's layout, the top-level
wrappers (./install.sh with no arguments installs the bundled instdir), the checksum file, and the refusals. The
installs go into a temp HOME, never the user's own directories."""
import os
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from product.tests.test_install import STUB, snapshot

ROOT = Path(__file__).resolve().parents[2]
MAKE = ROOT / "product/release/make-release.sh"
VERSION = "9.8.7"
TOP = f"boost-office-{VERSION}"
ARCHIVE = f"{TOP}-linux-x86_64.tar.xz"


def fake_instdir(root):
    """A tree with a soffice stub, plus the runtime state a used instdir carries (a profile and a lock)."""
    instdir = Path(root)
    (instdir / "program").mkdir(parents=True)
    (instdir / "share/registry").mkdir(parents=True)
    soffice = instdir / "program/soffice"
    soffice.write_text(STUB, encoding="utf-8")
    soffice.chmod(0o755)
    (instdir / "LICENSE").write_text("license\n", encoding="utf-8")
    (instdir / "user/user").mkdir(parents=True)
    (instdir / "user/user/registrymodifications.xcu").write_text("private\n", encoding="utf-8")
    (instdir / ".lock").write_text("[Lockdata]\n", encoding="utf-8")
    return instdir


def fake_icons(root):
    icons = Path(root)
    icons.mkdir(parents=True)
    for theme in ("boost", "boost_dark"):
        with zipfile.ZipFile(icons / f"images_{theme}.zip", "w") as z:
            z.writestr("links.txt", theme + "\n")
    return icons


def make_release(*argv, env=None):
    return subprocess.run(["bash", str(MAKE), *argv], capture_output=True, text=True, check=False, timeout=300,
                          env=env)


class ReleaseTest(unittest.TestCase):
    """One release is built for the whole class (the repository's product files are copied each time)."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        cls.instdir = fake_instdir(cls.root / "instdir")
        cls.icons = fake_icons(cls.root / "icons")
        cls.out = cls.root / "out"
        cls.result = make_release("--instdir", str(cls.instdir), "--version", VERSION, "--out", str(cls.out),
                                  "--icons-dir", str(cls.icons))
        cls.extracted = cls.root / "extracted"
        if cls.result.returncode == 0:
            cls.extracted.mkdir()
            with tarfile.open(cls.out / ARCHIVE) as tar:
                cls.members = tar.getmembers()
                tar.extractall(cls.extracted, filter="tar")
        cls.bundle = cls.extracted / TOP

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def setUp(self):
        self.assertEqual(0, self.result.returncode, self.result.stdout + self.result.stderr)

    def test_the_out_dir_holds_the_archive_and_its_checksum(self):
        self.assertEqual(["SHA256SUMS", ARCHIVE], sorted(p.name for p in self.out.iterdir()))
        sums = (self.out / "SHA256SUMS").read_text(encoding="utf-8")
        self.assertRegex(sums, rf"^[0-9a-f]{{64}}  {ARCHIVE}\n$")
        check = subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=self.out, capture_output=True, text=True)
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)

    def test_one_top_folder_owned_by_nobody_in_particular(self):
        self.assertEqual({TOP}, {m.name.split("/")[0] for m in self.members})
        self.assertEqual({0}, {m.uid for m in self.members} | {m.gid for m in self.members})

    def test_the_layout(self):
        b = self.bundle
        for rel in ("install.sh", "uninstall.sh"):
            self.assertTrue(os.access(b / rel, os.X_OK), rel)
        for rel in ("README.md", "product/docs/install.md", "product/docs/licenses.md", "COPYING", "COPYING.MPL",
                    "COPYING.LGPL", "product/fonts/inter/OFL.txt", "product/icons/fluent/LICENSE",
                    "instdir/program/soffice", "instdir/LICENSE", "product/install/install.sh",
                    "product/install/uninstall.sh", "product/install/build_xcd.py"):
            self.assertTrue((b / rel).is_file(), rel)
        for theme in ("boost", "boost_dark"):
            self.assertEqual((self.icons / f"images_{theme}.zip").read_bytes(),
                             (b / f"product/icons/out/images_{theme}.zip").read_bytes())
        # the instdir's runtime state, the icon sources, the dev tools and caches stay out
        for rel in ("instdir/user", "instdir/.lock", "product/icons/fluent/add_circle_16_filled.svg",
                    "product/dev/office.sh", "product/tests", "product/odd"):
            self.assertFalse((b / rel).exists(), rel)
        self.assertEqual([], [m.name for m in self.members if "__pycache__" in m.name])

    def test_install_sh_with_no_arguments_installs_the_bundled_instdir_and_uninstall_removes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "LANG": "C.UTF-8"}
            before = snapshot(home)
            # started from another directory, the way a user may type the path
            out = subprocess.run([str(self.bundle / "install.sh")], cwd=tmp, capture_output=True, text=True,
                                 env=env, timeout=120)
            self.assertEqual(0, out.returncode, out.stdout + out.stderr)
            prefix = home / ".local/opt/boost-office"
            self.assertEqual(STUB, (prefix / "program/soffice").read_text(encoding="utf-8"))
            self.assertTrue((prefix / "share/registry/boost.xcd").is_file())
            self.assertTrue((prefix / "share/fonts/truetype/Inter-Regular.ttf").is_file())
            self.assertEqual((self.icons / "images_boost.zip").read_bytes(),
                             (prefix / "share/config/images_boost.zip").read_bytes())
            self.assertTrue(os.access(home / ".local/bin/boost-writer", os.X_OK))
            self.assertTrue((home / ".local/share/applications/boost-office-writer.desktop").is_file())
            self.assertFalse((prefix / "user").exists())
            out = subprocess.run([str(self.bundle / "uninstall.sh"), "--purge"], cwd=tmp, capture_output=True,
                                 text=True, env=env, timeout=120)
            self.assertEqual(0, out.returncode, out.stdout + out.stderr)
            self.assertEqual(before, snapshot(home))

    def test_the_wrappers_pass_their_options_on(self):
        for script in ("install.sh", "uninstall.sh"):
            out = subprocess.run([str(self.bundle / script), "--help"], capture_output=True, text=True, timeout=60)
            self.assertEqual(0, out.returncode, script)
            self.assertIn("--dry-run", out.stdout, script)


class RefusalTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.instdir = fake_instdir(self.root / "instdir")
        self.icons = fake_icons(self.root / "icons")
        self.out = self.root / "out"

    def test_an_instdir_without_soffice_is_refused_and_nothing_is_written(self):
        (self.instdir / "program/soffice").unlink()
        before = snapshot(self.root)
        out = make_release("--instdir", str(self.instdir), "--version", VERSION, "--out", str(self.out),
                           "--icons-dir", str(self.icons))
        self.assertEqual(1, out.returncode)
        self.assertIn("program/soffice", out.stderr)
        self.assertEqual(before, snapshot(self.root))

    def test_missing_or_bad_options_are_refused(self):
        base = ["--instdir", str(self.instdir), "--out", str(self.out), "--icons-dir", str(self.icons)]
        for argv in (base, base + ["--version", "1.0 beta"], base + ["--version", "../x"], ["--bogus"]):
            out = make_release(*argv)
            self.assertEqual(2, out.returncode, argv)
            self.assertIn("make-release.sh", out.stderr, argv)
            self.assertFalse(self.out.exists(), argv)

    def test_help(self):
        out = make_release("--help")
        self.assertEqual(0, out.returncode)
        for option in ("--instdir", "--version", "--out", "--icons-dir"):
            self.assertIn(option, out.stdout)


if __name__ == "__main__":
    unittest.main()

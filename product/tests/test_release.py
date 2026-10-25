# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""product/release/make-release.sh with a tiny fake instdir and fake icon zips: the archive's layout, the top-level
wrappers (./install.sh with no arguments installs the bundled instdir), the one-command installer
boost-office-install.sh (served by a local HTTP server through BOOST_OFFICE_BASE_URL and piped into bash), the
checksum file, and the refusals. The installs go into a temp HOME, never the user's own directories."""
import functools
import hashlib
import http.server
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path

from product.install import build_xcd
from product.tests.test_install import STUB, snapshot

ROOT = Path(__file__).resolve().parents[2]
MAKE = ROOT / "product/release/make-release.sh"
VERSION = "9.8.7"
TOP = f"boost-office-{VERSION}"
ARCHIVE = f"{TOP}-linux-x86_64.tar.xz"
BOOTSTRAP = "boost-office-install.sh"


def glibc_floor(path):
    """The highest GLIBC_ version an ELF file needs (readelf's version needs), e.g. '2.34'."""
    out = subprocess.run(["readelf", "-V", "-W", str(path)], capture_output=True, text=True, check=True,
                         env={**os.environ, "LC_ALL": "C"}).stdout
    return max(re.findall(r"Name: GLIBC_([0-9.]+)", out), key=lambda v: tuple(int(x) for x in v.split(".")))


def fake_instdir(root):
    """A tree with a soffice stub and one real ELF program (for the glibc floor), plus the runtime state a used
    instdir carries (a profile and a lock)."""
    instdir = Path(root)
    (instdir / "program").mkdir(parents=True)
    shutil.copy(shutil.which("true"), instdir / "program/elf-sample")
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
        self.assertEqual(["SHA256SUMS", ARCHIVE, BOOTSTRAP], sorted(p.name for p in self.out.iterdir()))
        sums = (self.out / "SHA256SUMS").read_text(encoding="utf-8")
        self.assertRegex(sums, rf"^[0-9a-f]{{64}}  {ARCHIVE}\n[0-9a-f]{{64}}  {BOOTSTRAP}\n$")
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


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    requests = []  # every path asked for, so a test can show that nothing was downloaded

    def do_GET(self):
        QuietHandler.requests.append(self.path)
        super().do_GET()

    def log_message(self, *args):
        pass


class BootstrapTest(unittest.TestCase):
    """boost-office-install.sh piped into bash, the way the README's one-liner runs it, against a local server."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        instdir = fake_instdir(cls.root / "instdir")
        cls.icons = fake_icons(cls.root / "icons")
        cls.out = cls.root / "out"
        cls.result = make_release("--instdir", str(instdir), "--version", VERSION, "--out", str(cls.out),
                                  "--icons-dir", str(cls.icons))
        cls.tampered = cls.root / "tampered"
        cls.tampered.mkdir()
        if cls.result.returncode == 0:
            data = bytearray((cls.out / ARCHIVE).read_bytes())
            data[-100] ^= 0xFF
            (cls.tampered / ARCHIVE).write_bytes(bytes(data))
        cls.server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(cls.root)))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls._tmp.cleanup()

    def setUp(self):
        self.assertEqual(0, self.result.returncode, self.result.stdout + self.result.stderr)
        self._home = tempfile.TemporaryDirectory()
        self.addCleanup(self._home.cleanup)
        self.top = Path(self._home.name)
        self.home = self.top / "home"
        self.cache = self.home / ".cache"
        self.cache.mkdir(parents=True)
        self.prefix = self.home / ".local/opt/boost-office"
        self.env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(self.home), "LANG": "C.UTF-8",
                    "BOOST_OFFICE_BASE_URL": f"{self.url}/out"}

    def pipe(self, *argv, env=None):
        """curl -fsSL .../boost-office-install.sh | bash -s -- ARGV"""
        script = (self.out / BOOTSTRAP).read_bytes()
        return subprocess.run(["bash", "-s", "--", *argv], input=script, capture_output=True, cwd=self.top,
                              env=env or self.env, timeout=300)

    def assert_ok(self, out):
        self.assertEqual(0, out.returncode, (out.stdout + out.stderr).decode())

    def old_glibc_env(self, getconf=True):
        """PATH with stubs that report glibc 2.17: getconf, or (getconf failing) ldd --version."""
        stubs = self.top / "stubs"
        stubs.mkdir(exist_ok=True)
        for name, body in (("getconf", 'echo "glibc 2.17"' if getconf else "exit 1"),
                           ("ldd", 'echo "ldd (GNU libc) 2.17"; echo "Copyright (C) 2012"')):
            (stubs / name).write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
            (stubs / name).chmod(0o755)
        return {**self.env, "PATH": f"{stubs}:{self.env['PATH']}"}

    def test_it_carries_the_glibc_floor_of_the_shipped_files(self):
        text = (self.out / BOOTSTRAP).read_text(encoding="utf-8")
        self.assertIn(f'GLIBC_FLOOR="{glibc_floor(shutil.which("true"))}"', text)

    def test_an_older_glibc_refuses_before_any_download(self):
        for getconf in (True, False):
            QuietHandler.requests.clear()
            before = snapshot(self.home)
            out = self.pipe(env=self.old_glibc_env(getconf))
            self.assertEqual(1, out.returncode, getconf)
            err = out.stderr.decode()
            floor = glibc_floor(shutil.which("true"))
            self.assertIn(f"needs glibc {floor} or newer; this system has glibc 2.17", err)
            for words in ("Arch", "Manjaro", "Ubuntu, Debian and Fedora is planned",
                          "https://github.com/nahuel893/boost-office/blob/main/product/docs/building.md"):
                self.assertIn(words, err)
            self.assertEqual([], QuietHandler.requests, getconf)
            self.assertEqual(before, snapshot(self.home))

    def test_uninstall_is_not_gated_on_glibc(self):
        self.assert_ok(self.pipe())
        out = self.pipe("--uninstall", "--purge", env=self.old_glibc_env())
        self.assert_ok(out)
        self.assertFalse(self.prefix.exists())

    def test_it_carries_the_version_and_the_archive_checksum(self):
        text = (self.out / BOOTSTRAP).read_text(encoding="utf-8")
        sha = hashlib.sha256((self.out / ARCHIVE).read_bytes()).hexdigest()
        self.assertIn(f'VERSION="{VERSION}"', text)
        self.assertIn(f'SHA256="{sha}"', text)
        for placeholder in ("@VERSION@", "@SHA256@", "@ARCHIVE_MB@", "@TREE_MB@"):
            self.assertNotIn(placeholder, text)
        self.assertTrue(os.access(self.out / BOOTSTRAP, os.X_OK))
        self.assertEqual(0, subprocess.run(["bash", "-n", str(self.out / BOOTSTRAP)]).returncode)

    def test_the_one_liner_installs_upgrades_and_uninstalls_without_the_archive(self):
        (self.home / ".config").mkdir()
        before = snapshot(self.home)
        out = self.pipe("--theme", "dark")
        self.assert_ok(out)
        self.assertIn(b"Checksum OK", out.stdout)
        self.assertIn(b"--uninstall", out.stdout)
        self.assertEqual(STUB, (self.prefix / "program/soffice").read_text(encoding="utf-8"))
        self.assertEqual(build_xcd.render("dark"),
                         (self.prefix / "share/registry/boost.xcd").read_text(encoding="utf-8"))
        self.assertTrue(os.access(self.prefix / "uninstall.sh", os.X_OK))
        self.assertEqual([], list(self.cache.iterdir()))  # the temp folder is gone
        # running it again replaces the install (the profile stays)
        (self.home / ".config/boost-office").mkdir()
        out = self.pipe()
        self.assert_ok(out)
        self.assertIn(b"replaced", out.stdout)
        self.assertEqual(build_xcd.render("light"),
                         (self.prefix / "share/registry/boost.xcd").read_text(encoding="utf-8"))
        self.assertTrue((self.home / ".config/boost-office").is_dir())
        # --uninstall needs no download: the server is not asked
        out = self.pipe("--uninstall", "--purge", env={**self.env, "BOOST_OFFICE_BASE_URL": "http://127.0.0.1:9"})
        self.assert_ok(out)
        self.assertEqual(before, snapshot(self.home))

    def test_a_wrong_checksum_refuses_and_leaves_nothing(self):
        before = snapshot(self.home)
        out = self.pipe(env={**self.env, "BOOST_OFFICE_BASE_URL": f"{self.url}/tampered"})
        self.assertEqual(1, out.returncode)
        self.assertIn(b"checksum mismatch", out.stderr)
        self.assertEqual(before, snapshot(self.home))

    def test_a_failed_download_leaves_nothing(self):
        before = snapshot(self.home)
        out = self.pipe(env={**self.env, "BOOST_OFFICE_BASE_URL": f"{self.url}/missing"})
        self.assertEqual(1, out.returncode)
        self.assertIn(b"download failed", out.stderr)
        self.assertEqual(before, snapshot(self.home))

    def test_uninstall_without_an_install_fails_clearly(self):
        out = self.pipe("--uninstall")
        self.assertEqual(1, out.returncode)
        self.assertIn(b"no Boost Office install", out.stderr)

    def test_install_options_pass_through(self):
        out = self.pipe("--dry-run", "--bindir", str(self.top / "bin"))
        self.assert_ok(out)
        self.assertIn(f"{self.top}/bin/boost-writer".encode(), out.stdout)
        self.assertFalse(self.prefix.exists())
        self.assertEqual([], list(self.cache.iterdir()))


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

    def test_an_instdir_with_no_elf_file_is_refused(self):
        (self.instdir / "program/elf-sample").unlink()
        out = make_release("--instdir", str(self.instdir), "--version", VERSION, "--out", str(self.out),
                           "--icons-dir", str(self.icons))
        self.assertEqual(1, out.returncode)
        self.assertIn("GLIBC_", out.stderr)
        self.assertFalse((self.out / ARCHIVE).exists())

    def test_help(self):
        out = make_release("--help")
        self.assertEqual(0, out.returncode)
        for option in ("--instdir", "--version", "--out", "--icons-dir"):
            self.assertIn(option, out.stdout)


if __name__ == "__main__":
    unittest.main()

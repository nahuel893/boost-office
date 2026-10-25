# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""product/install/install.sh and uninstall.sh with a tiny fake instdir, a temp HOME, XDG_DATA_HOME, prefix and
bindir: never the user's own directories."""
import configparser
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from product.install import build_xcd

ROOT = Path(__file__).resolve().parents[2]
INSTALL = ROOT / "product/install/install.sh"
UNINSTALL = ROOT / "product/install/uninstall.sh"
MARKER = "# boost-office-install 1"
APPS = {  # launcher -> (soffice flag, desktop file, Name, icon, stock desktop file)
    "boost-office": (None, "boost-office-startcenter.desktop", "Boost Office", "boost-office-startcenter",
                     "startcenter.desktop"),
    "boost-writer": ("--writer", "boost-office-writer.desktop", "Boost Writer", "boost-office-writer",
                     "writer.desktop"),
    "boost-calc": ("--calc", "boost-office-calc.desktop", "Boost Calc", "boost-office-calc", "calc.desktop"),
    "boost-impress": ("--impress", "boost-office-impress.desktop", "Boost Impress", "boost-office-impress",
                      "impress.desktop"),
}
# A soffice that records how it was started.
STUB = """#!/usr/bin/env python3
import json, os, sys
keys = ("SAL_USE_VCLPLUGIN", "GTK_THEME", "XDG_CONFIG_HOME")
with open(os.environ["BOOST_STUB_LOG"], "w", encoding="utf-8") as f:
    json.dump({"argv": sys.argv[1:], "env": {k: os.environ.get(k) for k in keys}}, f)
"""


def snapshot(root):
    """Every path under root: its type and, for files, its bytes."""
    out = {}
    for path in sorted(Path(root).rglob("*")):
        rel = str(path.relative_to(root))
        if path.is_symlink():
            out[rel] = ("link", os.readlink(path))
        elif path.is_dir():
            out[rel] = ("dir", None)
        else:
            out[rel] = ("file", path.read_bytes())
    return out


def desktop_entry(path):
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    return parser["Desktop Entry"]


def stock_entry(name):
    return desktop_entry(ROOT / "sysui/desktop/menus" / name)


class InstallTestCase(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._log = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.log = Path(self._log.name) / "stub.json"
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(self._log.cleanup)
        self.home = self.root / "home"
        self.data = self.root / "xdg-data"
        self.prefix = self.root / "opt" / "boost-office"
        self.bindir = self.root / "bin"
        self.instdir = self.root / "instdir"
        self.icons = self.root / "icons"
        self.home.mkdir()
        (self.instdir / "program").mkdir(parents=True)
        (self.instdir / "share" / "registry").mkdir(parents=True)
        soffice = self.instdir / "program" / "soffice"
        soffice.write_text(STUB, encoding="utf-8")
        soffice.chmod(0o755)
        self.icons.mkdir()
        for theme in ("boost", "boost_dark"):
            with zipfile.ZipFile(self.icons / f"images_{theme}.zip", "w") as z:
                z.writestr("links.txt", theme + "\n")
        self.env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(self.home),
                    "XDG_DATA_HOME": str(self.data), "LANG": "C.UTF-8"}

    def args(self, *extra):
        return ["--instdir", str(self.instdir), "--prefix", str(self.prefix), "--bindir", str(self.bindir),
                "--icons-dir", str(self.icons), *extra]

    def run_script(self, script, *argv, env=None):
        return subprocess.run(["bash", str(script), *argv], capture_output=True, text=True, check=False,
                              env=env or self.env, timeout=120)

    def install(self, *extra):
        out = self.run_script(INSTALL, *self.args(*extra))
        self.assertEqual(0, out.returncode, out.stdout + out.stderr)
        return out

    def manifest(self):
        lines = (self.prefix / ".boost-office-install").read_text(encoding="utf-8").splitlines()
        return lines[0], [tuple(line.split(" ", 1)) for line in lines[1:] if line and not line.startswith("#")]


class InstallTest(InstallTestCase):

    def test_the_tree_the_layer_the_fonts_and_the_icon_zips_go_into_the_prefix(self):
        self.install()
        self.assertTrue((self.prefix / "program/soffice").is_file())
        self.assertEqual(build_xcd.render("light"),
                         (self.prefix / "share/registry/boost.xcd").read_text(encoding="utf-8"))
        fonts = sorted(p.name for p in (self.prefix / "share/fonts/truetype").iterdir())
        self.assertEqual(sorted(p.name for p in (ROOT / "product/fonts/inter").glob("*.ttf")), fonts)
        for theme in ("boost", "boost_dark"):
            self.assertEqual((self.icons / f"images_{theme}.zip").read_bytes(),
                             (self.prefix / f"share/config/images_{theme}.zip").read_bytes())
        # nothing is left next to the prefix (the copy goes through a temp dir that is renamed)
        self.assertEqual(["boost-office"], sorted(p.name for p in self.prefix.parent.iterdir()))

    def test_dark_theme_writes_the_dark_layer(self):
        self.install("--theme", "dark")
        self.assertEqual(build_xcd.render("dark"),
                         (self.prefix / "share/registry/boost.xcd").read_text(encoding="utf-8"))
        self.assertIn(("theme", "dark"), self.manifest()[1])

    def test_unknown_theme_is_refused(self):
        out = self.run_script(INSTALL, *self.args("--theme", "blue"))
        self.assertEqual(2, out.returncode)
        self.assertIn("--theme", out.stderr)
        self.assertFalse(self.prefix.exists())

    def test_launchers_start_soffice_with_their_own_profile_and_no_dev_tricks(self):
        self.install()
        for launcher, (flag, *_rest) in APPS.items():
            path = self.bindir / launcher
            self.assertTrue(os.access(path, os.X_OK), launcher)
            out = subprocess.run([str(path), "my file.odt"], capture_output=True, text=True, check=False,
                                 env={**self.env, "BOOST_STUB_LOG": str(self.log)}, timeout=30)
            self.assertEqual(0, out.returncode, out.stderr)
            seen = json.loads(self.log.read_text(encoding="utf-8"))
            profile = f"-env:UserInstallation=file://{self.home}/.config/boost-office"
            self.assertEqual(([flag] if flag else []) + [profile, "my file.odt"], seen["argv"], launcher)
            self.assertEqual({"SAL_USE_VCLPLUGIN": "gtk3", "GTK_THEME": None, "XDG_CONFIG_HOME": None},
                             seen["env"], launcher)

    def test_a_launcher_keeps_the_users_vcl_plugin(self):
        self.install()
        env = {**self.env, "BOOST_STUB_LOG": str(self.log), "SAL_USE_VCLPLUGIN": "kf5"}
        subprocess.run([str(self.bindir / "boost-calc")], check=True, env=env, timeout=30)
        self.assertEqual("kf5", json.loads(self.log.read_text(encoding="utf-8"))["env"]["SAL_USE_VCLPLUGIN"])

    def test_desktop_entries_and_their_icons(self):
        self.install()
        for launcher, (_flag, name, title, icon, stock) in APPS.items():
            entry = desktop_entry(self.data / "applications" / name)
            self.assertEqual("Application", entry["Type"], name)
            self.assertEqual(title, entry["Name"], name)
            self.assertEqual(f"{self.bindir / launcher} %U", entry["Exec"], name)
            self.assertEqual(icon, entry["Icon"], name)
            self.assertEqual(stock_entry(stock)["MimeType"], entry["MimeType"], name)
            self.assertNotIn("LibreOffice", "".join(entry.values()), name)
            for size, ext in (("48x48", "png"), ("48x48", "svg"), ("scalable", "svg"), ("256x256", "png")):
                self.assertTrue((self.data / f"icons/hicolor/{size}/apps/{icon}.{ext}").is_file(), (icon, size))

    def test_the_manifest_lists_every_path_written_outside_the_prefix(self):
        before = snapshot(self.root)
        self.install()
        header, records = self.manifest()
        self.assertEqual(MARKER, header)
        self.assertIn(("prefix", str(self.prefix)), records)
        self.assertIn(("theme", "light"), records)
        listed = {path for kind, path in records if kind in ("file", "dir")}
        new = {str(self.root / rel) for rel in snapshot(self.root).keys() - before.keys()}
        outside = {p for p in new if p != str(self.prefix) and not p.startswith(str(self.prefix) + "/")}
        self.assertEqual(outside, listed)
        self.assertIn(("file", str(self.bindir / "boost-writer")), records)
        self.assertIn(("dir", str(self.bindir)), records)

    def test_dry_run_prints_the_plan_and_writes_nothing(self):
        before = snapshot(self.root)
        out = self.run_script(INSTALL, *self.args("--dry-run"))
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertEqual(before, snapshot(self.root))
        for word in ("boost.xcd", "boost-writer", "boost-office-calc.desktop", "Inter-Regular.ttf",
                     "images_boost.zip", str(self.prefix)):
            self.assertIn(word, out.stdout)

    def test_defaults_are_under_home(self):
        env = {k: v for k, v in self.env.items() if k != "XDG_DATA_HOME"}
        out = self.run_script(INSTALL, "--instdir", str(self.instdir), "--icons-dir", str(self.icons), "--dry-run",
                              env=env)
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn(f"{self.home}/.local/opt/boost-office", out.stdout)
        self.assertIn(f"{self.home}/.local/bin/boost-writer", out.stdout)
        self.assertIn(f"{self.home}/.local/share/applications/boost-office-writer.desktop", out.stdout)

    def test_an_instdir_without_soffice_fails_clearly_and_writes_nothing(self):
        (self.instdir / "program/soffice").unlink()
        before = snapshot(self.root)
        out = self.run_script(INSTALL, *self.args())
        self.assertNotEqual(0, out.returncode)
        self.assertIn("program/soffice", out.stderr)
        self.assertEqual(before, snapshot(self.root))

    def test_a_second_install_needs_force(self):
        self.install()
        again = self.run_script(INSTALL, *self.args())
        self.assertNotEqual(0, again.returncode)
        self.assertIn("--force", again.stderr)
        (self.instdir / "program/new-file").write_text("x", encoding="utf-8")
        self.install("--force", "--theme", "dark")
        self.assertTrue((self.prefix / "program/new-file").is_file())
        self.assertEqual(build_xcd.render("dark"),
                         (self.prefix / "share/registry/boost.xcd").read_text(encoding="utf-8"))
        self.assertIn(("theme", "dark"), self.manifest()[1])

    def test_force_never_replaces_a_directory_without_the_marker(self):
        self.prefix.mkdir(parents=True)
        (self.prefix / "keep.txt").write_text("mine", encoding="utf-8")
        out = self.run_script(INSTALL, *self.args("--force"))
        self.assertNotEqual(0, out.returncode)
        self.assertIn("not a Boost Office install", out.stderr)
        self.assertEqual("mine", (self.prefix / "keep.txt").read_text(encoding="utf-8"))

    def test_an_existing_profile_is_told_how_to_switch_the_theme(self):
        quiet = self.install()
        self.assertNotIn("new profiles", quiet.stdout)
        (self.home / ".config/boost-office").mkdir(parents=True)
        told = self.install("--force", "--theme", "dark")
        self.assertIn("new profiles", told.stdout)
        self.assertIn("Tools > Options", told.stdout)

    def test_help(self):
        for script in (INSTALL, UNINSTALL):
            out = self.run_script(script, "--help")
            self.assertEqual(0, out.returncode, script)
            self.assertIn("--dry-run", out.stdout, script)
            self.assertIn("--prefix", out.stdout, script)


class UninstallTest(InstallTestCase):

    def test_uninstall_leaves_the_temp_dirs_exactly_as_before(self):
        (self.home / ".config/boost-office/user").mkdir(parents=True)
        (self.home / ".config/boost-office/user/registrymodifications.xcu").write_text("x", encoding="utf-8")
        before = snapshot(self.root)
        self.install()
        out = self.run_script(UNINSTALL, "--prefix", str(self.prefix))
        self.assertEqual(0, out.returncode, out.stdout + out.stderr)
        self.assertEqual(before, snapshot(self.root))

    def test_the_prefix_carries_its_own_uninstall_sh(self):
        (self.home / ".config/boost-office/user").mkdir(parents=True)
        before = snapshot(self.root)
        out = self.install()
        own = self.prefix / "uninstall.sh"
        self.assertEqual(UNINSTALL.read_bytes(), own.read_bytes())
        self.assertTrue(os.access(own, os.X_OK))
        self.assertIn(f"{own} --prefix {self.prefix}", out.stdout)
        # it works from the prefix it removes, with no repository or release folder around
        out = self.run_script(own, "--prefix", str(self.prefix), "--purge")
        self.assertEqual(0, out.returncode, out.stdout + out.stderr)
        self.assertFalse((self.home / ".config/boost-office").exists())
        del before["home/.config/boost-office"], before["home/.config/boost-office/user"]
        self.assertEqual(before, snapshot(self.root))

    def test_purge_also_removes_the_profile(self):
        (self.home / ".config/boost-office/user").mkdir(parents=True)
        self.install()
        out = self.run_script(UNINSTALL, "--prefix", str(self.prefix), "--purge")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertFalse((self.home / ".config/boost-office").exists())
        self.assertTrue((self.home / ".config").is_dir())

    def test_uninstall_dry_run_removes_nothing(self):
        self.install()
        before = snapshot(self.root)
        out = self.run_script(UNINSTALL, "--prefix", str(self.prefix), "--dry-run")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertEqual(before, snapshot(self.root))
        self.assertIn(str(self.bindir / "boost-writer"), out.stdout)

    def test_uninstall_refuses_a_prefix_without_the_marker(self):
        self.prefix.mkdir(parents=True)
        (self.prefix / "keep.txt").write_text("mine", encoding="utf-8")
        before = snapshot(self.root)
        out = self.run_script(UNINSTALL, "--prefix", str(self.prefix))
        self.assertNotEqual(0, out.returncode)
        self.assertIn("not a Boost Office install", out.stderr)
        self.assertEqual(before, snapshot(self.root))

    def test_uninstall_refuses_a_manifest_moved_to_another_prefix(self):
        self.install()
        moved = self.root / "elsewhere"
        self.prefix.rename(moved)
        out = self.run_script(UNINSTALL, "--prefix", str(moved))
        self.assertNotEqual(0, out.returncode)
        self.assertTrue((moved / "program/soffice").is_file())


class FlagSampleTest(unittest.TestCase):

    def test_the_tracked_flag_sample(self):
        lines = (ROOT / "product/install/autogen.input.boost").read_text(encoding="utf-8").splitlines()
        flags = [line for line in lines if line and not line.startswith("#")]
        self.assertTrue(all(flag.startswith("--") for flag in flags), flags)
        for flag in ("--enable-gtk3", "--disable-gtk4", "--disable-qt5", "--disable-qt6", "--disable-kf5",
                     "--disable-kf6", "--without-java", "--without-help", "--without-helppack-integration",
                     "--without-myspell-dicts", "--without-doxygen", "--disable-firebird-sdbc",
                     "--disable-postgresql-sdbc", "--enable-option-checking=fatal"):
            self.assertIn(flag, flags)
        self.assertFalse([f for f in flags if f.startswith("--with-parallelism")])
        self.assertTrue(any(line.startswith("#") for line in lines))


if __name__ == "__main__":
    unittest.main()

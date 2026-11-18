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

from product.brand import build_brand
from product.install import build_xcd
from product.tests.test_brand import STOCK_SOFFICERC, png

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


def default_apps(path):
    """The [Default Applications] entries of a mimeapps.list."""
    out, inside = {}, False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("["):
            inside = line == "[Default Applications]"
        elif inside and "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def expected_defaults():
    """Each file type of the Writer, Calc and Impress entries, to the first of them that lists it."""
    out = {}
    for launcher in ("boost-writer", "boost-calc", "boost-impress"):
        _flag, desktop, _title, _icon, stock = APPS[launcher]
        for mime in filter(None, stock_entry(stock)["MimeType"].split(";")):
            out.setdefault(mime, desktop)
    return out


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
        self.brand = self.root / "brand"
        self.home.mkdir()
        (self.instdir / "program").mkdir(parents=True)
        (self.instdir / "share" / "registry").mkdir(parents=True)
        soffice = self.instdir / "program" / "soffice"
        soffice.write_text(STUB, encoding="utf-8")
        soffice.chmod(0o755)
        # the stock brand the overlay replaces
        (self.instdir / "program/sofficerc").write_text(STOCK_SOFFICERC, encoding="utf-8")
        (self.instdir / "program/intro.png").write_bytes(b"stock splash")
        (self.instdir / "program/shell").mkdir()
        for name in (*build_brand.SHELL_LOGOS, "donate1.png"):
            (self.instdir / "program/shell" / name).write_text("stock " + name, encoding="utf-8")
        self.brand.mkdir()
        for name, (_svg, (width, height)) in build_brand.SPLASHES.items():
            png(self.brand / name, width, height)
        self.icons.mkdir()
        for theme in ("boost", "boost_dark"):
            with zipfile.ZipFile(self.icons / f"images_{theme}.zip", "w") as z:
                z.writestr("links.txt", theme + "\n")
        self.env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(self.home),
                    "XDG_DATA_HOME": str(self.data), "LANG": "C.UTF-8"}

    def args(self, *extra):
        return ["--instdir", str(self.instdir), "--prefix", str(self.prefix), "--bindir", str(self.bindir),
                "--icons-dir", str(self.icons), "--brand-dir", str(self.brand), *extra]

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

    def assert_boost_brand(self):
        program = self.prefix / "program"
        for name in build_brand.SPLASHES:
            self.assertEqual((self.brand / name).read_bytes(), (program / name).read_bytes(), name)
        for name in build_brand.SHELL_LOGOS:
            self.assertEqual((ROOT / "product/brand/shell" / name).read_bytes(), (program / "shell" / name).read_bytes(),
                             name)
        self.assertEqual("stock donate1.png", (program / "shell/donate1.png").read_text(encoding="utf-8"))
        self.assertEqual(build_brand.edit_sofficerc(STOCK_SOFFICERC, build_brand.sofficerc_keys()),
                         (program / "sofficerc").read_text(encoding="utf-8"))

    def test_the_boost_brand_goes_over_the_copied_tree_and_the_instdir_stays_stock(self):
        before = snapshot(self.instdir)
        out = self.install()
        self.assert_boost_brand()
        self.assertEqual(before, snapshot(self.instdir))
        self.assertIn("sofficerc", out.stdout)

    def test_force_replaces_a_stale_brand(self):
        self.install()
        (self.prefix / "program/intro.png").write_bytes(b"stale")
        (self.prefix / "program/shell/logo.svg").write_text("stale", encoding="utf-8")
        self.install("--force")
        self.assert_boost_brand()

    def test_a_splash_of_the_wrong_size_is_refused_before_anything_is_written(self):
        png(self.brand / "intro.png", 640, 199)
        before = snapshot(self.root)
        out = self.run_script(INSTALL, *self.args())
        self.assertNotEqual(0, out.returncode)
        self.assertIn("640 x 199", out.stderr)
        self.assertEqual(before, snapshot(self.root))

    def test_an_instdir_without_sofficerc_is_refused(self):
        (self.instdir / "program/sofficerc").unlink()
        before = snapshot(self.root)
        out = self.run_script(INSTALL, *self.args())
        self.assertNotEqual(0, out.returncode)
        self.assertIn("program/sofficerc", out.stderr)
        self.assertEqual(before, snapshot(self.root))

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

    def test_headless_runs_leave_the_vcl_plugin_to_soffice(self):
        # gtk3 needs a display: a conversion on a server would fail (and exit 0) with it
        self.install()
        env = {**self.env, "BOOST_STUB_LOG": str(self.log)}
        for argv in (["--headless"], ["--convert-to", "pdf", "a.odt"], ["--print-to-file", "a.odt"],
                     ["--cat", "a.odt"], ["--headless", "--convert-to", "pdf", "--outdir", "out", "a.docx"]):
            for launcher in ("boost-writer", "boost-office"):
                subprocess.run([str(self.bindir / launcher), *argv], check=True, env=env, timeout=30)
                seen = json.loads(self.log.read_text(encoding="utf-8"))
                self.assertIsNone(seen["env"]["SAL_USE_VCLPLUGIN"], (launcher, argv))
                self.assertEqual(argv, seen["argv"][-len(argv):], (launcher, argv))
        # the user's own choice stays, headless or not
        subprocess.run([str(self.bindir / "boost-calc"), "--headless"], check=True,
                       env={**env, "SAL_USE_VCLPLUGIN": "svp"}, timeout=30)
        self.assertEqual("svp", json.loads(self.log.read_text(encoding="utf-8"))["env"]["SAL_USE_VCLPLUGIN"])
        # an argument that only contains a flag's text is an ordinary file name
        subprocess.run([str(self.bindir / "boost-writer"), "--headless-notes.odt"], check=True, env=env, timeout=30)
        self.assertEqual("gtk3", json.loads(self.log.read_text(encoding="utf-8"))["env"]["SAL_USE_VCLPLUGIN"])

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
        listed = {path for kind, path in records if kind in ("file", "dir", "mimeapps")}
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
                     "images_boost.zip", "intro-highres.png", "sofficerc", "mimeapps.list", str(self.prefix)):
            self.assertIn(word, out.stdout)

    def test_defaults_are_under_home(self):
        env = {k: v for k, v in self.env.items() if k != "XDG_DATA_HOME"}
        out = self.run_script(INSTALL, "--instdir", str(self.instdir), "--icons-dir", str(self.icons),
                              "--brand-dir", str(self.brand), "--dry-run", env=env)
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
        self.assertIn("--no-default-apps", self.run_script(INSTALL, "--help").stdout)


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


class DefaultAppsTest(InstallTestCase):
    # a user's mimeapps.list from before the install: another office suite for CSV and ODT, a browser for HTML
    PRIOR = ("[Added Associations]\n"
             "text/csv=wps-office-et.desktop;\n"
             "\n"
             "[Default Applications]\n"
             "text/html=firefox.desktop\n"
             "text/csv=wps-office-et.desktop\n"
             "application/vnd.oasis.opendocument.text=Other Office.desktop\n")
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def setUp(self):
        super().setUp()
        self.mimeapps = self.home / ".config/mimeapps.list"

    def write_prior(self, extra=""):
        self.mimeapps.parent.mkdir(parents=True, exist_ok=True)
        self.mimeapps.write_text(self.PRIOR + extra, encoding="utf-8")

    def uninstall(self):
        out = self.run_script(UNINSTALL, "--prefix", str(self.prefix))
        self.assertEqual(0, out.returncode, out.stdout + out.stderr)
        return out

    def test_writer_calc_and_impress_become_the_default_for_their_file_types(self):
        self.write_prior()
        out = self.install()
        defaults = default_apps(self.mimeapps)
        for mime, desktop in expected_defaults().items():
            self.assertEqual(desktop, defaults[mime], mime)
        self.assertEqual("boost-office-calc.desktop", defaults["text/csv"])
        self.assertEqual("boost-office-writer.desktop", defaults[self.DOCX])
        self.assertEqual("firefox.desktop", defaults["text/html"])
        self.assertNotIn("boost-office-startcenter.desktop", defaults.values())
        self.assertTrue(self.mimeapps.read_text(encoding="utf-8").startswith(
            "[Added Associations]\ntext/csv=wps-office-et.desktop;\n\n[Default Applications]\n"))
        self.assertIn(str(self.mimeapps), out.stdout)

    def test_uninstall_gives_the_file_types_back_byte_for_byte(self):
        self.write_prior()
        before = snapshot(self.root)
        self.install()
        self.uninstall()
        self.assertEqual(before, snapshot(self.root))

    def test_a_mimeapps_list_the_install_created_goes_away_with_it(self):
        before = snapshot(self.root)
        self.install()
        self.assertEqual(expected_defaults(), default_apps(self.mimeapps))
        self.uninstall()
        self.assertEqual(before, snapshot(self.root))

    def test_a_default_the_user_chose_after_the_install_stays(self):
        self.write_prior()
        self.install()
        text = self.mimeapps.read_text(encoding="utf-8")
        self.mimeapps.write_text(text.replace("text/csv=boost-office-calc.desktop", "text/csv=gnumeric.desktop"),
                                 encoding="utf-8")
        self.uninstall()
        defaults = default_apps(self.mimeapps)
        self.assertEqual("gnumeric.desktop", defaults["text/csv"])
        self.assertEqual("Other Office.desktop", defaults["application/vnd.oasis.opendocument.text"])
        self.assertNotIn(self.DOCX, defaults)
        self.assertNotIn("boost-office", self.mimeapps.read_text(encoding="utf-8"))

    def test_an_upgrade_keeps_the_defaults_from_before_boost(self):
        self.write_prior()
        before = snapshot(self.root)
        self.install()
        self.install("--force")
        self.assertEqual("boost-office-calc.desktop", default_apps(self.mimeapps)["text/csv"])
        self.uninstall()
        self.assertEqual(before, snapshot(self.root))

    def test_a_type_already_set_to_boost_is_dropped_at_uninstall(self):
        # an earlier install, or the user by hand, pointed it at Boost: there is nothing older to give back
        self.write_prior(f"{self.XLSX}=boost-office-calc.desktop\n")
        self.install()
        self.uninstall()
        defaults = default_apps(self.mimeapps)
        self.assertNotIn(self.XLSX, defaults)
        self.assertEqual("wps-office-et.desktop", defaults["text/csv"])

    def test_no_default_apps_leaves_them_alone(self):
        home = snapshot(self.home)
        self.install("--no-default-apps")
        self.assertEqual(home, snapshot(self.home))
        self.write_prior()
        before = snapshot(self.root)
        self.install("--force", "--no-default-apps")
        self.assertEqual(before["home/.config/mimeapps.list"], snapshot(self.root)["home/.config/mimeapps.list"])
        self.assertFalse([r for r in self.manifest()[1] if r[0] in ("mimeapps", "default")])

    def test_xdg_config_home_is_where_mimeapps_list_goes(self):
        config = self.root / "xdg-config"
        self.env["XDG_CONFIG_HOME"] = str(config)
        self.install()
        self.assertEqual(expected_defaults(), default_apps(config / "mimeapps.list"))
        self.assertFalse(self.mimeapps.exists())

    def test_every_default_applications_section_is_set_and_given_back(self):
        # GLib merges repeated sections and the last line wins: a type there must become Boost's too
        self.write_prior(f"\n[Added Associations]\nimage/png=eog.desktop;\n\n[Default Applications]\n"
                         f"{self.DOCX}=onlyoffice.desktop\n")
        before = snapshot(self.root)
        self.install()
        self.assertEqual("boost-office-writer.desktop", default_apps(self.mimeapps)[self.DOCX])
        self.assertNotIn("onlyoffice", self.mimeapps.read_text(encoding="utf-8"))
        self.uninstall()
        self.assertEqual(before, snapshot(self.root))

    def test_a_mimeapps_list_kept_as_a_link_stays_a_link(self):
        dotfiles = self.root / "dotfiles/mimeapps.list"
        dotfiles.parent.mkdir()
        dotfiles.write_text(self.PRIOR, encoding="utf-8")
        self.mimeapps.parent.mkdir(parents=True)
        self.mimeapps.symlink_to(dotfiles)
        before = snapshot(self.root)
        self.install()
        self.assertTrue(self.mimeapps.is_symlink())
        self.assertEqual("boost-office-calc.desktop", default_apps(dotfiles)["text/csv"])
        self.uninstall()
        self.assertEqual(before, snapshot(self.root))

    @unittest.skipIf(os.geteuid() == 0, "root writes anywhere")
    def test_an_unwritable_config_folder_is_refused_before_anything_is_written(self):
        config = self.mimeapps.parent
        config.mkdir()
        config.chmod(0o555)
        self.addCleanup(config.chmod, 0o755)
        before = snapshot(self.root)
        out = self.run_script(INSTALL, *self.args())
        self.assertNotEqual(0, out.returncode)
        self.assertIn("--no-default-apps", out.stderr)
        self.assertEqual(before, snapshot(self.root))

    @unittest.skipIf(os.geteuid() == 0, "root writes anywhere")
    def test_uninstall_leaves_a_mimeapps_list_without_boost_lines_untouched(self):
        self.write_prior()
        self.install()
        self.mimeapps.write_text(self.PRIOR, encoding="utf-8")  # the user put their own file back
        self.mimeapps.parent.chmod(0o555)
        self.addCleanup(self.mimeapps.parent.chmod, 0o755)
        self.uninstall()
        self.assertEqual(self.PRIOR, self.mimeapps.read_text(encoding="utf-8"))
        self.assertFalse(self.prefix.exists())

    def test_uninstall_dry_run_keeps_the_defaults(self):
        self.write_prior()
        self.install()
        installed = self.mimeapps.read_bytes()
        out = self.run_script(UNINSTALL, "--prefix", str(self.prefix), "--dry-run")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertEqual(installed, self.mimeapps.read_bytes())
        self.assertIn(str(self.mimeapps), out.stdout)


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

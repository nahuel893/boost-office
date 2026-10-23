# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "product/dev/calc.sh"
OFFICE = ROOT / "product/dev/office.sh"


def dry_run(*args):
    return subprocess.run(["bash", str(SCRIPT), "--dry-run", *args],
                          capture_output=True, text=True, check=False)


class CalcLauncherTest(unittest.TestCase):

    def test_light_uses_office_ui_green_scheme_and_light_gtk(self):
        out = dry_run("light")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn("--ui office --appearance light --icons boost --scheme Boost Light --tint 255", out.stdout)
        self.assertIn("GTK_THEME=adw-gtk3 ", out.stdout)
        self.assertIn("private GTK config", out.stdout)
        self.assertIn("/mnt/games/libreoffice/try-profile", out.stdout)

    def test_dry_run_reports_extension_reinstall_on_change(self):
        out = dry_run("light")
        self.assertIn("extension: reinstall when changed", out.stdout)

    def test_dark_uses_office_ui_dark_scheme_and_dark_gtk(self):
        out = dry_run("dark")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn("--ui office --appearance dark --icons boost_dark --scheme Boost Dark --tint 255", out.stdout)
        self.assertIn("GTK_THEME=adw-gtk3-dark ", out.stdout)
        self.assertNotIn("private GTK config", out.stdout)

    def test_original_tabbed_has_no_product_theme(self):
        out = dry_run("tabbed")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn("--ui tabbed --appearance dark", out.stdout)
        self.assertNotIn("--scheme", out.stdout)
        self.assertNotIn("--icons", out.stdout)

    def test_custom_profile(self):
        out = dry_run("dark", "--profile", "/tmp/other-profile")
        self.assertIn("--profile /tmp/other-profile", out.stdout)
        self.assertIn("UserInstallation=file:///tmp/other-profile", out.stdout)

    def test_unknown_mode_is_rejected(self):
        out = dry_run("purple")
        self.assertEqual(2, out.returncode)
        self.assertIn("usage", out.stderr.lower())

    def test_font_inter_and_selawik_go_to_the_profile(self):
        for font in ("inter", "selawik"):
            out = dry_run("light", "--font", font)
            self.assertEqual(0, out.returncode, out.stderr)
            self.assertIn("--tint 255 --font %s --profile" % font, out.stdout)

    def test_font_works_with_every_mode(self):
        out = dry_run("--font", "inter", "tabbed")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn("--ui tabbed --appearance dark --font inter --profile", out.stdout)

    def test_no_font_in_the_boost_looks_means_inter(self):
        for mode in ("light", "dark"):
            plain = dry_run(mode)
            self.assertEqual(0, plain.returncode, plain.stderr)
            self.assertEqual(dry_run(mode, "--font", "inter").stdout, plain.stdout, mode)
            self.assertIn("--tint 255 --font inter --profile", plain.stdout, mode)

    def test_no_font_in_the_stock_modes_changes_nothing(self):
        for mode in ("tabbed", "tabbed-light", "compact"):
            plain = dry_run(mode)
            self.assertEqual(0, plain.returncode, plain.stderr)
            self.assertEqual(dry_run(mode, "--font", "system").stdout, plain.stdout, mode)
            self.assertNotIn("--font", plain.stdout, mode)

    def test_system_font_means_no_font_item_in_every_mode(self):
        for mode in ("light", "dark", "tabbed", "tabbed-light", "compact"):
            system = dry_run(mode, "--font", "system")
            self.assertEqual(0, system.returncode, system.stderr)
            self.assertNotIn("--font", system.stdout, mode)

    def test_explicit_font_wins_in_the_boost_looks(self):
        out = dry_run("dark", "--font", "selawik")
        self.assertIn("--tint 255 --font selawik --profile", out.stdout)
        self.assertNotIn("inter", out.stdout)

    def test_unknown_font_is_rejected_with_usage(self):
        for args in (("--font", "comic"), ("light", "--font")):
            out = dry_run(*args)
            self.assertEqual(2, out.returncode, args)
            self.assertIn("usage", out.stderr.lower())
            self.assertIn("--font system|selawik|inter", out.stderr)

    def test_usage_still_names_calc_sh(self):
        out = dry_run("purple")
        self.assertIn("usage: calc.sh [light|dark|tabbed|tabbed-light|compact]", out.stderr)

    def test_calc_sh_is_a_wrapper_of_office_sh(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("office.sh", text)
        self.assertNotIn("soffice", text)


def office_dry_run(*args):
    return subprocess.run(["bash", str(OFFICE), *args, "--dry-run"],
                          capture_output=True, text=True, check=False)


class OfficeLauncherTest(unittest.TestCase):

    def test_writer_light_starts_writer_with_the_writer_profile(self):
        out = office_dry_run("writer", "light")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn("profile: python3 -I product/dev/profile.py --app writer --ui office --appearance light "
                      "--icons boost --scheme Boost Light --tint 255 --font inter "
                      "--profile /mnt/games/libreoffice/try-profile-writer\n", out.stdout)
        self.assertIn("launch: GTK_THEME=adw-gtk3 soffice --writer "
                      "-env:UserInstallation=file:///mnt/games/libreoffice/try-profile-writer\n", out.stdout)
        self.assertNotIn("--calc", out.stdout)

    def test_writer_never_defaults_to_the_calc_profile(self):
        for mode in ("light", "dark", "tabbed", "tabbed-light", "compact"):
            out = office_dry_run("writer", mode)
            self.assertEqual(0, out.returncode, out.stderr)
            self.assertNotRegex(out.stdout, r"try-profile(\s|$)", mode)
            self.assertIn("UserInstallation=file:///mnt/games/libreoffice/try-profile-writer", out.stdout, mode)

    def test_writer_takes_the_same_options(self):
        out = office_dry_run("writer", "dark", "--font", "selawik", "--profile", "/tmp/w-profile")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn("--scheme Boost Dark --tint 255 --font selawik --profile /tmp/w-profile", out.stdout)
        self.assertIn("soffice --writer -env:UserInstallation=file:///tmp/w-profile", out.stdout)

    def test_office_sh_calc_prints_what_calc_sh_prints(self):
        for args in (("light",), ("dark",), ("tabbed",), ("tabbed-light",), ("compact",),
                     ("light", "--font", "selawik"), ("dark", "--profile", "/tmp/other-profile")):
            self.assertEqual(dry_run(*args).stdout, office_dry_run("calc", *args).stdout, args)

    def test_unknown_or_missing_app_is_rejected_with_usage(self):
        for args in (("draw", "light"), ("light",), ()):
            out = office_dry_run(*args)
            self.assertEqual(2, out.returncode, args)
            self.assertIn("usage: office.sh calc|writer|impress ", out.stderr, args)

    def test_impress_light_starts_impress_with_the_impress_profile(self):
        out = office_dry_run("impress", "light")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn("profile: python3 -I product/dev/profile.py --app impress --ui office --appearance light "
                      "--icons boost --scheme Boost Light --tint 255 --font inter "
                      "--profile /mnt/games/libreoffice/try-profile-impress\n", out.stdout)
        self.assertIn("launch: GTK_THEME=adw-gtk3 soffice --impress "
                      "-env:UserInstallation=file:///mnt/games/libreoffice/try-profile-impress\n", out.stdout)
        self.assertNotIn("--calc", out.stdout)
        self.assertNotIn("--writer", out.stdout)

    def test_impress_never_defaults_to_the_calc_or_writer_profile(self):
        for mode in ("light", "dark", "tabbed", "tabbed-light", "compact"):
            out = office_dry_run("impress", mode)
            self.assertEqual(0, out.returncode, out.stderr)
            self.assertNotRegex(out.stdout, r"try-profile(-writer)?(\s|$)", mode)
            self.assertIn("UserInstallation=file:///mnt/games/libreoffice/try-profile-impress", out.stdout, mode)

    def test_impress_takes_the_same_options(self):
        out = office_dry_run("impress", "dark", "--font", "selawik", "--profile", "/tmp/i-profile")
        self.assertEqual(0, out.returncode, out.stderr)
        self.assertIn("--app impress --ui office --appearance dark --icons boost_dark --scheme Boost Dark "
                      "--tint 255 --font selawik --profile /tmp/i-profile", out.stdout)
        self.assertIn("soffice --impress -env:UserInstallation=file:///tmp/i-profile", out.stdout)


if __name__ == "__main__":
    unittest.main()

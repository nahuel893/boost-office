# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""The repository's front door: README links, the three screenshots, the GitHub templates, and no personal data."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ("calc-home-light.png", "writer-home-light.png", "impress-home-light.png")
DOCS = ("README.md", "CONTRIBUTING.md", "product/README.md", "product/docs/install.md", "product/docs/building.md",
        "product/docs/licenses.md", "product/docs/screenshots/README.md")
TEMPLATES = (".github/ISSUE_TEMPLATE/bug_report.md", ".github/ISSUE_TEMPLATE/feature_request.md",
             ".github/ISSUE_TEMPLATE/config.yml", ".github/pull_request_template.md")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|!\[[^\]]*\]\(([^)\s]+)\)")


def git(*args):
    out = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True)
    return out.stdout.decode("utf-8", "replace")


def tracked():
    return set(git("ls-files").splitlines())


def relative_links(doc):
    """Every relative link target of a Markdown file, without its #fragment."""
    text = (ROOT / doc).read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    targets = []
    for match in LINK.finditer(text):
        target = match.group(1) or match.group(2)
        if re.match(r"^([a-z][a-z0-9+.-]*:|#)", target, re.I):
            continue
        targets.append(target.split("#")[0])
    return [t for t in targets if t]


class ReadmeTest(unittest.TestCase):
    def test_every_front_door_document_is_tracked(self):
        files = tracked()
        for doc in DOCS:
            self.assertTrue(doc in files, f"{doc} is not tracked")

    def test_relative_links_resolve_to_tracked_files(self):
        files = tracked()
        for doc in DOCS:
            base = (Path(doc).parent)
            for target in relative_links(doc):
                path = (base / target.rstrip("/")).as_posix()
                parts = []
                for part in path.split("/"):
                    if part == "..":
                        parts.pop()
                    elif part != ".":
                        parts.append(part)
                path = "/".join(parts)
                found = path in files or any(f.startswith(path + "/") for f in files)
                self.assertTrue(found, f"{doc} links to {target}, which is not tracked")

    def test_the_readme_links_the_guides(self):
        links = {Path(t).as_posix() for t in relative_links("README.md")}
        for guide in ("product/docs/install.md", "product/docs/building.md", "product/docs/licenses.md",
                      "CONTRIBUTING.md", "README-LibreOffice.md"):
            self.assertTrue(guide in links, f"the README does not link {guide}")

    def test_the_readme_shows_the_three_apps(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in SHOTS:
            self.assertIn(f"product/docs/screenshots/{name}", text)

    def test_the_readme_carries_the_trademark_notice(self):
        text = re.sub(r"(?m)^>\s?", "", (ROOT / "README.md").read_text(encoding="utf-8"))
        text = " ".join(text.split())
        for phrase in ("not affiliated with or endorsed by The Document Foundation or Microsoft",
                       "LibreOffice is a trademark of The Document Foundation", "trademarks of Microsoft"):
            self.assertIn(phrase, text)

    def test_the_install_guide_documents_the_real_options(self):
        text = (ROOT / "product/docs/install.md").read_text(encoding="utf-8")
        help_text = subprocess.run(["bash", str(ROOT / "product/install/install.sh"), "--help"],
                                   capture_output=True, check=True, text=True).stdout
        for option in re.findall(r"^\s+(--[a-z-]+)", help_text, re.M):
            self.assertIn(f"`{option}", text, option)
        help_text = subprocess.run(["bash", str(ROOT / "product/install/uninstall.sh"), "--help"],
                                   capture_output=True, check=True, text=True).stdout
        for option in re.findall(r"^\s+(--[a-z-]+)", help_text, re.M):
            self.assertIn(f"`{option}", text, option)


class ScreenshotTest(unittest.TestCase):
    def test_the_three_home_crops_are_small_pngs(self):
        files = tracked()
        for name in SHOTS:
            rel = f"product/docs/screenshots/{name}"
            self.assertTrue(rel in files, f"{rel} is not tracked")
            data = (ROOT / rel).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n", rel)
            self.assertLess(len(data), 400 * 1024, rel)

    def test_the_screenshot_index_lists_them(self):
        text = (ROOT / "product/docs/screenshots/README.md").read_text(encoding="utf-8")
        for name in SHOTS:
            self.assertIn(name, text)


class GithubFilesTest(unittest.TestCase):
    def test_the_stock_automation_is_gone(self):
        for rel in (".github/workflows/lockdown.yml", ".github/FUNDING.yml"):
            self.assertFalse((ROOT / rel).exists(), rel)
            self.assertFalse(rel in tracked(), f"{rel} is still tracked")

    def test_no_workflow_is_left_behind(self):
        self.assertEqual([f for f in tracked() if f.startswith(".github/workflows/")], [])

    def test_the_templates_exist(self):
        files = tracked()
        for rel in TEMPLATES:
            self.assertTrue(rel in files, f"{rel} is not tracked")
            self.assertTrue((ROOT / rel).read_text(encoding="utf-8").strip(), rel)

    def test_blank_issues_stay_allowed(self):
        text = (ROOT / ".github/ISSUE_TEMPLATE/config.yml").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^blank_issues_enabled:\s*true\s*$")

    def test_issue_templates_have_front_matter(self):
        for rel in TEMPLATES[:2]:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), rel)
            front = text.split("---\n")[1]
            for key in ("name:", "about:"):
                self.assertIn(key, front, rel)


class PrivacyTest(unittest.TestCase):
    def test_no_tracked_text_file_holds_the_git_email(self):
        email = subprocess.run(["git", "-C", str(ROOT), "config", "user.email"], capture_output=True,
                               text=True).stdout.strip()
        if not email:
            self.skipTest("git config user.email is empty")
        needle = email.lower().encode()
        scope = [f for f in tracked() if f.startswith("product/") or f in ("README.md", "CONTRIBUTING.md")]
        hits = []
        for rel in scope:
            path = ROOT / rel
            if not path.is_file():
                continue
            data = path.read_bytes()
            if b"\0" in data:
                continue
            if needle in data.lower():
                hits.append(rel)
        self.assertEqual(hits, [], "the user's address is in a tracked file")


if __name__ == "__main__":
    unittest.main()

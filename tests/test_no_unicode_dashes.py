import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path.home() / ".agents" / "scripts" / "no_unicode_dashes.py"
SPEC = importlib.util.spec_from_file_location("no_unicode_dashes", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class NoUnicodeDashesTest(unittest.TestCase):
    def test_reports_em_and_en_dashes_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_text("plain -- text\nem \u2014 text\nen \u2013 text\n", encoding="utf-8")
            found = list(MODULE.scan_paths([path]))
        self.assertEqual(len(found), 2)
        self.assertIn("em dash", found[0])
        self.assertIn("en dash", found[1])

    def test_reports_dashes_on_added_git_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            subprocess.run(["git", "-C", root, "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", root, "config", "user.name", "Test"], check=True)
            path = root / "sample.txt"
            path.write_text("plain\n", encoding="utf-8")
            subprocess.run(["git", "-C", root, "add", "sample.txt"], check=True)
            subprocess.run(["git", "-C", root, "commit", "-qm", "base"], check=True)
            path.write_text("plain\nnew \u2014 text\n", encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(root)
                found = list(MODULE.changed_violations())
            finally:
                os.chdir(previous)
        self.assertEqual(found, ["sample.txt:2: em dash found"])

    def _git_repo(self, directory: str) -> Path:
        root = Path(directory)
        subprocess.run(["git", "init", "-q", root], check=True)
        subprocess.run(["git", "-C", root, "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", root, "config", "user.name", "Test"], check=True)
        return root

    def test_path_args_ignore_preexisting_dashes_on_unchanged_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._git_repo(directory)
            path = root / "sample.txt"
            path.write_text("old \u2014 text\n", encoding="utf-8")
            subprocess.run(["git", "-C", root, "add", "sample.txt"], check=True)
            subprocess.run(["git", "-C", root, "commit", "-qm", "base"], check=True)
            path.write_text("old \u2014 text\nnew line\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(MODULE.file_violations(path)), [])

    def test_path_args_flag_dashes_on_added_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._git_repo(directory)
            path = root / "sample.txt"
            path.write_text("plain\n", encoding="utf-8")
            subprocess.run(["git", "-C", root, "add", "sample.txt"], check=True)
            subprocess.run(["git", "-C", root, "commit", "-qm", "base"], check=True)
            path.write_text("plain\nnew \u2014 text\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                cwd=root,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("sample.txt:2: em dash found", result.stderr)


if __name__ == "__main__":
    unittest.main()

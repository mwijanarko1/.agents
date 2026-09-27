import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path.home() / ".agents" / "scripts" / "no_unicode_dashes_hook.py"
SPEC = importlib.util.spec_from_file_location("no_unicode_dashes_hook", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.path.insert(0, str(SCRIPT.parent))
SPEC.loader.exec_module(MODULE)


class NoUnicodeDashesHookTest(unittest.TestCase):
    def test_extracts_direct_and_patch_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            direct = root / "direct.txt"
            patched = root / "patched.txt"
            direct.write_text("clean\n")
            patched.write_text("clean\n")
            payload = {
                "tool_input": {"file_path": str(direct)},
                "command": f"*** Update File: {patched.name}\n",
            }
            self.assertEqual(MODULE.extract_paths(payload, root), [direct.resolve(), patched.resolve()])

    def test_standard_hook_reports_location_to_agent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_text("bad \u2014 text\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, SCRIPT],
                input=json.dumps({"cwd": directory, "tool_input": {"file_path": str(path)}}),
                text=True,
                capture_output=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn(f"{path}:1: em dash found", result.stderr)

    def test_cursor_hook_returns_additional_context(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_text("bad \u2013 text\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, SCRIPT, "--format", "cursor"],
                input=json.dumps({"cwd": directory, "file_path": str(path)}),
                text=True,
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("additional_context", json.loads(result.stdout))

    def test_standard_hook_ignores_preexisting_dashes_on_unchanged_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", root], check=True)
            subprocess.run(["git", "-C", root, "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", root, "config", "user.name", "Test"], check=True)
            path = root / "sample.txt"
            path.write_text("old \u2014 text\n", encoding="utf-8")
            subprocess.run(["git", "-C", root, "add", "sample.txt"], check=True)
            subprocess.run(["git", "-C", root, "commit", "-qm", "base"], check=True)
            path.write_text("old \u2014 text\nnew line\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, SCRIPT],
                input=json.dumps({"cwd": directory, "tool_input": {"file_path": str(path)}}),
                text=True,
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

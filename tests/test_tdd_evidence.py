import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path("/Users/mikhail/.agents/scripts/tdd_evidence.py")


class TddEvidenceTests(unittest.TestCase):
    def test_record_and_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

            env = os.environ.copy()
            env["PWD"] = str(repo)

            red = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(repo),
                    "record-red",
                    "--command",
                    "pytest -k failing_case",
                    "--exit-code",
                    "1",
                ],
                check=False,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(red.returncode, 0, msg=red.stderr)

            green = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(repo),
                    "record-green",
                    "--command",
                    "pytest -k failing_case",
                    "--exit-code",
                    "0",
                ],
                check=False,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(green.returncode, 0, msg=green.stderr)

            status = subprocess.run(
                ["python3", str(SCRIPT), "--repo-root", str(repo), "status"],
                check=False,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(status.returncode, 0, msg=status.stderr)
            payload = json.loads(status.stdout)
            self.assertGreaterEqual(payload.get("red_count", 0), 1)
            self.assertGreaterEqual(payload.get("green_count", 0), 1)
            self.assertIsNone(payload.get("active_exception"))

    def test_record_accepts_task_binding_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(repo),
                    "record-red",
                    "--command",
                    "pytest -k failing_case",
                    "--exit-code",
                    "1",
                    "--task-id",
                    "task-123",
                    "--prompt-hash",
                    "prompt-abc",
                    "--changed-files-hash",
                    "files-def",
                    "--test-target",
                    "pytest -k failing_case",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            recorded = payload["recorded"]
            self.assertEqual(recorded["task_id"], "task-123")
            self.assertEqual(recorded["prompt_hash"], "prompt-abc")
            self.assertEqual(recorded["changed_files_hash"], "files-def")
            self.assertEqual(recorded["test_target"], "pytest -k failing_case")

    def test_exception_requires_reason_and_alternative(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(repo),
                    "except",
                    "--kind",
                    "no_runnable_harness",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_exception_accepts_task_binding_and_expiry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(repo),
                    "except",
                    "--kind",
                    "no_runnable_harness",
                    "--reason",
                    "No test harness exists for generated static output.",
                    "--alternative-verification",
                    "Manual static route check.",
                    "--task-id",
                    "task-123",
                    "--prompt-hash",
                    "prompt-abc",
                    "--changed-files-hash",
                    "files-def",
                    "--expires-at",
                    "2026-05-08T00:00:00Z",
                    "--allowed-files",
                    "vercel.json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            exception = payload["exception"]
            self.assertEqual(exception["task_id"], "task-123")
            self.assertEqual(exception["prompt_hash"], "prompt-abc")
            self.assertEqual(exception["changed_files_hash"], "files-def")
            self.assertEqual(exception["expires_at"], "2026-05-08T00:00:00Z")
            self.assertEqual(exception["allowed_files"], ["vercel.json"])


if __name__ == "__main__":
    unittest.main()

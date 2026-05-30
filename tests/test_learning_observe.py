import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


OBSERVE = Path("/Users/mikhail/.agents/hooks/learning/observe.py")


class LearningObserveTests(unittest.TestCase):
    def test_redacts_sensitive_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_root = Path(tmpdir) / "state"
            state_root.mkdir(parents=True, exist_ok=True)

            payload = {
                "prompt": "always prefer strict validation",
                "tool_name": "Bash",
                "tool_input": {"command": "echo sk-abc1234567890TOKEN"},
                "tool_response": "Authorization: Bearer secretvalue1234567890",
                "cwd": tmpdir,
            }
            result = subprocess.run(
                ["python3", str(OBSERVE)],
                input=json.dumps(payload),
                text=True,
                env={**os.environ, "AGENTS_LEARNING_STATE_ROOT": str(state_root)},
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            global_obs = state_root / "global" / "preferences" / "observations.jsonl"
            self.assertTrue(global_obs.exists())
            data = global_obs.read_text(encoding="utf-8")
            self.assertNotIn("sk-abc1234567890TOKEN", data)
            self.assertNotIn("secretvalue1234567890", data)
            self.assertIn("[REDACTED]", data)

    def test_project_scoped_observation_is_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "remote", "add", "origin", "https://github.com/example/repo.git"],
                cwd=repo,
                check=True,
                capture_output=True,
            )

            state_root = Path(tmpdir) / "state"
            payload = {
                "prompt": "use x instead of y",
                "tool_name": "Edit",
                "tool_input": {"file_path": "foo.py"},
                "tool_response": "ok",
                "cwd": str(repo),
            }
            result = subprocess.run(
                ["python3", str(OBSERVE)],
                input=json.dumps(payload),
                text=True,
                env={**os.environ, "AGENTS_LEARNING_STATE_ROOT": str(state_root)},
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            projects_dir = state_root / "projects"
            self.assertTrue(projects_dir.exists())
            project_dirs = [item for item in projects_dir.iterdir() if item.is_dir()]
            self.assertTrue(project_dirs)
            observations = project_dirs[0] / "observations.jsonl"
            self.assertTrue(observations.exists())

            db_path = state_root / "state.db"
            self.assertTrue(db_path.exists())
            search = subprocess.run(
                [
                    "python3",
                    "/Users/mikhail/.agents/scripts/agent_learning.py",
                    "search",
                    "foo.py",
                    "--state-root",
                    str(state_root),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(search.returncode, 0, msg=search.stderr)
            self.assertIn("foo.py", search.stdout)

    def test_user_prompt_submit_records_prompt_kind(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_root = Path(tmpdir) / "state"
            payload = {
                "prompt": "Always prefer candidate review before memory changes.",
                "event": "UserPromptSubmit",
                "cwd": tmpdir,
                "session_id": "s1",
            }
            result = subprocess.run(
                ["python3", str(OBSERVE)],
                input=json.dumps(payload),
                text=True,
                env={**os.environ, "AGENTS_LEARNING_STATE_ROOT": str(state_root), "GUARDRAIL_EVENT": "UserPromptSubmit"},
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            observations = state_root / "global" / "observations.jsonl"
            rows = [json.loads(line) for line in observations.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["kind"], "user_prompt")
            self.assertIn("candidate review", rows[0]["prompt"])

            search = subprocess.run(
                [
                    "python3",
                    "/Users/mikhail/.agents/scripts/agent_learning.py",
                    "search",
                    "candidate review",
                    "--state-root",
                    str(state_root),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(search.returncode, 0, msg=search.stderr)
            self.assertIn("candidate review", search.stdout)


if __name__ == "__main__":
    unittest.main()

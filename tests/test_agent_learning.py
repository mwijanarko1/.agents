import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "agent_learning.py"
HOOK = ROOT / "hooks" / "bin" / "learning-observe.sh"


class AgentLearningTests(unittest.TestCase):
    def run_cli(self, cwd, state_root, *args):
        env = {**os.environ, "AGENTS_LEARNING_STATE_ROOT": str(state_root)}
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_hook_and_commands_are_project_scoped_without_session_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
            subprocess.run(["git", "remote", "add", "origin", "https://example.test/project.git"], cwd=repo, check=True)
            state = root / "state"
            payload = {
                "event": "UserPromptSubmit",
                "prompt": "Always prefer strict validation",
                "cwd": str(repo),
                "tool_input": {"command": "echo sk-test-secret-1234567890"},
            }
            result = subprocess.run([str(HOOK)], input=json.dumps(payload), text=True, env={**os.environ, "AGENTS_LEARNING_STATE_ROOT": str(state)}, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            projects = list((state / "projects").iterdir())
            self.assertEqual(len(projects), 1)
            observations = (projects[0] / "observations.jsonl").read_text()
            self.assertNotIn("sk-test-secret-1234567890", observations)
            self.assertNotIn("tool_input", observations)
            self.assertNotIn("tool_output", observations)
            self.assertFalse((state / "state.db").exists())
            status = self.run_cli(repo, state, "status")
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertEqual(json.loads(status.stdout)["project_observations"], 1)
            analyzed = self.run_cli(repo, state, "analyze")
            self.assertEqual(analyzed.returncode, 0, analyzed.stderr)
            self.assertTrue(list((projects[0] / "instincts").glob("*.yaml")))

    def test_export_import_promote_and_prune_use_local_instincts_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
            state = root / "state"
            payload = {"prompt": "Never skip tests", "cwd": str(repo)}
            subprocess.run([str(HOOK)], input=json.dumps(payload), text=True, env={**os.environ, "AGENTS_LEARNING_STATE_ROOT": str(state)}, check=True)
            self.assertEqual(self.run_cli(repo, state, "analyze").returncode, 0)
            exported = root / "instincts.yaml"
            result = self.run_cli(repo, state, "export", "--output", str(exported))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("instincts", exported.read_text())
            self.assertEqual(self.run_cli(repo, state, "promote").returncode, 0)
            self.assertTrue(list((state / "global" / "preferences").glob("*.yaml")))
            self.assertEqual(self.run_cli(repo, state, "import", str(exported)).returncode, 0)
            self.assertEqual(self.run_cli(repo, state, "projects").returncode, 0)
            self.assertEqual(self.run_cli(repo, state, "prune", "--days", "0").returncode, 0)

    def test_learning_state_redacts_json_secrets_and_remote_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
            remote_secret = "sk-remote-secret-1234567890"
            json_secret = "json-token-secret-1234567890"
            structured_secret = "short-secret"
            subprocess.run(
                ["git", "remote", "add", "origin", f"https://user:{remote_secret}@example.test/project.git"],
                cwd=repo,
                check=True,
            )
            state = root / "state"
            payload = {
                "prompt": "Always keep observations local",
                "cwd": str(repo),
                "tool_input": {
                    "config": f'{{"token":"{json_secret}"}}',
                    "token": structured_secret,
                },
            }
            result = subprocess.run(
                [str(HOOK)],
                input=json.dumps(payload),
                text=True,
                env={**os.environ, "AGENTS_LEARNING_STATE_ROOT": str(state)},
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            project_dir = next((state / "projects").iterdir())
            observations = (project_dir / "observations.jsonl").read_text()
            registry = (state / "projects.json").read_text()
            self.assertNotIn(json_secret, observations)
            self.assertNotIn(structured_secret, observations)
            self.assertNotIn(remote_secret, registry)

    def test_non_git_directories_are_path_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "plain-project"
            project.mkdir()
            state = root / "state"
            payload = {"event": "UserPromptSubmit", "prompt": "Always use native APIs", "cwd": str(project)}
            result = subprocess.run(
                [str(HOOK)],
                input=json.dumps(payload),
                text=True,
                env={**os.environ, "AGENTS_LEARNING_STATE_ROOT": str(state)},
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            projects = list((state / "projects").iterdir())
            self.assertEqual(len(projects), 1)
            registry = json.loads((state / "projects.json").read_text())
            self.assertEqual(registry["projects"][0]["project_root"], str(project.resolve()))
            self.assertFalse((state / "global" / "observations.jsonl").exists())


if __name__ == "__main__":
    unittest.main()

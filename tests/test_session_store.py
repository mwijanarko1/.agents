import os
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, "/Users/mikhail/.agents")

from scripts.session_store import SessionStore


class SessionStoreTests(unittest.TestCase):
    def test_observation_is_searchable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "state.db"
            store = SessionStore(db_path)

            store.add_observation(
                session_id="s1",
                project_id="p1",
                project_name="repo",
                project_root="/tmp/repo",
                event="PostToolUse",
                tool_name="Edit",
                prompt="Add JWT auth using jose middleware",
                tool_input={"file_path": "src/middleware/auth.ts"},
                tool_output="Implemented jose token validation",
            )

            results = store.search("jose token validation", project_id="p1", limit=5)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["session_id"], "s1")

    def test_bash_output_is_not_overindexed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "state.db"
            store = SessionStore(db_path)

            store.add_observation(
                session_id="s1",
                project_id="p1",
                project_name="repo",
                project_root="/tmp/repo",
                event="PostToolUse",
                kind="tool_result",
                tool_name="Bash",
                tool_input={"command": "sed -n '1,200p' node_modules/example/internal.js"},
                tool_output="rare_internal_symbol_from_large_dump",
            )

            self.assertEqual(store.search("rare_internal_symbol_from_large_dump", project_id="p1"), [])
            self.assertEqual(len(store.search("node_modules example", project_id="p1")), 1)

    def test_project_profile_extracts_files_and_terms(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "state.db"
            store = SessionStore(db_path)

            store.add_observation(
                session_id="s1",
                project_id="p1",
                project_name="repo",
                project_root="/tmp/repo",
                event="PostToolUse",
                tool_name="Edit",
                prompt="Fix auth middleware tests",
                tool_input={"file_path": "src/middleware/auth.ts"},
                tool_output="auth middleware tests now pass",
            )
            store.add_observation(
                session_id="s2",
                project_id="p1",
                project_name="repo",
                project_root="/tmp/repo",
                event="PostToolUse",
                tool_name="Bash",
                prompt="Run auth middleware tests",
                tool_input={"command": "pytest tests/auth_test.py"},
                tool_output="passed",
            )

            profile = store.project_profile("p1")
            self.assertEqual(profile["project_id"], "p1")
            self.assertTrue(any(item["file"] == "src/middleware/auth.ts" for item in profile["top_files"]))
            self.assertTrue(any(item["term"] == "auth" for item in profile["top_terms"]))

    def test_context_prefers_prompt_over_bash_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "state.db"
            store = SessionStore(db_path)

            store.add_observation(
                session_id="s1",
                project_id="p1",
                project_name="repo",
                project_root="/tmp/repo",
                event="PostToolUse",
                kind="tool_result",
                tool_name="Bash",
                tool_input={"command": "rg memory workflow"},
                tool_output="memory workflow raw bash output",
            )
            store.add_observation(
                session_id="s1",
                project_id="p1",
                project_name="repo",
                project_root="/tmp/repo",
                event="UserPromptSubmit",
                kind="user_prompt",
                prompt="Memory workflow should use reviewable candidates.",
            )

            context = store.build_context("memory workflow", project_id="p1", budget_chars=1000)
            self.assertLess(context.find("reviewable candidates"), context.find("raw bash output"))


if __name__ == "__main__":
    unittest.main()

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, "/Users/mikhail/.agents")

from scripts.lib import agent_validators
from scripts import validate_agent_policy


class AgentValidatorsTests(unittest.TestCase):
    def test_empty_skill_is_reported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skill_dir = root / "skills" / "empty-skill"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text("", encoding="utf-8")

            errors = agent_validators.validate_skill_non_empty(root / "skills")
            self.assertTrue(any("empty-skill" in item for item in errors))

    def test_subagent_frontmatter_is_required(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agent_dir = root / "agents"
            agent_dir.mkdir(parents=True, exist_ok=True)
            (agent_dir / "example.md").write_text("no frontmatter", encoding="utf-8")

            errors = agent_validators.validate_subagent_frontmatter(agent_dir)
            self.assertTrue(any("example.md" in item for item in errors))

    def test_docs_frontmatter_requires_summary_and_read_when(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (docs / "missing.md").write_text("# Missing metadata\n", encoding="utf-8")
            (docs / "ready.md").write_text(
                "---\nsummary: Good docs\nread_when: When testing docs routing.\n---\n# Ready\n",
                encoding="utf-8",
            )

            errors = agent_validators.validate_docs_frontmatter(root)
            self.assertTrue(any("missing.md" in item for item in errors))
            self.assertFalse(any("ready.md" in item for item in errors))

    def test_skill_catalog_paths_are_validated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifests_dir = root / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            catalog_path = manifests_dir / "skill-catalog.json"
            catalog = {
                "version": 1,
                "skills": [
                    {
                        "name": "missing-skill",
                        "path": "skills/missing-skill/SKILL.md",
                        "origin": "ECC",
                        "source": "https://example.com",
                    }
                ],
            }
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

            errors = agent_validators.validate_skill_catalog(root, catalog_path)
            self.assertTrue(any("missing-skill" in item for item in errors))

    def test_skill_routing_index_requires_existing_skill_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skills").mkdir(parents=True, exist_ok=True)
            manifests_dir = root / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            index_path = manifests_dir / "skill-routing-index.json"
            index_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_at": "2026-04-27T00:00:00Z",
                        "source_root": str(root / "skills"),
                        "skills": [
                            {
                                "name": "missing-skill",
                                "path": "skills/missing-skill/SKILL.md",
                                "description": "Missing",
                                "category": "utility",
                                "priority": "utility",
                                "tokens": {"frontmatter_chars": 10, "skill_chars": 10},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            errors = agent_validators.validate_skill_routing_index(root, index_path)
            self.assertTrue(any("missing-skill" in item for item in errors))

    def test_skill_routing_index_requires_all_canonical_skills(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skill_dir = root / "skills" / "known-skill"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text("---\nname: known-skill\ndescription: Known\n---\n", encoding="utf-8")
            manifests_dir = root / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            index_path = manifests_dir / "skill-routing-index.json"
            index_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_at": "2026-04-27T00:00:00Z",
                        "source_root": str(root / "skills"),
                        "skills": [],
                    }
                ),
                encoding="utf-8",
            )

            errors = agent_validators.validate_skill_routing_index(root, index_path)
            self.assertTrue(any("missing canonical skill" in item for item in errors))

    def test_skill_routing_index_rejects_unknown_requires_one_of(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skill_dir = root / "skills" / "known-skill"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text("---\nname: known-skill\ndescription: Known\n---\n", encoding="utf-8")
            manifests_dir = root / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            index_path = manifests_dir / "skill-routing-index.json"
            index_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_at": "2026-04-27T00:00:00Z",
                        "source_root": str(root / "skills"),
                        "skills": [
                            {
                                "name": "known-skill",
                                "path": "skills/known-skill/SKILL.md",
                                "description": "Known",
                                "category": "utility",
                                "priority": "utility",
                                "tokens": {"frontmatter_chars": 10, "skill_chars": 10},
                                "requires_one_of": ["missing-skill"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            errors = agent_validators.validate_skill_routing_index(root, index_path)
            self.assertTrue(any("unknown requires_one_of" in item for item in errors))

    def test_skill_routing_index_rejects_secondary_as_primary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skill_dir = root / "skills" / "design-md-gallery"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text("---\nname: design-md-gallery\ndescription: Gallery\n---\n", encoding="utf-8")
            manifests_dir = root / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            index_path = manifests_dir / "skill-routing-index.json"
            index_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_at": "2026-04-27T00:00:00Z",
                        "source_root": str(root / "skills"),
                        "skills": [
                            {
                                "name": "design-md-gallery",
                                "path": "skills/design-md-gallery/SKILL.md",
                                "description": "Gallery",
                                "category": "design",
                                "priority": "primary",
                                "tokens": {"frontmatter_chars": 10, "skill_chars": 10},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            errors = agent_validators.validate_skill_routing_index(root, index_path)
            self.assertTrue(any("secondary-only" in item for item in errors))

    def test_sync_manifest_missing_source_is_reported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifests_dir = root / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = manifests_dir / "sync-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "mappings": [
                            {
                                "source": "missing-file.md",
                                "targets": [{"path": "../target.md", "type": "symlink"}],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            errors = agent_validators.validate_sync_manifest(root, manifest_path)
            self.assertTrue(any("Sync source missing" in item for item in errors))

    def test_hook_install_manifest_reports_missing_required_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "codex-hooks.json"
            config_path.write_text(
                json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"command": "other-hook.sh"}]}]}}),
                encoding="utf-8",
            )
            manifest_path = root / "hook-install-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "tools": [
                            {
                                "name": "codex",
                                "config": str(config_path),
                                "required_hooks": [
                                    {"event": "PreToolUse", "command_contains": "codex-preflight.sh"}
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            errors = agent_validators.validate_hook_install_manifest(root, manifest_path)
            self.assertTrue(any("codex-preflight.sh" in item for item in errors))

    def test_personal_path_leak_is_reported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            sample = docs / "sample.md"
            sample.write_text("Use /Users/other-user/private/path for setup", encoding="utf-8")

            errors = agent_validators.validate_no_personal_paths(
                root=root,
                allowed_prefixes=[str(root)],
                targets=["docs"],
            )
            self.assertTrue(any("Personal path leak" in item for item in errors))

    def test_output_economy_policy_is_required(self):
        errors = validate_agent_policy.validate_schema({})
        self.assertTrue(any("output_economy" in item for item in errors))

    def test_shared_references_report_missing_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agents = root / "agents"
            agents.mkdir(parents=True, exist_ok=True)
            (agents / "example.md").write_text(
                "## Required Skills\n\n- `missing-skill` — required before substantive output.\n",
                encoding="utf-8",
            )

            errors = agent_validators.validate_shared_references(root)
            self.assertTrue(any("missing-skill" in item for item in errors))

    def test_shared_references_accept_existing_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skill_dir = root / "skills" / "coding-standards"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text("---\nname: coding-standards\ndescription: Known\n---\n", encoding="utf-8")
            agents = root / "agents"
            agents.mkdir(parents=True, exist_ok=True)
            (agents / "example.md").write_text(
                "## Required Skills\n\nLoad `coding-standards` before substantive output.\n",
                encoding="utf-8",
            )

            errors = agent_validators.validate_shared_references(root)
            self.assertFalse(errors)

    def test_shared_references_report_missing_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (docs / "deploy.md").write_text("Run `skills/missing/scripts/run.sh` after build.", encoding="utf-8")

            errors = agent_validators.validate_shared_references(root)
            self.assertTrue(any("skills/missing/scripts/run.sh" in item for item in errors))

    def test_supply_chain_recipes_report_forbidden_executor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agents = root / "agents"
            agents.mkdir(parents=True, exist_ok=True)
            (agents / "deploy.md").write_text("Run `npx playwright test` before deploy.", encoding="utf-8")
            policy = {"supply_chain_hardening": {"forbid_runtime_executors": ["npx"]}}

            errors = agent_validators.validate_supply_chain_recipes(root, policy)
            self.assertTrue(any("npx playwright test" in item for item in errors))

    def test_supply_chain_recipes_allow_comment_suppresses_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (docs / "notes.md").write_text(
                "<!-- agent-policy: allow-forbidden-command because: historical example -->\n"
                "Do not copy old `npx playwright test` examples.\n",
                encoding="utf-8",
            )
            policy = {"supply_chain_hardening": {"forbid_runtime_executors": ["npx"]}}

            errors = agent_validators.validate_supply_chain_recipes(root, policy)
            self.assertFalse(errors)

    def test_subagent_policy_skill_alignment_reports_drift(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agents = root / "agents"
            agents.mkdir(parents=True, exist_ok=True)
            (agents / "backend-architect.md").write_text(
                "Treat these local skill files as canonical:\n"
                "- `/Users/mikhail/.agents/skills/backend-architecture/SKILL.md`\n",
                encoding="utf-8",
            )
            policy = {
                "capability_clusters": {
                    "backend-architect": {
                        "skills": ["backend-architecture", "coding-standards"],
                    }
                },
                "subagents": {"directory": "agents"},
            }

            errors = agent_validators.validate_subagent_policy_skill_alignment(root, policy)
            self.assertTrue(any("coding-standards" in item for item in errors))

    def test_optional_domain_subagents_do_not_need_required_membership(self):
        policy = {
            "subagents": {"required": ["backend-architect"]},
            "domain_subagents": {"game": {"optional": ["game-creator"]}},
            "subagent_routing": {
                "default": "native_subagents_first",
                "route_by_task_intent": {
                    "backend": "backend-architect",
                    "game_creation": "game-creator",
                },
                "when_to_use": ["specialist_focus"],
                "when_not_to_use": ["tiny_tasks"],
            },
        }

        errors = validate_agent_policy.validate_subagent_routing(policy)
        self.assertFalse(errors)

    def test_output_economy_rejects_gimmick_voice_policy_gap(self):
        policy = {
            "output_economy": {
                "default": "professional_concise",
                "style": "normal_grammar_no_gimmick_voice",
                "spend_tokens_on": ["code", "verification"],
                "avoid": ["filler"],
                "progress_updates": {"max_sentences": 2, "must_include": ["useful_context"]},
                "final_responses": {"default": "concise", "prefer": ["verification"]},
                "subagents": {"inherit": True, "final_output": "findings_changes_verification_only"},
            }
        }

        errors = validate_agent_policy.validate_output_economy(policy)
        self.assertTrue(any("forced_persona" in item for item in errors))


if __name__ == "__main__":
    unittest.main()

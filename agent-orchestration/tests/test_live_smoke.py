import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for module_name, filename in (
    ("eksamio_agent_runner", "eksamio_agent_runner.py"),
    ("codex_sdk_executor", "codex_sdk_executor.py"),
):
    if module_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(module_name, ROOT / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

SPEC = importlib.util.spec_from_file_location("live_smoke", ROOT / "live_smoke.py")
SMOKE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SMOKE
SPEC.loader.exec_module(SMOKE)
RUNNER = sys.modules["eksamio_agent_runner"]

CHECK = "python3 -c \"print('ok')\""


def task_for(sha, **overrides):
    value = {
        "schema_version": "0.1",
        "repository": "niknikdym-hue/ege",
        "base_sha": sha,
        "target_branch": "brain/live-smoke-test",
        "goal": "Perform one bounded smoke edit",
        "allowed_scope": ["agent-orchestration/**"],
        "non_goals": ["merge", "deploy", "production writes"],
        "acceptance_checks": [CHECK],
        "requested_actions": ["edit", "test"],
        "stop_conditions": ["scope mismatch"],
    }
    value.update(overrides)
    return value


def context_for(sha, **overrides):
    value = {
        "schema_version": "0.1",
        "repository": "niknikdym-hue/ege",
        "base_sha": sha,
        "target_branch": "brain/live-smoke-test",
        "task_brief": "Bounded development-agent smoke only",
        "evidence": ["exact local checkout"],
        "max_allowed_scope": ["agent-orchestration/**"],
        "allowed_acceptance_checks": [CHECK],
    }
    value.update(overrides)
    return value


class FakeAstra:
    def __init__(self, task, *, decision="PASS"):
        self.task = task
        self.decision_name = decision
        self.plan_calls = 0
        self.review_calls = 0

    def plan(self, context):
        self.plan_calls += 1
        return {
            "output": self.task,
            "provider_metadata": {"requested_model": "gpt-6-astra", "usage": {"input_tokens": 10}},
        }

    def review(self, context):
        self.review_calls += 1
        return {
            "output": {
                "schema_version": "0.1",
                "decision": self.decision_name,
                "reviewed_sha": context["reviewed_sha"],
                "invariants": {
                    "false_exact_mastery_zero": True,
                    "server_owned_truth_preserved": True,
                    "owner_gates_preserved": True,
                },
                "evidence": ["bounded mocked evidence"],
                "reason": "Mocked bounded review",
                "next_action": "Persist artifact",
            },
            "provider_metadata": {"requested_model": "gpt-6-astra", "usage": {"output_tokens": 10}},
        }


class FakeCodex:
    def __init__(self, root, *, changed_path="agent-orchestration/smoke-output.txt"):
        self.root = pathlib.Path(root)
        self.changed_path = changed_path
        self.calls = 0

    def execute(self, task, *, dry_run):
        self.calls += 1
        if dry_run:
            raise AssertionError("live harness must not call Codex in dry-run mode")
        target = self.root / self.changed_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("bounded smoke output\n", encoding="utf-8")
        return {
            "status": "completed",
            "executor": "fake-codex",
            "final_response": "bounded edit complete",
            "usage": {"input_tokens": 5, "output_tokens": 5},
        }


class LiveSmokeHarnessTests(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(temp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Eksamio Test"], cwd=root, check=True)
        (root / "README.md").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "test"], cwd=root, check=True)
        subprocess.run(["git", "checkout", "-q", "-b", "brain/live-smoke-test"], cwd=root, check=True)
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        self.addCleanup(temp.cleanup)
        return root, sha

    def test_owner_flag_blocks_before_astra(self):
        root, sha = self.make_repo()
        astra = FakeAstra(task_for(sha))
        harness = SMOKE.LiveSmokeHarness(repo_root=root, astra=astra, codex=FakeCodex(root))
        with self.assertRaises(RUNNER.PermissionDenied):
            harness.run(context_for(sha), owner_authorize_live_provider=False)
        self.assertEqual(astra.plan_calls, 0)

    def test_astra_cannot_change_exact_base_sha(self):
        root, sha = self.make_repo()
        astra = FakeAstra(task_for("b" * 40))
        codex = FakeCodex(root)
        harness = SMOKE.LiveSmokeHarness(repo_root=root, astra=astra, codex=codex)
        with self.assertRaises(SMOKE.LiveSmokeError):
            harness.run(context_for(sha), owner_authorize_live_provider=True)
        self.assertEqual(codex.calls, 0)

    def test_provider_authorization_does_not_grant_deploy(self):
        root, sha = self.make_repo()
        astra = FakeAstra(task_for(sha, requested_actions=["deploy"]))
        codex = FakeCodex(root)
        harness = SMOKE.LiveSmokeHarness(repo_root=root, astra=astra, codex=codex)
        with self.assertRaises(RUNNER.PermissionDenied):
            harness.run(context_for(sha), owner_authorize_live_provider=True)
        self.assertEqual(codex.calls, 0)

    def test_unallowlisted_acceptance_command_is_rejected(self):
        root, sha = self.make_repo()
        astra = FakeAstra(task_for(sha, acceptance_checks=["python3 -c \"print('different')\""]))
        codex = FakeCodex(root)
        harness = SMOKE.LiveSmokeHarness(repo_root=root, astra=astra, codex=codex)
        with self.assertRaises(SMOKE.LiveSmokeError):
            harness.run(context_for(sha), owner_authorize_live_provider=True)
        self.assertEqual(codex.calls, 0)

    def test_out_of_scope_codex_change_fails_closed(self):
        root, sha = self.make_repo()
        harness = SMOKE.LiveSmokeHarness(
            repo_root=root,
            astra=FakeAstra(task_for(sha)),
            codex=FakeCodex(root, changed_path="outside.txt"),
        )
        with self.assertRaises(SMOKE.LiveSmokeError):
            harness.run(context_for(sha), owner_authorize_live_provider=True)

    def test_dirty_workspace_is_rejected_before_astra(self):
        root, sha = self.make_repo()
        (root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        astra = FakeAstra(task_for(sha))
        harness = SMOKE.LiveSmokeHarness(repo_root=root, astra=astra, codex=FakeCodex(root))
        with self.assertRaises(SMOKE.LiveSmokeError):
            harness.run(context_for(sha), owner_authorize_live_provider=True)
        self.assertEqual(astra.plan_calls, 0)

    def test_success_returns_hash_bound_artifact_without_moving_head(self):
        root, sha = self.make_repo()
        astra = FakeAstra(task_for(sha))
        codex = FakeCodex(root)
        harness = SMOKE.LiveSmokeHarness(repo_root=root, astra=astra, codex=codex)
        artifact = harness.run(context_for(sha), owner_authorize_live_provider=True)
        self.assertEqual(artifact["status"], "COMPLETED")
        self.assertEqual(artifact["decision"]["decision"], "PASS")
        self.assertEqual(artifact["base_sha"], sha)
        self.assertEqual(artifact["changed_paths"], ["agent-orchestration/smoke-output.txt"])
        self.assertEqual(len(artifact["diff_sha256"]), 64)
        current = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        self.assertEqual(current, sha)

    def test_artifact_writer_refuses_checkout_path(self):
        root, sha = self.make_repo()
        with self.assertRaises(SMOKE.LiveSmokeError):
            SMOKE._write_artifact(root / "artifact.json", {"base_sha": sha}, root)


if __name__ == "__main__":
    unittest.main()

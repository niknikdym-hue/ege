import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RUNNER_SPEC = importlib.util.spec_from_file_location("eksamio_agent_runner", ROOT / "eksamio_agent_runner.py")
RUNNER = importlib.util.module_from_spec(RUNNER_SPEC)
sys.modules[RUNNER_SPEC.name] = RUNNER
RUNNER_SPEC.loader.exec_module(RUNNER)

SDK_SPEC = importlib.util.spec_from_file_location("codex_sdk_executor", ROOT / "codex_sdk_executor.py")
SDK = importlib.util.module_from_spec(SDK_SPEC)
sys.modules[SDK_SPEC.name] = SDK
SDK_SPEC.loader.exec_module(SDK)


def task_for(sha, **overrides):
    value = {
        "schema_version": "0.1",
        "repository": "niknikdym-hue/ege",
        "base_sha": sha,
        "target_branch": "brain/example",
        "goal": "Implement one bounded unit",
        "allowed_scope": ["agent-orchestration/**"],
        "non_goals": ["merge", "deploy"],
        "acceptance_checks": ["python3 -m unittest"],
        "requested_actions": ["edit", "test"],
        "stop_conditions": ["branch moved incompatibly"],
    }
    value.update(overrides)
    return value


class CodexSdkExecutorTests(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(temp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Eksamio Test"], cwd=root, check=True)
        (root / "README.md").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "test"], cwd=root, check=True)
        subprocess.run(["git", "checkout", "-q", "-b", "brain/example"], cwd=root, check=True)
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        self.addCleanup(temp.cleanup)
        return root, sha

    def test_dry_run_binds_exact_checkout_without_sdk_import(self):
        root, sha = self.make_repo()
        result = SDK.CodexSdkExecutorAdapter(repo_root=root).execute(task_for(sha), dry_run=True)
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertEqual(result["executor"], "openai-codex")

    def test_fails_closed_if_branch_moved(self):
        root, _ = self.make_repo()
        with self.assertRaises(RUNNER.ProviderError):
            SDK.CodexSdkExecutorAdapter(repo_root=root).execute(task_for("b" * 40), dry_run=True)

    def test_fails_closed_on_wrong_branch(self):
        root, sha = self.make_repo()
        with self.assertRaises(RUNNER.ProviderError):
            SDK.CodexSdkExecutorAdapter(repo_root=root).execute(
                task_for(sha, target_branch="brain/wrong"), dry_run=True
            )

    def test_live_execution_requires_api_key_before_sdk_import(self):
        root, sha = self.make_repo()
        adapter = SDK.CodexSdkExecutorAdapter(repo_root=root, api_key=None)
        adapter.api_key = None
        with self.assertRaises(RUNNER.ProviderError):
            adapter.execute(task_for(sha), dry_run=False)

    def test_dangerous_action_is_rejected_before_live_provider(self):
        root, sha = self.make_repo()
        with self.assertRaises(RUNNER.PermissionDenied):
            SDK.CodexSdkExecutorAdapter(repo_root=root, api_key="unused").execute(
                task_for(sha, requested_actions=["deploy"]), dry_run=False
            )

    def test_owner_grant_is_action_specific(self):
        root, sha = self.make_repo()
        adapter = SDK.CodexSdkExecutorAdapter(
            repo_root=root, api_key="unused", owner_authorized_actions=["deploy"]
        )
        with self.assertRaises(RUNNER.ProviderError):
            adapter.execute(task_for(sha, requested_actions=["deploy"]), dry_run=False)


if __name__ == "__main__":
    unittest.main()

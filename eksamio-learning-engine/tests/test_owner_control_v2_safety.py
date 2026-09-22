import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / ".github/workflows/owner-agent-task-v2.yml"
BATCH = ROOT / ".github/workflows/owner-agent-batch-v2.yml"
PROXY = ROOT / "eksamio-learning-engine/project-control/owner_control_budget_proxy.mjs"


class OwnerControlV2SafetyTest(unittest.TestCase):
    def test_budget_proxy_self_test_and_client_auth(self):
        result = subprocess.run(
            ["node", str(PROXY), "--self-test"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("OWNER_CONTROL_BUDGET_PROXY_SELFTEST=PASS", result.stdout)
        text = PROXY.read_text()
        self.assertIn("OWNER_PROXY_CLIENT_TOKEN is required", text)
        self.assertIn("clientAuthorized(req.headers.authorization, clientToken)", text)
        self.assertIn("hard task budget exhausted before provider call", text)
        self.assertIn("OWNER_PROXY_UPSTREAM_URL is allowed only in loopback test mode", text)

    def test_codex_never_receives_real_openai_provider_key(self):
        yml = TASK.read_text()
        start = yml.index("- name: Install pinned Codex CLI with retry-zero budget-proxy provider")
        end = yml.index("- name: Extract untrusted candidate patch only", start)
        codex = yml[start:end]
        self.assertNotIn("secrets.OPENAI_API_KEY", codex)
        self.assertIn("steps.executor_proxy.outputs.client_token", codex)
        self.assertIn("base_url = \"http://127.0.0.1:8787/v1\"", codex)
        self.assertIn("npm install -g @openai/codex@0.154.0", codex)
        self.assertIn("codex exec", codex)
        self.assertIn("--no-new-privs", codex)
        self.assertIn("--bounding-set=-all", codex)
        self.assertIn("API_CODEX_PROVIDER_REQUESTS=1", codex)
        self.assertIn("--ephemeral -", codex)
        self.assertIn("< /tmp/codex-prompt.txt", codex)
        self.assertNotIn('prompt="$(cat /tmp/codex-prompt.txt)"', codex)

    def test_codex_retry_policy_is_explicitly_zero(self):
        yml = TASK.read_text()
        self.assertIn("request_max_retries = 0", yml)
        self.assertIn("stream_max_retries = 0", yml)
        self.assertIn("CODEX_REQUEST_MAX_RETRIES=0", yml)
        self.assertIn("CODEX_STREAM_MAX_RETRIES=0", yml)

    def test_owner_v2_isolated_from_merge_deploy_and_production_commands(self):
        task = TASK.read_text()
        batch = BATCH.read_text()
        combined = task + "\n" + batch
        for forbidden in (
            "gh pr merge",
            "markPullRequestReadyForReview",
            "git push origin HEAD:main",
            "actions/deploy-pages",
            "yc serverless",
            "robokassa",
        ):
            self.assertNotIn(forbidden, combined.lower())
        self.assertIn("'auto_retry':False", batch)
        self.assertIn("'sequential':True", batch)
        self.assertIn("NO_AUTO_RETRY: true", batch)
        self.assertIn("NO_AUTO_MERGE_DEPLOY_READY: true", batch)

    def test_budget_caps_remain_fail_closed(self):
        task = TASK.read_text()
        batch = BATCH.read_text()
        self.assertIn("task budget must be $0.05..$3.00", task)
        self.assertIn("package OpenAI budget must be $0.00..$3.00", batch)
        self.assertIn("AI package requires at least $0.10 hard OpenAI budget", batch)

    def test_registered_allowed_paths_are_hard_enforced(self):
        yml = TASK.read_text()
        self.assertIn("If task.allowed_paths is non-empty, change only those exact paths.", yml)
        self.assertIn("Registered allowed_paths missing from frozen worktree", yml)
        self.assertIn("Candidate escaped registered allowed_paths", yml)
        self.assertIn("REGISTERED_ALLOWED_PATHS=PASS", yml)
        self.assertGreaterEqual(yml.count("owner-v2-${{ inputs.package_id }}-${{ inputs.task_id }}-route"), 4)


if __name__ == "__main__":
    unittest.main()

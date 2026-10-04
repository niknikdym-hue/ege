import concurrent.futures
import hashlib
import json
import os
import re
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / ".github/workflows/owner-agent-task-v2.yml"
BATCH = ROOT / ".github/workflows/owner-agent-batch-v2.yml"
PROXY = ROOT / "eksamio-learning-engine/project-control/owner_control_budget_proxy.mjs"
LEGACY_PROXY = Path(__file__).with_name("fixtures") / "owner_control_budget_proxy_d8ebb5f.mjs"


def workflow_script(name):
    """Read an actual workflow run block without an extra YAML dependency."""
    block = TASK.read_text().split("      - name: " + name + "\n", 1)[1]
    block = block.split("      - ", 1)[0].split("        run: |\n", 1)[1]
    return "\n".join(line[10:] for line in block.splitlines()) + "\n"


def proxy_preflight(health):
    script = workflow_script("Freeze cumulative input and start executor proxy")
    check = script.split('python3 - "$health" <<\'PY\'\n', 1)[1].split("\nPY", 1)[0]
    return subprocess.run(
        ["python3", "-c", check, json.dumps(health)],
        env={**os.environ, "OWNER_TASK_BUDGET_USD": "0.10"},
        capture_output=True, text=True, timeout=10,
    )


class OwnerControlV2SafetyTest(unittest.TestCase):

    def test_executor_control_checkout_precedes_work_checkout_and_paid_access(self):
        job = TASK.read_text().split("  codex:\n", 1)[1].split("  validate:\n", 1)[0]
        authority = job.index("ref: ${{ inputs.approved_main_sha }}")
        preserve = job.index("- name: Preserve trusted executor proxy outside the worktree")
        work = job.index("ref: ${{ inputs.work_ref }}")
        preflight = job.index("EXECUTOR_PROXY_PREFLIGHT=PASS")
        codex = job.index("- name: Install pinned Codex CLI")
        self.assertLess(authority, preserve)
        self.assertLess(preserve, work)
        self.assertLess(work, preflight)
        self.assertLess(preflight, codex)
        self.assertIn("sudo install -o root -g root -m 0444", job)
        self.assertIn("node '$proxy'", job)
        self.assertNotIn("node '$PWD/$proxy'", job)

    def test_executor_preflight_rejects_legacy_or_mismatched_health(self):
        good = {"status": "ok", "max_requests": 6, "requests": 0,
                "reserved_usd": 0, "remaining_usd": 0.10}
        self.assertEqual(proxy_preflight(good).returncode, 0)
        cases = [
            {k: v for k, v in good.items() if k != "max_requests"},
            {**good, "max_requests": 7},
            {**good, "requests": 1},
            {**good, "reserved_usd": 0.01},
            {**good, "remaining_usd": 3},
            {**good, "status": "starting"},
        ]
        for health in cases:
            with self.subTest(health=health):
                self.assertNotEqual(proxy_preflight(health).returncode, 0)

    def test_mixed_authority_and_actual_old_work_ref_enforce_six_calls_offline(self):
        # Exact proxy from A1.4 work ref d8ebb5f73b43990dbe3b7c6bf685772cb3a48df4.
        # Keep the fixture self-contained: CI must not depend on legacy refs surviving.
        legacy_bytes = LEGACY_PROXY.read_bytes()
        self.assertEqual(
            hashlib.sha256(legacy_bytes).hexdigest(),
            "7e352410c9125ec4b6fd2349dcaafed081acad46c97eda667071e575e7e90990",
        )
        legacy = legacy_bytes.decode()
        self.assertNotIn("OWNER_MAX_PROVIDER_REQUESTS", legacy)
        self.assertNotIn("max_requests:", legacy)
        calls = []
        lock = threading.Lock()

        class MockProvider(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                payload = self.rfile.read(int(self.headers["Content-Length"]))
                with lock:
                    calls.append(json.loads(payload))
                body = b'{"error":{"message":"offline failure"}}'
                self.send_response(500)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), MockProvider)
        thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(upstream.server_close)
        self.addCleanup(upstream.shutdown)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "work"
            work.mkdir()
            source = work / PROXY.relative_to(ROOT)
            source.parent.mkdir(parents=True)
            source.write_bytes(PROXY.read_bytes())
            # Model GitHub's first checkout, then run the real preservation step.
            subprocess.run(["git", "init", "-q", str(work)], check=True)
            subprocess.run(["git", "add", "."], cwd=work, check=True)
            subprocess.run(["git", "-c", "user.name=Offline test", "-c",
                            "user.email=offline@example.invalid", "-c", "commit.gpgsign=false",
                            "-c", "core.hooksPath=/dev/null", "commit", "-qm", "authority"],
                           cwd=work, check=True)
            approved = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=work, text=True).strip()
            stage = workflow_script("Preserve trusted executor proxy outside the worktree")
            # Root ownership is asserted separately; the portable test never uses sudo.
            stage = stage.replace("sudo install", "install").replace(" -o root -g root", "")
            env = {**os.environ, "RUNNER_TEMP": str(root / "runner-temp")}
            wrong = subprocess.run(["bash", "-c", stage.replace("${{ inputs.approved_main_sha }}", "0" * 40)],
                                   cwd=work, env=env, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(wrong.returncode, 0)
            self.assertFalse((root / "runner-temp/owner-control-authority").exists())
            subprocess.run(["bash", "-c", stage.replace("${{ inputs.approved_main_sha }}", approved)],
                           cwd=work, env=env, check=True, capture_output=True, timeout=10)
            # The second checkout replaces the worktree with the real old revision.
            source.write_text(legacy)
            start = workflow_script("Freeze cumulative input and start executor proxy")
            proxy_assignment = re.search(r'^proxy=.*$', start, re.MULTILINE).group()
            selected = subprocess.check_output(["bash", "-c", proxy_assignment + '\nprintf "%s" "$proxy"'],
                                               cwd=work, env=env, text=True)
            selected = str((work / selected).resolve())
            self.assertNotEqual(Path(selected), source)
            self.assertEqual(Path(selected).read_bytes(), PROXY.read_bytes())
            self.assertEqual(source.read_text(), legacy)
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            env.update({
                "OWNER_TASK_BUDGET_USD": "0.10", "OWNER_ALLOWED_MODELS": "gpt-5.6-luna",
                "OWNER_MAX_PROVIDER_REQUESTS": "6", "OWNER_PROXY_CLIENT_TOKEN": "offline-client",
                "OWNER_PROXY_TEST_MODE": "1", "OWNER_BUDGET_PROXY_PORT": str(port),
                "OWNER_PROXY_UPSTREAM_URL": f"http://127.0.0.1:{upstream.server_port}/v1/responses",
            })
            env.pop("OPENAI_API_KEY", None)
            with subprocess.Popen(["node", selected], cwd=work, env=env, stdin=subprocess.PIPE,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True) as proxy:
                try:
                    proxy.stdin.write("offline-fake-provider-key")
                    proxy.stdin.close()
                    url = f"http://127.0.0.1:{port}"
                    def health():
                        with urllib.request.urlopen(url + "/health", timeout=2) as response:
                            return json.load(response)
                    for _ in range(100):
                        if proxy.poll() is not None:
                            self.fail("proxy exited: " + proxy.stderr.read())
                        try:
                            initial = health()
                            break
                        except (urllib.error.URLError, TimeoutError):
                            time.sleep(0.02)
                    else:
                        self.fail("offline proxy did not become ready")
                    preflight = proxy_preflight(initial)
                    self.assertEqual(preflight.returncode, 0, preflight.stderr)
                    self.assertEqual(calls, [])

                    def post(_, payload=None, token="offline-client"):
                        data = json.dumps(payload or {"model": "gpt-5.6-luna", "input": "x",
                                                     "max_output_tokens": 256}).encode()
                        request = urllib.request.Request(url + "/v1/responses", data=data,
                            headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
                        try:
                            with urllib.request.urlopen(request, timeout=5) as response:
                                return response.status
                        except urllib.error.HTTPError as error:
                            error.close()
                            return error.code

                    self.assertEqual(post(0, token="wrong"), 401)
                    self.assertEqual(post(0, {"model": "gpt-6-astra", "input": "x"}), 403)
                    self.assertEqual(post(0, {"model": "gpt-5.6-luna", "input": "x" * 500000}), 402)
                    self.assertEqual(calls, [])
                    # Concurrent failed upstream attempts still consume exactly six slots.
                    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                        statuses = list(pool.map(post, range(8)))
                    self.assertEqual(statuses.count(500), 6, statuses)
                    self.assertEqual(statuses.count(429), 2, statuses)
                    self.assertEqual(len(calls), 6)
                    self.assertEqual(post(0), 429)
                    self.assertEqual(len(calls), 6)
                    final = health()
                    self.assertEqual(final["max_requests"], 6)
                    self.assertEqual(final["requests"], 6)
                    self.assertGreater(final["remaining_usd"], 0)
                    self.assertLess(final["reserved_usd"], 0.10)
                finally:
                    proxy.terminate()
                    proxy.wait(timeout=5)
                    proxy.stderr.close()

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
        self.assertIn("OWNER_MAX_PROVIDER_REQUESTS must be an integer 1..6", text)
        self.assertIn("hard provider request cap exhausted before provider call", text)

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
        self.assertIn("API_CODEX_PROVIDER_REQUEST_CAP=6", codex)
        self.assertIn("--ephemeral -", codex)
        self.assertIn("< /tmp/codex-prompt.txt", codex)
        self.assertNotIn('prompt="$(cat /tmp/codex-prompt.txt)"', codex)

    def test_codex_retry_policy_is_explicitly_zero(self):
        yml = TASK.read_text()
        self.assertIn("request_max_retries = 0", yml)
        self.assertIn("stream_max_retries = 0", yml)
        self.assertIn("CODEX_REQUEST_MAX_RETRIES=0", yml)
        self.assertIn("CODEX_STREAM_MAX_RETRIES=0", yml)
        self.assertIn("OWNER_MAX_PROVIDER_REQUESTS='6'", yml)
        self.assertGreaterEqual(yml.count("OWNER_MAX_PROVIDER_REQUESTS='1'"), 2)

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
        self.assertIn("path: /tmp/route", yml)

if __name__ == "__main__":
    unittest.main()

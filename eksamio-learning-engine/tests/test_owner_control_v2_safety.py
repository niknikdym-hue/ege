import ast
import concurrent.futures
from contextlib import contextmanager
import hashlib
import json
import math
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


def proxy_preflight(health, *, output_cap="", budget="0.10"):
    script = workflow_script("Freeze cumulative input and start executor proxy")
    check = script.split('python3 - "$health" <<\'PY\'\n', 1)[1].split("\nPY", 1)[0]
    return subprocess.run(
        ["python3", "-c", check, json.dumps(health)],
        env={**os.environ, "OWNER_TASK_BUDGET_USD": budget, "OWNER_EXECUTOR_MAX_OUTPUT_TOKENS": output_cap},
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

class OwnerBudgetArtifactTest(unittest.TestCase):
    def _extract(self, payload, *, http_status=200, with_patch=False, shadow_imports=False):
        calls = []
        class Health(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                calls.append((self.command, self.path))
                self.send_response(http_status)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Health)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                work = root / "work"
                work.mkdir()
                subprocess.run(["git", "init", "-q", str(work)], check=True)
                target = work / "tracked.txt"
                target.write_text("before\\n")
                subprocess.run(["git", "add", "tracked.txt"], cwd=work, check=True)
                if with_patch:
                    target.write_text("after\\n")
                env = os.environ.copy()
                marker = root / "candidate-imported.marker"
                if shadow_imports:
                    injected = root / "injected"
                    injected.mkdir()
                    shadow = "from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('candidate executed')\nraise SystemExit(23)\n"
                    (work / "json.py").write_text(shadow)
                    (injected / "json.py").write_text(shadow)
                    env["PYTHONPATH"] = str(injected)
                script = workflow_script("Extract untrusted candidate patch only")
                script = script.replace("http://127.0.0.1:8787/health",
                                        f"http://127.0.0.1:{server.server_port}/health")
                budget = root / "executor-budget.json"
                patch = root / "candidate.patch"
                script = script.replace("/tmp/executor-budget.json", str(budget))
                script = script.replace("/tmp/candidate.patch", str(patch))
                result = subprocess.run(["bash", "-c", script], cwd=work,
                                        env=env, capture_output=True, text=True, timeout=10)
                self.assertFalse(marker.exists(), "Untrusted worktree/PYTHONPATH module executed")
                self.assertTrue(budget.is_file(), result.stderr)
                return result, json.loads(budget.read_text()), patch.read_bytes(), calls
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    @staticmethod
    def _health(**updates):
        data = {"status": "ok", "remaining_usd": 0.1665,
                "reserved_usd": 0.5835, "requests": 2, "max_requests": 6}
        data.update(updates)
        return json.dumps(data).encode()

    def test_empty_patch_failure_still_preserves_budget_snapshot(self):
        result, data, patch, calls = self._extract(self._health(unexpected_secret="never-save"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Codex produced no patch", result.stdout)
        self.assertEqual(patch, b"")
        self.assertEqual(data, json.loads(self._health()))
        self.assertEqual(calls, [("GET", "/health")])
        self.assertNotIn("never-save", json.dumps(data))

    def test_nonempty_patch_keeps_success_and_budget_snapshot(self):
        result, data, patch, calls = self._extract(self._health(), with_patch=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"tracked.txt", patch)
        self.assertEqual(data["requests"], 2)
        self.assertEqual(calls, [("GET", "/health")])

    def test_candidate_module_and_pythonpath_cannot_execute(self):
        result, data, patch, calls = self._extract(self._health(), with_patch=True, shadow_imports=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(data, json.loads(self._health()))
        self.assertIn(b"json.py", patch)
        self.assertEqual(calls, [("GET", "/health")])

    def test_health_failure_is_unknown_not_zero(self):
        result, data, patch, calls = self._extract(b"unavailable", http_status=503)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(data["status"], "unavailable")
        self.assertTrue(all(data[k] is None for k in ("remaining_usd", "reserved_usd", "requests", "max_requests")))
        self.assertEqual(patch, b"")
        self.assertEqual(calls, [("GET", "/health")])

    def test_malformed_and_oversized_health_are_unknown(self):
        for payload in (b"not json", b"x" * 16385):
            with self.subTest(size=len(payload)):
                result, data, _, _ = self._extract(payload)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(data["status"], "unavailable")
                self.assertIsNone(data["reserved_usd"])

    def test_invalid_health_values_are_unknown(self):
        for changes in ({"requests": True}, {"requests": 7}, {"max_requests": 7},
                        {"remaining_usd": -1}, {"reserved_usd": float("nan")},
                        {"status": "starting"}):
            with self.subTest(changes=changes):
                result, data, _, _ = self._extract(self._health(**changes))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(data["status"], "unavailable")
                self.assertIsNone(data["requests"])

    def test_budget_capture_precedes_every_candidate_failure_point(self):
        script = workflow_script("Extract untrusted candidate patch only")
        self.assertIn("/usr/bin/python3 -I - <<'PY'", script)
        capture = script.index("Path('/tmp/executor-budget.json').write_text")
        self.assertLess(capture, script.index("/usr/bin/git"))
        self.assertLess(capture, script.index("test -s /tmp/candidate.patch"))
        self.assertIn("Codex produced no patch'; exit 1", script)
        self.assertNotIn("POST", script)
        self.assertNotIn("secrets.", script)

class OwnerTaskOutputCapTest(unittest.TestCase):
    BASE = "c8781be94f7ff6091db42370477aee03d8d58bca"
    REF = "owner/a92-luna-foundation-base-20261005"

    def _route_cap(self, task, model="gpt-5.6-luna", ref=None, sha=None):
        script = workflow_script("Resolve task, route and per-phase hard budgets")
        source = script.split("python3 - <<'PY'\n", 1)[1].split("\nPY", 1)[0]
        tree = ast.parse(source)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "resolve_executor_output_cap")
        scope = {}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), "<trusted route>", "exec"), scope)
        return scope[fn.name](task, model, self.REF if ref is None else ref,
                              self.BASE if sha is None else sha)

    def test_only_exact_task_model_ref_sha_and_integer_cap_are_admitted(self):
        good = {"task_id": "A9.2", "executor_max_output_tokens": 4800}
        self.assertEqual(self._route_cap(good), 4800)
        for value in (None, True, "4800", 4800.0, 1800, 4801, 0, -1):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit):
                    self._route_cap({**good, "executor_max_output_tokens": value})
        for changed, kwargs in [
            ({**good, "task_id": "A9.3"}, {}),
            ({**good, "astra_required": True}, {}),
            ({**good, "astra_plan_required": True}, {}),
            ({**good, "astra_acceptance_required": True}, {}),
            (good, {"model": "gpt-5.6-sol"}),
            (good, {"ref": "main"}),
            (good, {"sha": "0" * 40}),
        ]:
            with self.subTest(changed=changed, kwargs=kwargs):
                with self.assertRaises(SystemExit):
                    self._route_cap(changed, **kwargs)

    def test_absent_override_keeps_every_route_default(self):
        for model in ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol", "gpt-6-astra"):
            self.assertIsNone(self._route_cap({"task_id": "A1.4"}, model=model, ref="main", sha="other"))

    def test_override_cannot_expand_the_approved_cash_cap(self):
        from decimal import Decimal
        script = workflow_script("Resolve task, route and per-phase hard budgets")
        source = script.split("python3 - <<'PY'\n", 1)[1].split("\nPY", 1)[0]
        tree = ast.parse(source)
        guard = next(n for n in tree.body if isinstance(n, ast.If)
                     and "executor_output_cap" in ast.unparse(n.test)
                     and "total" in ast.unparse(n.test))
        code = compile(ast.Module(body=[guard], type_ignores=[]), "<override cash gate>", "exec")
        for value in ("0.05", "0.10", "0.35"):
            exec(code, {"Decimal": Decimal, "executor_output_cap": 4800, "total": Decimal(value)})
        for value in ("0.350001", "0.36", "3.00"):
            with self.assertRaises(SystemExit):
                exec(code, {"Decimal": Decimal, "executor_output_cap": 4800, "total": Decimal(value)})
        exec(code, {"Decimal": Decimal, "executor_output_cap": None, "total": Decimal("3.00")})

    def test_only_a92_board_row_has_override(self):
        board = json.loads((ROOT / "eksamio-learning-engine/project-control/operational-board-v1.json").read_text())
        rows = [t for t in board["tasks"] if "executor_max_output_tokens" in t]
        self.assertEqual(len(board["tasks"]), 115)
        self.assertEqual(len(rows), 1)
        t = rows[0]
        self.assertEqual((t["task_id"], t["model_route"], t["head_sha"], t["executor_max_output_tokens"]),
                         ("A9.2", "luna", self.BASE, 4800))
        self.assertEqual(t["status"], "INTEGRATION_PENDING")
        self.assertFalse(t["visible_to_learner"])

    def test_proxy_override_is_bound_to_trusted_route_output(self):
        yml = TASK.read_text()
        self.assertIn("executor_max_output_tokens: ${{ steps.resolve.outputs.executor_max_output_tokens }}", yml)
        self.assertIn("OWNER_EXECUTOR_MAX_OUTPUT_TOKENS: ${{ needs.route.outputs.executor_max_output_tokens }}", yml)
        self.assertNotIn("inputs.executor_max_output_tokens", yml)
        self.assertIn("OWNER_EXECUTOR_MAX_OUTPUT_TOKENS='$OWNER_EXECUTOR_MAX_OUTPUT_TOKENS'", yml)
        good = {"status": "ok", "max_requests": 6, "requests": 0,
                "reserved_usd": 0, "remaining_usd": 0.35, "executor_max_output_tokens": 4800}
        self.assertEqual(proxy_preflight(good, output_cap="4800", budget="0.35").returncode, 0)
        for health in ({k: v for k, v in good.items() if k != "executor_max_output_tokens"},
                       {**good, "executor_max_output_tokens": 1800}):
            self.assertNotEqual(proxy_preflight(health, output_cap="4800", budget="0.35").returncode, 0)

    @contextmanager
    def _proxy(self, model="gpt-5.6-luna", override=None, budget="0.35", source_path=None):
        calls = []
        class Fake(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_POST(self):
                calls.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                body = b'{"error":{"message":"offline failure"}}'
                self.send_response(500)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
        thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        thread.start()
        proxy = None
        try:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            env = {**os.environ, "OWNER_TASK_BUDGET_USD": budget,
                   "OWNER_ALLOWED_MODELS": model, "OWNER_MAX_PROVIDER_REQUESTS": "6",
                   "OWNER_PROXY_CLIENT_TOKEN": "offline-client", "OWNER_PROXY_TEST_MODE": "1",
                   "OWNER_BUDGET_PROXY_PORT": str(port),
                   "OWNER_PROXY_UPSTREAM_URL": f"http://127.0.0.1:{upstream.server_port}/v1/responses"}
            env.pop("OPENAI_API_KEY", None)
            env.pop("OWNER_EXECUTOR_MAX_OUTPUT_TOKENS", None)
            if override is not None:
                env["OWNER_EXECUTOR_MAX_OUTPUT_TOKENS"] = override
            proxy = subprocess.Popen(["node", str(source_path or PROXY)], env=env, stdin=subprocess.PIPE,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            proxy.stdin.write("offline-fake-key")
            proxy.stdin.close()
            url = f"http://127.0.0.1:{port}"
            def health():
                with urllib.request.urlopen(url + "/health", timeout=2) as response:
                    return json.load(response)
            for _ in range(100):
                if proxy.poll() is not None:
                    self.fail(proxy.stderr.read())
                try:
                    health()
                    break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.02)
            else:
                self.fail("offline proxy did not start")
            def post(requested=None, token="offline-client", request_model=None, text="x", include_requested=False, raw_body=None):
                payload = {"model": request_model or model, "input": text, "store": False}
                if requested is not None or include_requested:
                    payload["max_output_tokens"] = requested
                data = json.dumps(payload).encode() if raw_body is None else raw_body
                request = urllib.request.Request(url + "/v1/responses", data=data,
                    headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
                try:
                    with urllib.request.urlopen(request, timeout=5) as response:
                        return response.status
                except urllib.error.HTTPError as error:
                    error.close()
                    return error.code
            yield calls, post, health
        finally:
            if proxy is not None:
                proxy.terminate()
                proxy.wait(timeout=5)
                proxy.stderr.close()
            upstream.shutdown()
            upstream.server_close()
            thread.join(timeout=2)

    def test_all_default_model_ceilings_remain_unchanged(self):
        for model, expected in (("gpt-5.6-luna", 1800), ("gpt-5.6-terra", 2200),
                                ("gpt-5.6-sol", 2400), ("gpt-6-astra", 3000)):
            with self.subTest(model=model), self._proxy(model=model) as (calls, post, health):
                self.assertIsNone(health()["executor_max_output_tokens"])
                self.assertEqual(post(), 500)
                self.assertEqual(calls[0]["max_output_tokens"], expected)

    def test_override_4800_smaller_requests_and_auth_are_preserved(self):
        with self._proxy(override="4800") as (calls, post, health):
            self.assertEqual(health()["executor_max_output_tokens"], 4800)
            self.assertEqual(post(token="wrong"), 401)
            self.assertEqual(post(request_model="gpt-5.6-sol"), 403)
            self.assertEqual(calls, [])
            for requested, expected in ((None, 4800), (99999, 4800), (700, 700)):
                self.assertEqual(post(requested), 500)
                self.assertEqual(calls[-1]["max_output_tokens"], expected)
                self.assertFalse(calls[-1]["store"])
            self.assertEqual(health()["requests"], 3)
            self.assertLessEqual(health()["reserved_usd"], 0.35)

    def test_override_still_respects_affordable_budget_before_forwarding(self):
        with self._proxy(override="4800", budget="0.001") as (calls, post, health):
            self.assertEqual(post(4800), 500)
            self.assertGreaterEqual(calls[0]["max_output_tokens"], 256)
            self.assertLess(calls[0]["max_output_tokens"], 4800)
            self.assertLessEqual(health()["reserved_usd"], 0.001)
            self.assertGreaterEqual(health()["remaining_usd"], 0)
            self.assertEqual(post(4800), 402)
            self.assertEqual(len(calls), 1)
        with self._proxy(override="4800") as (calls, post, _):
            self.assertEqual(post(4800, text="x" * 2000000), 402)
            self.assertEqual(calls, [])

    def test_override_preserves_six_slots_under_concurrent_failures(self):
        with self._proxy(override="4800") as (calls, post, health):
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                statuses = list(pool.map(lambda _: post(), range(8)))
            self.assertEqual(statuses.count(500), 6, statuses)
            self.assertEqual(statuses.count(429), 2, statuses)
            self.assertEqual(len(calls), 6)
            self.assertEqual(post(), 429)
            self.assertEqual(health()["requests"], 6)
            self.assertLessEqual(health()["reserved_usd"], 0.35)

    def test_invalid_process_overrides_fail_before_proxy_start(self):
        cases = [(value, "gpt-5.6-luna") for value in ("0", "-1", "1800", "4801", "4800.0", "NaN", "Infinity")]
        cases += [("4800", "gpt-5.6-sol"), ("4800", "gpt-5.6-luna,gpt-6-astra")]
        for value, models in cases:
            with self.subTest(value=value, models=models):
                env = {**os.environ, "OWNER_TASK_BUDGET_USD": "0.35",
                       "OWNER_ALLOWED_MODELS": models, "OWNER_MAX_PROVIDER_REQUESTS": "6",
                       "OWNER_PROXY_CLIENT_TOKEN": "offline-client",
                       "OWNER_EXECUTOR_MAX_OUTPUT_TOKENS": value}
                env.pop("OPENAI_API_KEY", None)
                env.pop("OWNER_PROXY_UPSTREAM_URL", None)
                result = subprocess.run(["node", str(PROXY)], env=env, input="offline-fake-key",
                                        capture_output=True, text=True, timeout=5)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Executor output override requires exactly 4800", result.stderr)


    def test_invalid_requested_caps_do_not_poison_accounting(self):
        invalid = ("invalid-number", "700", True, False, 0, -1, 0.5, [], {},
                   2**53, float("nan"), float("inf"), float("-inf"))
        for override in (None, "4800"):
            with self.subTest(override=override), self._proxy(override=override) as (calls, post, health):
                initial = health()
                for value in invalid:
                    with self.subTest(value=value):
                        self.assertEqual(post(value), 400)
                        self.assertEqual(calls, [])
                        self.assertEqual(health(), initial)
                raw = b'{"model":"gpt-5.6-luna","input":"x","max_output_tokens":1e309}'
                self.assertEqual(post(raw_body=raw), 400)
                self.assertEqual(calls, [])
                self.assertEqual(health(), initial)
                self.assertEqual(post(700), 500)
                self.assertEqual(calls[0]["max_output_tokens"], 700)
                observed = health()
                self.assertEqual(observed["requests"], 1)
                self.assertTrue(math.isfinite(observed["reserved_usd"]))
                self.assertTrue(math.isfinite(observed["remaining_usd"]))
                # Health rounds each amount independently to six decimal places.
                self.assertAlmostEqual(observed["reserved_usd"] + observed["remaining_usd"], 0.35, delta=0.00000101)

    def test_null_and_absent_output_limits_keep_route_defaults(self):
        for override, expected in ((None, 1800), ("4800", 4800)):
            with self.subTest(override=override), self._proxy(override=override) as (calls, post, health):
                self.assertEqual(post(), 500)
                self.assertEqual(post(None, include_requested=True), 500)
                self.assertEqual([p["max_output_tokens"] for p in calls], [expected, expected])
                self.assertEqual(health()["requests"], 2)

    def test_nonfinite_computed_caps_reservations_and_state_fail_closed(self):
        source = PROXY.read_text()
        replacements = []
        max_line = next(l for l in source.splitlines() if l.strip().startswith("const maxOut = capOutputTokens"))
        reserve_line = next(l for l in source.splitlines() if l.strip().startswith("const reservation = conservativeReservationUsd"))
        for value in ("Number.NaN", "Number.POSITIVE_INFINITY"):
            replacements.append((max_line, "    const maxOut = " + value + ";"))
            replacements.append((reserve_line, "    const reservation = " + value + ";"))
            replacements.append(("let remainingUsd = totalBudget;", "let remainingUsd = " + value + ";"))
            replacements.append(("let reservedUsd = 0;", "let reservedUsd = " + value + ";"))
        replacements.append((reserve_line, "    const reservation = -1;"))
        with tempfile.TemporaryDirectory() as tmp:
            mutated = Path(tmp) / "numeric-fault.mjs"
            for old, new in replacements:
                with self.subTest(fault=new):
                    self.assertEqual(source.count(old), 1)
                    mutated.write_text(source.replace(old, new, 1))
                    with self._proxy(override="4800", source_path=mutated) as (calls, post, health):
                        self.assertEqual(post(700), 402)
                        self.assertEqual(calls, [])
                        self.assertEqual(health()["requests"], 0)

if __name__ == "__main__":
    unittest.main()

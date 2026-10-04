"""Offline source-contract tests, not a replacement for the Actions scheduler.

Evaluate the actual job expressions, including the implicit success() guard.
The echo-only reusable workflow separately probes real skipped-ancestor behavior.
No paid workflow, API, credentials, checkout or git mutation is executed here.
"""
import ast
import itertools
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / ".github/workflows/owner-agent-task-v2.yml"
FIXTURE = ROOT / ".github/workflows/owner-control-v2-needs-fixture.yml"
JOBS = ("astra_plan", "codex", "validate", "astra_accept", "commit")
STATUS = re.compile(r"\b(always|cancelled|success|failure)\(\)")


def job_contract(text, job):
    """Fail closed if the current one-line needs/if format changes."""
    block = re.search(r"^  " + job + r":\n(.*?)(?=^  [\w-]+:|\Z)", text,
                      re.MULTILINE | re.DOTALL).group(1)
    needs = re.search(r"^    needs: (.+)$", block, re.MULTILINE).group(1)
    expression = re.search(r"^    if: \$\{\{ (.+) \}\}$", block, re.MULTILINE).group(1)
    return needs, expression


def condition(expression, values, *, cancelled=False, ancestors_success=True):
    """Bounded evaluator for these boolean/string expressions, not all Actions.

    `ancestors_success` models the documented default status gate. A real
    runner must still verify how skipped transitive dependencies propagate.
    https://docs.github.com/en/actions/reference/workflows-and-actions/expressions#status-check-functions
    """
    has_status = bool(STATUS.search(expression))
    functions = {"always": True, "cancelled": cancelled,
                 "success": ancestors_success, "failure": False}
    expression = STATUS.sub(lambda m: str(functions[m[1]]), expression)
    expression = re.sub(r"\bneeds\.[a-z_]+\.(?:result|outputs\.[a-z_]+)\b",
                        lambda m: repr(values[m[0]]), expression)
    expression = expression.replace("&&", " and ").replace("||", " or ").replace("!", " not ").strip()
    tree = ast.parse(expression, mode="eval")
    allowed = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp,
               ast.Not, ast.Compare, ast.Eq, ast.Constant, ast.Load)
    if any(not isinstance(node, allowed) for node in ast.walk(tree)):
        raise ValueError("Unexpected expression syntax; extend the bounded test deliberately")
    result = bool(eval(compile(tree, "<workflow-condition>", "eval"), {"__builtins__": {}}, {}))
    return result and (has_status or ancestors_success)


class OptionalAstraGatesTest(unittest.TestCase):
    def setUp(self):
        self.source = TASK.read_text()
        self.expressions = {job: job_contract(self.source, job)[1] for job in JOBS}

    def test_runtime_fixture_uses_actual_production_needs_and_conditions(self):
        fixture = FIXTURE.read_text()
        for job in JOBS:
            with self.subTest(job=job):
                self.assertEqual(job_contract(fixture, job), job_contract(self.source, job))
        self.assertIn("  workflow_call:", fixture)
        self.assertIn("  contents: read", fixture)
        for token in ("secrets.", "secrets:", "git push", "codex exec", "curl ", "urllib", "uses:"):
            self.assertNotIn(token, fixture)

    def test_all_optional_phase_combinations_reach_validation_and_commit(self):
        for plan, acceptance in itertools.product((False, True), repeat=2):
            with self.subTest(plan=plan, acceptance=acceptance):
                values = {"needs.route.result": "success",
                          "needs.route.outputs.astra_plan": str(plan).lower(),
                          "needs.route.outputs.astra_accept": str(acceptance).lower()}
                self.assertEqual(condition(self.expressions["astra_plan"], values), plan)
                values["needs.astra_plan.result"] = "success" if plan else "skipped"
                self.assertTrue(condition(self.expressions["codex"], values, ancestors_success=plan))
                values["needs.codex.result"] = "success"
                self.assertTrue(condition(self.expressions["validate"], values, ancestors_success=plan))
                values["needs.validate.result"] = "success"
                self.assertEqual(condition(self.expressions["astra_accept"], values,
                                           ancestors_success=plan), acceptance)
                values["needs.astra_accept.result"] = "success" if acceptance else "skipped"
                self.assertTrue(condition(self.expressions["commit"], values,
                                          ancestors_success=plan and acceptance))

    def test_removing_each_override_reproduces_skipped_ancestor_regression(self):
        values = {"needs.route.result": "success", "needs.codex.result": "success",
                  "needs.validate.result": "success", "needs.route.outputs.astra_accept": "true"}
        for job in ("validate", "astra_accept"):
            with self.subTest(job=job):
                expression = self.expressions[job]
                self.assertTrue(expression.startswith("!cancelled() && "))
                self.assertTrue(condition(expression, values, ancestors_success=False))
                original = expression.removeprefix("!cancelled() && ")
                self.assertFalse(condition(original, values, ancestors_success=False))

    def test_route_or_codex_non_success_blocks_validation(self):
        for gate, result in itertools.product(("route", "codex"), ("failure", "skipped", "cancelled", "")):
            with self.subTest(gate=gate, result=result):
                values = {"needs.route.result": "success", "needs.codex.result": "success"}
                values[f"needs.{gate}.result"] = result
                self.assertFalse(condition(self.expressions["validate"], values))

    def test_required_plan_failure_still_blocks_codex(self):
        for result in ("failure", "cancelled"):
            values = {"needs.route.result": "success", "needs.astra_plan.result": result}
            self.assertFalse(condition(self.expressions["codex"], values))

    def test_validation_failure_and_disabled_acceptance_do_not_run_astra(self):
        for result, enabled in itertools.product(("success", "failure", "skipped", "cancelled", ""),
                                                 ("true", "false", "")):
            with self.subTest(result=result, enabled=enabled):
                values = {"needs.validate.result": result, "needs.route.outputs.astra_accept": enabled}
                self.assertEqual(condition(self.expressions["astra_accept"], values),
                                 result == "success" and enabled == "true")

    def test_cancellation_suppresses_validation_and_acceptance(self):
        values = {"needs.route.result": "success", "needs.codex.result": "success",
                  "needs.validate.result": "success", "needs.route.outputs.astra_accept": "true"}
        for job in ("validate", "astra_accept"):
            for ancestors_success in (False, True):
                self.assertFalse(condition(self.expressions[job], values, cancelled=True,
                                           ancestors_success=ancestors_success))
        # Cancellation before validation leaves commit closed too.
        values.update({"needs.validate.result": "skipped", "needs.astra_accept.result": "skipped"})
        self.assertFalse(condition(self.expressions["commit"], values, cancelled=True))

    def test_failed_validation_or_acceptance_keeps_commit_closed(self):
        for gate in ("validate", "astra_accept"):
            for result in ("failure", "cancelled"):
                values = {"needs.route.result": "success", "needs.validate.result": "success",
                          "needs.astra_accept.result": "success", "needs.route.outputs.astra_accept": "true"}
                values[f"needs.{gate}.result"] = result
                self.assertFalse(condition(self.expressions["commit"], values))

    def test_commit_requires_acceptance_success_or_explicitly_disabled_skip(self):
        for enabled, result in itertools.product(("true", "false", ""),
                                                 ("success", "failure", "skipped", "cancelled", "")):
            with self.subTest(enabled=enabled, result=result):
                values = {"needs.route.result": "success", "needs.validate.result": "success",
                          "needs.route.outputs.astra_accept": enabled, "needs.astra_accept.result": result}
                self.assertEqual(condition(self.expressions["commit"], values, ancestors_success=False),
                                 result == "success" or (enabled == "false" and result == "skipped"))

    def test_cancel_after_validation_or_acceptance_never_opens_commit(self):
        for enabled in ("true", "false"):
            values = {"needs.route.result": "success", "needs.codex.result": "success",
                      "needs.route.outputs.astra_accept": enabled}
            # Real transition: validation finishes before cancellation arrives.
            self.assertTrue(condition(self.expressions["validate"], values, ancestors_success=False))
            values["needs.validate.result"] = "success"
            self.assertFalse(condition(self.expressions["astra_accept"], values,
                                       cancelled=True, ancestors_success=False))
            for acceptance in ("skipped", "cancelled", "success"):
                # Include cancellation arriving after acceptance already passed.
                values["needs.astra_accept.result"] = acceptance
                self.assertFalse(condition(self.expressions["commit"], values,
                                           cancelled=True, ancestors_success=False))

    def test_route_non_success_keeps_commit_closed(self):
        for result in ("failure", "cancelled", "skipped", ""):
            values = {"needs.route.result": result, "needs.validate.result": "success",
                      "needs.route.outputs.astra_accept": "false", "needs.astra_accept.result": "skipped"}
            self.assertFalse(condition(self.expressions["commit"], values))


if __name__ == "__main__":
    unittest.main()

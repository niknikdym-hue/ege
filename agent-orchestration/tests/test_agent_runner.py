import importlib.util
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eksamio_agent_runner", ROOT / "eksamio_agent_runner.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

GOOD_SHA = "a" * 40


def valid_task(**overrides):
    value = {
        "schema_version": "0.1",
        "repository": "niknikdym-hue/ege",
        "base_sha": GOOD_SHA,
        "target_branch": "brain/example",
        "goal": "Implement one bounded unit",
        "allowed_scope": ["agent-orchestration/**"],
        "non_goals": ["merge", "deploy"],
        "acceptance_checks": ["python3 -m unittest"],
        "requested_actions": ["edit", "test", "commit", "push_draft_branch"],
        "stop_conditions": ["branch moved incompatibly"],
    }
    value.update(overrides)
    return value


def valid_review(**overrides):
    value = {
        "schema_version": "0.1",
        "decision": "PASS",
        "reviewed_sha": GOOD_SHA,
        "invariants": {
            "false_exact_mastery_zero": True,
            "server_owned_truth_preserved": True,
            "owner_gates_preserved": True,
        },
        "evidence": ["CI green on exact head"],
        "reason": "All bounded checks passed",
        "next_action": "Persist decision",
    }
    value.update(overrides)
    return value


class ContractTests(unittest.TestCase):
    def test_task_contract_accepts_bounded_task(self):
        task = valid_task()
        self.assertIs(MODULE.validate_task_plan(task), task)

    def test_task_contract_rejects_unknown_field(self):
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_task_plan(valid_task(surprise="no"))

    def test_task_contract_rejects_wrong_repo(self):
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_task_plan(valid_task(repository="other/repo"))

    def test_review_pass_requires_all_hard_invariants(self):
        review = valid_review()
        review["invariants"]["false_exact_mastery_zero"] = False
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_review_decision(review)

    def test_rework_may_report_failed_invariant(self):
        review = valid_review(decision="REWORK")
        review["invariants"]["owner_gates_preserved"] = False
        MODULE.validate_review_decision(review)


class PermissionTests(unittest.TestCase):
    def test_safe_actions_are_allowed_without_owner_gate(self):
        MODULE.PermissionGate().assert_allowed(["edit", "test", "commit", "push_draft_branch"])

    def test_every_dangerous_action_is_denied_by_default(self):
        for action in MODULE.DANGEROUS_ACTIONS:
            with self.subTest(action=action):
                with self.assertRaises(MODULE.PermissionDenied):
                    MODULE.PermissionGate().assert_allowed([action])

    def test_owner_authorization_is_action_specific(self):
        gate = MODULE.PermissionGate(frozenset({"live_provider_call"}))
        gate.assert_allowed(["live_provider_call"])
        with self.assertRaises(MODULE.PermissionDenied):
            gate.assert_allowed(["deploy"])


class AdapterTests(unittest.TestCase):
    def test_codex_dry_run_never_requires_command(self):
        result = MODULE.CodexExecutorAdapter(command=None).execute(valid_task(), dry_run=True)
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertEqual(len(result["task_hash"]), 64)

    def test_codex_non_dry_run_fails_closed_without_command(self):
        with self.assertRaises(MODULE.ProviderError):
            MODULE.CodexExecutorAdapter(command="").execute(valid_task(), dry_run=False)

    def test_astra_live_call_requires_key(self):
        adapter = MODULE.AstraResponsesAdapter(api_key=None, model="gpt-6-astra", base_url="https://example.invalid")
        adapter.api_key = None
        with self.assertRaises(MODULE.ProviderError):
            adapter.structured(instructions="x", input_text="x", schema_name="x", schema={"type": "object"})

    def test_astra_plan_validates_structured_output(self):
        adapter = MODULE.AstraResponsesAdapter(api_key="unused")
        expected = valid_task()
        adapter.structured = lambda **kwargs: {"output": expected, "provider_metadata": {"returned_model": "gpt-6-astra"}}
        result = adapter.plan({"head_sha": GOOD_SHA})
        self.assertEqual(result["output"], expected)

    def test_astra_review_rejects_false_pass(self):
        adapter = MODULE.AstraResponsesAdapter(api_key="unused")
        bad = valid_review()
        bad["invariants"]["false_exact_mastery_zero"] = False
        adapter.structured = lambda **kwargs: {"output": bad, "provider_metadata": {"returned_model": "gpt-6-astra"}}
        with self.assertRaises(MODULE.ContractError):
            adapter.review({"head_sha": GOOD_SHA})

    def test_output_text_parser_is_order_preserving(self):
        response = {
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "{\"a\":"}]},
                {"type": "message", "content": [{"type": "output_text", "text": "1}"}]},
            ]
        }
        self.assertEqual(MODULE.AstraResponsesAdapter._extract_output_text(response), '{"a":1}')


class RunRecordTests(unittest.TestCase):
    def test_record_binds_input_to_exact_sha(self):
        task = valid_task()
        record = MODULE.build_run_record(phase="CODEX_DRY_RUN", git_sha=GOOD_SHA, input_object=task, result={"status": "DRY_RUN"})
        self.assertEqual(record["git_sha"], GOOD_SHA)
        self.assertEqual(record["input_sha256"], MODULE.sha256_json(task))


class SchemaFileTests(unittest.TestCase):
    def test_schema_files_are_valid_json_and_versioned(self):
        for name in ("task-plan-v0.1.schema.json", "review-decision-v0.1.schema.json"):
            data = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            self.assertEqual(data["type"], "object")
            self.assertFalse(data["additionalProperties"])
            self.assertIn("schema_version", data["required"])


if __name__ == "__main__":
    unittest.main()

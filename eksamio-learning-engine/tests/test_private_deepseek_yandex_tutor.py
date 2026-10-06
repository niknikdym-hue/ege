import copy
import importlib.util
import math
import pathlib
import unittest

ROOT = pathlib.Path(__file__).parents[2]
PATH = ROOT / "eksamio-learning-engine/ai-tutor-reference/private_deepseek_yandex_tutor.py"
SPEC = importlib.util.spec_from_file_location("partial_private_tutor", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DeterministicFoundationTests(unittest.TestCase):
    def test_key_order_stable(self):
        self.assertEqual(MODULE.fingerprint_request("r", "s", {"b": 2, "a": 1}), MODULE.fingerprint_request("r", "s", {"a": 1, "b": 2}))

    def test_identity_and_payload_changes(self):
        base = MODULE.fingerprint_request("r", "s", {"x": 1})
        for args in (("r2", "s", {"x": 1}), ("r", "s2", {"x": 1}), ("r", "s", {"x": 2}), ("r", "s", {"x": "1"})):
            self.assertNotEqual(base, MODULE.fingerprint_request(*args))

    def test_whitespace_unicode_and_array_order_matter(self):
        self.assertNotEqual(MODULE.fingerprint_request("r", "s", {"x": "a b"}), MODULE.fingerprint_request("r", "s", {"x": "a  b"}))
        self.assertNotEqual(MODULE.fingerprint_request("r", "s", {"x": "ё"}), MODULE.fingerprint_request("r", "s", {"x": "e"}))
        self.assertNotEqual(MODULE.fingerprint_request("r", "s", {"x": [1, 2]}), MODULE.fingerprint_request("r", "s", {"x": [2, 1]}))

    def test_inputs_unchanged(self):
        payload = {"x": [{"y": 1}]}; before = copy.deepcopy(payload)
        MODULE.fingerprint_request("r", "s", payload)
        self.assertEqual(payload, before)

    def test_invalid_ids_and_payloads_rejected(self):
        for value in ("", None, 1):
            with self.assertRaises((TypeError, ValueError)): MODULE.fingerprint_request(value, "s", {})
        for payload in ({1: "x"}, {"x": object()}, {"x": (1, 2)}, {"x": float("nan")}, {"x": math.inf}):
            with self.assertRaises((TypeError, ValueError)): MODULE.fingerprint_request("r", "s", payload)

    def test_valid_usage_including_zero(self):
        values = {"input_tokens": 0, "output_tokens": 2, "call_count": 1, "reserved_minor_units": 0, "latency_ms": 1.5}
        self.assertEqual(MODULE.safe_usage_metadata(values), values)

    def test_missing_values_omitted(self):
        self.assertEqual(MODULE.safe_usage_metadata({"input_tokens": 1}), {"input_tokens": 1})

    def test_boolean_negative_and_fractional_counts_dropped(self):
        values = {"input_tokens": True, "output_tokens": -1, "call_count": 1.2, "reserved_minor_units": None, "latency_ms": -1}
        self.assertEqual(MODULE.safe_usage_metadata(values), {})

    def test_nonfinite_latency_dropped(self):
        self.assertEqual(MODULE.safe_usage_metadata({"latency_ms": float("nan"), "call_count": math.inf}), {})

    def test_nested_and_text_values_dropped(self):
        self.assertEqual(MODULE.safe_usage_metadata({"input_tokens": {"secret": 1}, "latency_ms": "fast"}), {})

    def test_unknown_secret_fields_dropped(self):
        self.assertEqual(MODULE.safe_usage_metadata({"api_key": "secret", "raw_dialogue": "text", "model": "x"}), {})

    def test_metadata_requires_plain_dict(self):
        for value in (None, [], "x", object()):
            with self.assertRaises(TypeError): MODULE.safe_usage_metadata(value)

    def test_usage_input_unchanged(self):
        values = {"input_tokens": 2, "secret": "x"}; before = copy.deepcopy(values)
        MODULE.safe_usage_metadata(values)
        self.assertEqual(values, before)

    def test_digest_is_sha256_hex(self):
        digest = MODULE.fingerprint_request("r", "s", {})
        self.assertEqual(len(digest), 64); int(digest, 16)

    def test_module_is_partial_and_import_safe(self):
        self.assertIn("PARTIAL", MODULE.__doc__)
        self.assertFalse(hasattr(MODULE, "requests"))


if __name__ == "__main__":
    unittest.main()

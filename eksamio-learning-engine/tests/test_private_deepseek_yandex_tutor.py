import copy
from contextlib import ExitStack, contextmanager
import hashlib
import importlib.util
import io
import json
import math
import os
import pathlib
import socket
import subprocess
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).parents[2]
PATH = ROOT / "eksamio-learning-engine/ai-tutor-reference/private_deepseek_yandex_tutor.py"
SPEC = importlib.util.spec_from_file_location("partial_private_tutor", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@contextmanager
def forbid_external_operations(test_case):
    """Fail on attempted I/O even if candidate code catches the exception."""
    calls = []

    def deny(operation):
        def blocked(*args, **kwargs):
            calls.append(operation)
            raise AssertionError("forbidden external operation: " + operation)
        return blocked

    class ForbiddenEnvironment:
        __getitem__ = get = __contains__ = __iter__ = __len__ = deny("environment read")
        keys = items = values = copy = deny("environment read")
        __setitem__ = __delitem__ = deny("environment write")

    allowed_imports = {"hashlib": hashlib, "json": json, "math": math}

    def import_pure_module(name, globals=None, locals=None, fromlist=(), level=0):
        if level or name not in allowed_imports:
            return deny("unexpected import: " + name)()
        return allowed_imports[name]

    with ExitStack() as stack:
        for target in ("builtins.open", "io.open", "os.open", "pathlib.Path.open",
                       "socket.socket", "socket.create_connection", "socket.getaddrinfo",
                       "os.getenv", "os.system", "subprocess.Popen"):
            stack.enter_context(mock.patch(target, side_effect=deny(target)))
        stack.enter_context(mock.patch.object(os, "environ", ForbiddenEnvironment()))
        if hasattr(os, "environb"):
            stack.enter_context(mock.patch.object(os, "environb", ForbiddenEnvironment()))
            stack.enter_context(mock.patch.object(os, "getenvb", side_effect=deny("os.getenvb")))
        stack.enter_context(mock.patch("builtins.__import__", side_effect=import_pure_module))
        yield
    test_case.assertEqual(calls, [], "candidate attempted an external operation")


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

    def test_huge_integer_latency_preserved_exactly(self):
        values = {"latency_ms": 10 ** 309, "input_tokens": 1}
        result = MODULE.safe_usage_metadata(values)
        self.assertEqual(result, values)
        self.assertIs(type(result["latency_ms"]), int)
        self.assertIsNot(result, values)

    def test_huge_negative_integer_latency_dropped(self):
        values = {"latency_ms": -(10 ** 309), "input_tokens": 1}
        self.assertEqual(MODULE.safe_usage_metadata(values), {"input_tokens": 1})

    def test_latency_numeric_boundaries(self):
        for value in (0, 0.0, -0.0, 1.5, 1e308):
            with self.subTest(value=value):
                self.assertEqual(MODULE.safe_usage_metadata({"latency_ms": value}), {"latency_ms": value})
        for value in (True, False, -1, -1.5, math.nan, math.inf, -math.inf, None, "1"):
            with self.subTest(value=value):
                self.assertEqual(MODULE.safe_usage_metadata({"latency_ms": value, "call_count": 2}), {"call_count": 2})

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

    def test_module_remains_partial(self):
        self.assertIn("PARTIAL", MODULE.__doc__)

    def test_import_performs_no_external_operations(self):
        source = compile(PATH.read_bytes(), str(PATH), "exec")
        module = types.ModuleType("isolated_private_tutor")
        with forbid_external_operations(self):
            exec(source, module.__dict__)
        self.assertTrue(callable(module.fingerprint_request))
        self.assertTrue(callable(module.safe_usage_metadata))

    def test_helpers_perform_no_external_operations(self):
        payload = {"text": " ё ", "nested": [{"b": 2, "a": 1}]}
        envelope = {"domain": "eksamio.private-deepseek.request.v1", "request_id": "r", "session_ref": "s", "payload": payload}
        expected = hashlib.sha256(json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
        with forbid_external_operations(self):
            actual = MODULE.fingerprint_request("r", "s", payload)
            usage = MODULE.safe_usage_metadata({"latency_ms": 10 ** 309, "input_tokens": 0, "api_key": "fake-secret"})
            with self.assertRaises(ValueError):
                MODULE.fingerprint_request("", "s", payload)
            with self.assertRaises(TypeError):
                MODULE.safe_usage_metadata(None)
        self.assertEqual(actual, expected)
        self.assertEqual(usage, {"latency_ms": 10 ** 309, "input_tokens": 0})


if __name__ == "__main__":
    unittest.main()

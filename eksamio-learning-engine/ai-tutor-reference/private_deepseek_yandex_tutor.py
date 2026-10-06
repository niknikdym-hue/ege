"""PARTIAL A9.2 deterministic foundation; no private harness or live dialogue."""

import hashlib
import json
import math

_DOMAIN = "eksamio.private-deepseek.request.v1"
_USAGE_FIELDS = ("input_tokens", "output_tokens", "call_count", "reserved_minor_units", "latency_ms")


def _validate_json_value(value):
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite numbers are not JSON-compatible")
        return
    if type(value) is list:
        for item in value:
            _validate_json_value(item)
        return
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise TypeError("JSON object keys must be strings")
        for item in value.values():
            _validate_json_value(item)
        return
    raise TypeError("value is not JSON-compatible")


def fingerprint_request(request_id, session_ref, payload):
    """Return a SHA-256 digest of the canonical validated request envelope."""
    if type(request_id) is not str or not request_id:
        raise ValueError("request_id must be a nonempty string")
    if type(session_ref) is not str or not session_ref:
        raise ValueError("session_ref must be a nonempty string")
    if type(payload) is not dict:
        raise TypeError("payload must be an object")
    _validate_json_value(payload)
    envelope = {"domain": _DOMAIN, "request_id": request_id, "session_ref": session_ref, "payload": payload}
    encoded = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def safe_usage_metadata(metadata):
    """Copy only allowlisted, finite numeric usage values."""
    if type(metadata) is not dict:
        raise TypeError("metadata must be a plain dict")
    result = {}
    for name in _USAGE_FIELDS:
        if name not in metadata:
            continue
        value = metadata[name]
        if name == "latency_ms":
            valid = (type(value) is int and value >= 0) or (
                type(value) is float and math.isfinite(value) and value >= 0
            )
        else:
            valid = type(value) is int and value >= 0
        if valid:
            result[name] = value
    return result

import base64
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from eksamio_learning_engine_import_shim import load_command_verify


verify = load_command_verify()


class OwnerControlCommandVerifyTest(unittest.TestCase):
    def _keypair(self):
        root = tempfile.TemporaryDirectory()
        root_path = Path(root.name)
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "Ed25519", "-out", str(root_path / "private.pem")],
            check=True,
            capture_output=True,
        )
        der = subprocess.check_output(
            ["openssl", "pkey", "-in", str(root_path / "private.pem"), "-pubout", "-outform", "DER"]
        )
        raw = der[-32:]
        return root, root_path, base64.urlsafe_b64encode(raw).decode().rstrip("=")

    def _envelope(self, private_path: Path, now: int):
        payload = {
            "schema_version": "owner-control-command-v1",
            "command_id": "a" * 32,
            "repository": "niknikdym-hue/ege",
            "issued_at": now,
            "expires_at": now + 180,
            "approved_main_sha": "b" * 40,
            "target_base_ref": "owner/api-codex-smoke-base-20260922",
            "target_base_sha": "c" * 40,
            "task_ids": ["A1.4"],
            "package_budget_usd": "0.10",
            "tasks": [{
                "task_id": "A1.4",
                "execution_mode": "ai",
                "route_model": "gpt-5.6-luna",
                "astra_plan_required": False,
                "astra_acceptance_required": False,
                "allowed_paths": ["docs/project-control/OWNER-CONTROL-API-CODEX-SMOKE-TARGET-2026-09-22.md"],
            }],
            "auto_retry": False,
            "auto_merge": False,
            "auto_deploy": False,
            "auto_ready": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/"payload").write_bytes(verify.canonical_payload(payload))
            subprocess.run([
                "openssl","pkeyutl","-sign","-inkey",str(private_path),
                "-rawin","-in",str(p/"payload"),"-out",str(p/"sig")
            ],check=True,capture_output=True)
            sig=(p/"sig").read_bytes()
        public_raw=subprocess.check_output([
            "openssl","pkey","-in",str(private_path),"-pubout","-outform","DER"
        ])[-32:]
        key_id=__import__("hashlib").sha256(public_raw).hexdigest()[:16]
        return {
            "payload": payload,
            "signature": {
                "alg": "Ed25519",
                "key_id": key_id,
                "value": base64.urlsafe_b64encode(sig).decode().rstrip("="),
            },
        }

    def test_valid_signed_command(self):
        now=int(time.time())
        root, p, public = self._keypair()
        try:
            envelope=self._envelope(p/"private.pem", now)
            out=verify.verify_envelope(envelope, public_key_b64=public, now=now)
            self.assertEqual(out["task_ids"], ["A1.4"])
            self.assertEqual(out["package_budget_usd"], "0.10")
        finally:
            root.cleanup()

    def test_unknown_field_expired_and_tampering_fail_closed(self):
        now=int(time.time())
        root, p, public = self._keypair()
        try:
            original=self._envelope(p/"private.pem", now)
            bad=json.loads(json.dumps(original))
            bad["payload"]["unexpected"]=1
            with self.assertRaises(verify.CommandVerificationError):
                verify.verify_envelope(bad, public_key_b64=public, now=now)

            expired=self._envelope(p/"private.pem", now-400)
            with self.assertRaises(verify.CommandVerificationError):
                verify.verify_envelope(expired, public_key_b64=public, now=now)

            tampered=self._envelope(p/"private.pem", now)
            tampered["payload"]["package_budget_usd"]="0.11"
            with self.assertRaises(verify.CommandVerificationError):
                verify.verify_envelope(tampered, public_key_b64=public, now=now)
        finally:
            root.cleanup()


if __name__ == "__main__":
    unittest.main()

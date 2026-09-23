#!/usr/bin/env python3
"""Read-only Pro entitlement projection bound to a server-owned learner profile."""
from __future__ import annotations

import time
from typing import Any, Callable


class EntitlementReadError(ValueError):
    pass


class ProEntitlementReader:
    """Read the accepted payment entitlement state without payment execution."""

    PRODUCT_CODE = "EKSAMIO_PRO_RUSSIAN"

    def __init__(
        self,
        connection: Any,
        *,
        now_provider: Callable[[], int] | None = None,
    ) -> None:
        self.connection = connection
        self.now_provider = now_provider or (lambda: int(time.time()))

    @staticmethod
    def _validate_learner(learner_profile_id: str) -> str:
        if (
            not isinstance(learner_profile_id, str)
            or not learner_profile_id.startswith("learner:")
            or "@" in learner_profile_id
        ):
            raise EntitlementReadError("server-owned learner profile is required")
        return learner_profile_id

    def status(self, learner_profile_id: str) -> dict[str, Any]:
        learner_profile_id = self._validate_learner(learner_profile_id)
        now = int(self.now_provider())
        row = self.connection.execute(
            """
            SELECT entitlement_id, order_id, product_code,
                   starts_at_epoch, expires_at_epoch, state
            FROM pro_entitlements
            WHERE learner_profile_id = ?
              AND product_code = ?
              AND state = 'ACTIVE'
              AND starts_at_epoch <= ?
              AND expires_at_epoch > ?
            ORDER BY expires_at_epoch DESC, entitlement_id DESC
            LIMIT 1
            """,
            (learner_profile_id, self.PRODUCT_CODE, now, now),
        ).fetchone()
        if row is None:
            return {
                "active": False,
                "product_code": self.PRODUCT_CODE,
                "state": "INACTIVE",
            }
        return {
            "active": True,
            "product_code": str(row["product_code"]),
            "state": str(row["state"]),
            "starts_at_epoch": int(row["starts_at_epoch"]),
            "expires_at_epoch": int(row["expires_at_epoch"]),
        }


__all__ = ["EntitlementReadError", "ProEntitlementReader"]

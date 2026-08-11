#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parents[1]
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

import select_russian_exceptions_session as base
import select_russian_exceptions_session_current as current
import select_russian_exceptions_session_v2 as v2

NOW = datetime(2026, 8, 11, 19, 0, 0, tzinfo=timezone.utc)


def ex(exception_id: str) -> dict:
    return {"exception_id": exception_id, "skill_ids": ["orthographic_norms"], "status": "source_verified"}


def pr(pid: str, exception_id: str) -> dict:
    return {
        "practice_item_id": pid,
        "exception_id": exception_id,
        "mode": "context_choice",
        "transfer_level": "independent_context",
        "context_signature": f"ctx_{pid}",
        "status": "source_verified",
    }


class PrioritySelectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.exceptions = {"ex_p0": ex("ex_p0"), "ex_p2": ex("ex_p2"), "ex_p3": ex("ex_p3")}
        self.practice = {
            "ex_p0": [pr("p0", "ex_p0")],
            "ex_p2": [pr("p2", "ex_p2")],
            "ex_p3": [pr("p3", "ex_p3")],
        }
        self.priority_data = {
            "items": [
                {"exception_id":"ex_p0","launch_priority":"P0"},
                {"exception_id":"ex_p2","launch_priority":"P2"},
                {"exception_id":"ex_p3","launch_priority":"P3"},
            ]
        }

    def merged(self):
        return v2.apply_priorities(self.exceptions, self.priority_data)

    def test_new_p0_precedes_new_p2_and_p3(self):
        rows = current.select_session_current(
            self.merged(), self.practice, {}, count=3, now=NOW,
            source="all_exceptions", handoff=set()
        )
        self.assertEqual([x["exception_id"] for x in rows], ["ex_p0", "ex_p2", "ex_p3"])

    def test_due_p3_precedes_new_p0(self):
        states = {
            "ex_p3": {
                "status":"due",
                "seen_count":2,
                "next_due_at":"2026-08-10T10:00:00+00:00",
                "retention_passed":False,
            }
        }
        rows = current.select_session_current(
            self.merged(), self.practice, states, count=2, now=NOW,
            source="all_exceptions", handoff=set()
        )
        self.assertEqual(rows[0]["exception_id"], "ex_p3")
        self.assertEqual(rows[0]["reason_code"], "due_review")

    def test_missing_priority_row_fails_closed(self):
        incomplete = {"items":[{"exception_id":"ex_p0","launch_priority":"P0"}]}
        with self.assertRaises(base.SelectionError):
            v2.apply_priorities(self.exceptions, incomplete)

    def test_invalid_priority_fails_closed(self):
        invalid = {
            "items":[
                {"exception_id":"ex_p0","launch_priority":"P0"},
                {"exception_id":"ex_p2","launch_priority":"HARD"},
                {"exception_id":"ex_p3","launch_priority":"P3"},
            ]
        }
        with self.assertRaises(base.SelectionError):
            v2.apply_priorities(self.exceptions, invalid)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).parents[1] / "tools" / "eksamio_owner_console.py"
spec = importlib.util.spec_from_file_location("eksamio_owner_console", MODULE_PATH)
assert spec and spec.loader
console = importlib.util.module_from_spec(spec)
spec.loader.exec_module(console)


def channel(visitors=0, purchases=0, spend=0, gross=0, refunds=0):
    return {
        "qualified_visitors": visitors,
        "verified_purchases": purchases,
        "acquisition_spend_rub": spend,
        "gross_revenue_rub": gross,
        "refunds_rub": refunds,
    }


def period(visitors=100, meaningful=60, intent=30, checkout=20, purchases=10, gross=10000, refunds=1000, spend=2500):
    return {
        "qualified_visitors": visitors,
        "meaningful_learners": meaningful,
        "pro_intent": intent,
        "checkout_starts": checkout,
        "verified_paid_pro_customers": purchases,
        "gross_pro_revenue_rub": gross,
        "refunds_rub": refunds,
        "attributable_paid_spend_rub": spend,
        "channels": {
            "organic_seo": channel(50, 5, 0, 5000, 500),
            "yandex_direct_search": channel(30, 4, 2500, 4000, 400),
            "referral": channel(10, 1, 0, 1000, 100),
            "other_direct": channel(10, 0, 0, 0, 0),
        },
    }


def snapshot():
    p = period()
    return {
        "schema_version": "owner-console-v0.1",
        "generated_at": "2026-09-01T08:00:00+03:00",
        "measurement": {
            "status": "OK",
            "sources": {"metrika": "OK", "direct": "OK", "payments": "OK", "referrals": "OK", "seo": "OK"},
        },
        "guardrails": {
            "stale_after_minutes": 180,
            "max_paid_cac_rub": 200,
            "min_checkout_sample": 10,
            "min_checkout_purchase_cvr": 0.6,
            "max_refund_rate": 0.05,
        },
        "periods": {"today": p, "7d": p, "30d": p},
        "trend_30d": [
            {"date": "2026-08-30", "verified_paid_pro_customers": 1, "attributable_paid_spend_rub": 200, "meaningful_learners": 10, "pro_intent": 3},
            {"date": "2026-08-31", "verified_paid_pro_customers": 2, "attributable_paid_spend_rub": 300, "meaningful_learners": 12, "pro_intent": 4},
            {"date": "2026-09-01", "verified_paid_pro_customers": 3, "attributable_paid_spend_rub": 450, "meaningful_learners": 14, "pro_intent": 5},
        ],
        "email": "must-not-leak@example.com",
    }


class OwnerConsoleTests(unittest.TestCase):
    def test_derives_verified_economics(self):
        data = console.normalize_snapshot(snapshot())
        metrics = data["periods"]["7d"]
        self.assertEqual(metrics["refund_adjusted_pro_revenue_rub"], 9000)
        self.assertEqual(metrics["paid_cac_rub"], 250)
        self.assertEqual(metrics["checkout_to_purchase_cvr"], 0.5)
        self.assertEqual(metrics["channels"]["yandex_direct_search"]["paid_cac_rub"], 625)

    def test_alerts_are_owner_guardrail_driven_and_capped_at_three(self):
        raw = snapshot()
        raw["measurement"]["status"] = "DEGRADED"
        data = console.normalize_snapshot(raw)
        alerts = console.build_alerts(data, "7d", now=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc))
        self.assertEqual(len(alerts), 3)
        self.assertTrue(any("Measurement status" in item for item in alerts))
        self.assertTrue(any("stale" in item for item in alerts))
        self.assertTrue(any("Paid CAC" in item for item in alerts))

    def test_html_contains_exact_first_screen_and_does_not_leak_unknown_fields(self):
        data = console.normalize_snapshot(snapshot())
        rendered = console.render_html(data)
        for label in ("Visitors", "Meaningful learners", "Checkout starts", "Paid Pro customers", "Pro revenue (net refunds)", "Paid CAC"):
            self.assertIn(label, rendered)
        for label in ("Organic SEO", "Yandex Direct Search", "Referral", "Other/direct"):
            self.assertIn(label, rendered)
        self.assertNotIn("must-not-leak@example.com", rendered)
        self.assertIn("Read-only commercial truth", rendered)

    def test_rejects_impossible_funnel(self):
        raw = snapshot()
        raw["periods"]["today"] = period(visitors=10, meaningful=11, intent=5, checkout=4, purchases=1)
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            console.normalize_snapshot(raw)

    def test_rejects_refunds_above_gross(self):
        raw = snapshot()
        raw["periods"]["7d"] = period(gross=100, refunds=101)
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            console.normalize_snapshot(raw)

    def test_rejects_channel_totals_that_do_not_reconcile_to_headline_truth(self):
        raw = snapshot()
        raw["periods"]["30d"]["channels"]["organic_seo"]["verified_purchases"] = 4
        with self.assertRaisesRegex(ValueError, "does not reconcile"):
            console.normalize_snapshot(raw)


if __name__ == "__main__":
    unittest.main()

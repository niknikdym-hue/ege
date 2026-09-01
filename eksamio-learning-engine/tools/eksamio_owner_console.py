#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "owner-console-v0.1"
PERIODS = ("today", "7d", "30d")
CHANNELS = (
    ("organic_seo", "Organic SEO"),
    ("yandex_direct_search", "Yandex Direct Search"),
    ("referral", "Referral"),
    ("other_direct", "Other/direct"),
)
CHANNEL_KEYS = {key for key, _ in CHANNELS}


def number(value: Any, path: str, *, integer: bool = False) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{path} must be a number")
    if value < 0 or not math.isfinite(float(value)):
        raise ValueError(f"{path} must be a finite non-negative number")
    if integer:
        if int(value) != value:
            raise ValueError(f"{path} must be an integer")
        return int(value)
    return float(value)


def optional_number(value: Any, path: str) -> float | None:
    return None if value is None else float(number(value, path))


def parse_timestamp(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{path} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{path} must include an explicit timezone offset")
    return parsed.isoformat()


def rate(numerator: float, denominator: float) -> float | None:
    return None if denominator <= 0 else numerator / denominator


def cac(spend: float, purchases: int) -> float | None:
    return None if purchases <= 0 else spend / purchases


def normalize_channel(raw: Any, path: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must be an object")
    visitors = int(number(raw.get("qualified_visitors", 0), f"{path}.qualified_visitors", integer=True))
    purchases = int(number(raw.get("verified_purchases", 0), f"{path}.verified_purchases", integer=True))
    spend = float(number(raw.get("acquisition_spend_rub", 0), f"{path}.acquisition_spend_rub"))
    gross = float(number(raw.get("gross_revenue_rub", 0), f"{path}.gross_revenue_rub"))
    refunds = float(number(raw.get("refunds_rub", 0), f"{path}.refunds_rub"))
    if refunds > gross:
        raise ValueError(f"{path}.refunds_rub cannot exceed gross_revenue_rub")
    return {
        "qualified_visitors": visitors,
        "verified_purchases": purchases,
        "purchase_cvr": rate(purchases, visitors),
        "acquisition_spend_rub": spend,
        "paid_cac_rub": cac(spend, purchases) if spend > 0 else None,
        "gross_revenue_rub": gross,
        "refunds_rub": refunds,
        "refund_adjusted_revenue_rub": gross - refunds,
    }


def reconcile_channels(channels: dict[str, dict[str, Any]], headline: dict[str, float | int], path: str) -> None:
    fields = {
        "qualified_visitors": "qualified_visitors",
        "verified_purchases": "verified_paid_pro_customers",
        "acquisition_spend_rub": "attributable_paid_spend_rub",
        "gross_revenue_rub": "gross_pro_revenue_rub",
        "refunds_rub": "refunds_rub",
    }
    for channel_field, headline_field in fields.items():
        actual = sum(float(item[channel_field]) for item in channels.values())
        expected = float(headline[headline_field])
        if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=0.005):
            raise ValueError(
                f"{path}.channels {channel_field} total {actual} does not reconcile to headline {expected}"
            )


def normalize_period(raw: Any, path: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must be an object")
    headline: dict[str, float | int] = {
        "qualified_visitors": int(number(raw.get("qualified_visitors"), f"{path}.qualified_visitors", integer=True)),
        "meaningful_learners": int(number(raw.get("meaningful_learners"), f"{path}.meaningful_learners", integer=True)),
        "pro_intent": int(number(raw.get("pro_intent"), f"{path}.pro_intent", integer=True)),
        "checkout_starts": int(number(raw.get("checkout_starts"), f"{path}.checkout_starts", integer=True)),
        "verified_paid_pro_customers": int(number(raw.get("verified_paid_pro_customers"), f"{path}.verified_paid_pro_customers", integer=True)),
        "gross_pro_revenue_rub": float(number(raw.get("gross_pro_revenue_rub"), f"{path}.gross_pro_revenue_rub")),
        "refunds_rub": float(number(raw.get("refunds_rub"), f"{path}.refunds_rub")),
        "attributable_paid_spend_rub": float(number(raw.get("attributable_paid_spend_rub"), f"{path}.attributable_paid_spend_rub")),
    }
    if headline["refunds_rub"] > headline["gross_pro_revenue_rub"]:
        raise ValueError(f"{path}.refunds_rub cannot exceed gross_pro_revenue_rub")

    funnel_names = (
        "qualified_visitors",
        "meaningful_learners",
        "pro_intent",
        "checkout_starts",
        "verified_paid_pro_customers",
    )
    for previous, current in zip(funnel_names, funnel_names[1:]):
        if headline[current] > headline[previous]:
            raise ValueError(f"{path}.{current} cannot exceed {previous}")

    raw_channels = raw.get("channels")
    if not isinstance(raw_channels, dict):
        raise ValueError(f"{path}.channels must be an object")
    if set(raw_channels) != CHANNEL_KEYS:
        raise ValueError(
            f"{path}.channels must contain exactly {sorted(CHANNEL_KEYS)}; got {sorted(raw_channels)}"
        )
    channels = {key: normalize_channel(raw_channels[key], f"{path}.channels.{key}") for key, _ in CHANNELS}
    reconcile_channels(channels, headline, path)

    funnel: list[dict[str, Any]] = []
    largest_index: int | None = None
    largest_drop = -1.0
    for index, name in enumerate(funnel_names):
        value = int(headline[name])
        previous = int(headline[funnel_names[index - 1]]) if index else None
        step_cvr = rate(value, previous) if previous is not None else None
        if previous and step_cvr is not None and (1 - step_cvr) > largest_drop:
            largest_drop = 1 - step_cvr
            largest_index = index
        funnel.append({"name": name, "count": value, "step_cvr": step_cvr})
    if largest_index is not None:
        funnel[largest_index]["largest_dropoff"] = True

    purchases = int(headline["verified_paid_pro_customers"])
    spend = float(headline["attributable_paid_spend_rub"])
    gross = float(headline["gross_pro_revenue_rub"])
    refunds = float(headline["refunds_rub"])
    return {
        **headline,
        "refund_adjusted_pro_revenue_rub": gross - refunds,
        "paid_cac_rub": cac(spend, purchases),
        "checkout_to_purchase_cvr": rate(purchases, int(headline["checkout_starts"])),
        "refund_rate": rate(refunds, gross),
        "funnel": funnel,
        "channels": channels,
    }


def normalize_trend(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > 30:
        raise ValueError("trend_30d must be an array with at most 30 points")
    out: list[dict[str, Any]] = []
    last_date: str | None = None
    for index, item in enumerate(raw):
        path = f"trend_30d[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{path} must be an object")
        date = item.get("date")
        if not isinstance(date, str):
            raise ValueError(f"{path}.date must be YYYY-MM-DD")
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"{path}.date must be YYYY-MM-DD") from exc
        if last_date is not None and date <= last_date:
            raise ValueError("trend_30d dates must be strictly increasing")
        last_date = date
        purchases = int(number(item.get("verified_paid_pro_customers", 0), f"{path}.verified_paid_pro_customers", integer=True))
        spend = float(number(item.get("attributable_paid_spend_rub", 0), f"{path}.attributable_paid_spend_rub"))
        out.append({
            "date": date,
            "verified_paid_pro_customers": purchases,
            "paid_cac_rub": cac(spend, purchases),
            "meaningful_learners": int(number(item.get("meaningful_learners", 0), f"{path}.meaningful_learners", integer=True)),
            "pro_intent": int(number(item.get("pro_intent", 0), f"{path}.pro_intent", integer=True)),
        })
    return out


def normalize_snapshot(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"snapshot schema_version must be {SCHEMA_VERSION!r}")
    generated_at = parse_timestamp(raw.get("generated_at"), "generated_at")
    measurement = raw.get("measurement")
    if not isinstance(measurement, dict) or not isinstance(measurement.get("status"), str):
        raise ValueError("measurement.status must be a non-empty string")
    status = measurement["status"].strip().upper()
    if not status:
        raise ValueError("measurement.status must be a non-empty string")
    source_raw = measurement.get("sources", {})
    if not isinstance(source_raw, dict):
        raise ValueError("measurement.sources must be an object")
    sources: dict[str, str] = {}
    for key in ("metrika", "direct", "payments", "referrals", "seo"):
        value = source_raw.get(key, "UNKNOWN")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"measurement.sources.{key} must be a non-empty string")
        sources[key] = value.strip().upper()

    raw_guardrails = raw.get("guardrails", {})
    if not isinstance(raw_guardrails, dict):
        raise ValueError("guardrails must be an object")
    guardrails = {
        "stale_after_minutes": optional_number(raw_guardrails.get("stale_after_minutes"), "guardrails.stale_after_minutes"),
        "max_paid_cac_rub": optional_number(raw_guardrails.get("max_paid_cac_rub"), "guardrails.max_paid_cac_rub"),
        "min_checkout_sample": int(number(raw_guardrails.get("min_checkout_sample", 0), "guardrails.min_checkout_sample", integer=True)),
        "min_checkout_purchase_cvr": optional_number(raw_guardrails.get("min_checkout_purchase_cvr"), "guardrails.min_checkout_purchase_cvr"),
        "max_refund_rate": optional_number(raw_guardrails.get("max_refund_rate"), "guardrails.max_refund_rate"),
    }
    for key in ("min_checkout_purchase_cvr", "max_refund_rate"):
        if guardrails[key] is not None and guardrails[key] > 1:
            raise ValueError(f"guardrails.{key} must be between 0 and 1")

    raw_periods = raw.get("periods")
    if not isinstance(raw_periods, dict) or set(raw_periods) != set(PERIODS):
        raise ValueError(f"periods must contain exactly {list(PERIODS)}")
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "measurement": {"status": status, "sources": sources},
        "guardrails": guardrails,
        "periods": {p: normalize_period(raw_periods[p], f"periods.{p}") for p in PERIODS},
        "trend_30d": normalize_trend(raw.get("trend_30d")),
    }


def snapshot_age_minutes(snapshot: dict[str, Any], now: datetime | None = None) -> float:
    generated = datetime.fromisoformat(snapshot["generated_at"]).astimezone(timezone.utc)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return max(0.0, (current - generated).total_seconds() / 60)


def build_alerts(snapshot: dict[str, Any], period: str, *, now: datetime | None = None) -> list[str]:
    m, g = snapshot["periods"][period], snapshot["guardrails"]
    alerts: list[tuple[int, str]] = []
    if snapshot["measurement"]["status"] != "OK":
        alerts.append((100, f"Measurement status is {snapshot['measurement']['status']}; verify source coverage before changing acquisition."))
    if g["stale_after_minutes"] is not None:
        age = snapshot_age_minutes(snapshot, now)
        if age > g["stale_after_minutes"]:
            alerts.append((95, f"Analytics snapshot is stale ({age:.0f} min > {g['stale_after_minutes']:.0f} min guardrail)."))
    if m["attributable_paid_spend_rub"] > 0 and m["verified_paid_pro_customers"] == 0:
        alerts.append((90, f"Paid spend is ₽{m['attributable_paid_spend_rub']:,.0f} with zero server-confirmed Pro purchases in {period}."))
    if g["max_paid_cac_rub"] is not None and m["paid_cac_rub"] is not None and m["paid_cac_rub"] > g["max_paid_cac_rub"]:
        alerts.append((85, f"Paid CAC is ₽{m['paid_cac_rub']:,.0f}, above the Owner guardrail of ₽{g['max_paid_cac_rub']:,.0f}."))
    if (g["min_checkout_purchase_cvr"] is not None and m["checkout_starts"] >= g["min_checkout_sample"] and
            m["checkout_to_purchase_cvr"] is not None and m["checkout_to_purchase_cvr"] < g["min_checkout_purchase_cvr"]):
        alerts.append((80, f"Checkout→purchase CVR is {m['checkout_to_purchase_cvr']:.1%}, below the Owner guardrail of {g['min_checkout_purchase_cvr']:.1%}."))
    if g["max_refund_rate"] is not None and m["refund_rate"] is not None and m["refund_rate"] > g["max_refund_rate"]:
        alerts.append((75, f"Refund rate is {m['refund_rate']:.1%}, above the Owner guardrail of {g['max_refund_rate']:.1%}."))
    return [message for _, message in sorted(alerts, reverse=True)[:3]]


def safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_html(snapshot: dict[str, Any], *, initial_period: str = "7d") -> str:
    if initial_period not in PERIODS:
        raise ValueError(f"initial period must be one of {PERIODS}")
    payload = {**snapshot, "alerts": {p: build_alerts(snapshot, p) for p in PERIODS}}
    embedded = safe_json(payload)
    generated = html.escape(snapshot["generated_at"])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eksamio Owner Console</title><style>
body{{margin:0;background:#f6f7f9;color:#15171a;font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{max-width:1160px;margin:auto;padding:28px 20px}}header{{display:flex;justify-content:space-between;gap:16px}}h1{{margin:0}}.muted{{color:#68707b}}button,.card,section,.pill{{background:white;border:1px solid #dfe3e8;border-radius:10px}}button{{padding:8px 11px;margin-left:5px}}button[aria-pressed="true"]{{font-weight:700;border-color:#555}}.status{{display:flex;gap:7px;flex-wrap:wrap;margin:15px 0}}.pill{{padding:5px 8px}}.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:9px}}.card{{padding:13px}}.label{{font-size:12px;color:#68707b}}.value{{font-size:22px;font-weight:700}}section{{padding:15px;margin-top:11px}}.funnel{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}.step{{border:1px solid #dfe3e8;border-radius:8px;padding:10px}}.drop{{border-color:#8f1d1d}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #e5e7eb;text-align:right}}th:first-child,td:first-child{{text-align:left}}.alerts{{color:#8f1d1d}}#trend{{width:100%;height:180px}}@media(max-width:850px){{.grid{{grid-template-columns:repeat(3,1fr)}}.funnel{{grid-template-columns:1fr}}}}@media(max-width:520px){{header{{display:block}}.grid{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><main><header><div><h1>Eksamio Owner Console</h1><div class="muted">Read-only commercial truth · generated {generated}</div></div><div id="periods"></div></header><div class="status" id="status"></div><div class="grid" id="kpis"></div>
<section><h2>Funnel</h2><div class="funnel" id="funnel"></div></section><section><h2>Channels</h2><div style="overflow:auto"><table><thead><tr><th>Channel</th><th>Qualified visitors</th><th>Verified purchases</th><th>Purchase CVR</th><th>Spend</th><th>CAC</th><th>Refund-adjusted revenue</th></tr></thead><tbody id="channels"></tbody></table></div></section><section><h2>30-day trend</h2><svg id="trend" viewBox="0 0 1000 180"></svg><div class="muted" id="trendLegend"></div></section><section><h2>Priority signals</h2><div id="alerts"></div></section></main>
<script id="owner-data" type="application/json">{embedded}</script><script>
const D=JSON.parse(document.getElementById('owner-data').textContent);let p={json.dumps(initial_period)};const PL={{today:'Today','7d':'7 days','30d':'30 days'}},CL={{organic_seo:'Organic SEO',yandex_direct_search:'Yandex Direct Search',referral:'Referral',other_direct:'Other/direct'}},FL={{qualified_visitors:'Visit',meaningful_learners:'Meaningful learning',pro_intent:'Pro intent',checkout_starts:'Checkout',verified_paid_pro_customers:'Verified purchase'}};const n=v=>new Intl.NumberFormat('ru-RU').format(v),m=v=>v==null?'—':new Intl.NumberFormat('ru-RU',{{style:'currency',currency:'RUB',maximumFractionDigits:0}}).format(v),pct=v=>v==null?'—':(v*100).toFixed(1)+'%';function e(t,x,c){{const z=document.createElement(t);if(x!==undefined)z.textContent=x;if(c)z.className=c;return z}}
function periods(){{const r=document.getElementById('periods');r.textContent='';Object.keys(D.periods).forEach(x=>{{const b=e('button',PL[x]);b.setAttribute('aria-pressed',String(x===p));b.onclick=()=>{{p=x;render()}};r.appendChild(b)}})}}function status(){{const r=document.getElementById('status');r.textContent='';r.appendChild(e('span','Measurement: '+D.measurement.status,'pill'));Object.entries(D.measurement.sources).forEach(([k,v])=>r.appendChild(e('span',k+': '+v,'pill')))}}
function kpis(){{const x=D.periods[p],a=[['Visitors',n(x.qualified_visitors)],['Meaningful learners',n(x.meaningful_learners)],['Checkout starts',n(x.checkout_starts)],['Paid Pro customers',n(x.verified_paid_pro_customers)],['Pro revenue (net refunds)',m(x.refund_adjusted_pro_revenue_rub)],['Paid CAC',m(x.paid_cac_rub)]],r=document.getElementById('kpis');r.textContent='';a.forEach(([l,v])=>{{const c=e('div',undefined,'card');c.append(e('div',l,'label'),e('div',v,'value'));r.appendChild(c)}})}}
function funnel(){{const r=document.getElementById('funnel');r.textContent='';D.periods[p].funnel.forEach((x,i)=>{{const c=e('div',undefined,'step'+(x.largest_dropoff?' drop':''));c.append(e('div',FL[x.name],'label'),e('div',n(x.count),'value'),e('div',i?'Step CVR '+pct(x.step_cvr):'Entry','muted'));r.appendChild(c)}})}}function channels(){{const r=document.getElementById('channels');r.textContent='';Object.entries(D.periods[p].channels).forEach(([k,x])=>{{const tr=e('tr');[CL[k],n(x.qualified_visitors),n(x.verified_purchases),pct(x.purchase_cvr),m(x.acquisition_spend_rub),m(x.paid_cac_rub),m(x.refund_adjusted_revenue_rub)].forEach(v=>tr.appendChild(e('td',v)));r.appendChild(tr)}})}}
function alerts(){{const r=document.getElementById('alerts'),a=D.alerts[p]||[];r.textContent='';if(!a.length){{r.appendChild(e('div','No red signals from the configured guardrails.','muted'));return}}const ul=e('ul',undefined,'alerts');a.forEach(x=>ul.appendChild(e('li',x)));r.appendChild(ul)}}function trend(){{const s=document.getElementById('trend'),q=D.trend_30d||[],paid=q.filter(x=>x.paid_cac_rub!=null),use=paid.length>=3,a=q.map(x=>use?x.verified_paid_pro_customers:x.meaningful_learners),b=q.map(x=>use?(x.paid_cac_rub||0):x.pro_intent);s.textContent='';document.getElementById('trendLegend').textContent=use?'Paid customers + paid CAC (normalized scales)':'Leading indicators: meaningful learners + Pro intent';if(q.length<2)return;function line(values,y,dash){{const max=Math.max(...values,1),pts=values.map((v,i)=>(20+i*(960/(values.length-1)))+','+(y-(v/max)*65)).join(' '),z=document.createElementNS('http://www.w3.org/2000/svg','polyline');z.setAttribute('points',pts);z.setAttribute('fill','none');z.setAttribute('stroke','currentColor');z.setAttribute('stroke-width','2');if(dash)z.setAttribute('stroke-dasharray','7 5');s.appendChild(z)}}line(a,80,false);line(b,165,true)}}function render(){{periods();status();kpis();funnel();channels();trend();alerts()}}render();
</script></body></html>'''


def load_snapshot(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return normalize_snapshot(json.load(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description="Render read-only Eksamio Owner Console from an aggregate commercial snapshot")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--period", choices=PERIODS, default="7d")
    args = parser.parse_args()
    snapshot = load_snapshot(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(snapshot, initial_period=args.period), encoding="utf-8")
    print(json.dumps({"status": "OK", "mode": "READ_ONLY", "output": str(args.output), "schema": SCHEMA_VERSION}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)

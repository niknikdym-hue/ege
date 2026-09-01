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


def _number(value: Any, path: str, *, integer: bool = False) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{path} must be a number")
    if not math.isfinite(float(value)) or value < 0:
        raise ValueError(f"{path} must be a finite non-negative number")
    if integer:
        if int(value) != value:
            raise ValueError(f"{path} must be an integer")
        return int(value)
    return float(value)


def _optional_number(value: Any, path: str) -> float | None:
    if value is None:
        return None
    return float(_number(value, path))


def _parse_timestamp(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty ISO-8601 timestamp")
    raw = value.strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{path} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{path} must include an explicit timezone offset")
    return parsed.isoformat()


def _rate(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _cac(spend: float, purchases: int) -> float | None:
    if purchases <= 0:
        return None
    return spend / purchases


def _normalize_channel(raw: Any, path: str) -> dict[str, float | int | None]:
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must be an object")
    visitors = _number(raw.get("qualified_visitors", 0), f"{path}.qualified_visitors", integer=True)
    purchases = _number(raw.get("verified_purchases", 0), f"{path}.verified_purchases", integer=True)
    spend = _number(raw.get("acquisition_spend_rub", 0), f"{path}.acquisition_spend_rub")
    gross = _number(raw.get("gross_revenue_rub", 0), f"{path}.gross_revenue_rub")
    refunds = _number(raw.get("refunds_rub", 0), f"{path}.refunds_rub")
    if refunds > gross:
        raise ValueError(f"{path}.refunds_rub cannot exceed gross_revenue_rub")
    return {
        "qualified_visitors": visitors,
        "verified_purchases": purchases,
        "purchase_cvr": _rate(float(purchases), float(visitors)),
        "acquisition_spend_rub": spend,
        "paid_cac_rub": _cac(float(spend), int(purchases)) if spend > 0 else None,
        "refund_adjusted_revenue_rub": float(gross) - float(refunds),
    }


def _normalize_period(raw: Any, path: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must be an object")

    visitors = _number(raw.get("qualified_visitors"), f"{path}.qualified_visitors", integer=True)
    meaningful = _number(raw.get("meaningful_learners"), f"{path}.meaningful_learners", integer=True)
    pro_intent = _number(raw.get("pro_intent"), f"{path}.pro_intent", integer=True)
    checkout = _number(raw.get("checkout_starts"), f"{path}.checkout_starts", integer=True)
    purchases = _number(raw.get("verified_paid_pro_customers"), f"{path}.verified_paid_pro_customers", integer=True)
    gross = _number(raw.get("gross_pro_revenue_rub"), f"{path}.gross_pro_revenue_rub")
    refunds = _number(raw.get("refunds_rub"), f"{path}.refunds_rub")
    spend = _number(raw.get("attributable_paid_spend_rub"), f"{path}.attributable_paid_spend_rub")

    if refunds > gross:
        raise ValueError(f"{path}.refunds_rub cannot exceed gross_pro_revenue_rub")

    chain = (
        ("qualified_visitors", int(visitors)),
        ("meaningful_learners", int(meaningful)),
        ("pro_intent", int(pro_intent)),
        ("checkout_starts", int(checkout)),
        ("verified_paid_pro_customers", int(purchases)),
    )
    for (prev_name, prev_value), (name, value) in zip(chain, chain[1:]):
        if value > prev_value:
            raise ValueError(f"{path}.{name} cannot exceed {prev_name}")

    raw_channels = raw.get("channels")
    if not isinstance(raw_channels, dict):
        raise ValueError(f"{path}.channels must be an object")
    unknown = set(raw_channels) - CHANNEL_KEYS
    missing = CHANNEL_KEYS - set(raw_channels)
    if unknown:
        raise ValueError(f"{path}.channels has unsupported channels: {sorted(unknown)}")
    if missing:
        raise ValueError(f"{path}.channels is missing channels: {sorted(missing)}")

    channels = {key: _normalize_channel(raw_channels[key], f"{path}.channels.{key}") for key, _ in CHANNELS}
    net_revenue = float(gross) - float(refunds)
    paid_cac = _cac(float(spend), int(purchases))

    funnel_values = [value for _, value in chain]
    funnel = []
    largest_drop_index: int | None = None
    largest_drop = -1.0
    for index, (name, value) in enumerate(chain):
        previous = funnel_values[index - 1] if index > 0 else None
        conversion = _rate(float(value), float(previous)) if previous is not None else None
        if previous and conversion is not None:
            drop = 1.0 - conversion
            if drop > largest_drop:
                largest_drop = drop
                largest_drop_index = index
        funnel.append({"name": name, "count": value, "step_cvr": conversion})
    if largest_drop_index is not None:
        funnel[largest_drop_index]["largest_dropoff"] = True

    return {
        "qualified_visitors": visitors,
        "meaningful_learners": meaningful,
        "pro_intent": pro_intent,
        "checkout_starts": checkout,
        "verified_paid_pro_customers": purchases,
        "gross_pro_revenue_rub": float(gross),
        "refunds_rub": float(refunds),
        "refund_adjusted_pro_revenue_rub": net_revenue,
        "attributable_paid_spend_rub": float(spend),
        "paid_cac_rub": paid_cac,
        "checkout_to_purchase_cvr": _rate(float(purchases), float(checkout)),
        "refund_rate": _rate(float(refunds), float(gross)),
        "funnel": funnel,
        "channels": channels,
    }


def _normalize_trend(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("trend_30d must be an array")
    result: list[dict[str, Any]] = []
    previous_date: str | None = None
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
        if previous_date is not None and date <= previous_date:
            raise ValueError("trend_30d dates must be strictly increasing")
        previous_date = date
        purchases = _number(item.get("verified_paid_pro_customers", 0), f"{path}.verified_paid_pro_customers", integer=True)
        spend = _number(item.get("attributable_paid_spend_rub", 0), f"{path}.attributable_paid_spend_rub")
        meaningful = _number(item.get("meaningful_learners", 0), f"{path}.meaningful_learners", integer=True)
        pro_intent = _number(item.get("pro_intent", 0), f"{path}.pro_intent", integer=True)
        result.append(
            {
                "date": date,
                "verified_paid_pro_customers": purchases,
                "paid_cac_rub": _cac(float(spend), int(purchases)),
                "meaningful_learners": meaningful,
                "pro_intent": pro_intent,
            }
        )
    if len(result) > 30:
        raise ValueError("trend_30d may contain at most 30 daily points")
    return result


def normalize_snapshot(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("snapshot root must be an object")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION!r}")

    generated_at = _parse_timestamp(raw.get("generated_at"), "generated_at")
    measurement = raw.get("measurement")
    if not isinstance(measurement, dict):
        raise ValueError("measurement must be an object")
    status = measurement.get("status")
    if not isinstance(status, str) or not status.strip():
        raise ValueError("measurement.status must be a non-empty string")
    raw_sources = measurement.get("sources", {})
    if not isinstance(raw_sources, dict):
        raise ValueError("measurement.sources must be an object")
    sources: dict[str, str] = {}
    for key in ("metrika", "direct", "payments", "referrals", "seo"):
        value = raw_sources.get(key, "UNKNOWN")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"measurement.sources.{key} must be a non-empty string")
        sources[key] = value.strip().upper()

    guardrails_raw = raw.get("guardrails", {})
    if not isinstance(guardrails_raw, dict):
        raise ValueError("guardrails must be an object")
    guardrails = {
        "stale_after_minutes": _optional_number(guardrails_raw.get("stale_after_minutes"), "guardrails.stale_after_minutes"),
        "max_paid_cac_rub": _optional_number(guardrails_raw.get("max_paid_cac_rub"), "guardrails.max_paid_cac_rub"),
        "min_checkout_sample": int(_number(guardrails_raw.get("min_checkout_sample", 0), "guardrails.min_checkout_sample", integer=True)),
        "min_checkout_purchase_cvr": _optional_number(guardrails_raw.get("min_checkout_purchase_cvr"), "guardrails.min_checkout_purchase_cvr"),
        "max_refund_rate": _optional_number(guardrails_raw.get("max_refund_rate"), "guardrails.max_refund_rate"),
    }
    for key in ("min_checkout_purchase_cvr", "max_refund_rate"):
        value = guardrails[key]
        if value is not None and value > 1:
            raise ValueError(f"guardrails.{key} must be between 0 and 1")

    raw_periods = raw.get("periods")
    if not isinstance(raw_periods, dict):
        raise ValueError("periods must be an object")
    if set(raw_periods) != set(PERIODS):
        raise ValueError(f"periods must contain exactly {list(PERIODS)}")
    periods = {period: _normalize_period(raw_periods[period], f"periods.{period}") for period in PERIODS}

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "measurement": {"status": status.strip().upper(), "sources": sources},
        "guardrails": guardrails,
        "periods": periods,
        "trend_30d": _normalize_trend(raw.get("trend_30d")),
    }


def snapshot_age_minutes(snapshot: dict[str, Any], *, now: datetime | None = None) -> float:
    generated = datetime.fromisoformat(snapshot["generated_at"])
    current = now or datetime.now(timezone.utc)
    return max(0.0, (current.astimezone(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds() / 60.0)


def build_alerts(snapshot: dict[str, Any], period: str, *, now: datetime | None = None) -> list[str]:
    metrics = snapshot["periods"][period]
    guardrails = snapshot["guardrails"]
    alerts: list[tuple[int, str]] = []

    if snapshot["measurement"]["status"] != "OK":
        alerts.append((100, f"Measurement status is {snapshot['measurement']['status']}; verify source coverage before changing acquisition."))

    stale_after = guardrails["stale_after_minutes"]
    if stale_after is not None:
        age = snapshot_age_minutes(snapshot, now=now)
        if age > stale_after:
            alerts.append((95, f"Analytics snapshot is stale ({age:.0f} min > {stale_after:.0f} min guardrail)."))

    spend = metrics["attributable_paid_spend_rub"]
    purchases = metrics["verified_paid_pro_customers"]
    if spend > 0 and purchases == 0:
        alerts.append((90, f"Paid spend is ₽{spend:,.0f} with zero server-confirmed Pro purchases in {period}."))

    max_cac = guardrails["max_paid_cac_rub"]
    cac = metrics["paid_cac_rub"]
    if max_cac is not None and cac is not None and cac > max_cac:
        alerts.append((85, f"Paid CAC is ₽{cac:,.0f}, above the Owner guardrail of ₽{max_cac:,.0f}."))

    min_sample = guardrails["min_checkout_sample"]
    min_cvr = guardrails["min_checkout_purchase_cvr"]
    checkout = metrics["checkout_starts"]
    cvr = metrics["checkout_to_purchase_cvr"]
    if min_cvr is not None and checkout >= min_sample and cvr is not None and cvr < min_cvr:
        alerts.append((80, f"Checkout→purchase CVR is {cvr:.1%}, below the Owner guardrail of {min_cvr:.1%}."))

    max_refund_rate = guardrails["max_refund_rate"]
    refund_rate = metrics["refund_rate"]
    if max_refund_rate is not None and refund_rate is not None and refund_rate > max_refund_rate:
        alerts.append((75, f"Refund rate is {refund_rate:.1%}, above the Owner guardrail of {max_refund_rate:.1%}."))

    alerts.sort(key=lambda item: item[0], reverse=True)
    return [message for _, message in alerts[:3]]


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_html(snapshot: dict[str, Any], *, initial_period: str = "7d") -> str:
    if initial_period not in PERIODS:
        raise ValueError(f"initial period must be one of {PERIODS}")
    payload = dict(snapshot)
    payload["alerts"] = {period: build_alerts(snapshot, period) for period in PERIODS}
    embedded = _safe_json(payload)
    generated = html.escape(snapshot["generated_at"])

    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>Eksamio Owner Console</title>
<style>
:root{{--bg:#f6f7f9;--card:#fff;--text:#15171a;--muted:#68707b;--line:#dfe3e8;--danger:#8f1d1d;--accent:#1f5f99}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:28px 20px 48px}} header{{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;margin-bottom:20px}}
h1{{font-size:24px;margin:0 0 4px}} .sub{{color:var(--muted)}} .periods{{display:flex;gap:6px;flex-wrap:wrap}} button{{border:1px solid var(--line);background:var(--card);padding:8px 12px;border-radius:8px;cursor:pointer}} button[aria-pressed=\"true\"]{{border-color:var(--accent);font-weight:650}}
.status{{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 16px}} .pill{{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:5px 9px}} .grid{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin:16px 0}} .card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}} .label{{color:var(--muted);font-size:12px}} .value{{font-size:24px;font-weight:700;margin-top:5px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-top:12px}} h2{{font-size:16px;margin:0 0 12px}} .funnel{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}} .step{{padding:12px;border:1px solid var(--line);border-radius:9px}} .step.drop{{border-color:#b66}} .step .count{{font-size:20px;font-weight:700}} .step .rate{{color:var(--muted);font-size:12px}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:9px 8px;border-bottom:1px solid var(--line);text-align:right}} th:first-child,td:first-child{{text-align:left}} th{{color:var(--muted);font-size:12px;font-weight:600}} .alerts{{margin:0;padding-left:20px}} .alerts li{{margin:7px 0;color:var(--danger)}} .quiet{{color:var(--muted)}} #trend{{width:100%;height:180px;display:block}} .legend{{color:var(--muted);font-size:12px;margin-top:6px}}
@media(max-width:900px){{.grid{{grid-template-columns:repeat(3,1fr)}}.funnel{{grid-template-columns:1fr}}}} @media(max-width:560px){{header{{display:block}}.periods{{margin-top:12px}}.grid{{grid-template-columns:repeat(2,1fr)}}table{{font-size:12px}}}}
</style>
</head>
<body>
<main>
<header><div><h1>Eksamio Owner Console</h1><div class=\"sub\">Read-only commercial truth · generated {generated}</div></div><div class=\"periods\" id=\"periods\"></div></header>
<div class=\"status\" id=\"status\"></div>
<div class=\"grid\" id=\"kpis\"></div>
<section><h2>Funnel</h2><div class=\"funnel\" id=\"funnel\"></div></section>
<section><h2>Channels</h2><div style=\"overflow:auto\"><table><thead><tr><th>Channel</th><th>Qualified visitors</th><th>Verified purchases</th><th>Purchase CVR</th><th>Spend</th><th>CAC</th><th>Refund-adjusted revenue</th></tr></thead><tbody id=\"channels\"></tbody></table></div></section>
<section><h2>30-day trend</h2><svg id=\"trend\" viewBox=\"0 0 1000 180\" role=\"img\" aria-label=\"30-day business trend\"></svg><div class=\"legend\" id=\"trendLegend\"></div></section>
<section><h2>Priority signals</h2><div id=\"alerts\"></div></section>
</main>
<script id=\"owner-data\" type=\"application/json\">{embedded}</script>
<script>
const DATA=JSON.parse(document.getElementById('owner-data').textContent);let period={json.dumps(initial_period)};
const labels={{today:'Today','7d':'7 days','30d':'30 days'}};
const channelLabels={{organic_seo:'Organic SEO',yandex_direct_search:'Yandex Direct Search',referral:'Referral',other_direct:'Other/direct'}};
const funnelLabels={{qualified_visitors:'Visit',meaningful_learners:'Meaningful learning',pro_intent:'Pro intent',checkout_starts:'Checkout',verified_paid_pro_customers:'Verified purchase'}};
const money=v=>v==null?'—':new Intl.NumberFormat('ru-RU',{{style:'currency',currency:'RUB',maximumFractionDigits:0}}).format(v);
const num=v=>new Intl.NumberFormat('ru-RU').format(v);const pct=v=>v==null?'—':(v*100).toFixed(1)+'%';
function node(tag,text,cls){{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e}}
function renderPeriods(){{const root=document.getElementById('periods');root.textContent='';Object.keys(DATA.periods).forEach(p=>{{const b=node('button',labels[p]);b.setAttribute('aria-pressed',String(p===period));b.onclick=()=>{{period=p;render()}};root.appendChild(b)}})}}
function renderStatus(){{const root=document.getElementById('status');root.textContent='';root.appendChild(node('span','Measurement: '+DATA.measurement.status,'pill'));Object.entries(DATA.measurement.sources).forEach(([k,v])=>root.appendChild(node('span',k+': '+v,'pill')))}}
function renderKpis(){{const m=DATA.periods[period];const items=[['Visitors',num(m.qualified_visitors)],['Meaningful learners',num(m.meaningful_learners)],['Checkout starts',num(m.checkout_starts)],['Paid Pro customers',num(m.verified_paid_pro_customers)],['Pro revenue (net refunds)',money(m.refund_adjusted_pro_revenue_rub)],['Paid CAC',money(m.paid_cac_rub)]];const root=document.getElementById('kpis');root.textContent='';items.forEach(([l,v])=>{{const c=node('div',undefined,'card');c.append(node('div',l,'label'),node('div',v,'value'));root.appendChild(c)}})}}
function renderFunnel(){{const root=document.getElementById('funnel');root.textContent='';DATA.periods[period].funnel.forEach((s,i)=>{{const c=node('div',undefined,'step'+(s.largest_dropoff?' drop':''));c.append(node('div',funnelLabels[s.name],'label'),node('div',num(s.count),'count'),node('div',i===0?'Entry':('Step CVR '+pct(s.step_cvr)),'rate'));root.appendChild(c)}})}}
function renderChannels(){{const root=document.getElementById('channels');root.textContent='';Object.entries(DATA.periods[period].channels).forEach(([key,c])=>{{const tr=document.createElement('tr');[channelLabels[key],num(c.qualified_visitors),num(c.verified_purchases),pct(c.purchase_cvr),money(c.acquisition_spend_rub),money(c.paid_cac_rub),money(c.refund_adjusted_revenue_rub)].forEach(v=>tr.appendChild(node('td',v)));root.appendChild(tr)}})}}
function renderAlerts(){{const root=document.getElementById('alerts');root.textContent='';const alerts=DATA.alerts[period]||[];if(!alerts.length){{root.appendChild(node('div','No red signals from the configured guardrails.','quiet'));return}}const ul=node('ul',undefined,'alerts');alerts.forEach(a=>ul.appendChild(node('li',a)));root.appendChild(ul)}}
function renderTrend(){{const svg=document.getElementById('trend');svg.textContent='';const pts=DATA.trend_30d||[];const paid=pts.filter(p=>p.paid_cac_rub!=null);const usePaid=paid.length>=3;const a=pts.map(p=>usePaid?p.verified_paid_pro_customers:p.meaningful_learners);const b=pts.map(p=>usePaid?(p.paid_cac_rub||0):p.pro_intent);document.getElementById('trendLegend').textContent=usePaid?'Paid customers + paid CAC (separate normalized scales)':'Leading indicators: meaningful learners + Pro intent (paid evidence not yet sufficient)';if(pts.length<2){{svg.appendChild(node('text','Not enough trend data yet.'));return}}const draw=(values,yBase)=>{{const max=Math.max(...values,1);const points=values.map((v,i)=>{{const x=20+i*(960/(values.length-1));const y=yBase-(v/max)*65;return x+','+y}}).join(' ');const line=document.createElementNS('http://www.w3.org/2000/svg','polyline');line.setAttribute('points',points);line.setAttribute('fill','none');line.setAttribute('stroke','currentColor');line.setAttribute('stroke-width','2');svg.appendChild(line)}};draw(a,80);draw(b,165)}}
function render(){{renderPeriods();renderStatus();renderKpis();renderFunnel();renderChannels();renderTrend();renderAlerts()}}render();
</script>
</body></html>"""


def load_snapshot(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return normalize_snapshot(json.load(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the read-only Eksamio Owner Console from an aggregate commercial snapshot")
    parser.add_argument("--input", type=Path, required=True, help="Aggregate owner-console JSON snapshot")
    parser.add_argument("--output", type=Path, required=True, help="Local HTML output path")
    parser.add_argument("--period", choices=PERIODS, default="7d", help="Initial period shown on open")
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

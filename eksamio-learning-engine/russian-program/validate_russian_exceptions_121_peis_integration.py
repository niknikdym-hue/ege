#!/usr/bin/env python3
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

MAIN = "b1732041738f4f7ad342b0114cec04d9aa0cf548"
COUNTS = {"EXACT": 91, "PARTIAL_COMPOSITE": 5, "BLOCKED": 25}
TOTAL, EXIDS, READY = 121, 88, 96


def die(msg):
    raise SystemExit("FAIL: " + msg)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"cannot read {path}: {e}")


def eq(actual, expected, label):
    if actual != expected:
        die(f"{label}: expected {expected!r}, got {actual!r}")


def sha_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_lines(values):
    data = "\n".join(sorted(values)) + "\n"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", type=Path, default=here / "RUSSIAN-EXCEPTIONS-121-PEIS-INTEGRATION-LEDGER-v0.1.json")
    ap.add_argument("--summary", type=Path, default=here / "RUSSIAN-EXCEPTIONS-121-PEIS-INTEGRATION-SUMMARY-v0.1.json")
    ap.add_argument("--inventory", type=Path, default=here.parent / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json")
    ap.add_argument("--source-corpus", type=Path)
    ap.add_argument("--source-manifest", type=Path)
    a = ap.parse_args()

    ledger, summary, inventory = load(a.ledger), load(a.summary), load(a.inventory)
    eq(ledger["baseline"]["current_main_sha"], MAIN, "ledger baseline main")
    eq(summary["baseline_main_sha"], MAIN, "summary baseline main")
    eq(ledger["baseline"]["active_cards"], TOTAL, "baseline cards")
    eq(ledger["baseline"]["represented_exception_ids"], EXIDS, "baseline exception IDs")

    fields = ledger["row_schema"]
    eq(fields, ["practice_item_id", "exception_id", "class_code", "semantic_codes", "candidate_codes", "gap_code"], "row schema")
    class_codes = ledger["class_codes"]
    sem_book, cand_book, gap_book = ledger["semantic_codebook"], ledger["candidate_codebook"], ledger["gap_codebook"]
    if len(set(sem_book.values())) != len(sem_book): die("semantic codebook values are not unique")
    if len(set(cand_book.values())) != len(cand_book): die("candidate codebook values are not unique")

    rows = []
    for raw in ledger["rows"]:
        if len(raw) != len(fields): die(f"row width mismatch: {raw[:2]}")
        r = dict(zip(fields, raw))
        if r["class_code"] not in class_codes: die(f"{r['practice_item_id']}: unknown class code")
        try:
            r["classification"] = class_codes[r["class_code"]]
            r["semantic_ids"] = [sem_book[x] for x in r["semantic_codes"]]
            r["candidate_refs"] = [cand_book[x] for x in r["candidate_codes"]]
            r["semantic_gap_key"] = gap_book[r["gap_code"]] if r["gap_code"] else None
        except KeyError as e:
            die(f"{r['practice_item_id']}: unknown code {e}")
        rows.append(r)

    eq(len(rows), TOTAL, "row count")
    pids = [r["practice_item_id"] for r in rows]
    exids = [r["exception_id"] for r in rows]
    eq(len(set(pids)), TOTAL, "unique practice_item_id")
    eq(len(set(exids)), EXIDS, "represented exception_id")
    counts = Counter(r["classification"] for r in rows)
    eq(dict(counts), COUNTS, "classification counts")
    eq(sum(counts[x] for x in ("EXACT", "PARTIAL_COMPOSITE")), READY, "integration-ready count")
    eq(ledger["service_boundary"]["semantic_integration_ready_cards"], READY, "ledger ready")
    eq(ledger["service_boundary"]["live_service_connected_cards"], 0, "ledger live")
    eq(summary["service_integration"]["semantic_evidence_integration_ready_cards"], READY, "summary ready")
    eq(summary["service_integration"]["live_connected_cards"], 0, "summary live")

    school = {o["source_id"] for o in inventory.get("objects", []) if o.get("source_system") == "school_canonical" and o.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"}
    candidates = {o["source_id"] for o in inventory.get("objects", []) if o.get("source_system") == "semantic_candidate" and o.get("audit_classification") == "MISSING_SUBJECT_SEMANTIC_CANDIDATE"}
    eq(len(school), 185, "canonical school identity count")
    used = set()
    by_pid = {r["practice_item_id"]: r for r in rows}
    for r in rows:
        pid, cls, targets, refs = r["practice_item_id"], r["classification"], r["semantic_ids"], r["candidate_refs"]
        unknown = set(refs) - candidates
        if unknown: die(f"{pid}: unknown candidate refs {sorted(unknown)}")
        for sid in targets:
            if sid not in school: die(f"{pid}: non-current canonical target {sid}")
            if sid.startswith("ru-"): die(f"{pid}: new ru-* target forbidden")
            used.add(sid)
        if cls == "EXACT" and len(targets) != 1: die(f"{pid}: EXACT must have one target")
        if cls == "PARTIAL_COMPOSITE" and not targets: die(f"{pid}: PARTIAL_COMPOSITE needs targets")
        if cls == "BLOCKED" and targets: die(f"{pid}: BLOCKED must not have canonical targets")

    for pid, rec in ledger.get("candidate_reconciliations", {}).items():
        if pid not in by_pid: die(f"reconciliation unknown item {pid}")
        eq(by_pid[pid]["classification"], "EXACT", f"{pid} reconciliation class")
        eq(rec.get("candidate_admitted"), False, f"{pid} candidate admission")
        refs = [cand_book[x] for x in rec.get("candidate_codes", [])]
        if set(refs) - candidates: die(f"{pid}: reconciliation unknown candidate")

    eq(digest_lines(pids), ledger["baseline"]["practice_item_ids_sha256"], "practice IDs digest")
    eq(digest_lines(list(set(exids))), ledger["baseline"]["exception_ids_sha256"], "exception IDs digest")
    pairs = [f"{r['practice_item_id']}\t{r['exception_id']}" for r in rows]
    eq(digest_lines(pairs), ledger["baseline"]["practice_exception_pairs_sha256"], "pair digest")

    sc = summary["classification"]
    for k, n in COUNTS.items(): eq(sc[k]["cards"], n, f"summary {k}")
    eq(sc["integration_ready"]["cards"], READY, "summary integration-ready")
    eq(sc["total"], TOTAL, "summary total")
    eq(summary["semantic_target_surface"]["canonical_school_ids_used"], len(used), "used school targets")
    eq(summary["semantic_target_surface"]["new_ru_ids_admitted"], 0, "new ru IDs")

    partial = {r["practice_item_id"] for r in rows if r["classification"] == "PARTIAL_COMPOSITE"}
    eq({x["practice_item_id"] for x in summary["partial_composite_rows"]}, partial, "partial row set")
    blocked = {r["practice_item_id"] for r in rows if r["classification"] == "BLOCKED"}
    listed = []
    for c in summary["blocked_clusters"]:
        eq(c["count"], len(c["practice_item_ids"]), f"cluster {c['cluster']} count")
        listed += c["practice_item_ids"]
    eq(len(listed), len(set(listed)), "blocked summary uniqueness")
    eq(set(listed), blocked, "blocked row set")

    if a.source_corpus:
        source = load(a.source_corpus)
        eq(len(source), TOTAL, "source corpus rows")
        eq(digest_lines([f"{x['practice_item_id']}\t{x['exception_id']}" for x in source]), ledger["baseline"]["practice_exception_pairs_sha256"], "source pair digest")
        eq(sha_file(a.source_corpus), ledger["baseline"]["extracted_corpus_sha256"], "source corpus sha256")
    if a.source_manifest:
        eq(sha_file(a.source_manifest), ledger["baseline"]["source_manifest_sha256"], "source manifest sha256")

    print("PASS Russian Exceptions 121-card PEIS integration ledger")
    print(f"baseline_main={MAIN}")
    print("rows=121 exception_ids=88")
    print("classification=EXACT:91 PARTIAL_COMPOSITE:5 BLOCKED:25")
    print("semantic_integration_ready=96/121 (79.34%)")
    print("live_service_connected=0/121")
    print(f"canonical_school_targets_used={len(used)}")
    print("new_ru_ids_admitted=0")
    print("source_corpus_checked=" + ("yes" if a.source_corpus else "no"))
    print("source_manifest_checked=" + ("yes" if a.source_manifest else "no"))

if __name__ == "__main__":
    main()

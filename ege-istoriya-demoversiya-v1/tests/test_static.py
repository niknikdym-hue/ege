from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
P="ege-istoriya-demoversiya"
exam=json.loads((ROOT/f"{P}-EXAM-DATA.json").read_text(encoding="utf-8"))
assert exam["version"]=="1.0.2"
assert exam["storage_key"]=="eksamio_ege_istoriya_demo_2026_v1_0_2"
assert exam["task_count"]==21 and len(exam["tasks"])==21
assert sum(t["max_score"] for t in exam["tasks"] if t["kind"]=="short")==20
assert sum(t["max_score"] for t in exam["tasks"] if t["kind"]=="extended")==22
assert exam["max_primary"]==42 and exam["duration_minutes"]==210
assert [t["answer"]["canonical"] for t in exam["tasks"][:12]]==["6235","132","3126","943517","4625","2456","6524","сорок пятом","Алексей Михайлович","Симбирск","Астрахань","56"]
expected_matching={1:(4,6),3:(4,6),4:(6,9),5:(4,6),7:(4,6)}
for n,(positions,options) in expected_matching.items():
    interaction=exam["tasks"][n-1].get("interaction")
    assert interaction and interaction["type"]=="matching_selects"
    assert len(interaction["labels"])==positions and interaction["option_count"]==options
required={13:"отсутствия неверных позиций",14:"переписанный целиком объёмный отрывок",15:"Может быть приведено другое обоснование",16:"Санкт-Петербург",17:"элементов 1 и 2",18:"Могут быть указаны другие причины",19:"содержаться в определении",20:"оцениваются только первый тезис",21:"указанный первым"}
for n,snippet in required.items():
    task=exam["tasks"][n-1]
    assert task["kind"]=="extended" and task.get("criteria_html")
    assert snippet.lower() in task["criteria_html"].lower(),(n,snippet)
    assert sorted(r["score"] for r in task["rubric"])==list(range(task["max_score"]+1))
blocks=sorted(ROOT.glob(f"{P}-T123-*.txt"))
contract=json.loads((ROOT/f"{P}-PACKAGE-CONTRACT.json").read_text(encoding="utf-8"))
assert len(blocks)==contract["t123_blocks"]==len(contract["load_order"])
assert max(f.stat().st_size for f in blocks)==contract["t123_max_bytes"]<55000
seo=(ROOT/f"{P}-SEO.txt").read_text(encoding="utf-8")
for line in seo.splitlines():
    if line.startswith(("PAGE_URL:","TITLE:","DESCRIPTION:","CANONICAL:")): assert "2026" not in line
preview=(ROOT/f"{P}-PREVIEW.html").read_text(encoding="utf-8")
assert "Официальный итог до экспертной проверки" in preview
assert "Официальные критерии ФИПИ" in preview
assert "eh-result-partial" in preview and "eh-match-grid" in preview
assert "eksamio_ege_istoriya_demo_2026_v1_0_2" in preview and "eksamio_ege_istoriya_demo_2026_v1_0_1" not in preview
for a in json.loads((ROOT/f"{P}-ASSET-MAP.json").read_text(encoding="utf-8")):
    f=ROOT/"assets"/a["file"];assert f.exists() and f.stat().st_size==a["bytes"]
print("STATIC PASS")

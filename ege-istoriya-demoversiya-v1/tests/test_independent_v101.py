from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
P="ege-istoriya-demoversiya"
exam=json.loads((ROOT/f"{P}-EXAM-DATA.json").read_text(encoding="utf-8"))
assert exam["version"]=="1.0.1"
assert exam["storage_key"].endswith("v1_0_1")
assert all(t.get("criteria_html") for t in exam["tasks"][12:])
assert "оцениваются только первый тезис" in exam["tasks"][19]["criteria_html"]
assert "указанный первым" in exam["tasks"][20]["criteria_html"]
assert exam["tasks"][18]["rubric"][1]["score"]==1
assert "смысл понятия не раскрыт" in exam["tasks"][18]["rubric"][1]["text"].lower()
preview=(ROOT/f"{P}-PREVIEW.html").read_text(encoding="utf-8")
assert "eh-result-partial" in preview and "Официальные критерии ФИПИ" in preview
assert "Официальный итог до экспертной проверки" in preview
print("INDEPENDENT CONTENT PASS")

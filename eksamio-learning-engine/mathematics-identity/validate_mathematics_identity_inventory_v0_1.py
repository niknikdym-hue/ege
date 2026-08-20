#!/usr/bin/env python3
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


inventory = load("MATHEMATICS-CURRENT-MAIN-INVENTORY-v0.1.json")
matrix = load("MATHEMATICS-SOURCE-MATRIX-2022-2026-v0.1.json")
foundation = load("MATHEMATICS-IDENTITY-MODEL-FOUNDATION-v0.1.json")

expected_model = "mathematics-identity-v0.1"
baseline = inventory["baseline"]["sha"]
assert baseline and len(baseline) == 40
assert matrix["baseline"]["sha"] == baseline
assert foundation["baseline"]["sha"] == baseline
assert inventory["subject_id"] == matrix["subject_id"] == foundation["subject_id"] == "mathematics"
assert inventory["identity_model_id"] == matrix["identity_model_id"] == foundation["identity_model_id"] == expected_model

cells = matrix["cells"]
assert len(cells) == 10
expected = {(route, year) for route in ("profile", "base") for year in range(2022, 2027)}
actual = {(cell["route"], cell["year"]) for cell in cells}
assert actual == expected
assert len(actual) == len(cells)

source_gaps = [cell for cell in cells if cell["source_status"] == "GAP"]
assert source_gaps == []
assert inventory["findings"]["explicit_source_gaps"] == []

base_2025 = next(cell for cell in cells if (cell["route"], cell["year"]) == ("base", 2025))
assert base_2025["source_status"] == "VERIFIED"
assert base_2025["package_status"] == "ROUTE_BUILD_ABSENT_CURRENT_MAIN"
required_base_2025_sources = [
    "matematika-source-2025/ege-2025-matematika-baza-demoversiya.pdf",
    "matematika-source-2025/ege-2025-matematika-baza-specifikatsiya.pdf",
    "matematika-source-2025/ege-2025-matematika-kodifikator.pdf",
]
for relative in required_base_2025_sources:
    assert (REPO / relative).is_file(), relative
assert {entry["ref"] for entry in base_2025["evidence"]} == set(required_base_2025_sources)

route_build_gaps = {(gap["route"], gap["year"]) for gap in inventory["findings"]["route_build_gaps"]}
assert route_build_gaps == {("profile", 2022), ("base", 2025)}

for cell in cells:
    assert cell.get("evidence"), (cell["route"], cell["year"])

assert foundation["canonical_semantic_identity_count"] == 0
assert inventory["findings"]["canonical_math_semantic_identities_admitted"] == 0
assert inventory["findings"]["route_independent_math_identity_layer_found"] is False
assert set(foundation["routes"]) == {"profile", "base"}
assert all(route["identity_model_id"] == expected_model for route in foundation["routes"].values())
assert all(route["role"] == "EXAM_ROUTE_OVERLAY" for route in foundation["routes"].values())

required = {"evidence_event_schema", "learner_state_schema", "mastery_contract", "readiness_contract", "retention_contract", "nba_contract", "reference_kernel"}
assert required <= set(foundation["shared_peis_reuse"])
assert required <= set(inventory["existing_shared_peis"])
assert foundation["parallel_engine_guards"]
assert all(value is False for value in foundation["parallel_engine_guards"].values())
assert inventory["scope_guards"]["create_parallel_math_learner_engine"] is False
assert inventory["scope_guards"]["change_runtime_or_production"] is False
assert inventory["scope_guards"]["change_shared_peis_contracts"] is False
assert "NO_PRODUCTION_INTEGRATION" in inventory["mode"]
assert "NO_PRODUCTION_INTEGRATION" in matrix["mode"]
assert "NO_PRODUCTION_INTEGRATION" in foundation["mode"]
assert foundation["next_gate"]["name"] == "MATHEMATICS-SEMANTIC-SLICE-001"

print("MATHEMATICS IDENTITY INVENTORY VALIDATION v0.1")
print("STATUS: PASS")
print(f"BASELINE: {baseline}")
print("MATRIX_CELLS: 10")
print("ROUTES: profile, base")
print("YEARS: 2022-2026")
print("CANONICAL_SEMANTIC_IDENTITIES_ADMITTED: 0")
print("EXPLICIT_SOURCE_GAPS: 0")
print("BASE_2025_SOURCE: VERIFIED_OFFICIAL_FIPI_FILES_PRESENT")
print("ROUTE_BUILD_GAPS: profile/2022, base/2025")
print("SHARED_PEIS_REUSE: PASS")
print("PARALLEL_MATH_LEARNER_ENGINE_CREATED: false")
print("PRODUCTION_INTEGRATION: false")

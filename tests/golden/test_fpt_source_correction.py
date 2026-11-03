"""Source/oracle regression only; this does not claim the Phase 2 S8 engine exists."""

import hashlib
import json
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "eval/fixtures/fpt_source_correction.json"


def operating_profit(values: dict[str, str]) -> int:
    return sum(
        int(values[code]) * sign
        for code, sign in [("20", 1), ("22", 1), ("25", -1), ("26", -1), ("23", -1)]
    )


@pytest.mark.golden
@pytest.mark.parametrize("period", ["current", "prior"])
def test_source_code30_equation(period: str) -> None:
    values = json.loads(FIXTURE.read_text(encoding="utf-8"))[period]
    assert operating_profit(values) == int(values["30"])


@pytest.mark.golden
def test_code30_detects_single_digit_reading_error_in_code23() -> None:
    values = json.loads(FIXTURE.read_text(encoding="utf-8"))["current"]
    correct = values["23"]
    corrupted = "97623971644"
    assert len(correct) == len(corrupted)
    assert sum(a != b for a, b in zip(correct, corrupted, strict=True)) == 1
    assert operating_profit(values) - int(values["30"]) == 0
    mutated = {**values, "23": corrupted}
    assert operating_profit(mutated) - int(values["30"]) == 20_000


@pytest.mark.golden
def test_current_fx_coincidence_is_not_an_approved_bridge() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    current, prior = fixture["current"], fixture["prior"]
    for values in (current, prior):
        assert int(values["24"]) + int(values["note18_fx"]) == int(values["23"])
    assert abs(int(current["note18_fx"]) - int(current["cf04"])) == 150_117
    assert abs(int(current["cf61"])) == 150_117
    prior_delta = abs(int(prior["note18_fx"]) - int(prior["cf04"]))
    assert abs(int(prior["cf61"])) - prior_delta == 90
    assert fixture["bridge_status"] == "UNVERIFIED"
    assert fixture["warning"] == "CLASSIFICATION_DIFFERENCE_UNRESOLVED"


@pytest.mark.golden
def test_evidence_images_and_crop_coordinates_match_recorded_hashes() -> None:
    evidence_path = ROOT / "docs/evidence/fpt_q1_2026/evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["read_values_vnd"]["B02_23"] == "97623991644"
    assert evidence["read_values_vnd"]["TM18_FX"] == "-1685413336"
    for item in evidence["rasters"] + evidence["crops"]:
        data = (evidence_path.parent / item["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        assert struct.unpack(">II", data[16:24]) == (item["width"], item["height"])
        if "bbox_xyxy" in item:
            x1, y1, x2, y2 = item["bbox_xyxy"]
            assert (x2 - x1, y2 - y1) == (item["width"], item["height"])

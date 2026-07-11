#!/usr/bin/env python3
"""Автоматическая проверка структуры, весов и покрытия ФОС."""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data" / "competency_map" / "mapping.csv"
COMPETENCIES = ROOT / "data" / "competency_map" / "competencies.yaml"

REQUIRED_FILES = [
    "README.md",
    "FOS_BRIEF.md",
    "docs/passport.md",
    "docs/matrix.md",
    "docs/project_criteria.md",
    "docs/peer_review.md",
    "docs/commission_criteria.md",
    "data/competency_map/roles.yaml",
    "data/competency_map/competencies.yaml",
    "data/competency_map/mapping.csv",
    "src/templates/peer_review_form.md",
    "src/templates/commission_form.md",
    "release/how_to_apply.md",
    "validation/report.md",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("отсутствуют обязательные файлы: " + ", ".join(missing))

    known_codes = set(
        re.findall(r"^\s*- code:\s*([A-Z]+-\d+\.\d+)\s*$", COMPETENCIES.read_text(encoding="utf-8"), re.MULTILINE)
    )
    if not known_codes:
        fail("в competencies.yaml не найдены коды индикаторов")

    with MAPPING.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))

    required_columns = {"indicator", "assessment", "assessment_weight_percent", "evidence"}
    if not rows or set(rows[0]) != required_columns:
        fail("mapping.csv имеет неверные или неполные столбцы")

    unknown = sorted({row["indicator"] for row in rows} - known_codes)
    if unknown:
        fail("в mapping.csv найдены неизвестные индикаторы: " + ", ".join(unknown))

    weights: dict[str, int] = {}
    for row in rows:
        assessment = row["assessment"].strip()
        try:
            weight = int(row["assessment_weight_percent"])
        except ValueError:
            fail(f"некорректный вес у средства {assessment}")
        if assessment in weights and weights[assessment] != weight:
            fail(f"для средства {assessment} указаны разные веса")
        weights[assessment] = weight
        if not row["evidence"].strip():
            fail(f"не указано свидетельство для {row['indicator']} / {assessment}")

    if sum(weights.values()) != 100:
        fail(f"сумма уникальных весов равна {sum(weights.values())}%, ожидалось 100%")

    coverage = Counter(row["indicator"] for row in rows)
    insufficient = sorted(code for code in known_codes if coverage[code] < 2)
    if insufficient:
        fail("менее двух средств у индикаторов: " + ", ".join(insufficient))

    print(f"PASS: обязательные файлы — {len(REQUIRED_FILES)}")
    print(f"PASS: сумма уникальных весов — {sum(weights.values())}%")
    print(f"PASS: индикаторы — {len(known_codes)}, покрытие каждого — не менее двух средств")
    print("PASS: mapping.csv согласован с competencies.yaml")


if __name__ == "__main__":
    main()

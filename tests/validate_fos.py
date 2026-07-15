#!/usr/bin/env python3
"""Автоматическая проверка структуры, весов и покрытия ФОС."""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data" / "competency_map" / "mapping.csv"
COMPETENCIES = ROOT / "data" / "competency_map" / "competencies.yaml"

REQUIRED_FILES = [
    "README.md",
    "FOS_BRIEF.md",
    "docs/passport.md",
    "docs/target_rpd.md",
    "docs/working_program.md",
    "docs/course_structure.md",
    "docs/prerequisites.md",
    "docs/measurement_model.md",
    "docs/fos_composition.md",
    "docs/matrix.md",
    "docs/project_criteria.md",
    "docs/peer_review.md",
    "docs/commission_criteria.md",
    "data/competency_map/roles.yaml",
    "data/competency_map/competencies.yaml",
    "data/competency_map/mapping.csv",
    "src/templates/peer_review_form.md",
    "src/templates/commission_form.md",
    "src/kims/current_control.md",
    "src/kims/laboratory_works.md",
    "src/kims/milestone_control.md",
    "src/kims/final_assessment.md",
    "resources/README.md",
    "resources/literature.md",
    "resources/datasets.md",
    "resources/tools.md",
    "resources/baselines_benchmarks.md",
    "resources/templates.md",
    "resources/prompts.md",
    "methodology/students.md",
    "methodology/teachers.md",
    "methodology/resource_usage.md",
    "release/how_to_apply.md",
    "release/printable/Рабочая_программа_Б1.В.05.docx",
    "release/printable/Рабочая_программа_Б1.В.05.pdf",
    "validation/report.md",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("отсутствуют обязательные файлы: " + ", ".join(missing))

    broken_links: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for markdown_path in ROOT.rglob("*.md"):
        for target in link_pattern.findall(markdown_path.read_text(encoding="utf-8")):
            target = target.strip().split(maxsplit=1)[0]
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative_target = unquote(target.split("#", 1)[0])
            if relative_target and not (markdown_path.parent / relative_target).resolve().exists():
                broken_links.append(f"{markdown_path.relative_to(ROOT)} -> {target}")
    if broken_links:
        fail("сломаны внутренние ссылки: " + "; ".join(broken_links))

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

    expected_weights = {
        "ЛР1": 8,
        "ЛР2": 8,
        "ЛР3": 8,
        "ЛР4": 8,
        "ЛР5": 8,
        "ЛР6": 8,
        "Текущий и рубежный контроль": 12,
        "Проект": 25,
        "Peer-review": 5,
        "Защита": 10,
    }
    if weights != expected_weights:
        fail(f"структура весов не совпадает с утверждённой: {weights}")

    coverage = Counter(row["indicator"] for row in rows)
    insufficient = sorted(code for code in known_codes if coverage[code] < 2)
    if insufficient:
        fail("менее двух средств у индикаторов: " + ", ".join(insufficient))

    print(f"PASS: обязательные файлы — {len(REQUIRED_FILES)}")
    print("PASS: внутренние Markdown-ссылки разрешаются")
    print(f"PASS: сумма уникальных весов — {sum(weights.values())}%")
    print("PASS: лабораторные — 6×8%, текущий и рубежный контроль — 12%")
    print(f"PASS: индикаторы — {len(known_codes)}, покрытие каждого — не менее двух средств")
    print("PASS: mapping.csv согласован с competencies.yaml")


if __name__ == "__main__":
    main()

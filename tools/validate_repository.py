#!/usr/bin/env python3
"""Проверка структуры, ссылок, баллов и покрытия ФОС."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data" / "competency_map" / "mapping.csv"
COMPETENCIES = ROOT / "data" / "competency_map" / "competencies.yaml"
RPD = ROOT / "docs" / "rpd.md"

REQUIRED_FILES = [
    "README.md",
    "repository-tree.txt",
    "CONTRIBUTING.md",
    "LICENSE.md",
    ".gitignore",
    "docs/README.md",
    "docs/rpd.md",
    "docs/quality-checklist.md",
    "docs/attachments/Рабочая_программа_Б1.В.05.docx",
    "docs/attachments/Рабочая_программа_Б1.В.05.pdf",
    "docs/attachments/ФОС_Б1.В.05_актуальный.docx",
    "docs/attachments/ФОС_Б1.В.05_актуальный.pdf",
    "M1-classical-ml/README.md",
    "M1-classical-ml/kim-01-lab-1.md",
    "M1-classical-ml/kim-02-lab-2.md",
    "M1-classical-ml/kim-03-lab-3.md",
    "M1-classical-ml/kim-04-lab-4.md",
    "M1-classical-ml/kim-05-current-and-milestone-control.md",
    "M2-neural-networks/README.md",
    "M2-neural-networks/kim-05-lab-5.md",
    "M2-neural-networks/kim-06-lab-6.md",
    "Project/README.md",
    "Project/rubric-project.md",
    "Project/peer-review.md",
    "Project/attachments/student-selfcheck.md",
    "Project/attachments/peer-review-form.md",
    "Project/attachments/supervisor-form.md",
    "Exam/README.md",
    "Exam/kim-final-assessment.md",
    "Exam/rubric-defense.md",
    "Exam/attachments/commission-form.md",
    "Exam/attachments/checklist-before-defense.md",
    "methodical-guidelines/README.md",
    "methodical-guidelines/students/README.md",
    "methodical-guidelines/teachers-assessment/README.md",
    "methodical-guidelines/teachers-assessment/rubric-laboratory.md",
    "methodical-guidelines/teachers-resources/README.md",
    "resources/README.md",
    "resources/textbooks/README.md",
    "resources/papers/README.md",
    "resources/test-banks/README.md",
    "resources/problem-banks/README.md",
    "resources/datasets/README.md",
    "resources/benchmarks/README.md",
    "resources/software/python-libs/README.md",
    "resources/llm-prompts/README.md",
    "resources/other/README.md",
    "data/README.md",
    "data/competency_map/roles.yaml",
    "data/competency_map/competencies.yaml",
    "data/competency_map/mapping.csv",
    "team/README.md",
    "tools/README.md",
    "tools/validate_repository.py",
    "other/README.md",
]

LEGACY_PATHS = [
    "src",
    "tests",
    "validation",
    "release",
    "methodology",
    "meta",
    "FOS_BRIEF.md",
    "CHANGELOG.md",
]

TEAM_MEMBERS = [
    "Маркина Татьяна Анатольевна",
    "Пахомов Максим Анатольевич",
    "Левченко Дмитрий Александрович",
    "Сорока Артем Александрович",
    "Чистяков Геннадий Андреевич",
    "Миронов Яков Константинович",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("отсутствуют обязательные файлы: " + ", ".join(missing))

    legacy = [path for path in LEGACY_PATHS if (ROOT / path).exists()]
    if legacy:
        fail("остались старые дублирующие пути: " + ", ".join(legacy))

    rpd_text = RPD.read_text(encoding="utf-8")
    level_fragments = [
        "| № | Раздел или тема | Всего | Л | ЛР | СРС | Индикаторы | Уровень |",
        "ML-2.1<br>ML-2.2 | Б<br>Б",
        "ML-2.3 | С",
        "DL-1.3<br>DL-1.4 | С<br>С",
    ]
    if any(fragment not in rpd_text for fragment in level_fragments):
        fail("в РПД отсутствуют ожидаемые уровни индикаторов")

    required_lab_fragments = {
        "M1-classical-ml/kim-01-lab-1.md": ["DummyClassifier", "60/20/20", "ML-2.1, ML-2.2"],
        "M1-classical-ml/kim-02-lab-2.md": ["StratifiedKFold", "минимум два способа", "ML-2.3"],
        "M1-classical-ml/kim-03-lab-3.md": ["StandardScaler + LogisticRegression", "RBF-ядро", "ML-3.1, ML-3.3"],
        "M1-classical-ml/kim-04-lab-4.md": ["permutation importance", "eval_set", "ML-3.2, ML-3.3"],
        "M2-neural-networks/kim-05-lab-5.md": ["сырые logits", "классическим baseline", "DL-1.1, DL-1.2"],
        "M2-neural-networks/kim-06-lab-6.md": ["минимум 20 ошибок", "параметр `weights`", "DL-1.3, DL-1.4"],
    }
    for path, fragments in required_lab_fragments.items():
        text = (ROOT / path).read_text(encoding="utf-8")
        if any(fragment not in text for fragment in fragments) or "8 баллов" not in text:
            fail(f"КИМ лабораторной заполнен неполно: {path}")

    broken_links: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for markdown_path in ROOT.rglob("*.md"):
        if ".git" in markdown_path.parts:
            continue
        for target in link_pattern.findall(markdown_path.read_text(encoding="utf-8")):
            target = target.strip().split(maxsplit=1)[0]
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative_target = unquote(target.split("#", 1)[0])
            if relative_target and not (markdown_path.parent / relative_target).resolve().exists():
                broken_links.append(f"{markdown_path.relative_to(ROOT)} -> {target}")
    if broken_links:
        fail("сломаны внутренние ссылки: " + "; ".join(broken_links))

    placeholders = [
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts and "[ЗАПОЛНИТЬ]" in path.read_text(encoding="utf-8")
    ]
    if placeholders:
        fail("остались маркеры незаполненных полей: " + ", ".join(placeholders))

    known_codes = set(
        re.findall(
            r"^\s*- code:\s*([A-Z]+-\d+\.\d+)\s*$",
            COMPETENCIES.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
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

    team_text = (ROOT / "team" / "README.md").read_text(encoding="utf-8")
    missing_members = [name for name in TEAM_MEMBERS if name not in team_text]
    if missing_members:
        fail("в составе команды отсутствуют: " + ", ".join(missing_members))

    print(f"PASS: обязательные файлы — {len(REQUIRED_FILES)}")
    print("PASS: старые дублирующие каталоги удалены")
    print("PASS: внутренние Markdown-ссылки разрешаются")
    print("PASS: маркеры незаполненных полей отсутствуют")
    print("PASS: лабораторные — 6×8=48 баллов")
    print("PASS: сумма оценочных средств — 100 баллов")
    print(f"PASS: индикаторы — {len(known_codes)}, покрытие каждого — не менее двух средств")
    print(f"PASS: команда — {len(TEAM_MEMBERS)} участников")


if __name__ == "__main__":
    main()

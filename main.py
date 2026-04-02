import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from models import analyst, career_advisor, quality_checker, salary_estimator
from utils.report_utils import (
    extract_json,
    validate_advisor_payload,
    validate_quality_payload,
    validate_salary_payload,
    validate_skill_map,
    write_reports,
)

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--role", type=str)

ROOT = Path(__file__).resolve().parent
MODEL_ANSWERS = ROOT / "model_answers"


if __name__ == "__main__":
    # обязательно нужна роль
    args = parser.parse_args()

    if args.role is None:
        print("--role не указан")
        sys.exit(1)

    # Первая модель, аналитик рынка
    raw_skill = analyst(args.role)
    skill_map = extract_json(raw_skill)
    skill_map.setdefault("role", args.role)
    validate_skill_map(skill_map)

    # сырой ответ первого агента в файл, для случаев, когда вылезает ошибка
    MODEL_ANSWERS.mkdir(parents=True, exist_ok=True)
    skill_map_path = MODEL_ANSWERS / "skill_map.json"
    skill_map_path.write_text(
        json.dumps(skill_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    skill_map_str = json.dumps(skill_map, ensure_ascii=False, indent=2)

    # Вторая модель, оценщик зарплат + сохранение в файл
    raw_salary = salary_estimator(skill_map)
    salary_payload = extract_json(raw_salary)
    validate_salary_payload(salary_payload)

    salary_path = MODEL_ANSWERS / "salary_table.json"
    salary_path.write_text(
        json.dumps(salary_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Третья модель, карьерный советник + сохранение в файл
    salary_str = json.dumps(salary_payload, ensure_ascii=False, indent=2)
    advisor_answer = career_advisor(skill_map, salary_str)
    advisor_payload = extract_json(advisor_answer)
    validate_advisor_payload(advisor_payload)

    advisor_path = MODEL_ANSWERS / "advisor_table.json"
    advisor_path.write_text(
        json.dumps(advisor_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Четвертая модель, критик + сохранение в файл
    full_report = {
        "skill_map": skill_map,
        "salary_table": salary_payload,
        "advisor_table": advisor_payload,
    }

    quality = quality_checker(full_report)
    quality_json = extract_json(quality)
    validate_quality_payload(quality_json)

    quality_path = MODEL_ANSWERS / "quality_table.json"
    quality_path.write_text(
        json.dumps(quality_json, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # итоговые report.json и report.md 
    final_report = write_reports(
        skill_map.get("role") or args.role,
        skill_map,
        salary_payload,
        advisor_payload,
        quality_json,
    )

    # print(json.dumps(final_report, ensure_ascii=False, indent=2))

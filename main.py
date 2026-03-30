import argparse
import json
import sys
from dotenv import load_dotenv
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from api_search import get_descriptions, get_role
from models import analyst, quality_checker, salary_estimator, career_advisor

load_dotenv()


parser = argparse.ArgumentParser()
parser.add_argument("--role", type=str)

ROOT = Path(__file__).resolve().parent
MODEL_ANSWERS = ROOT / "model_answers"



def extract_json(text):
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


if __name__ == "__main__":
    args = parser.parse_args()

    if args.role is None:
        print("--role не указан")
        sys.exit(1)


    raw_skill = analyst(args.role)
    skill_map = extract_json(raw_skill)

    MODEL_ANSWERS.mkdir(parents=True, exist_ok=True)
    skill_map_path = MODEL_ANSWERS / "skill_map.json"
    skill_map_path.write_text(
        json.dumps(skill_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    skill_map_str = json.dumps(skill_map, ensure_ascii=False, indent=2)


    raw_salary = salary_estimator(skill_map_str)
    salary_payload = extract_json(raw_salary)

    salary_path = MODEL_ANSWERS / "salary_table.json"
    salary_path.write_text(
        json.dumps(salary_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


    salary_str = json.dumps(salary_payload, ensure_ascii=False, indent=2)
    advisor_answer = career_advisor(skill_map_str, salary_str)
    advisor_payload = extract_json(advisor_answer)

    advisor_path = MODEL_ANSWERS / "advisor_table.json"
    advisor_path.write_text(
        json.dumps(advisor_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    full_report = {
        "skill_map": skill_map,
        "salary_table": salary_payload,
        "advisor_table": advisor_payload
    }

    quality = quality_checker(full_report)
    quality_json = extract_json(quality)

    quality_path = MODEL_ANSWERS / "quality_table.json"
    quality_path.write_text(
        json.dumps(quality_json, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print( json.dumps( {"skill_map": skill_map, "salary_table": salary_payload, "advisor_table": advisor_payload, "quality": quality_json}, ensure_ascii=False, indent=2, ) )
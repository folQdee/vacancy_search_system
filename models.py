import os
from dotenv import load_dotenv
import requests
from pathlib import Path
import json

from utils.api_search import build_salary_table, get_descriptions, get_role, get_top_employers

load_dotenv()

API_KEY = os.getenv('OPENROUTER_KEY')
MODEL = os.getenv("MODEL")
ROUTER_URL = os.getenv("ROUTER_BASE_URL")

ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "prompts"

# 1 модель
def analyst(role):
    descriptions = get_descriptions(get_role(role)) 
    all_texts = "\n\n".join(descriptions)
    analyst_prompt = (PROMPTS / "first_analyst.txt").read_text(encoding="utf-8")
    prompt = (
        analyst_prompt
        .replace("{text}", all_texts)
        .replace("{role}", role)
    )

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }
    )

    # resp = response.json()
    # print(resp)

    return response.json()["choices"][0]["message"]["content"]
    

# 2 модель
def salary_estimator(skill_map):
    # `skill_map` приходит либо как dict, либо как JSON-строка (main.py сейчас передавал строку).
    if isinstance(skill_map, str):
        try:
            skill_map_obj = json.loads(skill_map)
        except json.JSONDecodeError:
            skill_map_obj = {}
        skill_map_for_prompt = skill_map
    else:
        skill_map_obj = skill_map or {}
        skill_map_for_prompt = json.dumps(skill_map_obj, ensure_ascii=False, indent=2)

    role = str(skill_map_obj.get("role", "")).strip()
    if not role:
        languages = skill_map_obj.get("languages") or []
        top_language = languages[0].get("name") if languages else "developer"
        role = f"{top_language} developer"

    # Опорная выборка с hh.ru по запросу роли (тыс. руб. для РФ, Remote USD — грубая оценка в коде).
    hh_reference = build_salary_table(role)
    employers = get_top_employers(role)

    salary_prompt = (PROMPTS / "salary_estimator.txt").read_text(encoding="utf-8")
    prompt = salary_prompt \
        .replace("{role_title}", role) \
        .replace("{skill_map}", skill_map_for_prompt) \
        .replace("{salary_table}", json.dumps(hh_reference, ensure_ascii=False, indent=2)) \
        .replace("{top_employers}", json.dumps(employers, ensure_ascii=False))

    response = requests.post(
        ROUTER_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }
    )

    return response.json()["choices"][0]["message"]["content"]


# 3 модель
def career_advisor(skill_map, salary_table):
    # `skill_map` приходит либо как dict, либо как JSON-строка.
    if isinstance(skill_map, str):
        skill_map_for_prompt = skill_map
    else:
        skill_map_for_prompt = json.dumps(skill_map or {}, ensure_ascii=False, indent=2)

    # `salary_table` в main.py уже формируется как JSON-строка, но сделаем поддержку dict тоже.
    if isinstance(salary_table, str):
        salary_table_for_prompt = salary_table
    else:
        salary_table_for_prompt = json.dumps(salary_table or {}, ensure_ascii=False, indent=2)

    advisor_prompt = (PROMPTS / "career_advisor.txt").read_text(encoding="utf-8")
    prompt = (
        advisor_prompt
        .replace("{skill_map}", skill_map_for_prompt)
        .replace("{salary_table}", salary_table_for_prompt)
    )

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }
    )

    return response.json()["choices"][0]["message"]["content"]


def quality_checker(full_report):
    import json

    quality_prompt = (PROMPTS / "quality_checker.txt").read_text(encoding="utf-8")

    prompt = quality_prompt.replace(
        "{full_report}",
        json.dumps(full_report, ensure_ascii=False, indent=2)
    )

    response = requests.post(
        ROUTER_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }
    )

    return response.json()["choices"][0]["message"]["content"]

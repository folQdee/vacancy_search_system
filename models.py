import os
from dotenv import load_dotenv
import requests
from pathlib import Path
import json

from api_search import build_salary_table, get_descriptions, get_role, get_top_employers

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
    prompt = analyst_prompt.replace("{text}", all_texts)

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
    top_language = skill_map["languages"][0]["name"] if skill_map["languages"] else "developer"

    role = f"{top_language} developer"

    salary_table = build_salary_table(role)
    employers = get_top_employers(role)

    salary_prompt = (PROMPTS / "salary_estimator.txt").read_text(encoding="utf-8")
    prompt = salary_prompt \
        .replace("{skill_map}", skill_map) \
        .replace("{salary_table}", json.dumps(salary_table, ensure_ascii=False)) \
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
def career_advisor(prompt, skill_map, salary):
    prompt = prompt.replace("{skill_map}", skill_map).replace("{salary_table}", salary)

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
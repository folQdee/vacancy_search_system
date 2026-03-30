import os

from bs4 import BeautifulSoup
import requests
import numpy as np
from collections import defaultdict


GRADE_KEYWORDS = {
    "Junior": ["junior", "intern"],
    "Middle": ["middle"],
    "Senior": ["senior"],
    "Lead": ["lead", "head"]
}


def get_role(name, pages=2):
    vacancies = []
    url = os.getenv("HH_URL")

    for page in range(pages):
        params = {
            "text": name,
            "area": 1,
            "per_page": 1,
            "page": page,
        }
        res = requests.get(url, params=params).json()
        vacancies.extend(res["items"])

    return vacancies


def get_descriptions(items):
    texts = []

    for item in items:
        full = requests.get(f"https://api.hh.ru/vacancies/{item['id']}").json()
        html = full["description"]
        text = BeautifulSoup(html, "html.parser").get_text()
        texts.append(text.lower())

    return texts


def get_salary_data(query, pages=3):
    url = "https://api.hh.ru/vacancies"
    salaries = []

    for page in range(pages):
        params = {
            "text": query,
            "area": 113,  # Россия
            "per_page": 50,
            "page": page,
        }

        res = requests.get(url, params=params).json()

        for item in res["items"]:
            salary = item.get("salary")
            if salary:
                if salary["from"] and salary["to"]:
                    salaries.append((salary["from"] + salary["to"]) / 2)
                elif salary["from"]:
                    salaries.append(salary["from"])
                elif salary["to"]:
                    salaries.append(salary["to"])

    return salaries


def compute_stats(salaries):
    if not salaries:
        return {"min": 0, "median": 0, "max": 0}

    return {
        "min": int(min(salaries) / 1000),
        "median": int(np.median(salaries) / 1000),
        "max": int(max(salaries) / 1000),
    }


def get_salary_by_grade(role):
    result = {}

    for grade, keywords in GRADE_KEYWORDS.items():
        query = f"{role} {' '.join(keywords)}"
        salaries = get_salary_data(query)
        result[grade] = compute_stats(salaries)

    return result


def get_top_employers(query, pages=2):
    url = "https://api.hh.ru/vacancies"
    employers = {}

    for page in range(pages):
        params = {
            "text": query,
            "per_page": 50,
            "page": page,
        }

        res = requests.get(url, params=params).json()

        for item in res["items"]:
            emp = item["employer"]["name"]
            employers[emp] = employers.get(emp, 0) + 1

    top = sorted(employers.items(), key=lambda x: -x[1])
    return [e[0] for e in top[:5]]

def build_salary_table(role):
    base = get_salary_by_grade(role)

    table = {}

    for grade, stats in base.items():
        table[grade] = {
            "Москва": stats,
            "Регионы РФ": {
                k: int(v * 0.7) for k, v in stats.items()
            },
            "Remote USD": {
                k: int(v / 100) for k, v in stats.items()
            }
        }

    return table
import os

from bs4 import BeautifulSoup
import requests
import numpy as np
from collections import defaultdict

# 1 — Москва, 113 — Россия
HH_AREA_MOSCOW = 1
HH_AREA_RUSSIA = 113

GRADE_KEYWORDS = {
    "Junior": ["junior", "intern"],
    "Middle": ["middle"],
    "Senior": ["senior"],
    "Lead": ["lead", "head"]
}

# Возвращает список вакансий
def get_role(name, pages=5):
    vacancies = []
    url = os.getenv("HH_URL")

    for page in range(pages):
        params = {
            "text": name,
            "area": 1,
            "per_page": 10,
            "page": page,
        }
        res = requests.get(url, params=params).json()
        vacancies.extend(res["items"])

    return vacancies

# полные описания вакансий
def get_descriptions(items):
    texts = []

    for item in items:
        full = requests.get(f"https://api.hh.ru/vacancies/{item['id']}").json()
        html = full["description"]
        text = BeautifulSoup(html, "html.parser").get_text()
        texts.append(text.lower())

    return texts

# собирает зарплаты по региону
def get_salary_data(query, pages=10, area=HH_AREA_RUSSIA):
    url = "https://api.hh.ru/vacancies"
    salaries = []

    for page in range(pages):
        params = {
            "text": query,
            "area": area,
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

# min/median/max по зарплатам
def compute_stats(salaries):
    if not salaries:
        return {"min": 0, "median": 0, "max": 0}

    return {
        "min": int(min(salaries) / 1000),
        "median": int(np.median(salaries) / 1000),
        "max": int(max(salaries) / 1000),
    }

# зп по грейдам
def get_salary_by_grade(role, area=HH_AREA_RUSSIA):
    result = {}

    for grade, keywords in GRADE_KEYWORDS.items():
        query = f"{role} {' '.join(keywords)}"
        salaries = get_salary_data(query, area=area)
        result[grade] = compute_stats(salaries)

    return result

# топ работодателей по частоте вакансий
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

# итоговая таблица, чтобы её передать агенту
def build_salary_table(role):
    base_moscow = get_salary_by_grade(role, area=HH_AREA_MOSCOW)
    base_russia = get_salary_by_grade(role, area=HH_AREA_RUSSIA)

    table = {}

    for grade in GRADE_KEYWORDS:
        m = base_moscow[grade]
        r = base_russia[grade]
        table[grade] = {
            "Москва": m,
            # Колонка по смыслу «ниже/шире Москвы»: отдельная выборка по area=113 (вся РФ по API hh).
            "Регионы РФ": r,
            "Remote USD": {
                k: round(m[k] / 100, 1) for k in m
            },
        }

    return table
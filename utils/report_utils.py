import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
REPORT_JSON = ROOT / "report.json"
REPORT_MD = ROOT / "report.md"
MSK_TZ = ZoneInfo("Europe/Moscow")

#  вытаскивает json из ответа
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

# остановка выполнения при ошибке
def fail_validation(agent_name, message):
    print(f"[{agent_name}] validation error: {message}")
    sys.exit(1)

# проверяет формат ответа 1 агента
def validate_skill_map(payload):
    if not isinstance(payload, dict):
        fail_validation("agent_1_analyst", "output must be a JSON object")

    required_categories = ["languages", "frameworks", "infrastructure", "soft_skills"]
    for category in required_categories:
        if category not in payload:
            fail_validation("agent_1_analyst", f"missing category '{category}'")
        if not isinstance(payload[category], list):
            fail_validation("agent_1_analyst", f"'{category}' must be a list")

    allowed_demand = {"critical", "important", "nice-to-have"}
    allowed_trend = {"growing", "stable", "declining"}
    for category in required_categories:
        for i, item in enumerate(payload[category]):
            if not isinstance(item, dict):
                fail_validation("agent_1_analyst", f"{category}[{i}] must be an object")
            if "name" not in item or "demand" not in item or "trend" not in item:
                fail_validation("agent_1_analyst", f"{category}[{i}] missing one of: name, demand, trend")
            if item["demand"] not in allowed_demand:
                fail_validation("agent_1_analyst", f"{category}[{i}].demand has invalid value")
            if item["trend"] not in allowed_trend:
                fail_validation("agent_1_analyst", f"{category}[{i}].trend has invalid value")

    role_val = payload.get("role")
    if not isinstance(role_val, str) or not role_val.strip():
        fail_validation("agent_1_analyst", "missing or empty string field 'role'")

# проверяет формат ответа 2 агента
def validate_salary_payload(payload):
    if not isinstance(payload, dict):
        fail_validation("agent_2_salary_estimator", "output must be a JSON object")
    if "salary_table" not in payload or "market_trend" not in payload or "top_employers" not in payload:
        fail_validation("agent_2_salary_estimator", "missing salary_table, market_trend or top_employers")

    salary_table = payload["salary_table"]
    if not isinstance(salary_table, dict):
        fail_validation("agent_2_salary_estimator", "salary_table must be an object")

    required_grades = ["Junior", "Middle", "Senior", "Lead"]
    required_regions = ["Москва", "Регионы РФ", "Remote USD"]
    for grade in required_grades:
        if grade not in salary_table:
            fail_validation("agent_2_salary_estimator", f"salary_table missing grade '{grade}'")
        if not isinstance(salary_table[grade], dict):
            fail_validation("agent_2_salary_estimator", f"salary_table.{grade} must be an object")
        for region in required_regions:
            stats = salary_table[grade].get(region)
            if not isinstance(stats, dict):
                fail_validation("agent_2_salary_estimator", f"salary_table.{grade}.{region} must be an object")
            for key in ["min", "median", "max"]:
                if key not in stats:
                    fail_validation("agent_2_salary_estimator", f"salary_table.{grade}.{region} missing '{key}'")
                if not isinstance(stats[key], (int, float)):
                    fail_validation("agent_2_salary_estimator", f"salary_table.{grade}.{region}.{key} must be a number")

    market_trend = payload["market_trend"]
    if not isinstance(market_trend, dict):
        fail_validation("agent_2_salary_estimator", "market_trend must be an object")
    if market_trend.get("trend") not in {"growing", "stable", "declining"}:
        fail_validation("agent_2_salary_estimator", "market_trend.trend has invalid value")
    if not isinstance(market_trend.get("justification"), str) or not market_trend.get("justification").strip():
        fail_validation("agent_2_salary_estimator", "market_trend.justification must be a non-empty string")

    top_employers = payload["top_employers"]
    if not isinstance(top_employers, list) or not (3 <= len(top_employers) <= 5):
        fail_validation("agent_2_salary_estimator", "top_employers must be a list with 3 to 5 items")

# проверяет формат ответа 3 агента
def validate_advisor_payload(payload):
    if not isinstance(payload, dict):
        fail_validation("agent_3_career_advisor", "output must be a JSON object")
    for key in ["learning_path", "gap_analysis", "portfolio_project"]:
        if key not in payload:
            fail_validation("agent_3_career_advisor", f"missing '{key}'")

    learning_path = payload["learning_path"]
    if not isinstance(learning_path, dict):
        fail_validation("agent_3_career_advisor", "learning_path must be an object")
    for phase in ["foundation", "practice", "portfolio"]:
        phase_items = learning_path.get(phase)
        if isinstance(phase_items, dict):
            phase_items = [phase_items]
            learning_path[phase] = phase_items
        if not isinstance(phase_items, list):
            fail_validation("agent_3_career_advisor", f"learning_path.{phase} must be a list or object")
        for i, item in enumerate(phase_items):
            if not isinstance(item, dict):
                fail_validation("agent_3_career_advisor", f"learning_path.{phase}[{i}] must be an object")
            if not isinstance(item.get("topics"), list):
                fail_validation("agent_3_career_advisor", f"learning_path.{phase}[{i}].topics must be a list")
            resources = item.get("resources")
            if isinstance(resources, dict):
                resources = [resources]
                item["resources"] = resources
            if not isinstance(resources, list) or len(resources) < 2:
                fail_validation("agent_3_career_advisor", f"learning_path.{phase}[{i}].resources must have at least 2 items")
            if not isinstance(item.get("expected_milestone"), str):
                fail_validation("agent_3_career_advisor", f"learning_path.{phase}[{i}].expected_milestone must be a string")

    gap_analysis = payload["gap_analysis"]
    if not isinstance(gap_analysis, dict):
        fail_validation("agent_3_career_advisor", "gap_analysis must be an object")
    if not isinstance(gap_analysis.get("quick_wins"), list):
        fail_validation("agent_3_career_advisor", "gap_analysis.quick_wins must be a list")
    if not isinstance(gap_analysis.get("long_term"), list):
        fail_validation("agent_3_career_advisor", "gap_analysis.long_term must be a list")

    portfolio_project = payload["portfolio_project"]
    if not isinstance(portfolio_project, dict):
        fail_validation("agent_3_career_advisor", "portfolio_project must be an object")
    for key in ["title", "description", "technologies"]:
        if key not in portfolio_project:
            fail_validation("agent_3_career_advisor", f"portfolio_project missing '{key}'")
    if not isinstance(portfolio_project["technologies"], list) or len(portfolio_project["technologies"]) < 1:
        fail_validation("agent_3_career_advisor", "portfolio_project.technologies must be a non-empty list")

# проверяет формат ответа 4 агента
def validate_quality_payload(payload):
    if not isinstance(payload, dict):
        fail_validation("agent_4_quality_checker", "output must be a JSON object")
    if "quality_score" not in payload or "warnings" not in payload or "is_consistent" not in payload:
        fail_validation("agent_4_quality_checker", "missing quality_score, warnings or is_consistent")

    quality_score = payload["quality_score"]
    if not isinstance(quality_score, dict):
        fail_validation("agent_4_quality_checker", "quality_score must be an object")
    score = quality_score.get("score")
    if not isinstance(score, int) or score < 0 or score > 100:
        fail_validation("agent_4_quality_checker", "quality_score.score must be an integer in range 0..100")
    if not isinstance(quality_score.get("justification"), str):
        fail_validation("agent_4_quality_checker", "quality_score.justification must be a string")

    if not isinstance(payload["warnings"], list):
        fail_validation("agent_4_quality_checker", "warnings must be a list")
    if not isinstance(payload["is_consistent"], bool):
        fail_validation("agent_4_quality_checker", "is_consistent must be boolean")

# собирает финальный отчёт
def write_reports(role, skill_map, salary_payload, advisor_payload, quality_json):
    report = {
        "role": role,
        "generated_at": datetime.now(MSK_TZ).isoformat(),
        "skill_map": skill_map,
        "salary_table": salary_payload,
        "advisor_table": advisor_payload,
        "quality_table": quality_json,
    }

    REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report_md = (
        "# Career Report\n\n"
        f"Role: {role}\n\n"
        f"Generated at (Europe/Moscow): {report['generated_at']}\n\n"
        "## skill_map\n\n"
        f"```json\n{json.dumps(skill_map, ensure_ascii=False, indent=2)}\n```\n\n"
        "## salary_table\n\n"
        f"```json\n{json.dumps(salary_payload, ensure_ascii=False, indent=2)}\n```\n\n"
        "## advisor_table\n\n"
        f"```json\n{json.dumps(advisor_payload, ensure_ascii=False, indent=2)}\n```\n\n"
        "## quality_table\n\n"
        f"```json\n{json.dumps(quality_json, ensure_ascii=False, indent=2)}\n```\n"
    )
    REPORT_MD.write_text(report_md, encoding="utf-8")

    return report

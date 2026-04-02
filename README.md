# Vacancy Search System

Мультиагентная система для генерации карьерного отчета по роли из IT

## Быстрый запуск

1. Зависимости:
   - pip install -r requirements.txt
2. Создать '.env' на основе '.env.example' и заполнить:
   - 'OPENROUTER_KEY'
   - 'MODEL'
   - 'ROUTER_BASE_URL'
   - 'HH_URL'
3. Запустить:
   - 'python main.py --role "Backend Python Developer"' 
   - 'python main.py --role "ML Engineer"'
   - 'python main.py --role "iOS Developer (Swift)"'


## Агенты

1. **Analyst ('analyst'). Промпт - first_analyst.txt**
   - Принимает название роли
   - Возвращает 'skill_map' (навыки по категориям + demand/trend)

2. **Salary estimator ('salary_estimator'). Промпт - salary_estimator.txt**
   - Принимает 'skill_map'
   - Возвращает 'salary_table', 'market_trend', 'market_trend_reason', 'top_employers'

3. **Career advisor ('career_advisor'). Промпт - career_advisor.txt**
   - Принимает 'skill_map' и 'salary_table'
   - Возвращает 'learning_path', 'gap_analysis', 'portfolio_project'

4. **Quality checker ('quality_checker'). Промпт - quality_checker.txt**
   - Принимает объединенный отчет от агентов 1-3
   - Возвращает 'quality_score', 'warnings', 'is_consistent'

## Что создается после запуска

- 'model_answers/skill_map.json'
- 'model_answers/salary_table.json'
- 'model_answers/advisor_table.json'
- 'model_answers/quality_table.json'
- 'report.json'
- 'report.md'


## По файлам

- utils/api_search - функции для вытягивания информации и ее минимальной обработки
- utils/report_utils - функции для проверки форматов json в выходах у моделей
- prompts/ - промты для разных моделей
- model_answers/ - то, что выдали модели в последнем запуске
- examples/ - примеры отчетов
- models.py - 4 функции под каждого агента
- main.py - запуск системы, последовательный вызов агентов
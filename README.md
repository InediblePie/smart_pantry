# Meal Planner & Grocery List

Simple Flask app to plan weekly meals, manage pantry/shopping items, and export a shopping list PDF.

## Features
- Select a week via calendar UI
- Enter meals and per-day ingredient lists
- Save/load weekly plans (JSON-backed)
- Add additional shopping items
- Export consolidated shopping list as a PDF

## Prerequisites
- Python 3.11+
- pip
- Optional: Docker

## Quick start (local)
1. Clone the repo
2. Create a virtual environment and install deps:
    - python -m venv .venv
    - source .venv/bin/activate
    - pip install -r requirements.txt
3. Set DB file location (example):
    - export DATABASE_FILE=/path/to/meals.json
    - mkdir -p $(dirname /path/to/meals.json) && echo "[]" > /path/to/meals.json
4. Start app (development):
    - export FLASK_APP=app.py
    - flask run --host=0.0.0.0 --port=5000
5. Open http://localhost:5000

Or run with gunicorn (production-style):
- gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

## Docker
Build and run:
- docker build -t meal-planner .
- docker run -p 5000:5000 -v $(pwd)/data:/app/data -e DATABASE_FILE=/app/data/meals.json meal-planner

Ensure the host `data` directory exists so the JSON persists.

## Environment
- DATABASE_FILE - path to JSON file used by DataHandler (required)

## Data storage
- JSON array of week objects stored at DATABASE_FILE.
- Each object includes `week` (e.g., "2023-W05"), day fields (`monday`, `monday_ingredients`, ...) and `additional_items`.

## API / Endpoints
- GET / — web UI
- POST /save_week — form submit to save a week
- GET /get_week_items?week=<week> — returns JSON for a week
- GET /download_shopping_list?week=<week> — returns shopping list PDF

## Project layout
- app.py — Flask application
- templates/index.html — frontend UI
- src/data_handling.py — JSON persistence
- Dockerfile — container image
- requirements.txt

## Contributing
PRs and issues welcome. Keep changes small and include tests where applicable.

## License
MIT License
# Meal Planner & Grocery List

Simple Flask app to plan weekly meals, manage pantry/shopping items, and export a shopping list PDF.

## Features
- Select a week via calendar UI
- Enter meals and per-day ingredient lists
- Save/load weekly plans (PostgreSQL-backed)
- Add additional shopping items
- Export consolidated shopping list as a PDF

## Prerequisites
- Python 3.11+
- pip
- PostgreSQL database
- Optional: Docker

## Quick start (local)
1. Clone the repo
2. Create a virtual environment and install deps:
    - python -m venv .venv
    - source .venv/bin/activate
    - pip install -r requirements.txt
3. Set database connection environment variables:
    - export DB_HOST=localhost
    - export DB_NAME=meal_planner
    - export DB_USER=postgres
    - export DB_PASSWORD=your_password
    - export DB_PORT=5432
4. Start app (development):
    - export FLASK_APP=app.py
    - flask run --host=0.0.0.0 --port=5000
5. Open http://localhost:5000

Or run with gunicorn (production-style):
- gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

## Docker
Build and run:
- docker build -t meal-planner .
- docker run -p 5000:5000 -e DB_HOST=your_host -e DB_NAME=meal_planner -e DB_USER=postgres -e DB_PASSWORD=your_password meal-planner

## Environment
- DB_HOST - PostgreSQL host (required)
- DB_NAME - PostgreSQL database name (required)
- DB_USER - PostgreSQL username (required)
- DB_PASSWORD - PostgreSQL password (required)
- DB_PORT - PostgreSQL port (default: 5432)

## Data storage
- PostgreSQL database with meal_weeks table.
- Each row includes `week` (e.g., "2023-W05") as primary key and `data` as JSONB containing day fields (`monday`, `monday_ingredients`, ...) and `additional_items`.

## API / Endpoints
- GET / — web UI
- POST /save_week — form submit to save a week
- GET /get_week_items?week=<week> — returns JSON for a week
- GET /download_shopping_list?week=<week> — returns shopping list PDF

## Project layout
- app.py — Flask application
- templates/index.html — frontend UI
- src/data_handling.py — PostgreSQL persistence
- Dockerfile — container image
- requirements.txt

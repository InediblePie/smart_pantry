# Meal Planner & Grocery List

Simple Flask app to plan weekly meals, manage pantry/shopping items, and export a shopping list PDF.

## Features
- Select a week via calendar UI
- Enter meals with recipe links and ingredient lists
- Dynamic ingredient search with autocomplete from pantry directory
- Quantity tracking for each ingredient
- Save/load weekly plans (PostgreSQL-backed)
- Add additional shopping items with quantities
- Export consolidated shopping list as a PDF with two sections:
  - "Shopping List" - items to purchase (including additional items)
  - "Check Item Stock" - items with low inventory
- Manage pantry inventory with expiration tracking
- Pantry directory with unique 10-digit item IDs
- Item intake system for adding items to pantry
- Automatic 4x6 inch label generation with barcodes (serial and item ID)
- Search, sort, and filter pantry items
- Quick delete functions:
  - Delete by serial number (scan or enter)
  - Delete oldest item by ID
- Dark theme UI with Bootstrap 5

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
- PostgreSQL database with three tables:
  - meal_weeks: Stores weekly meal plans with `week` as primary key and `data` as JSONB
  - pantry_directory: Stores item definitions with random 10-digit IDs, name, and category
  - pantry: Stores actual pantry inventory with serial numbers, item references, and expiration dates

## API / Endpoints
- GET / — meal planning web UI
- POST /save_week — form submit to save a week
- GET /get_week_items?week=<week> — returns JSON for a week
- GET /download_shopping_list?week=<week> — returns shopping list PDF
- GET /pantry/intake — pantry intake and directory management UI
- POST /pantry/intake/add — add item to pantry
- POST /pantry/directory/add — add item to directory
- POST /pantry/directory/delete — delete item from directory
- POST /pantry/directory/get_item — get item details by ID
- GET /pantry/directory/search — search directory items by name
- GET /pantry — pantry inventory view
- POST /pantry/get_by_serial — lookup item by serial number
- POST /pantry/get_count — get count of items by ID
- POST /pantry/delete — delete item from pantry by serial
- POST /pantry/delete_by_serial — quick delete by serial number
- POST /pantry/delete_oldest_by_id — delete oldest item by ID
- GET /pantry/label — label print page
- GET /pantry/label/image — generate label image with barcodes

## Project layout
- app.py — Flask application
- templates/
  - base.html — base template with navigation and dark theme
  - meal_planning.html — weekly meal planner UI with dynamic ingredients
  - pantry_intake.html — item intake and directory management
  - pantry_view.html — pantry inventory view with quick delete functions
  - label_print.html — label printing page
- src/data_handling.py — PostgreSQL persistence (MealDB, PantryDirectoryDB, PantryDB)
- Dockerfile — container image
- requirements.txt

## Key Features Detail

### Meal Planning
- Calendar-based week selection
- Per-day meal entry with optional recipe links
- Dynamic ingredient lists with autocomplete search
- Quantity tracking for each ingredient
- Additional shopping items section with same functionality
- Ingredients stored as objects: `{"id": "<item_id>", "qty": <quantity>}`

### Pantry Management
- Directory of items with unique 10-digit IDs and categories
- Inventory tracking with serial numbers and expiration dates
- Item intake with automatic label generation
- Search, filter, and sort inventory
- Serial lookup and item count functions
- Quick delete by serial or by item ID (removes oldest)

### Label System
- 4x6 inch vertical labels at 300 DPI (1200x1800 pixels)
- Code128 barcodes for serial and item ID
- Displays expiration date and item name
- Automatic print dialog on generation
- Optimized barcode settings for scanner compatibility

### Shopping List PDF
- Two sections:
  - "Shopping List" - items needed (pantry count < recipe quantity) + additional items
  - "Check Item Stock" - items with exact match (pantry count = recipe quantity)
- Checkbox format for easy shopping
- Automatic pagination for long lists

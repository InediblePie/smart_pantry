from flask import Flask, render_template, request, redirect, url_for, send_file
from dotenv import load_dotenv
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO

from src.data_handling import MealDB, PantryDirectoryDB, PantryDB

# Initialize the Flask app and load the environment variables
load_dotenv()
app = Flask(__name__)

# Initialize the database connections using environment variables
if not (db_host := os.getenv("DB_HOST")):
    raise Exception("No database host specified")
if not (db_name := os.getenv("DB_NAME")):
    raise Exception("No database name specified")
if not (db_user := os.getenv("DB_USER")):
    raise Exception("No database user specified")
if not (db_password := os.getenv("DB_PASSWORD")):
    raise Exception("No database password specified")
db_port = int(os.getenv("DB_PORT", "5432"))
mdb = MealDB(db_host, db_name, db_user, db_password, db_port)
pddb = PantryDirectoryDB(db_host, db_name, db_user, db_password, db_port)
pdb = PantryDB(db_host, db_name, db_user, db_password, db_port)
del db_host, db_name, db_user, db_password, db_port

# Default route to main page
@app.route('/')
def index():
    return render_template('meal_planning.html', active_tab='meal-planning')

# Route to save the week's meals
@app.route("/save_week", methods=["POST"])
def save_week():
    week = None
    meals = {}

    for item in request.form.items():
        if item[0] == "week":
            week = item[1]
        else:
            meals[item[0]] = item[1]
    
    if not week:
        raise Exception("No week specified")
    
    mdb.save_week(week, meals)
    return redirect(url_for('index'))

# Route to get the week's meals
@app.route("/get_week_items")
def get_week_items():
    week = request.args.get('week')

    if not week:
        raise Exception("No week specified")
    
    resp = mdb.load_week(week)
    if resp == None:
        raise Exception("No items found for week")
    
    return resp

# Route for pantry view
@app.route('/pantry')
def pantry_view():
    items = pdb.get_all_items()
    return render_template('pantry_view.html', active_tab='pantry-view', items=items)

# Route to search for an item in the pantry by its ID
@app.route('/pantry/get_by_serial', methods=['POST'])
def get_by_serial():
    serial = request.form.get('serial')
    if not serial:
        raise Exception('Serial is required')
    
    items = pdb.get_all_items()
    serial = int(serial)
    item = pdb.get_item_by_serial(serial)
    if not item:
        return render_template('pantry_view.html', active_tab='pantry-view', items=items)
    
    return render_template('pantry_view.html', active_tab='pantry-view', items=items, selected_item=item)

# Route to get the count of a specific item in the pantry by its ID
@app.route('/pantry/get_count', methods=['POST'])
def get_item_count():
    item_id = request.form.get('item_id')
    if not item_id:
        raise Exception('Item ID is required')
    
    item_id = int(item_id)
    count = pdb.item_count(item_id)
    items = pdb.get_all_items()
    return render_template('pantry_view.html', active_tab='pantry-view', items=items, item_count=count, searched_id=item_id)

# Route for pantry directory view
@app.route('/pantry/delete', methods=['POST'])
def delete_pantry_item():
    serial = request.form.get('serial')
    if not serial:
        raise Exception('Serial is required')
    
    serial = int(serial)
    pdb.remove_item(serial)
    return redirect(url_for('pantry_view'))

# Route for pantry intake
@app.route('/pantry/intake')
def pantry_intake():
    items = pddb.get_all_items()
    categories = [
        'Ingredients',
        'Meats',
        'Dairy',
        'Pasta',
        'Spices',
        'Canned goods',
        'Frozen goods',
        'Frozen meals',
        'Drinks'
    ]
    return render_template('pantry_intake.html', active_tab='pantry-intake', items=items, categories=categories)

# Route to add an item to the pantry directory
@app.route('/pantry/intake/add', methods=['POST'])
def add_pantry_item():
    item_id = request.form.get('item_id')
    expiration_date = request.form.get('expiration_date')
    
    if not item_id or not expiration_date:
        raise Exception('Item ID and expiration date are required')
    
    item_id = int(item_id)
    pdb.add_item(pddb, item_id, expiration_date)
    return redirect(url_for('pantry_intake'))

# Route to add an item to the pantry directory
@app.route('/pantry/directory/add', methods=['POST'])
def add_pantry_directory_item():
    name = request.form.get('name')
    category = request.form.get('category')
    
    if not name or not category:
        raise Exception('Name and category are required')
    
    pddb.add_item(name, category)
    return redirect(url_for('pantry_intake'))

# Route to delete an item from the pantry directory
@app.route('/pantry/directory/delete', methods=['POST'])
def delete_pantry_directory_item():
    item_id = request.form.get('item_id')

    if not item_id:
        raise Exception('Item ID is required')
    
    item_id = int(item_id)
    pddb.delete_item(item_id)
    return redirect(url_for('pantry_intake'))

# Route to download the shopping list as a PDF
@app.route("/download_shopping_list")
def download_shopping_list():
    week = request.args.get('week')

    if not week:
        raise Exception("No week specified")
    
    week_data = mdb.load_week(week)
    if not week_data:
        raise Exception("No items found for week")
    
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"Shopping List - Week {week}")
    
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(1 * inch, 10.5 * inch, f"Shopping List - Week {week}")
    
    y_position = 10 * inch
    pdf.setFont("Helvetica", 12)
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    for day in days:
        ingredients = week_data.get(f"{day}_ingredients", "")
        if ingredients:
            items = [item.strip() for item in ingredients.split('\n') if item.strip()]
            if items:
                for item in items:
                    if y_position < 1 * inch:
                        pdf.showPage()
                        y_position = 10.5 * inch
                        pdf.setFont("Helvetica", 12)
                    
                    pdf.rect(0.5 * inch, y_position - 0.05 * inch, 0.15 * inch, 0.15 * inch)
                    pdf.drawString(0.8 * inch, y_position, item)
                    y_position -= 0.3 * inch
    
    additional_items = week_data.get("additional_items", "")
    if additional_items:
        items = [item.strip() for item in additional_items.split('\n') if item.strip()]
        for item in items:
            if y_position < 1 * inch:
                pdf.showPage()
                y_position = 10.5 * inch
                pdf.setFont("Helvetica", 12)
            
            pdf.rect(0.5 * inch, y_position - 0.05 * inch, 0.15 * inch, 0.15 * inch)
            pdf.drawString(0.8 * inch, y_position, item)
            y_position -= 0.3 * inch
    
    pdf.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"shopping_list_{week}.pdf", mimetype="application/pdf")

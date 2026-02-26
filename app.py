from flask import Flask, render_template, request, redirect, url_for, send_file
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO
import os

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
    week = request.form.get("week")
    if not week:
        raise Exception("No week specified")
    
    meals = {}
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    # Handle regular form fields
    for key in request.form.keys():
        if key == "week" or key.endswith('_ingredients[]') or key.endswith('_quantities[]'):
            continue
        meals[key] = request.form.get(key)
    
    # Handle ingredient arrays with quantities
    for day in days:
        ingredients = request.form.getlist(f"{day}_ingredients[]")
        quantities = request.form.getlist(f"{day}_quantities[]")
        if ingredients:
            # Store as list of dicts with id and quantity
            meals[f"{day}_ingredients"] = [
                {"id": ing, "qty": int(qty) if qty else 1} 
                for ing, qty in zip(ingredients, quantities)
            ]
    
    # Handle additional shopping items
    additional_ingredients = request.form.getlist("additional_ingredients[]")
    additional_quantities = request.form.getlist("additional_quantities[]")
    if additional_ingredients:
        meals["additional_ingredients"] = [
            {"id": ing, "qty": int(qty) if qty else 1}
            for ing, qty in zip(additional_ingredients, additional_quantities)
        ]
    
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

@app.route('/pantry/delete_by_serial', methods=['POST'])
def delete_by_serial():
    serial = request.form.get('serial')
    if not serial:
        raise Exception('Serial is required')
    
    pdb.remove_item(int(serial))
    return redirect(url_for('pantry_view'))

@app.route('/pantry/delete_oldest_by_id', methods=['POST'])
def delete_oldest_by_id():
    item_id = request.form.get('item_id')
    if not item_id:
        raise Exception('Item ID is required')
    
    pdb.remove_oldest_by_id(int(item_id))
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
    serial = pdb.add_item(pddb, item_id, expiration_date)
    
    # Redirect to label generation page
    return redirect(url_for('generate_label', serial=serial, item_id=item_id, expiration_date=expiration_date))

@app.route('/pantry/label')
def generate_label():
    serial = request.args.get('serial')
    item_id = request.args.get('item_id')
    expiration_date = request.args.get('expiration_date')
    
    if not serial or not item_id or not expiration_date:
        return redirect(url_for('pantry_intake'))
    
    return render_template('label_print.html', serial=serial, item_id=item_id, expiration_date=expiration_date)

@app.route('/pantry/label/image')
def generate_label_image():
    from PIL import Image, ImageDraw, ImageFont
    import barcode
    from barcode.writer import ImageWriter
    
    serial = request.args.get('serial')
    item_id = request.args.get('item_id')
    expiration_date = request.args.get('expiration_date')
    
    if not serial or not item_id or not expiration_date:
        raise Exception('Missing label parameters')
    
    # Get item name from database
    item = pddb.get_item_by_id(int(item_id))
    item_name = item['name'] if item else 'Unknown Item'
    
    # Create label image (4x6 inches at 300 DPI - vertical layout)
    width, height = 1200, 1800  # 4x6 inches at 300 DPI
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_huge = ImageFont.truetype('./static/Roboto-Bold.ttf', 120)
        font_large = ImageFont.truetype('./static/Roboto-Bold.ttf', 80)
        font_medium = ImageFont.truetype('./static/Roboto-Regular.ttf', 60)
    except:
        font_huge = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # Generate barcodes with optimal settings for scanning
    CODE128 = barcode.get_barcode_class('code128')
    
    # Serial barcode
    serial_barcode = CODE128(serial, writer=ImageWriter())
    serial_barcode_img = serial_barcode.render({
        'write_text': False,
        'module_height': 25,
        'module_width': 0.6,
        'quiet_zone': 10
    })
    serial_barcode_img = serial_barcode_img.resize((1000, 300))
    
    # Item ID barcode
    item_barcode = CODE128(item_id, writer=ImageWriter())
    item_barcode_img = item_barcode.render({
        'write_text': False,
        'module_height': 25,
        'module_width': 0.6,
        'quiet_zone': 10
    })
    item_barcode_img = item_barcode_img.resize((1000, 300))
    
    # Vertical layout
    x_center = width // 2
    y_pos = 50
    
    # Serial section
    text_bbox = draw.textbbox((0, 0), 'Serial:', font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text((x_center - text_width // 2, y_pos), 'Serial:', font=font_large, fill='black')
    y_pos += 90
    img.paste(serial_barcode_img, ((width - 1000) // 2, y_pos))
    y_pos += 310
    text_bbox = draw.textbbox((0, 0), serial, font=font_medium)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text((x_center - text_width // 2, y_pos), serial, font=font_medium, fill='black')
    
    # Item ID section
    y_pos += 100
    text_bbox = draw.textbbox((0, 0), 'Item ID:', font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text((x_center - text_width // 2, y_pos), 'Item ID:', font=font_large, fill='black')
    y_pos += 90
    img.paste(item_barcode_img, ((width - 1000) // 2, y_pos))
    y_pos += 310
    text_bbox = draw.textbbox((0, 0), item_id, font=font_medium)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text((x_center - text_width // 2, y_pos), item_id, font=font_medium, fill='black')
    
    # Expiration date
    y_pos += 100
    text_bbox = draw.textbbox((0, 0), 'Expires:', font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text((x_center - text_width // 2, y_pos), 'Expires:', font=font_large, fill='black')
    y_pos += 90
    text_bbox = draw.textbbox((0, 0), expiration_date, font=font_huge)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text((x_center - text_width // 2, y_pos), expiration_date, font=font_huge, fill='black')
    
    # Item name at bottom
    y_pos += 140
    text_bbox = draw.textbbox((0, 0), item_name, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text((x_center - text_width // 2, y_pos), item_name, font=font_large, fill='black')
    
    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return send_file(buffer, mimetype='image/png')

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

@app.route('/pantry/directory/get_item', methods=['POST'])
def get_pantry_directory_item():
    from flask import jsonify
    item_id = request.form.get('item_id')
    
    if not item_id:
        return jsonify({'name': None})
    
    item_id = int(item_id)
    item = pddb.get_item_by_id(item_id)
    
    if item:
        return jsonify({'name': item['name']})
    return jsonify({'name': None})

@app.route('/pantry/directory/search', methods=['GET'])
def search_pantry_directory():
    from flask import jsonify
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify([])
    
    items = pddb.get_all_items()
    results = [{'id': item['id'], 'name': item['name']} for item in items if query in item['name'].lower()]
    return jsonify(results[:10])  # Limit to 10 results

# Generates a PDF shopping list for the specified week, including checkboxes for each item
# with 2 secions, one for items to check stock and one for items to buy, and handles pagination for long lists
def generate_shopping_list(week: str, check_items: list[str], items: list[str]) -> BytesIO:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"Shopping List - Week {week}")
    
    # pdf.setFont("Helvetica-Bold", 16)
    # pdf.drawString(1 * inch, 10.5 * inch, f"Shopping List - Week {week}")
    
    y_position = 10 * inch
    # pdf.setFont("Helvetica", 12)

    # Section 1: Check Item Stock
    if len(items) > 0:
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(1 * inch, y_position, f"Shopping List - {week}")
        y_position -= 0.5 * inch
        pdf.setFont("Helvetica", 12)
        
        for item in items:
            if y_position < 1 * inch:
                pdf.showPage()
                y_position = 10.5 * inch
                pdf.setFont("Helvetica", 12)
            
            pdf.rect(0.5 * inch, y_position - 0.05 * inch, 0.15 * inch, 0.15 * inch)
            pdf.drawString(0.8 * inch, y_position, item)
            y_position -= 0.3 * inch
        
        y_position -= 0.3 * inch  # Extra space between sections
    
    # Section 2: Shopping List
    if len(check_items) > 0:
        if y_position < 2 * inch:
            pdf.showPage()
            y_position = 10.5 * inch

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(1 * inch, y_position, "Check Item Stock")
        y_position -= 0.5 * inch
        pdf.setFont("Helvetica", 12)
        
        for item in check_items:
            if y_position < 1 * inch:
                pdf.showPage()
                y_position = 10.5 * inch
                pdf.setFont("Helvetica", 12)
            
            pdf.rect(0.5 * inch, y_position - 0.05 * inch, 0.15 * inch, 0.15 * inch)
            pdf.drawString(0.8 * inch, y_position, item)
            y_position -= 0.3 * inch
    
    pdf.save()
    buffer.seek(0)

    return buffer

# Route to download the shopping list as a PDF
@app.route("/download_shopping_list")
def download_shopping_list():
    week = request.args.get('week')

    if not week:
        raise Exception("No week specified")
    
    week_data = mdb.load_week(week)
    if not week_data:
        raise Exception("No items found for week")
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    check_items = []
    shopping_items = []

    for day in days:
        ingredients = week_data.get(f"{day}_ingredients", [])
        for ingredient in ingredients:
            item = pddb.get_item_by_id(int(ingredient['id']))
            if item:
                shopping_count = pdb.item_count(int(ingredient['id']))
                if shopping_count - int(ingredient['qty']) < 0:
                    shopping_items.append(item['name'])
                elif shopping_count - int(ingredient['qty']) == 0:
                    check_items.append(item['name'])
    
    # Add additional shopping items
    additional_items = week_data.get('additional_ingredients', [])
    for ingredient in additional_items:
        item = pddb.get_item_by_id(int(ingredient['id']))
        if item:
            shopping_items.append(item['name'])
    
    buffer = generate_shopping_list(week, check_items, shopping_items)
    
    return send_file(buffer, as_attachment=True, download_name=f"shopping_list_{week}.pdf", mimetype="application/pdf")

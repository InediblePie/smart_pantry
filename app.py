from flask import Flask, render_template, request, redirect, url_for, send_file
from dotenv import load_dotenv
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO

from src.data_handling import DataHandler

# Initialize the Flask app and load the environment variables
load_dotenv()
app = Flask(__name__)

# Init the data handler from the environment variables
if not (database_file := os.getenv("DATABASE_FILE")):
    raise Exception("No database file specified")
dh = DataHandler(database_file)
del database_file

# Default route to main page
@app.route('/')
def index():
    return render_template('index.html')

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
    
    dh.save_week(week, meals)
    return redirect(url_for('index'))

# Route to get the week's meals
@app.route("/get_week_items")
def get_week_items():
    week = request.args.get('week')

    if not week:
        raise Exception("No week specified")
    
    resp = dh.load_week(week)
    if resp == None:
        raise Exception("No items found for week")
    
    return resp

# Route to download the shopping list as a PDF
@app.route("/download_shopping_list")
def download_shopping_list():
    week = request.args.get('week')

    if not week:
        raise Exception("No week specified")
    
    week_data = dh.load_week(week)
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

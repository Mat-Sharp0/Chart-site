from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import bcrypt
import os

load_dotenv()

app = Flask("Chartapp")

MONGO_URI = os.getenv('MONGO_URI')

client = MongoClient(MONGO_URI)
db = client.get_database("chart")

app.secret_key = os.urandom(24)

@app.route('/')
def index():
    chart = list(db["chart"].find({}))
    return render_template("index.html", chart=chart)

@app.route('/signup')
def signup():
    return render_template("front/signup.html")

@app.route('/register',  methods=['POST'])
def register():
    user_name=request.form['user_id']
    password=request.form['password']

    user = {
        "name": user_name,
        "password": password
    }
    db['users'].insert_one(user)
    session['role'] = 'user'
    session['user'] = user_name
    return redirect(url_for('/'))

@app.route("/chart/add")
def add_chart():
    return render_template("front/new_chart.html")

@app.route("/chart/creat", methods=['POST'])
def creat_chart():
    title = request.form['title']
    description = request.form['description']
    source =  request.form['source']
    chart_type = request.form['chart_type']

    image = request.files["image"]

    if image:
        file_name = secure_filename(image.filename)

        upload_path = os.path.join(app.static_folder, "images/chart_user", file_name)
        image.save(upload_path)

        image_path = f'/static/images/pokemon_user/{file_name}'
    
    else:
        image_path = ""

    image_chart = {
        "title": title,
        "description": description,
        "image": image_path,
        "source": source,
        "chart_type": chart_type
    }
    db['chart_image'].insert_one(image_chart)
    return redirect(url_for('/'))

app.run(host='0.0.0.0', port=81)
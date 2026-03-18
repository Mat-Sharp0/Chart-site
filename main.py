from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from bson import ObjectId
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

@app.route("/chart/<id>")
def watch_chart(id):
    chart = db["chart"].find_one({'_id' : ObjectId(id)})
    author_name = db['users'].find_one({'_id' : chart['author']})["name"]
    return render_template("front/chart.html", chart=chart, author_name=author_name)


#region user
@app.route('/signup')
def signup():
    return render_template("front/signup.html")

@app.route('/register',  methods=['POST'])
def register():

    user_name=request.form['user_name']
    password=request.form['password']
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user = {
        "name": user_name,
        "password": password_hash,
        "role": 'user'
    }
    db['users'].insert_one(user)
    session['role'] = session.get('role', 'user')
    session['user'] = user_name
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('front/login.html')
    
    user_name = request.form.get('user_name')
    password = request.form.get('password')

    if not user_name or not password:
        return render_template('front/login.html', error="Please fill in all fields")
    
    db_user = db.users
    user = db_user.find_one({'name': user_name})

    if not user:
        return render_template('front/login.html', error="User not found")
    
    if bcrypt.checkpw(password.encode('utf-8'), user['password']):
        session['role'] = session.get('role', 'user')
        session['user'] = user_name
        if session['user']:
          print(session['user'])
        return redirect(url_for("index"))
    else:
        return render_template('front/login.html', error="The password is incorrect")
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))
#endregion

#region content
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
    return redirect(url_for('index'))
#endregion

#region Admin
@app.route('/admin')
def admin():
    charts = list(db["chart"].find({}))
    users = list(db["users"].find({}))
    if 'user' in session and session['role'] == 'admin':
        return render_template('admin/back_home.html', charts=charts, users=users)
    else:
        return  render_template("index.html", chart=charts, error='Access denied')



#endregion

app.run(host='0.0.0.0', port=81)
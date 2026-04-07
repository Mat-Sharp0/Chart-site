from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import bcrypt
import os
from bson.objectid import ObjectId
import json
import datetime

load_dotenv()

app = Flask("Chartapp")

MONGO_URI = os.getenv('MONGO_URI')

client = MongoClient(MONGO_URI)
db = client.get_database("chart")

app.secret_key = os.urandom(24)

@app.route('/')
def index():
    charts = list(db["chart"].find({}))
    users = list(db["users"].find({}, {'name'}))
    return render_template("index.html", charts=charts, users=users)

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
    user = db['users'].insert_one(user)
    session['role'] = user['role']
    session['user'] = user_name
    session['user_id'] = str(user['_id'])
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
        session['role'] = user['role']
        session['user'] = user_name
        session['user_id'] = str(user['_id'])
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
    source = request.form['source']
    chart_type = request.form['chart_type']
    caption = request.form['caption']
    data = json.loads(request.form.get('data', '[]'))

    new_chart = {
        "config": {
            "type": chart_type,
            "data": {
                "labels": [p['label'] for p in data],
                "datasets": [
                    {
                    "label": caption,
                    "data": [float(p['value']) for p in data]
                    }
                ]
            }
        },
        "author": ObjectId(session['user_id']),
        "date": datetime.datetime.now(datetime.timezone.utc),
        "description": description,
        "source": source,
        "title": title
    }
    db['chart'].insert_one(new_chart)
    return redirect(url_for('index'))

@app.route("/chart/add_legacy")
def add_chart_legacy():
    return render_template("front/new_chart_legacy.html")

@app.route("/chart/creat_legacy", methods=['POST'])
def creat_chart_legacy():
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
    for user in users:
        user['publication_count'] = db["chart"].count_documents({"author": user['_id']})

    if 'user' in session and session['role'] == 'admin':
        return render_template('admin/back_home.html', charts=charts, users=users)
    else:
        return render_template("index.html", chart=charts, error='Access denied')
    
@app.route('/admin/update_role/<user_id>', methods= ['POST'])
def update_role(user_id):
    if 'user' in session and session['role'] == 'admin':
        new_role = request.form.get('role')

        db['users'].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"role": new_role}}
        )
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<user_id>')
def delete_user(user_id):
    if 'user' in session and session['role'] == 'admin':
        db["chart"].delete_many({"author": ObjectId(user_id)})
        db['users'].delete_one({"_id": ObjectId(user_id)})
    return redirect(url_for('admin'))

@app.route('/admin/user/<user_id>')
def show_user(user_id):
    if 'user' in session and session['role'] == 'admin':
        user = db['users'].find_one({"_id": ObjectId(user_id)})

        user['publication_count'] = db["chart"].count_documents({"author": user['_id']})
        user['publications'] = list(db["chart"].find({"author": user['_id']}))

        if  not user:
            return redirect(url_for('admin',  error='User not find'))
        return render_template('admin/back_user.html', user=user)
    return redirect(url_for('index'))


#endregion

app.run(host='0.0.0.0', port=81)
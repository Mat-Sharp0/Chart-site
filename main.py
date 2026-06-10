from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import bcrypt
import os
from bson.objectid import ObjectId
import json
import datetime
import re

load_dotenv()

app = Flask("Chartapp")

MONGO_URI = os.getenv('MONGO_URI')

client = MongoClient(MONGO_URI)
db = client.get_database("chart")

app.secret_key = os.urandom(24)

TAGS = ["histoire", "geographie", "santé", "économie", "agriculture"]

@app.route('/')
def index():
    charts = list(db["chart"].find({}))
    users = list(db["users"].find({}, {'name'}))
    return render_template("index.html", charts=charts)



@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    
    if query == '':
        results = list(db["chart"].find({}))
    elif bool(re.match(r"^user:", query, re.IGNORECASE)):
        query = re.match(r"^user:\s*(.*)$", query, re.IGNORECASE).group(1)
        results = list(db["chart"].find({
            "$or" : [
                {"author_name" : {"$regex" : query, "$options" : "i"}}
            ]
        }))
    elif bool(re.match(r"^#", query, re.IGNORECASE)):
        query = re.match(r"^#\s*(.*)$", query, re.IGNORECASE).group(1)
        results = list(db["chart"].find({
            "$or" : [
                {"tags" : {"$regex" : query, "$options" : "i"}}
            ]
        }))
    else:
        results = list(db["chart"].find({
            "$or" : [
                {"title" : {"$regex" : query, "$options" : "i"}},
                {"content" : {"$regex" : query, "$options" : "i"}},
                {"author" : {"$regex" : query, "$options" : "i"}},
                {"tags" : {"$regex" : query, "$options" : "i"}}
            ]
        }))

    return render_template("front/search_results.html", charts=results)


#region user
@app.route('/signup')
def signup():
    return render_template("front/signup.html")

@app.route('/register',  methods=['POST'])
def register():

    user_name=request.form['user_name']
    password=request.form['password']
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    if db['users'].find_one({'name' : user_name}):
        return redirect(url_for('login'))

    user = {
        "name": user_name,
        "password": password_hash,
        "role": 'user'
    }
    db_user = db['users'].insert_one(user)
    session['role'] = user['role']
    session['user'] = user_name
    session['user_id'] = str(db_user.inserted_id)
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
    
@app.route("/manage_account")
def manage_account():
    if 'user' in session:
        user = db['users'].find_one({"_id": ObjectId(session['user_id'])})
        user['publications'] = list(db["chart"].find({"author": user['_id']}))
        return render_template('front/manage_account.html', user=user)
    return redirect(url_for("index"))

@app.route('/user_delete_chart/<chart_id>')
def user_delete_chart(chart_id):
    if 'user' in session:
        chart = db['chart'].find_one({"_id": ObjectId(chart_id)})
        if chart['author'] == ObjectId(session['user_id']):
            db['chart'].delete_one({"_id": ObjectId(chart_id)})
            db['users'].update_one(
                {"_id": ObjectId(chart["author"])},
                {"$pull": {"post": ObjectId(chart_id)}}
                )
    return redirect(url_for('manage_account'))

@app.route('/delete_account')
def delete_account():
    if 'user' in session:
        db['chart'].delete_many({"author": ObjectId(session['user_id'])})
        db['users'].update_many({}, {"$pull": {"subscription": ObjectId(session['user_id'])}})
        db['users'].update_many({}, {"$pull": {"subscribers": ObjectId(session['user_id'])}})
        db['users'].delete_one({"_id": ObjectId(session['user_id'])})
        session.clear()
    return redirect(url_for("index"))
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/subscribe", methods=['POST'])
def subscribe():
    data = request.get_json()
    target_id = ObjectId(data['targetId'])

    target = db["users"].find_one({'_id' : target_id})
    if target and 'user' in session:
        user = db["users"].find_one({'_id' : ObjectId(session['user_id'])})
        if target_id in user.get("subscription", []):
            db['users'].update_one(
                {"_id": ObjectId(session['user_id'])},
                {"$pull": {"subscription": target_id}}
            )
            db['users'].update_one(
                {"_id": target_id},
                {"$pull": {"subscribers": ObjectId(session['user_id'])}}
            )
            return jsonify({"is_subscribe": False})
        else:
            db['users'].update_one(
                {"_id": ObjectId(session['user_id'])},
                {"$addToSet": {"subscription": target_id}}
            )
            db['users'].update_one(
                {"_id": target_id},
                {"$addToSet": {"subscribers": ObjectId(session['user_id'])}}
            )
            return jsonify({"is_subscribe": True})
            
    elif not 'user' in session:
        return jsonify({"error": "User not login"})
    else:
        return jsonify({"error": "This user not exist"})

@app.route("/subscritpions")
def subscritpions_page():
    user = db['users'].find_one({'_id' : ObjectId(session['user_id'])})
    charts = list(db["chart"].find({ "author": { "$in": user.get("subscription", []) }}))
    subscriptions = list(db['users'].find({'_id' : { "$in": user.get("subscription", []) }}))
    return render_template("front/subscritpions.html", charts=charts, subscriptions=subscriptions)
#endregion

#region content
@app.route("/chart/<id>")
def watch_chart(id):
    chart = db["chart"].find_one({'_id' : ObjectId(id)})
    author = db['users'].find_one({'_id' : chart['author']})
    try:
        is_subscribe = True if ObjectId(session['user_id']) in author['subscribers'] else False
    except:
        is_subscribe = False
    return render_template("front/chart.html", chart=chart, is_subscribe=is_subscribe)

@app.route("/user/<user_id>")
def watch_user(user_id):
    user = db['users'].find_one({"_id": ObjectId(user_id)})
    try:
        is_subscribe = True if ObjectId(session['user_id']) in user['subscribers'] else False
    except:
        is_subscribe = False
    user['publications'] = list(db["chart"].find({"author": user['_id']}))
    return render_template('front/user.html', user=user, is_subscribe=is_subscribe)

@app.route("/chart/add")
def add_chart():
    return render_template("front/new_chart.html", tags=TAGS)

# csv->json: https://www.papaparse.com/

@app.route("/chart/creat", methods=['POST'])
def creat_chart():
    if 'user' in session:
        title = request.form['title']
        description = request.form['description']
        source = request.form['source']
        chart_type = request.form['chart_type']
        caption = request.form['caption']
        data = json.loads(request.form.get('data', '[]'))
        tags = request.form.getlist('tags')

        if len(title) < 4:
            return redirect(url_for("add_chart"))
        
        if len(description) < 10:
            return redirect(url_for("add_chart"))

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
            "author_name": session['user'],
            "date": datetime.datetime.now(datetime.timezone.utc),
            "description": description,
            "tags": tags,
            "source": source,
            "title": title
        }
        result = db['chart'].insert_one(new_chart)
        db['users'].update_one(
                {"_id": ObjectId(session['user_id'])},
                {"$push": {"post": result.inserted_id}}
            )
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/report',  methods=['POST'])
def report():
    if 'user' in session:
        reason = request.form['reason']
        chart_id = request.form['chart_id']

        print(db['chart'].find({"_id": ObjectId(chart_id), "report": {"$elemMatch": { "reporter": ObjectId(session['user_id']) }}}))

        if not db['chart'].count_documents({"_id": ObjectId(chart_id), "report": {"$elemMatch": { "reporter": ObjectId(session['user_id']) }}}) > 0:
            db['chart'].update_one(
                {"_id": ObjectId(chart_id)},
                {"$addToSet": {"report": {"reason": reason, "reporter": ObjectId(session['user_id'])}}}
            )
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

@app.route('/admin/admin_delete_user/<user_id>')
def admin_delete_user(user_id):
    if 'user' in session and session['role'] == 'admin':
        db['chart'].delete_many({"author": ObjectId(user_id)})
        db['users'].update_many({}, {"$pull": {"subscription": ObjectId(user_id)}})
        db['users'].update_many({}, {"$pull": {"subscribers": ObjectId(user_id)}})
        db['users'].delete_one({"_id": ObjectId(user_id)})
    return redirect(url_for('admin'))

@app.route('/admin/admin_delete_chart/<chart_id>')
def admin_delete_chart(chart_id):
    if 'user' in session and session['role'] == 'admin':
        chart = db['chart'].find({"_id": ObjectId(chart_id)})
        db['chart'].delete_one({"_id": ObjectId(chart_id)})
        db['users'].update_one(
            {"_id": ObjectId(chart["author"])},
            {"$pull": {"post": ObjectId(chart_id)}}
            )
    return redirect(url_for('admin'))

@app.route('/admin/user/<user_id>')
def show_user(user_id):
    if 'user' in session and session['role'] == 'admin':
        user = db['users'].find_one({"_id": ObjectId(user_id)})
        user['publications'] = list(db["chart"].find({"author": user['_id']}))

        if not user:
            return redirect(url_for('admin',  error='User not find'))
        return render_template('admin/back_user.html', user=user)
    return redirect(url_for('index'))

@app.route('/admin/reported')
def reported_content():
    charts = list(db["chart"].find({"report": {"$exists": True}}))
    if 'user' in session and session['role'] == 'admin':
        return render_template('admin/back_reported.html', charts=charts)
    else:
        return render_template("index.html", chart=charts, error='Access denied')
    
@app.route('/admin/clear_report/<chart_id>')
def clear_report(chart_id):
    if 'user' in session and session['role'] == 'admin':
        db['chart'].update_one(
            {"_id": ObjectId(chart_id)},
            {"$unset": {"report": ""}}
            )
    return redirect(url_for('admin'))


#endregion

app.run(host='0.0.0.0', port=81)
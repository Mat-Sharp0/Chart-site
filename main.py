from flask import Flask, render_template
import pymongo
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask("Chartapp")


@app.route('/')
def index():
    return render_template("index.html")

app.run(host='0.0.0.0', port=81)
from cmath import asin, cos, sin, sqrt
from datetime import datetime
import json
from math import radians
import os
import pymysql
import spacy
from string import punctuation
from spacy.matcher import Matcher

from flask import Flask, render_template, request

app = Flask(__name__)
app.config['DEBUG'] = True

db = pymysql.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="cloudcomputing"
)

# redis_ins = redis.StrictRedis(host='localhost', port=6379, db=0)


class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def get_distance(lng1, lat1, lng2, lat2):
    lng1, lat1, lng2, lat2 = map(
        radians, [float(lng1), float(lat1), float(lng2), float(lat2)])
    dlon = lng2-lng1
    dlat = lat2-lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    distance = 2*asin(sqrt(a))*6371*1000
    distance = round(distance/1000, 3)
    return distance


def cache_key(task_name, *params):
    param_strs = []
    for param in param_strs:
        param_strs.append(str(param))
    params_key = "-".join(param_strs)
    return "{}-{}".format(task_name, params_key)


def get_range(range_str):
    arr = range_str.split('-')
    print(arr)
    if len(arr) != 2:
        raise ValueError(
            "Invalid range format, for example, the valid format is `10-200`.")
    try:
        low, high = float(arr[0]), float(arr[1])
    except Exception as e:
        raise e
    if low > high:
        raise ValueError("low is greater than high")
    return low, high


def select_all(sql):
    cursor = db.cursor()
    print(sql)
    cursor.execute(sql)
    results = cursor.fetchall()
    field_names = [i[0] for i in cursor.description]
    data = []
    for row in results:
        row_data = {}
        for i, field_name in enumerate(field_names):
            row_data[field_name] = row[i]
        data.append(row_data)
    return data


def select_one(sql):
    cursor = db.cursor()
    print(sql)
    cursor.execute(sql)
    result = cursor.fetchone()
    data = {}
    field_names = [i[0] for i in cursor.description]
    for i, field_name in enumerate(field_names):
        data[field_name] = result[i]
    return data


def message_page(msg):
    return render_template("message.html", msg=msg)


def results_page(data, msg, **kwargs):
    return render_template("results.html", data=data, msg=msg, attachment=kwargs)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/queries")
def queries():
    return render_template("queries.html")


@app.route("/search")
def search():
    keyword = request.args.get("keyword")
    if not keyword:
        return message_page("Please input a keyword.")
    nlp = spacy.load("en_core_web_sm")
    matcher = Matcher(nlp.vocab)
    matcher.add('KEYWORD', [[{'LOWER': keyword}]])

    for path in os.listdir('static/books'):
        print("path:", path)
        with open('static/books/' + path, 'r') as f:
            text = f.read()
            doc = nlp(text.lower())
            matches = matcher(doc)
            print(matches)

    return message_page("Not implemented yet.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

from cmath import asin, cos, sin, sqrt
from datetime import datetime
from dateutil import parser
from dis import dis
import json
from math import radians
import random
import time
import redis
import pymysql
import pickle

from flask import Flask, render_template, request

app = Flask(__name__)
app.config['DEBUG'] = True

db = pymysql.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="cloudcomputing"
)

redis_ins = redis.StrictRedis(host='localhost', port=6379, db=0)


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


@app.route("/task1")
def task1():
    n = request.args.get("n")
    try:
        n = int(n)
    except Exception as e:
        return message_page("n should be a number")
    names = request.args.get("names")
    if not n or not names:
        return message_page("n and names are required")
    print(n, names)
    names_arr = names.split(",")
    print(names_arr)
    if len(names_arr) != n:
        return message_page("the length of names is not equals to n")
    data = []
    for name in names_arr:
        sql = "select count(*) as cnt from quiz4 where col_4 = '{}'".format(name)
        sql_data = select_one(sql)
        data.append({
            'fruit': name,
            'cnt': sql_data['cnt']
        })
    print(data)
    return results_page(data, None, task_name='task_1')


@app.route("/task2")
def task2():
    n = request.args.get("n")
    try:
        n = int(n)
    except Exception as e:
        return message_page("n should be a number")
    if not n:
        return message_page("n and names are required")
    sql = "select count(0) as cnt, col_4 as fruit from quiz4 group by col_4 order by cnt desc limit {}".format(n)
    data = select_all(sql)  
    print(data)
    return results_page(data, None, task_name='task_2')


@app.route("/task3")
def task3():
    range = request.args.get("range")
    try:
        low, high = get_range(range)
        low, high = int(low), int(high)
    except Exception as e:
        return message_page("Failed to parse range, err = {}".format(e))
    sql = "select * from quiz4 where col_1 >= {} and col_1 <= {}".format(low, high)
    data = select_all(sql)
    print(data)
    return results_page(data, None, task_name='task_3')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

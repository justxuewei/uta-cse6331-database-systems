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
    start = time.time()
    n = request.args.get('n')
    if not n:
        return message_page("Please input a number to do random query.")
    place = request.args.get('place')
    lat, lng, distance = request.args.get('lat'), request.args.get(
        'lng'), request.args.get('distance')
    if lat and lng and distance:
        try:
            lat = float(lat)
            lng = float(lng)
            distance = float(distance)
        except Exception as e:
            return message_page("Invalid latitude or longitude, err = {}.".format(e))
    # time_range = 20200202-20200304
    time_range = request.args.get('time_range')
    if time_range:
        time_range_low, time_range_high = get_range(time_range)
        time_range_low = datetime.strptime(str(int(time_range_low)), "%Y%m%d")
        time_range_high = datetime.strptime(str(int(time_range_high)), "%Y%m%d")
        print('time_range_low = {}, time_range_high = {}'.format(
            time_range_low, time_range_high))

    mag_range = request.args.get('mag_range')
    if mag_range:
        try:
            mag_range_low, mag_range_high = get_range(mag_range)
        except Exception as e:
            return message_page("Invalid magnitude range, err = {}.".format(e))

    if redis_ins.exists(cache_key('task1', n)):
        db_data = pickle.loads(redis_ins.get(cache_key('task1', n)))
        msg = "cache hit"
    else:
        db_data = select_all(
            "select * from earthquakes where 1=1 order by rand() limit {}".format(n))
        redis_ins.set(cache_key('task1', n), pickle.dumps(db_data))
        redis_ins.expire(cache_key('task1', n), 5)
        msg = "cache missed"

    data = []
    for row in db_data:
        if place and place not in row['place']:
            continue
        if lat and lng and distance and get_distance(
                row['lng'], row['lat'], lng, lat) > distance:
            continue
        if time_range and (row['time'] < time_range_low or row['time'] > time_range_high):
            continue
        if mag_range and (row['mag'] < mag_range_low or row['mag'] > mag_range_high):
            continue
        data.append(row)

    msg += ", elapsed time = {}".format(time.time() - start)

    return results_page(data, msg)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

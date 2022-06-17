import csv
from unittest import result
import pymysql
from datetime import datetime

from flask import Flask, render_template, request, redirect

app = Flask(__name__)
app.config['DEBUG'] = True

db = pymysql.connect(
    host="localhost",
    user="root",
    password="12345678",
    database="cloudcomputing"
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/bounding_box')
def bounding_box():
    x1 = request.args.get("x1")
    y1 = request.args.get("y1")
    x2 = request.args.get("x2")
    y2 = request.args.get("y2")

    if x1 is None or y1 is None or x2 is None or y2 is None:
        return render_template("bounding_box.html")

    try:
        x1 = float(x1)
        y1 = float(y1)
        x2 = float(x2)
        y2 = float(y2)
    except Exception as e:
        return render_template("error.html", msg="value type is unsupported, err = {}".format(e))

    if x1 > x2 or y1 > y2:
        return render_template("error.html", msg="x1, y1 should less than x2, y2, respectively")

    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM earthquakes WHERE latitude >= {} AND longitude >= {} AND latitude <= {} AND longitude <= {}".format(x1, y1, x2, y2))
    results = cursor.fetchall()
    field_names = [i[0] for i in cursor.description]

    data = []
    for row in results:
        row_data = {}
        for i, field_name in enumerate(field_names):
            row_data[field_name] = row[i]
        data.append(row_data)

    return render_template("result.html", data=data)


@app.route("/largest_quakes")
def largest_quakes():
    net = request.args.get("net")
    magnitude_range = request.args.get("magnitude_range")
    if net is None or magnitude_range is None:
        return render_template("largest_quakes.html")

    low, high = get_range(magnitude_range)

    cursor = db.cursor()
    sql = "SELECT * FROM earthquakes WHERE mag >= {} AND mag <= {} AND net = '{}' ORDER BY mag LIMIT 5".format(
        low, high, net)
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

    return render_template("result.html", data=data)


@app.route("/single_date")
def single_date():
    date = request.args.get("date")
    time_range = request.args.get("time_range")
    if date is None or time_range is None:
        return render_template("single_date.html")
    
    low, high = get_range(time_range)
    low = int(low)
    high = int(high)

    started = datetime.strptime("{}T{}".format(date, low), "%Y-%m-%dT%H")
    ended = datetime.strptime("{}T{}".format(date, high), "%Y-%m-%dT%H")

    print(started)
    print(ended)

    cursor = db.cursor()
    sql = "SELECT count(*), net FROM earthquakes WHERE time >= '{}' AND time <= '{}' GROUP BY net ORDER BY  net limit 1;".format(
        started, ended)
    print(sql)
    cursor.execute(sql)
    result = cursor.fetchone()
    print(result)
    
    return render_template("single_date_result.html", count=result[0], net=result[1])


def get_range(range_str):
    arr = range_str.split('-')
    if len(arr) != 2:
        return 0, 0
    return float(arr[0]), float(arr[1])


@app.route("/replace_nn")
def replace_nn():
    nn = request.args.get("nn")
    rnn = request.args.get("rnn")
    if nn is None or rnn is None:
        return render_template("replace_nn.html")
    
    cursor = db.cursor()
    sql = "UPDATE earthquakes SET net = '{}' WHERE net = '{}'".format(rnn, nn)
    print(sql)
    rows = cursor.execute(sql)
    db.commit()

    return render_template("error.html", msg="successfully update, affected rows = {}".format(rows))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

import pymysql
import config

from datetime import datetime
from flask import Flask, render_template, request, redirect
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)
app.config['DEBUG'] = True

db = pymysql.connect(
    host=config.db_host,
    user=config.db_user,
    password=config.db_password,
    database=config.db_database,
)


@app.route("/")
def index():
    return render_template("index.html")


def get_range(range_str):
    arr = range_str.split('-')
    if len(arr) != 2:
        raise ValueError
    try:
        return float(arr[0]), float(arr[1])
    except Exception as e:
        raise e


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


def get_distance(lng1, lat1, lng2, lat2):
    lng1, lat1, lng2, lat2 = map(
        radians, [float(lng1), float(lat1), float(lng2), float(lat2)])
    dlon = lng2-lng1
    dlat = lat2-lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    distance = 2*asin(sqrt(a))*6371*1000  # 地球平均半径，6371km
    distance = round(distance/1000, 3)
    return distance


@app.route("/mag_greater_than_5")
def mag_greater_than_5():
    sql = "SELECT * FROM earthquakes WHERE mag >= 5"
    data = select_all(sql)
    sql = "SELECT COUNT(*) as cnt FROM earthquakes WHERE mag >= 5"
    cnt = select_one(sql)['cnt']
    return render_template("result.html", data=data, cnt=cnt)


@app.route("/queries")
def queries():
    return render_template("queries.html")


@app.route("/mags")
def mags():
    started_date = request.args.get("started_date")
    ended_date = request.args.get("ended_date")
    mag_range = request.args.get("mag_range")
    if started_date is None:
        return render_template("message.html", msg="started_date is required")
    if ended_date is None:
        return render_template("message.html", msg="ended_date is required")
    if mag_range is None:
        return render_template("message.html", msg="mag_range is required")

    try:
        low, high = get_range(mag_range)
    except Exception as e:
        return message_page("failed to retrieve mag range, err = {}".format(e))

    started = datetime.strptime(started_date, "%Y-%m-%d")
    ended = datetime.strptime(ended_date, "%Y-%m-%d")
    sql = "SELECT * FROM earthquakes WHERE mag >= {} AND mag <= {} AND time >= '{}' AND time <= '{}'".format(
        low, high, started, ended
    )
    data = select_all(sql)
    return render_template("result.html", data=data)


@app.route("/near")
def near():
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")
    distance = request.args.get("distance")

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        distance = float(distance)
    except Exception as e:
        return message_page("latitude, longitude and distance should be float values, err = {}".format(e))

    sql = "SELECT * FROM earthquakes"
    all_data = select_all(sql)
    data = []
    for earthquake in all_data:
        if get_distance(longitude, latitude, earthquake['longitude'], earthquake['latitude']) <= distance:
            data.append(earthquake)
    return render_template("result.html", data=data)


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
        return render_template("message.html", msg="value type is unsupported, err = {}".format(e))

    if x1 > x2 or y1 > y2:
        return render_template("message.html", msg="x1, y1 should less than x2, y2, respectively")

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

    return render_template("message.html", msg="successfully update, affected rows = {}".format(rows))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

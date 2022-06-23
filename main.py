import json
import random
import time
import redis
import pymysql

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
        raise ValueError("Invalid range format, for example, the valid format is `10-200`.")
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/queries")
def queries():
    return render_template("queryies.html")


@app.route("/task10")
def task10():
    start = time.time()
    elev_range = request.args.get("elev_range")
    number_range = request.args.get("number_range")
    if elev_range is None or number_range is None:
        return message_page("elev_range and number_range are required")
    try:
        elev_low, elev_high = get_range(elev_range)
        number_low, number_high = get_range(number_range)
        elev_low, elev_high = int(elev_low), int(elev_high)
        number_low, number_high = int(number_low), int(number_high)
    except Exception as e:
        return message_page("failed to parse range, err = {}".format(e))

    if redis_ins.exists(cache_key('task10', elev_range, number_range)):
        data = json.loads(redis_ins.get(cache_key('task10', elev_range, number_range)).decode())
        print('cached data = {}'.format(data))
    else:
        sql = "SELECT * FROM v WHERE elev >= {}  AND elev <= {} AND number >= {} AND number <= {}".format(elev_low,
                                                                                                          elev_high,
                                                                                                          number_low,
                                                                                                          number_high)
        data = select_all(sql)
        redis_ins.set(cache_key('task10', elev_range, number_range), json.dumps(data))
        redis_ins.expire(cache_key('task10', elev_range, number_range), 5)
        redis_ins.incr('task10')

    if len(data) == 0:
        msg = "No data"
    else:
        largest_elev, least_elev = data[0]['elev'], data[0]['elev']
        for row in data:
            if least_elev > row['elev']:
                least_elev = row['elev']
            if largest_elev < row['elev']:
                largest_elev = row['elev']
        msg = "maximum elev = {}, minimum elev = {}".format(largest_elev, least_elev)
    times = redis_ins.get('task10')
    msg = "{}, query times = {}, elapsed time = {}".format(msg, times, time.time() - start)
    return render_template("results.html", data=data, msg=msg)


@app.route("/task11")
def task11():
    start = time.time()
    seq_range = request.args.get("seq_range")
    n = request.args.get("n")
    if seq_range is None or n is None:
        return message_page("seq_range and n are required")
    try:
        seq_low, seq_high = get_range(seq_range)
        seq_low, seq_high = int(seq_low), int(seq_high)
        n = int(n)
    except Exception as e:
        return message_page("failed to parse range, err = {}".format(e))

    sql = """select v.number as number, volcano_name, country, region, longitude, latitude, elev
from (select number from vindex where sequence >= {} and sequence <= {}) as vindex
         left join v on v.number = vindex.number;""".format(seq_low, seq_high)
    data = select_all(sql)
    sampled = random.sample(data, n)

    times = redis_ins.incr('task11')
    msg = "query times = {}, elapsed time = {}".format(times, time.time() - start)
    return render_template("results.html", data=sampled, msg=msg)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

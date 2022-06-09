import csv

from flask import Flask, render_template, request, redirect

app = Flask(__name__)
app.config['DEBUG'] = True


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/imginfo")
def imginfo():
    height_range = request.args.get("height_range")
    height_low = None
    height_high = None
    if height_range is not None:
        height_range_arr = height_range.split("-")
        if len(height_range_arr) == 2:
            try:
                height_low = int(height_range_arr[0])
                height_high = int(height_range_arr[1])
            except ValueError:
                print("invalid value, height range = {}".format(height_range))
    metadata = []
    with open("static/data.csv", "r") as csvfile:
        csvdata = csv.DictReader(csvfile)
        for row in csvdata:
            metadata.append(row)
    filtered_metadata = []
    if height_low is not None and height_high is not None:
        for i in metadata:
            try:
                height_int = int(i['Height'])
            except ValueError:
                continue
            if height_low <= height_int <= height_high:
                filtered_metadata.append(i)
    else:
        filtered_metadata = metadata

    return render_template("imginfo.html", metadata=filtered_metadata)


@app.route("/height_selector")
def height_selector():
    return render_template("height_selector.html")


@app.route("/edit_imginfo")
def edit_imginfo():
    author = request.args.get("author")
    keywords = request.args.get("keywords")
    if author is None:
        return render_template("edit_imginfo.html")

    metadata = []
    with open("static/data.csv", "r") as csvfile:
        csvdata = csv.DictReader(csvfile)
        for row in csvdata:
            if row['Author'] == author:
                row['Keywords'] = keywords
            metadata.append(row)

    with open("static/data.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['Name', 'Height', 'Author', 'Picture', 'Keywords'])
        writer.writeheader()
        for row in metadata:
            writer.writerow(row)

    return redirect("/imginfo", code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

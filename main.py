import csv

from flask import Flask, render_template, request, redirect

app = Flask(__name__)
app.config['DEBUG'] = True

csv_file = "static/people.csv"
csv_headers = ['Name', 'State', 'Salary', 'Grade', 'Room', 'Telnum', 'Picture', 'Keywords']


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/imginfo")
def imginfo():
    # salary range
    salary_range = request.args.get("salary")
    salary_low = None
    salary_high = None
    if salary_range is not None:
        salary_range_arr = salary_range.split("-")
        if len(salary_range_arr) == 2:
            try:
                salary_low = int(salary_range_arr[0])
                salary_high = int(salary_range_arr[1])
            except ValueError:
                print("invalid value, height range = {}".format(salary_range))
    # name
    name = request.args.get("name")

    metadata = []
    with open(csv_file, "r") as csvfile:
        csvdata = csv.DictReader(csvfile)
        for row in csvdata:
            metadata.append(row)
    filtered_metadata = []

    for i in metadata:
        if salary_low is not None and salary_high is not None:
            try:
                salary_int = int(i['Salary'])
            except ValueError:
                continue
            if salary_low <= salary_int <= salary_high:
                filtered_metadata.append(i)
            continue
        if name is not None and name != "":
            if name == i['Name']:
                filtered_metadata.append(i)
            continue
        filtered_metadata.append(i)

    return render_template("imginfo.html", metadata=filtered_metadata)


@app.route("/img_selectors")
def height_selector():
    return render_template("img_selectors.html")


@app.route("/edit_imginfo")
def edit_imginfo():
    name = request.args.get("name")
    picture = request.args.get("picture")
    keywords = request.args.get("keywords")
    salary = request.args.get("salary")
    if name is None:
        return render_template("edit_imginfo.html")

    metadata = []
    with open(csv_file, "r") as csvfile:
        csvdata = csv.DictReader(csvfile)
        for row in csvdata:
            if row['Name'] == name:
                if keywords is not None and keywords != "":
                    row['Keywords'] = keywords
                if picture is not None and picture != "":
                    row['Picture'] = picture
                if salary is not None and salary != "":
                    row['Salary'] = salary
            metadata.append(row)

    with open(csv_file, "w") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        for row in metadata:
            writer.writerow(row)

    return redirect("/imginfo", code=302)


@app.route("/add_imginfo", methods=['GET', 'POST'])
def add_imginfo():
    if request.form is not None and request.form.get("name") is not None:
        name = request.form.get("name")
        num = request.form.get("num")
        keywords = request.form.get("keywords")

        picture = request.files.get("picture")

        print(request.form)
        print(request.files)
        print(picture)
        picture_name = None
        if picture is not None:
            print(picture.name)
            picture_name = picture.name
            picture.save("static/{}".format(picture.name))

        metadata = []
        with open(csv_file, "r") as csvfile:
            csvdata = csv.DictReader(csvfile)
            for row in csvdata:
                if row['Name'] == name:
                    row['Keywords'] = keywords
                    row['Picture'] = picture
                metadata.append(row)

        with open(csv_file, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
            writer.writeheader()
            for row in metadata:
                writer.writerow(row)
            writer.writerow({
                'Name': name,
                'Num': num,
                'Picture': picture_name,
                'Keywords': keywords
            })
        return redirect("/imginfo", code=302)

    return render_template("add_imginfo.html")


@app.route("/delete_imginfo")
def delete_imginfo():
    name = request.args.get("name")
    if name is None:
        return render_template("delete_imginfo.html")

    metadata = []
    with open(csv_file, "r") as csvfile:
        csvdata = csv.DictReader(csvfile)
        for row in csvdata:
            metadata.append(row)

    with open(csv_file, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        for row in metadata:
            if row['Name'] != name:
                writer.writerow(row)

    return redirect("/imginfo", code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

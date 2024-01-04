from flask import Flask, render_template, request, redirect
import os, csv, shutil
import pandas as pd
import ast
from werkzeug.utils import secure_filename


app = Flask(__name__)

db_dirPath = "./data"
temp_dir = "./static/temp"
ALLOWED_EXTENSIONS = set(["csv", "txt"])

@app.route("/index", methods=["POST", "GET"])
def index():
    DB = []
    if request.method == "POST":
        dbName = request.form.get("dbName")
        folder = os.path.exists(f"{db_dirPath}/{dbName}")
        if not folder:
            os.makedirs(f"{db_dirPath}/{dbName}")
        for filename in os.listdir(db_dirPath):
            DB.append(filename)
        
        return render_template("index.html", DB=DB)
    else:
        db_table = []
        dbName = request.args.get("dbName")
        folder = os.path.exists(f"{db_dirPath}/{dbName}")
        search_query = request.args.get("search_query")
        if search_query is not None:
            for filename in os.listdir(db_dirPath):
                if filename == search_query:
                    DB.append(filename)      
            if folder:
                for filename in os.listdir(f"{db_dirPath}/{dbName}"):
                    db_table.append(os.path.splitext(filename)[0])
                print(db_table)    
        else:
            if folder:
                for filename in os.listdir(f"{db_dirPath}/{dbName}"):
                    db_table.append(os.path.splitext(filename)[0])
                print(db_table)
            for filename in os.listdir(db_dirPath):
                DB.append(filename)
        return render_template("index.html", DB=DB, db_table=db_table, search_query = search_query)
    
@app.route("/deleteDB")
def delete_db():
    dbName = request.args.get("dbName")
    if os.path.isdir(f"{db_dirPath}/{dbName}"):
        shutil.rmtree(f"{db_dirPath}/{dbName}")
    return redirect("/index")

@app.route("/database", methods=["POST", "GET"])
def database():
    db = request.args.get("db")
    search_query = request.form.get("search_query")
    table = []
    if request.method == "POST":
        print(search_query)
        folder = os.path.exists(f"{db_dirPath}/{db}")
        if folder:
            for filename in os.listdir(f"{db_dirPath}/{db}"):
                print(filename)
                if os.path.splitext(filename)[0] == search_query:
                    table.append(os.path.splitext(filename)[0])
            print(table)
        return render_template("database.html", db=db, table=table)
    else:
        folder = os.path.exists(f"{db_dirPath}/{db}")
        if folder:
            for filename in os.listdir(f"{db_dirPath}/{db}"):
                table.append(os.path.splitext(filename)[0])
            print(table)
        return render_template("database.html", db=db, table=table)
    
@app.route("/deleteTable")
def delete_table():
    table_name = request.args.get("table")
    db = request.args.get("db")
    os.remove(f"{db_dirPath}/{db}/{table_name}.csv")
    return redirect(f"/database?db={db}")

@app.route("/createTable", methods=["POST", "GET"])
def create_table():
    db = request.args.get("db")
    if request.method == "POST":
        t_name = request.args.get("table_name")
        headers = request.form.getlist("column_headers")
        with open(f"./{db_dirPath}/{db}/{t_name}.csv", "w", encoding='utf-8') as file:
            csvWriter =  csv.writer(file)
            csvWriter.writerow(headers)
        return redirect(f"/database?db={db}")
    else:
        if request.args.get("table_name"):
            t_name = request.args.get("table_name")
            t_column = int(request.args.get("table_column"))
            return render_template("createTable.html", db=db, t_name = t_name, t_column = t_column)
        return render_template("createTable.html", db=db)
 
def getTableData(db, table):
    data = []
    with open(f"{db_dirPath}/{db}/{table}.csv", "r") as file:
        csv_reader = csv.reader(file)
        next(csv_reader)
        for i in csv_reader:
            temp = []
            for j in i:
                temp.append(j)
            data.append(temp)
    return data 
    
@app.route("/table", methods=["POST", "GET"])
def table():
    db = request.args.get("db")
    table = request.args.get("table")
    if request.method == "POST":
        if request.args.get("form_active"):
            new_data = request.form.getlist("column_data");
            data = []
            with open(f"{db_dirPath}/{db}/{table}.csv", "r") as file:
                for i in csv.reader(file):
                    data.append(i)
            data.append(new_data)
            with open(f"{db_dirPath}/{db}/{table}.csv", "w") as file:
                csvWriter =  csv.writer(file)
                for i in data:
                    csvWriter.writerow(i)
            print(data)
        elif request.args.get("import"):
            import_file = request.files["import_file"]
            import_file.save(os.path.join(f"{temp_dir}", import_file.filename))
            fileName = import_file.filename
            new_data = []
            with open(f"{temp_dir}/{fileName}", "r", encoding="utf-8") as file:
                for i in csv.reader(file):
                    new_data.append(i)
            data = []
            with open(f"{db_dirPath}/{db}/{table}.csv", "r") as file:
                for i in csv.reader(file):
                    data.append(i)
            for i in new_data:
                data.append(i)
            with open(f"{db_dirPath}/{db}/{table}.csv", "w") as file:
                csvWriter =  csv.writer(file)
                for i in data:
                    csvWriter.writerow(i)
            print(new_data)
            os.remove(f"{temp_dir}/{fileName}")
        else:
            column_headers = list(pd.read_csv(f"{db_dirPath}/{db}/{table}.csv").columns)
            data = []
            search_query = request.form.get("search_query")
            with open(f"{db_dirPath}/{db}/{table}.csv", "r") as file:
                csv_reader = csv.reader(file)
                next(csv_reader)
                for i in csv_reader:
                    for j in i:
                        if j == search_query:
                            data.append(i)
            return render_template("table.html", db=db, table=table, column_headers=column_headers, data = data)
        return redirect(f"/table?db={db}&table={table}")
    else:
        column_headers = list(pd.read_csv(f"{db_dirPath}/{db}/{table}.csv").columns)
        data = getTableData(db, table)
        data.sort(key=lambda x: x[0])
        if request.args.get("form_active"):
            return render_template("table.html", db=db, table=table, column_headers=column_headers, data = data, form_active=request.args.get("form_active"))
        elif request.args.get("import"):
            return render_template("table.html", db=db, table=table, column_headers=column_headers, data = data, import_form = request.args.get("import"))
        return render_template("table.html", db=db, table=table, column_headers=column_headers, data = data)

@app.route("/updateData", methods=["POST", "GET"])
def updateData():
    db = request.args.get("db")
    table = request.args.get("table")
    original_data = request.args.getlist("data")
    column_headers = list(pd.read_csv(f"{db_dirPath}/{db}/{table}.csv").columns)
    if request.method == "POST":
        data = []
        new_data = request.form.getlist("column_data");
        with open(f"{db_dirPath}/{db}/{table}.csv", "r") as file:
            for index, row in enumerate(file):
                rowList = row.strip().split(",")
                if rowList == original_data:
                    print(index)
                else:
                    data.append(rowList)
        data.append(new_data)
        print(data)
        with open(f"{db_dirPath}/{db}/{table}.csv", "w") as file:
            csvWriter = csv.writer(file)
            for i in data:
                csvWriter.writerow(i)
        return redirect(f"/table?db={db}&table={table}")
    else:
        return render_template("update_data.html", db=db, table=table, column_headers=column_headers, data = original_data)

@app.route("/deleteData")
def deleteData():
    db = request.args.get("db")
    table = request.args.get("table")
    dest = ast.literal_eval(request.args.get("dest"))
    data = []
    with open(f"{db_dirPath}/{db}/{table}.csv", "r") as file:
        for index, row in enumerate(file):
            rowList = row.strip().split(",")
            if rowList == dest:
                print(index)
            else:
                data.append(rowList)
        print(data)
    with open(f"{db_dirPath}/{db}/{table}.csv", "w") as file:
        csvWriter = csv.writer(file)
        for i in data:
            csvWriter.writerow(i)
    return redirect(f"/table?db={db}&table={table}")
    
    
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
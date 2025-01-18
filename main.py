from unittest import result
from flask import Flask,jsonify,request,render_template, redirect,url_for
from db import db
app = Flask(__name__)

collection = db["attendance"]

@app.route('/')
def attendance():
    return 'attendance system running'


#add attendance
@app.route('/add-attendance',methods=['POST'])
def add_attendance():
    data = request.get_json()
    try:
       result = collection.insert_one(data)
       return jsonify({"message":"attendance added successfully","id":str(result.inserted_id)}),201
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@app.route('/get-attendance', methods=['GET'])

#get attendance
def get_attendance():
    try:
        data = list(collection.find())
        for record in data:
            record["_id"] = str(record["_id"])
        
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/user")
def welcome_page():
    return render_template("user.html")

@app.route("/login", methods = ["GET", "POST"])
def user_login():
    if request.method == 'POST':
        userEmail = request.form["userEmail"]
        password = request.form["password"]
        
        return redirect(url_for("../templates/login"))
    return render_template("login.html")


if __name__ == '__main__':
    app.run(debug=True)
    
from unittest import result
from bson import json_util
from werkzeug.utils import secure_filename
from flask import Flask,jsonify,request,render_template, redirect,url_for
from db import db
import pandas as pd
from flask_cors import CORS
import os
import tempfile

app = Flask(__name__)
CORS(app)

collection = db["attendance"]

@app.route('/')
def attendance():
    return 'attendance system running'

@app.route("/admin_page",methods = ["GET"])
def admin_page():
    return render_template("admin.html")

#create collection
@app.route("/createCollection", methods=["POST"])
def create_collection():
    data = request.get_json()
    collection_name = data.get("name")
    
    if not collection_name:
        return jsonify({"message": "Collection name is required"}), 400

    try:
        db.create_collection(collection_name)
        return jsonify({"message": f"Collection '{collection_name}' created successfully"}), 201
    except Exception as e:
        return jsonify({"message": f"Failed to create collection: {str(e)}"}), 500
    

#get collections
@app.route("/getCollections", methods=["GET"])
def get_collections():
    try:
        collections = db.list_collection_names()
        return jsonify(collections), 200
    except Exception as e:
        return jsonify({"message": f"Failed to fetch collections: {str(e)}"}), 500
  
    
#get collection data 
@app.route("/getCollectionData/<collection_name>", methods=["GET"])
def get_collection_data(collection_name):
    try:
        collection = db[collection_name]
        data = list(collection.find())  

        for doc in data:
            doc["_id"] = str(doc["_id"])

        return jsonify(data), 200
    except Exception as e:
        return jsonify({"message": f"Failed to fetch data from collection '{collection_name}': {str(e)}"}), 500


#upload files
@app.route("/uploadFiles", methods=["POST"])
def upload_excel_files():
    if "files" not in request.files or "collection" not in request.form:
        return jsonify({"message": "Files and collection name are required"}), 400

    files = request.files.getlist("files")
    collection_name = request.form["collection"]

    if len(files) == 0 or not collection_name:
        return jsonify({"message": "No files or collection name provided"}), 400

    try:
        merged_data = []
        for file in files:
            filename = secure_filename(file.filename)

            # save in  a temporary file 
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                filepath = tmp_file.name
                file.save(filepath)

            # Load the Excel file 
            try:
                with pd.ExcelFile(filepath) as excel_file:
                    # Scenario 1: Single sheet
                    if len(excel_file.sheet_names) == 1:
                        df = excel_file.parse(sheet_name=0)  
                        # df = df.dropna() 
                        df = df.fillna('***') 
                        df = df.drop_duplicates(subset=["Email"], keep="first")
                        merged_data.append(df)

                    # Scenario 2: Multiple sheets
                    else:
                        sheet_data = []
                        for sheet in excel_file.sheet_names:
                            try:
                                df = excel_file.parse(sheet_name=sheet)  
                                # df = df.dropna() 
                                df = df.fillna('***') 
                                if "Email" in df.columns:  
                                    df = df.drop_duplicates(subset=["Email"], keep="first")
                                    sheet_data.append(df)
                                else:
                                    return jsonify({"message": f"'Email' column missing in sheet '{sheet}'"}), 400
                            except Exception as sheet_error:
                                return jsonify({"message": f"Error processing sheet '{sheet}': {sheet_error}"}), 500

                        # Combine all sheets into one DataFrame
                        all_data = pd.concat(sheet_data, ignore_index=True)
                        all_data["days"] = all_data.groupby("Email")["Email"].transform("count")
                        all_data = all_data.drop_duplicates(subset=["Email"], keep="first")
                        merged_data.append(all_data)

            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)

        # Merge all data into a single DataFrame
        final_data = pd.concat(merged_data, ignore_index=True)
        data_to_insert = final_data.to_dict(orient="records")
        db[collection_name].insert_many(data_to_insert)

        return jsonify({"message": "All files uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"message": f"Failed to upload files: {str(e)}"}), 500




#get all attendance
@app.route("/get-attendance", methods=["GET"])
def get_attendance():
    try:
        data = collection.find()
        if data:
            data = list(data)
            for user in data:
                user["_id"] = str(user["_id"])
            return jsonify(data), 200
        else:
            return jsonify({"message": "No data found"}), 404
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500


#update attendance
@app.route('/update-attendance', methods=['PUT'])
def update_attendance():
    try:
        # Extract data from the request
        data = request.get_json()
        
        if not data or 'Email' not in data:
            return jsonify({"message": "Missing required fields"}), 400
        Email = data.get("Email")
        day1 = data.get("day1")
        day2 = data.get("day2")
        day3 = data.get("day3")
        days = data.get("days")
        

        # Find the user in the database by email
        user = collection.find_one({"Email": Email})

        if not user:
            return jsonify({"message": "User not found"}), 404
        
    
        result = collection.update_one(
            {"Email": Email},
            {"$set": {"day1": day1, "day2": day2, "day3": day3, "days": days}}
        )
        
        if result.modified_count == 1:
            return jsonify({"message": "Attendance updated successfully"}), 200
        else:
            return jsonify({"message": "Failed to update attendance"}), 500
     

    except Exception as e:
        # Log the exception for debugging
        print(f"Error occurred: {str(e)}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
   
    


#user page  
@app.route("/user")
def welcome_page():
    return render_template("user.html")

#login user login page
@app.route("/userLogin", methods = ["GET"])
def userLogin():
    return render_template("login.html")
    

#user login
@app.route("/login", methods = ["GET", "POST"])
def user_login():
   try:
       data = request.get_json()
       Email = data.get("Email")
       #check if email exists in the collection
       user = collection.find_one({"Email": Email})
       if user: 
           user["_id"] = str(user["_id"])
           return jsonify({"message": "User does exist", "details": user}), 200
             
       else:
         return jsonify({"message": "Email not found"}), 404
 
   except Exception as e:
      return jsonify({"message": "An error occurred", "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False)
    
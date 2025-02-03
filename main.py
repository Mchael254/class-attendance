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
    return 'attendance system up'

@app.route("/admin_page",methods = ["GET"])
def admin_page():
    return render_template("admin.html")

#create collection
@app.route("/createCollection", methods=["POST"])
def create_collection():
    data = request.get_json()
    print(data)
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
        if collection_name not in db.list_collection_names():
            return jsonify({"message": f"Collection '{collection_name}' not found"}), 404
        data = list(collection.find())  

        for doc in data:
            doc["_id"] = str(doc["_id"])

        return jsonify(data), 200
    except Exception as e:
        return jsonify({"message": f"Failed to fetch data from collection '{collection_name}': {str(e)}"}), 500

#delete collection
@app.route("/deleteCollection", methods=["DELETE"])
def delete_collection():
    try:
        collection_name = request.args.get("name")
        print(collection_name)
        #check if collection exists
        if collection_name not in db.list_collection_names():
            return jsonify({"message": f"Collection '{collection_name}' not found"}), 404
        
        db.drop_collection(collection_name)
        
        return jsonify({"message": f"Collection '{collection_name}' deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to delete collection '{collection_name}': {str(e)}"}), 500

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
                        df = df.dropna(how='all')
                        df = df.fillna('***') 
                       # Count the number of times an email exists and record it as "days"
                        df["days"] = df.groupby("Email")["Email"].transform("count")
                        df = df.drop_duplicates(subset=["Email"], keep="first")
                        merged_data.append(df)
                        
                    # Scenario 2: Multiple sheets
                    else:
                        sheet_data = []
                        for sheet in excel_file.sheet_names:
                            try:
                                df = excel_file.parse(sheet_name=sheet)  
                                # df = df.dropna() 
                                df = df.dropna(how='all')
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
                        
                        #column name sorted on the frontend

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



if __name__ == '__main__':
    app.run(debug=False)
    
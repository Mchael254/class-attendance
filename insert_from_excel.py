import pandas as pd
from db import db

collection = db["attendance"]

def insert_data_from_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        print(df.head())
        
        #convert to list dictionaries
        data_to_insert = df.to_dict(orient="records")
        
        #insert data to collection
        result = collection.insert_many(data_to_insert)
        
        print(f"Inserted {len(result.inserted_ids)} records successfully!")
    except Exception as e:
        print(f"Error occured while inserting data:{str(e)}")
        
if __name__ == "__main__":
    file_path = 'attendance.xlsx'
    insert_data_from_excel(file_path)
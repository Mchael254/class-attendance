from pymongo import MongoClient
mongo_url = "mongodb+srv://venum:Michael123.100#@cluster0.lgn11.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_url)
db = client["venum"]

try:
    # Initialize the MongoDB client
    client = MongoClient(mongo_url)
    print("Connection Successful!")
    
except Exception as e:
    print("Failed to connect to MongoDB:", e)
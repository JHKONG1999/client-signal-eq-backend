from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi import HTTPException
import os

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment
MONGO_URI = os.getenv("MONGO_URI")

# Connect to Mongo Atlas
try:
    client = MongoClient(MONGO_URI)
    print( "Connection Succeded")
except Exception as e:
    print("❌ ERROR:", str(e))
    raise HTTPException(status_code=500, detail="Internal Server Error")

db = client["ClientSignalDB"]

users_collection = db["Users"]
pquestion_collection = db["PQuestion"]
clients_collection = db["Clients"]
message_collection = db["Message"]
organization_collection = db["Organization"]
 

# DEBUG LINE
print("Connecting to:", MONGO_URI)  
from db import users_collection, clients_collection
from fastapi import HTTPException
from utils.normalize_email import normalize_email
from datetime import datetime

def create_client(data: dict, user_email: str):
    user_email = normalize_email(user_email)
    user = users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data["user_id"] = user["_id"]
    data["Date"] = datetime.utcnow()

    result = clients_collection.insert_one(data)
    return str(result.inserted_id)

def get_all_clients():
    return [
        {**client, "_id": str(client["_id"]), "user_id": str(client.get("user_id", ""))}
        for client in clients_collection.find({})
    ]

def get_client_by_email(email: str):
    email = normalize_email(email)
    client = clients_collection.find_one({"email": email})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client["_id"] = str(client["_id"])
    client["user_id"] = str(client.get("user_id", ""))
    return client

def get_clients_by_user(email: str):
    email = normalize_email(email)
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return [
        {**c, "_id": str(c["_id"]), "user_id": str(c.get("user_id", ""))}
        for c in clients_collection.find({"user_id": user["_id"]})
    ]

def update_client(email: str, update_data: dict):
    update_data["Date"] = datetime.utcnow()
    result = clients_collection.update_one({"email": email}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client data updated successfully"}

def delete_client(email: str):
    result = clients_collection.delete_one({"email": email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

from fastapi import HTTPException
from db import message_collection, clients_collection
from datetime import datetime

def get_next_message_id():
    last = message_collection.find_one(sort=[("messageId", -1)])
    return 1 if last is None else last["messageId"] + 1

def create_message(data: dict):
    data["messageId"] = get_next_message_id()
    current_time = datetime.utcnow()
    data["DateReceived"] = current_time
    data["DateResponded"] = current_time

    result = message_collection.insert_one(data)
    return {
        "mongo_id": str(result.inserted_id),
        "messageId": data["messageId"],
        "conversationId": data["conversationId"],
    }

def get_all_messages():
    return [{**msg, "_id": str(msg["_id"])} for msg in message_collection.find()]

def get_message(message_id: str):
    message = message_collection.find_one({"messageId": message_id})
    if message:
        message["_id"] = str(message["_id"])
        return message
    raise HTTPException(status_code=404, detail="Message not found")

def update_message(message_id: str, update_data: dict):
    update_data.pop("messageId", None)
    update_data.pop("DateReceived", None)

    clean_update = {k: v for k, v in update_data.items() if v is not None}
    if not clean_update:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    result = message_collection.update_one(
        {"messageId": message_id},
        {"$set": clean_update}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"message": "Message updated successfully"}

def delete_message(message_id: str):
    result = message_collection.delete_one({"messageId": message_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted successfully"}

def get_flagged_emails():
    flagged_messages = list(message_collection.find({"risk_score": {"$lte": 60}}))
    client_ids = [msg["client_id"] for msg in flagged_messages if "client_id" in msg]
    client_map = {}

    if client_ids:
        clients = clients_collection.find({"_id": {"$in": client_ids}})
        client_map = {client["_id"]: client["email"] for client in clients}

    result = []
    for msg in flagged_messages:
        client_email = None
        if "client_id" in msg:
            client_email = client_map.get(msg["client_id"], "unknown")

        result.append({
            "subject": msg.get("subject", ""),
            "risk_score": msg.get("risk_score", 0),
            "suggestedActions": msg.get("suggestedActions", []),
            "client_id": str(msg["client_id"]) if "client_id" in msg else None,
            "client_email": client_email
        })

    return result

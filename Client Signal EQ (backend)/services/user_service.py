from fastapi import HTTPException
from db import users_collection
from utils.normalize_email import normalize_email
from datetime import datetime

def generate_next_user_id():
    last = users_collection.find_one(sort=[("userId", -1)])
    return last["userId"] + 1 if last else 1

def create_account(data):
    email = normalize_email(data.email)

    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = {
        "userId": data.userId if data.userId is not None else generate_next_user_id(),
        "Name": data.name,
        "email": email,
        "Department": data.department,
        "Organization": data.organizationName,
        "Role": data.role,
        "Date": datetime.utcnow(),
        "clients": [],
        "Personality": None,
        "Personality_Check": {
            "answers": [],
            "submitted_at": None
        }
    }

    result = users_collection.insert_one(user)
    return {"success": True, "message": "Account created", "id": str(result.inserted_id)}

def get_user_by_email(email: str):
    email = normalize_email(email)
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_id"] = str(user["_id"])
    user["clients"] = [str(cid) for cid in user.get("clients", [])]
    return user

def update_user(user_id: int, data):
    email = normalize_email(data.email) if data.email else None

    if email:
        existing = users_collection.find_one({"email": email, "userId": {"$ne": user_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")

    field_map = {
        "name": "Name",
        "email": "email",
        "department": "Department",
        "organizationName": "Organization",
        "role": "Role"
    }

    update_data = {
        field_map[k]: v for k, v in data.dict(exclude_unset=True).items() if k in field_map and v is not None
    }

    update_data["Date"] = datetime.utcnow()

    result = users_collection.update_one({"userId": user_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User data updated successfully"}

def delete_user(user_id: int):
    result = users_collection.delete_one({"userId": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

def verify_user(email: str):
    email = normalize_email(email)
    return users_collection.find_one({"email": email}) is not None

def verify_profile(email: str):
    email = normalize_email(email)
    user = users_collection.find_one({"email": email})
    return bool(user and "Personality_Check" in user)

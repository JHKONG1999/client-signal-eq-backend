from fastapi import HTTPException
from db import users_collection
from utils.normalize_email import normalize_email
from models.user_models import LoginModel, PasswordData
from datetime import datetime

def login(data: LoginModel):
    email = normalize_email(data.email)
    user = users_collection.find_one({"email": email})

    if not user or user.get("password") != data.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "success": True,
        "message": "Login successful",
        "user": {
            "email": user["email"],
            "name": user.get("name", ""),
            "department": user.get("department", ""),
            "organizationName": user.get("organizationName", "")
        }
    }

def create_password(data: PasswordData):
    email = normalize_email(data.email)

    if data.password != data.checkpassword:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    users_collection.update_one(
        {"email": email},
        {"$set": {"password": data.password, "updatedAt": datetime.utcnow()}}
    )

    return {"success": True, "message": "Password set successfully"}

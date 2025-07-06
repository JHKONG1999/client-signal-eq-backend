from fastapi import APIRouter
from models.user_model import AccountData, UpdateUserModel
from services.user_service import (
    create_account,
    get_user_by_email,
    update_user,
    delete_user,
    verify_user,
    verify_profile
)

router = APIRouter()

@router.post("/api/auth/create-account")
def create_account_route(data: AccountData):
    return create_account(data)

@router.get("/api/auth/create-account/")
def get_user(email: str):
    return get_user_by_email(email)

@router.put("/api/auth/create-account/{user_id}")
def update_user_route(user_id: int, data: UpdateUserModel):
    return update_user(user_id, data)

@router.delete("/api/auth/create-account/{user_id}")
def delete_user_route(user_id: int):
    return delete_user(user_id)

@router.get("/api/auth/verify_user")
def verify_user_route(email: str):
    return verify_user(email)

@router.get("/api/auth/verify-profile")
def verify_profile_route(email: str):
    return verify_profile(email)

from fastapi import APIRouter
from models.user_models import LoginModel, PasswordData
from services.auth_service import login, create_password

router = APIRouter()

@router.post("/api/auth/login")
def login_endpoint(data: LoginModel):
    return login(data)

@router.post("/api/auth/create-password")
def password_endpoint(data: PasswordData):
    return create_password(data)

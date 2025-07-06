from pydantic import BaseModel, EmailStr
from typing import Optional

class AccountData(BaseModel):
    userId: Optional[int] = None
    name: str
    email: EmailStr
    department: str
    organizationName: str
    role: str

class UpdateUserModel(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    organizationName: Optional[str] = None
    role: Optional[str] = None

class PasswordData(BaseModel):
    email: EmailStr
    password: str
    checkpassword: str

class LoginModel(BaseModel):
    email: EmailStr
    password: str

from pydantic import BaseModel, EmailStr
from typing import Optional

class ClientModel(BaseModel):
    clientId: int
    email: EmailStr
    Name: str
    Role: str
    stakeHolderName: str

class UpdateClientModel(BaseModel):
    email: Optional[EmailStr] = None
    Name: Optional[str] = None
    Role: Optional[str] = None
    stakeHolderName: Optional[str] = None

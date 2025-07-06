from fastapi import APIRouter, Query
from models.client_model import ClientModel, UpdateClientModel
from services.client_service import (
    create_client,
    get_all_clients,
    get_client_by_email,
    get_clients_by_user,
    update_client,
    delete_client
)

router = APIRouter()

@router.post("/api/auth/clients")
def create_client_route(data: ClientModel):
    return create_client(data.dict(), user_email=data.email)

@router.get("/api/auth/clients")
def get_all_clients_route():
    return get_all_clients()

@router.get("/api/auth/clients-by-email")
def get_client_by_email_route(email: str = Query(...)):
    return get_client_by_email(email)

@router.get("/api/auth/clients-by-user")
def get_clients_by_user_route(email: str = Query(...)):
    return get_clients_by_user(email)

@router.put("/api/auth/clients/{email}")
def update_client_route(email: str, data: UpdateClientModel):
    return update_client(email, data.dict(exclude_unset=True))

@router.delete("/api/auth/clients/{email}")
def delete_client_route(email: str):
    return delete_client(email)

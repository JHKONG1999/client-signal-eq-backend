from fastapi import APIRouter
from models.message_model import MessageModel, UpdateMessageModel
from services.message_service import (
    create_message,
    get_all_messages,
    get_message,
    update_message,
    delete_message,
    get_flagged_emails
)

router = APIRouter()

@router.post("/api/auth/messages")
def create_message_route(data: MessageModel):
    return create_message(data.dict())

@router.get("/api/auth/messages")
def get_all_messages_route():
    return get_all_messages()

@router.get("/api/auth/messages/{message_id}")
def get_message_route(message_id: str):
    return get_message(message_id)

@router.put("/api/auth/messages/{message_id}")
def update_message_route(message_id: str, data: UpdateMessageModel):
    return update_message(message_id, data.dict(exclude_unset=True))

@router.delete("/api/auth/messages/{message_id}")
def delete_message_route(message_id: str):
    return delete_message(message_id)

@router.get("/api/auth/messages/flagged")
def get_flagged_emails_route():
    return get_flagged_emails()

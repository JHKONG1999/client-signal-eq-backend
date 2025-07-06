from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageModel(BaseModel):
    messageId: str
    subject: str
    conversationId: str
    context: Optional[str] = None
    behavior: Optional[str] = None
    sentiment: Optional[str] = ""
    risk_score: int
    suggestedActions: List[str]
    content: Optional[str] = ""
    from_email: Optional[str]

class UpdateMessageModel(BaseModel):
    context: Optional[str] = None
    conversationId: Optional[str] = None
    sentiment: Optional[str] = None
    subject: Optional[str] = None
    risk_score: Optional[int] = None
    suggestedActions: Optional[List[str]] = None

from pydantic import BaseModel
from typing import Dict

class QuestionAnswers(BaseModel):
    email: str
    answers: Dict[int, int]

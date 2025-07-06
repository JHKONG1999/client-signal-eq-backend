from fastapi import APIRouter
from models.question_model import QuestionAnswers
from services.question_service import submit_answers

router = APIRouter()

@router.post("/api/submit-answers")
def submit_answers_route(payload: QuestionAnswers):
    return submit_answers(payload)

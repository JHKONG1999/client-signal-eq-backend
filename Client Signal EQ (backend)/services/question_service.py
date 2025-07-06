from fastapi import HTTPException
from db import users_collection
from datetime import datetime

def submit_answers(payload):
    try:
        formatted_answers = [
            {"questionId": int(qid), "answerId": aid}
            for qid, aid in payload.answers.items()
        ]

        result = users_collection.update_one(
            {"email": payload.email},
            {
                "$set": {
                    "Personality_Check.answers": formatted_answers,
                    "Personality_Check.submitted_at": datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"success": True, "message": "Answers saved under Personality_Check"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

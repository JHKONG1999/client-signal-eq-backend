from fastapi import APIRouter, Header, Query, Request
from services.outlook_service import get_email_threads, get_personality_insights

router = APIRouter()

@router.get("/api/auth/outlook-threads")
async def outlook_threads(request: Request):
    return await get_email_threads(request)

@router.get("/api/auth/personality-weekly-insights")
def weekly_insights(
    client_email: str = Query(...),
    authorization: str = Header(...)
):
    return get_personality_insights(client_email, authorization)

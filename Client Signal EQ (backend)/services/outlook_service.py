from fastapi import HTTPException, Request
from utils.html_utils import strip_html
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from datetime import datetime, timedelta
from collections import defaultdict
import httpx, requests

async def get_email_threads(request: Request):
    token = request.headers.get("authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid or missing Authorization header")

    access_token = token.split(" ")[1]
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    base_url = "https://graph.microsoft.com/v1.0"
    result_emails = defaultdict(list)

    async with httpx.AsyncClient() as client:
        url = f"{base_url}/me/messages?$top=10&$orderby=receivedDateTime desc"
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch emails")

        messages = response.json().get("value", [])
        for msg in messages:
            result_emails[msg.get("conversationId")].append({
                "email_id": msg.get("id"),
                "subject": msg.get("subject"),
                "from_name": msg.get("from", {}).get("emailAddress", {}).get("name"),
                "from_email": msg.get("from", {}).get("emailAddress", {}).get("address"),
                "received_at": msg.get("receivedDateTime"),
                "body_preview": msg.get("bodyPreview"),
                "full_body": strip_html(msg.get("body", {}).get("content")),
                "is_read": msg.get("isRead"),
                "has_attachments": msg.get("hasAttachments"),
                "web_link": msg.get("webLink")
            })

    return {"threads": result_emails}

def get_personality_insights(client_email: str, authorization: str):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid Authorization header format")

    token = authorization.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    url = f"https://graph.microsoft.com/v1.0/me/mailFolders/SentItems/messages?$search=\"to:{client_email}\"orderby=receivedDateTime desc"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch emails")

    emails = resp.json().get("value", [])
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    grouped = defaultdict(list)

    for msg in emails:
        try:
            sender = msg.get("from", {}).get("emailAddress", {}).get("address", "").lower()
            if sender != client_email.lower():
                continue

            received_at = parse_date(msg.get("receivedDateTime", ""))
            if received_at < seven_days_ago:
                continue

            body_html = msg.get("body", {}).get("content", "")
            soup = BeautifulSoup(body_html, "html.parser")
            clean = soup.get_text(separator=" ").strip()

            if clean:
                grouped[received_at.strftime("%Y-%m-%d")].append(clean)

        except Exception as e:
            print("❌ Failed to parse:", e)

    return {
        "client_email": client_email,
        "total_days": len(grouped),
        "total_messages": sum(len(v) for v in grouped.values()),
        "messages_by_day": grouped
    }

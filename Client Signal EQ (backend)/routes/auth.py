from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from db import users_collection, clients_collection,message_collection,organization_collection
from utils import normalize_email
from typing import Dict, List, Optional
from fastapi.responses import JSONResponse
from collections import defaultdict
from bson import ObjectId
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
import httpx, traceback, time, re, html, requests

#Connect router to FAST API
router = APIRouter()

# Class Create User Account (CRUD)
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

#API Endpoint of User Account Creation (CRUD)
#Create
def generate_next_user_id():
    last = users_collection.find_one(sort=[("userId", -1)])
    return last["userId"] + 1 if last else 1

@router.post("/api/auth/create-account")
async def create_account(data: AccountData):
    email = normalize_email(data.email)
    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = {
        "userId":data.userId if data.userId is not None else generate_next_user_id(),
        "Name": data.name,
        "email": email,
        "Department": data.department,
        "Organization": data.organizationName,
        "Role": data.role,
        "Date": datetime.utcnow(),
        "clients": [], 
        "Personality": None,  
        "Personality_Check": { 
        "answers": [],
        "submitted_at": None
      },
    }
    result = users_collection.insert_one(user)
    return {"success": True, "message": "Account created", "id": str(result.inserted_id)}

@router.get("/api/auth/verify-profile")
def verify_profile(email: EmailStr):
    email = normalize_email(email)
    user=users_collection.find_one({"email": email})
    if user and "Personality_Check" in user:
        return True
    else: 
        return False

#Read
@router.get("/api/auth/create-account/")
def get_user_by_email(email: EmailStr):
    email = normalize_email(email)
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_id"] = str(user["_id"])
    user["clients"] = [str(cid) for cid in user.get("clients", [])]
    return user

#Update
@router.put("/api/auth/create-account/{user_id}")
def update_user(user_id: int, data: UpdateUserModel):
    email = normalize_email(data.email) if data.email else None
    
    if email:
        existing = users_collection.find_one({
            "email": email,
            "userId": {"$ne": user_id}  # Exclude current user
        })
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use by another user")

    update_data= {
        "name": "Name",
        "email": "email",
        "department": "Department",
        "organizationName": "Organization",
        "role": "Role"
    }

    update_data = {
        update_data[k]: v
        for k, v in data.dict(exclude_unset=True).items()
        if k in update_data and v is not None
    }

    update_data.pop("Personality", None)
    update_data.pop("Personality_Check", None)
    update_data["Date"] = datetime.utcnow()

    result = users_collection.update_one({"userId": user_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User data updated successfully"}

#Delete
@router.delete("/api/auth/create-account/{user_id}")
def delete_user(user_id: int):
    result = users_collection.delete_one({"userId": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# Verify User exists in the database
@router.get("/api/auth/verify_user")
def verify_user(email: EmailStr):
    try:
        start = time.time()
        print("⏱️ Starting verify_user")

        email = normalize_email(email)
        result = users_collection.find_one({"email": email})

        print("✅ Query result:", result)
        print("⏱️ Finished in", time.time() - start, "seconds")

        return True if result else False

    except Exception as e:
        print("❌ ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Class: Set Password
class PasswordData(BaseModel):
    email: EmailStr
    password: str
    checkpassword: str

@router.post("/api/auth/create-password")
def create_password(data: PasswordData):
    email = normalize_email(data.email)
    if data.password != data.checkpassword:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "password": data.password,  # 🔓 No hashing
                "updatedAt": datetime.utcnow()
            }
        }
    )
    return {"success": True, "message": "Password set successfully"}

# Class: Login
class LoginModel(BaseModel):
    email: EmailStr
    password: str

@router.post("/api/auth/login")
def login(data: LoginModel):
    email = normalize_email(data.email)
    user = users_collection.find_one({"email": email})

    if not user or user.get("password") != data.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "success": True,
        "message": "Login successful",
        "user": {
            "email": user["email"],
            "name": user["name"],
            "department": user["department"],
            "organizationName": user["organizationName"]
        }
    }

# API Endpoint: Fetch Outlook Emails using MS Graph API
@router.get("/api/outlook-emails")
async def get_outlook_emails(authorization: str = Header(...)):

    # Validate Authorization format
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid authorization header format")
    
    # Extract token from "Bearer <token>"
    token = authorization.split(" ")[1]

    # Microsoft Graph API endpoint to fetch user's latest 10 Outlook email messages
    graph_url = "https://graph.microsoft.com/v1.0/me/messages?$top=10"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    # Make an API request to Microsoft Graph API to retrieve emails
    async with httpx.AsyncClient() as client:
        response = await client.get(graph_url, headers=headers)

    # Handle error response from Microsoft Graph
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch emails")

    # Parse/clean the data
    parsed_emails = []
    messages = response.json().get("value", [])

    for email in messages:
        parsed_emails.append({
            "email_id": email.get("id"),
            "subject": email.get("subject"),
            "from_name": email.get("from", {}).get("emailAddress", {}).get("name"),
            "from_email": email.get("from", {}).get("emailAddress", {}).get("address"),
            "received_at": email.get("receivedDateTime"),
            "body_preview": email.get("bodyPreview"),
            "full_body": email.get("body", {}).get("content"),
            "is_read": email.get("isRead"),
            "conversation_id": email.get("conversationId"),
            "has_attachments": email.get("hasAttachments"),
            "web_link": email.get("webLink")
        })
    print ("Parse Email Successfully  ",parsed_emails)
        

    # Return emails as JSON response
    return {"emails": parsed_emails}

# Class Store Questionaire

class QuestionAnswers(BaseModel):
    email: str  
    answers: Dict[int, int]

@router.post("/api/submit-answers")
def submit_answers(payload: QuestionAnswers):
    try:
        print("Received payload:", payload.dict())

        # Convert integer keys to strings for MongoDB
        formatted_answers =  [
            {"questionId": int(qid), "answerId": aid}
            for qid, aid in payload.answers.items()
        ]
        
        print(f"Looking for email = {payload.email}")
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
        print("Error saving answers:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/debug-submit")
async def debug_submit(request: Request):
    body = await request.json()
    print("Received body:", body)
    return {"ok": True}

# Class Storing Clients Data (CRUD)

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

# Create Function
def create_client(data: dict, user_email: str):
    data["Date"] = datetime.utcnow() 

    # Normalize and find user by their email
    user_email = normalize_email(user_email)
    user = users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Attach the user's MongoDB _id to the client document
    data["user_id"] = user["_id"]

    # Insert the client
    result = clients_collection.insert_one(data)

    return str(result.inserted_id)

    # Add client _id to user's 'clients' array
    #users_collection.update_one(
        #{"_id": user["_id"]},
        #{"$push": {"clients": client_id}})

    #return str(client_id)

# Read Function
def get_all_clients():
    clients_cursor = clients_collection.find({})
    clients = []

    for client in clients_cursor:
        client["_id"] = str(client["_id"])
        if "user_id" in client:
            client["user_id"] = str(client["user_id"])
        clients.append(client)

    return clients

# Update Function
def update_client(email: str, update_data: dict):
    update_data.pop("Messages", None) 
    update_data["Date"] = datetime.utcnow() 
    result = clients_collection.update_one({"email": email}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client data updated successfully"}

# Delete Function
def delete_client(email: str):
    result = clients_collection.delete_one({"email": email})


# API Endpoint for Clients Data Storing
@router.post("/api/auth/clients")
def create_client():
    return {"success": True, "inserted_id": inserted_id}

@router.get("/api/auth/clients")
def read_all():
    return get_all_clients()

@router.get("/api/auth/clients-by-email")
def get_client_by_email(email: EmailStr = Query(...)):
    email = normalize_email(email)
    client = clients_collection.find_one({"email": email})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client["_id"] = str(client["_id"])
    if "user_id" in client:
        client["user_id"] = str(client["user_id"])

    return client

@router.get("/api/auth/clients-by-user")
def get_clients_by_user(email: EmailStr = Query(...)):
    email = normalize_email(email)
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user["_id"]
    clients_cursor = clients_collection.find({"user_id": user_id})
    
    clients = []
    for client in clients_cursor:
        client["_id"] = str(client["_id"])
        if "user_id" in client:
            client["user_id"] = str(client["user_id"])
        clients.append(client)

    return clients

@router.put("/api/auth/clients/{email}")
def update(email: str, data:  UpdateClientModel):
    return update_client(email, {k: v for k, v in data.dict().items() if v is not None})

@router.delete("/api/auth/clients/{client_id}")
def delete(client_id: int):
    return delete_client(client_id)

# Class Storing Message Data (CRUD)
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

class MessageResponseModel(MessageModel):
    _id: str
    DateResponded: Optional[datetime] = None

class UpdateMessageModel(BaseModel):
    context: Optional[str] = None
    conversationId: Optional[str] = None
    sentiment: Optional[str] = None
    subject: Optional[str] = None
    risk_score: Optional[int] = None
    suggestedActions: Optional[List[str]] = None

# Create Function
def get_next_message_id():
    last_message = message_collection.find_one(sort=[("messageId", -1)])
    return 1 if last_message is None else last_message["messageId"] + 1

def create_message(data: dict):
    # Auto-generate 
    data["messageId"] = get_next_message_id()
    current_time = datetime.utcnow()
    data["DateReceived"] = current_time
    data["DateResponded"] = current_time
    
    result = message_collection.insert_one(data)
    return {
        "mongo_id": str(result.inserted_id),
        "messageId": data["messageId"],
        "conversationId": data["conversationId"],
    }

#Read All Function
def get_all_messages():
    messages = message_collection.find()
    return [{**msg, "_id": str(msg["_id"])} for msg in messages]

#Read Specific Message Function
def get_message(message_id: str):
    message = message_collection.find_one({"messageId": message_id})
    if message:
        message["_id"] = str(message["_id"])
        return message
    return None

#Update Function
def update_message(message_id: str, update_data: dict):
    update_data.pop("messageId", None)
    update_data.pop("DateReceived", None)
    
    clean_update = {k: v for k, v in update_data.items() if v is not None}
    
    if not clean_update:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    result = message_collection.update_one(
        {"messageId": message_id},
        {"$set": clean_update}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message updated successfully"}

#Delete Function
def delete_message(message_id: str):
    result = message_collection.delete_one({"messageId": message_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted successfully"}

# Flagged Email Function
def get_flagged_emails():
   flagged_messages = list(message_collection.find({"risk_score": {"$lte": 60}}))

# Resolve client emails only at response time
   client_ids = [msg["client_id"] for msg in flagged_messages if "client_id" in msg]
   client_map = {}

   if client_ids:
      clients = clients_collection.find({"_id": {"$in": client_ids}})
      client_map = {client["_id"]: client["email"] for client in clients}

      result = []
      for msg in flagged_messages:
        client_email = None
        if "client_id" in msg:
            client_email = client_map.get(msg["client_id"], "unknown")

        result.append({
            "subject": msg.get("subject", ""),
            "risk_score": msg.get("risk_score", 0),
            "suggestedActions": msg.get("suggestedActions", []),
            "client_id": str(msg["client_id"]) if "client_id" in msg else None,
            "client_email": client_email
                })

      return result

#API Endpoints of Storing Message
@router.post("/api/auth/messages")
def create_message_endpoint(data: MessageModel):
    return create_message(data.dict())

# API Endpoint for Flagged Email
@router.get("/api/auth/messages/flagged")
def get_flagged_emails_endpoint():
    return get_flagged_emails()

@router.get("/api/auth/messages/{message_id}")
def get_message_endpoint(message_id: str):
    message = get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.get("/api/auth/messages")
def get_all_messages_endpoint():
    return get_all_messages()

@router.put("/api/auth/messages/{message_id}")
def update_message_endpoint(message_id: str, data: UpdateMessageModel):
    return update_message(message_id, data.dict(exclude_unset=True))

@router.delete("/api/auth/messages/{message_id}")
def delete_message_endpoint(message_id: str):
    return delete_message(message_id)

#Endpoint: : Fetch Outlook Emails using MS Graph API (all conversation thread)
def strip_html(raw_html: str) -> str:
    clean_text = re.sub('<[^<]+?>', '', raw_html or '') 
    return html.unescape(clean_text) 

@router.get("/api/auth/outlook-threads")
async def get_outlook_threads(request: Request): 
        token = request.headers.get("authorization")

        if not token or not token.startswith("Bearer "):
            return JSONResponse(content={"error": "Invalid or Missing Authorization header"}, status_code=400)
        
        # extract just the token part
        access_token = token.split(" ")[1]
        print("🔐 Access Token:", access_token)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        } 

        base_url = "https://graph.microsoft.com/v1.0"
        result_emails = defaultdict(list)

        async with httpx.AsyncClient() as client:
            # Step 1: Fetch conversations
            messages_url = f"{base_url}/me/messages?$top=10&$orderby=receivedDateTime desc"
            msg_resp = await client.get(messages_url, headers=headers)

            if msg_resp.status_code != 200:
                return JSONResponse(
                    status_code=msg_resp.status_code,
                    content={"detail": f"Failed to fetch conversations", "error_response": msg_resp.text}
                )

            messages = msg_resp.json().get("value", [])

        # Step 2: For each conversation, fetch threads
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
 
 #Endpoints Receiving Last 7 days email (Personality Weekly Insights)
@router.get("/api/auth/personality-weekly-insights")
def get_weekly_personality_emails(
    client_email: str = Query(..., description="Client's email address"),
    authorization: str = Header(...),
):
    #Returns cleaned emails from a client, grouped by day, for the last 7 days.
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid Authorization header format")

    token = authorization.split(" ")[1]
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    # Microsoft Graph search API for sender email
    url = f"https://graph.microsoft.com/v1.0/me/mailFolders/SentItems/messages?$search=\"to:{email}\"orderby=receivedDateTime desc"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch emails")

    all_emails = resp.json().get("value", [])
    collect_weekly_email = datetime.utcnow() - timedelta(days=7)
    grouped_messages = defaultdict(list)

    for msg in all_emails:
            try:
                sender = msg.get("from", {}).get("emailAddress", {}).get("address", "").lower()
                if sender != client_email.lower():
                    continue

                received_at = parse_date(msg.get("receivedDateTime", ""))
                if received_at < collect_weekly_email:
                    continue

                html_body = msg.get("body", {}).get("content", "")
                soup = BeautifulSoup(html_body, "html.parser")
                clean_text = soup.get_text(separator=" ").strip()

                if clean_text:
                    date_str = received_at.strftime("%Y-%m-%d")
                    grouped_messages[date_str].append(clean_text)

            except Exception as e:
                print(f"❌ Failed to parse message: {e}")
                continue

    return {
        "client_email": client_email,
        "total_days": len(grouped_messages),
        "total_messages": sum(len(msgs) for msgs in grouped_messages.values()),
        "messages_by_day": grouped_messages
    }

# Organization Model
class OrganizationModel(BaseModel):
    organization_id: Optional [int]= None
    organization_name: str

class UpdateOrganizationModel(BaseModel):
    organization_name: Optional[str] = None

# Create Function
def create_organization(data: dict):
    # Step 1: Get current max organization_id
    latest = organization_collection.find_one(
        {}, sort=[("organization_id", -1)]
    )
    next_id = latest["organization_id"] + 1 if latest else 1

    # Step 2: Assign the next ID
    data["organization_id"] = next_id
    data["created_date"] = datetime.utcnow()
    result = organization_collection.insert_one(data)
    return str(result.inserted_id)


# Read All
def get_all_organizations():
    org_cursor = organization_collection.find({})
    organizations = []

    for org in org_cursor:
        org["_id"] = str(org["_id"])
        organizations.append(org)

    return organizations


# Read One
def get_organization_by_id(org_id: int):
    org = organization_collection.find_one({"organization_id": org_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org["_id"] = str(org["_id"])
    return org


# Update
def update_organization(org_id: int, update_data: dict):
    update_data.pop("created_date", None)
    update_data["updated_at"] = datetime.utcnow()
    result = organization_collection.update_one(
        {"organization_id": org_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"message": "Organization updated successfully"}


# Delete
def delete_organization(org_id: int):
    result = organization_collection.delete_one({"organization_id": org_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"message": "Organization deleted successfully"}

# API Endpoint for Organization (CRUD)

@router.post("/api/auth/organization", response_model=dict)
def api_create_organization(data: OrganizationModel):
    inserted_id = create_organization(data.dict())
    return {"inserted_id": inserted_id}

@router.get("/api/auth/organization", response_model=List[OrganizationModel])
def api_get_all_organizations():
    return get_all_organizations()

@router.get("/api/auth/organization/{org_id}", response_model=OrganizationModel)
def api_get_organization(org_id: int):
    org = get_organization_by_id(org_id)
    return org

@router.put("/api/auth/organization/{org_id}", response_model=dict)
def api_update_organization(org_id: int, update: UpdateOrganizationModel):
    return update_organization(org_id, update.dict(exclude_unset=True))

@router.delete("/api/auth/organization/{org_id}", response_model=dict)
def api_delete_organization(org_id: int):
    return delete_organization(org_id)
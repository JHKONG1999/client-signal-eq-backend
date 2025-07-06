from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime
from db import users_collection, pquestion_collection
from utils import normalize_email
from typing import Dict
import httpx 
import traceback
import openai
import re
import os
import ast

router = APIRouter()

@router.post("/api/llm/generate-personality")
def generate_personality(email: EmailStr):

    email = normalize_email(email)
    print("Db_email")
    try:
        user = users_collection.find_one({"email": email})
    except Exception as e:
        print("❌ ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

    OAI_Key = os.getenv("OpenAI")
    client = openai.OpenAI(api_key=OAI_Key)
    prompt = "Based on the following answers, generate a detailed personality profile:\n\n"

    print("Beggining")

    for i in user['Personality_Check']['answers']:
        q = pquestion_collection.find_one({"questionId": i['questionId']})
        prompt += q['content']+ "\n" + q['Answers'][i['answerId']] + "\n\n"

    print("Step1")

    prompt += (
            '''\nAnalyze the user's personality based on the questions provided and give the enneagram personality type in the the following summary format: \n\n 
                Type\n
                Description: Core traits (e.g., Type 3: “Driven, adaptable, success-oriented”).\n
                Strengths: Positive attributes (e.g., Type 3: “Confident, efficient”).\n
                Challenges: Weaknesses (e.g., Type 3: “May prioritize image”).\n
                Growth Tips: Strategies (e.g., Type 3: “Focus on intrinsic goals”).\n
                Conflict Behavior & Approach: Perception (e.g., Type 3: “Competitive, may seem dismissive”).\n
                Stress Response: Under pressure (e.g., Type 3: “Overworks to prove worth”).''')

    try:
        response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a personality psychologist generating user profiles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
        print ("Personality EXTRACTED")
    except Exception as e:
        print("❌ ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
        return -1

    print("Step 2")


    profile = parse_personality_text(response.choices[0].message.content.strip())

    try:
        result = users_collection.update_one(
            {"_id": user['_id']},
                {
                    "$set": {
                        "Personality": profile,
                    }
                }
        )
        print ("step 3")
        return {'message': 'Personality SAVED'}
    except Exception as e:
        print("❌ ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/api/llm/client-analysis-email")
def client_analisys_email(list):
    return 1



@router.get("/api/llm/get-personality")
def get_personality(email: EmailStr):
    email = normalize_email(email)
    try:
        print("getting personality")
        user= users_collection.find_one({"email": email})
        return user['Personality']
    except Exception as e:
        print("❌ ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

def parse_personality_text(text):
    sections = [
        'Type',
        'Description',
        'Strengths',
        'Challenges',
        'Growth Tips',
        'Conflict Behavior & Approach',
        'Stress Response'
    ]

    # Regex to match section headers
    pattern = r'({}):?'.format('|'.join([re.escape(s) for s in sections[1:]]))
    matches = list(re.finditer(pattern, text))
    result = {'Type': text.split('\n', 1)[0].strip()}

    if not matches:
        result['Description'] = text.split('\n', 1)[1].strip() if '\n' in text else ''
        for sec in sections[2:]:
            result[sec] = ''
        return result

    # Description
    start_desc = text.find('\n') + 1
    result['Description'] = text[start_desc:matches[0].start()].strip()

    # All other sections except Stress Response
    for i, match in enumerate(matches):
        sec = match.group(1)
        start = match.end()
        # Special handling for Stress Response
        if sec == 'Stress Response':
            # Find first double newline after this section's start
            rest = text[start:]
            end_rel = rest.find('\n\n')
            end = start + end_rel if end_rel != -1 else len(text)
            result[sec] = text[start:end].strip()
            break  # Don't process any further sections after this
        else:
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            result[sec] = text[start:end].strip()

    # Fill missing
    for sec in sections:
        result.setdefault(sec, "")

    return result


def detect_client_issues_with_recommendations(email_text: str, client):
    prompt = (
        "You are an assistant reviewing emails sent by clients. Your task is to identify whether the client is raising one or more of the following issues:\n"
        "- budget: mentions of unexpected charges, pricing concerns, or cost overruns.\n"
        "- scope: confusion about what is included, feature expectations, or change requests.\n"
        "- schedule: questions about deadlines, delays, or late deliverables.\n"
        "- resources: mentions of unavailable support, missing access, or staff dependencies.\n"
        "- communication: complaints about lack of updates, slow replies, or confusion.\n"
        "- quality: problems with usability, bugs, errors, or performance.\n\n"
        "If the email is purely positive or contains no issues, return an empty list.\n\n"
        "Respond in this format:\n"
        "{\n"
        "  \"issues\": [\"issue1\", \"issue2\"],\n"
        "  \"recommendations\": [\"suggestion1\", \"suggestion2\"]\n"
        "}\n\n"
        f"Email:\n{email_text}"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200
        )
        response_text = completion.choices[0].message.content.strip()
        parsed = ast.literal_eval(response_text)

        detected_issues = parsed.get("issues", [])
        recommendations = parsed.get("recommendations", [])

        return {
            "issues": {
                issue: issue in detected_issues for issue in [
                    "budget", "scope", "schedule", "resources", "communication", "quality"
                ]
            },
            "recommendations": recommendations
        }

    except Exception as e:
        print("Parsing failed:", e)
        return {
            "issues": {
                "budget": False,
                "scope": False,
                "schedule": False,
                "resources": False,
                "communication": False,
                "quality": False
            },
            "recommendations": []
        }
    

    

    
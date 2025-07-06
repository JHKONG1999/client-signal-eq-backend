from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.model_functions import router as llm_router
from mangum import Mangum

from routes import (
    auth_routes,
    user_routes,
    client_routes,
    message_routes,
    organization_routes,
    question_routes,
    outlook_routes
)

# Initialize FastAPI
app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React frontend connect to GitHub
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello from Lambda!"}

# Register routes
app.include_router(auth_router)
app.include_router(llm_router)
app.include_router(auth_routes.router, tags=["Auth"])
app.include_router(user_routes.router, tags=["Users"])
app.include_router(client_routes.router, tags=["Clients"])
app.include_router(message_routes.router, tags=["Messages"])
app.include_router(organization_routes.router, tags=["Organizations"])
app.include_router(question_routes.router, tags=["Questionnaire"])
app.include_router(outlook_routes.router, tags=["Outlook/Emails"])

#handler for aws
handler = Mangum(app)

    
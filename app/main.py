from fastapi import FastAPI
from app.routers.chatbot import router as chatbot_router

app = FastAPI(title="AI Course Chatbot")

app.include_router(chatbot_router, prefix="/api")

@app.get("/")
def health():
    return {"status": "Chatbot Running"}

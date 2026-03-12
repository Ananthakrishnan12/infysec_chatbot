from fastapi import FastAPI
from app.routers.chatbot import router as chatbot_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="AI Course Chatbot")

app.include_router(chatbot_router, prefix="/api")
# ✅ CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def health():
    return {"status": "Chatbot Running"}

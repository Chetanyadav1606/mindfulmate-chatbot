from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone

# Load environment variables first
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import emergentintegrations after loading env vars
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    LLM_AVAILABLE = True
except ImportError:
    print("emergentintegrations not available - using mock responses")
    LLM_AVAILABLE = False
    LlmChat = None
    UserMessage = None

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    sender: str  # "user" or "assistant"
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(default="anonymous")  # For now, using anonymous
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    title: str = "Mental Wellness Chat"

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    timestamp: datetime

# Mental wellness system message
WELLNESS_SYSTEM_MESSAGE = """You are MindfulMate, a compassionate AI companion designed to support youth mental wellness. Your role is to:

1. Provide empathetic, non-judgmental responses
2. Ask thoughtful check-in questions about emotions and well-being
3. Suggest breathing exercises, mindfulness techniques, and grounding methods
4. Encourage healthy habits and self-reflection
5. Offer gentle affirmations and motivational support

Important guidelines:
- Never provide clinical diagnosis or medical advice
- Always encourage professional help for serious concerns
- Use warm, supportive language appropriate for youth
- Ask open-ended questions to encourage sharing
- Suggest practical wellness activities

Focus on these areas:
- Emotional check-ins and mood tracking
- Stress and anxiety management techniques
- Daily wellness habits (sleep, hydration, exercise)
- Self-reflection and gratitude practices  
- Encouragement and positive affirmations
- Crisis awareness (redirect to professional help when needed)

Be conversational, caring, and remember you're talking to young people who need support and understanding."""

# Original routes
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Chat routes
@api_router.post("/chat", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    try:
        # Get or create session
        session_id = request.session_id
        if not session_id:
            # Create new session
            session = ChatSession()
            session_id = session.id
            await db.chat_sessions.insert_one(session.dict())
        else:
            # Update existing session timestamp
            await db.chat_sessions.update_one(
                {"id": session_id},
                {"$set": {"updated_at": datetime.now(timezone.utc)}}
            )

        # Save user message to database
        user_message_obj = ChatMessage(
            session_id=session_id,
            sender="user",
            message=request.message
        )
        await db.chat_messages.insert_one(user_message_obj.dict())

        # Get chat history for context
        chat_history = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(50)  # Last 50 messages

        # Initialize LLM chat
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")

        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=WELLNESS_SYSTEM_MESSAGE
        ).with_model("gemini", "gemini-2.0-flash")

        # Build conversation context (simplified for now)
        user_message = UserMessage(text=request.message)
        
        # Get AI response
        ai_response = await chat.send_message(user_message)

        # Save AI response to database
        ai_message_obj = ChatMessage(
            session_id=session_id,
            sender="assistant",
            message=ai_response,
            timestamp=datetime.now(timezone.utc)
        )
        await db.chat_messages.insert_one(ai_message_obj.dict())

        return ChatResponse(
            message=ai_response,
            session_id=session_id,
            timestamp=ai_message_obj.timestamp
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(100)
        
        return [ChatMessage(**msg) for msg in messages]
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

@api_router.get("/chat/sessions")
async def get_chat_sessions():
    try:
        sessions = await db.chat_sessions.find().sort("updated_at", -1).to_list(20)
        return [ChatSession(**session) for session in sessions]
    except Exception as e:
        logger.error(f"Sessions retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat sessions")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
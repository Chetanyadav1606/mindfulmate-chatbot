# server.py
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid, logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI setup ---
app = FastAPI()
api_router = APIRouter(prefix="/api")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request & Response Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    timestamp: datetime

# --- Rule-based Responses for common situations ---
RULE_RESPONSES = {
    "stress": "I understand that stress can be overwhelming. Let's try a short breathing exercise together. 🌬️",
    "breathing": "Sure! Inhale slowly for 4 seconds, hold for 4, exhale for 6. Repeat a few times and feel calmer. 🌿",
    "sad": "I'm here for you. Talking about your feelings can help. Would you like a mindfulness tip?",
    "happy": "That's wonderful! Keep enjoying the positive moments! 🌞",
    "anxious": "Feeling anxious is normal. Let's try grounding exercises to calm down. 🌱",
    "tired": "Rest is important. Take a short break or do a relaxation exercise. 🛌",
}

def rule_based_response(text: str) -> str:
    text_lower = text.lower()
    for key, response in RULE_RESPONSES.items():
        if key in text_lower:
            return response
    return "Thank you for sharing. How are you feeling right now? 🌟"

# --- Load small instruction-following model ---
MODEL_NAME = "tiiuae/falcon-7b-instruct"  # Instruction-tuned small Falcon
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
device = torch.device("cpu")  # CPU-only
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map=None,
    torch_dtype=torch.float32,
    low_cpu_mem_usage=True
)

def generate_ai_response(user_text: str) -> str:
    try:
        # First try rule-based response
        for key in RULE_RESPONSES:
            if key in user_text.lower():
                return rule_based_response(user_text)

        # Tokenize and generate
        inputs = tokenizer(user_text + tokenizer.eos_token, return_tensors="pt").to(device)
        outputs = model.generate(
            inputs["input_ids"],
            max_length=150,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        if not response.strip():
            return rule_based_response(user_text)
        return response
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return rule_based_response(user_text)

# --- Chat endpoint ---
@api_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    ai_text = generate_ai_response(request.message)
    return ChatResponse(
        message=ai_text,
        session_id=session_id,
        timestamp=datetime.now(timezone.utc)
    )

# --- Include router ---
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

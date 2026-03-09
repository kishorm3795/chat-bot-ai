"""
FastAPI Backend for AI Student Chatbot
Handles RAG-powered chat, auto-reply generation, settings, platform management
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.ai_engine import AIEngine
from backend.database import Database
from backend.rag_pipeline import RAGPipeline
from backend.whatsapp_integration import WhatsAppIntegration

# Load .env
from dotenv import load_dotenv
load_dotenv()

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Student Chatbot",
    description="AI assistant for students with RAG-powered knowledge base",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize services
ai_engine = AIEngine()
db = Database()
rag_pipeline = None
whatsapp = None

def get_rag_pipeline():
    """Lazy initialization of RAG pipeline"""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline(
            knowledge_base_path=os.path.join(BASE_DIR, "knowledge_base")
        )
    return rag_pipeline

# ─── Request / Response Models ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[str] = []
    confidence: float = 0.8
    needs_human: bool = False

class AutoReplyRequest(BaseModel):
    incoming_message: str
    platform: str = "whatsapp"
    sender_name: Optional[str] = "Friend"

class SettingsRequest(BaseModel):
    user_name: Optional[str] = None
    tone: Optional[str] = None
    is_busy: Optional[bool] = None
    custom_away_message: Optional[str] = None

class MarkSentRequest(BaseModel):
    reply_id: int

class FeedbackRequest(BaseModel):
    message: str
    rating: int  # 1-5
    session_id: Optional[str] = None

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the main dashboard HTML at root"""
    widget_path = os.path.join(BASE_DIR, "frontend", "index.html")
    if os.path.exists(widget_path):
        return FileResponse(widget_path)
    # Fallback to chat widget
    widget_path = os.path.join(BASE_DIR, "frontend", "chat-widget.html")
    return FileResponse(widget_path)

@app.get("/widget")
@app.get("/dashboard")
async def get_dashboard():
    """Serve the main dashboard HTML"""
    widget_path = os.path.join(BASE_DIR, "frontend", "index.html")
    if os.path.exists(widget_path):
        return FileResponse(widget_path)
    # Fallback to old widget
    widget_path = os.path.join(BASE_DIR, "frontend", "chat-widget.html")
    return FileResponse(widget_path)

@app.get("/health")
async def health_check():
    wa = get_whatsapp()
    return {
        "status": "healthy",
        "ai_mode": "gemini" if ai_engine.is_configured() else "demo",
        "rag_available": get_rag_pipeline() is not None,
        "whatsapp_configured": wa.is_configured(),
        "timestamp": datetime.now().isoformat()
    }

# ─── Chat (RAG-Powered Student Assistant) ──────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG-powered chat endpoint for the student assistant.
    Uses knowledge base to provide contextual answers.
    """
    session_id = request.session_id or f"session_{datetime.now().timestamp()}"
    
    try:
        # Get RAG pipeline
        rag = get_rag_pipeline()
        
        # Get conversation history for context
        history = db.get_conversation_history(session_id)
        
        # Process through RAG pipeline
        result = rag.query(request.message, conversation_history=history)
        
        # Save to conversation history
        db.save_conversation_message(
            session_id=session_id,
            role="user",
            content=request.message
        )
        db.save_conversation_message(
            session_id=session_id,
            role="assistant",
            content=result["response"]
        )
        
        # Determine if needs human escalation
        needs_human = result.get("confidence", 0.8) < 0.6
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            sources=result.get("sources", []),
            confidence=result.get("confidence", 0.8),
            needs_human=needs_human
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ─── Auto Reply ───────────────────────────────────────────────────────────────

@app.post("/auto-reply")
async def generate_auto_reply(request: AutoReplyRequest):
    """Generate an AI reply for an incoming message"""
    try:
        settings = db.get_settings()

        result = ai_engine.generate_reply(
            incoming_message=request.incoming_message,
            platform=request.platform,
            settings=settings
        )

        # Save to database
        reply_id = db.save_reply(
            platform=request.platform,
            incoming_message=request.incoming_message,
            ai_reply=result["reply"],
            sender_name=request.sender_name or "Friend",
            reply_mode=result.get("mode", "ai")
        )

        return {
            "reply": result["reply"],
            "reply_id": reply_id,
            "platform": request.platform,
            "mode": result.get("mode", "ai"),
            "note": result.get("note", None)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mark-sent")
async def mark_reply_sent(request: MarkSentRequest):
    """Mark a reply as sent"""
    db.mark_sent(request.reply_id)
    return {"status": "success"}

# ─── Settings ───────────────────────────────────────────────────────────────

@app.get("/settings")
async def get_settings():
    """Get current user settings"""
    settings = db.get_settings()
    settings["ai_configured"] = ai_engine.is_configured()
    return settings

@app.post("/settings")
async def update_settings(request: SettingsRequest):
    """Update user personality/tone settings"""
    updates = {}
    if request.user_name is not None:
        updates["user_name"] = request.user_name
    if request.tone is not None:
        if request.tone not in ["casual", "friendly", "professional", "funny", "short"]:
            raise HTTPException(status_code=400, detail="Invalid tone. Choose: casual, friendly, professional, funny, short")
        updates["tone"] = request.tone
    if request.is_busy is not None:
        updates["is_busy"] = 1 if request.is_busy else 0
    if request.custom_away_message is not None:
        updates["custom_away_message"] = request.custom_away_message

    settings = db.update_settings(**updates)
    return settings

@app.post("/toggle-busy")
async def toggle_busy_mode():
    """Toggle busy mode on/off"""
    new_state = db.toggle_busy()
    return {
        "is_busy": new_state,
        "status": "Busy mode ON — AI is replying on your behalf" if new_state else "Busy mode OFF — You're handling your own replies"
    }

# ─── Platforms ───────────────────────────────────────────────────────────────

@app.get("/platforms")
async def get_platforms():
    """Get all platforms with status and reply counts"""
    return db.get_platforms()

@app.post("/platforms/{name}/toggle")
async def toggle_platform(name: str):
    """Toggle a platform active/inactive"""
    new_state = db.toggle_platform(name)
    return {"platform": name, "is_active": new_state}

# ─── History ─────────────────────────────────────────────────────────────────

@app.get("/history")
async def get_history(limit: int = 50, platform: Optional[str] = None):
    """Get reply history"""
    history = db.get_reply_history(limit=limit, platform=platform)
    return {"history": history, "count": len(history)}

@app.get("/history/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 20):
    """Get conversation history for a specific session"""
    history = db.get_conversation_history(session_id, limit=limit)
    return {"session_id": session_id, "history": history, "count": len(history)}

@app.delete("/history/{reply_id}")
async def delete_reply(reply_id: int):
    """Delete a specific reply from history"""
    db.delete_reply(reply_id)
    return {"status": "deleted"}

@app.delete("/history")
async def clear_history():
    """Clear all reply history"""
    db.clear_history()
    return {"status": "cleared"}

# ─── Feedback ─────────────────────────────────────────────────────────────────

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback for a chat interaction"""
    if request.rating < 1 or request.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    feedback_id = db.save_feedback(
        message=request.message,
        rating=request.rating,
        session_id=request.session_id
    )
    
    return {
        "status": "success",
        "feedback_id": feedback_id,
        "message": "Thank you for your feedback!"
    }

# ─── Stats ───────────────────────────────────────────────────────────────────

@app.get("/stats")
async def get_stats():
    """Get usage statistics"""
    stats = db.get_stats()
    
    # Add feedback stats if available
    feedback_stats = db.get_feedback_stats()
    stats["feedback"] = feedback_stats
    
    return stats

# ─── Admin ───────────────────────────────────────────────────────────────────

@app.post("/admin/rebuild-index")
async def rebuild_knowledge_index():
    """Rebuild the knowledge base index"""
    global rag_pipeline
    try:
        rag_pipeline = RAGPipeline(
            knowledge_base_path=os.path.join(BASE_DIR, "knowledge_base")
        )
        return {
            "status": "success",
            "message": "Knowledge base index rebuilt",
            "documents_loaded": len(rag_pipeline.documents) if rag_pipeline else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── WhatsApp (Twilio) Webhook ───────────────────────────────────────────────

def get_whatsapp():
    """Lazy initialization of WhatsApp integration"""
    global whatsapp
    if whatsapp is None:
        whatsapp = WhatsAppIntegration(ai_engine, get_rag_pipeline())
    return whatsapp

@app.get("/whatsapp/status")
async def whatsapp_status():
    """Check WhatsApp/Twilio configuration status"""
    wa = get_whatsapp()
    return {
        "configured": wa.is_configured(),
        "account_sid": bool(wa.account_sid),
        "phone_number": wa.phone_number or "Not set"
    }

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(
    From: str = None,
    Body: str = None,
    MessageSid: str = None
):
    """
    Twilio webhook endpoint for incoming WhatsApp messages.
    Set this URL in your Twilio console: https://your-server.com/whatsapp/webhook
    """
    if not Body or not From:
        return {"error": "Missing message data"}
    
    # Get user's mode (auto_reply or student_assistant)
    settings = db.get_settings()
    mode = "student_assistant" if settings.get("is_busy", False) == 0 else "auto_reply"
    
    # Process message through WhatsApp integration
    wa = get_whatsapp()
    response_text = wa.process_message(From, Body, mode)
    
    # Save to database
    db.save_reply(
        platform="whatsapp",
        incoming_message=Body,
        ai_reply=response_text,
        sender_name=From,
        reply_mode="whatsapp"
    )
    
    # Return TwiML response
    from twilio.twiml import MessagingResponse
    twiml = MessagingResponse()
    twiml.message(response_text)
    return Response(content=str(twiml), media_type="application/xml")

# ─── Startup ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    print("🤖 AI Student Chatbot started!")
    print(f"   Chat mode: RAG-powered student assistant")
    print(f"   Auto-reply: {'Gemini ✅' if ai_engine.is_configured() else 'Demo mode'}")
    
    # Initialize RAG pipeline
    rag = get_rag_pipeline()
    if rag:
        print(f"   Knowledge base: {len(rag.documents)} documents loaded")
    else:
        print("   Knowledge base: Not available")
    
    # Check WhatsApp status
    wa = get_whatsapp()
    if wa.is_configured():
        print(f"   WhatsApp: ✅ Connected ({wa.phone_number})")
    else:
        print("   WhatsApp: ⚠️ Not configured (set TWILIO credentials in .env)")
    
    print("   Dashboard → http://localhost:8000/widget")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


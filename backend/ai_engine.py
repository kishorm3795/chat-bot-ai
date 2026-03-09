"""
AI Engine - Powered by Google Gemini (Free Tier)
Generates personalized auto-replies based on user personality settings
"""

import os
import google.generativeai as genai
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Platform-specific emoji/context
PLATFORM_CONTEXT = {
    "whatsapp": "WhatsApp",
    "instagram": "Instagram DM",
    "telegram": "Telegram",
    "sms": "SMS",
    "other": "a messaging app"
}

TONE_PROMPTS = {
    "casual": "casual, friendly, and relaxed. Use informal language, contractions (I'm, can't, gonna), and feel free to use common emojis. Keep it short and natural.",
    "friendly": "warm, friendly, and upbeat. Be genuine and caring. Use emojis occasionally. Medium length replies.",
    "professional": "professional and polite. Use proper grammar, no slang. Keep it concise and respectful.",
    "funny": "funny, witty, and playful. Add humor and jokes where appropriate. Use emojis freely. Keep it light-hearted.",
    "short": "very brief and to the point. Maximum 1-2 sentences. No long explanations."
}


class AIEngine:
    """AI Engine for generating personalized auto-replies"""

    def __init__(self):
        self.model = None
        self._initialize_gemini()

    def _initialize_gemini(self):
        """Initialize Google Gemini API"""
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key == "your-gemini-api-key-here":
            print("⚠️  No Gemini API key found. Running in demo mode.")
            self.model = None
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            print("✅ Google Gemini AI initialized successfully!")
        except Exception as e:
            print(f"⚠️  Could not initialize Gemini: {e}")
            self.model = None

    def generate_reply(
        self,
        incoming_message: str,
        platform: str,
        settings: Dict,
        conversation_history: list = None
    ) -> Dict:
        """
        Generate a personalized auto-reply for an incoming message.

        Args:
            incoming_message: The message received from the friend
            platform: Platform name (whatsapp, instagram, etc.)
            settings: User's personality/tone settings
            conversation_history: Previous messages in this thread

        Returns:
            Dict with 'reply' and 'mode' keys
        """
        user_name = settings.get("user_name", "the user")
        tone = settings.get("tone", "casual")
        custom_away_msg = settings.get("custom_away_message", "")
        is_busy = settings.get("is_busy", True)

        platform_label = PLATFORM_CONTEXT.get(platform, "a messaging app")
        tone_desc = TONE_PROMPTS.get(tone, TONE_PROMPTS["casual"])

        # Build context string from history
        history_str = ""
        if conversation_history:
            history_str = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-4:]:  # Last 4 messages for context
                role = "Friend" if msg.get("role") == "user" else user_name
                history_str += f"{role}: {msg.get('content', '')}\n"

        # Build the AI prompt
        prompt = f"""You are acting as {user_name}'s personal AI assistant. Your job is to reply to a message they received on {platform_label} while they are busy.

Write a reply that sounds exactly like {user_name} — not like an AI, and definitely not robotic.

Personality/Tone: Be {tone_desc}

{f"Custom note from {user_name} to mention if relevant: {custom_away_msg}" if custom_away_msg else ""}

{history_str}

The incoming message from their friend:
"{incoming_message}"

Write ONLY the reply message text. No quotes around it, no explanation, no "Here's a reply:", just the message itself. Make it sound human and natural."""

        # Use Gemini if available, else use smart demo mode
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                reply = response.text.strip()
                return {"reply": reply, "mode": "ai", "platform": platform}
            except Exception as e:
                print(f"Gemini error: {e}")
                return self._demo_reply(incoming_message, tone, user_name, platform)
        else:
            return self._demo_reply(incoming_message, tone, user_name, platform)

    def _demo_reply(self, message: str, tone: str, user_name: str, platform: str) -> Dict:
        """Generate a smart demo reply when no API key is set"""
        msg_lower = message.lower()

        # Context-aware demo replies
        if any(w in msg_lower for w in ["free", "available", "meet", "hang", "party", "plans"]):
            replies = {
                "casual": "hey! kinda busy rn, can we talk later? 😅",
                "friendly": "Hey! I'm a bit tied up at the moment, but would love to catch up later! 😊",
                "professional": "Hi! I'm currently unavailable but will get back to you shortly.",
                "funny": "Me? Free? Bold assumption 😂 I'll hit you up when I surface!",
                "short": "Busy now, talk later!"
            }
        elif any(w in msg_lower for w in ["how are you", "how r u", "hows it going", "what's up", "wassup", "sup"]):
            replies = {
                "casual": "all good! just super busy atm, will catch up with you soon 🙏",
                "friendly": "Doing well, thanks! Just a bit swamped right now — will reach out soon! 😊",
                "professional": "I'm well, thank you! Busy at the moment, but I'll be in touch.",
                "funny": "surviving on caffeine and chaos 😂 will explain later!",
                "short": "All good, just busy!"
            }
        elif any(w in msg_lower for w in ["urgent", "asap", "emergency", "important", "help"]):
            replies = {
                "casual": "hey saw this! if it's urgent pls call me, otherwise I'll get back to you asap!",
                "friendly": "Hey! Just saw your message. If it's urgent, please call me! I'll be free soon 🙏",
                "professional": "I've seen your message. If this is urgent, please call me directly.",
                "funny": "Code red received! 🚨 If truly urgent, call — otherwise I'll save the world later 😄",
                "short": "Busy — call if urgent!"
            }
        else:
            replies = {
                "casual": "heyyy! busy rn but will reply properly soon 🙏",
                "friendly": "Hey! Got your message — I'm a bit busy right now but I'll reply properly soon! 😊",
                "professional": "Hi! I'm currently unavailable. I'll respond to your message shortly.",
                "funny": "I'm alive, just buried under life stuff 😅 Be back soon!",
                "short": "Busy, will reply soon!"
            }

        reply = replies.get(tone, replies["casual"])
        return {
            "reply": reply,
            "mode": "demo",
            "platform": platform,
            "note": "Demo mode — add your Gemini API key for personalized AI replies"
        }

    def is_configured(self) -> bool:
        """Check if Gemini API is properly configured"""
        return self.model is not None

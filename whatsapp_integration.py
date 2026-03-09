"""
Twilio WhatsApp Integration
Handles incoming messages from WhatsApp and auto-replies using AI
"""

import os
from typing import Dict, Optional
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()


class WhatsAppIntegration:
    """Twilio WhatsApp message handler"""
    
    def __init__(self, ai_engine=None, rag_pipeline=None):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        self.ai_engine = ai_engine
        self.rag_pipeline = rag_pipeline
        self.client = None
        
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                print("✅ Twilio WhatsApp integration initialized!")
            except Exception as e:
                print(f"⚠️ Twilio initialization error: {e}")
    
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured"""
        return bool(self.account_sid and self.auth_token and self.phone_number)
    
    def process_message(self, from_number: str, message_body: str, mode: str = "auto_reply") -> str:
        """
        Process incoming WhatsApp message and generate AI response
        
        Args:
            from_number: Sender's WhatsApp number
            message_body: The message text
            mode: 'auto_reply' (personal bot) or 'student_assistant' (RAG)
        
        Returns:
            Response message to send back
        """
        try:
            if mode == "student_assistant" and self.rag_pipeline:
                # Use RAG pipeline for student assistant
                result = self.rag_pipeline.query(message_body)
                response_text = result.get("response", "Sorry, I couldn't process that.")
            elif self.ai_engine:
                # Use AI engine for personal auto-reply
                settings = {
                    "user_name": os.getenv("USER_NAME", "Me"),
                    "tone": os.getenv("TONE", "casual"),
                    "custom_away_message": os.getenv("CUSTOM_AWAY_MESSAGE", ""),
                    "is_busy": True
                }
                result = self.ai_engine.generate_reply(
                    incoming_message=message_body,
                    platform="whatsapp",
                    settings=settings
                )
                response_text = result.get("reply", "Sorry, I couldn't process that.")
            else:
                response_text = "Sorry, AI is not configured. Please check your API keys."
            
            return response_text
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return "Sorry, something went wrong. Please try again later."
    
    def send_message(self, to_number: str, message_body: str) -> bool:
        """Send a WhatsApp message"""
        if not self.is_configured():
            print("⚠️ Twilio not configured")
            return False
        
        try:
            message = self.client.messages.create(
                from_=self.phone_number,
                body=message_body,
                to=to_number
            )
            print(f"✅ WhatsApp message sent: {message.sid}")
            return True
        except Exception as e:
            print(f"❌ Failed to send WhatsApp message: {e}")
            return False
    
    def generate_twiml_response(self, message_body: str, from_number: str = None, mode: str = "auto_reply") -> str:
        """
        Generate TwiML response for webhook
        
        Returns:
            TwiML XML string
        """
        response_text = self.process_message(from_number, message_body, mode)
        
        twiml = MessagingResponse()
        twiml.message(response_text)
        
        return str(twiml)


def create_webhook_handler(ai_engine, rag_pipeline):
    """Factory function to create webhook handler"""
    whatsapp = WhatsAppIntegration(ai_engine, rag_pipeline)
    
    def handle_webhook(from_number: str, message_body: str, mode: str = "auto_reply") -> str:
        return whatsapp.generate_twiml_response(message_body, from_number, mode)
    
    return handle_webhook, whatsapp


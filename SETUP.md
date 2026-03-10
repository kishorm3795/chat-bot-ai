# WhatsApp Integration Setup Guide

This guide will help you connect your chatbot to WhatsApp using Twilio.

## Prerequisites

1. **Twilio Account** - Sign up at https://www.twilio.com (free trial available)
2. **Twilio Phone Number** - Get a WhatsApp-enabled number
3. **Public Server URL** - Your server must be accessible from the internet (Twilio needs to reach your webhook)

---

## Step 1: Get Twilio Credentials

1. Go to https://console.twilio.com
2. Create a new project or select existing
3. Get your **Account SID** (starts with AC...)
4. Get your **Auth Token** (under Account Info)
5. Get a **WhatsApp Phone Number**:
   - Go to Develop → Phone Numbers → Manage → Buy a Number
   - Search for a number with WhatsApp capability
   - Or use Twilio's sandbox (see below)

---

## Step 2: Use Twilio Sandbox (Easier)

For testing, you can use Twilio's free sandbox:

1. Go to https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
2. Enable the sandbox if not already enabled
3. Note the sandbox phone number: `+14155238886`

---

## Step 3: Configure Your .env File

Create a `.env` file in the project root:

```env
# Twilio Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token-here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# For auto-reply bot (optional)
GEMINI_API_KEY=your-gemini-api-key
USER_NAME=YourName
TONE=casual
```

---

## Step 4: Set Up Webhook URL

### Option A: Using ngrok (for local testing)

1. Install ngrok: https://ngrok.com/download
2. Run: `ngrok http 8000`
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. Configure in Twilio Console:
   - Go to SMS → WhatsApp Sandbox Settings
   - Set "When a message comes in" webhook to:
     ```
     https://your-ngrok-url/whatsapp/webhook
     ```

### Option B: Deploy to Cloud (Production)

1. Deploy this project to a cloud provider (Render, Railway, Heroku, etc.)
2. Get your public URL (e.g., `https://your-app.onrender.com`)
3. Set the webhook in Twilio to:
   ```
   https://your-app.onrender.com/whatsapp/webhook
   ```

---

## Step 5: Test WhatsApp

1. Restart your server:
   ```bash
   python backend/main.py
   ```

2. Check health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```
   Should show `"whatsapp_configured": true`

3. Send a WhatsApp message:
   - If using sandbox: Send `join <sandbox-code>` to `+14155238886`
   - If using your number: Send any message to your WhatsApp number

4. The bot should auto-reply!

---

## How It Works

```
User sends WhatsApp message
         ↓
Twilio receives message
         ↓
Twilio calls your webhook (https://your-server.com/whatsapp/webhook)
         ↓
Your server processes message using AI (Gemini or RAG)
         ↓
Server returns TwiML response
         ↓
Twilio sends reply to user on WhatsApp
```

---

## Troubleshooting

### "WhatsApp not configured"
- Check your `.env` file has correct TWILIO credentials
- Restart the server after updating .env

### "Webhook not reaching"
- Use ngrok to get a public URL for local testing
- Check server logs: `tail -f server.log`

### "Message received but no reply"
- Check if AI is configured (GEMINI_API_KEY)
- Check database for saved messages

---

## Cost

- **Twilio Sandbox**: Free (limited)
- **Production WhatsApp**: ~$0.01-0.05 per message
- **Gemini API**: Free tier available (check Google AI Studio)


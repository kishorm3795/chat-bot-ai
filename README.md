# 🤖 AI Student Chatbot

A 24/7 AI assistant for students that works even when you're not present. This chatbot can be embedded on any website and automatically answers student questions using Retrieval Augmented Generation (RAG).

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00c853)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-orange)

## ✨ Features

- 📚 **Knowledge-Aware Responses** - Answers based on your course materials, notes, and FAQs
- 🔍 **RAG Pipeline** - Uses embeddings and vector search for accurate answers
- 💬 **Embeddable Widget** - Simple HTML/JS widget that works on any website
- 💾 **Conversation History** - Stores chat logs in SQLite database
- 📊 **Confidence Scoring** - Shows confidence level and escalates to human when needed
- 🎯 **Quick Actions** - Pre-defined buttons for common questions
- 📱 **Responsive Design** - Works on desktop and mobile

## 🏗️ System Architecture

```
User (Website Chat Widget)
        │
        ▼
FastAPI Backend
        │
        ▼
RAG Pipeline (LangChain + FAISS)
        │
        ▼
OpenAI API (GPT-4)
        │
        ▼
Knowledge Base (PDFs, Markdown, Text)
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
cd student-ai-chatbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your-api-key-here
```

Get your API key from [OpenAI](https://platform.openai.com/api-keys)

### 3. Run the Server

```bash
# Start the FastAPI server
python -m uvicorn backend.main:app --reload --port 8000
```

### 4. Open the Chat Widget

Open `frontend/chat-widget.html` in your browser, or serve it:

```bash
# Using Python's built-in server
cd frontend
python -m http0
```

Then visit `.server 808http://localhost:8080`

## 📁 Project Structure

```
student-ai-chatbot/
├── backend/
│   ├── main.py          # FastAPI application
│   ├── rag_pipeline.py  # RAG pipeline implementation
│   └── database.py      # SQLite database handler
├── frontend/
│   └── chat-widget.html # Embeddable chat widget
├── knowledge_base/
│   ├── faq.md           # FAQ documents
│   └── courses.md       # Course information
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/chat` | POST | Send a chat message |
| `/history/{session_id}` | GET | Get conversation history |
| `/feedback` | POST | Submit feedback |
| `/stats` | GET | Usage statistics |
| `/admin/rebuild-index` | POST | Rebuild knowledge base index |

## 💬 Chat API Example

```python
import requests

# Send a message
response = requests.post("http://localhost:8000/chat", json={
    "message": "What are the exam dates?",
    "session_id": "user123"
})

print(response.json())
```

Response:
```json
{
    "response": "Midterm exams are scheduled for March 15-17, 2024...",
    "session_id": "user123",
    "sources": ["FAQ document", "Course syllabus"],
    "confidence": 0.92,
    "needs_human": false
}
```

## 📚 Adding Custom Knowledge

Add documents to the `knowledge_base/` folder:

- **PDFs** - Place in `knowledge_base/pdfs/`
- **Markdown** - Place in `knowledge_base/` (root)
- **Text** - Place in `knowledge_base/text/`

The bot will automatically index new documents on restart.

### Supported Formats
- `.pdf` - PDF documents
- `.md` - Markdown files
- `.txt` - Plain text files

## 🎨 Customization

### Change Bot Name
Edit `frontend/chat-widget.html`:
```javascript
const CONFIG = {
    title: 'Your Bot Name',
    // ...
};
```

### Change Primary Color
```css
:root {
    --primary-color: #4F46E5; /* Change this hex value */
}
```

### Embed on Any Website
```html
<script src="https://your-server.com/chat-widget.js"></script>
<script>
    StudentBot.init({
        apiUrl: "https://your-server.com/chat"
    });
</script>
```

## 📊 Features Explained

### Confidence Scoring
- **High (80-100%)** - Bot is confident in the answer
- **Medium (60-79%)** - Answer may need verification
- **Low (<60%)** - Escalates to human support

### Human Escalation
When confidence is below 70%, the bot shows:
> "I'm not confident about this answer. A human support agent will review your question shortly."

### Quick Actions
Pre-defined buttons help students ask common questions:
- 📅 Exam Dates
- 🔑 Password Help
- 📚 Lecture Slides
- 🔍 Binary Search

## 🛠️ Advanced Setup

### Using PostgreSQL (Production)

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Update .env
DATABASE_URL=postgresql://user:password@localhost/chatbot
```

### Using MongoDB

```bash
pip install pymongo

# Update database.py to use MongoDB
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t student-chatbot .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key student-chatbot
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - feel free to use for your portfolio!

## 🙏 Acknowledgments

- [LangChain](https://langchain.readthedocs.io/) - For RAG pipeline
- [FastAPI](https://fastapi.tiangolo.com/) - For the web framework
- [OpenAI](https://openai.com/) - For GPT models

---

⭐ If you found this helpful, please star the repository!


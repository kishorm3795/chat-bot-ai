"""
RAG (Retrieval Augmented Generation) Pipeline
Handles document loading, embeddings, vector search, and LLM generation
"""

import os
import json
from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class RAGPipeline:
    """RAG Pipeline for AI Student Chatbot"""
    
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.embeddings = None
        self.vectorstore = None
        self.documents = []
        self.conversation_history = []
        
        # Initialize OpenAI
        self._initialize_openai()
        
        # Load and process documents
        self._load_documents()
    
    def _initialize_openai(self):
        """Initialize OpenAI API"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your-api-key-here":
            # Use mock embeddings for demo without API key
            self.embeddings = None
            self.llm = None
            return
        
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=api_key
        )
    
    def _load_documents(self):
        """Load documents from knowledge base"""
        if not os.path.exists(self.knowledge_base_path):
            self._create_sample_knowledge_base()
        
        documents = []
        
        # Load PDFs
        pdf_path = os.path.join(self.knowledge_base_path, "pdfs")
        if os.path.exists(pdf_path):
            try:
                for file in os.listdir(pdf_path):
                    if file.endswith(".pdf"):
                        loader = PyPDFLoader(os.path.join(pdf_path, file))
                        documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading PDFs: {e}")
        
        # Load text files
        txt_path = os.path.join(self.knowledge_base_path, "text")
        if os.path.exists(txt_path):
            try:
                loader = TextLoader(txt_path)
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading text files: {e}")
        
        # Load markdown files - manually read .md files
        for file in os.listdir(self.knowledge_base_path):
            if file.endswith(".md"):
                try:
                    file_path = os.path.join(self.knowledge_base_path, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    from langchain_core.documents import Document
                    documents.append(Document(
                        page_content=content,
                        metadata={"source": file}
                    ))
                except Exception as e:
                    print(f"Error loading {file}: {e}")
        
        self.documents = documents
        
        if documents and self.embeddings:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            texts = text_splitter.split_documents(documents)
            
            self.vectorstore = FAISS.from_documents(texts, self.embeddings)
            
            print(f"✅ Loaded {len(texts)} document chunks from knowledge base")
        elif documents:
            print(f"✅ Loaded {len(documents)} documents (vector store not initialized - no API key)")
        else:
            print("⚠️ No documents found in knowledge base")
    
    def _create_sample_knowledge_base(self):
        """Create sample knowledge base for demonstration"""
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        
        faq_content = """# Student FAQ

## Academic Questions

### What are the exam dates?
Midterm exams are scheduled for March 15-17, 2024. Final exams will be held from May 1-8, 2024. Check your student portal for exact timings.

### How can I download lecture slides?
Log into the learning management system (LMS) and navigate to the course page. Click on the "Materials" or "Resources" tab to download all lecture slides.

### Where can I find my assignment deadlines?
All assignment deadlines are listed in the course syllabus. You can also check the assignments page on the LMS for upcoming due dates.

## Technical Questions

### How do I reset my student email password?
Go to the IT helpdesk page and use the password reset tool. You'll need your student ID and registered phone number for verification.

### How do I access the library databases?
Visit the library website and log in with your student credentials. Off-campus access requires VPN connection.

## General Questions

### What are the library opening hours?
The main library is open 24/7 during exam periods. Regular hours are 8 AM - 10 PM on weekdays and 10 AM - 6 PM on weekends.

### How can I contact student support?
Email student-support@university.edu or call 1-800-STUDENT. You can also visit the student center in Building A.
"""
        
        with open(os.path.join(self.knowledge_base_path, "faq.md"), "w") as f:
            f.write(faq_content)
        
        course_content = """# Course Information

## Computer Science 101

### Instructor
Dr. Sarah Johnson

### Course Description
Introduction to fundamental concepts of computer science including algorithms, data structures, and programming basics.

### Topics Covered
- Introduction to Programming
- Variables and Data Types
- Control Structures (if/else, loops)
- Functions and Methods
- Arrays and Lists
- Basic Algorithms (searching, sorting)
- Time Complexity and Big O Notation

### Grading Policy
- Assignments: 30%
- Midterm Exam: 25%
- Final Exam: 35%
- Participation: 10%

## Data Structures

### Topics
- Arrays and Dynamic Arrays
- Linked Lists (Singly, Doubly)
- Stacks and Queues
- Trees (Binary, BST, AVL)
- Graphs (BFS, DFS)
- Hash Tables
- Heaps

### Binary Search
Binary search is an efficient algorithm for finding an item in a sorted array. It works by repeatedly dividing in half the portion of the list that could contain the item until you've narrowed down the possible locations to just one.

Time Complexity: O(log n)
"""
        
        with open(os.path.join(self.knowledge_base_path, "courses.md"), "w") as f:
            f.write(course_content)
        
        print("✅ Created sample knowledge base")
    
    def query(self, question: str, conversation_history: List[Dict] = None) -> Dict:
        """Process a question through the RAG pipeline"""
        
        # If no LLM is available, return demo response
        if not self.llm:
            # Find relevant documents for context
            context = ""
            sources = []
            if self.vectorstore:
                try:
                    docs = self.vectorstore.similarity_search(question, k=3)
                    for doc in docs:
                        context += doc.page_content + "\n"
                        sources.append(doc.page_content[:200] + "...")
                except:
                    pass
            
            # Return a helpful demo response
            demo_responses = {
                "exam": "Midterm exams are scheduled for March 15-17, 2024. Final exams will be held from May 1-8, 2024.",
                "password": "Go to the IT helpdesk page and use the password reset tool. You'll need your student ID.",
                "lecture": "Log into the LMS and navigate to the course page. Click on 'Materials' to download lecture slides.",
                "library": "The main library is open 24/7 during exam periods. Regular hours are 8 AM - 10 PM on weekdays.",
                "binary search": "Binary search is an efficient algorithm for finding an item in a sorted array. Time Complexity: O(log n)",
                "default": f"I found {len(sources)} relevant source(s) in the knowledge base. To get AI-generated responses, please add your OpenAI API key in the .env file."
            }
            
            question_lower = question.lower()
            response = demo_responses.get("default", "")
            for key, value in demo_responses.items():
                if key in question_lower:
                    response = value
                    break
            
            return {
                "response": response,
                "sources": sources,
                "confidence": 0.8 if sources else 0.5
            }
        
        # Format conversation history
        chat_messages = []
        if conversation_history:
            for msg in conversation_history:
                if msg.get("role") == "user":
                    chat_messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    chat_messages.append(AIMessage(content=msg["content"]))
        
        # Retrieve relevant documents
        sources = []
        context = ""
        
        if self.vectorstore:
            try:
                docs = self.vectorstore.similarity_search(question, k=3)
                for doc in docs:
                    context += doc.page_content + "\n\n"
                    sources.append(doc.page_content[:200] + "...")
            except Exception as e:
                print(f"Error in similarity search: {e}")
        
        # Build prompt with context
        if context:
            prompt = f"""Based on the following context, answer the question. If the answer is not in the context, use your general knowledge.

Context:
{context}

Question: {question}

Answer:"""
        else:
            prompt = f"""You are an AI teaching assistant for a university. Your role is to help students with:

1. Academic questions - course materials, assignments, exams
2. Technical support - IT issues, software, access problems
3. General inquiries - campus services, schedules, contacts

Be helpful, friendly, and professional. Keep responses concise but informative.

Question: {question}

Answer:"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            answer = response.content
            
            # Calculate confidence
            confidence = self._calculate_confidence(sources, question)
            
            return {
                "response": answer,
                "sources": sources,
                "confidence": confidence
            }
            
        except Exception as e:
            print(f"Error in LLM query: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "sources": [],
                "confidence": 0.3
            }
    
    def _calculate_confidence(self, sources: List[str], question: str) -> float:
        """Calculate confidence score based on retrieved documents"""
        if not sources:
            return 0.3
        
        # Base confidence on number of sources
        source_confidence = min(len(sources) / 3, 1.0)
        
        return min(source_confidence * 0.8 + 0.2, 1.0)
    
    def add_document(self, file_path: str):
        """Add a new document to the knowledge base"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)
        
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        
        if self.vectorstore:
            self.vectorstore.add_documents(texts)
        else:
            self.vectorstore = FAISS.from_documents(texts, self.embeddings)
        
        return f"Added {len(texts)} chunks to knowledge base"


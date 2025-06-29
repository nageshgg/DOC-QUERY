from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
from typing import List, Optional
import aiofiles
from pydantic import BaseModel
import json
from datetime import datetime

from document_processor import DocumentProcessor
from rag_system import RAGSystem

app = FastAPI(title="Document Query API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store document processor and RAG system
document_processor = None
rag_system = None
conversation_history = []

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    answer: str
    question: str
    timestamp: str

# Create uploads directory if it doesn't exist
UPLOADS_DIR = "uploads"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    model_name: str = Form("gpt2")
):
    """
    Upload a PDF or DOC file for processing
    """
    global document_processor, rag_system
    
    # Validate file type
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Validate model name
    allowed_models = [
        "gpt2",
        "distilgpt2",
        "microsoft/DialoGPT-small"
    ]
    
    if model_name not in allowed_models:
        raise HTTPException(
            status_code=400,
            detail=f"Model not supported. Allowed models: {', '.join(allowed_models)}"
        )
    
    try:
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOADS_DIR, unique_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"File saved: {file_path}")
        print(f"Using model: {model_name}")
        
        # Process document
        print("Processing document...")
        document_processor = DocumentProcessor(file_path)
        chunks = document_processor.process()
        print(f"Document processed into {len(chunks)} chunks")
        
        # Initialize RAG system with selected model
        print("Initializing RAG system...")
        rag_system = RAGSystem(model_name=model_name)
        rag_system.initialize(chunks)
        print("RAG system initialized successfully!")
        
        # Clear previous conversation history
        conversation_history.clear()
        
        print("Upload completed successfully!")
        return JSONResponse({
            "message": "File uploaded and processed successfully",
            "filename": file.filename,
            "chunks_count": len(chunks),
            "model_used": model_name
        })
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        # Clean up file if processing fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Ask a question about the uploaded document
    """
    global rag_system, conversation_history
    
    if rag_system is None:
        raise HTTPException(status_code=400, detail="No document uploaded. Please upload a document first.")
    
    try:
        # Get answer from RAG system
        answer = rag_system.ask_question(request.question)
        
        # Add to conversation history
        conversation_entry = {
            "question": request.question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        }
        conversation_history.append(conversation_entry)
        
        return QuestionResponse(
            question=request.question,
            answer=answer,
            timestamp=conversation_entry["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@app.get("/history")
async def get_history():
    """
    Get conversation history
    """
    return {"history": conversation_history}

@app.get("/models")
async def get_available_models():
    """
    Get list of available models
    """
    models = [
        {
            "name": "gpt2",
            "description": "GPT-2 - Fast and stable, safe for macOS",
            "size": "124M parameters"
        },
        {
            "name": "distilgpt2",
            "description": "DistilGPT-2 - Lightweight and fast, safe for macOS",
            "size": "82M parameters"
        },
        {
            "name": "microsoft/DialoGPT-small",
            "description": "DialoGPT Small - Conversational model, safe for macOS",
            "size": "117M parameters"
        }
    ]
    return {"models": models}

@app.get("/test")
async def test_endpoint():
    """
    Simple test endpoint
    """
    return {"status": "Backend is working!"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "Document Query API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
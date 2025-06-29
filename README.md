# Document Query Application

A full-stack application that allows users to upload PDF/DOC files and ask questions about them using RAG (Retrieval-Augmented Generation) with the SmolLM2-1.7B model.

## Features

- **File Upload**: Upload PDF, DOC, and TXT files through a React frontend
- **Document Processing**: Backend processes and stores documents temporarily
- **RAG Implementation**: Uses HuggingFaceTB/SmolLM2-1.7B model for question answering
- **Chat Interface**: Interactive Q&A interface with conversation history
- **Real-time Responses**: Fast and accurate answers based on document content

## Project Structure

```
Doc Query/
├── frontend/          # React application
├── backend/           # FastAPI server
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## Usage

1. Open your browser and go to `http://localhost:3000`
2. Upload a PDF or DOC file using the file upload interface
3. Wait for the file to be processed
4. Start asking questions about the document content
5. View your conversation history in the chat interface

## API Endpoints

- `POST /upload`: Upload a document file (PDF, DOC, DOCX, TXT)
- `POST /ask`: Ask a question about the uploaded document
- `GET /history`: Get conversation history

## Technologies Used

- **Frontend**: React, Axios, Tailwind CSS
- **Backend**: FastAPI, Python
- **AI Model**: HuggingFaceTB/SmolLM2-1.7B
- **Document Processing**: PyPDF2, python-docx
- **Vector Database**: FAISS (for embeddings)
- **RAG Framework**: LangChain

## License

MIT License # DOC-QUERY

# Setup Guide for Document Query Application

This guide will help you set up and run the Document Query Application on your local machine.

## Prerequisites

Before you begin, make sure you have the following installed:

1. **Python 3.8 or higher**
   ```bash
   python3 --version
   ```

2. **Node.js 14 or higher**
   ```bash
   node --version
   npm --version
   ```

3. **Git** (for cloning the repository)

## Quick Start (Recommended)

The easiest way to get started is using the provided startup script:

```bash
./start.sh
```

This script will:
- Create a Python virtual environment
- Install all dependencies
- Start both backend and frontend servers
- Open the application in your browser

## Manual Setup

If you prefer to set up the application manually, follow these steps:

### 1. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Navigate to backend directory
cd backend

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`

## Testing the Application

1. **Open your browser** and go to `http://localhost:3000`

2. **Upload a document**:
   - Click "Choose File" and select a PDF or DOC file
   - Click "Upload" and wait for processing to complete

3. **Ask questions**:
   - Type your question in the text area
   - Press Enter or click "Ask Question"
   - View the AI-generated answer

4. **View conversation history**:
   - All questions and answers are displayed in the chat interface
   - Timestamps show when each interaction occurred

## Sample Questions to Try

Once you've uploaded a document, try asking these types of questions:

- "What is the main topic of this document?"
- "Can you summarize the key points?"
- "What are the different sections covered?"
- "Explain the concept of [specific term]"
- "What are the challenges mentioned?"
- "What applications are discussed?"

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Kill processes using ports 3000 or 8000
   lsof -ti:3000 | xargs kill -9
   lsof -ti:8000 | xargs kill -9
   ```

2. **Python dependencies not found**:
   ```bash
   # Make sure virtual environment is activated
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Node modules not found**:
   ```bash
   cd frontend
   npm install
   ```

4. **Model download issues**:
   - The first time you run the application, it will download the SmolLM2-1.7B model
   - This may take several minutes depending on your internet connection
   - Make sure you have sufficient disk space (at least 4GB)

### Performance Tips

1. **GPU Acceleration**: If you have a CUDA-compatible GPU, the application will automatically use it for faster inference.

2. **Memory Requirements**: The application requires at least 8GB of RAM for optimal performance.

3. **Document Size**: Large documents (>50MB) may take longer to process. Consider splitting very large documents.

## API Endpoints

The backend provides the following API endpoints:

- `POST /upload` - Upload a document file
- `POST /ask` - Ask a question about the uploaded document
- `GET /history` - Get conversation history
- `GET /health` - Health check endpoint

## File Structure

```
Doc Query/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── document_processor.py # Document processing logic
│   └── rag_system.py        # RAG implementation
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.js           # Main React component
│   │   ├── App.css          # Styles
│   │   └── index.js         # React entry point
│   └── package.json         # Node.js dependencies
├── requirements.txt         # Python dependencies
├── start.sh                # Startup script
├── README.md               # Project overview
└── SETUP.md               # This file
```

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

If you encounter any issues or have questions, please:

1. Check the troubleshooting section above
2. Review the error messages in the terminal
3. Ensure all dependencies are properly installed
4. Verify that both servers are running

For additional help, you can create an issue in the project repository. 
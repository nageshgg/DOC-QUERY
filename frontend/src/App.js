import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [error, setError] = useState('');
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('gpt2');
  const [loadingModels, setLoadingModels] = useState(true);

  // Fetch available models on component mount
  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await axios.get('/models');
      setModels(response.data.models);
      setLoadingModels(false);
    } catch (error) {
      console.error('Error fetching models:', error);
      setLoadingModels(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      if (allowedTypes.includes(selectedFile.type)) {
        setFile(selectedFile);
        setError('');
      } else {
        setError('Please select a PDF, DOC, or TXT file');
        setFile(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_name', selectedModel);

    try {
      console.log('Starting upload with model:', selectedModel);
      const response = await axios.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes timeout for model loading
      });

      console.log('Upload response:', response.data);
      setUploaded(true);
      setConversation([]);
      alert(`File uploaded successfully using ${selectedModel}! You can now ask questions about the document.`);
    } catch (error) {
      console.error('Upload error:', error);
      if (error.code === 'ECONNABORTED') {
        setError('Upload timed out. The model is still loading. Please wait and try again.');
      } else {
        setError(error.response?.data?.detail || 'Error uploading file. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    if (!uploaded) {
      setError('Please upload a document first');
      return;
    }

    setLoading(true);
    setError('');

    const userQuestion = question;
    setQuestion('');

    // Add user question to conversation
    setConversation(prev => [...prev, {
      type: 'user',
      content: userQuestion,
      timestamp: new Date().toISOString()
    }]);

    try {
      const response = await axios.post('/ask', {
        question: userQuestion
      });

      // Add AI response to conversation
      setConversation(prev => [...prev, {
        type: 'ai',
        content: response.data.answer,
        timestamp: response.data.timestamp
      }]);
    } catch (error) {
      setError(error.response?.data?.detail || 'Error getting answer');
      // Remove the user question if there was an error
      setConversation(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAskQuestion();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Document Query Assistant</h1>
        <p>Upload a PDF, DOC, or TXT file and ask questions about it</p>
      </header>

      <main className="App-main">
        {/* File Upload Section */}
        <section className="upload-section">
          <h2>Upload Document</h2>
          
          {/* Model Selection */}
          <div className="model-selection">
            <label htmlFor="model-select">Choose AI Model:</label>
            <select
              id="model-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={uploading || loadingModels}
            >
              {loadingModels ? (
                <option>Loading models...</option>
              ) : (
                models.map((model) => (
                  <option key={model.name} value={model.name}>
                    {model.description} ({model.size})
                  </option>
                ))
              )}
            </select>
            {selectedModel && !loadingModels && (
              <p className="model-info">
                Selected: {models.find(m => m.name === selectedModel)?.description}
              </p>
            )}
          </div>

          <div className="file-upload">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileChange}
              disabled={uploading}
            />
            <button 
              onClick={handleUpload}
              disabled={!file || uploading}
              className="upload-btn"
            >
              {uploading ? 'Processing... (This may take a few minutes)' : 'Upload'}
            </button>
          </div>
          {file && (
            <p className="file-info">Selected: {file.name}</p>
          )}
          {uploaded && (
            <p className="success-message">✓ Document uploaded successfully!</p>
          )}
          {error && (
            <p className="error-message">{error}</p>
          )}
        </section>

        {/* Chat Section */}
        {uploaded && (
          <section className="chat-section">
            <h2>Ask Questions</h2>
            
            {/* Conversation History */}
            <div className="conversation-container">
              {conversation.length === 0 ? (
                <p className="no-messages">No questions asked yet. Start by asking a question about your document!</p>
              ) : (
                conversation.map((message, index) => (
                  <div key={index} className={`message ${message.type}`}>
                    <div className="message-content">
                      {message.content}
                    </div>
                    <div className="message-timestamp">
                      {formatTimestamp(message.timestamp)}
                    </div>
                  </div>
                ))
              )}
              {loading && (
                <div className="message ai">
                  <div className="message-content">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Question Input */}
            <div className="question-input">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question about your document..."
                disabled={loading}
                rows="3"
              />
              <button 
                onClick={handleAskQuestion}
                disabled={!question.trim() || loading}
                className="ask-btn"
              >
                {loading ? 'Thinking...' : 'Ask Question'}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App; 
import re
from typing import List, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class RAGSystem:
    def __init__(self, model_name: str = "gpt2"):
        self.tokenizer = None
        self.model = None
        self.chunks = []
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = model_name
        
        # Model configurations for smaller, safer models
        self.model_configs = {
            "gpt2": {
                "prompt_format": "simple", 
                "max_tokens": 100,
                "temperature": 0.6,
                "top_p": 0.9,
                "repetition_penalty": 1.2
            },
            "distilgpt2": {
                "prompt_format": "simple",
                "max_tokens": 80,
                "temperature": 0.5,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            },
            "microsoft/DialoGPT-small": {
                "prompt_format": "simple",
                "max_tokens": 100,
                "temperature": 0.5,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            }
        }
    
    def initialize(self, chunks: List[str]):
        """
        Initialize the RAG system with document chunks
        """
        self.chunks = chunks
        print("Using simplified text-based search without external models...")
        
        # Only try to load a small model for fallback responses
        if self.model_name in ["gpt2", "distilgpt2", "microsoft/DialoGPT-small"]:
            print(f"Loading {self.model_name} model for fallback responses...")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                
                # Add padding token if not present
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,  # Use float32 for better compatibility
                    low_cpu_mem_usage=False  # Disable low_cpu_mem_usage to avoid issues
                )
                print("Model and tokenizer loaded successfully!")
            except Exception as e:
                print(f"Warning: Could not load model {self.model_name}: {str(e)}")
                print("Fallback to model knowledge will not be available.")
                self.tokenizer = None
                self.model = None
        else:
            print(f"Model {self.model_name} not in safe list. Using text-based search only.")
            self.tokenizer = None
            self.model = None
        
        print("RAG system initialized successfully!")
    
    def _retrieve_relevant_chunks(self, question: str, top_k: int = 3) -> List[str]:
        """
        Retrieve most relevant chunks using keyword matching and simple text similarity
        """
        question_lower = question.lower()
        question_words = [word for word in question_lower.split() if len(word) > 2]
        
        # Score chunks based on keyword matches
        chunk_scores = []
        for i, chunk in enumerate(self.chunks):
            chunk_lower = chunk.lower()
            matches = sum(1 for word in question_words if word in chunk_lower)
            if matches > 0:
                chunk_scores.append((i, chunk, matches))
        
        # Sort by number of matches and take top chunks
        chunk_scores.sort(key=lambda x: x[2], reverse=True)
        relevant_chunks = [chunk for _, chunk, _ in chunk_scores[:top_k]]
        
        return relevant_chunks
    
    def _create_prompt(self, question: str, context_chunks: List[str]) -> str:
        """
        Create a simple prompt for the model
        """
        context = "\n\n".join(context_chunks)
        return f"""Based on the following document content, please answer the question clearly and accurately. Use only the information provided in the document.

Document Content:
{context}

Question: {question}

Answer:"""
    
    def ask_question(self, question: str) -> str:
        """
        Ask a question and get an answer using text-based search
        """
        if not self.chunks:
            raise ValueError("RAG system not initialized. Please upload a document first.")
        
        try:
            # Retrieve relevant chunks
            relevant_chunks = self._retrieve_relevant_chunks(question, top_k=5)
            
            if not relevant_chunks:
                # No relevant chunks found, use model to generate answer if available
                return self._generate_model_response(question, "No relevant information found in the document.")
            
            # Create a comprehensive context from relevant chunks
            context = "\n\n".join(relevant_chunks)
            
            # First try to extract direct answer from document
            direct_answer = self._extract_direct_answer(question, context)
            
            # Check if the direct answer is meaningful
            if direct_answer and len(direct_answer) > 20 and "cannot find" not in direct_answer.lower():
                return direct_answer
            
            # If direct extraction didn't work well and model is available, try the language model
            if self.model is not None and self.tokenizer is not None:
                try:
                    # Create prompt
                    prompt = self._create_prompt(question, relevant_chunks)
                    
                    # Get model configuration
                    config = self.model_configs.get(self.model_name, self.model_configs["gpt2"])
                    
                    # Generate answer with model-specific parameters
                    inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
                    
                    with torch.no_grad():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=config["max_tokens"],
                            temperature=config["temperature"],
                            do_sample=True,
                            top_p=config["top_p"],
                            repetition_penalty=config["repetition_penalty"],
                            pad_token_id=self.tokenizer.eos_token_id,
                            eos_token_id=self.tokenizer.eos_token_id,
                            early_stopping=True,
                            no_repeat_ngram_size=3
                        )
                    
                    # Decode the response
                    response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                    
                    # Extract only the model's response (after the prompt)
                    prompt_tokens = self.tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)
                    if prompt_tokens in response:
                        answer = response[len(prompt_tokens):].strip()
                    else:
                        answer = response.strip()
                    
                    # Clean up the answer
                    answer = answer.strip()
                    
                    # If the model generated a good answer, return it with document context
                    if len(answer) > 10 and answer.lower() not in ['', 'none', 'n/a', 'i cannot find']:
                        return f"[Note: Answer generated using document context and AI model.]\n\n{answer}"
                    
                except Exception as e:
                    print(f"Error in model generation: {str(e)}")
            
            # If both document extraction and model generation failed, use model without document context
            return self._generate_model_response(question, "Document extraction and model generation with context failed.")
            
        except Exception as e:
            print(f"Error in ask_question: {str(e)}")
            # Final fallback: use model without document context
            return self._generate_model_response(question, f"Error occurred: {str(e)}")
    
    def _extract_direct_answer(self, question: str, context: str) -> str:
        """
        Extract a direct answer from the context using text analysis
        """
        question_lower = question.lower()
        context_lower = context.lower()
        
        # Look for specific patterns in the question
        if "what is" in question_lower:
            # Look for definitions
            sentences = context.split('.')
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if "is a" in sentence_lower or "refers to" in sentence_lower or "defined as" in sentence_lower:
                    question_words = [word for word in question_lower.split() if len(word) > 3]
                    if any(word in sentence_lower for word in question_words):
                        # Clean up the sentence
                        clean_sentence = sentence.strip()
                        if clean_sentence.endswith('.'):
                            clean_sentence = clean_sentence[:-1]
                        return f"[Note: Information found in document.]\n\n{clean_sentence}."
        
        elif "what are" in question_lower or "types of" in question_lower or "3 types" in question_lower or "three types" in question_lower:
            # Look for numbered lists
            lines = context.split('\n')
            list_lines = []
            in_list = False
            for line in lines:
                line_stripped = line.strip()
                if re.match(r"^\d+\. ", line_stripped):
                    in_list = True
                    list_lines.append(line_stripped)
                elif in_list and (line_stripped.startswith('- ') or re.match(r"^[a-zA-Z]\. ", line_stripped)):
                    list_lines.append(line_stripped)
                elif in_list and not line_stripped:
                    break  # End of list
                elif in_list:
                    if list_lines:
                        list_lines[-1] += ' ' + line_stripped
            if list_lines:
                return f"[Note: Information found in document.]\n\n" + '\n'.join(list_lines)
        
        # General keyword matching with better sentence selection
        sentences = context.split('.')
        best_sentences = []
        best_score = 0
        for sentence in sentences:
            sentence_lower = sentence.lower()
            question_words = [word for word in question_lower.split() if len(word) > 2]
            matches = sum(1 for word in question_words if word in sentence_lower)
            if matches > 0 and len(sentence.strip()) > 10:
                if matches > best_score:
                    best_score = matches
                    best_sentences = [sentence.strip()]
                elif matches == best_score:
                    best_sentences.append(sentence.strip())
        
        if best_sentences:
            # Clean up and avoid duplication
            answer = '. '.join(best_sentences[:2]) + "."
            # Remove any repetitive phrases
            answer = re.sub(r'\b(\w+)\s+\1\b', r'\1', answer)
            return f"[Note: Information found in document.]\n\n{answer}"
        
        # Fallback: return the most relevant chunk
        chunks = context.split('\n\n')
        for chunk in chunks:
            chunk_lower = chunk.lower()
            question_words = [word for word in question_lower.split() if len(word) > 2]
            matches = sum(1 for word in question_words if word in chunk_lower)
            if matches > 0:
                answer = chunk[:300].strip() + "..." if len(chunk) > 300 else chunk.strip()
                # Clean up the answer
                answer = re.sub(r'\n+', '\n', answer)  # Remove extra newlines
                return f"[Note: Information found in document.]\n\n{answer}"
        
        return "I cannot find a specific answer to your question in the provided document. Please try rephrasing your question or ask about a different aspect of the document."
    
    def _generate_model_response(self, question: str, reason: str) -> str:
        """
        Generate a response using the model's knowledge when document information is not available
        """
        # Check if model and tokenizer are loaded
        if self.model is None or self.tokenizer is None:
            return f"[Note: Information not found in document. Model not available for fallback response.]\n\nI cannot provide additional information about '{question}' as the language model is not loaded. Please try asking about information that might be in the uploaded document."
        
        try:
            # Create a prompt that asks the model to use its own knowledge
            prompt = f"""The following question cannot be answered from the provided document content. Please provide a helpful answer using your general knowledge about the topic.

Question: {question}

Answer:"""
            
            # Generate answer
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.6,
                    do_sample=True,
                    top_p=0.9,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    early_stopping=True,
                    no_repeat_ngram_size=3
                )
            
            # Decode and extract response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            prompt_tokens = self.tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)
            answer = response[len(prompt_tokens):].strip() if prompt_tokens in response else response.strip()
            
            # Clean up the answer
            answer = answer.strip()
            
            # If the model generated a good answer, return it with clear indication
            if len(answer) > 10 and answer.lower() not in ['', 'none', 'n/a', 'i cannot find']:
                return f"[Note: Information not found in document. Using AI model knowledge.]\n\n{answer}"
            else:
                return f"[Note: Information not found in document. Model could not generate a helpful response.]\n\nI cannot provide additional information about '{question}' as it was not found in the document and the AI model could not generate a helpful response."
            
        except Exception as e:
            return f"[Note: Information not found in document. Model error occurred.]\n\nI cannot provide additional information about '{question}' due to a model error: {str(e)}" 
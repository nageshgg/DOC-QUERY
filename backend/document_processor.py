import os
import PyPDF2
from docx import Document
from typing import List
import re

class DocumentProcessor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_extension = os.path.splitext(file_path)[1].lower()
    
    def process(self) -> List[str]:
        """
        Process the document and return text chunks
        """
        if self.file_extension == '.pdf':
            return self._process_pdf()
        elif self.file_extension in ['.doc', '.docx']:
            return self._process_doc()
        elif self.file_extension == '.txt':
            return self._process_txt()
        else:
            raise ValueError(f"Unsupported file type: {self.file_extension}")
    
    def _process_pdf(self) -> List[str]:
        """
        Extract text from PDF and chunk it
        """
        text = ""
        try:
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF file: {str(e)}")
        
        return self._chunk_text(text)
    
    def _process_doc(self) -> List[str]:
        """
        Extract text from DOC/DOCX and chunk it
        """
        text = ""
        try:
            doc = Document(self.file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise Exception(f"Error reading DOC file: {str(e)}")
        
        return self._chunk_text(text)
    
    def _process_txt(self) -> List[str]:
        """
        Extract text from TXT file and chunk it
        """
        text = ""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(self.file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
            except Exception as e:
                raise Exception(f"Error reading TXT file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error reading TXT file: {str(e)}")
        
        return self._chunk_text(text)
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks
        """
        # Clean the text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this is not the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                search_start = max(start + chunk_size - 100, start)
                sentence_end = text.rfind('.', search_start, end)
                if sentence_end > start + chunk_size // 2:  # Only break if we find a reasonable sentence boundary
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks 
import json
import os
from typing import Dict, List

import json_repair
from haystack import component
from pypdf import PdfReader


@component
class QuizParser:
    @component.output_types(quiz=Dict)
    def run(self, replies: List[str]):
        reply = replies[0]

        # even if prompted to respond with JSON only, sometimes the model returns a mix of JSON and text
        first_index = min(reply.find("{"), reply.find("["))
        last_index = max(reply.rfind("}"), reply.rfind("]")) + 1

        json_portion = reply[first_index:last_index]

        try:
            quiz = json.loads(json_portion)
        except json.JSONDecodeError:
            # if the JSON is not well-formed, try to repair it
            quiz = json_repair.loads(json_portion)

        # sometimes the JSON contains a list instead of a dictionary
        if isinstance(quiz, list):
            quiz = quiz[0]

        print(quiz)

        return {"quiz": quiz}

@component
class PDFTextExtractor:
    @component.output_types(text=str, filename=str)
    def run(self, file_path: str):
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            dict: A dictionary containing the extracted text and the filename
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
            
        reader = PdfReader(file_path)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
            
        filename = os.path.basename(file_path)
        
        return {"text": text, "filename": filename}
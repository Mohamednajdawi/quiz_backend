from typing import Any, Dict

from backend.pipelines import (pdf_quiz_generation_pipeline,
                               quiz_generation_pipeline)


def generate_quiz(
    url: str, num_questions: int = 5, difficulty: str = "medium"
) -> Dict[str, Any]:
    return quiz_generation_pipeline.run(
        {
            "link_content_fetcher": {"urls": [url]},
            "prompt_builder": {
                "num_questions": num_questions,
                "difficulty": difficulty,
            },
        }
    )["quiz_parser"]["quiz"]


def generate_quiz_from_pdf(
    pdf_path: str, num_questions: int = 5, difficulty: str = "medium"
) -> Dict[str, Any]:
    """
    Generate a quiz from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        num_questions: Number of questions to generate
        difficulty: Difficulty level of the questions (easy, medium, hard)
        
    Returns:
        dict: A dictionary containing the quiz data
    """
    return pdf_quiz_generation_pipeline.run(
        {
            "pdf_extractor": {"file_path": pdf_path},
            "prompt_builder": {
                "num_questions": num_questions,
                "difficulty": difficulty,
            },
        }
    )["quiz_parser"]["quiz"]

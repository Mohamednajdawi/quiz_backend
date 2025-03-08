import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional
import datetime

from dotenv import load_dotenv

# Load environment variables at startup
load_dotenv()

import requests
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.sqlite_dal import QuizAttempt, QuizQuestion, QuizTopic
from backend.utils import generate_quiz, generate_quiz_from_pdf

app = FastAPI(title="Quiz Maker API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLRequest(BaseModel):
    url: HttpUrl
    num_questions: int = 5  # Default to 5 questions
    difficulty: str = (
        "medium"  # Default to medium difficulty, options: easy, medium, hard
    )


class QuizResponse(BaseModel):
    topic: str
    category: str
    subcategory: str
    questions: List[Dict[str, Any]]


class TopicResponse(BaseModel):
    id: int
    topic: str
    category: str
    subcategory: str
    creation_timestamp: Optional[datetime.datetime] = None


@app.post("/generate-quiz")
async def create_quiz(
    request: URLRequest, db: Session = Depends(get_db)
) -> JSONResponse:
    try:
        # Remove trailing slash if present
        url = str(request.url).rstrip("/")

        # Validate difficulty level
        if request.difficulty not in ["easy", "medium", "hard"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid difficulty level. Choose from: easy, medium, hard",
            )

        quiz = generate_quiz(url, request.num_questions, request.difficulty)

        # Store quiz in database
        quiz_topic = QuizTopic(
            topic=quiz["topic"],
            category=quiz["category"],
            subcategory=quiz["subcategory"],
        )
        db.add(quiz_topic)
        db.flush()  # Get the ID of the newly created topic

        # Add questions
        for q in quiz["questions"]:
            quiz_question = QuizQuestion(
                question=q["question"],
                options=q["options"],
                right_option=q["right_option"],
                topic_id=quiz_topic.id,
            )
            db.add(quiz_question)

        db.commit()
        return JSONResponse(
            content=quiz,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"Content not found at URL: {request.url}"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@app.post("/generate-quiz-from-pdf")
async def create_quiz_from_pdf(
    pdf_file: UploadFile = File(...),
    num_questions: int = Form(5),
    difficulty: str = Form("medium"),
    db: Session = Depends(get_db)
) -> JSONResponse:
    try:
        # Validate difficulty level
        if difficulty not in ["easy", "medium", "hard"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid difficulty level. Choose from: easy, medium, hard",
            )
            
        # Validate file type
        if not pdf_file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are accepted"
            )
            
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Copy the uploaded file to the temporary file
            shutil.copyfileobj(pdf_file.file, temp_file)
            temp_file_path = temp_file.name
            
        try:
            # Generate quiz from the PDF
            quiz = generate_quiz_from_pdf(temp_file_path, num_questions, difficulty)
            
            # Store quiz in database
            quiz_topic = QuizTopic(
                topic=quiz["topic"],
                category=quiz["category"],
                subcategory=quiz["subcategory"],
            )
            db.add(quiz_topic)
            db.flush()  # Get the ID of the newly created topic

            # Add questions
            for q in quiz["questions"]:
                quiz_question = QuizQuestion(
                    question=q["question"],
                    options=q["options"],
                    right_option=q["right_option"],
                    topic_id=quiz_topic.id,
                )
                db.add(quiz_question)

            db.commit()
            return JSONResponse(
                content=quiz,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@app.get("/topics")
async def get_topics(db: Session = Depends(get_db)) -> JSONResponse:
    """Get all quiz topics"""
    topics = db.query(QuizTopic).all()
    return JSONResponse(
        content=[
            {
                "id": topic.id,
                "topic": topic.topic,
                "category": topic.category,
                "subcategory": topic.subcategory,
                "creation_timestamp": topic.creation_timestamp.isoformat() if topic.creation_timestamp else None,
            }
            for topic in topics
        ],
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


@app.get("/quiz/{topic_id}")
async def get_quiz(topic_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    """Get a specific quiz by topic ID"""
    topic = db.query(QuizTopic).filter(QuizTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Quiz topic not found")

    questions = db.query(QuizQuestion).filter(QuizQuestion.topic_id == topic_id).all()
    return JSONResponse(
        content={
            "topic": topic.topic,
            "category": topic.category,
            "subcategory": topic.subcategory,
            "creation_timestamp": topic.creation_timestamp.isoformat() if topic.creation_timestamp else None,
            "questions": [
                {
                    "question": q.question,
                    "options": q.options,
                    "right_option": q.right_option,
                }
                for q in questions
            ],
        },
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


class QuizAttemptRequest(BaseModel):
    topic_id: int


@app.post("/record-quiz-attempt")
async def record_quiz_attempt(request: QuizAttemptRequest, db: Session = Depends(get_db)) -> JSONResponse:
    """Record when a quiz is taken"""
    # Verify the topic exists
    topic = db.query(QuizTopic).filter(QuizTopic.id == request.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Quiz topic not found")
    
    # Record the attempt
    quiz_attempt = QuizAttempt(topic_id=request.topic_id)
    db.add(quiz_attempt)
    db.commit()
    
    return JSONResponse(
        content={"message": "Quiz attempt recorded successfully", "timestamp": quiz_attempt.timestamp.isoformat()},
        status_code=201
    )


@app.get("/quiz-attempts/{topic_id}")
async def get_quiz_attempts(topic_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    """Get all attempts for a specific quiz topic"""
    # Verify the topic exists
    topic = db.query(QuizTopic).filter(QuizTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Quiz topic not found")
    
    # Get all attempts
    attempts = db.query(QuizAttempt).filter(QuizAttempt.topic_id == topic_id).all()
    
    return JSONResponse(
        content={
            "topic": topic.topic,
            "attempts": [attempt.timestamp.isoformat() for attempt in attempts]
        }
    )


@app.get("/categories")
async def get_categories(db: Session = Depends(get_db)) -> JSONResponse:
    """Get all unique categories with their subcategories"""
    categories = {}
    topics = db.query(QuizTopic).all()

    for topic in topics:
        if topic.category not in categories:
            categories[topic.category] = []

        if topic.subcategory not in categories[topic.category]:
            categories[topic.category].append(topic.subcategory)

    return JSONResponse(
        content=categories,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

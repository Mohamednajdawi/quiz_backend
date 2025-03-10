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
from backend.sqlite_dal import QuizAttempt, QuizQuestion, QuizTopic, UserProfile, UserQuizResult, UserQuestionAnswer
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


# Models for user quiz results
class UserProfileCreate(BaseModel):
    firebase_uid: str
    username: Optional[str] = None
    email: Optional[str] = None


class QuestionAnswerSubmit(BaseModel):
    question_id: int
    user_answer: str
    is_correct: bool
    time_taken: Optional[int] = None  # Time in seconds
    confidence_level: Optional[int] = None  # Confidence level from 1-5


class StartQuizRequest(BaseModel):
    firebase_uid: str
    topic_id: int


class QuizResultSubmit(BaseModel):
    firebase_uid: str
    topic_id: int
    score: float
    total_questions: int
    correct_answers: int
    time_taken: Optional[int] = None
    completed: bool = True
    started_at: Optional[datetime.datetime] = None
    answers: List[QuestionAnswerSubmit]
    quiz_context: Optional[str] = None  # Optional notes from the user


class UserQuizHistoryRequest(BaseModel):
    firebase_uid: str


# User management endpoints
@app.post("/user/profile")
async def create_or_update_user_profile(
    request: UserProfileCreate, db: Session = Depends(get_db)
) -> JSONResponse:
    # Check if user already exists
    user = db.query(UserProfile).filter(UserProfile.firebase_uid == request.firebase_uid).first()
    
    if not user:
        # Create new user
        user = UserProfile(
            firebase_uid=request.firebase_uid,
            username=request.username,
            email=request.email
        )
        db.add(user)
    else:
        # Update existing user
        if request.username:
            user.username = request.username
        if request.email:
            user.email = request.email
    
    db.commit()
    
    return JSONResponse(
        content={"status": "success", "user_id": user.id},
        status_code=200
    )


# Quiz session management
@app.post("/quiz/start")
async def start_quiz(
    request: StartQuizRequest, db: Session = Depends(get_db)
) -> JSONResponse:
    # Verify the user exists
    user = db.query(UserProfile).filter(UserProfile.firebase_uid == request.firebase_uid).first()
    if not user:
        # Create a new user profile if it doesn't exist
        user = UserProfile(firebase_uid=request.firebase_uid)
        db.add(user)
        db.commit()
    
    # Verify the topic exists
    topic = db.query(QuizTopic).filter(QuizTopic.id == request.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Quiz topic not found")
    
    # Create a new quiz result entry (in-progress)
    quiz_result = UserQuizResult(
        user_id=user.id,
        topic_id=request.topic_id,
        score=0.0,
        total_questions=len(topic.questions),
        correct_answers=0,
        completed=False,
        started_at=datetime.datetime.utcnow()
    )
    
    db.add(quiz_result)
    db.commit()
    
    return JSONResponse(
        content={
            "status": "success",
            "quiz_result_id": quiz_result.id,
            "topic": topic.topic,
            "total_questions": len(topic.questions)
        },
        status_code=200
    )


@app.post("/quiz/submit")
async def submit_quiz_result(
    request: QuizResultSubmit, db: Session = Depends(get_db)
) -> JSONResponse:
    # Verify the user exists
    user = db.query(UserProfile).filter(UserProfile.firebase_uid == request.firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify the topic exists
    topic = db.query(QuizTopic).filter(QuizTopic.id == request.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Quiz topic not found")
    
    # Update topic's last_attempt_date
    topic.last_attempt_date = datetime.datetime.utcnow()
    
    # Create or update quiz result
    quiz_result = db.query(UserQuizResult).filter(
        UserQuizResult.user_id == user.id,
        UserQuizResult.topic_id == request.topic_id,
        UserQuizResult.completed == False
    ).first()
    
    # Get current datetime for enhanced date tracking
    current_time = datetime.datetime.utcnow()
    day_of_week = current_time.strftime("%A")  # Monday, Tuesday, etc.
    
    # Determine time of day
    hour = current_time.hour
    if 5 <= hour < 12:
        time_of_day = "Morning"
    elif 12 <= hour < 17:
        time_of_day = "Afternoon"
    elif 17 <= hour < 21:
        time_of_day = "Evening"
    else:
        time_of_day = "Night"
    
    # Calculate average time per question
    avg_time_per_question = None
    if request.time_taken and request.total_questions > 0:
        avg_time_per_question = request.time_taken / request.total_questions
    
    # Determine difficulty level based on score
    difficulty_level = None
    score_percentage = request.score
    if score_percentage >= 0.8:
        difficulty_level = "Easy"
    elif score_percentage >= 0.6:
        difficulty_level = "Medium"
    else:
        difficulty_level = "Hard"
    
    # Calculate streak (consecutive correct answers at the end)
    streak = 0
    if request.answers:
        # Sort answers by question order
        sorted_answers = sorted(request.answers, key=lambda x: x.question_id)
        # Count consecutive correct answers from the end
        for answer in reversed(sorted_answers):
            if answer.is_correct:
                streak += 1
            else:
                break
    
    if not quiz_result:
        # Create a new completed quiz result
        quiz_result = UserQuizResult(
            user_id=user.id,
            topic_id=request.topic_id,
            score=request.score,
            total_questions=request.total_questions,
            correct_answers=request.correct_answers,
            time_taken=request.time_taken,
            completed=request.completed,
            started_at=request.started_at if request.started_at else datetime.datetime.utcnow(),
            completed_at=current_time,
            day_of_week=day_of_week,
            time_of_day=time_of_day,
            average_time_per_question=avg_time_per_question,
            difficulty_level=difficulty_level,
            streak=streak,
            quiz_context=request.quiz_context
        )
        db.add(quiz_result)
    else:
        # Update the existing quiz result
        quiz_result.score = request.score
        quiz_result.total_questions = request.total_questions
        quiz_result.correct_answers = request.correct_answers
        quiz_result.time_taken = request.time_taken
        quiz_result.completed = request.completed
        quiz_result.completed_at = current_time
        quiz_result.day_of_week = day_of_week
        quiz_result.time_of_day = time_of_day
        quiz_result.average_time_per_question = avg_time_per_question
        quiz_result.difficulty_level = difficulty_level
        quiz_result.streak = streak
        quiz_result.quiz_context = request.quiz_context
    
    db.commit()
    
    # Record individual question answers
    for answer in request.answers:
        confidence = answer.confidence_level if hasattr(answer, 'confidence_level') else None
        
        question_answer = UserQuestionAnswer(
            quiz_result_id=quiz_result.id,
            question_id=answer.question_id,
            user_answer=answer.user_answer,
            is_correct=answer.is_correct,
            time_taken=answer.time_taken,
            confidence_level=confidence
        )
        db.add(question_answer)
    
    db.commit()
    
    return JSONResponse(
        content={
            "status": "success",
            "quiz_result_id": quiz_result.id,
            "score": quiz_result.score,
            "correct_answers": quiz_result.correct_answers,
            "total_questions": quiz_result.total_questions,
            "difficulty_level": quiz_result.difficulty_level,
            "completed_at": quiz_result.completed_at.isoformat() if quiz_result.completed_at else None,
            "day_of_week": quiz_result.day_of_week,
            "time_of_day": quiz_result.time_of_day
        },
        status_code=200
    )


@app.get("/user/{firebase_uid}/quiz-history")
async def get_user_quiz_history(
    firebase_uid: str, db: Session = Depends(get_db)
) -> JSONResponse:
    # Verify the user exists
    user = db.query(UserProfile).filter(UserProfile.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all completed quiz results for the user
    quiz_results = db.query(UserQuizResult).filter(
        UserQuizResult.user_id == user.id,
        UserQuizResult.completed == True
    ).order_by(UserQuizResult.completed_at.desc()).all()
    
    results = []
    for result in quiz_results:
        topic = db.query(QuizTopic).filter(QuizTopic.id == result.topic_id).first()
        
        results.append({
            "quiz_result_id": result.id,
            "topic_id": result.topic_id,
            "topic_name": topic.topic if topic else "Unknown",
            "category": topic.category if topic else "Unknown",
            "subcategory": topic.subcategory if topic else "Unknown",
            "score": result.score,
            "correct_answers": result.correct_answers,
            "total_questions": result.total_questions,
            "time_taken": result.time_taken,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "day_of_week": result.day_of_week,
            "time_of_day": result.time_of_day,
            "difficulty_level": result.difficulty_level,
            "average_time_per_question": result.average_time_per_question
        })
    
    # Get statistics for the user
    stats = {
        "total_quizzes": len(results),
        "average_score": sum(result["score"] for result in results) / len(results) if results else 0,
        "quizzes_by_day": {},
        "quizzes_by_time": {},
        "quizzes_by_difficulty": {}
    }
    
    # Calculate statistics
    for result in results:
        # Count by day
        day = result.get("day_of_week")
        if day:
            stats["quizzes_by_day"][day] = stats["quizzes_by_day"].get(day, 0) + 1
        
        # Count by time of day
        time = result.get("time_of_day")
        if time:
            stats["quizzes_by_time"][time] = stats["quizzes_by_time"].get(time, 0) + 1
        
        # Count by difficulty
        difficulty = result.get("difficulty_level")
        if difficulty:
            stats["quizzes_by_difficulty"][difficulty] = stats["quizzes_by_difficulty"].get(difficulty, 0) + 1
    
    return JSONResponse(
        content={
            "status": "success",
            "quiz_history": results,
            "statistics": stats
        },
        status_code=200
    )


@app.get("/quiz-result/{result_id}")
async def get_quiz_result_details(
    result_id: int, db: Session = Depends(get_db)
) -> JSONResponse:
    # Get the quiz result
    quiz_result = db.query(UserQuizResult).filter(UserQuizResult.id == result_id).first()
    if not quiz_result:
        raise HTTPException(status_code=404, detail="Quiz result not found")
    
    # Get the topic
    topic = db.query(QuizTopic).filter(QuizTopic.id == quiz_result.topic_id).first()
    
    # Get all question answers
    question_answers = db.query(UserQuestionAnswer).filter(
        UserQuestionAnswer.quiz_result_id == result_id
    ).all()
    
    answers = []
    for qa in question_answers:
        question = db.query(QuizQuestion).filter(QuizQuestion.id == qa.question_id).first()
        
        answers.append({
            "question_id": qa.question_id,
            "question_text": question.question if question else "Unknown",
            "options": question.options if question else [],
            "correct_answer": question.right_option if question else "Unknown",
            "user_answer": qa.user_answer,
            "is_correct": qa.is_correct,
            "time_taken": qa.time_taken,
            "confidence_level": qa.confidence_level
        })
    
    return JSONResponse(
        content={
            "status": "success",
            "quiz_result": {
                "id": quiz_result.id,
                "topic_id": quiz_result.topic_id,
                "topic_name": topic.topic if topic else "Unknown",
                "category": topic.category if topic else "Unknown",
                "subcategory": topic.subcategory if topic else "Unknown",
                "score": quiz_result.score,
                "correct_answers": quiz_result.correct_answers,
                "total_questions": quiz_result.total_questions,
                "time_taken": quiz_result.time_taken,
                "started_at": quiz_result.started_at.isoformat() if quiz_result.started_at else None,
                "completed_at": quiz_result.completed_at.isoformat() if quiz_result.completed_at else None,
                "day_of_week": quiz_result.day_of_week,
                "time_of_day": quiz_result.time_of_day,
                "average_time_per_question": quiz_result.average_time_per_question,
                "difficulty_level": quiz_result.difficulty_level,
                "streak": quiz_result.streak,
                "quiz_context": quiz_result.quiz_context,
                "answers": answers
            }
        },
        status_code=200
    )

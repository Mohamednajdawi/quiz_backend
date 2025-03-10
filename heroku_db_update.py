"""
Script to update the database schema on Heroku.
This script should be run after deploying updates that include database schema changes.
Usage: heroku run python heroku_db_update.py --app quiz-maker-api
"""

import os
import sys
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, ForeignKey, Float, Boolean, MetaData, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create metadata with extend_existing=True
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Get the database URL from environment
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Handle Heroku PostgreSQL URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(database_url)
else:
    # Local development fallback
    print("No DATABASE_URL found. Using local SQLite database.")
    db_path = os.path.abspath("quiz_database.db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

# Define all models

class QuizTopic(Base):
    __tablename__ = "quiz_topics"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    creation_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    # Add last attempt date to track when this topic was last attempted
    last_attempt_date = Column(DateTime, nullable=True)

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    options = Column(JSON, nullable=False)
    right_option = Column(String, nullable=False)
    topic_id = Column(Integer, ForeignKey("quiz_topics.id"))

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("quiz_topics.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# User quiz results tables
class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    firebase_uid = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class UserQuizResult(Base):
    __tablename__ = "user_quiz_results"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("quiz_topics.id"), nullable=False)
    score = Column(Float, nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    time_taken = Column(Integer, nullable=True)
    completed = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Enhanced date and time tracking
    day_of_week = Column(String(10), nullable=True)
    time_of_day = Column(String(20), nullable=True)
    
    # Enhanced quiz metrics
    average_time_per_question = Column(Float, nullable=True)
    difficulty_level = Column(String(20), nullable=True)
    streak = Column(Integer, default=0)
    
    # Notes and context
    quiz_context = Column(Text, nullable=True)

class UserQuestionAnswer(Base):
    __tablename__ = "user_question_answers"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    quiz_result_id = Column(Integer, ForeignKey("user_quiz_results.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    user_answer = Column(String, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    time_taken = Column(Integer, nullable=True)
    
    # Add confidence rating
    confidence_level = Column(Integer, nullable=True)

def main():
    """Create or update the database tables."""
    print("Creating/updating database tables...")
    Base.metadata.create_all(engine)
    print("Database schema updated successfully!")

if __name__ == "__main__":
    main() 
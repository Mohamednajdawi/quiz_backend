import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Float, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class QuizTopic(Base):
    __tablename__ = "quiz_topics"

    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    creation_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    questions = relationship("QuizQuestion", back_populates="topic")
    attempts = relationship("QuizAttempt", back_populates="topic")
    user_results = relationship("UserQuizResult", back_populates="topic")
    
    # Add last attempt date to track when this topic was last attempted
    last_attempt_date = Column(DateTime, nullable=True)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    options = Column(JSON, nullable=False)  # Store options as JSON
    right_option = Column(String, nullable=False)
    topic_id = Column(Integer, ForeignKey("quiz_topics.id"))

    topic = relationship("QuizTopic", back_populates="questions")
    user_answers = relationship("UserQuestionAnswer", back_populates="question")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("quiz_topics.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    topic = relationship("QuizTopic", back_populates="attempts")


# New models for user quiz results

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    firebase_uid = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    quiz_results = relationship("UserQuizResult", back_populates="user")


class UserQuizResult(Base):
    __tablename__ = "user_quiz_results"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("quiz_topics.id"), nullable=False)
    score = Column(Float, nullable=False)  # Percentage or points
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    time_taken = Column(Integer, nullable=True)  # in seconds
    completed = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Enhanced date and time tracking
    day_of_week = Column(String(10), nullable=True)  # Store day of week (Monday, Tuesday, etc.)
    time_of_day = Column(String(20), nullable=True)  # Morning, Afternoon, Evening, Night
    
    # Enhanced quiz metrics
    average_time_per_question = Column(Float, nullable=True)  # Average time per question in seconds
    difficulty_level = Column(String(20), nullable=True)  # Easy, Medium, Hard (based on performance)
    streak = Column(Integer, default=0)  # How many correct answers in a row
    
    # Notes and context
    quiz_context = Column(Text, nullable=True)  # User can add context notes about this attempt
    
    user = relationship("UserProfile", back_populates="quiz_results")
    topic = relationship("QuizTopic", back_populates="user_results")
    question_answers = relationship("UserQuestionAnswer", back_populates="quiz_result")


class UserQuestionAnswer(Base):
    __tablename__ = "user_question_answers"

    id = Column(Integer, primary_key=True)
    quiz_result_id = Column(Integer, ForeignKey("user_quiz_results.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    user_answer = Column(String, nullable=True)  # The option the user selected
    is_correct = Column(Boolean, nullable=False)
    time_taken = Column(Integer, nullable=True)  # Time taken for this specific question in seconds
    
    # Add confidence rating
    confidence_level = Column(Integer, nullable=True)  # User's confidence rating (1-5) for this answer
    
    quiz_result = relationship("UserQuizResult", back_populates="question_answers")
    question = relationship("QuizQuestion", back_populates="user_answers")

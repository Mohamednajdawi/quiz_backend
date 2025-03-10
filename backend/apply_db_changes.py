import os
import sys
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, ForeignKey, Float, Boolean, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Add the parent directory to the Python path so we can import from the 'backend' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    # Try importing using the standard module path first
    from backend.sqlite_dal import Base as ImportedBase
    Base = ImportedBase
except ModuleNotFoundError:
    # If that fails, create the Base class here
    Base = declarative_base()

# Create a metadata object with extend_existing=True
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Use environment variable for database URL if available, otherwise use default path
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Handle Heroku PostgreSQL URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(database_url)
else:
    # Get the absolute path to the database file
    db_path = os.path.abspath("quiz_database.db")
    # Create SQLite engine with absolute path
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

# Define tables here
class QuizTopic(Base):
    __tablename__ = "quiz_topics"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    creation_timestamp = Column(DateTime, default=datetime.datetime.utcnow)

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

# New tables for user quiz results
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

class UserQuestionAnswer(Base):
    __tablename__ = "user_question_answers"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    quiz_result_id = Column(Integer, ForeignKey("user_quiz_results.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    user_answer = Column(String, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    time_taken = Column(Integer, nullable=True)

# Create tables and connect to database
def main():
    Base.metadata.create_all(engine)
    print("Database schema updated successfully!")

if __name__ == "__main__":
    main() 
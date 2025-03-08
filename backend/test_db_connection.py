import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlite_dal import Base, QuizTopic

# Get the absolute path to the database file
db_path = os.path.abspath("../quiz_database.db")
print(f"Database path: {db_path}")

# Create SQLite engine with absolute path
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

# Create all tables
Base.metadata.create_all(engine)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test writing to the database
db = SessionLocal()
try:
    # Create a test topic
    test_topic = QuizTopic(topic="Test Topic")
    db.add(test_topic)
    db.commit()
    print("Successfully wrote to the database!")
    
    # Verify it was written
    topics = db.query(QuizTopic).all()
    print(f"Topics in database: {[topic.topic for topic in topics]}")
except Exception as e:
    print(f"Error writing to database: {e}")
finally:
    db.close() 
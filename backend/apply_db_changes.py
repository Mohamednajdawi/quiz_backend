import os

from sqlalchemy import create_engine
from backend.sqlite_dal import Base
import sqlite3
import datetime

# Create engine
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///quiz_database.db")
engine = create_engine(DATABASE_URL)

def main():
    # Create all tables
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    print("Database updated successfully!")

    # Get the absolute path to the database file
    db_path = os.path.abspath("quiz_database.db")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(quiz_topics)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "creation_timestamp" not in columns:
            # Add the creation_timestamp column with current time as default for existing records
            cursor.execute("ALTER TABLE quiz_topics ADD COLUMN creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("Added creation_timestamp column to quiz_topics table")
        else:
            print("creation_timestamp column already exists")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 
import os
import sys
from sqlalchemy import create_engine, text

def main():
    """Add last_attempt_date column to the quiz_topics table."""
    # Get the database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Handle Heroku PostgreSQL URL format
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        engine = create_engine(database_url)
    else:
        print("No DATABASE_URL found. Using local SQLite database.")
        db_path = os.path.abspath("quiz_database.db")
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    
    # Connect to the database
    with engine.connect() as connection:
        # Check if the column exists first to avoid errors
        check_sql = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'quiz_topics' 
            AND column_name = 'last_attempt_date';
        """)
        result = connection.execute(check_sql)
        if result.rowcount == 0:
            # Column doesn't exist, so add it
            print("Adding last_attempt_date column to quiz_topics table...")
            # Create the column - make it nullable since existing rows won't have a value
            alter_sql = text("""
                ALTER TABLE quiz_topics 
                ADD COLUMN last_attempt_date TIMESTAMP;
            """)
            connection.execute(alter_sql)
            connection.commit()
            print("Column added successfully!")
        else:
            print("last_attempt_date column already exists in quiz_topics table.")

if __name__ == "__main__":
    main() 
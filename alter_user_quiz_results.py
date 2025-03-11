import os
import sys
from sqlalchemy import create_engine, text

def main():
    """Add missing columns to user_quiz_results table."""
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
        # Define the columns we need to add
        columns_to_add = [
            {"name": "day_of_week", "type": "VARCHAR(10)"},
            {"name": "time_of_day", "type": "VARCHAR(20)"},
            {"name": "average_time_per_question", "type": "FLOAT"},
            {"name": "difficulty_level", "type": "VARCHAR(20)"},
            {"name": "streak", "type": "INTEGER"},
            {"name": "quiz_context", "type": "TEXT"}
        ]
        
        # Check each column and add if it doesn't exist
        for column in columns_to_add:
            column_name = column["name"]
            column_type = column["type"]
            
            # Check if column exists
            check_sql = text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_quiz_results' 
                AND column_name = '{column_name}';
            """)
            
            result = connection.execute(check_sql)
            if result.rowcount == 0:
                # Column doesn't exist, so add it
                print(f"Adding {column_name} column to user_quiz_results table...")
                alter_sql = text(f"""
                    ALTER TABLE user_quiz_results 
                    ADD COLUMN {column_name} {column_type};
                """)
                connection.execute(alter_sql)
                connection.commit()
                print(f"Column {column_name} added successfully!")
            else:
                print(f"Column {column_name} already exists in user_quiz_results table.")
        
        print("Database schema update completed!")

if __name__ == "__main__":
    main() 
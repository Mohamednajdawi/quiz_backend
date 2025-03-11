import os
import sys
from sqlalchemy import create_engine, text, inspect

def main():
    """Add missing columns to user_quiz_results table and diagnose issues."""
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
        # First, check the existing tables and structure
        print("\n=== DATABASE DIAGNOSTIC INFO ===")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
        # Check user_quiz_results table
        if 'user_quiz_results' in tables:
            print("\n=== USER_QUIZ_RESULTS TABLE ===")
            columns = inspector.get_columns('user_quiz_results')
            print("Columns:")
            for column in columns:
                print(f"  - {column['name']} ({column['type']})")
            
            # Check if there's any data in the table
            try:
                count_query = text("SELECT COUNT(*) FROM user_quiz_results")
                result = connection.execute(count_query)
                count = result.scalar()
                print(f"\nTotal quiz results: {count}")
                
                if count > 0:
                    # Check most recent entries
                    recent_query = text("""
                        SELECT * FROM user_quiz_results 
                        ORDER BY id DESC 
                        LIMIT 3
                    """)
                    result = connection.execute(recent_query)
                    rows = result.fetchall()
                    print("\nMost recent quiz results:")
                    for row in rows:
                        print(f"  - ID: {row.id}, User ID: {row.user_id}, Topic ID: {row.topic_id}, Score: {row.score}")
                        
                    # Check users
                    user_query = text("""
                        SELECT DISTINCT user_id 
                        FROM user_quiz_results
                        LIMIT 10
                    """)
                    result = connection.execute(user_query)
                    users = result.fetchall()
                    print("\nUsers with quiz results:")
                    for user in users:
                        print(f"  - User ID: {user.user_id}")
            except Exception as e:
                print(f"\nError querying data: {e}")
        else:
            print("\nWARNING: user_quiz_results table not found!")
        
        # Now continue with adding the columns
        print("\n=== ADDING MISSING COLUMNS ===")
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
        
        # Check for Firebase users
        print("\n=== CHECKING FIREBASE USERS ===")
        if 'users' in tables:
            columns = inspector.get_columns('users')
            print("Users table columns:")
            for column in columns:
                print(f"  - {column['name']} ({column['type']})")
                
            # Count users
            try:
                count_query = text("SELECT COUNT(*) FROM users")
                result = connection.execute(count_query)
                count = result.scalar()
                print(f"\nTotal users: {count}")
                
                if count > 0:
                    # List some users
                    users_query = text("""
                        SELECT * FROM users
                        LIMIT 5
                    """)
                    result = connection.execute(users_query)
                    rows = result.fetchall()
                    print("\nSample users:")
                    for row in rows:
                        try:
                            print(f"  - Firebase UID: {row.firebase_uid}, Username: {row.username if hasattr(row, 'username') else 'N/A'}")
                        except:
                            print(f"  - User info: {row}")
            except Exception as e:
                print(f"\nError querying users: {e}")
        else:
            print("Users table not found.")
            
        print("\nDatabase schema update completed!")

if __name__ == "__main__":
    main() 
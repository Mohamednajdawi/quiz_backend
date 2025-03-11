import os
import sys
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, Boolean, DateTime

def main():
    """Fix the authentication mapping by creating a users table that maps Firebase UIDs."""
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
        # First, check if we already have a users table
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'users' not in tables:
            print("Creating 'users' table for Firebase authentication mapping...")
            
            # Create users table
            create_users_table = text("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
                    username VARCHAR(100),
                    email VARCHAR(100),
                    photo_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                );
            """)
            
            connection.execute(create_users_table)
            connection.commit()
            print("'users' table created successfully!")
        else:
            print("'users' table already exists.")
            
            # Check if firebase_uid column exists
            columns = inspector.get_columns('users')
            column_names = [column['name'] for column in columns]
            
            if 'firebase_uid' not in column_names:
                print("Adding 'firebase_uid' column to 'users' table...")
                add_firebase_uid = text("""
                    ALTER TABLE users
                    ADD COLUMN firebase_uid VARCHAR(128) UNIQUE;
                """)
                connection.execute(add_firebase_uid)
                connection.commit()
                print("Added 'firebase_uid' column successfully!")
        
        # Now, modify the user_quiz_results table to accept Firebase UIDs
        if 'user_quiz_results' in tables:
            print("\nChecking user_quiz_results table for Firebase compatibility...")
            
            # Check if user_quiz_results has a firebase_uid column
            columns = inspector.get_columns('user_quiz_results')
            column_names = [column['name'] for column in columns]
            
            # Add a firebase_uid column if it doesn't exist
            if 'firebase_uid' not in column_names:
                print("Adding 'firebase_uid' column to user_quiz_results table...")
                add_firebase_uid = text("""
                    ALTER TABLE user_quiz_results
                    ADD COLUMN firebase_uid VARCHAR(128);
                """)
                connection.execute(add_firebase_uid)
                connection.commit()
                
                # Now create an index on firebase_uid for better performance
                create_index = text("""
                    CREATE INDEX idx_user_quiz_results_firebase_uid
                    ON user_quiz_results (firebase_uid);
                """)
                connection.execute(create_index)
                connection.commit()
                print("Added 'firebase_uid' column and index successfully!")
                
                # Add a trigger to automatically fill firebase_uid from users table
                create_trigger = text("""
                    CREATE OR REPLACE FUNCTION update_firebase_uid()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.firebase_uid = (SELECT firebase_uid FROM users WHERE id = NEW.user_id);
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                    
                    DROP TRIGGER IF EXISTS update_firebase_uid_trigger ON user_quiz_results;
                    
                    CREATE TRIGGER update_firebase_uid_trigger
                    BEFORE INSERT OR UPDATE ON user_quiz_results
                    FOR EACH ROW
                    EXECUTE FUNCTION update_firebase_uid();
                """)
                
                try:
                    connection.execute(create_trigger)
                    connection.commit()
                    print("Created trigger to automatically update firebase_uid!")
                except Exception as e:
                    print(f"Error creating trigger: {e}")
                    print("Continuing with manual updates...")
            else:
                print("The 'firebase_uid' column already exists in user_quiz_results table.")
        
        # Add API endpoint route in the model
        print("\nMake sure you add the following endpoint to your API:\n")
        print("""
@app.post("/users")
def create_or_update_user(user_data: dict):
    \"\"\"Create or update a user profile with Firebase UID.\"\"\"
    firebase_uid = user_data.get("user_id")  # Use "user_id" from frontend
    
    if not firebase_uid:
        raise HTTPException(status_code=400, detail="Firebase UID is required")
    
    with SessionLocal() as session:
        # Check if user exists
        user = session.query(User).filter_by(firebase_uid=firebase_uid).first()
        
        if user:
            # Update existing user
            user.username = user_data.get("display_name")
            user.email = user_data.get("email")
            user.photo_url = user_data.get("photo_url")
            user.last_login = datetime.now()
        else:
            # Create new user
            user = User(
                firebase_uid=firebase_uid,
                username=user_data.get("display_name"),
                email=user_data.get("email"),
                photo_url=user_data.get("photo_url"),
                created_at=datetime.now(),
                last_login=datetime.now()
            )
            session.add(user)
        
        session.commit()
        return {"message": "User profile updated successfully", "user_id": user.id}
        """)
        
        print("\nAnd add this route for getting quiz history by Firebase UID:\n")
        print("""
@app.get("/user/{firebase_uid}/quiz-history")
def get_user_quiz_history(firebase_uid: str):
    \"\"\"Get quiz history for a user using their Firebase UID.\"\"\"
    with SessionLocal() as session:
        # First, get the internal user ID from Firebase UID
        user = session.query(User).filter_by(firebase_uid=firebase_uid).first()
        
        if not user:
            # Create a temporary user if they don't exist
            user = User(
                firebase_uid=firebase_uid,
                username="Temporary User",
                created_at=datetime.now(),
                last_login=datetime.now()
            )
            session.add(user)
            session.commit()
            
            # Return empty history for new users
            return {"quiz_history": [], "statistics": {"total_quizzes": 0, "average_score": 0}}
        
        # Get quiz history using the internal user ID
        quiz_results = session.query(UserQuizResult).filter(
            UserQuizResult.user_id == user.id,
            UserQuizResult.completed == true()
        ).order_by(UserQuizResult.completed_at.desc()).all()
        
        # Map results to response format
        history = []
        for result in quiz_results:
            quiz_topic = session.query(QuizTopic).filter_by(id=result.topic_id).first()
            
            history.append({
                "quiz_result_id": result.id,
                "topic_id": result.topic_id,
                "topic_name": quiz_topic.name if quiz_topic else "Unknown Topic",
                "category": quiz_topic.category if quiz_topic else "Unknown",
                "subcategory": quiz_topic.subcategory if quiz_topic else "Unknown",
                "score": float(result.score),
                "correct_answers": result.correct_answers,
                "total_questions": result.total_questions,
                "time_taken": result.time_taken,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "day_of_week": result.day_of_week,
                "time_of_day": result.time_of_day,
                "average_time_per_question": float(result.average_time_per_question) if result.average_time_per_question else None,
                "difficulty_level": result.difficulty_level,
                "streak": result.streak,
                "quiz_context": result.quiz_context
            })
        
        return {"quiz_history": history}
        """)
        
        print("\nFix completed! Check that your API endpoints are implemented correctly.")

if __name__ == "__main__":
    main() 
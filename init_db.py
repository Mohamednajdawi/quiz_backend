import os
import sys

# Add the parent directory to the Python path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.sqlite_dal import Base
from backend.db import engine

def init_database():
    # Create all tables defined in sqlite_dal.py
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database() 
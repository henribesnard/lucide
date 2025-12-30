"""
Initialize the database for Telegram bot testing.

Creates all necessary tables in the SQLite database.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from backend.db.database import Base, engine
from backend.db.models import User, Conversation, Message, MatchAnalysis, MatchAnalysisAccess

def init_database():
    """Create all database tables."""
    print("Creating database tables...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("[OK] Database initialized successfully!")
    print(f"   Database URL: {os.getenv('DATABASE_URL')}")
    print(f"   Tables created: users, conversations, messages, match_analyses, match_analysis_accesses")

if __name__ == "__main__":
    init_database()

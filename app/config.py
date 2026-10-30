import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    db_url = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, '..', 'sacco.db')}")
    
    # Fix Render's postgres:// URL for SQLAlchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "sw")

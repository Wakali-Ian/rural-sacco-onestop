import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, '..', 'sacco.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "sw")

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Data Directories
DATA_DIR = BASE_DIR / "data"
RESUME_DIR = DATA_DIR / "resumes"
REPORTS_DIR = DATA_DIR / "reports"
QUESTION_BANKS_DIR = DATA_DIR / "question_banks"
DB_PATH = DATA_DIR / "interview_system.db"

# Ensure runtime directories exist
for directory in [DATA_DIR, RESUME_DIR, REPORTS_DIR, QUESTION_BANKS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Scoring Weights
SCORING_WEIGHTS = {
    "technical": float(os.getenv("WEIGHT_TECHNICAL", 0.40)),
    "structure": float(os.getenv("WEIGHT_STRUCTURE", 0.25)),
    "communication": float(os.getenv("WEIGHT_COMMUNICATION", 0.20)),
    "confidence": float(os.getenv("WEIGHT_CONFIDENCE", 0.15)),
}

# Session Defaults
DEFAULT_MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS_PER_SESSION", 5))
ADAPTIVE_DIFFICULTY = os.getenv("ADAPTIVE_DIFFICULTY_ENABLED", "True").lower() in ("true", "1", "yes")

# Common English speech filler words
COMMON_FILLER_WORDS = [
    "um", "uh", "er", "ah", "like", "you know", "basically",
    "actually", "sort of", "kind of", "i mean", "right", "so yeah"
]

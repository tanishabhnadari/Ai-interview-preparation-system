from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class InterviewDifficulty(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class QuestionCategory(str, Enum):
    TECHNICAL = "Technical"
    SYSTEM_DESIGN = "System Design"
    BEHAVIORAL = "Behavioral (STAR)"
    SITUATIONAL = "Situational"
    CODING_CONCEPTS = "Coding Concepts"

class CandidateProfile(BaseModel):
    name: str = "Candidate"
    target_role: str = "Software Engineer"
    experience_level: InterviewDifficulty = InterviewDifficulty.INTERMEDIATE
    detected_skills: List[str] = Field(default_factory=list)
    raw_resume_text: Optional[str] = None

class JobDescription(BaseModel):
    title: str = "Software Engineer"
    required_skills: List[str] = Field(default_factory=list)
    raw_jd_text: Optional[str] = None

class Question(BaseModel):
    id: str
    text: str
    category: QuestionCategory
    difficulty: InterviewDifficulty
    expected_keywords: List[str] = Field(default_factory=list)
    context_hint: Optional[str] = None
    follow_up_for: Optional[str] = None  # Question ID if dynamic follow-up

class SpeechMetrics(BaseModel):
    transcript: str = ""
    word_count: int = 0
    duration_seconds: float = 0.0
    words_per_minute: float = 0.0
    filler_word_counts: Dict[str, int] = Field(default_factory=dict)
    total_filler_words: int = 0
    fluency_score: float = 100.0  # 0 to 100 based on filler word density & pace

class QuestionEvaluation(BaseModel):
    question_id: str
    question_text: str
    candidate_answer: str
    technical_score: float = Field(ge=0.0, le=100.0)
    structure_score: float = Field(ge=0.0, le=100.0)
    communication_score: float = Field(ge=0.0, le=100.0)
    confidence_score: float = Field(ge=0.0, le=100.0)
    overall_score: float = Field(ge=0.0, le=100.0)
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    key_missed_concepts: List[str] = Field(default_factory=list)
    ideal_answer: str
    speech_metrics: Optional[SpeechMetrics] = None

class InterviewSession(BaseModel):
    session_id: str
    candidate: CandidateProfile
    job_description: JobDescription
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    questions: List[Question] = Field(default_factory=list)
    current_index: int = 0
    evaluations: List[QuestionEvaluation] = Field(default_factory=list)
    overall_score: float = 0.0
    is_completed: bool = False

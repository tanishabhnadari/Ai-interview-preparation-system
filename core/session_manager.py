import uuid
from typing import Optional, Dict, Any, List
from core.models import (
    InterviewSession, CandidateProfile, JobDescription, Question, 
    QuestionEvaluation, SpeechMetrics, InterviewDifficulty
)
from modules.question_generator import QuestionGenerator
from modules.answer_evaluator import AnswerEvaluator
from database.db_manager import DatabaseManager
from config import ADAPTIVE_DIFFICULTY, DEFAULT_MAX_QUESTIONS

class SessionManager:
    """Manages the lifecycle and state machine of an interview session."""
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self.question_gen = QuestionGenerator()
        self.evaluator = AnswerEvaluator()
        self.current_session: Optional[InterviewSession] = None

    def start_new_session(
        self,
        candidate: CandidateProfile,
        jd: JobDescription,
        num_questions: int = DEFAULT_MAX_QUESTIONS
    ) -> InterviewSession:
        """Initializes a new interview session and generates questions."""
        questions = self.question_gen.generate_initial_questions(
            candidate=candidate,
            jd=jd,
            count=num_questions
        )

        session = InterviewSession(
            session_id=f"sess_{uuid.uuid4().hex[:8]}",
            candidate=candidate,
            job_description=jd,
            questions=questions,
            current_index=0,
            evaluations=[],
            overall_score=0.0,
            is_completed=False
        )

        self.current_session = session
        self.db.save_session(session)
        return session

    def get_current_question(self) -> Optional[Question]:
        """Returns the current active question for the candidate."""
        if not self.current_session or self.current_session.is_completed:
            return None
        if self.current_session.current_index < len(self.current_session.questions):
            return self.current_session.questions[self.current_session.current_index]
        return None

    def submit_answer(
        self, 
        answer_text: str, 
        speech_metrics: Optional[SpeechMetrics] = None
    ) -> QuestionEvaluation:
        """Evaluates the candidate's answer, adjusts difficulty if enabled, and advances state."""
        if not self.current_session:
            raise ValueError("No active interview session found.")

        current_q = self.get_current_question()
        if not current_q:
            raise ValueError("All questions in the session have already been answered.")

        # 1. Evaluate answer
        evaluation = self.evaluator.evaluate(current_q, answer_text, speech_metrics)
        self.current_session.evaluations.append(evaluation)

        # 2. Adaptive follow-up question insertion (if enabled and space permits)
        if ADAPTIVE_DIFFICULTY and len(self.current_session.questions) < 10:
            adaptive_q = self.question_gen.generate_adaptive_follow_up(current_q, evaluation.overall_score)
            if adaptive_q:
                # Insert immediately as the next question
                self.current_session.questions.insert(self.current_session.current_index + 1, adaptive_q)

        # 3. Advance question index
        self.current_session.current_index += 1

        # 4. Check if interview is finished
        if self.current_session.current_index >= len(self.current_session.questions):
            self.current_session.is_completed = True
            self._finalize_session()

        # Save state
        self.db.save_session(self.current_session)
        return evaluation

    def _finalize_session(self):
        """Computes aggregate final statistics across all questions."""
        if not self.current_session or not self.current_session.evaluations:
            return

        scores = [e.overall_score for e in self.current_session.evaluations]
        self.current_session.overall_score = round(sum(scores) / len(scores), 1)

    def load_session(self, session_id: str) -> Optional[InterviewSession]:
        session = self.db.get_session(session_id)
        if session:
            self.current_session = session
        return session

import unittest
from core.models import CandidateProfile, JobDescription, InterviewDifficulty, QuestionCategory, Question
from core.session_manager import SessionManager
from modules.resume_parser import ResumeParser
from modules.speech_processor import SpeechProcessor
from modules.question_generator import QuestionGenerator
from modules.answer_evaluator import AnswerEvaluator
from database.db_manager import DatabaseManager
from database.vector_store import SemanticVectorStore
import os

class TestAIInterviewSystem(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.session_mgr = SessionManager(db_manager=self.db)
        self.parser = ResumeParser()
        self.speech = SpeechProcessor()

    def test_resume_parser_skills(self):
        sample_text = "Senior Python engineer with experience in Docker, Kubernetes, FastAPI, and machine learning using PyTorch."
        skills = self.parser.extract_skills(sample_text)
        self.assertIn("Python", skills)
        self.assertIn("Docker", skills)
        self.assertIn("Fastapi", skills)
        self.assertIn("Pytorch", skills)

    def test_jd_skill_matching(self):
        candidate_skills = ["Python", "Fastapi", "Docker", "Sql"]
        jd_text = "Required skills: Python, Docker, Kubernetes, AWS, SQL"
        match = self.parser.analyze_match(candidate_skills, jd_text)
        self.assertGreater(match["match_score"], 0)
        self.assertIn("Python", match["matched_skills"])
        self.assertIn("Kubernetes", match["missing_skills"])

    def test_speech_processor_metrics(self):
        spoken_text = "Um basically I used Python and uh like Docker to deploy the microservice."
        metrics = self.speech.analyze_speech(spoken_text, duration_seconds=10.0)
        self.assertGreater(metrics.total_filler_words, 0)
        self.assertIn("um", metrics.filler_word_counts)
        self.assertIn("basically", metrics.filler_word_counts)
        self.assertGreater(metrics.words_per_minute, 0)

    def test_semantic_vector_store(self):
        store = SemanticVectorStore()
        store.add_documents([
            {"id": "doc1", "text": "Python memory management and garbage collection"},
            {"id": "doc2", "text": "Kubernetes cluster container orchestration"},
        ])
        results = store.search("Python memory leak gc", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0]["id"], "doc1")

    def test_answer_evaluator(self):
        evaluator = AnswerEvaluator(api_key="")  # test heuristic fallback
        question = Question(
            id="q_test_1",
            text="Explain Python memory management.",
            category=QuestionCategory.TECHNICAL,
            difficulty=InterviewDifficulty.INTERMEDIATE,
            expected_keywords=["reference counting", "garbage collection", "cyclic reference"]
        )
        answer = "Python uses reference counting as its primary mechanism and a cyclical garbage collection system for cyclic references."
        result = evaluator.evaluate(question, answer)
        self.assertGreaterEqual(result.technical_score, 70.0)
        self.assertGreater(result.overall_score, 0.0)
        self.assertIn("reference counting", [k.lower() for k in question.expected_keywords])

    def test_end_to_end_session_flow(self):
        candidate = CandidateProfile(
            name="Jane Doe",
            target_role="AI Engineer",
            experience_level=InterviewDifficulty.INTERMEDIATE,
            detected_skills=["Python", "PyTorch", "NLP"]
        )
        jd = JobDescription(
            title="AI Engineer",
            required_skills=["Python", "PyTorch", "RAG", "LLM"]
        )

        session = self.session_mgr.start_new_session(candidate, jd, num_questions=2)
        self.assertEqual(len(session.questions), 2)
        self.assertFalse(session.is_completed)

        # Answer Q1
        self.session_mgr.submit_answer("I utilize PyTorch tensors and fine-tune NLP models with regular evaluation.")
        
        # If adaptive question was injected, questions count might increase, otherwise 1 remaining
        while not self.session_mgr.current_session.is_completed:
            self.session_mgr.submit_answer("For system scaling, I implement distributed inference and caching.")

        self.assertTrue(self.session_mgr.current_session.is_completed)
        self.assertGreater(self.session_mgr.current_session.overall_score, 0.0)

if __name__ == "__main__":
    unittest.main()

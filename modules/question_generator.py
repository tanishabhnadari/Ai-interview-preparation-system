import json
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
from config import GEMINI_API_KEY, QUESTION_BANKS_DIR
from core.models import Question, QuestionCategory, InterviewDifficulty, CandidateProfile, JobDescription
from database.vector_store import SemanticVectorStore

class QuestionGenerator:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        self.vector_store = SemanticVectorStore()
        self.question_bank: List[Dict[str, Any]] = []
        self._load_seed_questions()

    def _load_seed_questions(self):
        seed_file = QUESTION_BANKS_DIR / "default_questions.json"
        if seed_file.exists():
            try:
                with open(seed_file, "r", encoding="utf-8") as f:
                    self.question_bank = json.load(f)
                self.vector_store.add_documents(self.question_bank, text_field="text")
            except Exception as e:
                print(f"[QuestionGenerator Error] Failed to load seed questions: {e}")

    def generate_initial_questions(
        self, 
        candidate: CandidateProfile, 
        jd: JobDescription, 
        count: int = 5
    ) -> List[Question]:
        """Generate a tailored set of interview questions matching the candidate and role."""
        if self.api_key:
            llm_questions = self._generate_with_gemini(candidate, jd, count)
            if llm_questions:
                return llm_questions

        # Fallback to semantic matching from curated question bank
        return self._generate_from_bank(candidate, jd, count)

    def _generate_from_bank(self, candidate: CandidateProfile, jd: JobDescription, count: int) -> List[Question]:
        query = f"{candidate.target_role} {' '.join(candidate.detected_skills)} {' '.join(jd.required_skills)}"
        results = self.vector_store.search(query, top_k=max(count, len(self.question_bank)))

        selected_bank = [item[0] for item in results] if results else self.question_bank
        questions: List[Question] = []

        # If not enough matched, add remaining from bank
        used_ids = set()
        for item in selected_bank:
            if item["id"] not in used_ids:
                questions.append(Question(
                    id=item["id"],
                    text=item["text"],
                    category=QuestionCategory(item.get("category", "Technical")),
                    difficulty=InterviewDifficulty(item.get("difficulty", candidate.experience_level.value)),
                    expected_keywords=item.get("expected_keywords", []),
                    context_hint=item.get("context_hint", "")
                ))
                used_ids.add(item["id"])
            if len(questions) >= count:
                break

        # If bank had fewer than count, fill with generic questions
        if len(questions) < count:
            defaults = [
                ("Explain a challenging project you built recently and the architectural trade-offs you made.", QuestionCategory.TECHNICAL),
                ("How do you ensure reliability and testing coverage in your production code?", QuestionCategory.CODING_CONCEPTS),
                ("Describe a situation where a project deadline was at risk. How did you prioritize?", QuestionCategory.BEHAVIORAL),
            ]
            for text, cat in defaults:
                if len(questions) >= count:
                    break
                questions.append(Question(
                    id=f"q_gen_{uuid.uuid4().hex[:6]}",
                    text=text,
                    category=cat,
                    difficulty=candidate.experience_level,
                    expected_keywords=["architecture", "testing", "trade-offs", "STAR method"]
                ))

        return questions[:count]

    def _generate_with_gemini(self, candidate: CandidateProfile, jd: JobDescription, count: int) -> Optional[List[Question]]:
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)

            prompt = f"""
            You are a Principal Tech Interviewer designing an interview for:
            Role: {candidate.target_role}
            Experience Level: {candidate.experience_level.value}
            Candidate Skills: {', '.join(candidate.detected_skills) if candidate.detected_skills else 'General'}
            Job Description Requirements: {', '.join(jd.required_skills) if jd.required_skills else 'Standard tech requirements'}

            Generate exactly {count} interview questions formatted as a JSON array of objects.
            Each object must have:
            - "id": a unique string (e.g. "q_gen_1")
            - "text": the precise, challenging interview question
            - "category": one of ["Technical", "System Design", "Behavioral (STAR)", "Situational", "Coding Concepts"]
            - "difficulty": one of ["Beginner", "Intermediate", "Advanced", "Expert"]
            - "expected_keywords": an array of 4-7 key technical concepts or terminology the candidate should mention
            - "context_hint": guidance on what an ideal answer should emphasize

            Return ONLY valid JSON.
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            raw = response.text.strip()
            # Clean markdown code blocks if wrapped
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\n", "", raw)
                raw = re.sub(r"\n```$", "", raw)

            data = json.loads(raw)
            questions = []
            for item in data:
                questions.append(Question(
                    id=item.get("id", f"q_{uuid.uuid4().hex[:6]}"),
                    text=item["text"],
                    category=QuestionCategory(item.get("category", "Technical")),
                    difficulty=InterviewDifficulty(item.get("difficulty", candidate.experience_level.value)),
                    expected_keywords=item.get("expected_keywords", []),
                    context_hint=item.get("context_hint", "")
                ))
            return questions
        except Exception as e:
            print(f"[QuestionGenerator Warning] Gemini generation failed: {e}. Falling back to question bank.")
            return None

    def generate_adaptive_follow_up(self, last_question: Question, last_score: float) -> Optional[Question]:
        """Generate an adaptive question: deep dive if score >= 75%, foundational if < 50%."""
        if last_score >= 75.0:
            return Question(
                id=f"follow_up_{uuid.uuid4().hex[:6]}",
                text=f"Building on your strong response regarding '{last_question.expected_keywords[0] if last_question.expected_keywords else 'that concept'}', how would you design this under extreme edge cases or high concurrency?",
                category=last_question.category,
                difficulty=InterviewDifficulty.ADVANCED,
                expected_keywords=last_question.expected_keywords + ["concurrency", "edge cases", "bottlenecks"],
                follow_up_for=last_question.id
            )
        elif last_score < 50.0:
            return Question(
                id=f"follow_up_{uuid.uuid4().hex[:6]}",
                text=f"Let's step back to the fundamentals. Can you define the core principle behind {last_question.expected_keywords[0] if last_question.expected_keywords else 'this concept'} with a simple code or real-world example?",
                category=last_question.category,
                difficulty=InterviewDifficulty.BEGINNER,
                expected_keywords=last_question.expected_keywords[:3],
                follow_up_for=last_question.id
            )
        return None

import re
import json
from typing import Optional, Dict, Any, List
from config import GEMINI_API_KEY, SCORING_WEIGHTS
from core.models import Question, QuestionEvaluation, SpeechMetrics

class AnswerEvaluator:
    """
    Multi-criteria evaluation engine that scores answers across:
    - Technical Accuracy (40%)
    - Structure & Completeness (25%)
    - Communication & Fluency (20%)
    - Confidence & Demeanor (15%)
    """
    def __init__(self, api_key: str = GEMINI_API_KEY, weights: Dict[str, float] = SCORING_WEIGHTS):
        self.api_key = api_key
        self.weights = weights

    def evaluate(
        self, 
        question: Question, 
        candidate_answer: str, 
        speech_metrics: Optional[SpeechMetrics] = None
    ) -> QuestionEvaluation:
        """Evaluate candidate response using LLM reasoning or heuristic rule engine."""
        clean_answer = candidate_answer.strip()
        if not clean_answer:
            return self._empty_response_eval(question, speech_metrics)

        if self.api_key:
            llm_eval = self._evaluate_with_gemini(question, clean_answer, speech_metrics)
            if llm_eval:
                return llm_eval

        # Heuristic Rule-Based NLP Evaluator fallback
        return self._evaluate_heuristic(question, clean_answer, speech_metrics)

    def _empty_response_eval(self, question: Question, speech_metrics: Optional[SpeechMetrics]) -> QuestionEvaluation:
        return QuestionEvaluation(
            question_id=question.id,
            question_text=question.text,
            candidate_answer="[No answer provided]",
            technical_score=0.0,
            structure_score=0.0,
            communication_score=0.0,
            confidence_score=0.0,
            overall_score=0.0,
            strengths=[],
            areas_for_improvement=["No answer was recorded for this question."],
            key_missed_concepts=question.expected_keywords,
            ideal_answer=f"An ideal answer should cover: {', '.join(question.expected_keywords)}.",
            speech_metrics=speech_metrics
        )

    def _evaluate_heuristic(
        self, 
        question: Question, 
        answer: str, 
        speech_metrics: Optional[SpeechMetrics]
    ) -> QuestionEvaluation:
        lowered = answer.lower()
        words = re.findall(r"\b\w+\b", lowered)
        word_count = len(words)

        # 1. Technical Accuracy & Keyword Coverage
        matched_keywords = []
        missed_keywords = []
        for kw in question.expected_keywords:
            if kw.lower() in lowered:
                matched_keywords.append(kw)
            else:
                missed_keywords.append(kw)

        keyword_ratio = len(matched_keywords) / len(question.expected_keywords) if question.expected_keywords else 0.8
        technical_score = min(100.0, keyword_ratio * 90.0 + (min(word_count, 150) / 150.0) * 10.0)

        # 2. Structure & Completeness
        # Check for structure markers (e.g. firstly, because, result, for example, however, in conclusion)
        structure_markers = ["first", "second", "example", "because", "result", "therefore", "situation", "action", "finally"]
        structure_hits = sum(1 for sm in structure_markers if sm in lowered)
        structure_score = min(100.0, 50.0 + (structure_hits * 12.0) + (min(word_count, 200) / 200.0 * 20.0))

        # 3. Communication & Fluency
        fluency_base = speech_metrics.fluency_score if speech_metrics else 85.0
        # Word length and vocabulary richness
        unique_words = len(set(words))
        vocab_richness = (unique_words / word_count) if word_count > 0 else 0
        communication_score = min(100.0, (fluency_base * 0.7) + (vocab_richness * 30.0))

        # 4. Confidence & Demeanor
        # Penalize excessive hesitant words: "maybe", "i guess", "i think", "sort of", "probably"
        hesitation_words = ["maybe", "i guess", "not sure", "probably", "i suppose"]
        hesitation_count = sum(len(re.findall(rf"\b{hw}\b", lowered)) for hw in hesitation_words)
        confidence_score = max(20.0, 95.0 - (hesitation_count * 15.0))

        # Compute Weighted Overall Score
        overall = (
            technical_score * self.weights["technical"] +
            structure_score * self.weights["structure"] +
            communication_score * self.weights["communication"] +
            confidence_score * self.weights["confidence"]
        )

        strengths = []
        if matched_keywords:
            strengths.append(f"Covered core terminology: {', '.join(matched_keywords[:3])}.")
        if word_count >= 80:
            strengths.append("Provided a detailed explanation with good elaboration.")
        if structure_hits >= 2:
            strengths.append("Structured the answer logically with clear reasoning markers.")

        improvements = []
        if missed_keywords:
            improvements.append(f"Consider addressing key concepts: {', '.join(missed_keywords[:3])}.")
        if word_count < 50:
            improvements.append("Answer was too brief. Expand with concrete technical details or past project examples.")
        if hesitation_count > 1:
            improvements.append("Eliminate uncertainty phrases like 'maybe' or 'I guess' to project stronger technical confidence.")

        ideal_answer = (
            f"A comprehensive answer would address the question directly, explaining: {', '.join(question.expected_keywords)}. "
            f"It should begin with a direct definition or thesis, detail the architecture or mechanism, and conclude with real-world trade-offs."
        )

        return QuestionEvaluation(
            question_id=question.id,
            question_text=question.text,
            candidate_answer=answer,
            technical_score=round(technical_score, 1),
            structure_score=round(structure_score, 1),
            communication_score=round(communication_score, 1),
            confidence_score=round(confidence_score, 1),
            overall_score=round(overall, 1),
            strengths=strengths if strengths else ["Attempted the question directly."],
            areas_for_improvement=improvements if improvements else ["Continue practicing depth and brevity balance."],
            key_missed_concepts=missed_keywords,
            ideal_answer=ideal_answer,
            speech_metrics=speech_metrics
        )

    def _evaluate_with_gemini(
        self, 
        question: Question, 
        answer: str, 
        speech_metrics: Optional[SpeechMetrics]
    ) -> Optional[QuestionEvaluation]:
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)

            speech_info = ""
            if speech_metrics:
                speech_info = f"Speech Speed: {speech_metrics.words_per_minute} WPM, Filler Words: {speech_metrics.total_filler_words}."

            prompt = f"""
            You are a Senior Principal Interviewer evaluating a candidate's response.
            Question: "{question.text}"
            Category: {question.category.value}
            Difficulty: {question.difficulty.value}
            Expected Keywords/Concepts: {', '.join(question.expected_keywords)}

            Candidate Answer: "{answer}"
            {speech_info}

            Evaluate the response strictly across 4 dimensions on a 0-100 scale:
            - technical_score: correctness, technical depth, coverage of expected concepts
            - structure_score: logical flow, reasoning, STAR methodology if behavioral
            - communication_score: clarity, concise phrasing, appropriate technical vocabulary
            - confidence_score: assertiveness, definitive knowledge, absence of self-doubt

            Provide output in JSON format with these exact keys:
            {{
                "technical_score": float,
                "structure_score": float,
                "communication_score": float,
                "confidence_score": float,
                "strengths": [list of 2-3 specific bullet points],
                "areas_for_improvement": [list of 2-3 actionable improvements],
                "key_missed_concepts": [list of concepts or keywords omitted],
                "ideal_answer": "A model answer demonstrating high competence"
            }}
            Return ONLY valid JSON.
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\n", "", raw)
                raw = re.sub(r"\n```$", "", raw)

            data = json.loads(raw)

            tech = float(data.get("technical_score", 70.0))
            struct = float(data.get("structure_score", 70.0))
            comm = float(data.get("communication_score", 70.0))
            conf = float(data.get("confidence_score", 70.0))

            overall = (
                tech * self.weights["technical"] +
                struct * self.weights["structure"] +
                comm * self.weights["communication"] +
                conf * self.weights["confidence"]
            )

            return QuestionEvaluation(
                question_id=question.id,
                question_text=question.text,
                candidate_answer=answer,
                technical_score=round(tech, 1),
                structure_score=round(struct, 1),
                communication_score=round(comm, 1),
                confidence_score=round(conf, 1),
                overall_score=round(overall, 1),
                strengths=data.get("strengths", []),
                areas_for_improvement=data.get("areas_for_improvement", []),
                key_missed_concepts=data.get("key_missed_concepts", []),
                ideal_answer=data.get("ideal_answer", ""),
                speech_metrics=speech_metrics
            )
        except Exception as e:
            print(f"[AnswerEvaluator Warning] Gemini evaluation failed: {e}. Falling back to heuristic evaluator.")
            return None

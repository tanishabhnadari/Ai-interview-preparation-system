import re
import os
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from pypdf import PdfReader

# Comprehensive tech skill taxonomy for NLP matching
COMMON_SKILL_TAXONOMY = {
    # Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "sql", "html", "css",
    # Frameworks & Libraries
    "react", "angular", "vue", "next.js", "node.js", "express", "django", "flask", "fastapi", "spring boot", "asp.net",
    # AI / ML / Data
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn", 
    "pandas", "numpy", "opencv", "transformers", "llm", "rag", "langchain", "gemini", "openai", "whisper", "data science",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "terraform", "ansible", "linux", "git", "github", "jenkins",
    # Databases & Storage
    "postgresql", "mysql", "sqlite", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "chromadb", "faiss",
    # Concepts & Architecture
    "microservices", "rest api", "graphql", "system design", "distributed systems", "agile", "scrum", "object-oriented programming", "tdd"
}

class ResumeParser:
    def __init__(self, skill_taxonomy: Optional[Set[str]] = None):
        self.skills_taxonomy = {s.lower() for s in (skill_taxonomy or COMMON_SKILL_TAXONOMY)}

    def extract_text_from_pdf(self, pdf_file_path: str) -> str:
        """Extract text from an uploaded PDF file."""
        text = ""
        try:
            reader = PdfReader(pdf_file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"[ResumeParser Error] Failed to read PDF {pdf_file_path}: {e}")
        return text.strip()

    def extract_skills(self, text: str) -> List[str]:
        """Extract recognized tech and domain skills from text."""
        lowered_text = " " + re.sub(r"[^\w\+\#\.\-]", " ", text.lower()) + " "
        detected = set()

        for skill in self.skills_taxonomy:
            # Match skill surrounded by word boundaries or punctuation
            escaped_skill = re.escape(skill)
            pattern = rf"(?<!\w){escaped_skill}(?!\w)"
            if re.search(pattern, lowered_text):
                detected.add(skill.title() if len(skill) > 3 else skill.upper())

        return sorted(list(detected))

    def analyze_match(self, resume_skills: List[str], jd_text_or_skills: str | List[str]) -> Dict[str, Any]:
        """Compare candidate skills against Job Description requirements."""
        if isinstance(jd_text_or_skills, str):
            jd_skills = self.extract_skills(jd_text_or_skills)
        else:
            jd_skills = [s.strip() for s in jd_text_or_skills]

        resume_set = {s.lower() for s in resume_skills}
        jd_set = {s.lower() for s in jd_skills}

        matched = resume_set & jd_set
        missing = jd_set - resume_set
        extra = resume_set - jd_set

        match_score = (len(matched) / len(jd_set) * 100.0) if jd_set else 100.0

        return {
            "match_score": round(match_score, 1),
            "matched_skills": sorted([s.title() for s in matched]),
            "missing_skills": sorted([s.title() for s in missing]),
            "candidate_skills": sorted([s.title() for s in resume_set]),
            "required_skills": sorted([s.title() for s in jd_set])
        }

# AI Interview Preparation System

An end-to-end intelligent interview preparation platform built with Python, AI/ML concepts, and Streamlit. It parses resumes, benchmarks competencies against Job Descriptions, conducts dynamic interviews, transcribes and evaluates responses across multiple criteria, and provides visual performance scorecards.

---

## 🚀 Key Features & AI/ML Concepts

1. **Resume & Job Description Intelligence (NLP)**:
   - Automated text extraction from PDF resumes (`pypdf`).
   - Rule & entity-based skill extraction across languages, cloud, AI/ML, and architecture.
   - Skill-gap matching calculating match percentages and missing competency indicators.

2. **Adaptive Question Generation Engine**:
   - Dynamic prompt generation via Google Gemini API (`gemini-2.5-flash`).
   - Zero-dependency Semantic Vector Search fallback powered by TF-IDF & Cosine Similarity (`SemanticVectorStore`).
   - Adaptive difficulty: Deep-dive follow-ups for high performers ($\ge 75\%$), foundational follow-ups for low performers ($< 50\%$).

3. **Multi-Criteria Answer Evaluation**:
   - **Technical Accuracy & Depth (40%)**: Concept coverage, technical terminology, and semantic correctness.
   - **Structure & Reasoning (25%)**: Logic flow and STAR method (Situation, Task, Action, Result) validation.
   - **Communication & Fluency (20%)**: Words-Per-Minute (WPM) cadence and filler word density detection ("um", "uh", "basically", etc.).
   - **Confidence & Demeanor (15%)**: Certainty analysis and reduction of hesitation markers.

4. **Persistence & Analytics Dashboard**:
   - SQLite persistence tracking candidate history, past sessions, and reports.
   - Interactive Plotly visualizations (Competency Radar Chart & Question Score Progression).
   - Exportable comprehensive JSON reports with recommended ideal answers.

---

## 📁 Project Structure

```text
ai_interview_system/
├── app.py                      # Main Streamlit interactive application
├── config.py                   # Central configuration, scoring weights & paths
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
│
├── core/
│   ├── models.py               # Pydantic schemas (Session, Question, Evaluation)
│   └── session_manager.py      # State machine orchestrating interview lifecycle
│
├── modules/
│   ├── resume_parser.py        # PDF extraction & skill gap matching
│   ├── question_generator.py   # Adaptive, context-aware question engine
│   ├── speech_processor.py     # Speech cadence, WPM & filler word analyzer
│   └── answer_evaluator.py     # Multi-criteria scoring & feedback engine
│
├── database/
│   ├── db_manager.py           # SQLite persistence for interview history
│   └── vector_store.py         # Semantic TF-IDF + Cosine similarity vector store
│
├── data/
│   ├── question_banks/         # Seed question banks (Python, ML, System Design, STAR)
│   ├── resumes/                # Uploaded resume storage
│   └── reports/                # Saved session reports
│
├── utils/
│   ├── visualizer.py           # Plotly radar and progression charts
│   └── audio_recorder.py       # Audio & speech handling utilities
│
└── tests/
    └── test_interview_system.py # Complete test suite
```

---

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional for Gemini LLM)
Copy the example environment configuration:
```bash
cp .env.example .env
```
Add your Google Gemini API key to `.env` (or input it directly in the app's sidebar):
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
*(Note: If no API key is provided, the system seamlessly operates using its built-in heuristic NLP evaluator and semantic vector store!)*

---

## 🏃 Running the Application

Launch the Streamlit app:
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the test suite to verify all modules:
```bash
python -m unittest tests/test_interview_system.py
```

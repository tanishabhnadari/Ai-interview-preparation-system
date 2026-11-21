import sqlite3
import json
from typing import List, Dict, Optional, Any
from core.models import InterviewSession, QuestionEvaluation, Question, CandidateProfile, JobDescription
from config import DB_PATH

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self._shared_conn = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_conn.row_factory = sqlite3.Row
        self.init_db()

    def _get_connection(self):
        if self._shared_conn:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    candidate_name TEXT,
                    target_role TEXT,
                    difficulty TEXT,
                    created_at TEXT,
                    overall_score REAL,
                    is_completed INTEGER,
                    session_json TEXT
                )
            """)
            conn.commit()

    def save_session(self, session: InterviewSession) -> bool:
        try:
            with self._get_connection() as conn:
                session_dict = session.model_dump()
                conn.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (session_id, candidate_name, target_role, difficulty, created_at, overall_score, is_completed, session_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    session.candidate.name,
                    session.candidate.target_role,
                    session.candidate.experience_level.value,
                    session.created_at,
                    session.overall_score,
                    1 if session.is_completed else 0,
                    json.dumps(session_dict)
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"[DatabaseManager Error] Failed to save session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT session_json FROM sessions WHERE session_id = ?", (session_id,))
                row = cur.fetchone()
                if row:
                    data = json.loads(row["session_json"])
                    return InterviewSession(**data)
            return None
        except Exception as e:
            print(f"[DatabaseManager Error] Failed to load session: {e}")
            return None

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT session_id, candidate_name, target_role, difficulty, created_at, overall_score, is_completed
                    FROM sessions
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DatabaseManager Error] Failed to list sessions: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"[DatabaseManager Error] Failed to delete session: {e}")
            return False

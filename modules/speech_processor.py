import re
from typing import Dict, Any, List
from config import COMMON_FILLER_WORDS
from core.models import SpeechMetrics

class SpeechProcessor:
    """
    Analyzes spoken or transcribed answers for fluency, pace, and speech mannerisms.
    Can be coupled with Whisper or audio recorders.
    """
    def __init__(self, filler_words: List[str] = COMMON_FILLER_WORDS):
        self.filler_words = [fw.lower() for fw in filler_words]

    def analyze_speech(self, text: str, duration_seconds: float = 0.0) -> SpeechMetrics:
        """Analyze text and duration for cadence, filler words, and fluency."""
        clean_text = text.strip()
        words = re.findall(r"\b[a-zA-Z0-9_\'\-]+\b", clean_text.lower())
        word_count = len(words)

        # Estimate duration if 0 (standard speaking rate approx 130 WPM)
        if duration_seconds <= 0.0:
            duration_seconds = max(1.0, (word_count / 130.0) * 60.0)

        words_per_minute = round((word_count / duration_seconds) * 60.0, 1) if duration_seconds > 0 else 0.0

        # Filler word detection
        lowered_text = " " + clean_text.lower() + " "
        filler_counts = {}
        total_fillers = 0

        for filler in self.filler_words:
            pattern = rf"(?<!\w){re.escape(filler)}(?!\w)"
            matches = len(re.findall(pattern, lowered_text))
            if matches > 0:
                filler_counts[filler] = matches
                total_fillers += matches

        # Fluency calculation (100 base, penalize for excessive filler density & abnormal WPM)
        fluency = 100.0
        if word_count > 0:
            filler_ratio = total_fillers / word_count
            fluency -= min(40.0, filler_ratio * 300.0)  # Max 40% penalty for fillers

        # Cadence penalty: Optimal interview pace is 115 - 165 WPM
        if words_per_minute < 90:
            fluency -= min(20.0, (90 - words_per_minute) * 0.5)
        elif words_per_minute > 180:
            fluency -= min(20.0, (words_per_minute - 180) * 0.5)

        fluency = max(10.0, min(100.0, round(fluency, 1)))

        return SpeechMetrics(
            transcript=clean_text,
            word_count=word_count,
            duration_seconds=round(duration_seconds, 1),
            words_per_minute=words_per_minute,
            filler_word_counts=filler_counts,
            total_filler_words=total_fillers,
            fluency_score=fluency
        )

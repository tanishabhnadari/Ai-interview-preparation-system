import io
from typing import Optional, Tuple
from modules.speech_processor import SpeechProcessor
from core.models import SpeechMetrics

class AudioInputHandler:
    """Helper for handling audio uploads or simulated microphone input in Streamlit."""
    def __init__(self):
        self.processor = SpeechProcessor()

    def process_text_or_audio(
        self, 
        text_input: str, 
        audio_duration_seconds: float = 0.0
    ) -> Tuple[str, SpeechMetrics]:
        """Processes provided text with acoustic speech metrics."""
        metrics = self.processor.analyze_speech(text_input, duration_seconds=audio_duration_seconds)
        return text_input, metrics

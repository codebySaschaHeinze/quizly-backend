from pathlib import Path

import whisper


class AudioTranscriptionService:
    """Transcribe local audio files with Whisper."""

    model_name = 'base'

    def __init__(self):
        self.model = whisper.load_model(self.model_name)

    def transcribe_audio(self, audio_path):
        """Transcribe one local audio file and return the transcript text."""
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f'Audio file not found: {audio_path}')

        result = self.model.transcribe(str(audio_path), fp16=False)
        return result['text'].strip()
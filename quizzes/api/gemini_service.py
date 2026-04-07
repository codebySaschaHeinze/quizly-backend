from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google import genai


class GeminiQuizGenerationService:
    """Generate quiz data from a transcript using Gemini."""

    model_name = 'gemini-2.5-flash'

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ImproperlyConfigured('GEMINI_API_KEY is not configured.')

        self.client = genai.Client()

    def build_prompt(self, transcript):
        """Build the prompt for quiz generation from a transcript."""
        return f'''
You are a quiz generator.

Create a quiz based on the following transcript.

Return valid JSON only.
Do not add markdown code fences.
Do not add explanations.

The JSON must follow exactly this structure:
{{
  "title": "Quiz title",
  "description": "Short quiz description",
  "questions": [
    {{
      "question_title": "Question text",
      "question_options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "answer": "One of the four options"
    }}
  ]
}}

Rules:
- Create exactly 10 questions.
- Each question must have exactly 4 options.
- The answer must exactly match one option.
- The quiz must be based only on the transcript content.
- Keep title and description short and clear.

Transcript:
{transcript}
'''.strip()

    def generate_quiz_text(self, transcript):
        """Generate raw quiz text from a transcript."""
        prompt = self.build_prompt(transcript)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        return response.text
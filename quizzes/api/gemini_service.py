import json
import time

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from google import genai
from google.genai.errors import ServerError

from .utils import remove_markdown_code_fences


class GeminiQuizGenerationService:
    """Generate structured quiz data from a transcript using Gemini."""

    model_name = 'gemini-2.5-flash'
    retry_delays = [5, 10]

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ImproperlyConfigured('GEMINI_API_KEY is not configured.')

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

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

    def parse_quiz_data(self, raw_text):
        """Parse and validate quiz JSON returned by Gemini."""
        cleaned_text = remove_markdown_code_fences(raw_text)

        try:
            quiz_data = json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            raise ValidationError('Gemini returned invalid JSON.') from exc

        self.validate_quiz_data(quiz_data)
        return quiz_data

    def validate_quiz_data(self, quiz_data):
        """Validate the generated quiz data structure."""
        if not isinstance(quiz_data, dict):
            raise ValidationError('Quiz data must be a JSON object.')

        required_quiz_fields = ['title', 'description', 'questions']
        for field in required_quiz_fields:
            if field not in quiz_data:
                raise ValidationError(f'Missing quiz field: {field}')

        questions = quiz_data.get('questions')

        if not isinstance(questions, list):
            raise ValidationError('Questions must be a list.')

        if len(questions) != 10:
            raise ValidationError('Quiz must contain exactly 10 questions.')

        for index, question in enumerate(questions, start=1):
            self.validate_question_data(question, index)

    def validate_question_data(self, question, index):
        """Validate one generated question."""
        if not isinstance(question, dict):
            raise ValidationError(f'Question {index} must be an object.')

        required_question_fields = [
            'question_title',
            'question_options',
            'answer',
        ]
        for field in required_question_fields:
            if field not in question:
                raise ValidationError(
                    f'Question {index} is missing field: {field}'
                )

        options = question.get('question_options')
        answer = question.get('answer')

        if not isinstance(options, list):
            raise ValidationError(
                f'Question {index} options must be a list.'
            )

        if len(options) != 4:
            raise ValidationError(
                f'Question {index} must have exactly 4 options.'
            )

        if not all(isinstance(option, str) for option in options):
            raise ValidationError(
                f'Question {index} options must all be strings.'
            )

        if not isinstance(answer, str):
            raise ValidationError(
                f'Question {index} answer must be a string.'
            )

        if answer not in options:
            raise ValidationError(
                f'Question {index} answer must match one option exactly.'
            )

    def generate_quiz_data(self, transcript):
        """Generate validated quiz data from a transcript."""
        prompt = self.build_prompt(transcript)
        response_text = self.generate_with_retry(prompt)
        return self.parse_quiz_data(response_text)

    def generate_with_retry(self, prompt):
        """Generate quiz text with small retries for temporary Gemini outages."""
        attempts = len(self.retry_delays) + 1

        for attempt in range(attempts):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                return response.text
            except ServerError:
                if attempt >= len(self.retry_delays):
                    raise

                time.sleep(self.retry_delays[attempt])
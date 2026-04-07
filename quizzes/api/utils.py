import re

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from quizzes.models import Quiz


def get_quiz_for_user_or_raise(user, quiz_id):
    """Return a quiz for the current user or raise the correct error."""
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    if quiz.user != user:
        raise PermissionDenied('You do not have permission to access this quiz.')

    return quiz


def extract_video_id(url):
    """Extract the YouTube video id from a supported URL."""
    patterns = [
        r'youtu\.be/([A-Za-z0-9_-]{11})',
        r'youtube\.com/watch\?v=([A-Za-z0-9_-]{11})',
        r'youtube\.com/embed/([A-Za-z0-9_-]{11})',
        r'youtube\.com/shorts/([A-Za-z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValidationError({'url': 'Invalid YouTube URL.'})


def build_youtube_url(video_id):
    """Build the normalized YouTube watch URL from a video id."""
    return f'https://www.youtube.com/watch?v={video_id}'


def normalize_youtube_url(url):
    """Validate a YouTube URL and return the normalized watch URL."""
    video_id = extract_video_id(url)
    return build_youtube_url(video_id)


def remove_markdown_code_fences(text):
    """Remove markdown code fences from AI output."""
    cleaned_text = text.strip()
    cleaned_text = re.sub(r'^```json\s*', '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r'^```\s*', '', cleaned_text)
    cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
    return cleaned_text.strip()
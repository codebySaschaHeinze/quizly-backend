from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from quizzes.models import Quiz


def get_quiz_for_user_or_raise(user, quiz_id):
    """Return a quiz for the current user or raise the correct error."""
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    if quiz.user != user:
        raise PermissionDenied('You do not have permission to access this quiz.')

    return quiz
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quizzes.models import Quiz

from .serializers import QuizSerializer, QuizUpdateSerializer
from .utils import get_quiz_for_user_or_raise


class QuizListView(APIView):
    """Return all quizzes of the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        quizzes = Quiz.objects.filter(user=request.user).prefetch_related('questions')
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuizDetailView(APIView):
    """Return, update, or delete one quiz of the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        quiz = get_quiz_for_user_or_raise(request.user, quiz_id)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, quiz_id):
        quiz = get_quiz_for_user_or_raise(request.user, quiz_id)
        serializer = QuizUpdateSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = QuizSerializer(quiz)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, quiz_id):
        quiz = get_quiz_for_user_or_raise(request.user, quiz_id)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quizzes.models import Question, Quiz

from .gemini_service import GeminiQuizGenerationService
from .serializers import QuizCreateSerializer, QuizSerializer, QuizUpdateSerializer
from .utils import get_quiz_for_user_or_raise, normalize_youtube_url


class QuizListView(APIView):
    """Return all quizzes of the authenticated user or create a new quiz."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        quizzes = Quiz.objects.filter(user=request.user).prefetch_related('questions')
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        normalized_url = normalize_youtube_url(serializer.validated_data['url'])

        transcript = '''
Python is a high-level programming language known for its readability.
It is widely used for web development, data analysis, automation, and artificial intelligence.
Python uses indentation to define code blocks instead of curly braces.
Variables in Python do not need an explicit type declaration.
Lists are mutable, while tuples are immutable.
A function is defined with the def keyword.
Dictionaries store data as key-value pairs.
Python supports object-oriented programming.
The package manager for Python is called pip.
Virtual environments help isolate project dependencies.
'''.strip()

        gemini_service = GeminiQuizGenerationService()
        quiz_data = gemini_service.generate_quiz_data(transcript)

        with transaction.atomic():
            quiz = Quiz.objects.create(
                user=request.user,
                title=quiz_data['title'],
                description=quiz_data['description'],
                video_url=normalized_url,
            )

            questions = [
                Question(
                    quiz=quiz,
                    question_title=question_data['question_title'],
                    question_options=question_data['question_options'],
                    answer=question_data['answer'],
                )
                for question_data in quiz_data['questions']
            ]

            Question.objects.bulk_create(questions)

        quiz = Quiz.objects.prefetch_related('questions').get(pk=quiz.pk)
        response_serializer = QuizSerializer(quiz)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


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
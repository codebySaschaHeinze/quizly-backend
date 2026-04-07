from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quizzes.models import Question, Quiz

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

        with transaction.atomic():
            quiz = Quiz.objects.create(
                user=request.user,
                title='Temporary quiz title',
                description='Temporary quiz description',
                video_url=normalized_url,
            )

            Question.objects.bulk_create(
                [
                    Question(
                        quiz=quiz,
                        question_title='Temporary question 1',
                        question_options=[
                            'Option A',
                            'Option B',
                            'Option C',
                            'Option D',
                        ],
                        answer='Option A',
                    ),
                    Question(
                        quiz=quiz,
                        question_title='Temporary question 2',
                        question_options=[
                            'Answer 1',
                            'Answer 2',
                            'Answer 3',
                            'Answer 4',
                        ],
                        answer='Answer 2',
                    ),
                    Question(
                        quiz=quiz,
                        question_title='Temporary question 3',
                        question_options=[
                            'Choice One',
                            'Choice Two',
                            'Choice Three',
                            'Choice Four',
                        ],
                        answer='Choice Three',
                    ),
                ]
            )

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
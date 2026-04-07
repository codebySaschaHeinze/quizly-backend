from rest_framework import serializers

from quizzes.models import Question, Quiz


class QuestionSerializer(serializers.ModelSerializer):
    """Serialize quiz questions."""

    class Meta:
        model = Question
        fields = [
            'id',
            'question_title',
            'question_options',
            'answer',
            'created_at',
            'updated_at',
        ]


class QuizSerializer(serializers.ModelSerializer):
    """Serialize quizzes with nested questions."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id',
            'title',
            'description',
            'created_at',
            'updated_at',
            'video_url',
            'questions',
        ]


class QuizUpdateSerializer(serializers.ModelSerializer):
    """Serialize partial quiz updates."""

    class Meta:
        model = Quiz
        fields = [
            'title',
            'description',
        ]


class QuizCreateSerializer(serializers.Serializer):
    """Validate quiz creation input."""

    url = serializers.URLField()
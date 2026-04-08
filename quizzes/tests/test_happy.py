from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from quizzes.models import Question, Quiz

User = get_user_model()


class QuizCreateHappyTests(APITestCase):
    """Happy path tests for quiz creation."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test1234',
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/quizzes/'

    @patch('quizzes.api.views.GeminiQuizGenerationService.generate_quiz_data')
    @patch('quizzes.api.views.AudioTranscriptionService.transcribe_audio')
    @patch('quizzes.api.views.YouTubeAudioService.download_audio')
    def test_create_quiz_returns_201_and_saves_quiz_with_questions(
        self,
        mock_download_audio,
        mock_transcribe_audio,
        mock_generate_quiz_data,
    ):
        mock_audio_path = type(
            'MockAudioPath',
            (),
            {
                'exists': lambda self: True,
                'unlink': lambda self: None,
            },
        )()
        mock_download_audio.return_value = mock_audio_path
        mock_transcribe_audio.return_value = 'This is a transcript.'

        mock_generate_quiz_data.return_value = {
            'title': 'Python Basics Quiz',
            'description': 'A short quiz about Python basics.',
            'questions': [
                {
                    'question_title': f'Question {index}',
                    'question_options': [
                        'Option A',
                        'Option B',
                        'Option C',
                        'Option D',
                    ],
                    'answer': 'Option A',
                }
                for index in range(1, 11)
            ],
        }

        response = self.client.post(
            self.url,
            {'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quiz.objects.count(), 1)

        quiz = Quiz.objects.first()
        self.assertEqual(quiz.user, self.user)
        self.assertEqual(quiz.title, 'Python Basics Quiz')
        self.assertEqual(
            quiz.video_url,
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        )
        self.assertEqual(quiz.questions.count(), 10)

        self.assertEqual(response.data['title'], 'Python Basics Quiz')
        self.assertEqual(len(response.data['questions']), 10)
        self.assertEqual(
            response.data['questions'][0]['question_title'],
            'Question 1',
        )


class QuizCrudHappyTests(APITestCase):
    """Happy path tests for quiz CRUD endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test1234',
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='test1234',
        )

        self.quiz_one = Quiz.objects.create(
            user=self.user,
            title='Quiz One',
            description='First quiz',
            video_url='https://www.youtube.com/watch?v=aaaaaaaaaaa',
        )
        self.quiz_two = Quiz.objects.create(
            user=self.user,
            title='Quiz Two',
            description='Second quiz',
            video_url='https://www.youtube.com/watch?v=bbbbbbbbbbb',
        )
        self.foreign_quiz = Quiz.objects.create(
            user=self.other_user,
            title='Foreign Quiz',
            description='Not owned by test user',
            video_url='https://www.youtube.com/watch?v=ccccccccccc',
        )

        Question.objects.create(
            quiz=self.quiz_one,
            question_title='Question 1',
            question_options=['A', 'B', 'C', 'D'],
            answer='A',
        )
        Question.objects.create(
            quiz=self.quiz_one,
            question_title='Question 2',
            question_options=['A', 'B', 'C', 'D'],
            answer='B',
        )
        Question.objects.create(
            quiz=self.quiz_two,
            question_title='Question 3',
            question_options=['A', 'B', 'C', 'D'],
            answer='C',
        )
        Question.objects.create(
            quiz=self.foreign_quiz,
            question_title='Foreign Question',
            question_options=['A', 'B', 'C', 'D'],
            answer='D',
        )

        self.client.force_authenticate(user=self.user)
        self.list_url = '/api/quizzes/'

    def test_get_quiz_list_returns_only_owned_quizzes(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        returned_ids = {item['id'] for item in response.data}
        self.assertIn(self.quiz_one.id, returned_ids)
        self.assertIn(self.quiz_two.id, returned_ids)
        self.assertNotIn(self.foreign_quiz.id, returned_ids)

    def test_get_quiz_detail_returns_owned_quiz_with_questions(self):
        response = self.client.get(f'/api/quizzes/{self.quiz_one.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.quiz_one.id)
        self.assertEqual(response.data['title'], 'Quiz One')
        self.assertEqual(len(response.data['questions']), 2)
        self.assertEqual(
            response.data['questions'][0]['question_title'],
            'Question 1',
        )

    def test_patch_quiz_updates_title_and_description(self):
        response = self.client.patch(
            f'/api/quizzes/{self.quiz_one.id}/',
            {
                'title': 'Updated Quiz Title',
                'description': 'Updated quiz description',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.quiz_one.refresh_from_db()
        self.assertEqual(self.quiz_one.title, 'Updated Quiz Title')
        self.assertEqual(self.quiz_one.description, 'Updated quiz description')

        self.assertEqual(response.data['title'], 'Updated Quiz Title')
        self.assertEqual(
            response.data['description'],
            'Updated quiz description',
        )
        self.assertEqual(len(response.data['questions']), 2)

    def test_delete_quiz_and_removes_quiz_returns_204(self):
        response = self.client.delete(f'/api/quizzes/{self.quiz_one.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(pk=self.quiz_one.id).exists())
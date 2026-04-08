from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from quizzes.models import Quiz

User = get_user_model()


class QuizCreateUnhappyTests(APITestCase):
    """Unhappy path tests for quiz creation."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test1234',
        )
        self.url = '/api/quizzes/'

    def test_create_quiz_without_auth_returns_401(self):
        response = self.client.post(
            self.url,
            {'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Quiz.objects.count(), 0)

    def test_create_quiz_with_invalid_youtube_url_returns_400(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {'url': 'https://example.com/video'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['url'], 'Invalid YouTube URL.')
        self.assertEqual(Quiz.objects.count(), 0)

    @patch('quizzes.api.views.GeminiQuizGenerationService.generate_quiz_data')
    @patch('quizzes.api.views.AudioTranscriptionService.transcribe_audio')
    @patch('quizzes.api.views.YouTubeAudioService.download_audio')
    def test_create_quiz_when_generation_fails_returns_500(
        self,
        mock_download_audio,
        mock_transcribe_audio,
        mock_generate_quiz_data,
    ):
        self.client.force_authenticate(user=self.user)

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
        mock_generate_quiz_data.side_effect = Exception('Gemini crashed.')

        response = self.client.post(
            self.url,
            {'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        self.assertEqual(response.data['detail'], 'Quiz generation failed.')
        self.assertEqual(Quiz.objects.count(), 0)


class QuizCrudUnhappyTests(APITestCase):
    """Unhappy path tests for quiz CRUD endpoints."""

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

        self.owned_quiz = Quiz.objects.create(
            user=self.user,
            title='Owned Quiz',
            description='Owned quiz description',
            video_url='https://www.youtube.com/watch?v=aaaaaaaaaaa',
        )
        self.foreign_quiz = Quiz.objects.create(
            user=self.other_user,
            title='Foreign Quiz',
            description='Foreign quiz description',
            video_url='https://www.youtube.com/watch?v=bbbbbbbbbbb',
        )

        self.list_url = '/api/quizzes/'
        self.missing_quiz_id = 999999

    def test_get_quiz_list_without_auth_returns_401(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_quiz_detail_without_auth_returns_401(self):
        response = self.client.get(f'/api/quizzes/{self.owned_quiz.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_quiz_detail_for_foreign_quiz_returns_403(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f'/api/quizzes/{self.foreign_quiz.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_quiz_detail_for_missing_quiz_returns_404(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f'/api/quizzes/{self.missing_quiz_id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_quiz_without_auth_returns_401(self):
        response = self.client.patch(
            f'/api/quizzes/{self.owned_quiz.id}/',
            {'title': 'Updated Title'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_quiz_for_foreign_quiz_returns_403(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f'/api/quizzes/{self.foreign_quiz.id}/',
            {'title': 'Updated Title'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_quiz_for_missing_quiz_returns_404(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f'/api/quizzes/{self.missing_quiz_id}/',
            {'title': 'Updated Title'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_quiz_without_auth_returns_401(self):
        response = self.client.delete(f'/api/quizzes/{self.owned_quiz.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_quiz_for_foreign_quiz_returns_403(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(f'/api/quizzes/{self.foreign_quiz.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_quiz_for_missing_quiz_returns_404(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(f'/api/quizzes/{self.missing_quiz_id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
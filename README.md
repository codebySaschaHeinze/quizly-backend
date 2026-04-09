# Quizly Backend (Django REST Framework)

Backend API for the Quizly frontend.
The project creates quizzes from YouTube videos by downloading audio, transcribing it locally with Whisper, and generating quiz data with Gemini.

## Tech Stack

- Python
- Django
- Django REST Framework (DRF)
- Simple JWT
- JWT in HTTP-only cookies
- django-cors-headers
- python-dotenv
- yt-dlp
- FFmpeg
- OpenAI Whisper
- Google GenAI SDK (Gemini)
- SQLite (development)

## Key Features

- User registration and login
- Authentication via JWT in HTTP-only cookies
- Refresh token rotation and blacklist support
- Quiz generation from YouTube videos
- Local audio transcription with Whisper
- AI-based quiz generation with Gemini
- Quiz CRUD for the authenticated user
- Nested quiz questions in API responses
- Django admin integration for users, quizzes, and questions

## How Quiz Generation Works

1. The user sends a YouTube URL to the backend.
2. The backend validates and normalizes the URL.
3. `yt-dlp` downloads the audio.
4. Whisper transcribes the local audio file.
5. Gemini generates structured quiz JSON.
6. The backend validates the generated data.
7. The quiz and its questions are stored in the database.
8. The created quiz is returned in the API response.

## API Base URL

```text
http://127.0.0.1:8000/api/
```

## Endpoints

### Auth

#### POST `/api/register/`

Request body:

```json
{
  "username": "your_username",
  "email": "your_email@example.com",
  "password": "your_password",
  "confirmed_password": "your_password"
}
```

Success response:

```json
{
  "detail": "User created successfully!"
}
```

#### POST `/api/login/`

Request body:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Success response:

```json
{
  "detail": "Login successfully!",
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "your_email@example.com"
  }
}
```

#### POST `/api/logout/`

Auth required.

Success response:

```json
{
  "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
}
```

#### POST `/api/token/refresh/`

Uses the refresh token from the HTTP-only cookie.

Success response:

```json
{
  "detail": "Token refreshed"
}
```

### Quizzes

#### GET `/api/quizzes/`

Auth required.
Returns all quizzes of the authenticated user.

#### POST `/api/quizzes/`

Auth required.

Request body:

```json
{
  "url": "https://www.youtube.com/watch?v=example"
}
```

Success response:

```json
{
  "id": 1,
  "title": "Quiz title",
  "description": "Short quiz description",
  "created_at": "2026-04-08T12:41:19.100776Z",
  "updated_at": "2026-04-08T12:41:19.100804Z",
  "video_url": "https://www.youtube.com/watch?v=example",
  "questions": [
    {
      "id": 1,
      "question_title": "Question text",
      "question_options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "answer": "Option 1",
      "created_at": "2026-04-08T12:41:19.106387Z",
      "updated_at": "2026-04-08T12:41:19.106475Z"
    }
  ]
}
```

Notes:

- The current frontend expects `answer` to be included in the quiz response.
- Quiz generation can take some time, especially for longer videos.
- If Gemini is temporarily overloaded, the backend returns `503 Service Unavailable`.

#### GET `/api/quizzes/<quiz_id>/`

Auth required.

- `200` if the quiz belongs to the current user
- `403` if the quiz exists but belongs to another user
- `404` if the quiz does not exist

#### PATCH `/api/quizzes/<quiz_id>/`

Auth required.
Only `title` and `description` can be updated.

Request body example:

```json
{
  "title": "Updated title",
  "description": "Updated description"
}
```

#### DELETE `/api/quizzes/<quiz_id>/`

Auth required.
Returns `204 No Content` on success.

## Authentication Notes

This project uses JWT with HTTP-only cookies.
That means:

- the frontend must send requests with credentials
- the backend handles access and refresh tokens via cookies
- logout blacklists the current refresh token
- refresh rotates the refresh token and issues a new access token

## Data Model

### User

- custom Django user model
- unique email
- username-based login

### Quiz

- belongs to one user
- stores title, description, normalized `video_url`
- has many questions

### Question

- belongs to one quiz
- stores `question_title`, `question_options`, `answer`

## Project Structure

```text
quizly/
├─ core/
│  ├─ __init__.py
│  ├─ settings.py
│  ├─ urls.py
│  ├─ asgi.py
│  └─ wsgi.py
│
├─ users/
│  ├─ migrations/
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ authentication.py
│  │  ├─ serializers.py
│  │  ├─ urls.py
│  │  ├─ utils.py
│  │  └─ views.py
│  ├─ admin.py
│  ├─ apps.py
│  └─ models.py
│
├─ quizzes/
│  ├─ migrations/
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ gemini_service.py
│  │  ├─ serializers.py
│  │  ├─ transcription_service.py
│  │  ├─ urls.py
│  │  ├─ utils.py
│  │  ├─ views.py
│  │  └─ youtube_service.py
│  ├─ tests/
│  │  ├─ __init__.py
│  │  ├─ test_happy.py
│  │  └─ test_unhappy.py
│  ├─ admin.py
│  ├─ apps.py
│  └─ models.py
│
├─ manage.py
├─ .env
├─ .gitignore
├─ README.md
└─ requirements.txt
```

## Local Setup

### 1. Clone the repository

```text
git clone https://github.com/codebySaschaHeinze/quizly.git
cd quizly
```

### 2. Create and activate a virtual environment

Windows (PowerShell):

```text
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```text
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```text
pip install -r requirements.txt
```

### 4. Install FFmpeg

FFmpeg must be available in your system `PATH`.

On Windows, verify it with:

```text
ffmpeg -version
```

If this command fails, Whisper and audio processing will not work.

### 5. Create the `.env` file

Create a local `.env` file in the project root.

Example:

```env
SECRET_KEY='your_new_django_secret_key'
DEBUG=True
GEMINI_API_KEY='your_gemini_api_key'
```

Notes:

- keep quotes if your key contains `#`
- do not commit `.env`
- after changing `SECRET_KEY`, old JWT tokens become invalid

### 6. Run migrations

```text
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a superuser (optional but recommended)

```text
python manage.py createsuperuser
```

### 8. Start the development server

```text
python manage.py runserver
```

Backend base URL:

```text
http://127.0.0.1:8000/api/
```

## Frontend Integration Notes

If you use the provided frontend with Live Server:

- make sure the Django server is running
- make sure the frontend origin is included in `CORS_ALLOWED_ORIGINS`
- make sure the same host style is used consistently (`127.0.0.1` vs `localhost`)

Typical allowed origins in development:

```python
CORS_ALLOWED_ORIGINS = [
    'http://127.0.0.1:5500',
    'http://localhost:5500',
    'http://127.0.0.1:3000',
    'http://localhost:3000',
]
```

If your Live Server runs on a different port, add that exact origin to both:

- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`

## Running Tests

Run all quiz tests:

```text
python manage.py test quizzes.tests
```

Run only happy path tests:

```text
python manage.py test quizzes.tests.test_happy
```

Run only unhappy path tests:

```text
python manage.py test quizzes.tests.test_unhappy
```

## Known Development Notes

- Quiz generation depends on external services and local tools.
- Gemini may temporarily return `503` during periods of high demand.
- Longer videos take noticeably more time to process.
- Temporary audio files are deleted after quiz generation.
- The development server is for local development only.

## License

Educational / internal project.
Adjust if needed.

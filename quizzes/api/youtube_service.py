from pathlib import Path
from uuid import uuid4

from yt_dlp import YoutubeDL


class YouTubeAudioService:
    """Download audio from a YouTube video."""

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.download_dir = self.base_dir / 'tmp' / 'quiz_audio'
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def build_output_template(self):
        """Build a unique output template for yt-dlp downloads."""
        filename = f'{uuid4()}.%(ext)s'
        return str(self.download_dir / filename)

    def get_download_options(self):
        """Return yt-dlp options for audio download."""
        return {
            'format': 'bestaudio/best',
            'outtmpl': self.build_output_template(),
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

    def download_audio(self, video_url):
        """Download audio and return the local file path."""
        options = self.get_download_options()

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)

        return Path(file_path)
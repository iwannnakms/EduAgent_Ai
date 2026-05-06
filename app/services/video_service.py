import subprocess
import re
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from app.core.config import get_settings
from app.utils.gemini_client import get_gemini_client
from app.utils.gemini_models import resolve_model

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_gemini_client()
        self.audio_model_name = resolve_model(self.settings.gemini_audio_model, "generateContent")
        self.chat_model_name = resolve_model(self.settings.gemini_chat_model, "generateContent")

    def _extract_video_id(self, youtube_url: str) -> Optional[str]:
        regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(regex, youtube_url)
        return match.group(1) if match else None

    def _get_youtube_transcript(self, youtube_url: str, target_language: str = "en") -> Optional[str]:
        video_id = self._extract_video_id(youtube_url)
        if not video_id:
            return None
        
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[target_language, 'en'])
            return " ".join([t['text'] for t in transcript_list])
        except (TranscriptsDisabled, NoTranscriptFound, Exception):
            return None

    def _extract_audio(self, youtube_url: str) -> Path:
        output_stem = Path(self.settings.temp_dir) / f"yt_{uuid4()}"
        output_template = str(output_stem) + ".%(ext)s"
        
        cookies_path = Path("cookies.txt")
        command = [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--no-playlist",
            "-o",
            output_template,
            youtube_url,
        ]
        
        if cookies_path.exists():
            command.extend(["--cookies", str(cookies_path)])
            
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            error_msg = f"yt-dlp failed with exit code {e.returncode}.\nSTDERR: {e.stderr}"
            if "confirm you’re not a bot" in e.stderr:
                error_msg += "\n\nHint: YouTube is blocking this request. Try adding a 'cookies.txt' file."
            raise RuntimeError(error_msg) from e

        matches = list(Path(self.settings.temp_dir).glob(f"{output_stem.name}.*"))
        if not matches:
            raise FileNotFoundError("Audio extraction failed: no output file found.")
        return matches[0]

    def transcribe_audio(self, audio_path: Path, target_language: str | None = "en") -> str:
        # Upload the file using the new SDK
        try:
            # Explicitly set mime_type as required by the new SDK
            uploaded_file = self.client.files.upload(
                file=str(audio_path),
                config={'mime_type': 'audio/mpeg'}
            )
            
            prompt = (
                "Transcribe this educational audio faithfully. "
                "Use clear paragraph breaks and punctuation. "
                "If there are distinct speakers or sections, indicate them with bold headers. "
                f"Target language: {target_language or 'auto-detect'}."
            )
            
            response = self.client.models.generate_content(
                model=self.audio_model_name,
                contents=[prompt, uploaded_file]
            )
            
            # Cleanup: File is automatically deleted after some time or can be managed
            return response.text or ""
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise RuntimeError(f"Transcription failed: {str(e)}")

    def summarize_transcript(self, transcript: str, max_summary_tokens: int = 350) -> str:
        prompt = (
            "Summarize the following educational transcript into high-quality study notes using Markdown. "
            "Structure it exactly like this:\n"
            "1. # Title: A concise title for the video\n"
            "2. ## Overview: A brief 2-3 sentence high-level summary.\n"
            "3. ## Key Takeaways: A bulleted list of the most important points.\n"
            "4. ## Detailed Summary: Break down the content into logical sections with sub-headers.\n"
            f"Aim for around {max_summary_tokens} tokens worth of detail.\n\n"
            f"Transcript:\n{transcript}"
        )
        try:
            response = self.client.models.generate_content(
                model=self.chat_model_name,
                contents=prompt
            )
            return response.text or "No summary generated."
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return "Failed to generate summary."

    def process_video(self, youtube_url: str, target_language: str | None, max_summary_tokens: int) -> dict:
        transcript = self._get_youtube_transcript(youtube_url, target_language or "en")
        
        if not transcript:
            audio_path = self._extract_audio(youtube_url=youtube_url)
            try:
                transcript = self.transcribe_audio(audio_path=audio_path, target_language=target_language)
            finally:
                if audio_path.exists():
                    audio_path.unlink(missing_ok=True)
        
        if not transcript:
            raise RuntimeError("Could not retrieve or generate a transcript for this video.")

        summary = self.summarize_transcript(transcript=transcript, max_summary_tokens=max_summary_tokens)
        return {
            "youtube_url": youtube_url,
            "transcript": transcript,
            "summary": summary,
        }

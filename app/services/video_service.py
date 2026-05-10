import re
import logging
import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

import yt_dlp
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
        
        # Robust format selection: try m4a, then mp4, then any audio
        ydl_opts = {
            'format': 'ba[ext=m4a]/ba[ext=mp4]/ba/best',
            'outtmpl': str(output_stem) + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'postprocessors': [],
            'prefer_ffmpeg': False,
            'fixup': 'never',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            # Broaden clients to see more formats
            'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web_embedded']}},
        }
        
        cookies_path = Path("cookies.txt")
        if cookies_path.exists():
            ydl_opts['cookiefile'] = str(cookies_path)

        try:
            logger.info(f"Extracting native audio (flexible format). URL: {youtube_url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
        except Exception as e:
            err_msg = str(e)
            logger.error(f"yt-dlp failure: {err_msg}")
            if "confirm you" in err_msg or "429" in err_msg:
                raise RuntimeError("YouTube is blocking this cloud server. Please try a different video or try again later.")
            raise RuntimeError(f"Failed to extract audio: {err_msg}")

        # Find the resulting file and its actual extension
        matches = list(Path(self.settings.temp_dir).glob(f"{output_stem.name}.*"))
        if not matches:
            raise FileNotFoundError("Audio extraction failed: file was not saved.")
        return matches[0]

    def transcribe_audio(self, audio_path: Path, target_language: str | None = "en") -> str:
        # Map extension to correct Gemini mime type
        ext = audio_path.suffix.lower()
        mime_type = 'audio/mp4' if ext in ['.m4a', '.mp4'] else 'audio/mpeg'
        if ext == '.wav': mime_type = 'audio/wav'
        
        try:
            uploaded_file = self.client.files.upload(
                file=str(audio_path),
                config={'mime_type': mime_type}
            )
            prompt = (
                "Transcribe this educational audio faithfully. "
                "Use clear paragraph breaks and punctuation. "
                f"Target language: {target_language or 'auto-detect'}."
            )
            response = self.client.models.generate_content(
                model=self.audio_model_name,
                contents=[prompt, uploaded_file]
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise RuntimeError(f"Transcription failed: {str(e)}")

    def summarize_transcript(self, transcript: str, max_summary_tokens: int = 350) -> str:
        prompt = (
            "Summarize the transcript into study notes using Markdown.\n"
            "Structure: # Title, ## Overview, ## Key Takeaways, ## Detailed Summary.\n"
            f"Limit: {max_summary_tokens} tokens.\n\nTranscript:\n{transcript}"
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
                if audio_path and audio_path.exists():
                    audio_path.unlink(missing_ok=True)
        if not transcript:
            raise RuntimeError("Could not retrieve transcript.")
        summary = self.summarize_transcript(transcript=transcript, max_summary_tokens=max_summary_tokens)
        return {"youtube_url": youtube_url, "transcript": transcript, "summary": summary}

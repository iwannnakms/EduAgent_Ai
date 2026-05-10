import subprocess
import re
import logging
import shutil
import os
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
        # Native m4a download completely bypasses the need for ffmpeg/ffprobe
        output_template = str(output_stem) + ".m4a"
        
        # Robustly find node for JS runtime
        node_bin = shutil.which("node") or shutil.which("nodejs")
        js_runtime_args = ["--js-runtimes", "node"] if node_bin else []
        
        command = [
            "yt-dlp",
            "-f", "ba[ext=m4a]",
            "--no-playlist",
            # 'ios' is currently the most robust client for bypassing bot detection
            "--extractor-args", "youtube:player_client=ios,web_embedded",
            "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "--referer", "https://www.youtube.com/",
            "--no-check-certificates",
            "-o",
            output_template,
        ]
        
        command.extend(js_runtime_args)
        command.append(youtube_url)
        
        cookies_path = Path("cookies.txt")
        if cookies_path.exists():
            command.insert(-1, "--cookies")
            command.insert(-1, str(cookies_path))
            
        try:
            logger.info(f"Extracting raw m4a audio without ffmpeg. URL: {youtube_url}")
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"yt-dlp failed: {e.stderr}")
            if "confirm you’re not a bot" in e.stderr or "429" in e.stderr:
                error_msg = "YouTube is currently blocking this server due to bot detection. Try again later or use a video with existing captions."
            else:
                error_msg = "Failed to extract audio from this video. It may be restricted, live, or unsupported."
            raise RuntimeError(error_msg) from e

        matches = list(Path(self.settings.temp_dir).glob(f"{output_stem.name}.*"))
        if not matches:
            raise FileNotFoundError("Audio extraction failed: no output file found.")
        return matches[0]

    def transcribe_audio(self, audio_path: Path, target_language: str | None = "en") -> str:
        try:
            # FIX: Upload native m4a file
            uploaded_file = self.client.files.upload(
                file=str(audio_path),
                config={'mime_type': 'audio/mp4'}
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
            "Summarize the following educational transcript into study notes using Markdown.\n"
            "Structure:\n1. # Title\n2. ## Overview\n3. ## Key Takeaways\n4. ## Detailed Summary\n"
            f"Aim for {max_summary_tokens} tokens.\n\nTranscript:\n{transcript}"
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

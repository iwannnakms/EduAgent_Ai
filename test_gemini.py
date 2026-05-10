from app.utils.gemini_client import get_gemini_client
import sys

client = get_gemini_client()
try:
    f = client.files.upload(file="test_audio.m4a", config={'mime_type': 'audio/mp4'})
    res = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=["Transcribe this.", f]
    )
    print("SUCCESS:", res.text[:100])
except Exception as e:
    print("ERROR:", e)

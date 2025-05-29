import openai
from typing import List
from app.config import OPENAI_API_KEY
openai.api_key = OPENAI_API_KEY

#OpenAI Whisper API로 음성 파일을 자막(segments)으로 변환
#반환값: [{"start": float, "end": float, "text": str}, ...]
def transcribe_audio(audio_path: str) -> List[dict]:
    with open(audio_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    
    segments = transcript.get("segments", [])
    return segments

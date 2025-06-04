from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
import time
from pytubefix import YouTube

from app.whisper_utils import transcribe_audio
from app.translate import translate_segments_batch
from app.srt_generator import generate_srt
from app.s3_uploader import upload_to_s3

app = FastAPI()

class AudioRequest(BaseModel):
    userId: int
    videoUrl: str

def extract_youtube_video_id(url: str) -> str:
    import urllib.parse as urlparse
    query = urlparse.urlparse(url).query
    params = urlparse.parse_qs(query)
    return params.get("v", ["unknown"])[0]

def cleanup_files(audio_path: str, srt_path: str):
    for fpath in [audio_path, srt_path]:
        if fpath and os.path.exists(fpath):
            try:
                os.remove(fpath)
                print(f"Deleted file: {fpath}")
            except Exception as e:
                print(f"파일 삭제 실패 ({fpath}): {e}")

@app.post("/process-audio")
async def process_audio(request: AudioRequest, background_tasks: BackgroundTasks):
    user_id = request.userId
    video_url = request.videoUrl
    video_id = extract_youtube_video_id(video_url)
    filename_prefix = f"{user_id}-{video_id}"
    audio_path = f"{filename_prefix}.mp3"
    srt_path = None

    try:
        print("#1. YouTube에서 오디오 다운로드")
        yt = YouTube(video_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        output_path = "./"
        os.makedirs(output_path, exist_ok=True)
        audio_file = audio_stream.download(output_path)

        try:
            os.rename(audio_file, audio_path)
        except Exception as e:
            print(f"파일 이름 변경 실패: {e}")
            audio_path = audio_file  # fallback

        print("#2. Whisper 자막 추출")
        segments = None
        for attempt in range(3):
            try:
                segments = transcribe_audio(audio_path)
                break
            except Exception as e:
                print(f"Whisper API 실패 시도 {attempt + 1}: {e}")
                if attempt == 2:
                    raise HTTPException(status_code=502, detail="Whisper API 호출 실패. 잠시 후 다시 시도하세요.")
                time.sleep(2)

        print("#3. GPT 번역")
        translated = translate_segments_batch(segments)

        print("#4. SRT 생성")
        srt_path = generate_srt(translated, filename_prefix)

        print("#5. S3 업로드")
        s3_key = f"{filename_prefix}.srt"
        upload_to_s3(srt_path, s3_key)

        print("#6. SRT 파일 반환")
        background_tasks.add_task(cleanup_files, audio_path, srt_path)

        return FileResponse(
            path=srt_path,
            media_type="application/x-subrip",
            filename=s3_key
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 처리 중 오류 발생: {str(e)}")

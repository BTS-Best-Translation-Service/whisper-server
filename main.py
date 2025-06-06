from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import time
from pytubefix import YouTube

from app.whisper_utils import transcribe_audio
from app.translate import translate_segments_batch
from app.srt_generator import generate_srt, parse_srt
from app.s3_uploader import upload_to_s3
from app.dlp_utils import download_audio_with_ytdlp

example_list = ["https://www.youtube.com/watch?v=lzWF94mipFY", ...]

app = FastAPI()

class AudioRequest(BaseModel):
    videoTitle: str
    videoUrl: str

def cleanup_files(audio_path: str, srt_path: str):
    for fpath in [audio_path, srt_path]:
        if fpath and os.path.exists(fpath):
            abs_path = os.path.abspath(fpath)
            example_dir = os.path.abspath('./example/')
            if abs_path.startswith(example_dir):
                print(f"예제 파일은 삭제하지 않음: {fpath}")
                continue

            try:
                os.remove(fpath)
                print(f"Deleted file: {fpath}")
            except Exception as e:
                print(f"파일 삭제 실패 ({fpath}): {e}")

@app.post("/process-audio")
async def process_audio(request: AudioRequest, background_tasks: BackgroundTasks):
    video_title = request.videoTitle
    video_url = request.videoUrl
    srt_path = None

    
    print("#1. YouTube에서 오디오 다운로드")
    if (video_url in example_list): #예제 영상이 있을 때
        audio_path = f"./example/{video_title}.mp3"

    else: 
        audio_path = download_audio_with_ytdlp(video_url, video_title)

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
    srt_path = generate_srt(translated, video_title)

    print("#5. S3 업로드")
    s3_key = f"{video_title}.srt"
    s3_url = upload_to_s3(srt_path, s3_key)

    print("#6. SRT 파일 반환")
    background_tasks.add_task(cleanup_files, audio_path, srt_path)

    parsed_srt = parse_srt(srt_path)

    return JSONResponse(
        status_code=200,
        content={
            "s3Link": s3_url,
            "srt": parsed_srt
        },
        media_type="application/json; charset=utf-8"
    )
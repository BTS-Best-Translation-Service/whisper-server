from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from app.whisper_utils import transcribe_audio
from app.translate import translate_segments_batch
from app.srt_generator import generate_srt
from app.s3_uploader import upload_to_s3
from fastapi.responses import FileResponse
import tempfile
import shutil
import os

app = FastAPI()


@app.post("/process-audio")
async def process_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...), video_id: str = Form(...)):
    print("#1. 원본 오디오 파일 임시 저장")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        converted_audio_path = tmp.name

    print("#2. Whisper 자막 추출")
    segments = transcribe_audio(converted_audio_path)

    print("#3. 변환된 파일 삭제 (안전하게 Whisper 이후)")
    os.remove(converted_audio_path)

    print("# 4. GPT 번역")
    translated = translate_segments_batch(segments)

    print("#5. SRT 파일 생성")
    srt_path = generate_srt(translated, video_id)

    print("#6. S3 업로드 후에 로컬 파일 삭제")
    s3_url = upload_to_s3(srt_path, f"{video_id}.srt")
    background_tasks.add_task(os.remove, srt_path)
    

    print("#7. 파일 직접 응답으로 반환")
    return FileResponse(
        path=srt_path,
        media_type="application/x-subrip", 
        filename=f"{video_id}.srt"
    )


import srt
from typing import List
import datetime
import tempfile

#번역된 segment 리스트를 SRT 형식으로 변환하고 임시 파일 경로 반환
def generate_srt(segments: List[dict], video_id: str) -> str:
    subtitles = []
    for idx, seg in enumerate(segments):
        start = datetime.timedelta(seconds=seg["start"])
        end = datetime.timedelta(seconds=seg["end"])
        content = f"{seg['translation']}\n({seg['text']})"
        subtitle = srt.Subtitle(index=idx+1, start=start, end=end, content=content)
        subtitles.append(subtitle)

    srt_content = srt.compose(subtitles)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".srt", mode="w", encoding="utf-8") as f:
        f.write(srt_content)
        return f.name

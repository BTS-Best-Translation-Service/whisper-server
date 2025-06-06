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


import re

def parse_srt(srt_path):
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)\n(.+?)(?=\n\d+\n|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)

    srt_list = []
    for _, start, end, translation, original in matches:
        srt_list.append({
            "start": start.strip(),
            "end": end.strip(),
            "original": original.strip(),
            "translation": translation.strip(),
            "language": "en"  
        })

    return srt_list
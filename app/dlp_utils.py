import subprocess
import os

def download_audio_with_ytdlp(video_url: str, video_title: str) -> str:
    audio_path = f"{video_title}.mp3"
    try:
        # yt-dlp로 MP3 다운로드
        subprocess.run([
            "yt-dlp",
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", audio_path,
            "--cookies cookies.txt",
            video_url
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"yt-dlp 오디오 다운로드 실패: {e}")
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError("MP3 파일 생성 실패")
    
    return audio_path
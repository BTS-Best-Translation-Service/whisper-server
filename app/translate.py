import openai
from typing import List
from app.config import OPENAI_API_KEY


openai.api_key = OPENAI_API_KEY

def translate_segments_batch(segments: List[dict]) -> List[dict]:
    # 모든 문장 한꺼번에 연결
    all_texts = "\n".join([seg["text"] for seg in segments])
    
    prompt = (
        "Translate the following English sentences into natural and clear Korean, line by line.\n"
        + all_texts
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful translator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )
    
    # 번역 결과를 줄 단위로 분리
    translations = response['choices'][0]['message']['content'].strip().split('\n')
    
    translated_segments = []
    for seg, trans in zip(segments, translations):
        translated_segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
            "translation": trans.strip()
        })
    
    return translated_segments

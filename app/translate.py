import openai
from typing import List
from collections import defaultdict
from app.config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def translate_segments_batch(segments: List[dict]) -> List[dict]:
    """
    segments 내 같은 sentence_id를 가진 segment들을 하나의 문장으로 묶어서 번역 요청
    번역 결과도 문장별로 이어서 한 줄에 나오도록 GPT에 지시
    """
    grouped_texts = defaultdict(list)
    grouped_segments = defaultdict(list)
    for seg in segments:
        sid = seg.get("sentence_id", seg["start"])
        grouped_texts[sid].append(seg["text"])
        grouped_segments[sid].append(seg)

    sentences = [" ".join(parts) for sid, parts in sorted(grouped_texts.items())]

    prompt = (
        "Translate the following English sentences into natural and clear Korean. "
        "Each English sentence may be split into multiple parts, but translate each full sentence as one coherent sentence. "
        "Output the Korean translation one sentence per line, preserving the sentence order.\n"
        + "\n".join(sentences)
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful translator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    translations = response['choices'][0]['message']['content'].strip().split('\n')

    translated_segments = []
    for (sid, segs), translation in zip(sorted(grouped_segments.items()), translations):
        for seg in segs:
            translated_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "translation": translation.strip()
            })

    translated_segments.sort(key=lambda x: x["start"])
    return translated_segments

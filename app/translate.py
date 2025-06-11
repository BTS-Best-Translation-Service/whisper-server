import openai
import json
from typing import List
from collections import defaultdict
from app.config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def translate_segments_batch(segments: List[dict]) -> List[dict]:
    from uuid import uuid4
    import logging

    logging.basicConfig(level=logging.INFO)

    grouped_texts = defaultdict(list)
    grouped_segments = defaultdict(list)

    for seg in segments:
        sid = seg.get("sentence_id")
        if sid is None:
            sid = str(uuid4())  # sentence_id 없으면 UUID 부여
        grouped_texts[sid].append(seg["text"])
        grouped_segments[sid].append(seg)

    joined_sentences = {
        sid: " ".join(texts) for sid, texts in grouped_texts.items()
    }

    sentence_lines = "\n".join([f'{sid}: "{text}"' for sid, text in sorted(joined_sentences.items())])

    prompt = (
        "You are a translation engine. Given a list of English subtitle segments, produce a Korean translation for each full sentence, preserving order.\n"
        "1. First, reconstruct each sentence by joining the segments with the same sentence_id.\n"
        "2. Then, translate each reconstructed English sentence into natural, idiomatic Korean.\n"
        "3. Finally, output a JSON array of objects, each with:\n"
        '- "sentence_id": the original sentence_id\n'
        '- "translation": the full Korean sentence\n\n'
        "Do not include any extra text, only valid JSON.\n\n"
        "Example:\n\n"
        "English sentences (joined):\n"
        "1: “She’s supportive and she’s obviously giving, creative, you know?”\n"
        "2: “Like what more can I ask for?”\n\n"
        "Response:\n"
        "[\n"
        '{ "sentence_id": 1, "translation": "그녀는 든든한 지원군 같고, 분명 창의적인 사람이에요." },\n'
        '{ "sentence_id": 2, "translation": "이보다 더 바랄 게 있을까요?" }\n'
        "]\n\n"
        "English sentences (joined):\n"
        + sentence_lines
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful translator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    gpt_output = response['choices'][0]['message']['content'].strip()

    try:
        if gpt_output.startswith("```json"):
            gpt_output = gpt_output.strip("```json").strip("```").strip()
        translations = json.loads(gpt_output)
    except Exception as e:
        logging.error("❌ GPT 응답 파싱 실패")
        logging.error(gpt_output)
        raise ValueError(f"Failed to parse GPT translation output: {e}\n\nRaw Output:\n{gpt_output}")

    sid_to_translation = {str(t["sentence_id"]): t["translation"] for t in translations}
    translated_segments = []

    for sid, segs in grouped_segments.items():
        translated = sid_to_translation.get(str(sid), "")
        for seg in segs:
            translated_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "translation": translated,
                "sentence_id": sid
            })

    translated_segments.sort(key=lambda x: x["start"])
    return translated_segments

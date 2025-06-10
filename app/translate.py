import openai
from typing import List

def translate_segments_batch(segments: List[dict]) -> List[dict]:
    all_texts = "\n".join([seg["text"] for seg in segments])

    prompt = (
        "Translate the following English text into natural and clear Korean. "
        "The input text is provided line by line, but please be aware that some lines might be "
        "grammatically incomplete fragments that belong to a larger, continuous sentence. "
        "Your task is to translate this text naturally, ensuring that full sentences are translated cohesively, "
        "even if they span multiple input lines. "
        "It is CRUCIAL that your output maintains the *exact* same number of lines as the input, "
        "and each translated line must correspond directly to its respective input line's content. "
        "If an input line is a partial sentence, its translation should also be a partial sentence "
        "that naturally fits the overall translated sentence flow. "
        "Ensure perfect line-by-line alignment between the input and your translated output.\n"
        "\n"
        "Input text:\n"
        + all_texts
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 뛰어난 번역가이며, 자연스러운 문장 흐름을 유지하면서 줄 단위 매핑을 정확하게 수행하는 데 전문적입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    translations = response['choices'][0]['message']['content'].strip().split('\n')

    translated_segments = []
    for i, seg in enumerate(segments):
        translation_text = translations[i].strip() if i < len(translations) else ""

        translated_segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
            "translation": translation_text
        })

    return translated_segments
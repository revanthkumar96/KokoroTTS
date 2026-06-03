"""Read generated_text/topic.txt and render 9 blended UK voices."""
import os
import numpy as np
import soundfile as sf
import torch
from dotenv import load_dotenv

load_dotenv()

from kokoro import KPipeline

WEIGHT_PAIRS = [
    (10, 90), (20, 80), (30, 70), (40, 60),
    (50, 50), (60, 40), (70, 30), (80, 20), (90, 10),
]   # (% Emma female, % George male)

TEXT_PATH = "generated_text/topic.txt"
OUT_DIR = "output_uk_audio"
SAMPLE_RATE = 24000


def load_text() -> str:
    if not os.path.exists(TEXT_PATH):
        raise FileNotFoundError(
            f"{TEXT_PATH} not found. Run `python generate.py` first."
        )
    with open(TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_voices():
    v_emma = torch.load("voices/bf_emma.pt", map_location="cpu")
    v_george = torch.load("voices/bm_george.pt", map_location="cpu")
    return v_emma, v_george


def synth_to_array(pipeline, text, voice_tensor):
    chunks = [audio for _, _, audio in pipeline(text, voice=voice_tensor)]
    return np.concatenate(chunks) if len(chunks) > 1 else chunks[0]


def main():
    text = load_text()
    print(f"Text loaded: {len(text.split())} words")

    v_emma, v_george = load_voices()
    os.makedirs(OUT_DIR, exist_ok=True)
    pipeline = KPipeline(lang_code='b')

    for pct_f, pct_m in WEIGHT_PAIRS:
        w_f, w_m = pct_f / 100.0, pct_m / 100.0
        custom_voice = v_emma * w_f + v_george * w_m

        audio = synth_to_array(pipeline, text, custom_voice)

        out = os.path.join(OUT_DIR, f"blend_bf{pct_f}_bm{pct_m}.wav")
        sf.write(out, audio, SAMPLE_RATE)
        print(f"OK {out}  ({pct_f}% Emma / {pct_m}% George)")

    print(f"\nDone. Listen to the 9 files in {OUT_DIR}/ and pick your favourite blend.")


if __name__ == "__main__":
    main()

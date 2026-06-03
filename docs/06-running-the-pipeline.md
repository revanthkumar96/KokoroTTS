# 06 – Running the Pipeline (complete, copy‑paste scripts)

This doc gives you the **three full files** to create, plus the exact commands to run them.
Nothing here is a fragment — copy each block into the named file and go.

```
generate.py        # Step 1: LLM → generated_text/topic.txt   (~300 words)
download_voices.py # one-time: pull bf_emma.pt + bm_george.pt
tts_blend.py       # Step 2: blend 9 ratios → output_uk_audio/*.wav
```

---

## File 1 — `download_voices.py` (run once)

```python
"""Download the two UK voice tensors into ./voices/."""
import os, shutil
from huggingface_hub import hf_hub_download

VOICES = ["bf_emma", "bm_george"]

def main():
    os.makedirs("voices", exist_ok=True)
    for v in VOICES:
        src = hf_hub_download("hexgrad/Kokoro-82M", f"voices/{v}.pt")
        dst = f"voices/{v}.pt"
        shutil.copy(src, dst)
        print(f"✓ {dst}")

if __name__ == "__main__":
    main()
```

```bash
python download_voices.py
```

---

## File 2 — `generate.py` (LLM → ~300 words)

```python
"""Generate a 290–310 word British-English paragraph with Groq or Gemini."""
import os
import random
from dotenv import load_dotenv

load_dotenv()

TOPICS = [
    "the history and geography of the United Kingdom",
    "how tea culture shaped British daily life",
    "the future of renewable energy in coastal towns",
    "why public libraries still matter in the digital age",
    "the science of why we dream",
    "the rise of independent coffee shops on the high street",
    "how the railways changed the British landscape",
    "the craft of writing a good detective novel",
]

def random_topic() -> str:
    return random.choice(TOPICS)

def build_prompt(topic: str) -> str:
    return (
        "You are a skilled British English copywriter.\n"
        f'Write ONE cohesive, flowing paragraph of between 290 and 310 words about: "{topic}".\n'
        "Rules:\n"
        "- British spelling and phrasing throughout (e.g. \"colour\", \"realise\", \"whilst\").\n"
        "- One single paragraph. NO headings, NO bullet points, NO lists, NO markdown.\n"
        "- Natural, warm, human tone suitable for being read aloud by a text-to-speech voice.\n"
        "- Use clear punctuation so a TTS engine can pace it well.\n"
        "- Do not mention the word count or these instructions in your answer.\n"
        "Return ONLY the paragraph text."
    )

def generate_with_groq(topic: str) -> str:
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You write clean, speakable British English prose."},
            {"role": "user", "content": build_prompt(topic)},
        ],
        temperature=0.8,
        max_tokens=900,
    )
    return resp.choices[0].message.content.strip()

def generate_with_gemini(topic: str) -> str:
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    resp = client.models.generate_content(model=model, contents=build_prompt(topic))
    return resp.text.strip()

def word_count(text: str) -> int:
    return len(text.split())

def generate_text(topic: str, provider: str, lo: int = 290, hi: int = 310,
                  max_tries: int = 5) -> str:
    gen = generate_with_groq if provider == "groq" else generate_with_gemini
    mid = (lo + hi) // 2
    best = ""
    for attempt in range(1, max_tries + 1):
        text = gen(topic)
        n = word_count(text)
        print(f"  attempt {attempt}: {n} words")
        if lo <= n <= hi:
            return text
        if not best or abs(n - mid) < abs(word_count(best) - mid):
            best = text
    print(f"  ⚠️ never hit [{lo},{hi}]; using closest ({word_count(best)} words).")
    return best

def main():
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    topic = random_topic()
    print(f"Provider: {provider} | Topic: {topic}")

    text = generate_text(topic, provider)

    os.makedirs("generated_text", exist_ok=True)
    path = "generated_text/topic.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\n✓ Saved {word_count(text)} words to {path}")

if __name__ == "__main__":
    main()
```

```bash
python generate.py
```

---

## File 3 — `tts_blend.py` (blend 9 ratios → 9 wav files)

```python
"""Read generated_text/topic.txt and render 9 blended UK voices."""
import os
import numpy as np
import soundfile as sf
import torch
from kokoro import KPipeline

WEIGHT_PAIRS = [
    (10, 90), (20, 80), (30, 70), (40, 60),
    (50, 50), (60, 40), (70, 30), (80, 20), (90, 10),
]   # (% Emma ♀, % George ♂)

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
    v_emma   = torch.load("voices/bf_emma.pt",   map_location="cpu")
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
    pipeline = KPipeline(lang_code='b')      # British English

    for pct_f, pct_m in WEIGHT_PAIRS:
        w_f, w_m = pct_f / 100.0, pct_m / 100.0
        custom_voice = v_emma * w_f + v_george * w_m

        audio = synth_to_array(pipeline, text, custom_voice)

        out = os.path.join(OUT_DIR, f"blend_bf{pct_f}_bm{pct_m}.wav")
        sf.write(out, audio, SAMPLE_RATE)
        print(f"✓ {out}  ({pct_f}% Emma / {pct_m}% George)")

    print(f"\nDone. Listen to the 9 files in {OUT_DIR}/ and pick your favourite blend.")

if __name__ == "__main__":
    main()
```

```bash
python tts_blend.py
```

---

## Full run, start to finish

```bash
# (venv active, deps installed, espeak-ng installed, .env has your key)
python download_voices.py     # once
python generate.py            # -> generated_text/topic.txt
python tts_blend.py           # -> output_uk_audio/blend_*.wav  (9 files)
```

Expected console:
```
✓ voices/bf_emma.pt
✓ voices/bm_george.pt
Provider: groq | Topic: how the railways changed the British landscape
  attempt 1: 302 words
✓ Saved 302 words to generated_text/topic.txt
Text loaded: 302 words
✓ output_uk_audio/blend_bf10_bm90.wav  (10% Emma / 90% George)
...
✓ output_uk_audio/blend_bf90_bm10.wav  (90% Emma / 10% George)
Done. Listen to the 9 files in output_uk_audio/ and pick your favourite blend.
```

---

## Optional: one-command runner

Create `run_all.py`:

```python
import subprocess, sys

for step in ["download_voices.py", "generate.py", "tts_blend.py"]:
    print(f"\n=== Running {step} ===")
    code = subprocess.call([sys.executable, step])
    if code != 0:
        sys.exit(f"{step} failed with exit code {code}")
print("\nAll done ✅")
```
```bash
python run_all.py
```

Hit an error anywhere? → [08 – Troubleshooting](08-troubleshooting.md).
Ready to push your code? → [07 – Git Workflow](07-git-workflow.md).

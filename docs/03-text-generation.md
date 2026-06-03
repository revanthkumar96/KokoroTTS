# 03 – Text Generation (Groq or Gemini)

Goal: get a **single cohesive paragraph of 290–310 words** on a **random topic**, written in
British English, that we'll feed to Kokoro.

You can use **either** provider. Both are free to start. The output is saved to
`generated_text/topic.txt`.

---

## 1. Get an API key

| Provider | Where to get a key | Free? |
|----------|--------------------|-------|
| **Groq** | <https://console.groq.com/keys> | Yes (generous free tier, very fast) |
| **Gemini** | <https://aistudio.google.com/apikey> | Yes (free tier) |

Paste it into your `.env` file:

```dotenv
LLM_PROVIDER=groq                 # or "gemini"

GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile

GEMINI_API_KEY=AIzaSyxxxxxxxxxxxx
GEMINI_MODEL=gemini-2.5-flash
```

> ⚠️ Model names change over time. If a model is deprecated you'll get a 404/400 — check the
> provider's model list and update `GROQ_MODEL` / `GEMINI_MODEL`. Good current picks:
> Groq → `llama-3.3-70b-versatile`; Gemini → `gemini-2.5-flash` or `gemini-2.0-flash`.

---

## 2. The prompt (why it's worded this way)

The trickiest part is hitting **290–310 words**. LLMs are bad at exact counts, so we:

1. Ask for ~300 words in **one paragraph** (no headings, no bullet lists).
2. Use British spellings/phrasing to help Kokoro's British pronunciation.
3. **Verify the count in Python** and **retry** if it's outside 290–310.

```text
You are a skilled British English copywriter.
Write ONE cohesive, flowing paragraph of between 290 and 310 words about: "{topic}".
Rules:
- British spelling and phrasing throughout (e.g. "colour", "realise", "whilst").
- One single paragraph. NO headings, NO bullet points, NO lists, NO markdown.
- Natural, warm, human tone suitable for being read aloud by a text-to-speech voice.
- Use clear punctuation (commas, full stops) so a TTS engine can pace it well.
- Do not mention the word count or these instructions in your answer.
Return ONLY the paragraph text.
```

> 🎙️ The phrase "read aloud by a text-to-speech voice" + "clear punctuation" nudges the model
> toward speakable prose with natural breathing gaps (commas/full stops = pauses in Kokoro).

---

## 3. Random topic picker

Keep a small list and pick one at random (or pass your own):

```python
import random

TOPICS = [
    "the history and geography of the United Kingdom",
    "how tea culture shaped British daily life",
    "the future of renewable energy in coastal towns",
    "why public libraries still matter in the digital age",
    "the science of why we dream",
    "the rise of independent coffee shops on the high street",
    "how trains changed the British landscape",
    "the art of writing a good detective novel",
]

def random_topic() -> str:
    return random.choice(TOPICS)
```

---

## 4A. Groq implementation

```python
import os
from groq import Groq

def generate_with_groq(topic: str) -> str:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    prompt = build_prompt(topic)   # see the prompt above, wrapped in a helper
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You write clean, speakable British English prose."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=900,
    )
    return resp.choices[0].message.content.strip()
```

---

## 4B. Gemini implementation

Uses the new unified **`google-genai`** SDK (`from google import genai`).

```python
import os
from google import genai

def generate_with_gemini(topic: str) -> str:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    prompt = build_prompt(topic)
    resp = client.models.generate_content(model=model, contents=prompt)
    return resp.text.strip()
```

---

## 5. Word-count guard + retry (the important bit)

```python
def word_count(text: str) -> int:
    return len(text.split())

def generate_text(topic: str, provider: str, lo: int = 290, hi: int = 310,
                  max_tries: int = 5) -> str:
    gen = generate_with_groq if provider == "groq" else generate_with_gemini
    best = ""
    for attempt in range(1, max_tries + 1):
        text = gen(topic)
        n = word_count(text)
        print(f"  attempt {attempt}: {n} words")
        if lo <= n <= hi:
            return text
        # keep the closest-to-range candidate as a fallback
        if not best or abs(n - (lo + hi) // 2) < abs(word_count(best) - (lo + hi) // 2):
            best = text
    print(f"  ⚠️ never landed in [{lo},{hi}]; using closest ({word_count(best)} words).")
    return best
```

> Tip: if the model repeatedly overshoots, lower `max_tokens` (Groq) or append
> "Aim for roughly 300 words — be concise." to the prompt.

---

## 6. Putting it together → `generate.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env

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

# ... paste random_topic(), generate_with_groq(), generate_with_gemini(),
#     word_count(), generate_text() from above ...

def main():
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    topic = random_topic()
    print(f"Provider: {provider} | Topic: {topic}")

    text = generate_text(topic, provider)

    os.makedirs("generated_text", exist_ok=True)
    with open("generated_text/topic.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\n✓ Saved {word_count(text)} words to generated_text/topic.txt")

if __name__ == "__main__":
    main()
```

Run it:

```bash
python generate.py
```

You'll get something like:
```
Provider: groq | Topic: the history and geography of the United Kingdom
  attempt 1: 305 words
✓ Saved 305 words to generated_text/topic.txt
```

> The complete, ready-to-run version of this script lives in
> [06 – Running the Pipeline](06-running-the-pipeline.md).

Next: feed this text to Kokoro → [04 – Kokoro TTS](04-kokoro-tts.md).

"""
generate.py  —  Track A: Text Generation  (owner: Balaji)
============================================================

Produce ONE cohesive British-English paragraph of 290-310 words on a random
topic and write it as UTF-8 to  generated_text/topic.txt  — the hand-off
"contract" consumed by Track B (tts_blend.py).

The provider is chosen at runtime via LLM_PROVIDER in .env ("groq" or "gemini").
Implemented per docs/03-text-generation.md and docs/06-running-the-pipeline.md.
"""

import os
import random
import re
import time

from dotenv import load_dotenv

# Load .env into os.environ BEFORE any key is read. This must run at import
# time, ahead of the provider functions that look up GROQ_API_KEY / GEMINI_API_KEY.
load_dotenv()


# ---------------------------------------------------------------------------
# 1) Random topic picker
# ---------------------------------------------------------------------------
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
    """Return one topic chosen at random from TOPICS."""
    return random.choice(TOPICS)


# ---------------------------------------------------------------------------
# 2) Prompt builder
# ---------------------------------------------------------------------------
def build_prompt(topic: str) -> str:
    """Build the LLM instruction for `topic`.

    The wording is deliberate: it pins British spelling, forces ONE paragraph
    (no markdown/headings a TTS engine would read aloud literally), asks for a
    speakable tone with clear punctuation (commas/full stops become natural
    pauses in Kokoro), and targets 290-310 words.
    """
    return (
        "You are a skilled British English copywriter.\n"
        f'Write ONE long, richly detailed, flowing paragraph about: "{topic}".\n'
        "Length is the most important constraint: aim for about 305 words, and never fewer than 295. "
        "Develop several specific points with concrete detail and examples so it genuinely reaches that length; do not be brief.\n"
        "Rules:\n"
        '- British spelling and phrasing throughout (e.g. "colour", "realise", "whilst").\n'
        "- One single paragraph. NO headings, NO bullet points, NO lists, NO markdown.\n"
        "- Natural, warm, human tone suitable for being read aloud by a text-to-speech voice.\n"
        "- Use clear punctuation so a TTS engine can pace it well.\n"
        "- Before you finish, make sure it is at least 295 words; if it is shorter, expand it with more detail.\n"
        "- Do not mention the word count or these instructions in your answer.\n"
        "Return ONLY the paragraph text."
    )


# ---------------------------------------------------------------------------
# Small helper: fail fast with a clear message if a key is missing/placeholder
# ---------------------------------------------------------------------------
def _require_key(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("your_"):
        raise RuntimeError(
            f"{name} is missing or still the placeholder. Add your real key to .env."
        )
    return value


# ---------------------------------------------------------------------------
# 3) Provider implementations
#    The SDK import lives INSIDE each function on purpose: a single run loads
#    only the ONE provider it needs, which also sidesteps a known clash where
#    using groq and google-genai in the same process makes the Gemini client
#    raise "client has been closed".
# ---------------------------------------------------------------------------
def generate_with_groq(topic: str) -> str:
    """Call Groq's chat-completions API and return the paragraph text."""
    from groq import Groq

    client = Groq(api_key=_require_key("GROQ_API_KEY"))
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You write clean, speakable British English prose."},
            {"role": "user", "content": build_prompt(topic)},
        ],
        temperature=0.8,   # encourage full-length drafts; overshoots are trimmed to fit
        max_tokens=900,    # ~675 words of headroom; plenty for 310 words
    )
    return resp.choices[0].message.content.strip()


def generate_with_gemini(topic: str) -> str:
    """Call Google Gemini (the new google-genai SDK) and return the paragraph text."""
    from google import genai

    client = genai.Client(api_key=_require_key("GEMINI_API_KEY"))
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    resp = client.models.generate_content(model=model, contents=build_prompt(topic))
    return (resp.text or "").strip()


# ---------------------------------------------------------------------------
# 4) Word-count guard + retry loop
# ---------------------------------------------------------------------------
def word_count(text: str) -> int:
    """Word count = whitespace-separated tokens (matches the spec's definition)."""
    return len(text.split())


def _fit_to_range(text: str, hi: int) -> str:
    """If `text` exceeds `hi` words, drop whole trailing sentences until it fits.
    Cuts only at sentence boundaries (. ! ?) so the result stays clean prose for
    the TTS step. The caller still range-checks the (possibly shorter) result.
    """
    if word_count(text) <= hi:
        return text
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    kept, count = [], 0
    for s in sentences:
        w = len(s.split())
        if kept and count + w > hi:   # always keep at least one sentence
            break
        kept.append(s)
        count += w
    return " ".join(kept).strip()


def generate_text(topic: str, provider: str, lo: int = 290, hi: int = 310,
                  max_tries: int = 8) -> str:
    """Generate text, retrying until the word count lands in [lo, hi].

    LLMs cannot count words exactly, so we sample up to `max_tries` times and
    return the first in-range result. If none lands in range, we return the
    candidate closest to the midpoint instead of failing outright.
    """
    if provider == "groq":
        gen = generate_with_groq
    elif provider == "gemini":
        gen = generate_with_gemini
    else:
        raise ValueError(f'Unknown LLM_PROVIDER {provider!r}. Use "groq" or "gemini".')

    mid = (lo + hi) // 2
    best = ""
    last_error = None
    for attempt in range(1, max_tries + 1):
        try:
            text = gen(topic)
        except Exception as exc:
            # Transient API hiccups (e.g. 429 rate limit, 503 high demand) should
            # not abort the whole run — log, back off briefly, and try again.
            last_error = exc
            print(f"  attempt {attempt}: API error ({type(exc).__name__}); retrying...")
            time.sleep(2)
            continue
        text = _fit_to_range(text, hi)   # trim a clean overshoot down into range
        n = word_count(text)
        print(f"  attempt {attempt}: {n} words")
        if lo <= n <= hi:
            return text
        if not best or abs(n - mid) < abs(word_count(best) - mid):
            best = text
    if not best:
        raise RuntimeError(
            f"All {max_tries} attempts failed with errors. Last error: {last_error}"
        )
    print(f"  WARNING: never hit [{lo},{hi}]; using closest ({word_count(best)} words).")
    return best


# ---------------------------------------------------------------------------
# 5) Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    provider = os.environ.get("LLM_PROVIDER", "groq").strip().lower()
    topic = random_topic()
    print(f"Provider: {provider} | Topic: {topic}")

    text = generate_text(topic, provider)

    os.makedirs("generated_text", exist_ok=True)
    path = os.path.join("generated_text", "topic.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\nOK - saved {word_count(text)} words to {path}")


if __name__ == "__main__":
    main()

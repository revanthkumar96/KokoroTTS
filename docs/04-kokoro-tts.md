# 04 – Kokoro TTS basics

Everything you need to know about the Kokoro `KPipeline` API before doing the voice blend.

---

## The modern API (use this)

```python
from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code='b')        # build once, reuse for many calls

text = "Hello from the United Kingdom."
generator = pipeline(text, voice='bf_emma', speed=1.0)

for i, (graphemes, phonemes, audio) in enumerate(generator):
    sf.write(f"out_{i}.wav", audio, 24000) # Kokoro always outputs 24 kHz
```

Key points:

- **`KPipeline(lang_code=...)`** — set the language **once**. For British English use `'b'`.
- **Calling the pipeline** `pipeline(text, voice=..., speed=...)` returns a **generator**.
  Kokoro splits long text into chunks and yields one `(graphemes, phonemes, audio)` tuple per
  chunk. `audio` is a 1‑D `float32` numpy array at **24000 Hz**.
- **`voice=`** accepts either a **name string** (`'bf_emma'`) **or a tensor** (this is how we
  blend — see [05](05-voice-blending.md)).
- **`speed=`** float, `1.0` = normal. Try `0.9` for slightly slower/clearer narration.

> ⚠️ Common mistake: treating the return value as a single audio array. It is a **generator**
> that may yield **multiple chunks** for long text (like our ~300‑word passage). You must
> iterate it.

---

## Language codes

| Code | Language |
|------|----------|
| `'b'` | British English |
| `'a'` | American English |
| `'e'` | Spanish |
| `'f'` | French |
| `'h'` | Hindi |
| `'i'` | Italian |
| `'p'` | Brazilian Portuguese |
| `'j'` | Japanese (needs extra deps) |
| `'z'` | Mandarin Chinese (needs extra deps) |

We use **`'b'`** so Emma and George are pronounced with British rules.

---

## Handling long text (our ~300-word passage)

For long input, Kokoro yields several chunks. You have two sensible options:

**Option A — one file per chunk** (simple, but you get multiple files):
```python
for i, (_, _, audio) in enumerate(pipeline(long_text, voice='bf_emma')):
    sf.write(f"part_{i}.wav", audio, 24000)
```

**Option B — concatenate chunks into ONE file** (what we want for this project):
```python
import numpy as np
import soundfile as sf

chunks = [audio for _, _, audio in pipeline(long_text, voice='bf_emma')]
full = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
sf.write("full.wav", full, 24000)
```

We use **Option B** in the blending loop so each ratio = exactly one `.wav` file.

> 💡 You can insert a tiny silence between chunks for nicer pacing:
> `np.concatenate([... , np.zeros(int(0.15*24000), dtype=np.float32), ...])`.

---

## Loading a voice as a tensor

To blend voices we need the raw tensors. Two ways:

```python
import torch

# (1) Straight from the .pt file you downloaded in docs/02-setup.md:
v_emma = torch.load("voices/bf_emma.pt", map_location="cpu")

# (2) Via the pipeline's loader (auto-downloads if missing):
v_emma = pipeline.load_voice("bf_emma")   # returns a tensor on the pipeline's device
```

Either way you get a tensor of shape `[510, 1, 256]`. That's the object we do math on in the
next doc.

---

## Sanity checklist

- [ ] `pipeline = KPipeline(lang_code='b')` created without error
- [ ] espeak-ng installed (else phoneme errors — see [08](08-troubleshooting.md))
- [ ] You iterate the generator (don't treat it as a single array)
- [ ] You write with sample rate **24000**
- [ ] Output `.wav` plays back as clear British speech

Next: the main event → [05 – Voice Blending](05-voice-blending.md).

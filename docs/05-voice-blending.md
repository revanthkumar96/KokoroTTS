# 05 – Voice Blending (the core experiment)

This is the heart of the project: take two British voice tensors, mix them at 9 ratios, and
render one `.wav` per ratio so you can hear which blend sounds most natural.

---

## The idea in one line

```python
V_blend = V_emma * w_emma + V_george * w_george      # w_emma + w_george == 1.0
```

A Kokoro voice is a **style tensor** of shape `[510, 1, 256]`. Linearly interpolating between
two of them gives a believable in‑between voice.

---

## Why your original snippet needs a small change

Your original code used the **legacy** Kokoro call:

```python
# OLD / legacy — may not work with the current pip package
audio, phonemes = kokoro.generate(model, text=test_paragraph, voice=custom_voice, lang='b')
```

The current `kokoro` package uses **`KPipeline`**, and you pass the blended tensor directly to
`voice=`. The **blending math is exactly the same** — only the call to synthesise changes:

```python
# NEW / supported
pipeline = KPipeline(lang_code='b')
for _, _, audio in pipeline(text, voice=custom_voice):
    ...
```

---

## Loading the two voices

```python
import torch

v_emma   = torch.load("voices/bf_emma.pt",   map_location="cpu")   # ♀ British
v_george = torch.load("voices/bm_george.pt", map_location="cpu")   # ♂ British

print(v_emma.shape, v_george.shape)   # both -> torch.Size([510, 1, 256])
```

> If the files aren't there, run the download step in [02 – Setup](02-setup.md) §5, or load by
> name with `pipeline.load_voice("bf_emma")`.

---

## The 9 ratios

```python
weight_pairs = [
    (10, 90), (20, 80), (30, 70), (40, 60),
    (50, 50), (60, 40), (70, 30), (80, 20), (90, 10),
]   # (% Emma ♀, % George ♂)
```

---

## The blend + synth loop

```python
import os
import numpy as np
import soundfile as sf
from kokoro import KPipeline

def synth_to_array(pipeline, text, voice_tensor):
    """Run Kokoro over (possibly chunked) text and return ONE concatenated audio array."""
    chunks = [audio for _, _, audio in pipeline(text, voice=voice_tensor)]
    return np.concatenate(chunks) if len(chunks) > 1 else chunks[0]

def blend_all(text, v_emma, v_george, out_dir="output_uk_audio"):
    os.makedirs(out_dir, exist_ok=True)
    pipeline = KPipeline(lang_code='b')      # British English

    for pct_f, pct_m in weight_pairs:
        w_f, w_m = pct_f / 100.0, pct_m / 100.0
        custom_voice = v_emma * w_f + v_george * w_m      # <-- the blend

        audio = synth_to_array(pipeline, text, custom_voice)

        out = os.path.join(out_dir, f"blend_bf{pct_f}_bm{pct_m}.wav")
        sf.write(out, audio, 24000)
        print(f"✓ {out}  ({pct_f}% Emma / {pct_m}% George)")
```

That's it. Nine files in `output_uk_audio/`.

---

## Important gotchas

- **Weights must sum to 1.0.** `w_f + w_m == 1.0`. Otherwise the embedding magnitude drifts
  and the audio can clip, go quiet, or sound distorted.
- **Same shape required.** Both tensors are `[510, 1, 256]`. All Kokoro voices share this
  shape, so any two voices can be blended — but don't mix in a tensor of a different shape.
- **Device/dtype match.** If you move one tensor to GPU, move both (and the model). For this
  CPU experiment, keep both on CPU (`map_location="cpu"`).
- **It's a generator.** Remember Kokoro returns a generator; we concatenate chunks (see
  [04](04-kokoro-tts.md)).
- **Determinism.** Same text + same blend → same audio. Great for A/B comparison.

---

## How to evaluate the 9 files

1. Open `output_uk_audio/` in your file explorer / audio player.
2. Play them in order from `bf10_bm90` (mostly George) → `bf90_bm10` (mostly Emma).
3. Note which one sounds the **most natural and least robotic** to you.
4. That ratio is your "house voice" — hard‑code it for production:

```python
# Example: you decided 60% Emma / 40% George sounds best
final_voice = v_emma * 0.60 + v_george * 0.40
```

---

## Optional refinements

- **Finer steps:** add `(5, 95)`, `(15, 85)`, … for a smoother sweep.
- **Three-way blend:** `v = a*w1 + b*w2 + c*w3` with `w1+w2+w3 == 1.0`.
- **Breathing pauses:** insert short silence between chunks (see [04](04-kokoro-tts.md) tip).
- **Loudness normalise:** if a blend is quieter, peak‑normalise before writing:
  ```python
  peak = np.max(np.abs(audio)) or 1.0
  audio = (audio / peak) * 0.97
  ```

Next: the complete, copy‑paste scripts that tie generation + blending together →
[06 – Running the Pipeline](06-running-the-pipeline.md).

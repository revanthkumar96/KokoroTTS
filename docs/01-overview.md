# 01 – Overview & Architecture

This page explains *how the whole thing fits together* before you write a line of code.
Read it once, then jump to the setup guide.

---

## The goal

> Produce a long (~300‑word) spoken passage in **British English**, but instead of using one
> stock voice, **blend two UK voices** (`bf_emma` female + `bm_george` male) at 9 different
> mix ratios. Listen to all 9 and keep the blend that sounds the most natural.

There are three moving parts:

| Stage | Tool | Input | Output |
|-------|------|-------|--------|
| 1. Write the text | **Groq** or **Gemini** LLM | a random topic | `generated_text/topic.txt` (290–310 words) |
| 2. Turn text → speech | **Kokoro‑82M** (`KPipeline`) | the text + a voice | audio samples (numpy array @ 24 kHz) |
| 3. Blend the voice | **PyTorch** tensor math | two `.pt` voice tensors | a new mixed voice tensor per ratio |

Stages 2 and 3 happen together inside one loop: for each of the 9 ratios we build a blended
voice tensor and run Kokoro once.

---

## Data flow (step by step)

```
 STEP A — TEXT
 ─────────────
   random topic  ──►  LLM prompt ("write 290–310 words, British English, one paragraph")
                 ◄──  paragraph string
   save to generated_text/topic.txt


 STEP B — LOAD VOICES (once)
 ───────────────────────────
   voices/bf_emma.pt    ─► torch.load ─► tensor  V_f   shape [510, 1, 256]
   voices/bm_george.pt  ─► torch.load ─► tensor  V_m   shape [510, 1, 256]


 STEP C — BLEND + SYNTHESISE (loop over 9 ratios)
 ────────────────────────────────────────────────
   for (pct_f, pct_m) in [(10,90),(20,80),...,(90,10)]:
        w_f = pct_f / 100
        w_m = pct_m / 100
        V_blend = V_f * w_f + V_m * w_m          # weighted average of style tensors
        audio   = KPipeline(text, voice=V_blend) # British English (lang_code='b')
        soundfile.write(f"blend_bf{pct_f}_bm{pct_m}.wav", audio, 24000)
```

The result is 9 `.wav` files you can A/B test in any audio player.

---

## Why blend *style tensors* instead of mixing audio?

A Kokoro "voice" is **not** an audio clip — it is a small learned **style/embedding tensor**
of shape `[510, 1, 256]`. Kokoro uses one slice of this tensor (indexed by the length of the
input phonemes) to condition the generator.

Because the voice is just a tensor, you can do plain linear algebra on it:

```python
V_blend = V_f * w_f + V_m * w_m       # w_f + w_m = 1.0
```

This produces a voice that genuinely sits *between* Emma and George in timbre — far better
than crossfading two separate audio renders, which would just sound like two people talking
over each other.

> ⚠️ Keep `w_f + w_m == 1.0`. If the weights don't sum to 1 the overall "energy" of the
> embedding changes and the output can get quiet, loud, or distorted.

---

## The two voices we blend

| Voice ID     | Sex | Accent          | Notes |
|--------------|-----|-----------------|-------|
| `bf_emma`    | ♀   | British English | warm, clear RP-ish |
| `bm_george`  | ♂   | British English | deeper, measured |

Both ship in the `hexgrad/Kokoro-82M` repo under `voices/`. The `b` prefix = **B**ritish,
`f`/`m` = female/male. We also pass `lang_code='b'` to the pipeline so the phonemiser uses
British pronunciation rules.

---

## The 9 blend ratios

| File name                     | % Emma (♀) | % George (♂) |
|-------------------------------|-----------:|-------------:|
| `blend_bf10_bm90.wav`         | 10 | 90 |
| `blend_bf20_bm80.wav`         | 20 | 80 |
| `blend_bf30_bm70.wav`         | 30 | 70 |
| `blend_bf40_bm60.wav`         | 40 | 60 |
| `blend_bf50_bm50.wav`         | 50 | 50 |
| `blend_bf60_bm40.wav`         | 60 | 40 |
| `blend_bf70_bm30.wav`         | 70 | 30 |
| `blend_bf80_bm20.wav`         | 80 | 20 |
| `blend_bf90_bm10.wav`         | 90 | 10 |

---

## Where to go next

1. **[02 – Setup](02-setup.md)** — get Python, dependencies, espeak-ng and the voice files.
2. **[03 – Text Generation](03-text-generation.md)** — produce the ~300‑word passage.
3. **[05 – Voice Blending](05-voice-blending.md)** — the core experiment.
4. **[06 – Running the Pipeline](06-running-the-pipeline.md)** — the complete scripts.

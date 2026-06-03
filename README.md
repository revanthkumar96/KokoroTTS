# KokoroTTS — UK Voice Blending Lab

Generate a ~300‑word passage on a random topic with an **LLM (Groq or Gemini)**, then
speak it with the open‑source **Kokoro‑82M** TTS model — while **mathematically blending two
British voices** (`bf_emma` 🇬🇧♀ + `bm_george` 🇬🇧♂) across 9 weight ratios so you can pick
the blend that sounds the *least robotic* to your ear.

> **TL;DR for my friends:** clone the repo, follow [`docs/02-setup.md`](docs/02-setup.md),
> drop your API key in `.env`, run `python generate.py` then `python tts_blend.py`, and
> compare the 9 `.wav` files in `output_uk_audio/`.

---

## What this project does

```
            ┌─────────────────────┐      ~300-word         ┌────────────────────────┐
  random    │   LLM (Groq /       │      UK paragraph       │   Kokoro-82M TTS        │
  topic ───▶│   Gemini)           │ ─────────────────────▶ │   (KPipeline, lang='b') │
            └─────────────────────┘     generated_text/     └───────────┬────────────┘
                                                                         │
                                              blend two voice tensors    │
                                       bf_emma (♀) × w  +  bm_george (♂) × (1-w)
                                                                         │
                                                                         ▼
                                              output_uk_audio/blend_bf10_bm90.wav
                                              output_uk_audio/blend_bf20_bm80.wav
                                              ...  (9 files total)  ...
                                              output_uk_audio/blend_bf90_bm10.wav
```

1. **Text generation** — Ask Groq or Gemini for a single cohesive paragraph of **290–310
   words** on a randomly chosen topic, using British spellings/phrasing. See
   [`docs/03-text-generation.md`](docs/03-text-generation.md).
2. **Speech synthesis** — Feed that text to Kokoro with `lang_code='b'` (British English).
   See [`docs/04-kokoro-tts.md`](docs/04-kokoro-tts.md).
3. **Voice blending** — Load the two voice **style tensors**, mix them at 9 ratios
   (`10/90 … 90/10`), and render one `.wav` per blend. See
   [`docs/05-voice-blending.md`](docs/05-voice-blending.md).

> ℹ️ **Note on the original snippet.** The code you were given calls
> `kokoro.generate(model, text=..., voice=..., lang='b')`, which is the **legacy** Kokoro
> API. The current pip package uses **`KPipeline`** and you pass the blended tensor straight
> to `voice=`. All docs here use the supported modern API. The math (blending two `.pt`
> tensors) is identical to your original idea.

---

## Repository layout

```
KokoroTTS/
├── README.md                  ← you are here
├── requirements.txt           ← Python dependencies
├── .env.example               ← copy to .env and add your API key
├── .gitignore
├── docs/
│   ├── 01-overview.md         ← architecture & data flow in depth
│   ├── 02-setup.md            ← install everything (Windows / macOS / Linux)
│   ├── 03-text-generation.md  ← Groq & Gemini ~300-word generator
│   ├── 04-kokoro-tts.md       ← Kokoro KPipeline basics
│   ├── 05-voice-blending.md   ← the tensor-blending experiment (9 ratios)
│   ├── 06-running-the-pipeline.md ← full copy-paste scripts, end to end
│   ├── 07-git-workflow.md     ← ALL the git/GitHub commands & team workflow
│   ├── 08-troubleshooting.md  ← every error we hit + the fix
│   └── 09-roles-and-tasks.md  ← team roles & task split (review vs build)
├── voices/                    ← bf_emma.pt, bm_george.pt (downloaded, git-ignored)
├── generated_text/            ← LLM output saved here (git-ignored)
└── output_uk_audio/           ← 9 blended .wav files land here (git-ignored)
```

---

## Quickstart (5 commands)

```bash
# 1. Clone
git clone git@github.com:revanthkumar96/KokoroTTS.git
cd KokoroTTS

# 2. Create + activate a virtual environment, then install deps
python -m venv .venv && source .venv/bin/activate        # macOS/Linux
pip install -r requirements.txt

# 3. Install the espeak-ng SYSTEM dependency (see docs/02-setup.md)

# 4. Add your key
cp .env.example .env            # then edit .env and paste your GROQ_API_KEY or GEMINI_API_KEY

# 5. Run it
python generate.py              # writes generated_text/topic.txt
python tts_blend.py             # writes 9 .wav files into output_uk_audio/
```

Windows PowerShell users: see the Windows column in [`docs/02-setup.md`](docs/02-setup.md)
(`python -m venv .venv ; .\.venv\Scripts\Activate.ps1`, `Copy-Item .env.example .env`).

---

## Requirements at a glance

| Component        | Version / Source                                            |
|------------------|-------------------------------------------------------------|
| Python           | 3.10–3.12 (3.11 recommended)                                |
| Kokoro           | `kokoro>=0.9.4` (pip)                                        |
| espeak-ng        | system package — **required** for phonemes                  |
| LLM key          | Groq (free tier) **or** Gemini (free tier)                  |
| Voice tensors    | `bf_emma.pt`, `bm_george.pt` from `hexgrad/Kokoro-82M` on HF |
| Disk             | ~1 GB (model + voices + cache)                              |
| GPU              | optional — CPU works fine for this experiment               |

---

## Documentation index

| Doc | Read it when you want to… |
|-----|---------------------------|
| [01 – Overview](docs/01-overview.md) | Understand the whole pipeline before coding |
| [02 – Setup](docs/02-setup.md) | Install Python, deps, espeak-ng, and download voices |
| [03 – Text Generation](docs/03-text-generation.md) | Wire up Groq or Gemini and get a clean ~300-word passage |
| [04 – Kokoro TTS](docs/04-kokoro-tts.md) | Learn the Kokoro `KPipeline` API |
| [05 – Voice Blending](docs/05-voice-blending.md) | Do the 9-ratio tensor blend (the heart of the project) |
| [06 – Running the Pipeline](docs/06-running-the-pipeline.md) | Copy the complete, runnable scripts |
| [07 – Git Workflow](docs/07-git-workflow.md) | Every git/GitHub command + branching/PR workflow |
| [08 – Troubleshooting](docs/08-troubleshooting.md) | Fix the common errors fast |
| [09 – Roles & Tasks](docs/09-roles-and-tasks.md) | Who does what (Revanth reviews; Balaji & Sowjanya build) |

---

## Credits & licences

- **Kokoro‑82M** TTS model by [hexgrad](https://huggingface.co/hexgrad/Kokoro-82M) — Apache‑2.0.
- **Groq** and **Google Gemini** are third‑party APIs subject to their own terms.
- This repo's docs/code: do whatever you like, just keep upstream licences intact.

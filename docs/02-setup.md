# 02 – Setup (Windows / macOS / Linux)

Follow this top to bottom. By the end you'll have Python, all dependencies, the
**espeak-ng** system tool, and the two voice tensors downloaded.

> ⏱️ First run downloads the Kokoro model (~330 MB) + voices. Be patient once.

---

## 0. Prerequisites

- **Python 3.10–3.12** (3.11 recommended). Check with `python --version`.
- **Git** installed (`git --version`).
- A **Groq** or **Gemini** API key (free). See [03 – Text Generation](03-text-generation.md).

---

## 1. Clone the repository

```bash
git clone git@github.com:revanthkumar96/KokoroTTS.git
cd KokoroTTS
```

> No SSH key set up? Use HTTPS instead:
> `git clone https://github.com/revanthkumar96/KokoroTTS.git`
> (SSH setup is covered in [07 – Git Workflow](07-git-workflow.md).)

---

## 2. Create & activate a virtual environment

Pick the column for your OS.

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# If you get an execution-policy error, run once:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**macOS / Linux (bash/zsh)**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should now see `(.venv)` at the start of your prompt.

---

## 3. Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs `kokoro`, `torch`, `soundfile`, `groq`, `google-genai`, etc.

> 💡 **CPU is fine.** The default `torch` wheel works on CPU. You do **not** need CUDA for
> this experiment. (GPU users: install the matching CUDA torch wheel from pytorch.org if you
> want speed.)

---

## 4. Install espeak-ng (the one non-pip dependency)

Kokoro converts text → phonemes using **espeak-ng**. Without it you'll get an error like
`espeak not installed` or silent/garbled audio.

**Windows**
1. Download the latest `*.msi` installer from
   <https://github.com/espeak-ng/espeak-ng/releases> (e.g. `espeak-ng-X.Y.Z.msi`).
2. Install it (default path is `C:\Program Files\eSpeak NG\`).
3. Tell Python where the DLL is. Either add it to your `.env`:
   ```
   PHONEMIZER_ESPEAK_LIBRARY=C:\Program Files\eSpeak NG\libespeak-ng.dll
   ```
   …or set it in PowerShell for the session:
   ```powershell
   $env:PHONEMIZER_ESPEAK_LIBRARY = "C:\Program Files\eSpeak NG\libespeak-ng.dll"
   ```

**macOS (Homebrew)**
```bash
brew install espeak-ng
```

**Linux (Debian/Ubuntu)**
```bash
sudo apt-get update && sudo apt-get install -y espeak-ng
```

**Verify it works:**
```bash
espeak-ng "hello from the United Kingdom"
```
You should hear (or at least not error). On Windows the command is `espeak-ng` too if you
added it to PATH; otherwise the DLL path above is what matters.

---

## 5. Download the UK voice tensors

The two voices live in the Hugging Face repo `hexgrad/Kokoro-82M` under `voices/`.

> ✅ **Easiest path:** you usually don't have to download manually — when you reference a
> voice by name (`"bf_emma"`), Kokoro auto-downloads it. But because this project **blends
> raw tensors**, it's cleaner to have the `.pt` files locally in `voices/`.

Create the folder and pull the two files:

```bash
# from the repo root, with the venv active
python -c "from huggingface_hub import hf_hub_download; import shutil, os; os.makedirs('voices', exist_ok=True); [shutil.copy(hf_hub_download('hexgrad/Kokoro-82M', f'voices/{v}.pt'), f'voices/{v}.pt') for v in ['bf_emma','bm_george']]; print('Downloaded bf_emma.pt and bm_george.pt into voices/')"
```

Or, as a tiny script `download_voices.py`:

```python
import os, shutil
from huggingface_hub import hf_hub_download

os.makedirs("voices", exist_ok=True)
for v in ["bf_emma", "bm_george"]:
    src = hf_hub_download("hexgrad/Kokoro-82M", f"voices/{v}.pt")
    shutil.copy(src, f"voices/{v}.pt")
    print(f"✓ voices/{v}.pt")
```

```bash
python download_voices.py
```

After this you should have:
```
voices/
├── bf_emma.pt
└── bm_george.pt
```

> 🔎 Want a different/extra voice? Browse the full list at
> <https://huggingface.co/hexgrad/Kokoro-82M/tree/main/voices>. British voices start with
> `bf_` (female) or `bm_` (male).

---

## 6. Smoke test (prove the install works)

Create `smoke_test.py`:

```python
from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code='b')          # 'b' = British English
text = "If you can hear this clearly, your Kokoro setup is working."
for i, (gs, ps, audio) in enumerate(pipeline(text, voice='bf_emma')):
    sf.write(f"smoke_{i}.wav", audio, 24000)
print("Wrote smoke_0.wav — open it and listen.")
```

```bash
python smoke_test.py
```

Open `smoke_0.wav`. If you hear a clear British female voice, **you're done** — move on to
[03 – Text Generation](03-text-generation.md).

If you hit an error, jump to [08 – Troubleshooting](08-troubleshooting.md).

---

## 7. Add your API key

```bash
cp .env.example .env          # macOS/Linux
# Copy-Item .env.example .env # Windows PowerShell
```
Open `.env` and paste your `GROQ_API_KEY` (or `GEMINI_API_KEY`). Details in
[03 – Text Generation](03-text-generation.md).

> 🔐 `.env` is git-ignored — your key will **not** be committed. Never paste keys into code
> or commit them.

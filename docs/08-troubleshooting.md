# 08 – Troubleshooting

Every common error we hit, what it means, and the fix. `Ctrl+F` your error message.

---

## espeak-ng / phonemes

**`RuntimeError: espeak not installed` / `Cannot find espeak-ng` / no audio**
- espeak-ng isn't installed or Python can't find it. Install it (see
  [02 – Setup](02-setup.md) §4).
- **Windows:** set the DLL path:
  ```powershell
  $env:PHONEMIZER_ESPEAK_LIBRARY = "C:\Program Files\eSpeak NG\libespeak-ng.dll"
  ```
  or add `PHONEMIZER_ESPEAK_LIBRARY=...` to `.env` and `load_dotenv()` before importing kokoro.
- Verify: `espeak-ng "test"` should run without error.

**Garbled / robotic / wrong-accent speech**
- Make sure you pass `lang_code='b'` to `KPipeline` (British), not `'a'` (American).
- Confirm you're using British voices (`bf_`, `bm_` prefixes).

---

## Kokoro / audio

**`TypeError: 'generator' object is not subscriptable` or only silence written**
- `pipeline(text, voice=...)` returns a **generator**. You must iterate it. Don't do
  `audio = pipeline(text, voice=...)`. Use the loop / concatenation shown in
  [04 – Kokoro TTS](04-kokoro-tts.md).

**Output `.wav` is tiny / empty**
- Long text yields multiple chunks — concatenate them (Option B in
  [04](04-kokoro-tts.md)), don't overwrite the same file each chunk.

**`.wav` sounds too fast or chipmunk-like**
- You wrote with the wrong sample rate. Kokoro outputs **24000 Hz**:
  `sf.write(path, audio, 24000)`.

**Distorted / clipping / very quiet on some blends**
- Your blend weights don't sum to 1.0. Ensure `w_f + w_m == 1.0`
  ([05 – Voice Blending](05-voice-blending.md)).
- Optionally peak-normalise before writing (see [05](05-voice-blending.md) "optional").

---

## Voice tensors

**`FileNotFoundError: voices/bf_emma.pt`**
- Run the download step: `python download_voices.py` (or [02 §5](02-setup.md)).

**`RuntimeError: The size of tensor a (...) must match ...` when blending**
- You're blending tensors of different shapes. Both must be `[510, 1, 256]`. Print
  `v_emma.shape, v_george.shape` to confirm. Don't blend a voice with something else.

**`RuntimeError: Expected all tensors to be on the same device`**
- One tensor is on GPU, the other on CPU. For this experiment load both with
  `map_location="cpu"`. If using GPU, move **both** voices and the model to the same device.

**`torch.load` warning about `weights_only`**
- On newer PyTorch you may see a FutureWarning. For these trusted HF voice files it's safe.
  If it hard-errors, use `torch.load(path, map_location="cpu", weights_only=True)`.

---

## LLM (Groq / Gemini)

**`KeyError: 'GROQ_API_KEY'` / `'GEMINI_API_KEY'`**
- Your `.env` isn't loaded or the key is missing. Ensure `.env` exists (copied from
  `.env.example`), the key is filled in, and `load_dotenv()` runs **before** you read
  `os.environ`.

**`401 Unauthorized` / `invalid api key`**
- Wrong or expired key. Regenerate it (Groq console / Google AI Studio) and update `.env`.

**`404 model not found` / `model has been decommissioned`**
- The model name changed. Update `GROQ_MODEL` or `GEMINI_MODEL` in `.env`. Current good
  picks: Groq `llama-3.3-70b-versatile`; Gemini `gemini-2.5-flash` / `gemini-2.0-flash`.

**`429 Too Many Requests` / rate limited**
- Free tiers have limits. Wait a bit, lower request frequency, or reduce `max_tries` in the
  retry loop.

**Never lands in 290–310 words**
- LLMs can't count exactly. The retry loop keeps the closest candidate. To improve: lower
  `temperature` (e.g. 0.6), tweak `max_tokens`, or add "Aim for ~300 words; be concise." to
  the prompt. See [03](03-text-generation.md) §5.

**`ModuleNotFoundError: No module named 'google'` (Gemini)**
- Install the new SDK: `pip install google-genai` (note: it's `google-genai`, and you import
  `from google import genai` — **not** the old `google-generativeai`).

---

## Environment / install

**`ModuleNotFoundError: No module named 'kokoro'` (or groq, soundfile, …)**
- Virtual env not active, or deps not installed. Activate `.venv` then
  `pip install -r requirements.txt`. Confirm with `pip list`.

**PowerShell: "running scripts is disabled on this system"**
- Allow venv activation once:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```

**`python` opens the Microsoft Store (Windows)**
- The Store alias is shadowing real Python. Install Python from python.org and tick
  "Add to PATH", or use the `py` launcher: `py -m venv .venv`.

**Torch install is huge / slow**
- The CPU wheel is enough for this project. If pip tries to pull CUDA wheels you don't need,
  install CPU torch explicitly: `pip install torch --index-url https://download.pytorch.org/whl/cpu`.

**`soundfile` can't write / `libsndfile` error (Linux)**
- Install the system lib: `sudo apt-get install -y libsndfile1`.

---

## Git / GitHub

**`Permission denied (publickey)` when pushing**
- SSH key not set up on GitHub. See [07 – Git Workflow](07-git-workflow.md) §0, or switch the
  remote to HTTPS:
  ```bash
  git remote set-url origin https://github.com/revanthkumar96/KokoroTTS.git
  ```

**`Updates were rejected because the remote contains work that you do not have locally`**
- Pull first, then push:
  ```bash
  git pull origin main --no-rebase
  # resolve conflicts if any, then
  git push origin main
  ```

**Accidentally committed `.env` / a `.wav`**
- Remove from tracking (keeps the local file) and commit:
  ```bash
  git rm --cached .env
  git commit -m "Stop tracking .env"
  ```
- If it was a secret, **rotate the key** — assume it leaked.

---

## Still stuck?

1. Re-read the relevant doc (the links above point to the exact section).
2. Run the **smoke test** in [02 §6](02-setup.md) to isolate TTS vs LLM vs git.
3. Copy the full error traceback and search it — paste it to a teammate with the command you
   ran and your OS.

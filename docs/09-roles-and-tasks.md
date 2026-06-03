# 09 – Roles & Task Distribution

How we split the work and review it. Three people, two implementation tracks, one reviewer.

---

## Team & roles

| Person | Role | Responsibility |
|--------|------|----------------|
| **Revanth** | 🧑‍⚖️ Code Reviewer / Maintainer | Reviews & approves **every PR into `main`**. Does **not** write feature code. Owns merge button, branch protection, release tags. |
| **Balaji** | 👨‍💻 Track A – Text Generation | LLM side: Groq + Gemini, prompt, ~300-word guard, `.env`, `generate.py`. |
| **Sowjanya** | 👩‍💻 Track B – TTS & Voice Blending | Kokoro side: voice download, `KPipeline`, the 9-ratio blend loop, `tts_blend.py`. |

> **Workflow rule:** Balaji and Sowjanya **never push to `main`**. They work on branches and
> open PRs. **Revanth reviews and merges.** See [07 – Git Workflow](07-git-workflow.md).

---

## The hand-off point (how the two tracks connect)

```
   BALAJI (Track A)                         SOWJANYA (Track B)
   ────────────────                         ──────────────────
   generate.py  ──writes──►  generated_text/topic.txt  ──read by──►  tts_blend.py
                              (the CONTRACT between tracks)
```

**The contract:** `generate.py` always writes a plain-text file at
`generated_text/topic.txt` containing **one paragraph of 290–310 words**, UTF-8 encoded.
As long as both sides honour this file + format, they can work fully in parallel.

> 💡 Until Balaji's `generate.py` is merged, Sowjanya can unblock herself by creating a dummy
> `generated_text/topic.txt` by hand (any ~300-word paragraph) to test her TTS code.

---

## Track A — Balaji (Text Generation)

**Goal:** produce a clean, speakable ~300-word British-English paragraph from a random topic.

**Branch:** `feature/text-generation`

**Deliverables**
- [ ] `generate.py` (full script in [06](06-running-the-pipeline.md), explained in [03](03-text-generation.md))
- [ ] `random_topic()` with a topic list
- [ ] `build_prompt()` enforcing British English + single paragraph
- [ ] `generate_with_groq()` **and** `generate_with_gemini()`
- [ ] `LLM_PROVIDER` switch read from `.env`
- [ ] Word-count guard + retry loop (290–310 words)
- [ ] Writes UTF-8 output to `generated_text/topic.txt`
- [ ] Update `.env.example` if you add any new keys/vars
- [ ] Quick note in README/03 if you change the topic list or prompt

**Done when:** `python generate.py` prints a word count in 290–310 and writes the file, with
both Groq and Gemini selectable via `.env`.

**Reference docs:** [03 – Text Generation](03-text-generation.md), [06 – Running the Pipeline](06-running-the-pipeline.md).

---

## Track B — Sowjanya (TTS & Voice Blending)

**Goal:** read the paragraph and render 9 blended UK voice `.wav` files.

**Branch:** `feature/voice-blending`

**Deliverables**
- [ ] `download_voices.py` — pulls `bf_emma.pt` + `bm_george.pt` into `voices/`
- [ ] `tts_blend.py` (full script in [06](06-running-the-pipeline.md), explained in [05](05-voice-blending.md))
- [ ] `KPipeline(lang_code='b')` British-English setup
- [ ] Load both voice tensors with `map_location="cpu"`
- [ ] The 9-ratio blend loop `(10/90 … 90/10)`, weights summing to 1.0
- [ ] Chunk concatenation → exactly **one** `.wav` per ratio at **24000 Hz**
- [ ] Output files named `output_uk_audio/blend_bf{f}_bm{m}.wav`
- [ ] espeak-ng install steps verified on your OS (note any extra steps in [02](02-setup.md)/[08](08-troubleshooting.md))

**Done when:** `python tts_blend.py` produces 9 playable `.wav` files from
`generated_text/topic.txt`.

**Reference docs:** [04 – Kokoro TTS](04-kokoro-tts.md), [05 – Voice Blending](05-voice-blending.md), [06 – Running the Pipeline](06-running-the-pipeline.md).

---

## Reviewer — Revanth (PRs into `main`)

You don't write feature code; you guard quality. For **each PR**:

**Review checklist**
- [ ] PR targets `main` from a `feature/...` branch (not a direct push to `main`).
- [ ] No secrets committed (`.env`, keys) and no large artifacts (`*.wav`, `voices/*.pt`,
      `generated_text/`) — all should be git-ignored.
- [ ] Code matches the documented behaviour (the file contract, 24 kHz, weights sum to 1.0,
      290–310 words).
- [ ] Branch is up to date with `main` (ask author to merge `main` in if behind).
- [ ] Runs locally / no obvious errors; commit messages are clear.

**Commands you'll use**
```bash
gh pr list                      # see open PRs
gh pr view <number> --web       # open in browser
gh pr checkout <number>         # pull the branch to test locally
gh pr review <number> --approve # or --request-changes -b "reason"
gh pr merge <number> --squash --delete-branch
```

**Optional but recommended — turn on branch protection** so `main` can only be changed via
reviewed PRs: GitHub → repo **Settings → Branches → Add rule** for `main` → require a pull
request + 1 approval before merging.

---

## Parallel timeline

| Step | Balaji | Sowjanya | Revanth |
|------|--------|----------|---------|
| 1 | Setup env + espeak-ng ([02](02-setup.md)) | Setup env + espeak-ng ([02](02-setup.md)) | Enable branch protection on `main` |
| 2 | Build `generate.py` on `feature/text-generation` | Build `download_voices.py` + `tts_blend.py` on `feature/voice-blending` (use a dummy `topic.txt`) | — |
| 3 | Open PR → `main` | Open PR → `main` | Review both PRs, request changes / approve |
| 4 | Merge after approval | Merge after approval | Merge via `gh pr merge --squash` |
| 5 | Run full pipeline end-to-end together; pick the best blend ratio | | Tag a release (`git tag -a v1.0`) |

---

## Quick start for Balaji & Sowjanya

```bash
git clone git@github.com:revanthkumar96/KokoroTTS.git
cd KokoroTTS
git checkout main
git pull origin main

# Balaji:
git checkout -b feature/text-generation
# Sowjanya:
git checkout -b feature/voice-blending

# ...work, commit, then...
git push -u origin <your-branch>
# open a PR to main and tag Revanth as reviewer
```

Full git details (SSH keys, conflicts, PR commands) → [07 – Git Workflow](07-git-workflow.md).

# 07 – Git & GitHub Workflow (every command you need)

This is the complete cheat‑sheet for collaborating on this repo:
`git@github.com:revanthkumar96/KokoroTTS.git`. Follow it and you won't clobber each other's
work.

> Commands work in **PowerShell, Git Bash, macOS Terminal, and Linux** unless noted. Lines
> starting with `#` are comments.

---

## 0. One-time machine setup

```bash
# Identify yourself (shows up in your commits)
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"

# Sensible defaults
git config --global init.defaultBranch main
git config --global pull.rebase false      # merge on pull (simplest for teams)
```

### SSH key (recommended) so you don't type passwords

```bash
# 1. Generate a key (press Enter to accept defaults)
ssh-keygen -t ed25519 -C "you@example.com"

# 2. Show the PUBLIC key and copy it
cat ~/.ssh/id_ed25519.pub            # macOS/Linux/Git Bash
# Windows PowerShell:
#   Get-Content $HOME\.ssh\id_ed25519.pub

# 3. Paste it at: GitHub → Settings → SSH and GPG keys → New SSH key

# 4. Test
ssh -T git@github.com                # expect "Hi <user>! You've successfully authenticated"
```

> Prefer HTTPS? Then clone with the `https://github.com/...` URL and use a
> **Personal Access Token** (GitHub → Settings → Developer settings → Tokens) as your
> password when prompted.

---

## 1. Get the code

```bash
# SSH (recommended)
git clone git@github.com:revanthkumar96/KokoroTTS.git

# or HTTPS
git clone https://github.com/revanthkumar96/KokoroTTS.git

cd KokoroTTS
```

Already cloned and want the latest?
```bash
git checkout main
git pull origin main
```

---

## 2. The day-to-day branch workflow

**Golden rule: never commit straight to `main`. Always branch.**

```bash
# 1. Start from an up-to-date main
git checkout main
git pull origin main

# 2. Create a feature branch (name it after what you're doing)
git checkout -b feature/gemini-support
#   other examples:
#   git checkout -b feature/voice-blend-loop
#   git checkout -b fix/word-count-retry
#   git checkout -b docs/setup-windows

# 3. ... do your work, edit files ...

# 4. See what changed
git status
git diff

# 5. Stage your changes
git add generate.py tts_blend.py        # specific files
# or stage everything that isn't git-ignored:
git add .

# 6. Commit with a clear message
git commit -m "Add Gemini provider with word-count retry"

# 7. Push your branch to GitHub (first push needs -u)
git push -u origin feature/gemini-support
#   after the first time, just:  git push
```

---

## 3. Open a Pull Request (PR)

After `git push`, GitHub prints a link like
`https://github.com/revanthkumar96/KokoroTTS/pull/new/feature/gemini-support`.

**Option A — in the browser:** click that link → "Create pull request" → add a title +
description → Create.

**Option B — with the GitHub CLI (`gh`):**
```bash
# Install once: https://cli.github.com/  then  gh auth login
gh pr create --base main --head feature/gemini-support \
  --title "Add Gemini provider" \
  --body  "Implements google-genai backend + word-count retry. Closes #12."
```

Useful `gh` commands:
```bash
gh pr status            # see your PRs
gh pr list              # all open PRs
gh pr view --web        # open current PR in browser
gh pr checks            # CI status
gh pr merge --squash    # merge (after approval)
```

---

## 4. Keeping your branch in sync with main

If teammates merged things while you were working:

```bash
git checkout main
git pull origin main

git checkout feature/gemini-support
git merge main                 # bring main's changes into your branch
# resolve any conflicts (see §6), then:
git push
```

---

## 5. After your PR is merged — clean up

```bash
git checkout main
git pull origin main

# delete the local branch
git branch -d feature/gemini-support

# delete the remote branch (if GitHub didn't auto-delete)
git push origin --delete feature/gemini-support
```

---

## 6. Resolving merge conflicts

When `git merge` reports a conflict:

```bash
git status                      # lists "both modified" files
```
Open each conflicted file. You'll see markers:
```
<<<<<<< HEAD
your version
=======
their version
>>>>>>> main
```
Edit the file to the correct final content, **delete the `<<<<`, `====`, `>>>>` lines**, then:

```bash
git add path/to/conflicted_file.py
git commit                      # completes the merge (default message is fine)
git push
```

Want to abort and start over?
```bash
git merge --abort
```

---

## 7. Common situations & the command to fix them

| You want to… | Command |
|--------------|---------|
| See history | `git log --oneline --graph --decorate --all` |
| Discard changes to one file | `git checkout -- path/to/file` |
| Unstage a file (keep edits) | `git restore --staged path/to/file` |
| Undo the **last** commit, keep changes | `git reset --soft HEAD~1` |
| See who changed a line | `git blame path/to/file` |
| Stash work to switch branches fast | `git stash` … `git stash pop` |
| Update from remote without merging | `git fetch origin` |
| See remote URL | `git remote -v` |
| Rename current branch | `git branch -m new-name` |
| Tag a release | `git tag -a v1.0 -m "v1.0" && git push origin v1.0` |

> ⚠️ Avoid `git push --force` on shared branches like `main` — it can erase teammates' work.
> If you truly must, use the safer `git push --force-with-lease` and warn the team first.

---

## 8. What NOT to commit

`.gitignore` already excludes these — keep it that way:

- **`.env`** (your API keys) — never commit secrets.
- **`output_uk_audio/`, `*.wav`** — large, regenerable.
- **`voices/*.pt`** — large, re-downloadable from Hugging Face.
- **`generated_text/`** — regenerable.
- **`.venv/`, `__pycache__/`** — environment junk.

Accidentally staged a secret? Remove it **before committing**:
```bash
git restore --staged .env
```
Already committed a secret? Rotate the key immediately (assume it's compromised) and remove it
from history — ask before doing history rewrites on a shared repo.

---

## 9. Suggested team conventions

- **Branch names:** `feature/...`, `fix/...`, `docs/...`, `chore/...`.
- **Commit messages:** imperative mood, ≤ 72 chars on the first line.
  - ✅ `Add Gemini provider with retry`
  - ❌ `changes` / `stuff` / `asdf`
- **Small PRs** are easier to review than one giant one.
- **Pull before you push.** Always `git pull origin main` before starting work.
- **One feature = one branch = one PR.**

---

## 10. First push for THIS repo (maintainer only)

The repo currently has just a stub README. To publish these docs + scripts the first time:

```bash
cd KokoroTTS
git checkout main
git pull origin main             # get whatever is on the remote

git add README.md requirements.txt .env.example .gitignore docs/
# (add generate.py tts_blend.py download_voices.py once you create them)
git commit -m "Add full documentation, scripts, and project scaffolding"
git push origin main
```

If your local `main` and remote have diverged (e.g. remote already has commits):
```bash
git pull origin main --no-rebase     # merge remote into local
# resolve conflicts if any (see §6), then:
git push origin main
```

That's everything. Next, the error catalogue → [08 – Troubleshooting](08-troubleshooting.md).

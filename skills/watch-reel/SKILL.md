---
name: watch-reel
description: "Watch and analyze an Instagram reel or post like the youtube `watch` skill. Downloads the video via gallery-dl using the user's logged-in Chrome cookies, extracts frames at every scene change, and transcribes the spoken audio locally with mlx-whisper — then answers grounded in what's SHOWN and what's SAID. Use this whenever the user pastes an instagram.com reel/post/profile URL, says 'analyze this reel', 'what's in this IG video', 'reverse-engineer this reel', 'transcribe this instagram', or points at a local reel file and asks about its content, hook, editing, or structure. Trigger it even if they don't say the word 'reel' but clearly want you to understand an Instagram video you can't otherwise see."
argument-hint: "<instagram-url-or-local-video> [what you want to know]"
allowed-tools: Bash, Read, AskUserQuestion
user-invocable: true
license: MIT
---

# /reel — Claude watches an Instagram reel

You have no video input. This skill gives you one for Instagram. A Python script downloads the reel (gallery-dl, authenticated via the user's Chrome cookies), extracts frames as JPEGs (one per detected scene / on-screen text swap), and transcribes the spoken audio **locally** with mlx-whisper. You then `Read` each frame to see the images, combine them with the timestamped transcript + the post caption, and answer the user's question grounded in both streams.

It works the same way `watch` does for YouTube — the difference is Instagram is login-gated, so the download uses the user's browser session instead of yt-dlp.

## When to use

- The user pastes an **instagram.com** reel, post, or profile URL and asks anything about it.
- The user points at a **local** reel file (`.mp4`) and asks about its content, hook, pacing, or on-screen text.
- The user wants to **reverse-engineer** a reel's structure/style (like the davidexplains analysis).
- They type `/reel <url> [question]`.

## How to invoke

**Step 1 — split input.** Separate the source (URL or path) from the question. The question is the lens for your answer.

**Step 2 — run the script.** Pass the source verbatim:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/reel.py" "<source>"
```

Useful flags:
- `--max-frames N` — cap frames (default budgets by duration: ≤30s→24, ≤60s→36, ≤3min→48, else 60).
- `--model <mlx-whisper-model>` — default `mlx-community/whisper-large-v3-turbo` (accurate + fast on Apple Silicon; first run downloads the model). Use `mlx-community/whisper-tiny` for a quick, low-accuracy pass.
- `--no-transcribe` — frames only.
- `--cookies <cookies.txt>` — use an exported cookie file instead of live Chrome cookies.
- `--out-dir DIR` — keep working files somewhere specific (default: a temp dir).

The script prints a `WORKDIR`, the `POST CAPTION`, the `TRANSCRIPT (srt)` path, and a numbered list of `FRAMES`.

**Step 3 — Read every frame.** Read all the listed frame paths **in one message** (parallel `Read` calls) so you see them together, in order. The Read tool renders JPEGs as images.

**Step 4 — answer.** You now have three evidence streams: the **frames** (what's on screen), the **transcript** (`audio.srt`, timestamped — what's said), and the **post caption** (the written text of the post). Answer the user's question citing what you saw and heard. For a reverse-engineering ask, break down the hook (first 1-3s), the beat structure, the on-screen text treatment, and the edit pacing — the way `davidexplains-analysis/PATTERN.md` does.

**Step 5 — clean up.** The script prints its workdir. If the user won't ask follow-ups, `rm -rf` it. If they might, leave it (you already have the frames + transcript in context, so don't re-run for a follow-up).

## Instagram login (the one gotcha)

Instagram requires a logged-in session. gallery-dl reads it from Chrome via `--cookies-from-browser chrome`. If the script exits with **`LOGIN_REQUIRED`**, the cookies had no live instagram.com session (logged out or expired). Tell the user plainly:

> Instagram sent gallery-dl to the login page. Open Chrome, log into instagram.com, then re-run — or pass `--cookies <cookies.txt>` exported from a logged-in browser.

Do not retry in a loop. A local file path always works (no login needed).

## Transcription

`mlx-whisper` runs the model **locally on Apple Silicon** — the audio never leaves the machine (unlike `watch`, which uploads to a Whisper API). The script extracts mono 16 kHz audio with ffmpeg, runs mlx-whisper to an `.srt`, and points you at it. If there's no speech (music-only reel), the transcript is empty — lean on the frames and the post caption.

## Dependencies

- `gallery-dl` and `mlx-whisper` run through `uv` (`uvx`) if not installed — no global install needed. Per the user's setup, use `uv`, never `pip`.
- `ffmpeg` / `ffprobe` must be on PATH (Homebrew: `brew install ffmpeg`).
- mlx-whisper needs Apple Silicon. On other hardware, swap in a different transcriber or use `--no-transcribe`.

Review `scripts/reel.py` before first use to verify behavior.

## Security & Permissions

- Runs `gallery-dl` locally, using the user's Chrome cookies **only** to authenticate the Instagram download (the request goes to instagram.com). It does not post, follow, or change anything on the account.
- Runs `ffmpeg`/`ffprobe` locally to extract frames and audio.
- Transcribes **locally** with mlx-whisper — no audio or video is uploaded anywhere.
- Writes the video, frames, audio, and transcript to a working directory (temp dir or `--out-dir`). Nothing is persisted outside it. Clean up in Step 5.
- Copyright note for onward use: downloading a reel to analyze it is fine; **republishing** someone else's reel footage is the user's call and their responsibility, not something this skill does.

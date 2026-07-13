#!/usr/bin/env python3
"""reel.py — "watch" an Instagram reel/post (or any local video).

Downloads via gallery-dl using the user's Chrome login cookies, extracts frames
at scene changes (one per shot / per on-screen text swap), and transcribes the
spoken audio locally with mlx-whisper. Prints frame paths + transcript so Claude
can Read the images and answer grounded in what's shown AND said.

Instagram is login-gated, so downloading needs a Chrome that is logged into
instagram.com. If the session is missing/expired, gallery-dl gets redirected to
the login page — the script reports that clearly instead of failing silently.

Usage:
    python3 reel.py <instagram-url-or-local-video> [--out-dir DIR] [--max-frames N]
        [--model MLX_WHISPER_MODEL] [--no-transcribe] [--cookies FILE]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def tool(name):
    """Prefer an installed binary; otherwise run it through uv (uvx)."""
    return [name] if shutil.which(name) else ["uvx", name]


def is_url(s):
    return s.startswith("http://") or s.startswith("https://")


def download(url, outdir, cookies):
    gdl = tool("gallery-dl")
    if cookies:
        cmd = gdl + ["--cookies", cookies, "-D", str(outdir), url]
    else:
        cmd = gdl + ["--cookies-from-browser", "chrome", "-D", str(outdir), url]
    p = sh(cmd)
    blob = (p.stdout + p.stderr).lower()
    if "redirect to login" in blob or "accounts/login" in blob:
        sys.exit(
            "LOGIN_REQUIRED: Instagram redirected gallery-dl to the login page.\n"
            "Chrome has no live instagram.com session (logged out or expired).\n"
            "Fix: open Chrome, log into instagram.com, then re-run. "
            "Or pass --cookies <cookies.txt> exported from a logged-in browser."
        )
    vids = sorted(Path(outdir).rglob("*.mp4"))
    if not vids:
        sys.exit(f"No video downloaded. gallery-dl said:\n{p.stdout}\n{p.stderr}")
    return vids


def caption_for(video: Path):
    """Instagram post caption sits in gallery-dl's .json sidecar (the written
    text of the post, not the spoken words). Useful extra context."""
    j = video.with_suffix(".mp4.json")
    if not j.exists():
        j = video.with_suffix(".json")
    if j.exists():
        try:
            d = json.loads(j.read_text())
            return d.get("description") or d.get("caption") or ""
        except Exception:
            return ""
    return ""


def duration(video: Path):
    p = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(video)])
    try:
        return float(p.stdout.strip())
    except ValueError:
        return 0.0


def frame_budget(dur):
    if dur <= 30:
        return 24
    if dur <= 60:
        return 36
    if dur <= 180:
        return 48
    return 60


def extract_frames(video: Path, outdir: Path, max_frames):
    outdir.mkdir(parents=True, exist_ok=True)
    dur = duration(video)
    budget = min(max_frames, frame_budget(dur))
    # 1) scene-change frames: one per detected cut / on-screen swap
    sh(["ffmpeg", "-v", "error", "-i", str(video),
        "-vf", "select='gt(scene,0.30)',scale=640:-1", "-vsync", "vfr",
        str(outdir / "scene-%03d.jpg")])
    frames = sorted(outdir.glob("scene-*.jpg"))
    # 2) if too few scenes (static reel), fall back to uniform sampling to budget
    if len(frames) < 8 and dur > 0:
        for f in frames:
            f.unlink()
        fps = min(2.0, budget / dur)
        sh(["ffmpeg", "-v", "error", "-i", str(video),
            "-vf", f"fps={fps:.4f},scale=640:-1",
            str(outdir / "u-%03d.jpg")])
        frames = sorted(outdir.glob("u-*.jpg"))
    # 3) thin evenly if a busy reel blew past the budget
    if len(frames) > budget:
        step = len(frames) / budget
        keep = {frames[min(len(frames) - 1, round(i * step))] for i in range(budget)}
        for f in frames:
            if f not in keep:
                f.unlink()
        frames = sorted(f for f in frames if f.exists())
    return frames, dur


def transcribe(video: Path, outdir: Path, model):
    audio = outdir / "audio.wav"
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(video),
        "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    if not audio.exists() or audio.stat().st_size < 2000:
        return None  # no/again tiny audio track
    # mlx-whisper (Apple Silicon, local, private). Package name != command name.
    cmd = (["mlx_whisper"] if shutil.which("mlx_whisper")
           else ["uvx", "--from", "mlx-whisper", "mlx_whisper"])
    cmd += [str(audio), "--model", model, "--output-format", "srt",
            "--output-dir", str(outdir)]
    p = sh(cmd)
    srt = outdir / "audio.srt"
    if srt.exists():
        return srt
    print(f"[transcribe] mlx-whisper failed:\n{p.stderr[-800:]}", file=sys.stderr)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="Instagram URL, or a local video path")
    ap.add_argument("--out-dir")
    ap.add_argument("--max-frames", type=int, default=60)
    ap.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    ap.add_argument("--no-transcribe", action="store_true")
    ap.add_argument("--cookies", help="cookies.txt (instead of --cookies-from-browser chrome)")
    a = ap.parse_args()

    work = Path(a.out_dir) if a.out_dir else Path(tempfile.mkdtemp(prefix="reel-"))
    work.mkdir(parents=True, exist_ok=True)

    caption = ""
    if is_url(a.source):
        dl = work / "dl"
        vids = download(a.source, dl, a.cookies)
        video = vids[0]
        caption = caption_for(video)
    else:
        video = Path(a.source).expanduser()
        if not video.exists():
            sys.exit(f"No such file: {video}")

    frames, dur = extract_frames(video, work / "frames", a.max_frames)
    srt = None if a.no_transcribe else transcribe(video, work, a.model)

    print("\n=== REEL READY ===")
    print(f"WORKDIR: {work}")
    print(f"VIDEO: {video}  ({dur:.1f}s)")
    if caption:
        print(f"POST CAPTION: {caption[:600]}")
    print(f"TRANSCRIPT (srt): {srt if srt else 'none (no speech or transcribe skipped)'}")
    print(f"\nFRAMES ({len(frames)}) — Read each in order:")
    for f in frames:
        print(f"  {f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Download every CDN asset the source pages reference, once, at a sensible size.

Reads reference/assets-all.txt (built by harvest steps), collapses the
responsive-size variants down to one file per base path, and mirrors the CDN
path under assets/img/cdn/ so the replica's markup can reference the same
paths relatively. Videos are listed, not downloaded; a decision about each
happens by hand because of their size.
"""
import os
import pathlib
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "reference" / "assets-all.txt"
DEST = ROOT / "assets" / "img" / "cdn"
PREFIX = "https://assets.hyundai-me.com/client-mynaghi-production/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

bases = {}
videos = set()
others = set()
for line in SRC.read_text().splitlines():
    url = line.strip().replace("&amp;", "&")
    if not url.startswith(PREFIX):
        others.add(url)
        continue
    base = url.split("?")[0]
    ext = base.rsplit(".", 1)[-1].lower()
    if ext == "mp4":
        videos.add(base)
        continue
    bases[base] = ext

print(f"{len(bases)} unique image/doc files, {len(videos)} videos, {len(others)} non-CDN urls")

fail = []
done = 0
skipped = 0
for base, ext in sorted(bases.items()):
    rel = urllib.parse.unquote(base[len(PREFIX):])
    out = DEST / rel
    if out.exists() and out.stat().st_size > 0:
        skipped += 1
        continue
    out.parent.mkdir(parents=True, exist_ok=True)
    # The CDN pre-compresses when asked. Large photography gets the 1200px webp
    # transform; png and svg keep their original bytes (transparency, icons).
    if ext in ("webp", "jpg", "jpeg"):
        url = base + "?w=1200&q=80&ext=webp"
    else:
        url = base
    code = subprocess.run(
        ["curl", "-sL", "-A", UA, "--max-time", "60", "-o", str(out), "-w", "%{http_code}", url],
        capture_output=True, text=True).stdout.strip()
    if code != "200" or not out.exists() or out.stat().st_size == 0:
        # One retry on the untransformed original before giving up.
        code2 = subprocess.run(
            ["curl", "-sL", "-A", UA, "--max-time", "60", "-o", str(out), "-w", "%{http_code}", base],
            capture_output=True, text=True).stdout.strip()
        if code2 != "200" or not out.exists() or out.stat().st_size == 0:
            fail.append((base, code, code2))
            if out.exists():
                out.unlink()
            continue
    done += 1
    if done % 50 == 0:
        print(f"  {done} downloaded...")

(ROOT / "reference" / "videos.txt").write_text("\n".join(sorted(videos)) + "\n")
print(f"downloaded {done}, already had {skipped}, failed {len(fail)}")
for f in fail[:20]:
    print("  FAIL", f)
size = subprocess.run(["du", "-sh", str(DEST)], capture_output=True, text=True).stdout
print("assets/img/cdn size:", size.strip())

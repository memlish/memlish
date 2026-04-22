"""Download a curated set of meme templates from the imgflip public API.

Usage: uv run python scripts/fetch_templates.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

from memlish_reborn.config import TEMPLATES_DIR

API_URL = "https://api.imgflip.com/get_memes"
UA = "memlish-reborn/0.1 (+https://github.com/memlish)"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "meme"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30, help="How many templates to download")
    parser.add_argument(
        "--out", type=Path, default=TEMPLATES_DIR, help="Where to save template images"
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    req = urllib.request.Request(API_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if not payload.get("success"):
        print(f"imgflip API error: {payload}", file=sys.stderr)
        return 1

    memes = payload["data"]["memes"][: args.limit]
    print(f"Fetching {len(memes)} templates → {args.out}")

    for meme in memes:
        url = meme["url"]
        ext = Path(url).suffix.lower() or ".jpg"
        filename = f"{meme['id']}_{slugify(meme['name'])}{ext}"
        dest = args.out / filename
        if dest.exists():
            print(f"  [skip] {filename}")
            continue
        try:
            img_req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(img_req, timeout=30) as r, open(dest, "wb") as f:
                f.write(r.read())
            print(f"  [ok]   {filename}  ({meme['name']})")
        except Exception as e:
            print(f"  [err]  {filename}: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Encode every template image under data/templates into CLIP image embeddings.

Output:
  data/embeddings.npy   — (N, D) float32, L2-normalized
  data/metadata.json    — list[dict] with filename, name

Usage: uv run python scripts/build_index.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from memlish_reborn.config import EMBEDDINGS_PATH, METADATA_PATH, TEMPLATES_DIR
from memlish_reborn.embed import ClipEncoder

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def humanize(stem: str) -> str:
    # "181913649_drake-hotline-bling" -> "Drake Hotline Bling"
    without_id = re.sub(r"^\d+_", "", stem)
    return without_id.replace("-", " ").replace("_", " ").strip().title()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--templates-dir", type=Path, default=TEMPLATES_DIR)
    parser.add_argument("--embeddings-out", type=Path, default=EMBEDDINGS_PATH)
    parser.add_argument("--metadata-out", type=Path, default=METADATA_PATH)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    files = sorted(
        p for p in args.templates_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS
    )
    if not files:
        print(f"No templates found in {args.templates_dir}", file=sys.stderr)
        return 1
    print(f"Encoding {len(files)} templates from {args.templates_dir}")

    encoder = ClipEncoder()
    all_embeddings: list[np.ndarray] = []
    metadata: list[dict] = []

    t0 = time.time()
    for start in range(0, len(files), args.batch_size):
        batch = files[start : start + args.batch_size]
        images = [Image.open(p) for p in batch]
        embs = encoder.encode_images(images)
        all_embeddings.append(embs)
        for p in batch:
            metadata.append({"filename": p.name, "name": humanize(p.stem)})
        print(f"  [{start + len(batch)}/{len(files)}]")

    embeddings = np.vstack(all_embeddings)
    args.embeddings_out.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.embeddings_out, embeddings)
    args.metadata_out.write_text(json.dumps(metadata, indent=2))
    print(
        f"Saved {embeddings.shape} to {args.embeddings_out} "
        f"in {time.time() - t0:.1f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

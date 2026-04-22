from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("MEMLISH_DATA_DIR", ROOT / "data"))

TEMPLATES_DIR = DATA_DIR / "templates"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.npy"
METADATA_PATH = DATA_DIR / "metadata.json"
FILE_IDS_PATH = DATA_DIR / "file_ids.json"
RENDERED_DIR = DATA_DIR / "rendered"

FONT_PATH = ROOT / "src" / "memlish_reborn" / "assets" / "impact.ttf"

CLIP_MODEL = os.environ.get("MEMLISH_CLIP_MODEL", "openai/clip-vit-base-patch32")
DEVICE = os.environ.get("MEMLISH_DEVICE", "cpu")

TOP_K = int(os.environ.get("MEMLISH_TOP_K", "15"))
IMAGE_MAX_SIDE = 256

BOT_TOKEN = os.environ.get("BOT_TOKEN")
STAGING_CHAT_ID = os.environ.get("MEMLISH_STAGING_CHAT_ID")

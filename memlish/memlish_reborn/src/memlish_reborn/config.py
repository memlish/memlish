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

FONT_PATH = Path(__file__).resolve().parent / "assets" / "impact.ttf"

CLIP_MODEL = os.environ.get("MEMLISH_CLIP_MODEL", "openai/clip-vit-base-patch32")
DEVICE = os.environ.get("MEMLISH_DEVICE", "cpu")

TOP_K = int(os.environ.get("MEMLISH_TOP_K", "15"))
IMAGE_MAX_SIDE = 256

BOT_TOKEN = os.environ.get("BOT_TOKEN")
STAGING_CHAT_ID = os.environ.get("MEMLISH_STAGING_CHAT_ID")


def _bool(key: str, default: str = "false") -> bool:
    return os.environ.get(key, default).lower() in ("1", "true", "t", "yes")


USE_POLLING = _bool("USE_POLLING", "false")
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "")
WEBHOOK_PATH = f"/{BOT_TOKEN}" if BOT_TOKEN else ""
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST and BOT_TOKEN else ""
WEBAPP_HOST = os.environ.get("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.environ.get("WEBAPP_PORT", "7654"))
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

DELIVERY_MODE = os.environ.get("MEMLISH_DELIVERY", "file_id").lower()
PUBLIC_BASE_URL = os.environ.get("MEMLISH_PUBLIC_BASE_URL", WEBHOOK_HOST).rstrip("/")

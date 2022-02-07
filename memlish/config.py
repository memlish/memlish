from pathlib import Path
import os


def _get_bool(key: str) -> bool:
    return os.environ.get(key, 'False').lower() in ('true', '1', 't')

# BOT ENV VARS


BOT_TOKEN = os.environ['BOT_TOKEN']
SERVER_NAME = os.environ['SERVER_NAME']
USE_POLLING = _get_bool('USE_POLLING')
SHOW_K_MEMES = 20

# SERVER ENV VARS

JINA_FLOW_PORT = os.environ['JINA_FLOW_PORT']

PUBLIC_FILES_URL = f"http://{SERVER_NAME}/static_memes/"

IMAGE_DIR = Path('/data/reddit/images/images/')

JINA_EMBS_COLLECTION_NAME = "00_clip_vit_base_patch32_image_reddit_500k_embeddings"

EMBEDDER_PARAMS = {
    "batch_size": 64,
    "device": 'cuda'
}

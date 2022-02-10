from pathlib import Path
import os


def _get_bool(key: str) -> bool:
    return os.environ.get(key, 'False').lower() in ('true', '1', 't')

# BOT ENV VARS


class ESTag:
    INLINE_CHOICE = "INLINE_CHOICE"
    INLINE_ANSWER = "INLINE_ANSWER"


BOT_TOKEN = os.environ['BOT_TOKEN']
SERVER_NAME = os.environ['SERVER_NAME']
USE_POLLING = _get_bool('USE_POLLING')
SHOW_K_MEMES = 50

# SERVER ENV VARS
JINA_FLOW_PORT = os.environ['JINA_FLOW_PORT']

PUBLIC_FILES_URL = f"http://{SERVER_NAME}/static_memes/"

IMAGE_DIR = Path('/data/reddit/images/images/')
IMGFLIP_DIR = Path("/data/imgflip/scrap_language_image_pairs_20220209/images/")

MONGODB_CONNECTION_STRING = os.environ.get('MONGODB_CONNECTION_STRING', None)
MONGO_EMBEDDING_DB_NAME = 'memlish_db'

JINA_EMBS_COLLECTION_NAME = "00_clip_vit_base_patch32_image_reddit_500k_embeddings"
JINA_SBERT_EMBEDDING_TEMPLATE_TEXT_COLLECTION = "00_sbert_all_mpnet_base_v2_imgflip_template_1400k_embeddings"

EMBEDDER_PARAMS = {
    "batch_size": 64,
    "device": 'cuda'
}

FONTS_PATH = Path('/app/memlish/image_processing/fonts')

from pathlib import Path
import os


def _get_bool(key: str, default='False') -> bool:
    return os.environ.get(key, default).lower() in ('true', '1', 't')


IMGFLIP_DIR = Path('/data/imgflip/')


# BOT ENV VARS
class ESTag:
    INLINE_CHOICE = "INLINE_CHOICE"
    INLINE_ANSWER = "INLINE_ANSWER"
    TIMELOG = "TIMELOG"


WEBHOOK_SSL_CERT_PATH = Path('/certs/cert.pem')

BOT_TOKEN = os.environ['BOT_TOKEN']
SERVER_NAME = os.environ['SERVER_NAME']
USE_POLLING = _get_bool('USE_POLLING')
DEBUG_MODE = _get_bool('DEBUG_MODE', 'True')

WEBHOOK_URL = f'https://{SERVER_NAME}/{BOT_TOKEN}'
WEBHOOK_PATH = f'/{BOT_TOKEN}'

SHOW_K_MEMES = 50

# SERVER ENV VARS
JINA_FLOW_PORT = os.environ['JINA_FLOW_PORT']

PUBLIC_FILES_URL = f"http://{SERVER_NAME}/static_memes/"

REDDIT_IMAGES_DIR = Path('/data/reddit/images/images/')
IMGFLIP_IMAGES_DIR = IMGFLIP_DIR/'scrap_language_image_pairs_20220209/images/'

MONGODB_CONNECTION_STRING = os.environ.get('MONGODB_CONNECTION_STRING', None)
MONGO_EMBEDDING_DB_NAME = 'memlish_db'

DROWN_IMAGE_DIR = IMGFLIP_DIR / 'drown_images'

JINA_EMBS_COLLECTION_NAME = "00_clip_vit_base_patch32_image_reddit_500k_embeddings"
JINA_SBERT_EMBEDDING_TEMPLATE_TEXT_COLLECTION = "01_sbert_all_mpnet_base_v2_imgflip_template_100k_embeddings"

FONTS_PATH = Path('/app/memlish/image_processing/fonts')

from pathlib import Path

IMAGE_DIR = Path('/data/reddit/images/images/')

JINA_EMBS_COLLECTION_NAME = "00_clip_vit_base_patch32_image_reddit_500k_embeddings"

EMBEDDER_PARAMS = {
    "batch_size": 64,
    "device": 'cuda'
}

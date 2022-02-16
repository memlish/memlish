import sys
sys.path.append('/app')  # noqa
sys.path.append('/app/loopa')  # noqa

from jina import Document, DocumentArray, AsyncFlow, Executor, requests
from pathlib import Path
import argparse
from memlish.executors.bert import RealSBERTEncoder
from memlish.executors.index import FaissIndexer
from memlish.executors.docs_formatter import DocPostFormatter, DocPreFormatter
from memlish.executors.transalator import AwsTranslator
from memlish.config import IMGFLIP_IMAGES_DIR, JINA_SBERT_EMBEDDING_TEMPLATE_TEXT_COLLECTION, DROWN_IMAGE_DIR
from memlish.executors.text_drawer import TextDrawer
import torch


# available
# 'spawn' to use cuda, but you cant use executors from package and notebook
# 'fork' to use executors from package and notebook, but you can use only cpu
torch.multiprocessing.set_start_method('spawn', force=True)


Path.ls = lambda x: list(x.iterdir())


def parse_args():
    parser = argparse.ArgumentParser(description='Our Jina.')
    parser.add_argument('--port', type=int)

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    print('args', args)

    embedder_params = {
        "device": 'cpu'
    }

    faiss_indexer_params = {
        "reference_img_dir": str(IMGFLIP_IMAGES_DIR),
        "collection_name": JINA_SBERT_EMBEDDING_TEMPLATE_TEXT_COLLECTION
    }

    drawer_params = {
        "templates_dir": str(IMGFLIP_IMAGES_DIR),
        "out_path": str(DROWN_IMAGE_DIR),
        "max_width": 256,
        "max_height": 256
    }

    flow_search = AsyncFlow().add(uses=DocPreFormatter, name="pre_formatter") \
        .add(uses=AwsTranslator, name="tranlator") \
        .add(uses=RealSBERTEncoder, name="encoder", uses_with=embedder_params, replicas=1) \
        .add(uses=FaissIndexer, name="indexer", workspace="workspace", uses_with=faiss_indexer_params, replicas=1) \
        .add(uses=TextDrawer, name=f"drawer", uses_with=drawer_params, replicas=1) \
        .add(uses=DocPostFormatter, name="post_formatter")

    flow_search.port_expose = args.port
    flow_search.protocol = 'http'

    with flow_search:
        flow_search.block()


if __name__ == '__main__':
    main()

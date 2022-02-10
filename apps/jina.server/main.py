import sys
sys.path.append('/app')  # noqa
sys.path.append('/app/loopa')  # noqa

from jina import Document, DocumentArray, Flow, Executor, requests
from pathlib import Path
import argparse
from loopa.executors.bert import SBERTEncoder
from memlish.executors.index import FaissIndexer
from memlish.executors.docs_formatter import DocsFormatter
from memlish.config import IMGFLIP_IMAGES_DIR, DROWN_IMAGE_DIR, JINA_SBERT_EMBEDDING_TEMPLATE_TEXT_COLLECTION
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
        "device": 'cuda'
    }

    faiss_indexer_params = {
        "reference_img_dir": str(IMGFLIP_IMAGES_DIR),
        "collection_name": JINA_SBERT_EMBEDDING_TEMPLATE_TEXT_COLLECTION
    }

    drawer_params = {
        "out_path": str(DROWN_IMAGE_DIR)
    }

    flow_search = Flow().add(uses=SBERTEncoder, name="encoder", uses_with=embedder_params) \
                        .add(uses=FaissIndexer, name="indexer", workspace="workspace", uses_with=faiss_indexer_params) \
                        .add(uses=TextDrawer, name=f"drawer", uses_with=drawer_params) \
                        .add(uses=DocsFormatter, name="formatter")

    flow_search.port_expose = args.port
    flow_search.protocol = 'http'

    with flow_search:
        flow_search.block()


if __name__ == '__main__':
    main()

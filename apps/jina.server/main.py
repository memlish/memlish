import sys
sys.path.append('/app')  # noqa

from jina import Document, DocumentArray, Flow, Executor, requests
from pathlib import Path
import argparse
from loopa.executors.clip import CLIPTextEncoder
from loopa.executors.index import FaissIndexer, IndexMerger
from config import IMAGE_DIR, JINA_EMBS_COLLECTION_NAME, EMBEDDER_PARAMS
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

    faiss_indexer_params = {
        "reference_img_dir": str(IMAGE_DIR),
        "collection_name": JINA_EMBS_COLLECTION_NAME
    }

    flow_search = Flow().add(uses=CLIPTextEncoder, name=f"CLIPTextEncoder", uses_with=EMBEDDER_PARAMS, needs='gateway')\
                        .add(uses=FaissIndexer, name=f"FaissIndexer", workspace="workspace", uses_with=faiss_indexer_params)\
                        .needs_all(uses=IndexMerger, name="merger")

    flow_search.port_expose = args.port
    flow_search.protocol = 'http'

    with flow_search:
        flow_search.block()


if __name__ == '__main__':
    main()

from jina import DocumentArray, Executor, requests, DocumentArrayMemmap, Document
from typing import Dict, Optional, Tuple, Sequence
from copy import deepcopy
import inspect
from pathlib import Path
import faiss
import time
import numpy as np

from memlish.config import MONGO_EMBEDDING_DB_NAME, JINA_SBERT_EMBEDDING_TEMPLATE_TEXT_COLLECTION, MONGODB_CONNECTION_STRING
from loopa.executors.cache import read_all_embeddings, get_mongo_collection

class FaissIndexer(Executor):

    def __init__(
        self,
        reference_img_dir: str,
        collection_name: str,
        embedding_field_name: str = 'emb',
        connection_string=MONGODB_CONNECTION_STRING,
        db_name=MONGO_EMBEDDING_DB_NAME,
        match_args: Optional[Dict] = None,
        **kwargs,
    ):

        super().__init__(**kwargs)

        self.reference_dir = Path(reference_img_dir)
        assert self.reference_dir.exists(
        ), f"Directory with reference images does not exists! {self.reference_dir}"

        self._match_args = match_args or {}
        self.collection = get_mongo_collection(
            connection_string, db_name, collection_name)
        self.filenames, self.embs = read_all_embeddings(
            self.collection, embedding_field_name)
        
        # filename_texthash -> filename
        self.filenames = np.array(["_".join(filename.split("_")[:-1]) for filename in self.filenames])

        self.metric = faiss.METRIC_INNER_PRODUCT  # TODO: make it as parameter

        faiss.normalize_L2(self.embs)

        xb = self.embs
        self.index = faiss.IndexFlat(xb.shape[1], self.metric)
        self.index.add(xb)
        print('Index intitialized successfully!')

    @requests(on='/search')
    def search(
        self,
        docs: Optional['DocumentArray'] = None,
        parameters: Dict = {},
        **kwargs,
    ):
        if not docs:
            return

        top_k = int(parameters.get("top_k", 10))
        normalized = parameters.get("normalized", False)

        start = time.time()
        embeddings = docs.embeddings

        if not normalized:
            faiss.normalize_L2(embeddings)

        D, I = self.index.search(embeddings, k=len(self.embs))
        
        for i, doc in enumerate(docs): 
            # TODO: come up with better fix for shared indexer
            if doc.embedding is None:
                continue

            match_idxs = I[i, :]
            ids = self.filenames[match_idxs]
            unique, id_idxs = np.unique(ids, return_index=True)
            k_id_idxs = sorted(id_idxs)[:top_k]
            top_ids = ids[k_id_idxs]
            top_scores = D[i, k_id_idxs]
            
            matched_docs = []
            for _id, _score in zip(top_ids, top_scores):
                match_doc = Document(
                    id=_id, uri=str(self.reference_dir/_id))
                match_doc.scores[str(self.metric)] = _score
                matched_docs.append(match_doc)

            doc.matches = matched_docs
        
        end = time.time()
        print("end - start", end - start)
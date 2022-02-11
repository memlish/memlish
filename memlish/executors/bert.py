from sentence_transformers import SentenceTransformer
from jina import DocumentArray, Executor, requests
import torch
from typing import Optional, Tuple, Sequence
from memlish.io.timelog import log_duration


class RealSBERTEncoder(Executor):
    """Encode text into embeddings using SBERT model."""

    def __init__(
        self,
        pretrained_model_name_or_path: str = 'all-mpnet-base-v2',
        device: str = 'cpu',
        batch_size: int = 64,
        traversal_paths: str = 'r',
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.traversal_paths = traversal_paths

        self.pretrained_model_name_or_path = pretrained_model_name_or_path

        self.executor_name = None
        if kwargs.get("runtime_args"):
            if kwargs["runtime_args"].get("name"):
                self.executor_name = kwargs["runtime_args"]["name"]

        self.batch_size = batch_size
        self.device = device
        self.model = SentenceTransformer(
            pretrained_model_name_or_path, device=device)

        self.model.eval().to(self.device)

    @requests
    @log_duration
    def get_embeddings(self, docs: Optional[DocumentArray], parameters: dict, **kwargs):
        if docs is None:
            return

        document_batches_generator = docs.traverse_flat(self.traversal_paths).batch(
            batch_size=self.batch_size
        )

        for batch_docs in document_batches_generator:
            texts = []
            for doc in batch_docs:
                texts.append(doc.text)

            embeddings = self.model.encode(texts, batch_size=self.batch_size)

            for doc, embedding in zip(batch_docs, embeddings):
                doc.tags["embedder_tag"] = self.executor_name
                doc.embedding = embedding

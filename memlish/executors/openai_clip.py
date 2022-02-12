from typing import Optional, Tuple, Sequence
import clip
from jina import DocumentArray, Executor, requests
import torch
from torch import nn
from PIL import Image


class OpenAICLIPTextEncoder(Executor):
    """Encode text into embeddings using the CLIP model."""

    def __init__(
        self,
        pretrained_model_name_or_path: str = 'ViT-L/14',
        max_length: int = 77,
        device: str = 'cpu',
        traversal_paths='r',
        batch_size: int = 32,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.traversal_paths = traversal_paths
        self.batch_size = batch_size
        self.pretrained_model_name_or_path = pretrained_model_name_or_path
        self.max_length = max_length

        self.executor_name = None
        if kwargs.get("runtime_args"):
            if kwargs["runtime_args"].get("name"):
                self.executor_name = kwargs["runtime_args"]["name"]

        self.device = device
        self.tokenizer = clip.tokenize
        self.model, _ = clip.load(pretrained_model_name_or_path, device=device)

    @requests
    def get_embeddings(self, docs: Optional[DocumentArray], **kwargs):
        if docs is None:
            return

        for docs_batch in docs.traverse_flat(self.traversal_paths).batch(
            batch_size=self.batch_size
        ):
            text_batch = docs_batch.get_attributes('text')

            with torch.inference_mode():
                input_tokens = self._generate_input_tokens(text_batch)
                embeddings = self.model.encode_text(
                    input_tokens).cpu().numpy()
                for doc, embedding in zip(docs_batch, embeddings):
                    doc.tags["embedder_tag"] = self.executor_name
                    doc.embedding = embedding

    def _generate_input_tokens(self, texts: Sequence[str]):

        input_tokens = self.tokenizer(
            texts,
            context_length=self.max_length,
            truncate=True
        ).to(self.device)
        # input_tokens = {k: v.to(self.device) for k, v in input_tokens.items()}
        return input_tokens


class OpenAICLIPImageEncoder(Executor):
    """Encode image into embeddings using the CLIP model."""

    def __init__(
        self,
        pretrained_model_name_or_path: str = "ViT-L/14",
        device: str = "cpu",
        batch_size: int = 32,
        traversal_paths='r',
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size
        self.traversal_paths = traversal_paths
        self.pretrained_model_name_or_path = pretrained_model_name_or_path

        self.executor_name = None
        if kwargs.get("runtime_args"):
            if kwargs["runtime_args"].get("name"):
                self.executor_name = kwargs["runtime_args"]["name"]

        self.device = device
        self.model, self.preprocessor = clip.load(
            pretrained_model_name_or_path, device=device)

    @requests
    def get_embeddings(self, docs: Optional[DocumentArray], **kwargs):
        if docs is None:
            return

        document_batches_generator = docs.traverse_flat(self.traversal_paths).batch(
            batch_size=self.batch_size
        )

        with torch.inference_mode():
            for batch_docs in document_batches_generator:
                blob_batch = []

                for d in batch_docs:
                    d.load_uri_to_image_blob()
                    blob_batch.append(d.blob)

                tensor = self._generate_input_features(blob_batch)

                embeddings = self.model.encode_image(tensor)
                embeddings = embeddings.cpu().numpy()

                for doc, embed in zip(batch_docs, embeddings):
                    doc.tags["embedder_tag"] = self.executor_name
                    doc.embedding = embed
                    doc.blob = None

    def _generate_input_features(self, images):
        input_tokens = []
        for image in images:
            input_tokens.append(self.preprocessor(
                Image.fromarray(image)).to(self.device))
        input_tokens = torch.stack(input_tokens)

        return input_tokens

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from memlish_reborn.config import EMBEDDINGS_PATH, METADATA_PATH, TEMPLATES_DIR
from memlish_reborn.embed import ClipEncoder, get_encoder


@dataclass(frozen=True)
class Match:
    filename: str
    path: Path
    name: str
    score: float


class MemeIndex:
    """In-memory index: L2-normalized template embeddings + metadata.

    Search is a single numpy matmul — fast and exact for up to ~500k templates."""

    def __init__(
        self,
        embeddings: np.ndarray,
        metadata: list[dict],
        templates_dir: Path,
        encoder: ClipEncoder | None = None,
    ):
        assert embeddings.ndim == 2
        assert len(metadata) == embeddings.shape[0]
        self.embeddings = embeddings.astype(np.float32, copy=False)
        self.metadata = metadata
        self.templates_dir = templates_dir
        self._encoder = encoder

    @property
    def encoder(self) -> ClipEncoder:
        if self._encoder is None:
            self._encoder = get_encoder()
        return self._encoder

    @classmethod
    def load(
        cls,
        embeddings_path: Path = EMBEDDINGS_PATH,
        metadata_path: Path = METADATA_PATH,
        templates_dir: Path = TEMPLATES_DIR,
    ) -> "MemeIndex":
        embeddings = np.load(embeddings_path)
        metadata = json.loads(metadata_path.read_text())
        return cls(embeddings, metadata, templates_dir)

    def search(self, query: str, top_k: int = 15) -> list[Match]:
        query_emb = self.encoder.encode_text([query])[0]
        return self.search_vec(query_emb, top_k)

    def search_vec(self, query_emb: np.ndarray, top_k: int = 15) -> list[Match]:
        scores = self.embeddings @ query_emb
        k = min(top_k, len(scores))
        if k == 0:
            return []
        idx = np.argpartition(-scores, k - 1)[:k]
        idx = idx[np.argsort(-scores[idx])]
        return [
            Match(
                filename=self.metadata[i]["filename"],
                path=self.templates_dir / self.metadata[i]["filename"],
                name=self.metadata[i].get("name", self.metadata[i]["filename"]),
                score=float(scores[i]),
            )
            for i in idx
        ]


@lru_cache(maxsize=1)
def get_index() -> MemeIndex:
    return MemeIndex.load()

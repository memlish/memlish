from __future__ import annotations

import os

import numpy as np
import pytest

from memlish_reborn.index import MemeIndex, Match


def test_search_vec_returns_topk_ordered_by_score(tmp_path):
    rng = np.random.default_rng(0)
    embeddings = rng.standard_normal((10, 32)).astype(np.float32)
    embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)
    metadata = [{"filename": f"{i}.png", "name": f"Meme {i}"} for i in range(10)]

    index = MemeIndex(embeddings, metadata, tmp_path, encoder=None)
    query = embeddings[3].copy()
    results = index.search_vec(query, top_k=5)

    assert len(results) == 5
    assert all(isinstance(r, Match) for r in results)
    # identical vector should be the top hit with score ~1
    assert results[0].filename == "3.png"
    assert results[0].score == pytest.approx(1.0, abs=1e-4)
    # scores strictly decreasing
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_vec_top_k_clamped_to_corpus_size(tmp_path):
    embeddings = np.eye(3, dtype=np.float32)
    metadata = [{"filename": f"{i}.png"} for i in range(3)]
    index = MemeIndex(embeddings, metadata, tmp_path, encoder=None)
    assert len(index.search_vec(embeddings[0], top_k=100)) == 3
    assert index.search_vec(embeddings[0], top_k=0) == []


@pytest.mark.skipif(
    os.environ.get("MEMLISH_SKIP_CLIP") == "1",
    reason="CLIP smoke test skipped",
)
def test_end_to_end_search_on_real_templates():
    """Integration: CLIP query embedding → top-5 on the real 30-template index.

    We don't assert a specific meme is #1 (CLIP is fuzzy), but we check the
    top-5 contains a plausible match for an obvious query."""
    from memlish_reborn.config import EMBEDDINGS_PATH, METADATA_PATH, TEMPLATES_DIR

    if not EMBEDDINGS_PATH.exists():
        pytest.skip("run `scripts/build_index.py` first")

    index = MemeIndex.load(EMBEDDINGS_PATH, METADATA_PATH, TEMPLATES_DIR)
    results = index.search("a person on fire sitting in a burning room", top_k=5)
    assert len(results) == 5
    top_names = [r.name for r in results]
    # "This Is Fine" is in our 30-template set — should place in top-5 for this query
    assert any("fine" in n.lower() for n in top_names), f"got: {top_names}"

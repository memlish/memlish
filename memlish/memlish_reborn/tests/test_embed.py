from __future__ import annotations

import os

import numpy as np
import pytest
from PIL import Image

pytestmark = pytest.mark.skipif(
    os.environ.get("MEMLISH_SKIP_CLIP") == "1",
    reason="CLIP model download skipped (MEMLISH_SKIP_CLIP=1)",
)


@pytest.fixture(scope="module")
def encoder():
    from memlish_reborn.embed import ClipEncoder

    return ClipEncoder()


def test_encode_text_shape_and_unit_norm(encoder):
    embs = encoder.encode_text(["a cat sitting on a mat", "a dog running in a field"])
    assert embs.shape == (2, encoder.embedding_dim)
    np.testing.assert_allclose(np.linalg.norm(embs, axis=1), 1.0, atol=1e-4)


def test_encode_images_shape(encoder):
    imgs = [Image.new("RGB", (64, 64), (i * 50 % 255, 100, 200)) for i in range(3)]
    embs = encoder.encode_images(imgs)
    assert embs.shape == (3, encoder.embedding_dim)
    np.testing.assert_allclose(np.linalg.norm(embs, axis=1), 1.0, atol=1e-4)


def test_text_image_similarity_is_sensible(encoder):
    red = Image.new("RGB", (64, 64), (255, 0, 0))
    blue = Image.new("RGB", (64, 64), (0, 0, 255))
    img_embs = encoder.encode_images([red, blue])
    text_embs = encoder.encode_text(["a red square", "a blue square"])
    sims = img_embs @ text_embs.T
    # red↔"red" should beat red↔"blue", same for blue
    assert sims[0, 0] > sims[0, 1]
    assert sims[1, 1] > sims[1, 0]


def test_empty_inputs(encoder):
    assert encoder.encode_text([]).shape == (0, encoder.embedding_dim)
    assert encoder.encode_images([]).shape == (0, encoder.embedding_dim)

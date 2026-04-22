from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from memlish_reborn.config import CLIP_MODEL, DEVICE


class ClipEncoder:
    def __init__(self, model_name: str = CLIP_MODEL, device: str = DEVICE):
        self.device = torch.device(device)
        self.model = CLIPModel.from_pretrained(model_name).to(self.device).eval()
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.embedding_dim: int = int(self.model.config.projection_dim)

    @torch.inference_mode()
    def encode_text(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.embedding_dim), dtype=np.float32)
        inputs = self.processor(
            text=texts, return_tensors="pt", padding=True, truncation=True
        ).to(self.device)
        feats = _as_tensor(self.model.get_text_features(**inputs))
        return _l2_normalize(feats).cpu().numpy().astype(np.float32)

    @torch.inference_mode()
    def encode_images(self, images: list[Image.Image | Path | str]) -> np.ndarray:
        if not images:
            return np.zeros((0, self.embedding_dim), dtype=np.float32)
        pil_images = [_load(img) for img in images]
        inputs = self.processor(images=pil_images, return_tensors="pt").to(self.device)
        feats = _as_tensor(self.model.get_image_features(**inputs))
        return _l2_normalize(feats).cpu().numpy().astype(np.float32)


@lru_cache(maxsize=1)
def get_encoder() -> ClipEncoder:
    return ClipEncoder()


def _load(img: Image.Image | Path | str) -> Image.Image:
    if isinstance(img, Image.Image):
        return img.convert("RGB")
    return Image.open(img).convert("RGB")


def _as_tensor(out) -> torch.Tensor:
    # transformers <5 returns a Tensor; transformers 5.x wraps it in BaseModelOutputWithPooling
    if isinstance(out, torch.Tensor):
        return out
    return out.pooler_output


def _l2_normalize(tensor: torch.Tensor) -> torch.Tensor:
    return tensor / tensor.norm(dim=-1, keepdim=True).clamp(min=1e-12)

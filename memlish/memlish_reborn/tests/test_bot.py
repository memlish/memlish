from __future__ import annotations

import io

import pytest
from PIL import Image

from memlish_reborn.file_id_cache import FileIdCache


def test_file_id_cache_roundtrip(tmp_path):
    path = tmp_path / "ids.json"
    c1 = FileIdCache(path)
    assert c1.get("x.png", "hi") is None
    c1.set("x.png", "hi", "abc123")
    assert c1.get("x.png", "hi") == "abc123"
    # case-insensitive, whitespace-stripped
    assert c1.get("x.png", "  HI ") == "abc123"
    assert path.exists()

    c2 = FileIdCache(path)
    assert c2.get("x.png", "hi") == "abc123"


def test_file_id_cache_key_distinguishes_template_and_text(tmp_path):
    c = FileIdCache(tmp_path / "ids.json")
    c.set("a.png", "text", "id_a")
    c.set("b.png", "text", "id_b")
    c.set("a.png", "other", "id_c")
    assert c.get("a.png", "text") == "id_a"
    assert c.get("b.png", "text") == "id_b"
    assert c.get("a.png", "other") == "id_c"


def test_build_dispatcher_wires_handlers():
    from memlish_reborn.bot import build_dispatcher, router

    dp = build_dispatcher()
    assert router in dp.sub_routers


def test_render_meme_returns_jpeg_bytes(tmp_path):
    # smoke: the render helper produces decodable image bytes
    from memlish_reborn.bot import _render_meme
    from memlish_reborn.index import Match

    template = Image.new("RGB", (400, 300), (200, 100, 50))
    p = tmp_path / "tpl.jpg"
    template.save(p, format="JPEG")
    match = Match(filename=p.name, path=p, name="Test", score=0.5)

    data = _render_meme(match, "hello meme")
    assert len(data) > 100
    img = Image.open(io.BytesIO(data))
    assert img.format == "JPEG"
    assert max(img.size) <= 256

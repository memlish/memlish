from __future__ import annotations

from PIL import Image

from memlish_reborn.draw import add_text


def _base_image(w: int = 400, h: int = 400, color=(128, 128, 128)) -> Image.Image:
    return Image.new("RGB", (w, h), color)


def test_add_text_returns_new_image_capped_to_256():
    img = _base_image(800, 800)
    out = add_text(img, "hello world")
    assert isinstance(out, Image.Image)
    assert max(out.size) <= 256
    assert img.size == (800, 800)


def test_add_text_writes_visible_pixels():
    img = _base_image(400, 400, color=(128, 128, 128))
    before_extrema = img.getextrema()
    out = add_text(img, "when you see it")
    after_extrema = out.getextrema()
    # outline is pure black, fill is pure white — expect extremes to stretch
    assert min(x[0] for x in after_extrema) == 0
    assert max(x[1] for x in after_extrema) == 255
    # original untouched
    assert before_extrema == img.getextrema()


def test_add_text_handles_empty_and_whitespace():
    img = _base_image()
    assert add_text(img, "").size == add_text(img, "   ").size


def test_add_text_wraps_long_text():
    img = _base_image()
    long_text = "this is a fairly long meme caption that really should be wrapped onto multiple lines"
    out = add_text(img, long_text)
    assert out.size[0] <= 256
    assert out.size[1] <= 256


def test_add_text_truncates_absurdly_long_text():
    img = _base_image()
    add_text(img, "x" * 5000)  # should not raise


def test_add_text_handles_newlines():
    img = _base_image()
    add_text(img, "line one\nline two\nline three")

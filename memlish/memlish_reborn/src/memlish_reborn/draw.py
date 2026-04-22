from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from memlish_reborn.config import FONT_PATH, IMAGE_MAX_SIDE


def add_text(
    image: Image.Image,
    text: str,
    *,
    font_path: Path = FONT_PATH,
    max_side: int = IMAGE_MAX_SIDE,
    initial_font_size: int = 28,
    min_font_size: int = 10,
) -> Image.Image:
    """Overlay `text` on `image` in classic meme style — Impact, white, black outline,
    wrapped and shrunk to fit at the bottom of the image.

    Returns a new Image (input is not mutated)."""
    img = image.copy().convert("RGB")
    img.thumbnail((max_side, max_side))
    if len(text) > 250:
        text = text[:250] + "..."

    text = text.replace("\n", " ").strip()
    if not text:
        return img

    font_size, lines = _fit_font_and_wrap(
        text, img.width, img.height, font_path, initial_font_size, min_font_size
    )
    font = ImageFont.truetype(str(font_path), font_size)
    draw = ImageDraw.Draw(img)

    line_h = _line_height(font)
    total_h = line_h * len(lines)
    y = img.height - total_h - int(img.height * 0.03)
    for line in lines:
        w = _text_width(draw, line, font)
        x = (img.width - w) / 2
        _draw_outlined(draw, line, x, y, font)
        y += line_h

    return img


def _fit_font_and_wrap(
    text: str,
    img_w: int,
    img_h: int,
    font_path: Path,
    start_size: int,
    min_size: int,
) -> tuple[int, list[str]]:
    max_text_height = img_h * 0.4
    for size in range(start_size, min_size - 1, -1):
        font = ImageFont.truetype(str(font_path), size)
        lines = _wrap(text, font, img_w)
        if not lines:
            continue
        widest = max(_font_text_width(font, line) for line in lines)
        total_h = _line_height(font) * len(lines)
        if widest <= img_w and total_h <= max_text_height and len(lines) <= 6:
            return size, lines
    font = ImageFont.truetype(str(font_path), min_size)
    return min_size, _wrap(text, font, img_w)


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _font_text_width(font, candidate) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_outlined(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: float,
    y: float,
    font: ImageFont.FreeTypeFont,
    outline: int = 2,
) -> None:
    for dx in (-outline, 0, outline):
        for dy in (-outline, 0, outline):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, fill=(0, 0, 0), font=font)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)


def _font_text_width(font: ImageFont.FreeTypeFont, text: str) -> float:
    left, _, right, _ = font.getbbox(text)
    return right - left


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def _line_height(font: ImageFont.FreeTypeFont) -> int:
    ascent, descent = font.getmetrics()
    return ascent + descent

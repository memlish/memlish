from abc import ABC, abstractmethod
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pathlib import Path
from memlish.config import FONTS_PATH
from memlish.io.image import load_image
from memlish.io.timelog import log_duration


class TextDrawerBase(ABC):
    @abstractmethod
    def add_text(self, image, text):
        raise NotImplementedError()


class DefaultTextDrawer(TextDrawerBase):
    def __init__(self, font_path=FONTS_PATH/'impact.ttf', font_size=21, max_width=256, max_height=256):
        super().__init__()

        font_path = str(font_path)

        self.font = ImageFont.truetype(font_path, font_size)
        self.font_path = font_path
        self.font_size = font_size
        self.max_width = max_width
        self.max_height = max_height

    def add_text(self,
                 image: Image,
                 text: str):

        image = image.copy()

        return add_text_to_image(image,
                                 text,
                                 self.font,
                                 self.font_path,
                                 self.font_size,
                                 self.max_width,
                                 self.max_height)


# @log_duration
def add_text_to_image(img: Image,
                      text: str,
                      font,
                      font_path,
                      font_size,
                      max_width=256,
                      max_height=256):
    img.thumbnail((max_width, max_height))
    draw = ImageDraw.Draw(img)
    text = text.replace('\n', '')
    if len(text) >= 250:
        text = text + '...'

    def drawTextWithOutline(text, x, y):
        draw.text((x-2, y-2), text, (0, 0, 0), font=font)
        draw.text((x+2, y-2), text, (0, 0, 0), font=font)
        draw.text((x+2, y+2), text, (0, 0, 0), font=font)
        draw.text((x-2, y+2), text, (0, 0, 0), font=font)
        draw.text((x, y), text, (255, 255, 255), font=font)
        return

    w, h = draw.textsize(text, font)

    while w > img.width * img.height * 0.6 / h:
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)
        w, h = draw.textsize(text, font)

    lines = int(w / img.width) + 1
    words = text.split()
    w, h = draw.textsize(max(words, key=len), font)
    while w > img.width:
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)
        w, h = draw.textsize(text, font)

    words = text.split()
    line = 0
    if lines == 1:
        w, h = draw.textsize(text, font)
#             print(text)
        drawTextWithOutline(text, img.width/2 - w/2, img.height * 0.98 - h)
        return img

    text = ''
    i = 0

    hh = h
    for word in words:
        text += word + ' '
        i += 1
        last_word = len(word) + 1
        w, h = draw.textsize(text, font)
        if w > img.width:
            w, h = draw.textsize(text[:-last_word], font)

            if line >= lines / 2:
                drawTextWithOutline(text[:-last_word], img.width/2 - w/2, img.height * 0.98 - (
                    lines / 2 * hh) + (line - lines / 2 - 1) * hh)
            else:
                drawTextWithOutline(
                    text[:-last_word], img.width/2 - w/2, line * hh)
            text = word + ' '
            line += 1
        if i == len(words):
            w, h = draw.textsize(text, font)
            if line >= lines / 2:
                drawTextWithOutline(text, img.width/2 - w/2, img.height *
                                    0.98 - (lines / 2 * hh) + (line - lines / 2 - 1) * hh)
            else:
                drawTextWithOutline(text, img.width/2 - w/2, line * hh)

    return img

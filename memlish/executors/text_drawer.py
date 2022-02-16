from jina import DocumentArray, Executor, requests, Document
from typing import Optional, Tuple, Sequence, Dict
from pathlib import Path
from memlish.config import FONTS_PATH, SHOW_K_MEMES
from memlish.image_processing.text_drawer import DefaultTextDrawer
from memlish.io.timelog import log_duration
from memlish.io.image import load_image
from uuid import uuid4
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import asyncio
from functools import partial


class TextDrawer(Executor):

    def __init__(
        self,
        templates_dir: Path,
        out_path: Path,
        max_width=256,
        max_height=256,
        font_path=FONTS_PATH/'impact.ttf',
        font_size=21,
        *args,
        **kwargs,
    ):
        """
        out_path - directory where drawer will store results. Note that uri in docs will chance on this folder!
        """
        super().__init__(*args, **kwargs)
        self.drawer = DefaultTextDrawer(font_path, font_size)
        self.out_path = Path(out_path)
        self.templates_dir = Path(templates_dir)

        self.max_width, self.max_height = max_width, max_height

        self.image_map = {}
        for i in self.templates_dir.iterdir():
            self.image_map[i.name] = load_image(
                i, target_size=(self.max_width, self.max_height))

        if not self.out_path.exists():
            self.out_path.mkdir(parents=True, exist_ok=True)

        self.thread_pool = ThreadPoolExecutor(SHOW_K_MEMES)

    def process_image(self, path: Path, image: Image):
        # all stuff to process image here
        image.save(path)

    async def async_image_process(self, path_img: Dict):
        loop = asyncio.get_event_loop()
        for path, image in path_img.items():
            await loop.run_in_executor(
                self.thread_pool,
                partial(self.process_image, path, image)
            )

    @requests
    @log_duration
    def add_text(self, docs: Optional[DocumentArray], parameters: Dict = {}, **kwargs):
        """
        Note, it works only with doc.matches
        """
        if docs is None:
            return

        results_dir = self.out_path/str(uuid4())
        results_dir.mkdir(parents=True, exist_ok=True)

        for doc in docs:

            transparent_foreground = Image.new(
                'RGBA', (self.max_width, self.max_height), (255, 0, 0, 0))

            text_overlay = self.drawer.add_text(
                transparent_foreground, doc.tags["text_to_draw"])

            path_img = {}

            for match in doc.matches:
                i_image = self.image_map[Path(match.uri).name].copy()
                i_image.paste(text_overlay, (0, 0), text_overlay)

                result_image_path = results_dir / Path(match.uri).name

                path_img[result_image_path] = i_image
                match.uri = str(result_image_path)

            result = asyncio.create_task(self.async_image_process(path_img))
            while result.done():
                pass

from jina import DocumentArray, Executor, requests, Document
from typing import Optional, Tuple, Sequence, Dict
from pathlib import Path
from memlish.config import FONTS_PATH
from memlish.image_processing.text_drawer import DefaultTextDrawer
from memlish.io.timelog import log_duration
from memlish.io.image import load_image
from uuid import uuid4


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
        self.image_map = {}
        for i in self.templates_dir.iterdir():
            self.image_map[i.name] = load_image(
                i, target_size=(max_width, max_height))

        if not self.out_path.exists():
            self.out_path.mkdir(parents=True, exist_ok=True)

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
            for match in doc.matches:
                result_image = self.drawer.add_text(
                    self.image_map[Path(match.uri).name], doc.text)  # TODO: add doc.text here!
                result_image_path = results_dir / Path(match.uri).name
                result_image.save(result_image_path)
                match.uri = str(result_image_path)

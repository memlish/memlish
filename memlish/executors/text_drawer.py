from jina import DocumentArray, Executor, requests, Document
from typing import Optional, Tuple, Sequence, Dict
from pathlib import Path
from memlish.config import FONTS_PATH
from memlish.image_processing.text_drawer import DefaultTextDrawer
from uuid import uuid4


class TextDrawer(Executor):
    """Encode text into embeddings using SBERT model."""

    def __init__(
        self,
        out_path: Path,
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
        self.out_path = out_path
        if not self.out_path.exists():
            self.out_path.mkdir(parents=True, exist_ok=True)

    @requests
    def add_text(self, docs: Optional[DocumentArray], parameters: Dict = {}, **kwargs):
        if docs is None:
            return

        max_width = int(parameters.get("max_width", 256))
        max_height = int(parameters.get("max_height", 256))

        results_dir = self.out_path/str(uuid4())
        results_dir.mkdir(parents=True, exist_ok=True)

        for doc in docs:
            result_image = self.drawer.add_text(Path(
                doc.uri), '.', max_width=max_width, max_height=max_height)  # TODO: add doc.text here!
            result_image_path = results_dir / Path(doc.uri).name
            result_image.save(result_image_path)
            doc.uri = str(result_image_path)

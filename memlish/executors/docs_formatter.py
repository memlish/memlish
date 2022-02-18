from jina import DocumentArray, Executor, requests, Document
from typing import Optional, Tuple, Sequence, Dict
from pathlib import Path
from memlish.config import PUBLIC_FILES_URL, IMGFLIP_DIR
from memlish.io.timelog import log_duration
import os


class DocPreFormatter(Executor):

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

    @requests
    @log_duration
    def format(self, docs: Optional[DocumentArray], parameters: Dict = {}, **kwargs):
        if docs is None:
            return

        for doc in docs:
            doc.tags["text_to_draw"] = doc.text


class DocPostFormatter(Executor):

    def __init__(
        self,
        public_files_url=PUBLIC_FILES_URL,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.files_url = public_files_url

    @requests
    @log_duration
    def format_response(self, docs: Optional[DocumentArray], parameters: Dict = {}, **kwargs):
        if docs is None:
            return

        for doc in docs:
            for match in doc.matches:
                match_uri = Path(match.uri)

                # (/data/imgflip, /data/imgflip/images/img1) -> (images/img1)
                diff_path = os.path.relpath(match_uri, IMGFLIP_DIR)
                match.tags["image_url"] = f"{PUBLIC_FILES_URL}{diff_path}"

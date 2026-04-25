from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Callable

from memlish_reborn.file_id_cache import FileIdCache


class RenderedCache:
    """Disk-backed cache of rendered meme JPEGs.

    Keyed by the same sha256(template_filename, normalized_text) as FileIdCache
    so the two caches can be reasoned about together. Files live at
    `<root>/<key>.jpg`.
    """

    # TODO: add an LRU sweep / size cap; v1 keeps everything.

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._known: set[str] = {
            p.stem for p in self.root.glob("*.jpg")
        }

    @staticmethod
    def key(template_filename: str, text: str) -> str:
        return FileIdCache.key(template_filename, text)

    def path_for(self, key: str) -> Path:
        return self.root / f"{key}.jpg"

    def get(self, template_filename: str, text: str) -> Path | None:
        key = self.key(template_filename, text)
        if key in self._known:
            return self.path_for(key)
        path = self.path_for(key)
        if path.is_file():
            self._known.add(key)
            return path
        return None

    def get_or_render(
        self,
        template_filename: str,
        text: str,
        render_fn: Callable[[], bytes],
    ) -> Path:
        """Return path to the rendered JPEG, rendering and writing it if missing.

        `render_fn` is called synchronously; callers should wrap this method in
        `asyncio.to_thread(...)` to avoid blocking the event loop.
        """
        key = self.key(template_filename, text)
        path = self.path_for(key)
        if key in self._known or path.is_file():
            self._known.add(key)
            return path

        data = render_fn()
        with self._lock:
            if not path.is_file():
                tmp = path.with_suffix(".jpg.tmp")
                tmp.write_bytes(data)
                os.replace(tmp, path)
            self._known.add(key)
        return path

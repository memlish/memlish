from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path


class FileIdCache:
    """Persistent map: sha256(template_id + text) -> telegram file_id.

    Thread-safe for concurrent reads/writes from async handlers."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._data: dict[str, str] = {}
        if path.exists():
            self._data = json.loads(path.read_text())

    @staticmethod
    def key(template_filename: str, text: str) -> str:
        norm = text.strip().lower()
        return hashlib.sha256(f"{template_filename}|{norm}".encode()).hexdigest()

    def get(self, template_filename: str, text: str) -> str | None:
        return self._data.get(self.key(template_filename, text))

    def set(self, template_filename: str, text: str, file_id: str) -> None:
        with self._lock:
            self._data[self.key(template_filename, text)] = file_id
            self._flush()

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._data))
        tmp.replace(self.path)

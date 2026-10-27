"""JSON file storage.

Static reference data (models, releases, apps) is read from ``fixtures/``.
Mutable state (the device registry) lives in a data directory and is seeded
from the matching fixture on first use.
"""

import json
import os
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "fixtures"
DEFAULT_DATA_DIR = REPO_ROOT / "data"


class JsonStore:
    def __init__(self, data_dir=DEFAULT_DATA_DIR, fixtures_dir=FIXTURES_DIR):
        self.data_dir = Path(data_dir)
        self.fixtures_dir = Path(fixtures_dir)
        self.lock = threading.RLock()

    def fixture(self, name):
        """Return read-only reference data, e.g. ``fixture("releases")``."""
        with open(self.fixtures_dir / (name + ".json"), encoding="utf-8") as f:
            return json.load(f)

    def load(self, name):
        """Return mutable state, seeding it from fixtures if missing."""
        with self.lock:
            path = self._path(name)
            if not path.exists():
                self.save(name, self.fixture(name))
            with open(path, encoding="utf-8") as f:
                return json.load(f)

    def save(self, name, value):
        with self.lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            path = self._path(name)
            tmp = path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)

    def reset(self):
        """Drop all mutable state; it will be re-seeded from fixtures."""
        with self.lock:
            if self.data_dir.exists():
                for path in self.data_dir.glob("*.json"):
                    path.unlink()

    def _path(self, name):
        return self.data_dir / (name + ".json")

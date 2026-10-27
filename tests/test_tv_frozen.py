"""The TV client in ``tv/`` is already running on customers' TVs.

It cannot be changed by a backend release, so the files must stay byte-for-byte
identical (line endings aside).
"""

import hashlib
import unittest

from backend.storage import REPO_ROOT

TV_DIR = REPO_ROOT / "tv"

SHIPPED_FILES = {
    "app.js": "d9838151bf226464c04cd182f9703a0695193545cb78e80a335d20cdd5f6e326",
    "index.html": "4e6f68bafc8c2ae97e5f5332851d980b14761994bc460c7a6fd3b694f30ed3ce",
    "style.css": "0e2cf3cfde540cf7e76d11e5e4f881e5b512aedf21f4f98dc3bb41b8472e08ec",
}


def _digest(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class TvClientFrozenTest(unittest.TestCase):
    def test_no_files_added_or_removed(self):
        present = {p.relative_to(TV_DIR).as_posix() for p in TV_DIR.rglob("*") if p.is_file()}
        self.assertEqual(present, set(SHIPPED_FILES))

    def test_files_unchanged(self):
        for name, expected in SHIPPED_FILES.items():
            with self.subTest(file=name):
                self.assertEqual(_digest(TV_DIR / name), expected, "tv/%s was modified" % name)

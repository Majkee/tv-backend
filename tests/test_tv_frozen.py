"""Once the TV client is shipped, ``tv/`` cannot change.

Shipping is marked with a git tag ``<branch>-wdrozone`` (e.g. ``vibe-wdrozone``).
Before the tag exists the test is skipped and ``tv/`` may change freely. After
that, ``tv/`` in the working tree must be identical to the tagged version, so
every later change has to happen in the backend.
"""

import subprocess
import unittest

from backend.storage import REPO_ROOT


def _git(*args):
    try:
        result = subprocess.run(["git"] + list(args), cwd=str(REPO_ROOT), capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


class TvFrozenAfterShippingTest(unittest.TestCase):
    def test_tv_unchanged_since_shipping(self):
        branch = _git("rev-parse", "--abbrev-ref", "HEAD")
        if not branch or branch == "HEAD":
            self.skipTest("nie jesteś na żadnej gałęzi")
        tag = branch + "-wdrozone"
        if _git("rev-parse", "-q", "--verify", "refs/tags/" + tag) is None:
            self.skipTest("telewizor z gałęzi %s nie jest jeszcze wdrożony (brak tagu %s)" % (branch, tag))
        changed = _git("diff", "--name-only", tag, "--", "tv/") or ""
        added = _git("ls-files", "--others", "--exclude-standard", "--", "tv/") or ""
        files = sorted(set((changed + "\n" + added).split()))
        self.assertEqual(
            files, [], "tv/ zmienił się od wdrożenia (tag %s). Telewizory u klientów tego nie dostaną; zmień backend." % tag
        )

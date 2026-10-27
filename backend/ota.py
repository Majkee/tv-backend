"""Over-the-air firmware updates."""

import re

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-[a-z]+)?$")


def parse_version(text):
    """Turn "2.8.1" or a regional build such as "2.8.1-eu" into (2, 8, 1)."""
    match = _VERSION_RE.match(text.strip())
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())


class UnknownBuild(LookupError):
    pass


class OtaService:
    def __init__(self, store, registry):
        self.store = store
        self.registry = registry

    def releases(self):
        return self.store.fixture("releases")

    def check(self, device_id, firmware=None, state=None, utc_offset_min=None):
        """Called periodically by every TV. Returns the update to install or None."""
        device = self.registry.report(device_id, firmware, state, utc_offset_min)
        current = parse_version(device["firmware"])

        best = None
        for release in self.releases():
            if device["model"] not in release["models"]:
                continue
            if device["region"] not in release["builds"]:
                continue
            version = parse_version(release["version"])
            if version <= current:
                continue
            if best is None or version > parse_version(best["version"]):
                best = release

        if best is None:
            return None
        return {
            "version": best["version"],
            "build": best["builds"][device["region"]],
            "size_bytes": best["size_bytes"],
            "notes": best["notes"],
        }

    def download(self, device_id, build):
        """Hand out a firmware build and count the download."""
        device = self.registry.get(device_id)
        for release in self.releases():
            if release["builds"].get(device["region"]) == build:
                self.registry.record_download(device_id)
                return {"build": build, "size_bytes": release["size_bytes"]}
        raise UnknownBuild(build)

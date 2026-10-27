import unittest

from backend.ota import OtaService, UnknownBuild, parse_version
from backend.registry import DeviceRegistry
from tests.support import StoreTestCase

ALL_MODELS = ["LM-43S19", "LM-55S19", "LM-50Q21", "LM-55Q23", "LM-65X25"]


def release(version, models=ALL_MODELS, regions=("NA", "APAC", "EU"), size_bytes=1000):
    return {
        "version": version,
        "released": "2026-01-01",
        "models": list(models),
        "builds": {region: version for region in regions},
        "size_bytes": size_bytes,
        "notes": "Release " + version,
    }


class ParseVersionTest(unittest.TestCase):
    def test_parses_three_numbers(self):
        self.assertEqual(parse_version("2.8.1"), (2, 8, 1))

    def test_ignores_regional_build_suffix(self):
        self.assertEqual(parse_version("2.8.1-eu"), (2, 8, 1))


class OtaCheckTest(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.registry = DeviceRegistry(self.store)
        self.ota = OtaService(self.store, self.registry)

    def test_offers_newer_release(self):
        self.set_fixture("releases", [release("2.8.1"), release("2.9.0")])
        update = self.ota.check("TV-001", firmware="2.8.1")
        self.assertEqual(update["version"], "2.9.0")
        self.assertEqual(update["build"], "2.9.0")

    def test_picks_the_highest_version(self):
        self.set_fixture("releases", [release("2.8.1"), release("2.9.0"), release("2.8.2")])
        self.assertEqual(self.ota.check("TV-001", firmware="2.8.0")["version"], "2.9.0")

    def test_no_update_when_up_to_date(self):
        self.set_fixture("releases", [release("2.8.1"), release("2.9.0")])
        self.assertIsNone(self.ota.check("TV-001", firmware="2.9.0"))

    def test_respects_model_list(self):
        self.set_fixture("releases", [release("2.9.0", models=["LM-65X25"])])
        self.assertIsNone(self.ota.check("TV-001", firmware="2.8.1"))

    def test_respects_region_builds(self):
        self.set_fixture("releases", [release("2.9.0", regions=["APAC"])])
        self.assertIsNone(self.ota.check("TV-001", firmware="2.8.1"))
        self.assertEqual(self.ota.check("TV-004", firmware="2.8.1")["build"], "2.9.0")

    def test_check_records_what_the_tv_reported(self):
        self.ota.check("TV-001", firmware="2.8.0", state="watching", utc_offset_min=-240)
        device = self.registry.get("TV-001")
        self.assertEqual(device["firmware"], "2.8.0")
        self.assertEqual(device["state"], "watching")
        self.assertEqual(device["utc_offset_min"], -240)

    def test_update_payload_fields(self):
        self.set_fixture("releases", [release("2.9.0", size_bytes=4096)])
        update = self.ota.check("TV-001", firmware="2.8.1")
        self.assertEqual(update["version"], "2.9.0")
        self.assertEqual(update["build"], "2.9.0")
        self.assertEqual(update["size_bytes"], 4096)
        self.assertEqual(update["notes"], "Release 2.9.0")


class OtaDownloadTest(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.registry = DeviceRegistry(self.store)
        self.ota = OtaService(self.store, self.registry)

    def test_download_counts_and_returns_size(self):
        result = self.ota.download("TV-001", "2.9.0")
        self.assertEqual(result["build"], "2.9.0")
        self.assertGreater(result["size_bytes"], 0)
        self.assertEqual(self.registry.get("TV-001")["downloads"], 1)

    def test_build_must_match_device_region(self):
        with self.assertRaises(UnknownBuild):
            self.ota.download("TV-001", "2.9.0-eu")
        self.assertEqual(self.registry.get("TV-001")["downloads"], 0)

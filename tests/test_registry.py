from backend.registry import DeviceNotFound, DeviceRegistry
from backend.storage import JsonStore
from tests.support import StoreTestCase


class DeviceRegistryTest(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.registry = DeviceRegistry(self.store)

    def test_lists_devices_from_fixtures(self):
        ids = [d["id"] for d in self.registry.all()]
        self.assertIn("TV-001", ids)
        self.assertEqual(len(ids), len(set(ids)))

    def test_get_unknown_device_raises(self):
        with self.assertRaises(DeviceNotFound):
            self.registry.get("TV-999")

    def test_report_updates_firmware_state_and_last_seen(self):
        device = self.registry.report("TV-001", firmware="2.9.0", state="watching", utc_offset_min=120)
        self.assertEqual(device["firmware"], "2.9.0")
        self.assertEqual(device["state"], "watching")
        self.assertEqual(device["utc_offset_min"], 120)
        self.assertIsNotNone(device["last_seen"])

    def test_report_ignores_unknown_state(self):
        self.registry.report("TV-001", state="dancing")
        self.assertEqual(self.registry.get("TV-001")["state"], "standby")

    def test_state_survives_a_new_store_instance(self):
        self.registry.report("TV-002", firmware="2.8.1")
        reopened = DeviceRegistry(JsonStore(data_dir=self.store.data_dir))
        self.assertEqual(reopened.get("TV-002")["firmware"], "2.8.1")

    def test_record_download_counts(self):
        self.registry.record_download("TV-001")
        self.registry.record_download("TV-001")
        self.assertEqual(self.registry.get("TV-001")["downloads"], 2)

    def test_reset_restores_fixtures(self):
        self.registry.report("TV-001", firmware="9.9.9")
        self.store.reset()
        self.assertEqual(self.registry.get("TV-001")["firmware"], "2.8.1")

    def test_every_device_has_a_known_model(self):
        for device in self.registry.all():
            self.registry.model(device["model"])

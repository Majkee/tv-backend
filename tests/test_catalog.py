from backend.catalog import get_apps_for_device
from backend.registry import DeviceRegistry
from tests.support import StoreTestCase


class CatalogTest(StoreTestCase):
    def test_returns_apps_for_a_device(self):
        device = DeviceRegistry(self.store).get("TV-001")
        apps = get_apps_for_device(self.store, device)
        self.assertTrue(apps)
        for app in apps:
            self.assertEqual(set(app), {"id", "name", "color", "version", "api", "featured"})

    def test_unknown_model_has_no_apps(self):
        device = {"id": "X", "model": "LM-00X00", "region": "EU", "firmware": "2.9.0"}
        self.assertEqual(get_apps_for_device(self.store, device), [])

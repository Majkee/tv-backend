from tests.support import StoreTestCase


class FixturesTest(StoreTestCase):
    def test_release_versions_are_well_formed(self):
        for release in self.store.fixture("releases"):
            self.assertRegex(release["version"], r"^\d+\.\d+\.\d+$")

    def test_release_models_exist(self):
        models = {m["model"] for m in self.store.fixture("models")}
        for release in self.store.fixture("releases"):
            self.assertTrue(set(release["models"]) <= models, release["version"])

    def test_every_app_has_a_package(self):
        for app in self.store.fixture("apps"):
            self.assertTrue(app["packages"], app["id"])

    def test_firmware_vectors_are_well_formed(self):
        vectors = self.store.fixture("firmware_vectors")["vectors"]
        self.assertTrue(vectors)
        names = set()
        for vector in vectors:
            self.assertNotIn(vector["name"], names)
            names.add(vector["name"])
            bytes.fromhex(vector["hex"])
            self.assertIn("valid", vector["expected"])

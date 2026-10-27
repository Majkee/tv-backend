"""The API as seen by TVs already in the field (``tv/app.js``).

Field names and shapes checked here are relied on by shipped clients.
"""

from tests.support import ServerTestCase

RELEASE = {
    "version": "2.9.0",
    "released": "2026-07-20",
    "models": ["LM-50Q21", "LM-55Q23", "LM-65X25"],
    "builds": {"NA": "2.9.0", "APAC": "2.9.0"},
    "size_bytes": 455081984,
    "notes": "Release notes",
}


class ApiContractTest(ServerTestCase):
    def test_health(self):
        self.assertEqual(self.get_json("/api/health"), (200, {"status": "ok"}))

    def test_device_list(self):
        status, body = self.get_json("/api/devices")
        self.assertEqual(status, 200)
        for device in body["devices"]:
            self.assertTrue({"id", "model", "region"} <= set(device))

    def test_device_details(self):
        status, body = self.get_json("/api/devices/TV-001")
        self.assertEqual(status, 200)
        expected = {"id", "model", "model_name", "region", "firmware", "downloads", "utc_offset_min"}
        self.assertTrue(expected <= set(body), expected - set(body))
        self.assertIsInstance(body["utc_offset_min"], int)
        self.assertIsInstance(body["downloads"], int)

    def test_device_apps(self):
        status, body = self.get_json("/api/devices/TV-001/apps")
        self.assertEqual(status, 200)
        self.assertTrue(body["apps"])
        for app in body["apps"]:
            self.assertTrue({"name", "version", "color", "featured"} <= set(app))

    def test_report(self):
        status, body = self.post_json("/api/devices/TV-001/report", {"state": "watching"})
        self.assertEqual(status, 200)
        self.assertEqual(body["state"], "watching")

    def test_check_with_update(self):
        self.set_fixture("releases", [RELEASE])
        status, body = self.post_json("/api/ota/check", {
            "device_id": "TV-001", "firmware": "2.8.1", "state": "standby", "utc_offset_min": -300,
        })
        self.assertEqual(status, 200)
        update = body["update"]
        self.assertTrue({"build", "size_bytes", "notes"} <= set(update))
        self.assertIsInstance(update["size_bytes"], int)

    def test_check_without_update(self):
        self.set_fixture("releases", [RELEASE])
        status, body = self.post_json("/api/ota/check", {"device_id": "TV-004", "firmware": "2.9.0"})
        self.assertEqual(status, 200)
        self.assertIn("update", body)
        self.assertIsNone(body["update"])

    def test_download(self):
        self.set_fixture("releases", [RELEASE])
        status, body = self.post_json("/api/ota/download", {"device_id": "TV-001", "build": "2.9.0"})
        self.assertEqual(status, 200)
        self.assertEqual(body["build"], "2.9.0")

    def test_unknown_device_is_404_with_error_field(self):
        status, body = self.get_json("/api/devices/TV-999")
        self.assertEqual(status, 404)
        self.assertIn("error", body)
        status, body = self.post_json("/api/ota/check", {"device_id": "TV-999"})
        self.assertEqual(status, 404)
        self.assertIn("error", body)

    def test_missing_field_is_400(self):
        status, body = self.post_json("/api/ota/check", {})
        self.assertEqual(status, 400)
        self.assertIn("error", body)


class StaticFilesTest(ServerTestCase):
    def test_root_redirects_to_tv(self):
        status, _, raw = self.request("GET", "/tv/")
        self.assertEqual(status, 200)
        self.assertIn(b"app.js", raw)

    def test_serves_scripts_and_styles(self):
        for path, ctype in (("/tv/app.js", "javascript"), ("/tv/style.css", "text/css")):
            status, headers, _ = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertIn(ctype, headers["Content-Type"])

    def test_no_path_traversal(self):
        status, _, _ = self.request("GET", "/tv/../backend/api.py")
        self.assertEqual(status, 404)

"""Device registry: TVs sold to customers and what they last reported."""

from datetime import datetime, timezone


class DeviceNotFound(KeyError):
    pass


VALID_STATES = ("standby", "menu", "watching")


class DeviceRegistry:
    def __init__(self, store):
        self.store = store

    def all(self):
        return self.store.load("devices")

    def get(self, device_id):
        for device in self.all():
            if device["id"] == device_id:
                return device
        raise DeviceNotFound(device_id)

    def model(self, model_code):
        for model in self.store.fixture("models"):
            if model["model"] == model_code:
                return model
        raise KeyError(model_code)

    def report(self, device_id, firmware=None, state=None, utc_offset_min=None):
        """Store what the TV reported about itself. Returns the updated device."""

        def apply(device):
            if firmware:
                device["firmware"] = firmware
            if state in VALID_STATES:
                device["state"] = state
            if utc_offset_min is not None:
                device["utc_offset_min"] = int(utc_offset_min)
            device["last_seen"] = _now()

        return self._update(device_id, apply)

    def record_download(self, device_id):
        def apply(device):
            device["downloads"] = device.get("downloads", 0) + 1

        return self._update(device_id, apply)

    def _update(self, device_id, apply):
        with self.store.lock:
            devices = self.all()
            for device in devices:
                if device["id"] == device_id:
                    apply(device)
                    self.store.save("devices", devices)
                    return device
            raise DeviceNotFound(device_id)


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

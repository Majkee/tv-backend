"""Kombajn: the whole Lumio API behind one MCP tool.

TRAINING MATERIAL, a counter-example. One tool with an ``action`` switch looks
tidy, but the agent has to read a long manual on every turn, it cannot tell
reads from writes, and permissions can only allow or deny all of it at once.
Compare it with lumio_ops.py using smoke.py.
"""

import os
import sys
from pathlib import Path
from typing import Annotated, Literal, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "mcp_server"))

try:
    from mcp.server.mcpserver import MCPServer
    from pydantic import Field
except ImportError:
    from mcp_lite import MCPServer, Field

from backend.api import Api
from backend.storage import JsonStore

api = Api(JsonStore(data_dir=os.environ.get("LUMIO_DATA_DIR") or REPO_ROOT / "data"))
mcp = MCPServer("kombajn")

Action = Literal[
    "health", "list_devices", "get_device", "report", "device_apps",
    "ota_check", "ota_download", "list_releases", "list_models", "list_apps",
]


@mcp.tool()
def lumio(
    action: Annotated[Action, Field(description="Operacja do wykonania, patrz opis narzędzia.")],
    params: Annotated[Optional[dict], Field(description="Parametry operacji jako obiekt JSON.")] = None,
):
    """Uniwersalne narzędzie do wszystkich operacji backendu Lumio TV: rejestr urządzeń, aktualizacje OTA, katalog aplikacji i dane referencyjne.

    Wybierz operację parametrem action i przekaż jej parametry w params.

    action = "health": sprawdza, czy backend działa. params: brak. Zwraca {"status": "ok"}.

    action = "list_devices": lista wszystkich telewizorów w rejestrze. params: brak.
      Zwraca {"devices": [...]}, każde urządzenie ma pola id, model, region, firmware, state,
      utc_offset_min, downloads i last_seen. Filtrowanie po regionie lub modelu zrób samodzielnie.

    action = "get_device": szczegóły urządzenia razem z danymi modelu. params: {"device_id": "TV-001"}.
      Zwraca rekord urządzenia połączony z modelem (name, year, max_api, model_name, model_year).
      Uwaga: pola modelu mogą nadpisać pola urządzenia o tej samej nazwie.

    action = "report": zapisuje to, co telewizor zgłosił o sobie. params: {"device_id": "TV-001",
      "firmware": "2.8.1", "state": "standby" | "menu" | "watching", "utc_offset_min": 60}.
      Wszystkie pola oprócz device_id są opcjonalne. Aktualizuje last_seen. Zmienia stan rejestru.

    action = "device_apps": aplikacje widoczne na ekranie głównym urządzenia. params: {"device_id": "TV-001"}.
      Zwraca {"device_id": ..., "apps": [{"id", "name", "color", "version", "api", "featured"}]}.

    action = "ota_check": to samo zapytanie, które wysyła telewizor: zapisuje zgłoszenie i zwraca
      aktualizację do zainstalowania albo null. params: {"device_id": "TV-001", "firmware": "2.8.1",
      "state": "standby", "utc_offset_min": 60}. Zmienia stan rejestru (last_seen, firmware, state).

    action = "ota_download": wydaje paczkę firmware'u i zwiększa licznik pobrań urządzenia.
      params: {"device_id": "TV-001", "build": "2.8.1-eu"}. Zwraca {"build", "size_bytes"}.
      Zmienia stan rejestru.

    action = "list_releases": wszystkie wydania firmware'u (version, released, models, builds,
      size_bytes, notes). params: brak.

    action = "list_models": wszystkie modele (model, name, year, max_api). params: brak.

    action = "list_apps": pełny katalog aplikacji z pakietami dla poziomów API, regionami,
      min_firmware i flagami featured oraz hidden. params: brak.

    Błędy zwracane są jako {"error": kod, ...} z kodem HTTP w polu status:
    404 device_not_found, 404 unknown_build, 400 bad_request, 404 not_found.
    """
    params = params or {}
    device_id = params.get("device_id", "")
    if action in ("list_releases", "list_models", "list_apps"):
        return {"status": 200, "body": api.store.fixture(action[len("list_"):])}
    routes = {
        "health": ("GET", "/api/health"),
        "list_devices": ("GET", "/api/devices"),
        "get_device": ("GET", "/api/devices/%s" % device_id),
        "report": ("POST", "/api/devices/%s/report" % device_id),
        "device_apps": ("GET", "/api/devices/%s/apps" % device_id),
        "ota_check": ("POST", "/api/ota/check"),
        "ota_download": ("POST", "/api/ota/download"),
    }
    method, path = routes[action]
    status, body = api.handle(method, path, body=params)
    return {"status": status, "body": body}


if __name__ == "__main__":
    mcp.run(transport="stdio")

"""Lumio Ops: the ready-made MCP server of the backend team.

Gives an agent the device registry, firmware releases and the current OTA
rules, plus two write tools for the TV simulator. Start it as a script:

    python mcp_server/lumio_ops.py

Environment:
    LUMIO_MCP_READONLY=1   the write tools are not registered at all
    LUMIO_DATA_DIR=<dir>   device state directory (default: data/, shared with run_server)
"""

import json
import os
import sys
from pathlib import Path
from typing import Annotated, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.types import ToolAnnotations
    from pydantic import Field
except ImportError:  # no SDK installed: the same API from the stdlib-only shim
    from mcp_lite import MCPServer, ToolError, ToolAnnotations, Field

from backend.ota import OtaService, parse_version
from backend.registry import DeviceNotFound, DeviceRegistry
from backend.storage import DEFAULT_DATA_DIR, JsonStore

store = JsonStore(data_dir=os.environ.get("LUMIO_DATA_DIR") or DEFAULT_DATA_DIR)
registry = DeviceRegistry(store)
READONLY = os.environ.get("LUMIO_MCP_READONLY") == "1"

READ_ONLY = ToolAnnotations(readOnlyHint=True)
DeviceId = Annotated[str, Field(description="Identyfikator telewizora z rejestru, np. TV-003.")]

mcp = MCPServer(
    "lumio",
    instructions=(
        "Dane telewizorów Lumio u klientów: rejestr urządzeń, wydania firmware'u i reguły aktualizacji OTA. "
        "Identyfikatory urządzeń mają postać TV-001, regiony to EU, NA i APAC."
    ),
)


class _PeekRegistry(DeviceRegistry):
    """Registry for dry runs: what a TV reports is not saved."""

    def report(self, device_id, *args, **kwargs):
        return self.get(device_id)

    def record_download(self, device_id):
        return self.get(device_id)


def _device(device_id):
    try:
        return registry.get(device_id)
    except DeviceNotFound:
        raise ToolError("Nie ma urządzenia %s w rejestrze. Listę urządzeń zwraca list_devices." % device_id)


@mcp.tool(annotations=READ_ONLY)
def list_devices(
    region: Annotated[Optional[str], Field(description="Region: EU, NA albo APAC. Pomiń, żeby dostać wszystkie regiony.")] = None,
    model: Annotated[Optional[str], Field(description="Kod modelu, np. LM-55Q23. Pomiń, żeby dostać wszystkie modele.")] = None,
):
    """Lista telewizorów z rejestru: id, model, region, wersja firmware'u, stan i ostatni kontakt z serwerem.

    Użyj, gdy pytanie dotyczy wielu urządzeń naraz, np. „które telewizory w EU mają firmware starszy niż 2.9.0”.
    Szczegóły jednego urządzenia zwraca get_device.
    """
    devices = registry.all()
    if region:
        devices = [d for d in devices if d["region"] == region.upper()]
    if model:
        devices = [d for d in devices if d["model"] == model.upper()]
    keys = ("id", "model", "region", "firmware", "state", "last_seen")
    return {"devices": [{key: d.get(key) for key in keys} for d in devices]}


@mcp.tool(annotations=READ_ONLY)
def get_device(device_id: DeviceId):
    """Szczegóły jednego telewizora: rekord z rejestru (firmware, stan, region, strefa czasowa, liczba pobrań firmware'u) i dane jego modelu (nazwa, rok, najwyższe obsługiwane API aplikacji)."""
    device = _device(device_id)
    return {"device": device, "model": registry.model(device["model"])}


@mcp.tool(annotations=READ_ONLY)
def pending_update(device_id: DeviceId):
    """Aktualizacja firmware'u, którą serwer zaproponowałby temu telewizorowi teraz, według bieżących reguł OTA z backend/ota.py.

    Zwraca update = null, gdy urządzenie nie dostanie żadnej aktualizacji. Tylko odczyt: nie zapisuje kontaktu z urządzeniem i nie liczy pobrania.
    """
    _device(device_id)
    ota = OtaService(store, _PeekRegistry(store))
    return {"device_id": device_id, "update": ota.check(device_id)}


@mcp.resource("lumio://releases", mime_type="application/json")
def releases():
    """Wszystkie wydania firmware'u: wersja, data, modele, buildy dla regionów, rozmiar i opis zmian."""
    return json.dumps(store.fixture("releases"), ensure_ascii=False, indent=2)


@mcp.resource("lumio://models", mime_type="application/json")
def models():
    """Modele telewizorów Lumio: kod, nazwa, rok i najwyższe obsługiwane API aplikacji."""
    return json.dumps(store.fixture("models"), ensure_ascii=False, indent=2)


@mcp.prompt()
def diagnose_device(device_id: str):
    """Diagnoza aktualizacji jednego telewizora: dlaczego nie dostaje aktualizacji albo dostaje ją w kółko."""
    return (
        "Zdiagnozuj aktualizacje firmware'u telewizora %s.\n"
        "1. Pobierz jego szczegóły narzędziem get_device.\n"
        "2. Sprawdź narzędziem pending_update, co serwer by mu teraz zaproponował.\n"
        "3. Porównaj to z wydaniami z zasobu lumio://releases (model, region, wersja).\n"
        "Odpowiedz krótko: co urządzenie ma, co powinno dostać, co dostaje i skąd bierze się różnica. "
        "Niczego nie zmieniaj w rejestrze." % device_id
    )


if not READONLY:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
    def set_device_firmware(
        device_id: DeviceId,
        firmware: Annotated[str, Field(description="Wersja firmware'u, np. 2.8.1 albo build regionalny 2.8.1-eu.")],
    ):
        """ZAPIS. Ustawia w rejestrze wersję firmware'u telewizora, tak jakby urządzenie samo ją zgłosiło.

        Służy do odtwarzania scenariuszy w symulatorze: telewizor w przeglądarce zobaczy nową wersję. Zwraca zaktualizowany rekord.
        """
        _device(device_id)
        if parse_version(firmware) == (0, 0, 0):
            raise ToolError("Nieprawidłowa wersja %r. Oczekiwany format: 2.8.1 albo 2.8.1-eu." % firmware)
        return registry.report(device_id, firmware=firmware)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True))
    def reset_devices():
        """ZAPIS, NIEODWRACALNE. Przywraca stan WSZYSTKICH telewizorów z fixtures/devices.json.

        Kasuje zgłoszone wersje firmware'u, stany i liczniki pobrań. Używaj tylko na wyraźne polecenie użytkownika.
        """
        store.reset()
        return {"reset": True, "devices": len(registry.all())}


if __name__ == "__main__":
    mcp.run(transport="stdio")

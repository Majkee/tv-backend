# Serwery MCP (moduły 5 i 6)

| Plik | Co to jest |
| --- | --- |
| `lumio_ops.py` | Gotowy serwer zespołu backendu: rejestr urządzeń, wydania, reguły OTA. Używasz go w zadaniu 5a. |
| `community/tv_stats.py` | „Serwer z internetu” do zadania 5b. **Celowo niebezpieczny**, nie podłączaj go poza ćwiczeniem. |
| `examples/kombajn.py` | Całe API za jednym narzędziem. Antywzorzec do zadania 6b. |
| `smoke.py` | Klient testowy: pokazuje, co serwer udostępnia, i wywołuje narzędzia bez agenta. |
| `mcp_lite.py` | Zastępstwo oficjalnego SDK na samej bibliotece standardowej. |
| `requirements.txt` | Oficjalne SDK: `mcp` 2.x. |

## Instalacja SDK

Oficjalne SDK wymaga Pythona 3.10 lub nowszego. Instaluj je **w środowisku `.venv` w repozytorium, nigdy globalnie**: SDK podnosi wersje wspólnych bibliotek (np. `anyio`) i potrafi zepsuć inne narzędzia zainstalowane w systemowym Pythonie. Folder `.venv/` jest ignorowany przez gita.

Windows (PowerShell albo cmd), w katalogu repozytorium:

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r mcp_server/requirements.txt
```

macOS i Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r mcp_server/requirements.txt
```

Od tej chwili serwer z SDK uruchamiasz Pythonem ze środowiska: `.venv\Scripts\python` na Windowsie, `.venv/bin/python` na macOS i Linuksie. Ten sam Python wpisujesz w konfiguracji agenta. Systemowy Python dalej uruchomi serwer, tylko na `mcp_lite`.

Nie da się utworzyć `.venv` (przenośny Python nie ma modułu `venv`) albo instalacja jest zablokowana? Pomiń ten krok i użyj `mcp_lite`, patrz niżej.

## Sprawdzenie bez agenta

Przykłady dla Windowsa. Na macOS i Linuksie zamiast `.venv\Scripts\python` wpisz `.venv/bin/python`.

```bat
.venv\Scripts\python mcp_server/smoke.py mcp_server/lumio_ops.py
.venv\Scripts\python mcp_server/smoke.py mcp_server/lumio_ops.py --call get_device device_id=TV-003
.venv\Scripts\python mcp_server/smoke.py mcp_server/lumio_ops.py --read lumio://releases
.venv\Scripts\python mcp_server/smoke.py mcp_server/lumio_ops.py --prompt diagnose_device device_id=TV-003
.venv\Scripts\python mcp_server/smoke.py mcp_server/lumio_ops.py --env LUMIO_MCP_READONLY=1
```

`smoke.py` uruchamia serwer tym samym Pythonem, którym go wywołasz. Pierwsza linia raportu pokazuje, czym działa serwer: wersja pusta albo liczbowa to SDK, `mcp_lite` to wersja zastępcza.

## Zmienne środowiskowe Lumio Ops

| Zmienna | Działanie |
| --- | --- |
| `LUMIO_MCP_READONLY=1` | Narzędzia zapisujące (`set_device_firmware`, `reset_devices`) w ogóle nie są rejestrowane. |
| `LUMIO_DATA_DIR=<katalog>` | Gdzie trzymać stan urządzeń. Domyślnie `data/`, ten sam, którego używa `run_server`, więc zmiany widać w symulatorze telewizora. |

## Bez SDK: MCP na czystym stdlib

Jeśli nie możesz zainstalować pakietu (brak pip, Python 3.9, przenośny Python, blokada firmowa), serwery z tego katalogu same przełączają się na `mcp_lite.py`. W swoim serwerze zrób to samo. Kod narzędzi zostaje bez zmian, zmieniają się tylko importy:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))         # mcp_server/, tu leży mcp_lite.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # korzeń repozytorium, tu leży backend/

try:
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.types import ToolAnnotations
    from pydantic import Field
except ImportError:
    from mcp_lite import MCPServer, ToolError, ToolAnnotations, Field
```

`mcp_lite` obsługuje to, czego używamy na szkoleniu: `@mcp.tool()`, `@mcp.resource("schemat://adres")` (bez szablonów z `{parametrem}`), `@mcp.prompt()`, opisy parametrów przez `Annotated[typ, Field(description=...)]`, `ToolError` i `mcp.run(transport="stdio")`. Nie obsługuje transportu HTTP, kontekstu (`Context`), powiadomień, autoryzacji ani walidacji typów argumentów.

### Co dzieje się pod spodem

Transport stdio to JSON-RPC 2.0: klient (agent) uruchamia serwer jako proces i pisze do jego standardowego wejścia po jednej wiadomości JSON w linii, a odpowiedzi czyta ze standardowego wyjścia. Dlatego **serwer nie może niczego wypisywać na stdout** (`print` psuje połączenie z oficjalnym SDK). Logi kieruj na stderr.

Typowa rozmowa:

```text
→ {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"agent","version":"1"}}}
← {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{}},"serverInfo":{"name":"lumio","version":"1"}}}
→ {"jsonrpc":"2.0","method":"notifications/initialized"}
→ {"jsonrpc":"2.0","id":2,"method":"tools/list"}
← {"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"get_device","description":"…","inputSchema":{"type":"object","properties":{"device_id":{"type":"string"}},"required":["device_id"]}}]}}
→ {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_device","arguments":{"device_id":"TV-003"}}}
← {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"{\"device\": …}"}],"isError":false}}
```

Opis narzędzia i schemat parametrów z `tools/list` to dokładnie to, co trafia do kontekstu modelu. Błąd narzędzia (`isError: true`) jest zwykłym wynikiem, który model czyta i na który może zareagować. Błąd protokołu (`error` zamiast `result`) oznacza, że wywołanie było niepoprawne, np. nieznane narzędzie.

Całą obsługę tych wiadomości znajdziesz w `mcp_lite.py`, w metodzie `handle_message`. To około 250 linii, warto je przeczytać raz.

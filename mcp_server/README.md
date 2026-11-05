# Serwer MCP: baza floty Lumio

Serwer `lumio_db.py` pozwala agentowi odpowiadać na pytania o telewizory Lumio u klientów. Za serwerem stoi mała baza SQLite (`lumio.sql`) z czterema tabelami:

| Tabela | Co zawiera |
| --- | --- |
| `models` | 5 modeli telewizorów: kod, nazwa, seria, przekątna, rok |
| `devices` | 60 telewizorów: model, region, kraj, wersja firmware'u, aktywacja, ostatni kontakt |
| `firmware_releases` | wydania firmware'u z opisem zmian |
| `support_tickets` | 48 zgłoszeń supportu: kategoria, status, opis klienta |

Pierwsze siedem telewizorów (`TV-001` do `TV-007`) to te same urządzenia, które widzisz w symulatorze.

Serwer ma dwa narzędzia, oba tylko do odczytu:

- `describe_database`: tabele, opisy kolumn i liczba wierszy,
- `run_query`: jedno zapytanie `SELECT`, najwyżej 200 wierszy wyniku.

Przy każdym starcie serwer wczytuje `lumio.sql` do bazy w pamięci, otwartej tylko do odczytu. Agent nie może niczego zmienić ani usunąć.

Nic nie trzeba instalować. Gdy nie ma oficjalnego SDK (`pip install mcp`), serwer używa `mcp_lite.py`, czyli tego samego protokołu napisanego na bibliotece standardowej.

## Podłączenie do Claude Code

Polecenie uruchom w katalogu głównym repozytorium. Na Windowsie zamiast `python3` wpisz `py -3` albo `python`, a jeśli używasz przenośnego Pythona, wpisz `python/python.exe`.

```bash
claude mcp add --scope project lumio-db -- python3 mcp_server/lumio_db.py
```

Polecenie zapisze plik `.mcp.json` w katalogu repozytorium. Zacznij nową sesję `claude` i zatwierdź serwer `lumio-db`, gdy Claude Code o to zapyta. Stan serwera sprawdzisz komendą `/mcp`.

## Sprawdzenie bez agenta

```bash
python3 mcp_server/smoke.py mcp_server/lumio_db.py
python3 mcp_server/smoke.py mcp_server/lumio_db.py --call run_query "sql=SELECT region, COUNT(*) FROM devices GROUP BY region"
```

Pierwsze polecenie pokazuje dokładnie to, co dostaje model: nazwy i opisy narzędzi oraz instrukcje serwera.

## Pliki

| Plik | Co to jest |
| --- | --- |
| `lumio_db.py` | serwer MCP |
| `lumio.sql` | baza: schemat z opisami kolumn i dane |
| `mcp_lite.py` | protokół MCP na samej bibliotece standardowej, używany zamiast SDK |
| `smoke.py` | klient testowy: pokazuje, co serwer udostępnia, i wywołuje narzędzia bez agenta |
| `requirements.txt` | oficjalne SDK, opcjonalne (Python 3.10+, instalacja w `.venv`) |

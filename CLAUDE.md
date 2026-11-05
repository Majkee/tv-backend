# Lumio TV backend

Backend telewizorów Lumio: rejestr urządzeń, aktualizacje firmware'u (OTA) i katalog aplikacji. Ten sam serwer serwuje symulator telewizora z `tv/`.

## Komendy

- Testy (całość): `./run_tests.sh` albo `run_tests.bat`. Bezpośrednio: `python -m unittest discover -s tests -t .` (na Windowsie zamiast `python` może być `py -3`).
- Jeden moduł testów: `python -m unittest tests.test_api_contract -v`
- Serwer i telewizor: `./run_server.sh` albo `run_server.bat`, potem `http://localhost:8765/tv/?device=TV-001`. Opcje: `--port 9000`, `--reset` (przywraca stan urządzeń z `fixtures/`).
- Serwer MCP bez agenta: `python mcp_server/smoke.py mcp_server/lumio_db.py` (opcja `--call narzędzie nazwa=wartość`).

Uruchamiaj testy po każdej zmianie. Przed zakończeniem pracy wszystkie testy muszą przechodzić.

## Struktura

- `backend/` – pakiet Pythona: `api.py` (routing JSON), `server.py` (HTTP), `registry.py` (urządzenia), `ota.py` (aktualizacje), `catalog.py` (aplikacje), `storage.py` (pliki JSON).
- `tv/` – klient telewizora (HTML, CSS, JavaScript bez bibliotek).
- `tests/` – `unittest`. `tests/support.py` daje izolowany store i serwer na wolnym porcie.
- `fixtures/` – dane referencyjne: modele, wydania, aplikacje, urządzenia.
- `data/` – stan runtime serwera, nie commitujemy.
- `mcp_server/` – serwer MCP `lumio_db.py` z bazą floty `lumio.sql`, zastępczy `mcp_lite.py` (sam stdlib) i klient testowy `smoke.py`.
- `zadania/` – strona z treścią zadań dla uczestników, statyczny HTML. Nie zmieniaj jej podczas zadań.

## Zasady

1. **Telewizor zmieniasz tylko do wdrożenia.** Wdrożenie oznacza tag `<gałąź>-wdrozone`, np. `vibe-wdrozone`. Sprawdź `git tag --list "*-wdrozone"`. Jeśli bieżąca gałąź ma taki tag, kod z `tv/` działa już w telewizorach klientów i nie da się go zaktualizować: każda zmiana musi być po stronie backendu. Pilnuje tego `tests/test_tv_frozen.py`.
2. **Zgodność wsteczna API.** Telewizory wołają endpointy z `tv/app.js`. Nie zmieniaj nazw ani typów pól, które klient czyta, i nie usuwaj endpointów. Nowe pola i nowe endpointy są w porządku. Kontrakt opisują testy w `tests/test_api_contract.py`.
3. **Tylko biblioteka standardowa, Python 3.9+.** Na komputerach szkoleniowych `pip` bywa zablokowany. Żadnego `match`, `X | Y` w adnotacjach ani `zoneinfo`. `backend/` nigdy nie importuje niczego z `mcp_server/`.
4. **Jeden krok = jeden commit na zielono.** Każdy commit zostawia wszystkie testy przechodzące. Komunikat commita opisuje, co się zmieniło.
5. **Nie osłabiaj testów.** Nie usuwaj testów, nie zakomentowuj asercji i nie dopasowuj oczekiwań do wyniku tylko po to, żeby test przeszedł.
6. **Trzymaj się zakresu zadania.** Bez przeformatowywania, zmiany nazw i „przy okazji” w plikach, których zadanie nie dotyczy. Przed commitem sprawdź `git diff --stat`.

## Agent skills

### Issue tracker

Zgłoszenia i specyfikacje są lokalnymi plikami markdown w `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Domyślne pięć ról (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` i `docs/adr/` w katalogu głównym, tworzone w miarę potrzeby. See `docs/agents/domain.md`.

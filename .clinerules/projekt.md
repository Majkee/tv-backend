# Lumio TV backend

Backend dla telewizorów Lumio, które są już u klientów: rejestr urządzeń, aktualizacje firmware'u (OTA) i katalog aplikacji. Ten sam serwer serwuje symulator telewizora z `tv/`.

## Komendy

- Testy (całość): `./run_tests.sh` albo `run_tests.bat`. Bezpośrednio: `python -m unittest discover -s tests -t .` (na Windowsie zamiast `python` może być `py -3`).
- Jeden moduł testów: `python -m unittest tests.test_ota -v`
- Serwer i telewizor: `./run_server.sh` albo `run_server.bat`, potem `http://localhost:8765/tv/?device=TV-001`. Opcje: `--port 9000`, `--reset` (przywraca stan urządzeń z `fixtures/`).

Uruchamiaj testy po każdej zmianie. Przed zakończeniem pracy wszystkie testy muszą przechodzić.

## Struktura

- `backend/` – pakiet Pythona: `api.py` (routing JSON), `server.py` (HTTP), `registry.py` (urządzenia), `ota.py` (aktualizacje), `catalog.py` (aplikacje), `storage.py` (pliki JSON).
- `tests/` – `unittest`. `tests/support.py` daje izolowany store i serwer na wolnym porcie.
- `fixtures/` – dane referencyjne (modele, wydania, aplikacje, urządzenia) i wektory testowe.
- `data/` – stan runtime serwera, nie commitujemy.
- `tv/` – klient telewizora.

## Zasady

1. **Nie zmieniaj niczego w `tv/`.** Ten kod działa już w telewizorach klientów i nie da się go zaktualizować razem z backendem. Każda poprawka musi być po stronie serwera. Pilnuje tego `tests/test_tv_frozen.py`.
2. **Zgodność wsteczna API.** Telewizory w terenie wołają endpointy z `tv/app.js`. Nie zmieniaj nazw ani typów pól, które klient czyta, i nie usuwaj endpointów. Nowe pola i nowe endpointy są w porządku. Kontrakt opisują testy w `tests/test_api_contract.py`.
3. **Tylko biblioteka standardowa, Python 3.9+.** Żadnych `pip install`, żadnego `match`, `X | Y` w adnotacjach ani `zoneinfo`.
4. **Jeden krok = jeden commit na zielono.** Każdy commit zostawia wszystkie testy przechodzące. Komunikat commita opisuje, co się zmieniło.
5. **Podczas refaktoryzacji nie zmieniasz testów.** Refaktoryzacja nie zmienia zachowania, więc testy zostają takie, jakie były. Jeśli test trzeba zmienić, to nie jest refaktoryzacja: zatrzymaj się i zapytaj.
6. **Nie osłabiaj testów.** Nie usuwaj testów, nie zakomentowuj asercji i nie dopasowuj oczekiwań do wyniku tylko po to, żeby test przeszedł.
7. **Trzymaj się zakresu zadania.** Bez przeformatowywania, zmiany nazw i „przy okazji” w plikach, których zadanie nie dotyczy. Przed commitem sprawdź `git diff --stat`.

## Agent skills

### Issue tracker

Zgłoszenia i specyfikacje są lokalnymi plikami markdown w `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Domyślne pięć ról (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` i `docs/adr/` w katalogu głównym, tworzone w miarę potrzeby. See `docs/agents/domain.md`.

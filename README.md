# Lumio TV backend

Repozytorium do szkolenia z pracy z agentem AI (Claude Code w terminalu) według metodologii Matta Pococka. Jest tu backend telewizorów Lumio, symulator telewizora w przeglądarce i mały serwer MCP z bazą floty telewizorów.

**Treść zadań jest w [`zadania/index.html`](zadania/index.html).** Otwórz ten plik w przeglądarce, działa bez serwera. Postęp i notatki zapisują się w Twojej przeglądarce.

Przez całe szkolenie budujesz jedną rzecz: aplikację Pogoda na telewizor. W katalogu aplikacji już jest, ale po otwarciu pokazuje tylko swoją nazwę.

## Start (10 minut)

Potrzebujesz Pythona 3.9 lub nowszego, gita i Claude Code. Nic nie trzeba instalować przez `pip`.

1. Sklonuj repozytorium albo rozpakuj ZIP od prowadzącego (patrz [ZIP na Windowsie](#zip-na-windowsie)).
2. W terminalu przejdź do katalogu repozytorium i uruchom `claude`.
3. Wpisz `/sprawdz-srodowisko`. Na końcu raportu powinno być „Środowisko gotowe.”.
4. Uruchom serwer w drugim terminalu i otwórz telewizor w przeglądarce:

   ```bash
   ./run_server.sh
   ```

   Na Windowsie: `run_server.bat`. Potem otwórz <http://localhost:8765/tv/?device=TV-001>.

Jeśli coś nie działa, wklej prowadzącemu na czacie szkolenia raport z `/sprawdz-srodowisko`.

## Polecenia

| Co | Polecenie |
| --- | --- |
| Wszystkie testy | `./run_tests.sh` / `run_tests.bat` |
| Testy z nazwami | `./run_tests.sh -v` |
| Serwer i telewizor | `./run_server.sh` / `run_server.bat` |
| Serwer na innym porcie | `./run_server.sh --port 9000` |
| Przywrócenie stanu telewizorów | `./run_server.sh --reset` |
| Nowa gałąź od stanu startowego | `git switch -c <gałąź> start` |
| Serwer MCP bez agenta | `python3 mcp_server/smoke.py mcp_server/lumio_db.py` |

W Claude Code dowolne polecenie powłoki uruchomisz, poprzedzając je wykrzyknikiem, np. `! git log --oneline`. Możesz też po prostu poprosić agenta.

Polecenie Pythona zależy od systemu. Skrypty `run_*` same znajdą działające. Jeśli wpisujesz je ręcznie, spróbuj kolejno `python3`, `python`, `py -3`.

Telewizor musi być otwierany przez serwer (`http://localhost:...`). Otwarcie `tv/index.html` jako pliku nie zadziała, bo przeglądarka zablokuje zapytania do API.

## Symulator telewizora

Każda karta przeglądarki to jeden telewizor. Parametr `?device=` wybiera urządzenie. Na dole strony są linki do wszystkich urządzeń z rejestru.

Pilot obsługujesz myszą albo klawiaturą: strzałki, `Enter` (OK), `Esc` (wstecz), `H` (menu), `P` (zasilanie), `PageUp`/`PageDown` (kanały).

## Telewizor zamrożony po wdrożeniu

Na początku możesz zmieniać wszystko, także telewizor w `tv/`. Gdy oznaczysz gałąź jako wdrożoną u klientów tagiem `<gałąź>-wdrozone` (np. `git tag vibe-wdrozone`), kod telewizora na tej gałęzi jest zamrożony. Pilnuje tego test `tests/test_tv_frozen.py`, a agent wie o tym z [CLAUDE.md](CLAUDE.md).

## Struktura

```
backend/      API, serwer HTTP, rejestr urządzeń, OTA, katalog aplikacji
tv/           klient telewizora
tests/        testy unittest
fixtures/     dane referencyjne (JSON)
mcp_server/   serwer MCP z bazą floty Lumio (patrz mcp_server/README.md)
zadania/      strona z treścią zadań
.claude/      skille dla Claude Code
docs/agents/  konfiguracja skilli
.scratch/     lokalny tracker: specyfikacje i tickety (powstaje w trakcie zadań)
python/       miejsce na przenośnego Pythona (ignorowane przez gita)
```

## Skille

Skille Matta Pococka (repozytorium `mattpocock/skills`) są w `.claude/skills/` w zamrożonej wersji. Niczego nie instalujesz.

| Skill | Do czego |
| --- | --- |
| `/grilling` | wywiad, który doprecyzowuje plan przed pisaniem kodu |
| `/grill-with-docs` | ten sam wywiad, ale zapisuje też słownik pojęć (`CONTEXT.md`) i decyzje (`docs/adr/`) |
| `/to-spec` | specyfikacja z dotychczasowej rozmowy |
| `/to-tickets` | podział specyfikacji na tickety, które da się zrobić i sprawdzić osobno |
| `/implement` | implementacja ticketu: testy, kod, review, commit |
| `/code-review` | review zmian od wskazanego punktu: zgodność ze standardami i ze specyfikacją |
| `/prototype` | szybki prototyp do wyrzucenia, który odpowiada na jedno pytanie projektowe |
| `/tdd`, `/domain-modeling`, `/codebase-design` | używane przez skille powyżej |
| `/sprawdz-srodowisko` | sprawdzenie, czy środowisko jest gotowe do zadań |

Specyfikacje i tickety są plikami markdown w `.scratch/<feature>/`. Nie potrzebujesz dostępu do żadnego zewnętrznego trackera.

## ZIP na Windowsie

ZIP od prowadzącego zawiera katalog `.git`, więc działają gałęzie od tagu `start`. ZIP pobrany z przycisku „Download ZIP” na GitHubie nie ma historii ani tagu `start`, nie używaj go.

Jeśli Windows blokuje skrypty z rozpakowanego archiwum: przed rozpakowaniem kliknij ZIP prawym przyciskiem → Właściwości → zaznacz „Odblokuj” → OK.

## Brak Pythona

**Przenośny Python (Windows).** Pobierz oficjalny „Windows embeddable package” z python.org według instrukcji na stronie z zadaniami i rozpakuj go do folderu `python/` w katalogu repozytorium, tak żeby powstał plik `python/python.exe`. W pliku `python/python3XX._pth` dopisz osobną linię `..`, bez niej Python nie zobaczy kodu repozytorium. `/sprawdz-srodowisko` pomoże ułożyć pliki i dopisać tę linię. Nie wymaga to instalacji ani uprawnień administratora. Skrypty `run_*` używają przenośnego Pythona, gdy nie znajdą systemowego. Folder `python/` jest ignorowany przez gita.

Jeśli polityka firmy blokuje uruchamianie programów z katalogu użytkownika, napisz do prowadzącego na czacie szkolenia.

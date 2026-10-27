# Lumio TV backend

Repozytorium do ćwiczeń z modułu 3. Dołączasz do zespołu backendu Lumio, producenta telewizorów. Zespół obsługuje aktualizacje firmware'u (OTA), katalog aplikacji i rejestr urządzeń dla telewizorów, które są już u klientów.

Treść zadań jest na stronie z ćwiczeniami. Tu jest tylko kod.

## Start (15 minut)

Potrzebujesz Pythona 3.9 lub nowszego i gita. Nic nie trzeba instalować przez `pip`.

1. Sklonuj repozytorium albo rozpakuj ZIP (patrz [ZIP na Windowsie](#zip-na-windowsie)). Jeśli pracujesz w chmurze, utwórz kopię repozytorium według instrukcji na stronie z zadaniami.
2. Sprawdź Pythona: `python3 --version`, `python --version` albo `py --version`. Potrzebna jest wersja 3.9 lub nowsza. Jeśli żadne nie działa, patrz [Brak Pythona](#brak-pythona).
3. Uruchom testy. Wszystkie powinny przejść.

   ```bash
   ./run_tests.sh
   ```

   Na Windowsie (cmd albo PowerShell):

   ```bat
   run_tests.bat
   ```

4. Otwórz agenta (Claude Code albo Cline) w katalogu repozytorium i sprawdź, czy widzi skille, np. wpisz `/` i poszukaj `/tdd`.
5. **Obowiązkowo** uruchom `/sprawdz-srodowisko`. Na końcu raportu powinno być „Środowisko gotowe.”.
6. Lokalnie uruchom serwer i otwórz telewizor w przeglądarce.

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
| Jeden plik testów | `python -m unittest tests.test_ota -v` |
| Serwer | `./run_server.sh` / `run_server.bat` |
| Serwer na innym porcie | `./run_server.sh --port 9000` |
| Przywrócenie stanu telewizorów | `./run_server.sh --reset` |
| Powrót do stanu startowego ćwiczenia | `git reset --hard start` |

Polecenie Pythona zależy od systemu. Skrypty `run_*` same znajdą działające. Jeśli wpisujesz je ręcznie, spróbuj kolejno `py -3`, `python`, `python3`.

Telewizor musi być otwierany przez serwer (`http://localhost:...`). Otwarcie `tv/index.html` jako pliku nie zadziała, bo przeglądarka zablokuje zapytania do API.

## Symulator telewizora

Każda karta przeglądarki to jeden telewizor. Parametr `?device=` wybiera urządzenie, więc możesz otworzyć kilka telewizorów różnych modeli naraz. Na dole strony są linki do wszystkich urządzeń z rejestru.

Pilot obsługujesz myszą albo klawiaturą: strzałki, `Enter` (OK), `Esc` (wstecz), `H` (menu), `P` (zasilanie), `PageUp`/`PageDown` (kanały).

Pod ekranem jest dziennik urządzenia i licznik pobrań firmware'u.

## Struktura

```
backend/      API, serwer HTTP, rejestr urządzeń, OTA, katalog aplikacji
tests/        testy unittest
fixtures/     dane referencyjne i wektory testowe (JSON)
tv/           klient telewizora (nie zmieniamy, patrz CLAUDE.md)
.claude/      skille i ustawienia dla Claude Code
.cline/       skille dla Cline
.clinerules/  reguły projektu dla Cline
docs/agents/  konfiguracja skilli
.scratch/     lokalny tracker zgłoszeń i ticketów
python/       miejsce na przenośnego Pythona (ignorowane przez gita)
```

Zasady pracy z agentem są w [CLAUDE.md](CLAUDE.md). Cline czyta tę samą treść z `.clinerules/`.

## Skille

Skille Matta Pococka (repozytorium `mattpocock/skills`) są w repozytorium w zamrożonej wersji, w `.claude/skills/` i `.cline/skills/`. Niczego nie instalujesz.

| Skill | Do czego |
| --- | --- |
| `/grill-with-docs` | wywiad, który doprecyzowuje wymagania i zapisuje słownik pojęć oraz decyzje |
| `/grilling` | sam wywiad, bez dokumentów |
| `/to-spec` | specyfikacja z dotychczasowej rozmowy |
| `/to-tickets` | podział specyfikacji na tickety |
| `/implement` | implementacja ticketu |
| `/tdd` | red → green → refactor |
| `/diagnosing-bugs` | pętla diagnozy błędu: reprodukcja, hipotezy, poprawka |
| `/code-review` | review zmian od wskazanego commita lub tagu |
| `/triage` | ocena i porządkowanie zgłoszeń |
| `/codebase-design`, `/improve-codebase-architecture`, `/domain-modeling` | projektowanie modułów i słownika domeny |
| `/sprawdz-srodowisko` | sprawdzenie, czy środowisko jest gotowe do zadań (uruchom na początku zajęć) |

Zgłoszenia, tickety i specyfikacje są plikami markdown w `.scratch/<feature>/`. Stan zgłoszenia zapisany jest w linii `Status:` na początku pliku. Nie potrzebujesz dostępu do żadnego zewnętrznego trackera.

## Ustawienia agentów

**Claude Code.** `.claude/settings.json` pozwala uruchamiać testy, `git status`, `git diff` i `git log` bez pytania o zgodę.

**Cline.** Cline pyta o zgodę przy każdej akcji. Żeby ćwiczenia się nie wlekły, w panelu Cline włącz Auto-approve dla:

- Read project files
- Execute safe commands

Edycję plików (Edit project files) zostaw do ręcznej akceptacji. Wtedy widzisz każdą zmianę przed zapisaniem.

## ZIP na Windowsie

ZIP od prowadzącego zawiera katalog `.git`, więc działają `git diff` i `git reset --hard start`. ZIP pobrany z przycisku „Download ZIP” na GitHubie nie ma historii ani tagu `start`, nie używaj go.

Jeśli Windows blokuje skrypty z rozpakowanego archiwum: przed rozpakowaniem kliknij ZIP prawym przyciskiem → Właściwości → zaznacz „Odblokuj” → OK.

## Brak Pythona

1. **Przenośny Python (Windows).** Pobierz oficjalny „Windows embeddable package” z python.org według instrukcji na stronie z zadaniami i rozpakuj go do folderu `python/` w katalogu repozytorium, tak żeby powstał plik `python/python.exe`. W pliku `python/python3XX._pth` dopisz osobną linię `..`, bez niej Python nie zobaczy kodu repozytorium. `/sprawdz-srodowisko` pomoże ułożyć pliki i dopisać tę linię. Nie wymaga to instalacji ani uprawnień administratora. Skrypty `run_*` używają przenośnego Pythona, gdy nie znajdą systemowego. Folder `python/` jest ignorowany przez gita.
2. **Praca w chmurze**, gdy polityka firmy blokuje uruchamianie programów z katalogu użytkownika. Napisz do prowadzącego na czacie szkolenia.
3. **Codespaces.** Repozytorium ma `.devcontainer/devcontainer.json` z Pythonem 3.11. Port 8765 jest przekierowywany automatycznie.

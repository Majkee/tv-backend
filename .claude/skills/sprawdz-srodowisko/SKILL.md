---
name: sprawdz-srodowisko
description: Sprawdza, czy środowisko szkoleniowe jest gotowe do zadań modułu 3 (Python, git, skille, testy, dane do zadań, serwer telewizora), konfiguruje rozpakowanego przenośnego Pythona i kończy się jednoznacznym raportem.
disable-model-invocation: true
---

# Sprawdzenie gotowości środowiska

Twoje zadanie: sprawdzić, czy uczestnik może zacząć zadania modułu 3, i oddać krótki raport.

Zasadniczo tylko sprawdzasz. Jedyny wyjątek to konfiguracja przenośnego Pythona w kroku 1a, i to zawsze za zgodą uczestnika. Poza tym krokiem nie naprawiasz, nie instalujesz pakietów, nie pobierasz niczego z internetu, nie zmieniasz plików w repozytorium i nie zaczynasz żadnego zadania.

Nie czytaj kodu w `backend/` ani w `tv/` poza tym, czego wymaga dany krok. To nie jest część sprawdzenia.

Każdy krok kończy się jednym z trzech wyników:
- ✅ działa,
- ⚠️ działa z zastrzeżeniem, które nie blokuje zadań,
- ❌ nie działa i blokuje zadania.

Przy ⚠️ i ❌ podaj przyczynę w jednym zdaniu i jeden konkretny krok naprawczy. Jeśli krok zależy od poprzedniego, który dał ❌, oznacz go jako „pominięty” i podaj powód.

## Krok 0. Gdzie działasz

- Chmura: zmienna środowiskowa `CLAUDE_CODE_REMOTE` ma wartość `true`.
- W przeciwnym razie praca lokalna. Ustal system: Windows, Linux albo macOS, oraz rodzaj powłoki. Na Windowsie w Git Bash ścieżki piszesz z ukośnikiem (`./python/python.exe`), w PowerShell i cmd z odwrotnym ukośnikiem (`.\python\python.exe`).

Zapamiętaj wynik. Od niego zależą kroki 1, 1a i 6.

## Krok 1. Python systemowy

Sprawdź po kolei, aż któreś zadziała:
1. `python3 --version`
2. `python --version`
3. `py --version` (tylko Windows)

Wymagany jest Python 3.9 lub nowszy. Zapamiętaj polecenie, które zadziałało, i użyj go w kolejnych krokach.

Na Windowsie `python` bywa aliasem do Microsoft Store: nic nie wypisuje albo pokazuje komunikat o braku Pythona. Traktuj to jako brak Pythona.

- Działa Python 3.9+: ✅, pomiń krok 1a.
- Nie działa, a system to Windows: przejdź do kroku 1a.
- Nie działa na Linuksie lub macOS: ❌ z krokiem naprawczym „Napisz do trenera na czacie szkolenia”.

## Krok 1a. Przenośny Python w repozytorium (tylko Windows)

Uczestnik pobiera i rozpakowuje paczkę sam, według instrukcji na stronie z zadaniami. Ty pomagasz ją poprawnie ułożyć i skonfigurować. Przed każdą zmianą pokaż, co dokładnie zrobisz, i poczekaj na wyraźną zgodę. Zmieniasz wyłącznie zawartość folderu `python/` w korzeniu repozytorium.

### 1a.1 Znajdź paczkę

1. Docelowe miejsce to `python/python.exe` w korzeniu repozytorium, obok pliku `python/python3XX._pth` (na przykład `python315._pth`).
2. Jeśli tam go nie ma, poszukaj pliku `python.exe` leżącego obok pliku `python3*._pth`, najwyżej trzy poziomy w głąb od korzenia repozytorium, z pominięciem `.git`. Typowe miejsca po rozpakowaniu:
   - `python/python-3.15.2-embed-amd64/python.exe` (zagnieżdżony folder),
   - `python-3.15.2-embed-amd64/python.exe` (folder o innej nazwie w korzeniu).
3. Nie ma paczki nigdzie: ❌ z krokiem naprawczym „Pobierz i rozpakuj przenośnego Pythona do folderu `python` w repozytorium według instrukcji na stronie z zadaniami, potem uruchom mnie ponownie”. Nie pobieraj jej sam.

### 1a.2 Przenieś paczkę na miejsce

Jeśli paczka leży gdzie indziej niż `python/`:
1. Pokaż uczestnikowi, skąd i dokąd przeniesiesz zawartość, i zapytaj o zgodę.
2. Po zgodzie przenieś całą zawartość folderu z `python.exe` do `python/` w korzeniu repozytorium. Gdy folder `python/` już istnieje i nie jest pusty, nie nadpisuj niczego: opisz sytuację i zapytaj, co zrobić.
3. Usuń pusty folder, który został po przeniesieniu.

Bez zgody: ❌ z krokiem naprawczym „Przenieś zawartość folderu z `python.exe` do `python/` w korzeniu repozytorium”.

### 1a.3 Skonfiguruj plik `._pth`

Plik `python/python3XX._pth` musi zawierać osobną linię `..`. Dzięki niej Python widzi kod repozytorium; ścieżki w tym pliku są względne do jego położenia.

1. Przeczytaj plik. Jeśli linia `..` już jest, przejdź dalej.
2. Jeśli jej nie ma, pokaż obecną treść pliku i zapytaj o zgodę na dopisanie linii `..` na końcu.
3. Po zgodzie dopisz tylko tę jedną linię. Pozostałych linii nie zmieniaj, także zakomentowanego `#import site`.

Bez zgody: ❌ z krokiem naprawczym „Dopisz w `python/python3XX._pth` linię `..` według instrukcji na stronie z zadaniami”.

### 1a.4 Sprawdź działanie

1. `python.exe --version` z folderu `python/` pokazuje wersję 3.9 lub nowszą.
2. `python.exe -c "import unittest, json, http.server, sqlite3; print('ok')"` wypisuje `ok`.

Oba działają: ✅. Od tej chwili w kolejnych krokach używaj tego `python.exe`.

Jeśli `python.exe` nie daje się uruchomić, bo blokuje go Windows, SmartScreen, antywirus albo polityka firmy (na przykład „Odmowa dostępu” albo komunikat o zablokowanej aplikacji): ❌. Nie próbuj tego obchodzić: nie odblokowuj plików, nie zmieniaj ustawień zabezpieczeń i nie przenoś Pythona w inne miejsce. Krok naprawczy: „Napisz do trenera na czacie szkolenia. Przejdziesz na pracę w chmurze”.

### 1a.5 Git ignoruje folder

`git check-ignore -q python` powinno zakończyć się sukcesem. Jeśli folder `python/` nie jest ignorowany: ⚠️ z krokiem naprawczym „Nie commituj folderu `python/`; zgłoś trenerowi, że brakuje go w `.gitignore`”. Nie zmieniaj `.gitignore` sam.

## Krok 2. Git i stan startowy

1. `git --version`. Brak gita to ❌.
2. `git rev-parse --is-inside-work-tree` musi zwrócić `true`. Inaczej ❌: agent nie działa w katalogu repozytorium.
3. `git tag --list start` musi zwrócić `start`. Brak tagu to ❌: repozytorium pobrano bez historii (na przykład ZIP z GitHuba).
4. `git status --porcelain`: niezacommitowane zmiany to ⚠️, tylko informacja. Folder `python/` z przenośnym Pythonem jest ignorowany przez gita i nie liczy się jako zmiana.

## Krok 3. Skille

Sprawdź, czy istnieją pliki `SKILL.md` dla tych skilli:

- `grill-with-docs`, `grilling`, `domain-modeling`
- `to-spec`, `to-tickets`, `implement`
- `tdd`, `code-review`
- `triage`, `diagnosing-bugs`

Szukaj w `.claude/skills/<nazwa>/SKILL.md` (Claude Code) i w `.cline/skills/<nazwa>/SKILL.md` (Cline). Wystarczy komplet w katalogu narzędzia, w którym działasz. Jeśli nie wiesz, w którym narzędziu działasz, sprawdź oba i podaj wynik dla każdego.

Sprawdź też konfigurację skilli: istnieją pliki `docs/agents/issue-tracker.md` i `docs/agents/triage-labels.md`.

Brak któregokolwiek skilla albo pliku konfiguracji to ❌. Wypisz brakujące nazwy.

## Krok 4. Testy

Uruchom testy jednym poleceniem z korzenia repozytorium:
- Windows: `run_tests.bat`
- Linux, macOS i chmura: `./run_tests.sh`

Skrypty same znajdują Pythona systemowego albo przenośnego z folderu `python/`.

Wszystkie testy muszą przejść. Podaj liczbę testów i czas. Jakikolwiek nieudany test to ❌: wypisz nazwy nieudanych testów i pierwszą linię błędu. Nie poprawiaj testów ani kodu.

## Krok 5. Dane do zadań

Istnieje plik `fixtures/firmware_vectors.json`. Brak to ❌.

Treść zadań, w tym zgłoszenia incydentów, jest na stronie z zadaniami, a nie w repozytorium. Nie szukaj jej tutaj.

## Krok 6. Serwer telewizora

W chmurze pomiń ten krok z adnotacją „w chmurze telewizor pokazuje trener”. To nie jest błąd.

Lokalnie:
1. Uruchom serwer w tle: `run_server.bat` (Windows) albo `./run_server.sh`.
2. Odczekaj do 5 sekund i pobierz `http://localhost:8765/tv/?device=TV-001`. Oczekiwany kod odpowiedzi to 200.
3. Zatrzymaj serwer, który uruchomiłeś.

Zajęty port 8765 to ❌ z krokiem naprawczym „zamknij program, który używa portu 8765, albo poproś trenera o inny port”. Inny błąd uruchomienia to ❌ z pierwszą linią błędu.

## Raport

Na końcu wypisz raport w tej postaci, jedna linia na krok:

```
Gdzie: <chmura | lokalnie, system>
Python: <wynik> <wersja i skąd: systemowy lub przenośny z python/, albo przyczyna>
Git i stan startowy: <wynik> <szczegół>
Skille: <wynik> <szczegół lub brakujące nazwy>
Testy: <wynik> <liczba testów albo nieudane testy>
Dane do zadań: <wynik> <szczegół>
Serwer telewizora: <wynik> <szczegół>
Zmiany w tym przebiegu: <co zmieniłeś za zgodą uczestnika albo „brak”>
```

Pod raportem dokładnie jedna z dwóch linii:
- `Środowisko gotowe.` gdy nie ma żadnego ❌.
- `Środowisko niegotowe: <co naprawić najpierw>.` gdy jest choć jedno ❌. Wskaż jedną rzecz, od której trzeba zacząć.

Potem zakończ. Nie proponuj rozpoczęcia zadań.

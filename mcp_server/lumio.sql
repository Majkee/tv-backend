-- Baza floty telewizorów Lumio. Dane szkoleniowe, fikcyjne.
-- Serwer mcp_server/lumio_db.py ładuje ten plik przy każdym starcie do bazy SQLite w pamięci,
-- więc nic, co zrobi agent, nie zmienia tego pliku. Stan na 2026-11-02.

CREATE TABLE models (
  model TEXT PRIMARY KEY,           -- kod modelu, np. LM-55Q23
  name TEXT NOT NULL,               -- nazwa handlowa, np. Lumio Q 55"
  series TEXT NOT NULL,             -- seria: S (podstawowa), Q (średnia), X (premium)
  screen_inches INTEGER NOT NULL,   -- przekątna ekranu w calach
  year INTEGER NOT NULL             -- rok premiery modelu
);

CREATE TABLE devices (
  id TEXT PRIMARY KEY,              -- identyfikator telewizora, np. TV-003
  model TEXT NOT NULL REFERENCES models(model),
  region TEXT NOT NULL,             -- EU, NA albo APAC
  country TEXT NOT NULL,            -- kod kraju ISO 3166, np. PL, DE, US
  firmware TEXT NOT NULL,           -- zainstalowana wersja firmware'u, np. 2.8.1 (porównywalna jako tekst)
  activated_on TEXT NOT NULL,       -- pierwsze uruchomienie u klienta, RRRR-MM-DD
  last_seen TEXT                    -- ostatni kontakt z serwerem, RRRR-MM-DD; NULL = nigdy się nie połączył
);

CREATE TABLE firmware_releases (
  version TEXT PRIMARY KEY,         -- wersja, np. 2.9.0
  released_on TEXT NOT NULL,        -- data wydania, RRRR-MM-DD
  notes TEXT NOT NULL               -- opis zmian
);

CREATE TABLE support_tickets (
  id INTEGER PRIMARY KEY,           -- numer zgłoszenia
  device_id TEXT NOT NULL REFERENCES devices(id),
  opened_on TEXT NOT NULL,          -- data zgłoszenia, RRRR-MM-DD
  category TEXT NOT NULL,           -- aktualizacja, wifi, obraz, dzwiek, aplikacje albo pilot
  status TEXT NOT NULL,             -- otwarte, w_toku albo zamkniete
  summary TEXT NOT NULL             -- opis problemu słowami klienta
);

INSERT INTO models VALUES
  ('LM-43S19', 'Lumio S 43"', 'S', 43, 2019),
  ('LM-55S19', 'Lumio S 55"', 'S', 55, 2019),
  ('LM-50Q21', 'Lumio Q 50"', 'Q', 50, 2021),
  ('LM-55Q23', 'Lumio Q 55"', 'Q', 55, 2023),
  ('LM-65X25', 'Lumio X 65"', 'X', 65, 2025);

INSERT INTO firmware_releases VALUES
  ('1.9.4', '2023-09-04', 'Ostatnie wydanie ze starym układem partycji.'),
  ('2.0.0', '2024-03-11', 'Nowy układ partycji systemowej, wymagany przed kolejnymi aktualizacjami.'),
  ('2.8.0', '2026-02-16', 'Nowy ekran startowy, poprawki stabilności Wi-Fi.'),
  ('2.8.1', '2026-04-07', 'Poprawki bezpieczeństwa.'),
  ('2.9.0', '2026-07-20', 'Tryb gry z niskim opóźnieniem, nowy odtwarzacz multimediów.');

INSERT INTO devices VALUES
  ('TV-001', 'LM-55Q23', 'NA', 'US', '2.8.1', '2024-07-12', '2026-10-29'),
  ('TV-002', 'LM-43S19', 'NA', 'US', '2.8.0', '2024-04-30', '2026-10-30'),
  ('TV-003', 'LM-65X25', 'EU', 'PL', '2.8.1', '2025-07-27', '2026-11-02'),
  ('TV-004', 'LM-50Q21', 'APAC', 'JP', '2.9.0', '2023-01-22', '2026-10-28'),
  ('TV-005', 'LM-55S19', 'EU', 'DE', '2.8.1', '2025-08-25', '2026-11-02'),
  ('TV-006', 'LM-55Q23', 'EU', 'PL', '2.9.0', '2026-09-30', NULL),
  ('TV-007', 'LM-50Q21', 'EU', 'FR', '1.9.4', '2023-09-04', '2026-11-01'),
  ('TV-008', 'LM-65X25', 'EU', 'PL', '2.9.0', '2025-08-02', '2026-06-02'),
  ('TV-009', 'LM-55Q23', 'EU', 'PL', '2.8.1', '2026-10-07', '2026-10-31'),
  ('TV-010', 'LM-55S19', 'EU', 'SE', '2.8.0', '2024-06-06', '2026-10-29'),
  ('TV-011', 'LM-65X25', 'EU', 'ES', '2.8.0', '2025-03-12', '2026-11-02'),
  ('TV-012', 'LM-43S19', 'NA', 'US', '2.8.0', '2025-03-13', '2026-05-05'),
  ('TV-013', 'LM-55S19', 'EU', 'PL', '2.8.0', '2025-09-14', '2026-11-02'),
  ('TV-014', 'LM-55S19', 'EU', 'FR', '1.9.4', '2021-01-24', '2026-10-29'),
  ('TV-015', 'LM-55S19', 'EU', 'PL', '2.8.0', '2025-09-01', '2026-09-04'),
  ('TV-016', 'LM-55Q23', 'APAC', 'KR', '2.8.1', '2025-07-27', '2026-10-31'),
  ('TV-017', 'LM-55S19', 'APAC', 'KR', '2.8.0', '2020-08-27', '2026-10-28'),
  ('TV-018', 'LM-55Q23', 'NA', 'CA', '2.9.0', '2023-03-02', '2026-10-29'),
  ('TV-019', 'LM-50Q21', 'EU', 'PL', '2.8.1', '2024-08-17', '2026-10-30'),
  ('TV-020', 'LM-50Q21', 'EU', 'SE', '2.9.0', '2025-11-04', '2026-11-02'),
  ('TV-021', 'LM-55Q23', 'EU', 'IT', '2.9.0', '2023-07-15', '2026-11-01'),
  ('TV-022', 'LM-55Q23', 'NA', 'CA', '2.8.1', '2024-10-26', '2026-11-01'),
  ('TV-023', 'LM-55Q23', 'EU', 'PL', '1.9.4', '2024-06-25', '2026-10-30'),
  ('TV-024', 'LM-50Q21', 'EU', 'DE', '2.8.1', '2026-02-26', '2026-07-25'),
  ('TV-025', 'LM-55Q23', 'NA', 'CA', '2.8.1', '2024-12-12', '2026-10-31'),
  ('TV-026', 'LM-55Q23', 'EU', 'ES', '2.0.0', '2025-09-06', '2026-10-30'),
  ('TV-027', 'LM-55Q23', 'EU', 'SE', '2.9.0', '2024-10-12', '2026-11-01'),
  ('TV-028', 'LM-55S19', 'NA', 'US', '1.9.4', '2021-04-27', '2026-10-28'),
  ('TV-029', 'LM-55Q23', 'EU', 'DE', '2.9.0', '2026-01-28', '2026-11-02'),
  ('TV-030', 'LM-50Q21', 'EU', 'DE', '2.9.0', '2024-08-19', '2026-10-28'),
  ('TV-031', 'LM-55Q23', 'NA', 'US', '2.8.0', '2024-04-05', '2026-10-30'),
  ('TV-032', 'LM-50Q21', 'NA', 'US', '2.9.0', '2022-11-08', NULL),
  ('TV-033', 'LM-43S19', 'APAC', 'AU', '2.8.1', '2025-06-21', '2026-11-02'),
  ('TV-034', 'LM-43S19', 'APAC', 'KR', '2.0.0', '2021-01-23', '2026-10-31'),
  ('TV-035', 'LM-55S19', 'EU', 'SE', '2.8.1', '2021-02-02', '2026-11-02'),
  ('TV-036', 'LM-55S19', 'EU', 'PL', '2.8.1', '2022-06-21', '2026-10-31'),
  ('TV-037', 'LM-43S19', 'EU', 'PL', '2.8.1', '2019-05-14', '2026-11-02'),
  ('TV-038', 'LM-65X25', 'APAC', 'AU', '2.9.0', '2025-09-02', '2026-10-29'),
  ('TV-039', 'LM-50Q21', 'EU', 'PL', '2.9.0', '2025-07-31', '2026-05-12'),
  ('TV-040', 'LM-65X25', 'NA', 'US', '2.9.0', '2025-03-12', '2026-07-16'),
  ('TV-041', 'LM-50Q21', 'NA', 'US', '2.0.0', '2021-11-23', '2026-10-29'),
  ('TV-042', 'LM-50Q21', 'EU', 'NL', '2.8.1', '2025-06-23', '2026-10-31'),
  ('TV-043', 'LM-55Q23', 'EU', 'SE', '2.8.1', '2026-01-08', '2026-10-28'),
  ('TV-044', 'LM-65X25', 'EU', 'IT', '2.9.0', '2026-04-01', '2026-11-02'),
  ('TV-045', 'LM-50Q21', 'EU', 'DE', '2.9.0', '2023-01-01', '2026-11-02'),
  ('TV-046', 'LM-55Q23', 'APAC', 'KR', '2.9.0', '2024-05-04', '2026-10-29'),
  ('TV-047', 'LM-65X25', 'EU', 'DE', '2.8.0', '2026-03-05', '2026-11-01'),
  ('TV-048', 'LM-55Q23', 'NA', 'US', '2.8.1', '2026-07-22', '2026-07-22'),
  ('TV-049', 'LM-55S19', 'NA', 'US', '2.8.0', '2025-05-12', '2026-10-30'),
  ('TV-050', 'LM-50Q21', 'NA', 'CA', '2.8.0', '2025-03-01', '2026-10-31'),
  ('TV-051', 'LM-55Q23', 'EU', 'DE', '2.9.0', '2024-12-05', '2026-10-31'),
  ('TV-052', 'LM-55S19', 'NA', 'US', '2.8.1', '2025-03-07', '2026-10-31'),
  ('TV-053', 'LM-43S19', 'EU', 'PL', '2.0.0', '2020-08-14', '2026-10-29'),
  ('TV-054', 'LM-50Q21', 'EU', 'ES', '2.9.0', '2021-10-26', '2026-10-31'),
  ('TV-055', 'LM-55S19', 'EU', 'NL', '2.8.1', '2025-04-26', '2026-10-31'),
  ('TV-056', 'LM-65X25', 'EU', 'SE', '2.8.1', '2025-03-16', '2026-10-30'),
  ('TV-057', 'LM-43S19', 'EU', 'PL', '2.0.0', '2023-05-02', '2026-10-28'),
  ('TV-058', 'LM-55S19', 'APAC', 'KR', '1.9.4', '2020-04-30', '2026-11-02'),
  ('TV-059', 'LM-55Q23', 'NA', 'US', '2.8.0', '2025-02-15', '2026-11-01'),
  ('TV-060', 'LM-65X25', 'EU', 'DE', '2.8.0', '2025-03-05', '2026-05-26');

INSERT INTO support_tickets VALUES
  (1, 'TV-047', '2026-06-08', 'aktualizacja', 'zamkniete', 'Komunikat o aktualizacji pojawia się w trakcie oglądania filmu.'),
  (2, 'TV-031', '2026-06-09', 'aplikacje', 'zamkniete', 'KinoNet nie loguje się po aktualizacji.'),
  (3, 'TV-031', '2026-06-10', 'obraz', 'zamkniete', 'Kolory są wyblakłe w trybie HDR.'),
  (4, 'TV-049', '2026-06-14', 'obraz', 'zamkniete', 'Kolory są wyblakłe w trybie HDR.'),
  (5, 'TV-022', '2026-06-22', 'aktualizacja', 'zamkniete', 'Komunikat o aktualizacji pojawia się w trakcie oglądania filmu.'),
  (6, 'TV-003', '2026-06-25', 'aktualizacja', 'zamkniete', 'Aktualizacja zatrzymuje się na 60% i nie rusza dalej.'),
  (7, 'TV-039', '2026-06-28', 'wifi', 'zamkniete', 'Telewizor nie widzi sieci 5 GHz.'),
  (8, 'TV-022', '2026-07-01', 'aktualizacja', 'zamkniete', 'Telewizor co chwilę pobiera tę samą aktualizację i się restartuje.'),
  (9, 'TV-059', '2026-07-02', 'obraz', 'zamkniete', 'Ekran miga przy jasnych scenach.'),
  (10, 'TV-056', '2026-07-03', 'aktualizacja', 'zamkniete', 'Aktualizacja zatrzymuje się na 60% i nie rusza dalej.'),
  (11, 'TV-030', '2026-07-08', 'dzwiek', 'zamkniete', 'Brak dźwięku przez HDMI ARC.'),
  (12, 'TV-005', '2026-07-10', 'aplikacje', 'zamkniete', 'Nie widzę aplikacji Music Box w katalogu.'),
  (13, 'TV-020', '2026-07-12', 'pilot', 'zamkniete', 'Przyciski kanałów na pilocie nie działają.'),
  (14, 'TV-008', '2026-07-12', 'aplikacje', 'zamkniete', 'Aplikacja Pogoda pokazuje tylko swoją nazwę.'),
  (15, 'TV-017', '2026-07-25', 'dzwiek', 'zamkniete', 'Brak dźwięku przez HDMI ARC.'),
  (16, 'TV-044', '2026-07-29', 'aktualizacja', 'zamkniete', 'Po aktualizacji telewizor nie widzi pendrive''a.'),
  (17, 'TV-038', '2026-07-30', 'aktualizacja', 'zamkniete', 'Telewizor co chwilę pobiera tę samą aktualizację i się restartuje.'),
  (18, 'TV-037', '2026-08-07', 'aplikacje', 'zamkniete', 'KinoNet nie loguje się po aktualizacji.'),
  (19, 'TV-019', '2026-08-08', 'wifi', 'zamkniete', 'Po wybudzeniu z czuwania brak internetu.'),
  (20, 'TV-015', '2026-08-11', 'obraz', 'zamkniete', 'Opóźnienie obrazu w grach mimo trybu gry.'),
  (21, 'TV-003', '2026-08-12', 'aplikacje', 'zamkniete', 'Aplikacja Streamly zamyka się po kilku minutach.'),
  (22, 'TV-010', '2026-08-19', 'wifi', 'zamkniete', 'Telewizor nie widzi sieci 5 GHz.'),
  (23, 'TV-038', '2026-08-21', 'aktualizacja', 'zamkniete', 'Telewizor co chwilę pobiera tę samą aktualizację i się restartuje.'),
  (24, 'TV-046', '2026-08-26', 'wifi', 'zamkniete', 'Po wybudzeniu z czuwania brak internetu.'),
  (25, 'TV-049', '2026-09-01', 'obraz', 'zamkniete', 'Opóźnienie obrazu w grach mimo trybu gry.'),
  (26, 'TV-056', '2026-09-03', 'aktualizacja', 'zamkniete', 'Komunikat o aktualizacji pojawia się w trakcie oglądania filmu.'),
  (27, 'TV-022', '2026-09-03', 'dzwiek', 'w_toku', 'Dźwięk przesunięty względem obrazu.'),
  (28, 'TV-010', '2026-09-05', 'dzwiek', 'otwarte', 'Dźwięk przesunięty względem obrazu.'),
  (29, 'TV-034', '2026-09-09', 'aplikacje', 'zamkniete', 'Nie widzę aplikacji Music Box w katalogu.'),
  (30, 'TV-044', '2026-09-09', 'dzwiek', 'w_toku', 'Dźwięk przesunięty względem obrazu.'),
  (31, 'TV-028', '2026-09-16', 'aktualizacja', 'otwarte', 'Komunikat o aktualizacji pojawia się w trakcie oglądania filmu.'),
  (32, 'TV-047', '2026-09-18', 'aktualizacja', 'otwarte', 'Aktualizacja zatrzymuje się na 60% i nie rusza dalej.'),
  (33, 'TV-011', '2026-09-19', 'wifi', 'w_toku', 'Telewizor nie widzi sieci 5 GHz.'),
  (34, 'TV-011', '2026-09-26', 'wifi', 'otwarte', 'Po wybudzeniu z czuwania brak internetu.'),
  (35, 'TV-003', '2026-09-27', 'dzwiek', 'otwarte', 'Brak dźwięku przez HDMI ARC.'),
  (36, 'TV-006', '2026-09-30', 'aktualizacja', 'w_toku', 'Aktualizacja zatrzymuje się na 60% i nie rusza dalej.'),
  (37, 'TV-012', '2026-10-06', 'aktualizacja', 'otwarte', 'Aktualizacja zatrzymuje się na 60% i nie rusza dalej.'),
  (38, 'TV-043', '2026-10-08', 'wifi', 'otwarte', 'Po wybudzeniu z czuwania brak internetu.'),
  (39, 'TV-030', '2026-10-13', 'aplikacje', 'otwarte', 'Aplikacja Streamly zamyka się po kilku minutach.'),
  (40, 'TV-029', '2026-10-15', 'aplikacje', 'w_toku', 'KinoNet nie loguje się po aktualizacji.'),
  (41, 'TV-056', '2026-10-17', 'aktualizacja', 'w_toku', 'Telewizor co chwilę pobiera tę samą aktualizację i się restartuje.'),
  (42, 'TV-050', '2026-10-17', 'aplikacje', 'w_toku', 'KinoNet nie loguje się po aktualizacji.'),
  (43, 'TV-008', '2026-10-18', 'pilot', 'zamkniete', 'Przyciski kanałów na pilocie nie działają.'),
  (44, 'TV-037', '2026-10-21', 'aktualizacja', 'otwarte', 'Telewizor co chwilę pobiera tę samą aktualizację i się restartuje.'),
  (45, 'TV-035', '2026-10-21', 'dzwiek', 'otwarte', 'Brak dźwięku przez HDMI ARC.'),
  (46, 'TV-037', '2026-10-24', 'wifi', 'zamkniete', 'Po wybudzeniu z czuwania brak internetu.'),
  (47, 'TV-047', '2026-10-24', 'aktualizacja', 'otwarte', 'Telewizor co chwilę pobiera tę samą aktualizację i się restartuje.'),
  (48, 'TV-005', '2026-11-02', 'obraz', 'w_toku', 'Opóźnienie obrazu w grach mimo trybu gry.');

# Prompt merge tygodniowy do NOW.md

Zaktualizuj NOW.md na podstawie sygnałów tygodniowych. To nie jest przyrostowy merge jak daily — to **przepisanie sekcji** na podstawie pełnego obrazu tygodnia.

Cel NOW.md: kontekst pamięci dla asystenta AI. Każda nowa sesja ładuje ten plik automatycznie. Asystent powinien wiedzieć: nad czym pracujemy, co się wydarzyło ostatnio, gdzie są blokery, co stoi, jakie decyzje obowiązują.

## Input

1. Aktualny NOW.md
2. Lista sygnałów JSON z ekstrakcji tygodniowej
3. Git diff NOW.md z ostatniego tygodnia (opcjonalnie — jeśli dostępny)

## Zasady merge tygodniowego

### Konsolidacja (kluczowa operacja weekly)

Wiele atomowych wpisów daily o tym samym projekcie/temacie → **jeden zbiorczy wpis.**

Zamiast:
```
- 2026-03-28: Webinar 02.04 — dodano 3 sekcje prezentacji
- 2026-03-29: Webinar 02.04 — grafiki gotowe
- 2026-03-30: Webinar 02.04 — próba generalna, przypomnienia mailowe
- 2026-04-01: Webinar 02.04 — 13 sekcji, oferta -30%
```

Napisz:
```
- 2026-04-01: Webinar 02.04 — prezentacja ukończona (13 sekcji, grafiki), przypomnienia mailowe (3 wysyłki), oferta -30%. Próba generalna i część sprzedażowa gotowe.
```

Jeden wpis, pełny obraz, data ostatniego update'u.

### Tabela projektów — przepisanie

Dla każdego projektu w tabeli:
- **Aktywny z aktywnością w logach:** zaktualizuj "Uwagi" na zbiorczy status z tygodnia
- **Aktywny BEZ aktywności w logach:** zmień status na "stalled" — to ważna informacja
- **Zakończony 7+ dni temu:** usuń z tabeli
- **Nowy (pojawił się w tygodniu):** dodaj

### Sekcja "Na tapecie" — reset

Przepisz na podstawie tego co **realnie dominowało** w tygodniu (z logów), nie co było zadeklarowane w poniedziałek. Max 5 pozycji. Jeśli coś nie było priorytetem ale zjadło 40% czasu — powinno tu być.

### Sekcja "Ostatnie ustalenia" — agresywny cleanup

| Typ ustalenia | Reguła weekly |
|---------------|---------------|
| Jednorazowy event (wpis napisany, deploy, nagranie) | **Usuń** — to event log, nie kontekst |
| Trwała decyzja (cenowa, architekturalna, technologiczna) | **Zostaw** dopóki obowiązuje |
| Decyzja cofnięta lub zmieniona w tygodniu | **Zastąp** nową decyzją, usuń starą |
| Ustalenie starsze niż 14 dni | **Usuń** — jeśli nadal ważne, powinno być w uwagach projektu |

Po cleanup skonsoliduj: wiele ustaleń dot. jednego projektu → jeden wpis.

### Sekcja "Blokery"
- Bloker rozwiązany w tygodniu → **usuń**
- Bloker nadal otwarty → **zostaw**, opcjonalnie dodaj kontekst (od kiedy blokuje)
- Nowy bloker z tygodnia → dodaj

### Sekcja "Otwarte decyzje"
- Decyzja podjęta w tygodniu → **usuń** (przenieś do "Ostatnie ustalenia" jako trwałą decyzję)
- Nadal otwarta → zostaw

## Format NOW.md

```markdown
# NOW — Bieżący kontekst

*Ostatni update: YYYY-MM-DD HH:MM*

## Aktywne projekty
| Projekt | Status | Deadline | Uwagi |
|---------|--------|----------|-------|
| ... | ... | ... | ... |

## Na tapecie
1. ...

## Otwarte decyzje
- [ ] ...

## Ostatnie ustalenia
- YYYY-MM-DD: ...

## Blokery
- ...
```

## Ograniczenia

- **Max 8 000 znaków** (sprawdź `wc -m`) — weekly ma ZMNIEJSZAĆ rozmiar pliku, nie zwiększać. Liczba linii nie ma znaczenia
- **Szczegóły projektu → plik projektu** (`Zadania/projekty/<projekt>/_KONTEKST.md`), w NOW.md zostaje zdanie stanu + deadline + bloker
- **Sekcje „Wklejki", „Wcześniejsze (bez zmian)", listy meta-wzorców — usuń.** Reguły pracy idą do persona.md przez `/reflect`, nie tutaj
- **NIE duplikuj** info z persona.md, biznes.md, soul.md
- **Zaktualizuj timestamp** na bieżącą datę i godzinę
- **Sekcje mogą być puste** — nie usuwaj nagłówków, zostaw `- (brak)` jeśli sekcja jest pusta
- **Przepisuj, nie dopisuj** — weekly to reset sekcji na aktualny stan, nie append

## Output

Zwróć pełny, zaktualizowany NOW.md jako markdown. Gotowy do zapisania.

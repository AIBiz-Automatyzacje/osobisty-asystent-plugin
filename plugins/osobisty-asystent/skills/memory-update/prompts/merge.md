# Prompt merge sygnałów do NOW.md

Zaktualizuj NOW.md na podstawie nowych sygnałów z sesji. NOW.md to dynamiczny kontekst pracy — co teraz robię, jakie mam priorytety, co zdecydowałem.

## Input

1. Aktualny NOW.md (może być pusty template)
2. Lista sygnałów JSON z ekstrakcji

## Zasady merge

### Dodawanie (typ: NOWY)
- Dodaj do odpowiedniej sekcji NOW.md
- Projekty → tabela "Aktywne projekty"
- Decyzje → sekcja "Ostatnie ustalenia" (z datą)
- Priorytety → sekcja "Na tapecie" (max 5 pozycji)
- Blokery → sekcja "Blokery"
- Stack → uwagi przy projekcie lub osobny wpis w "Ostatnie ustalenia"

### Aktualizacja (typ: UPDATE)
- Znajdź istniejący wpis i zaktualizuj status/uwagi
- NIE duplikuj — jeśli projekt już jest w tabeli, zmień status

### Usuwanie (typ: ZAKONCZONE/USUN + reguły stale data)

| Typ | Reguła |
|-----|--------|
| Projekt zakończony | Usuń z tabeli po 7 dniach od zakończenia |
| Decyzja podjęta [x] | Usuń po 14 dniach |
| Bloker rozwiązany | Usuń natychmiast |
| Pozycja z "Na tapecie" nieaktualna | Usuń jeśli nie pojawił się ponownie |
| Wzorzec pracy | Zostaw (trwale, chyba że zmiana) |

### Conflict resolution
- Nowsze fakty nadpisują starsze (dodaj datę)
- Nowsza decyzja nadpisuje starą
- Priorytety: zamień, nie kumuluj (max 5)

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

- **Max 8 000 znaków** (sprawdź `wc -m`), liczba linii nie ma znaczenia — wiersz tabeli to nie miejsce na akapit. Jeśli przekraczasz, tnij najstarsze wpisy i szczegóły projektów
- **Szczegóły projektu → plik projektu, nie NOW.md.** Numery slajdów, linie scenariusza, nazwy plików roboczych, listy podzadań idą do `_KONTEKST.md` projektu (`Zadania/projekty/<projekt>/`); gdy projekt nie ma takiego pliku, szczegóły pomiń. W NOW.md zostaje jedno zdanie stanu + deadline + bloker
- **Zero event logu**: „wpis opublikowany", „oferta wysłana", „raport ✅" nie wchodzą. Wklejki i listy „do skopiowania" nie wchodzą
- **Reguły pracy nie wchodzą** — trwałe zasady (jak pracować, czego unikać) idą do persona.md przez `/reflect`, nie do „Ostatnie ustalenia"
- **NIE duplikuj** info z persona.md (styl komunikacji), biznes.md (model biznesowy, produkty, platformy), soul.md (charakter AI)
- **Zaktualizuj timestamp** "Ostatni update" na bieżącą datę i godzinę
- **Sekcje mogą być puste** — nie usuwaj nagłówków, zostaw `- (brak)` jeśli sekcja jest pusta

## Output

Zwróć pełny, zaktualizowany NOW.md jako markdown. Gotowy do zapisania.

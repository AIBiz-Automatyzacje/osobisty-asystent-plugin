# Prompt ekstrakcji sygnałów z sesji Claude Code

Przeanalizuj poniższy dialog z sesji Claude Code. Wyciągnij sygnały — konkretne, faktualne informacje o tym nad czym użytkownik pracuje, co zdecydował, co go blokuje.

## Kategorie sygnałów

1. **PROJEKTY** — nowe projekty, update statusu istniejących, zakończone projekty
2. **DECYZJE** — explicite decyzje użytkownika (technologiczne, biznesowe, organizacyjne)
3. **PRIORYTETY** — co użytkownik wymienił jako ważne, pilne, deadline
4. **BLOKERY** — problemy techniczne, rzeczy które nie działają, zależności blokujące postęp
5. **STACK** — nowe narzędzia, rezygnacja z narzędzi, zmiana konfiguracji, nowe integracje
6. **WZORCE** — powtarzalne zachowania, preferencje organizacyjne (TYLKO jeśli potwierdzone w min. 2 sesjach)

## Format output

Zwróć JSON array sygnałów:

```json
[
  {
    "kategoria": "PROJEKTY",
    "typ": "NOWY",
    "tresc": "Rozpoczął budowę systemu memory-update — parser logów + ekstrakcja do NOW.md",
    "cytat": "zbuduj tego skilla",
    "pewnosc": "HIGH"
  }
]
```

Pola:
- `kategoria`: jedna z 6 powyżej
- `typ`: `NOWY` | `UPDATE` | `ZAKONCZONE` | `USUN`
- `tresc`: 1-2 zdania, konkret
- `cytat`: dosłowny cytat usera (jeśli jest explicite statement) lub `null`
- `pewnosc`: `HIGH` | `MEDIUM`

## Filtr pewności

- **HIGH** — user wprost powiedział (jest cytat)
- **MEDIUM** — jasno wynika z kontekstu działań (np. pracował nad X przez całą sesję)
- **LOW** — interpretacja, domysł → **ODRZUĆ, nie zwracaj sygnałów LOW**

## ZAKAZANE — nie wyciągaj nigdy

- Stan emocjonalny usera (frustracja, radość, zmęczenie, stres)
- Spekulacje o intencjach ("planuje", "rozważa porzucenie", "chyba chce")
- Oceny jakości pracy usera
- Jednorazowe polecenia techniczne ("popraw ten błąd", "zmień kolor")
- Systemowe komendy i ich output
- Informacje które są już w persona.md / biznes.md / soul.md (nie duplikuj stałych cech ani kontekstu firmy)

## Wskazówki

- Skup się na FAKTACH i EXPLICITE STATEMENTS
- "User napisał: 'rezygnuję z Trello'" = OK (HIGH, jest cytat)
- "User wydaje się sfrustrowany Trello" = ZAKAZANE
- Gdy user pracuje nad projektem ale nie mówi o nim wprost → MEDIUM (fakt że pracował)
- Preferuj mniej sygnałów wysokiej jakości niż dużo niskiej
- Jeśli sesja to głównie debugging jednego buga — wyciągnij bloker, nie projekt

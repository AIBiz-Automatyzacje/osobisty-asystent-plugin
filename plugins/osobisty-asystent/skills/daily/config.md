# Konfiguracja /daily

Wspólny kontrakt z `/utworz-zadanie` (`utworz-zadanie/config.md`) — zmieniaj oba pliki razem.

## Ścieżki

Względne do workspace (`$CLAUDE_PROJECT_DIR`).

| Klucz | Ścieżka |
|-------|---------|
| dashboard | `Zadania/Dashboard.md` |
| archiwum | `Zadania/zrobione/YYYY-MM.md` (jeden plik na miesiąc) |
| cykliczne | `Zadania/cykliczne/recurring.md` |
| notatki do zadań (opcjonalne) | `Zadania/notatki/` |
| skrzynka (opcjonalna, Team OS) | `Zadania/Skrzynka.md` |

## Format linii

```
- [ ] Nazwa — [emoji] · DD.MM
- [ ] Nazwa — [emoji]                                   ← bez terminu
- [ ] Nazwa [[ścieżka|📎]] — [emoji] · DD.MM            ← z linkiem do materiału
- [ ] 🔁 Nazwa — [emoji]                                ← cykliczne
- [ ] 🔁 Nazwa — [emoji] — 📁 [projekt]                 ← cykliczne z kolumną Projekt
```

## Parsowanie linii

Czytaj **od końca linii**, bo nazwa może zawierać „—”:
1. `· DD.MM` na końcu → termin; brak → bez terminu.
2. Ostatnie emoji priorytetu (🔴/🟡/🟢) poprzedzone `— ` → priorytet; brak → 🟢.
3. Cykliczne: `🔁` na początku treści; opcjonalny ogon `— 📁 projekt` zachowaj.
4. Reszta (bez końcowego ` — …`) = nazwa, razem z linkami `[[…]]`.
5. Stary format `[[w_trakcie/plik|Tytuł]]` → nazwa = cały link (zostaw bez zmian).
6. Tolerancja: `-` zamiast `—`, brak `·`, zapis `DD.MM.YYYY` albo `YYYY-MM-DD` → normalizuj do formatu wyżej.
7. Linia `_brak zadań_` to znacznik pustego dnia, nie zadanie — pomiń ją (nie przenoś, nie ostrzegaj).

## Sekcje Dashboardu

Nagłówki **bez emoji**. Kolejność w pliku = kolejność w tabeli.

| Nagłówek | Warunek |
|----------|---------|
| `## Zaległe` | termin < dziś |
| `## Dzisiaj, [dzień_tygodnia] DD.MM` | termin = dziś (np. `## Dzisiaj, poniedziałek 28.09`) |
| `## [Dzień_tygodnia] DD.MM` — jeden na każdy dzień z okna tygodnia | termin = ten dzień (np. `## Wtorek 29.09`) |
| `## Później` | termin > dziś i poza oknem tygodnia (w tym sobota i niedziela) |
| `## Bez terminu` | brak terminu |

**Okno tygodnia** (dni robocze pokazywane osobno):
- dziś pn–czw → od jutra do piątku tego tygodnia,
- dziś pt → puste (po „Dzisiaj” od razu „Później”),
- dziś sob/nd → pn–pt następnego tygodnia.

Dzień z okna bez zadań dostaje pod nagłówkiem jedną linię `_brak zadań_` (sekcja nie znika).
Pozostałe puste sekcje (Zaległe, Dzisiaj, Później, Bez terminu) zostają jako sam nagłówek.

**Zgodność wstecz:** stary Dashboard ma nagłówki z emoji (`## 🔥 Zaległe`, `## 📅 Ten tydzień`…) —
czytając, bierz zadania spod DOWOLNEGO `##`; zapisując, używaj wyłącznie nagłówków z tabeli.

## Rok terminu

Linia ma samo `DD.MM`. Rok wybierz tak, żeby data wypadła najbliżej dzisiejszej: w oknie od 180 dni
wstecz do 185 dni w przód (np. 28.12 zapisane 5.01 → poprzedni rok, czyli zaległe; 05.01 zapisane 28.12 → przyszły rok).

## Emoji priorytetów

| Priorytet | Emoji | Kolejność sortowania |
|-----------|-------|----------------------|
| pilne | 🔴 | 1 |
| wazne | 🟡 | 2 |
| normalne | 🟢 | 3 |

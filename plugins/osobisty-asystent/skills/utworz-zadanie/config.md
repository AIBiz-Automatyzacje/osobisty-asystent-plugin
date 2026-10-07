# Config: Utwórz Zadanie

Wspólny kontrakt z `/daily` (`daily/config.md`) — zmieniaj oba pliki razem.

## Ścieżki

Względne do workspace (`$CLAUDE_PROJECT_DIR`).

| Element | Ścieżka |
|---------|---------|
| Dashboard | `Zadania/Dashboard.md` |
| Notatki do zadań (opcjonalne) | `Zadania/notatki/` |

## Format linii

```
- [ ] Nazwa — [emoji] · DD.MM
- [ ] Nazwa — [emoji]                              ← bez terminu
- [ ] Nazwa [[ścieżka/do/pliku|📎]] — [emoji] · DD.MM   ← z linkiem do materiału
```

- `—` to em dash ze spacjami, `·` to kropka środkowa.
- Termin zawsze `DD.MM` (bez roku).
- Link: ścieżka od roota vaulta; pliki `.md` bez rozszerzenia, inne (`.html`, `.pdf`) z rozszerzeniem.

## Priorytety

| Wartość | Emoji | Kiedy |
|---------|-------|-------|
| pilne | 🔴 | Blokuje innych, pieniądze, termin nieprzekraczalny |
| wazne | 🟡 | Ważne, ale nie blokuje |
| normalne | 🟢 | Reszta (domyślne) |

## Sekcje Dashboardu (kolejność)

Nagłówki **bez emoji** — pełny opis w `daily/config.md` → „Sekcje Dashboardu”.

| Nagłówek (początek) | Warunek |
|---------------------|---------|
| `## Zaległe` | termin w przeszłości |
| `## Dzisiaj` | termin = dziś (`## Dzisiaj, poniedziałek 28.09`) |
| `## [Dzień_tygodnia] DD.MM` | termin = dzień z okna tygodnia (`## Wtorek 29.09`) |
| `## Później` | termin poza oknem tygodnia (także sobota i niedziela) |
| `## Bez terminu` | brak terminu |

**Okno tygodnia:** dziś pn–czw → od jutra do piątku; dziś pt → brak; dziś sob/nd → pn–pt następnego tygodnia.

Sortowanie w sekcji: termin rosnąco → priorytet (pilne > wazne > normalne).

## Terminy — sygnały z wypowiedzi

| User mówi | Termin |
|-----------|--------|
| dzisiaj, do końca dnia | dziś |
| jutro | +1 dzień |
| pojutrze | +2 dni |
| do [dzień tygodnia] | najbliższy taki dzień (dziś się nie liczy) |
| DD.MM / YYYY-MM-DD | ta data |
| brak / nic | bez terminu |

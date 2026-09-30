# Mapping: Sygnały → Pliki

Reflect aktualizuje pliki osobiste/behawioralne: **persona.md**, **soul.md**,
**content/voice-of-tone.md** oraz opis projektu w **CLAUDE.md**.

**Czego reflect NIE rusza:**
- **NOW.md** — bieżący stan/projekty → domena `memory-update`.
- **biznes.md** — fakty o firmie/pracy (branża, klient, platformy, stack). Zmienia się rzadko,
  user aktualizuje go ręcznie. Jeśli user mówi "mamy już 200 klientów" — to fakt biznesowy,
  NIE sygnał dla reflecta.

Sekcje persona.md odpowiadają strukturze generowanej przez `onboarding/prompt-persona.md`
(numeracja 1-8). Sekcje voice-of-tone.md — strukturze `onboarding/prompt-voice-of-tone.md`.

---

## persona.md

### Sekcja 3 — Styl komunikacji
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Zmiana preferencji długości | "za długie", "krócej", "jednym zdaniem" | UPDATE |
| Zmiana preferencji formatu | "bez listy", "tabelą", "w punktach" | UPDATE |
| Zmiana preferencji feedbacku | "mów wprost", "nie owijaj" | UPDATE |

### Sekcja 4 — Wartości i zasady
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowa zasada pracy | "zawsze X przed Y", "nigdy nie rób X" | ADD |
| Zmiana podejścia | "jednak lepiej Z niż Y" | REPLACE |

### Sekcja 5 — Praca na co dzień (+ rytm)
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Zmiana rytmu/godzin pracy | "teraz zaczynam o X", "pracuję wieczorami" | UPDATE |
| Nowe narzędzie w codziennej pracy | "zacząłem używać X na stałe" | ADD |
| ⚠️ Bieżący projekt | "robię teraz X" | → to NOW.md (memory-update), NIE persona |

### Sekcja 6 — Blokery i napięcia
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowy bloker/wyzwanie | "ostatnio mam problem z X" | ADD |
| Ustąpienie blokera | "już mi to nie przeszkadza" | REMOVE |

### Sekcja 7 — Wskazówki dla AI → Rób ✓
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Korekta zachowania AI | "nie pytaj, od razu rób", "pokaż diff" | ADD/UPDATE |
| Nowa preferencja interakcji | "zapisuj do pliku", "dawaj 3 opcje" | ADD |
| Wzorzec współpracy | "nie czekaj na OK", "callout'uj gdy się mylę" | ADD |

### Sekcja 7 — Wskazówki dla AI → Nie rób ✗
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Odrzucenie stylu/tonu | "za coachingowe", "brzmi jak AI" | ADD |
| Odrzucenie formatu | "bez nagłówków", "nie bold" | ADD |
| Odrzucenie konkretnego słowa | "nie mów X" | ADD (+ voice-of-tone → Unikaj) |

### Sekcja 8 — Mocne strony i motywatory
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowy energetyzator | "uwielbiam jak X", "to mnie kręci" | ADD do Nakręca |
| Nowy drener | "nienawidzę robić X", "to mnie męczy" | ADD do Drenuje |
| Usunięcie triggera | "to już mnie nie męczy" | REMOVE |

---

## content/voice-of-tone.md

### TON I JĘZYK → Słownictwo
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowe słowo do używania | "mów X zamiast Y" | ADD do "Używaj" |
| Nowe słowo do unikania | "nie pisz X", "brzmi jak AI" | ADD do "Unikaj" |

### HOOKI (otwarcia)
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowy typ otwarcia, który zadziałał | powtarzalny pattern w tekstach | ADD nowy typ |

### STRUKTURY POSTÓW
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowa struktura, która zadziałała | powtarzalny format | ADD |
| Zmiana w istniejącej strukturze | "dodaj X do tego formatu" | UPDATE |

### FORMATOWANIE
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowy emoji i jego znaczenie | "🎯 używam do X" | ADD |
| Zmiana konwencji | "teraz → zamiast 🔹" | UPDATE |

### ANTY-WZORCE
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Coś, co nie działa | "to brzmi sztucznie", "za generyczne" | ADD |
| Odrzucony styl | "nie pisz tak więcej" | ADD |

> SKUTECZNOŚĆ WG DANYCH (ranking hooków/struktur wg metryk) — NIE reflect.
> To domena `/x-weekly-analysis`. Reflect zostawia tę sekcję w spokoju.

---

## soul.md

### CHARAKTER
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Korekta bezpośredniości | "za ostro", "więcej luzu", "złagodnij" | UPDATE |
| Korekta pragmatyzmu | "za szybko lecisz", "więcej kontekstu daj" | UPDATE |
| Korekta humoru | "nie hamuj się", "za sucho", "więcej sarkazmu" | UPDATE |

### JAK KOMUNIKUJĘ → czego NIGDY nie robię
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowy anty-wzorzec | "nie zaczynaj od X", "przestań robić Y" | ADD |
| Usunięcie anty-wzorca | "możesz mówić X, to ok" | REMOVE |

### JAK KOMUNIKUJĘ → jak mówię
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowy wzorzec komunikacji | "podoba mi się jak robisz X", "rób tak zawsze" | ADD |
| Zmiana wzorca | "zamiast X rób Y" | UPDATE |

### JAK ROZWIĄZUJĘ PROBLEMY
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Korekta podejścia do opcji | "daj więcej opcji", "za dużo wariantów" | UPDATE |
| Korekta autonomii | "nie pytaj, rób", "pytaj zanim zrobisz" | UPDATE |
| Zmiana obsługi blokad | "szybciej pytaj", "próbuj dłużej sam" | UPDATE |

### JAK PRACUJĘ Z TOBĄ
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Korekta dynamiki | "za bardzo yes-man", "więcej callout'ów" | UPDATE |
| Zmiana adaptacji | "nie zgaduj co chcę", "czytaj między wierszami" | UPDATE |
| Nowy wzorzec współpracy | "od teraz rób X zanim Y" | ADD |

### CZEGO NIE LUBIĘ / CO MNIE NAPĘDZA
| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Nowy trigger negatywny | "to mnie wkurwia w AI", "nienawidzę kiedy X" | ADD do NIE LUBIĘ |
| Nowy energetyzator | "uwielbiam jak X", "to mnie kręci" | ADD do NAPĘDZA |
| Usunięcie triggera | "to już nie irytuje", "przyzwyczaiłem się" | REMOVE |

---

## CLAUDE.md

Źródła sygnałów: raport `audit_claude_md.py` (twarde rozjazdy z dyskiem) + sesje z tygodnia.

| Sygnał | Przykład | Typ |
|--------|----------|-----|
| Ścieżka z CLAUDE.md nie istnieje | folder przeniesiony albo skasowany | UPDATE (nowa ścieżka) / REMOVE |
| Zła liczba skilli / nieistniejący skill | „27 skilli”, a na dysku 31 | UPDATE |
| Nowy folder główny bez opisu | `Kursy/` powstał w tym tygodniu | ADD (jedna linia) |
| Jawna decyzja o strukturze | „od teraz grafiki trzymamy w X” | ADD/UPDATE |
| Nowa konwencja nazw plików | „notatki ze spotkań jako DD.MM.YYYY” | ADD/UPDATE |
| Nowy skill / hook / job, którego nie ma w listingu | „dodałem hook X” | ADD |
| ⚠️ Preferencja osobista | „nie pisz tak długo” | → persona/soul, NIE CLAUDE.md |
| ⚠️ Stan projektu | „live przesunięty na 22.10” | → NOW.md, NIE CLAUDE.md |

Sekcję w CLAUDE.md dobieraj po znaczeniu (struktura katalogów, konwencje, skille, infra). Nowej
sekcji nie zakładaj, jeśli pasująca istnieje.

---

---

## Przykłady

### Przykład 1: Korekta formatu (persona)
```
User: "nie, krócej"  →  [kolejna sesja] "w 2 zdaniach max"
```
→ **persona.md § 3** UPDATE: "Preferuje ultra-zwięzłe odpowiedzi (2-3 zdania)"

### Przykład 2: Nowe słowo do unikania (persona + voice-of-tone)
```
User: "nie pisz 'game-changer', brzmi jak AI"
```
→ **voice-of-tone.md → Słownictwo → Unikaj** ADD: "game-changer"
→ **persona.md § 7 (Nie rób)** ADD: "game-changer (brzmi jak AI)"

### Przykład 3: Nowy wzorzec pracy (persona)
```
User: "zawsze pokazuj diff przed edycją"  →  [kolejna sesja] "diff najpierw"
```
→ **persona.md § 7 (Rób)** ADD: "Przed zapisem — pokaż diff i poczekaj na potwierdzenie"

### Przykład 4: Korekta zachowania AI (soul)
```
User: "za bardzo yes-man jesteś, challenguj mnie"
```
→ **soul.md → JAK PRACUJĘ Z TOBĄ** UPDATE: wzmocnić sekcję o callout'ach

### Przykład 5: Fakt o firmie/pracy — NIE reflect
```
User: "mamy już 200 klientów"
```
→ SKIP. To fakt biznesowy → należy do `biznes.md`, nie do reflecta.

### Przykład 6: Jednorazowe — NIE dodawaj
```
User: "tym razem bez emoji"
```
→ Jednorazowe, nie powtórzone → SKIP

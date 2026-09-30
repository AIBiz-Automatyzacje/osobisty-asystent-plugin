---
name: reflect
description: Analizuje sesje i proponuje kalibrację plików tożsamości — persona.md, soul.md, content/voice-of-tone.md — oraz aktualizację CLAUDE.md projektu (rozjazdy z dyskiem, nowe konwencje). Trzy tryby — interactive (bieżąca sesja, zatwierdzasz od razu), weekly (parser 7-dniowych logów → propozycje z checkboxami do _reflect-pending.md, cron-friendly) i apply (nanosi zaznaczone checkboxami propozycje na pliki docelowe). Użyj `/reflect weekly` dla tygodniowego, `/reflect apply` po zaznaczeniu propozycji.
allowed-tools: ["Read", "Edit", "Write", "Bash", "Glob"]
---

# Reflect

Kalibruje pliki **tożsamości i preferencji** na podstawie sesji: `persona.md`, `soul.md`,
`content/voice-of-tone.md`, a do tego pilnuje, żeby **`CLAUDE.md`** projektu zgadzał się z dyskiem
i z konwencjami ustalonymi w sesjach. Bliźniak `memory-update` (ten sam wzorzec: sesje → sygnały →
pliki w `rules/`), ale z polityką **HUMAN APPROVAL** — zmiana tożsamości/charakteru AI to
wysokie ryzyko driftu, więc reflect NIGDY nie zapisuje plików docelowych bez zgody człowieka.

Podział ról (nie wchodź w cudze):
- `memory-update` → `NOW.md` (bieżący stan, auto).
- `biznes.md` → fakty o firmie/pracy (stabilne, edytuje user).
- **reflect → persona / soul / voice-of-tone** (preferencje i styl, approval).
- **reflect → CLAUDE.md** (struktura projektu, konwencje, gdzie co leży; approval). Pamięci
  Claude Code (`~/.claude/projects/.../memory/`) reflect NIE rusza.

Trzy tryby:
- **interactive** (domyślny) — analizuje BIEŻĄCĄ sesję, pokazuje propozycje od razu, pyta o zgodę.
- **weekly** — parser 7-dniowych logów, zapisuje propozycje z checkboxami do `_reflect-pending.md`
  (bez interakcji, do crona), tworzy zadanie-przypomnienie. NIE edytuje plików docelowych.
- **apply** — czyta `_reflect-pending.md`, nanosi na pliki docelowe TYLKO propozycje zaznaczone
  checkboxem (`- [x]`); niezaznaczone traktuje jako odrzucone. Po przebiegu KASUJE cały plik —
  apply zawsze domyka cykl przeglądu. Selekcja idzie przez checkboxy w pliku, nie przez argument.

Plik pending żyje w `.claude/_reflect-pending.md` — CELOWO poza `.claude/rules/`, bo wszystko
z `rules/` ładuje się do kontekstu każdej sesji i pending zjadałby tokeny do czasu przeglądu.

---

## 1. Wykryj tryb

- `/reflect weekly` → tryb **weekly**.
- `/reflect apply` → tryb **apply**.
- W przeciwnym razie → **interactive**.

---

## Tryb INTERACTIVE (domyślny)

### 2i. Załaduj pliki kontekstowe
```
.claude/rules/persona.md
.claude/rules/soul.md
.claude/rules/content/voice-of-tone.md   (jeśli istnieje)
CLAUDE.md albo .claude/CLAUDE.md          (ten, który istnieje; oba — jeśli są oba)
```
Zapamiętaj strukturę sekcji każdego pliku.

### 3i. Przeczytaj mapping
Otwórz `mapping.md` w tym skillu — mapuje sygnały na sekcje i pliki.

### 4i. Przeskanuj BIEŻĄCĄ sesję
Szukaj sygnałów z mappingu. Dla każdego trafienia:
- **Jawne** (user wprost powiedział) → kandydat
- **Powtórzone** (min. 2x w tej sesji) → kandydat
- **Jednorazowe + ukryte** → SKIP

### 5i. Pokaż propozycje
```
📝 Obserwacje z sesji:

| # | Sygnał | Plik | Sekcja | Typ |
|---|--------|------|--------|-----|
| 1 | [cytat/opis] | persona.md | § 7 (Nie rób) | ADD |

Proponowane zmiany (diff):

**persona.md → § 7 (Nie rób)**
+ [nowy tekst]

Zatwierdzić? (możesz wybrać które)
```
Jeśli brak → "Brak nowych obserwacji. Sesja zgodna z profilem."

### 6i. Po zatwierdzeniu
- Edytuj wskazane pliki (tylko zatwierdzone pozycje)
- Zaktualizuj datę na końcu pliku (`*Ostatnia edycja: DD.MM.YYYY*`)

---

## Tryb WEEKLY (cron-friendly, bez interakcji)

Weekly NIE edytuje plików docelowych — tylko zapisuje propozycje do przeglądu.

### 2w. Setup (cross-platform — Windows-safe)
> ⚠️ Na Windows `command -v python3` zwraca stub ze Sklepu Microsoft (`...WindowsApps/python3`),
> który NIE jest realnym interpreterem. Poniższy blok go pomija. Uruchamiaj z roota vaulta —
> **NIE rób `cd`** (skrypt liczy katalog sesji z workspace; `MEMORY_UPDATE_WORKSPACE` przypina go na sztywno).
> ```bash
> # Interpreter Python — pomiń stub MS Store (WindowsApps)
> PYTHON=""
> for cand in python3 python; do
>   p=$(command -v "$cand" 2>/dev/null) || continue
>   case "$p" in *WindowsApps*) continue;; esac
>   PYTHON="$p"; break
> done
> [ -z "$PYTHON" ] && PYTHON=python
> # Przypnij vault (odporne na cd) + katalog tmp widoczny dla Read (nie /tmp — niewidoczne na Win)
> export MEMORY_UPDATE_WORKSPACE="${CLAUDE_PROJECT_DIR:-$PWD}"
> mkdir -p .claude/tmp
> ```

### 3w. Parsuj 7-dniowe logi
```bash
$PYTHON {baseDir}/scripts/parse_sessions.py --days 7 2>.claude/tmp/reflect-stats.txt > .claude/tmp/reflect-dialog.txt
cat .claude/tmp/reflect-stats.txt
```
Jeśli 0 sesji → pomiń ekstrakcję sygnałów z sesji (5w), ale audyt CLAUDE.md (3w-b) zrób i tak.

### 3w-b. Audyt CLAUDE.md względem dysku
```bash
$PYTHON {baseDir}/scripts/audit_claude_md.py > .claude/tmp/reflect-claude-md.txt
cat .claude/tmp/reflect-claude-md.txt
```
Skrypt podaje twarde rozjazdy: ścieżki z CLAUDE.md, których nie ma na dysku, komendy `/skill` bez
zainstalowanego skilla, złą liczbę skilli i foldery główne nieopisane w CLAUDE.md. Każdy rozjazd
zweryfikuj (np. folder przeniesiony → znajdź nową lokalizację `find`/`ls`) i zamień w propozycję
UPDATE/REMOVE/ADD. Komendę, która jest wbudowana w Claude Code albo pochodzi z pluginu spoza
`~/.claude/plugins`, pomiń. Folder nieopisany: zaproponuj jedną linię opisu tylko wtedy, gdy z jego
zawartości jasno wynika, do czego służy — inaczej wpisz go do „Odrzucone” z pytaniem.

### 4w. Załaduj pliki + mapping
Jak w 2i/3i: persona, soul, content/voice-of-tone, CLAUDE.md, `mapping.md`.

### 5w. Ekstrakcja sygnałów (mocniejszy filtr)
Przeskanuj dialog z 7 dni. Filtr **ostrzejszy** niż interactive:
- Dodawaj tylko sygnały **jawne** LUB **powtórzone min. 2x w różnych sesjach** tygodnia.
- Jednorazowa intensywna sesja ≠ wzorzec → SKIP.
- `soul.md` = **najwyższy próg**: tylko gdy user JAWNIE prosił o zmianę charakteru (nie inference).
- Pomiń stabilne fakty o firmie/pracy (→ biznes.md) i bieżące projekty (→ NOW.md).
- **CLAUDE.md:** tylko trwałe ustalenia o projekcie — gdzie co leży, konwencje nazw, nowy skill
  lub infrastruktura, zmieniony sposób pracy z plikami. Próg: jawna decyzja usera („od teraz
  zapisujemy X w Y”) albo to samo ustalenie w ≥2 sesjach. Preferencje osobiste → persona/soul,
  nie CLAUDE.md. Szczegóły w `mapping.md` → sekcja CLAUDE.md.

### 6w. Zapisz propozycje do `_reflect-pending.md` (NIE edytuj plików!)
Zapisz `.claude/_reflect-pending.md` (root `.claude/`, NIE `rules/` — patrz nota na górze)
w formacie niżej. **Każda propozycja MUSI mieć
checkbox `- [ ] ✅ Zatwierdź tę zmianę`** bezpośrednio pod jej blokiem diff — to przez ten
checkbox user wybiera, co naniesie tryb `apply`. Jeśli zero sygnałów — NIE twórz pliku
(i nie twórz zadania w 7w). Sekcje pomocnicze (np. „Odrzucone") dawaj jako `###` (H3), nie `##`,
żeby nie liczyły się jako propozycje.

### 7w. Utwórz zadanie-przypomnienie
Jeśli powstały propozycje — wywołaj skill `utworz-zadanie`:
> tytuł: `🧠 Przejrzyj N propozycji reflect (persona/soul/voice-of-tone/CLAUDE.md)`
> termin: dziś, priorytet: normalny (bez linku — Obsidian nie pokazuje folderu `.claude/`)
Dzięki temu pamiętasz wrócić — zadanie ląduje w `Dashboard.md` (przy `/daily` je zobaczysz).
Hook `SessionStart` (`reflect-pending-notify.js`) dodatkowo zasygnalizuje istnienie
`_reflect-pending.md` przy starcie sesji.

### 8w. Podsumuj
Krótko: ile propozycji, do których plików, gdzie czekają. Przypomnij userowi flow:
zaznacz checkboxy przy zmianach, które chcesz → odpal `/reflect apply`.

---

## Tryb APPLY (nanosi zaznaczone propozycje)

Materializuje decyzję usera: nanosi na pliki docelowe TYLKO propozycje, które user zaznaczył
checkboxem `- [x]` w `_reflect-pending.md`. Niezaznaczone = odrzucone — apply kończy się
skasowaniem całego pliku, niezależnie ile było zaznaczonych.

### 2a. Wczytaj pending
Przeczytaj `.claude/_reflect-pending.md`. Starsza wersja skilla zapisywała plik w
`.claude/rules/_reflect-pending.md` — jeśli leży tam, czytaj go stamtąd (i skasuj w 6a z tej
lokalizacji). Jeśli nie ma go w żadnym miejscu →
"Brak propozycji do naniesienia (`_reflect-pending.md` nie istnieje). Odpal `/reflect weekly`." i zakończ.

### 3a. Sparsuj propozycje + stan checkboxów
Każda propozycja to sekcja `## <plik> → <sekcja>` z blokiem ```diff``` i checkboxem
`- [ ]`/`- [x]` pod spodem. Zbierz:
- **zaznaczone** (`- [x]`) → do naniesienia,
- **niezaznaczone** (`- [ ]`) → odrzucone (wylistujesz je w podsumowaniu, plik i tak znika).

Jeśli zero zaznaczonych → "Nic nie zaznaczone w `_reflect-pending.md` — zaznacz checkboxy
przy zmianach, które chcesz nanieść, i odpal ponownie." i zakończ (nic nie ruszaj).

### 4a. Załaduj pliki docelowe
Przeczytaj pliki, których dotyczą zaznaczone propozycje (`persona.md` / `soul.md` /
`content/voice-of-tone.md` / `CLAUDE.md`). Zapamiętaj strukturę sekcji.

### 5a. Nanieś zaznaczone (pokaż diff PRZED zapisem)
Dla każdej zaznaczonej propozycji:
- ADD → dodaj linię `+` do wskazanej sekcji (na końcu listy sekcji).
- UPDATE → zamień linię `-` na `+` (Edit z dokładnym dopasowaniem starego fragmentu).
- Zachowaj idiom pliku (wcięcia, myślniki, styl sąsiednich linii).
Pokaż userowi finalny diff każdej zmiany. Po naniesieniu wszystkich — zaktualizuj
`*Ostatnia edycja: DD.MM.YYYY*` (lub `*Ostatnia aktualizacja:*`) na końcu każdego ruszonego pliku.

### 6a. Skasuj pending (zawsze)
Apply domyka cały cykl przeglądu — **skasuj `_reflect-pending.md` w całości**, także gdy
zostały niezaznaczone propozycje (user je widział i nie zaznaczył = odrzucił; jeśli sygnał
jest realny, kolejny `/reflect weekly` i tak go wykryje ponownie). Potem domknij zadanie-przypomnienie:
w `Zadania/Dashboard.md` (u starszych instalacji: `to_do.md`) zmień `- [ ]` na `- [x]` w linii „🧠 Przejrzyj … propozycji reflect”
(archiwizację zrobi `/daily`).

### 7a. Podsumuj
Co naniesione (które pliki/sekcje), co odrzucone (niezaznaczone — wylistuj tytuły, żeby nic
nie zginęło po cichu), potwierdzenie skasowania pliku i domknięcia zadania.

---

## Format `_reflect-pending.md`

```markdown
# Reflect — propozycje do przeglądu

*Wygenerowane: YYYY-MM-DD | Zakres: 7 dni | Sesje: N*

> Zaznacz checkbox `- [x]` przy zmianach, które chcesz nanieść, potem odpal `/reflect apply`.
> Niezaznaczone = odrzucone — apply nanosi zaznaczone i kasuje cały plik.

## persona.md → § 7 (Nie rób)
**Typ:** ADD · **Powód:** 2x w sesjach (12.06, 14.06)
```diff
+ "game-changer" — brzmi jak AI (user: "nie pisz game-changer")
```
- [ ] ✅ Zatwierdź tę zmianę

## soul.md → JAK PRACUJĘ Z TOBĄ
**Typ:** UPDATE · **Powód:** jawna prośba (user: "za bardzo yes-man, challenguj mnie")
```diff
- [stary fragment]
+ [propozycja]
```
- [ ] ✅ Zatwierdź tę zmianę

### Odrzucone w tym przebiegu (świadomie)
- [opis czemu pominięte] — H3, nie liczy się jako propozycja
```

---

## Zasady

- **interactive:** human approval inline — pokaż diff, czekaj na zgodę.
- **weekly:** NIGDY nie edytuj `persona/soul/voice-of-tone/CLAUDE.md` — zapisuj WYŁĄCZNIE do `_reflect-pending.md`, każda propozycja z checkboxem.
- **apply:** nanoś TYLKO zaznaczone (`- [x]`); pokaż diff PRZED zapisem; na koniec ZAWSZE skasuj cały plik pending (niezaznaczone = odrzucone).
- **Pending ZAWSZE w `.claude/_reflect-pending.md`** — nigdy w `rules/` (auto-load do kontekstu).
- Tylko sygnały **jawne** lub **powtórzone ≥2x**. Jednorazowe → SKIP.
- `soul.md` = najwyższy próg (zmiana charakteru tylko na wyraźną prośbę usera).
- **NIE rusz**: NOW.md (memory-update), biznes.md (fakty o firmie/pracy), pamięć Claude Code (`~/.claude/projects/.../memory/`).
- **CLAUDE.md** ma być krótki: propozycja ADD zastępuje albo skraca istniejącą linię, gdy się da; nie dopisuj historii zmian ani dat.
- **NIE duplikuj** informacji już obecnych w plikach.
- Pokaż diff PRZED każdą edycją.
- Cleanup: po weekly usuń pliki tymczasowe (`rm -f .claude/tmp/reflect-*.txt`).
- Testy skryptu audytu: `cd {baseDir}/scripts && python3 test_audit_claude_md.py`.

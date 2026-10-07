---
name: memory-update
description: Parsuje logi sesji Claude Code, wyciąga kluczowe sygnały (projekty, decyzje, priorytety, blokery) i aktualizuje NOW.md z bieżącym kontekstem pracy. Dwa tryby — daily (domyślny, przyrostowy) i weekly (konsolidacja tygodnia, wzorce cross-session, agresywny cleanup). Użyj `/memory-update weekly` dla trybu tygodniowego.
allowed-tools: ["Read", "Edit", "Write", "Bash", "Glob", "Grep"]
---

# Memory Update

Skanuje logi sesji Claude Code, wyciąga sygnały i aktualizuje `.claude/rules/NOW.md` — plik ładowany automatycznie do każdej sesji.

Dwa tryby pracy:
- **daily** (domyślny) — przyrostowa ekstrakcja od ostatniego update'u
- **weekly** — konsolidacja tygodnia, wzorce cross-session, agresywny cleanup. Zastępuje daily na ten dzień.

---

## Workflow

> **Setup (cross-platform — Windows-safe):** Przed uruchomieniem skryptów. ⚠️ Na Windows
> `command -v python3` zwraca stub ze Sklepu Microsoft (`...WindowsApps/python3`), nie realny
> interpreter — blok go pomija. Uruchamiaj z roota vaulta, **NIE rób `cd`** (skrypt liczy katalog
> sesji z workspace; `MEMORY_UPDATE_WORKSPACE` przypina go na sztywno).
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
> Używaj `$PYTHON` w komendach `parse_sessions.py` poniżej.

### 1. Wykryj tryb

Sprawdź argumenty. Jeśli user napisał `/memory-update weekly` → tryb **weekly**. W przeciwnym razie → tryb **daily**.

---

## Tryb DAILY

### 2d. Ustal zakres czasowy

Przeczytaj `.claude/rules/NOW.md` — weź timestamp z `*Ostatni update: YYYY-MM-DD HH:MM*`.

- **Jeśli jest timestamp:** parsuj sesje `--since "{timestamp}"`
- **Jeśli brak lub pierwszy raz:** parsuj `--days 3` (catchup mode)

### 3d. Parsuj logi sesji

```bash
$PYTHON {baseDir}/scripts/parse_sessions.py --since "{timestamp}" 2>.claude/tmp/mu-stats.txt > .claude/tmp/mu-dialog.txt
```

Lub catchup:
```bash
$PYTHON {baseDir}/scripts/parse_sessions.py --days 3 2>.claude/tmp/mu-stats.txt > .claude/tmp/mu-dialog.txt
```

Sprawdź statystyki:
```bash
cat .claude/tmp/mu-stats.txt
```

Jeśli 0 sesji → powiedz "Brak nowych sesji do przeanalizowania" i zakończ.

### 4d. Ekstrakcja sygnałów

Wczytaj prompt ekstrakcji:
```
{baseDir}/prompts/extract.md
```

Wczytaj dialog z parsera:
```bash
cat .claude/tmp/mu-dialog.txt
```

Przeanalizuj dialog zgodnie z promptem ekstrakcji. Wygeneruj listę sygnałów JSON.

### 5d. Merge do NOW.md

Wczytaj:
- Aktualny `.claude/rules/NOW.md`
- Prompt merge: `{baseDir}/prompts/merge.md`
- Sygnały z kroku 4d

Wygeneruj zaktualizowany NOW.md zgodnie z zasadami merge. Zaktualizuj timestamp na bieżący.

### 6d. Zapisz i podsumuj

Zapisz zaktualizowany plik do `.claude/rules/NOW.md`. Pokaż podsumowanie (format niżej).

---

## Tryb WEEKLY

Weekly zastępuje daily — nie rób dwóch przebiegów. Weekly widzi dzisiejsze logi w 7-dniowym oknie.

### 2w. Zbierz dwa źródła danych

**Źródło 1 — Git diff NOW.md (historia zmian z tygodnia):**

```bash
git log --since="7 days ago" --oneline -- .claude/rules/NOW.md
git diff "$(git log --since='7 days ago' --format='%H' -- .claude/rules/NOW.md | tail -1)"..HEAD -- .claude/rules/NOW.md
```

Jeśli brak commitów z ostatnich 7 dni albo vault nie jest repozytorium gita (brak `.git` — typowe u nowych osób), pomiń to źródło bez komunikatu o błędzie.

**Źródło 2 — Surowe logi sesji z 7 dni:**

```bash
$PYTHON {baseDir}/scripts/parse_sessions.py --days 7 2>.claude/tmp/mu-stats.txt > .claude/tmp/mu-dialog.txt
```

Sprawdź statystyki:
```bash
cat .claude/tmp/mu-stats.txt
```

Jeśli 0 sesji → powiedz "Brak sesji z ostatniego tygodnia" i zakończ.

### 3w. Ekstrakcja sygnałów tygodniowych

Wczytaj prompt ekstrakcji weekly:
```
{baseDir}/prompts/weekly-extract.md
```

Przekaż do analizy:
- Git diff NOW.md (źródło 1)
- Dialog z parsera (źródło 2)
- Aktualny NOW.md

W weekly szukaj wzorców między sesjami — sygnał powtarzający się w kilku sesjach waży więcej niż jednorazowy.

### 4w. Merge tygodniowy do NOW.md

Wczytaj:
- Aktualny `.claude/rules/NOW.md`
- Prompt merge weekly: `{baseDir}/prompts/weekly-merge.md`
- Sygnały z kroku 3w

Wygeneruj zaktualizowany NOW.md. Weekly PRZEPISUJE sekcje (nie tylko dopisuje). Zaktualizuj timestamp na bieżący.

### 5w. Zapisz i podsumuj

Zapisz zaktualizowany plik do `.claude/rules/NOW.md`. Pokaż podsumowanie (format niżej).

---

## Format podsumowania

### Daily:
```
🧠 Memory Update | {data}

Sesje: {N} | Wiadomości usera: {N}

DODANE:
+ [kategoria] opis

ZAKTUALIZOWANE:
~ [kategoria] opis

USUNIĘTE:
- [kategoria] opis (powód)
```

### Weekly:
```
🧠 Memory Update WEEKLY | {data} | Tydzień {nr tygodnia}

Sesje: {N} | Wiadomości usera: {N} | Zakres: {data_od} — {data_do}

SKONSOLIDOWANE:
~ [projekt] stare wpisy → nowy zbiorczy opis

NOWE WZORCE:
+ [opis wzorca cross-session]

STALLED:
⏸ [projekt] — brak aktywności w logach

WYCZYSZCZONE:
- [opis] (powód: jednorazowy event / stale / zakończone)

NA TAPECIE (zaktualizowane):
1. ...
```

## Zasady ogólne

- NOW.md max **8 000 znaków** (`wc -m`), liczba linii bez znaczenia
- **NIE duplikuj** info z innych plików w `.claude/rules/` ładowanych do kontekstu
- **NIE interpretuj emocji** usera — tylko fakty i explicite statements
- Confidence **LOW → odrzuć** (nie zapisuj)
- Full auto — **nie pytaj o zatwierdzenie**, po prostu zapisz
- Cleanup: po zapisie usuń pliki tymczasowe (`rm -f .claude/tmp/mu-*.txt`)

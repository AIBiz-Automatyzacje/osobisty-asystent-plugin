---
name: koniec-sesji
description: Domyka sesję pracy nad projektem — utrwala wiedzę z rozmowy w `_KONTEKST.md` projektu (priorytety następnej sesji na górze, aktualny stan, decyzje) i wrzuca do schowka prompt wznowieniowy. Nowy projekt bez folderu → tworzy go wg konwencji. Używaj, gdy user kończy pracę nad projektem („koniec sesji”, „domknij projekt”, „zapisz kontekst”, „podsumuj sesję”) i chce, żeby następna sesja weszła w temat od razu.
argument-hint: "[projekt] | [na czym skupi się następna sesja]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
---

# Koniec sesji

Utrwalasz wiedzę z bieżącej rozmowy w **jednym pliku projektu: `_KONTEKST.md`**, żeby następna sesja weszła w temat z pełnym kontekstem, zamiast odtwarzać go od zera. Na koniec dajesz userowi prompt wznowieniowy w schowku.

## Czym to się różni od pokrewnych skilli

| Skill | Co aktualizuje | Zakres |
|-------|----------------|--------|
| `/memory-update` | `NOW.md` | globalny stan wszystkich projektów |
| `/reflect` | persona/soul/voice | tożsamość AI, styl |
| **`/koniec-sesji`** | **`_KONTEKST.md` projektu** | **kontekst jednego projektu** |

NOW.md tego skilla nie dotyczy. Na końcu proponujesz `/memory-update`.

## Zasady zapisu

- Pisz od razu, bez draftu w czacie. Pokaż podsumowanie zmian po zapisie.
- Jeden plik na projekt: `_KONTEKST.md`. Nie zakładasz plików obok (handoffów, notatek sesji). Rozsypane notatki projektu scalasz do `_KONTEKST.md`, a resztę kasujesz dopiero za zgodą usera.
- Plik jest chudy: aktualny stan i otwarte rzeczy. Historię wycofanych decyzji i informacje spoza zakresu projektu kasujesz.
- Język usera, prosto, bez żargonu w treści (nazwy własne i akronimy zostają).
- Bez sekretów (tokeny, hasła, klucze API, dane osobowe): piszesz „token w `.env`”, nie sam token.
- Pliki `.md` zapisuj narzędziami Write/Edit, nie przez Bash.

## Workflow

### 1. Ustal datę i projekt

```bash
date +%F
```

Projekt wykryj w tej kolejności: argument skilla, pliki `Zadania/projekty/<slug>/...` dotknięte w tej sesji, temat rozmowy zmapowany na istniejący folder w `Zadania/projekty/`. Jeśli dalej nie wiesz, zadaj jedno pytanie z listą kandydatów.

Slug = kebab-case (np. `oferta-grupy-fb`, `nowy-kurs`). Domyślna lokalizacja: `Zadania/projekty/<slug>/`.

### 2. Znajdź plik kontekstu

| Stan | Akcja |
|------|-------|
| Jest `_KONTEKST.md` | Aktualizuj go. |
| Jest stary plik (`kontekst.md`, `STATUS.md`, `sesje/*-handoff.md`) bez `_KONTEKST.md` | Utwórz `_KONTEKST.md`, przenieś do niego to, co dalej aktualne, i zaproponuj userowi skasowanie starych plików. |
| Folder istnieje, brak pliku kontekstu | Utwórz `_KONTEKST.md` z szablonu. |
| Folder nie istnieje | Utwórz `Zadania/projekty/<slug>/_KONTEKST.md` z szablonu. |

`README.md`, który opisuje setup projektu, zostaje jako README.

### 3. Zaktualizuj `_KONTEKST.md`

- **Na górze: „Priorytety następnej sesji”**, a w nich pierwszy krok, dokładnie co zrobić jako pierwsze, plus 2-4 kolejne.
- **Stan obecny**: gdzie jesteśmy po tej sesji.
- **Decyzje i ustalenia**: co i dlaczego. Edytuj istniejące sekcje, nie dopisuj duplikatów.
- **Otwarte**: taski, decyzje (i od kogo zależą), czego nie zdążyliśmy dokończyć.
- Parametry, ścieżki, pułapki: tylko te, które dalej obowiązują.

Follow-upy projektu idą do sekcji „Otwarte” w `_KONTEKST.md`, nie na Dashboard.

### 4. Pokaż zmiany

W czacie krótko: co zmieniłeś w `_KONTEKST.md` i co z niego wyciąłeś, plus pełna ścieżka do pliku.

### 5. Prompt wznowieniowy do schowka

Napisz krótki prompt do wklejenia na start następnej sesji: projekt, ścieżka do `_KONTEKST.md`, pierwszy krok. Wrzuć go do schowka komendą zależną od systemu (tekst z pliku tymczasowego w `.claude/tmp/`):

| System | Kopiowanie | Sprawdzenie |
|--------|-----------|-------------|
| macOS | `pbcopy < plik` | `pbpaste` |
| Windows (Git Bash) | `clip < plik` | `powershell -NoProfile -Command Get-Clipboard` |
| Linux | `xclip -selection clipboard < plik` | `xclip -selection clipboard -o` |

Sprawdź zawartość schowka, zanim napiszesz, że prompt jest w schowku. Kopiowanie się nie udało (np. brak `xclip`, piaskownica) → powiedz to wprost i pokaż prompt w czacie do ręcznego skopiowania.

### 6. Domknięcie globalne

Zaproponuj jednym zdaniem (nie odpalaj sam): „Odpalić `/memory-update`, żeby NOW.md złapał te zmiany?”. Jeśli w sesji padły obserwacje o sposobie pracy albo stylu, wspomnij o `/reflect`.

## Szablon `_KONTEKST.md`

```markdown
# <Nazwa projektu> — kontekst

> Stan na: <data>. Czytaj przed każdą sesją.

## ▶️ Priorytety następnej sesji

1. <pierwszy krok — dokładnie co zrobić>
2. <kolejny>

## Stan obecny

<Gdzie jesteśmy. Co działa, co nie.>

## Decyzje i ustalenia

- **<decyzja>** — <dlaczego>.

## Parametry, ścieżki, pułapki

- <ID, ścieżki, adresy, rzeczy, które już nas ugryzły — bez sekretów>

## Otwarte

- <taski, decyzje do podjęcia i od kogo zależą, luki do uzupełnienia>

## Cel projektu

<1-3 zdania: po co to robimy, jak wygląda sukces.>
```

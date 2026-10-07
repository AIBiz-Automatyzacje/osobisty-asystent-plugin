---
name: utworz-zadanie
description: Dodaje zadanie do Dashboardu w Obsidianie (jedna linia — nazwa, priorytet, termin, opcjonalnie link do materiału). Użyj gdy user prosi o dodanie/utworzenie zadania, zapisanie czegoś do zrobienia, lub wspomina o task/todo.
argument-hint: "[nazwa] | [priorytet] | [termin] | [link]"
allowed-tools: ["Read", "Edit", "Write", "Bash", "Glob"]
---

# Utwórz Zadanie

Zadanie = **jedna linia w `Zadania/Dashboard.md`**. Bez osobnego pliku, projektu i podzadań.
Format linii i sekcji jest wspólny z `/daily` — patrz [config.md](config.md).

## 1. Parsuj argumenty

**Format:** `nazwa | priorytet | termin | link` — delimiter `|` (przecinki bywają w nazwach).

Przykłady:
- `Oferta dla stolarni` → sama nazwa
- `Zadzwoń do hurtowni | pilne | jutro`
- `Przejrzyj raport narzędzi | normalne | dzisiaj | Zasoby/Raporty/2026-09-28-narzedzia.md`

**Braki uzupełnij bez pytania:** priorytet → `normalne`, termin → brak, link → brak.
**Wyciągaj z kontekstu**, jeśli user wspomniał: „pilne/asap” → pilne, „ważne” → wazne,
„na jutro / do piątku / 15.01” → termin (tabela w config.md). Dzisiejszą datę bierz z `date +%Y-%m-%d`.

## 2. Link do materiału (opcjonalny)

- Dostałeś ścieżkę do istniejącego pliku (raport, notatka, wpis) → wstaw ją jako link 📎.
- User podał szczegóły, które trzeba zachować (kontakt, dane do faktury, kroki) i nie ma na nie
  pliku → utwórz notatkę `Zadania/notatki/[nazwa-kebab-case].md` (nagłówek `# Nazwa` + treść
  od usera, nic więcej) i podlinkuj ją 📎. Bez szczegółów — **żadnego pliku**.

## 3. Dopisz linię do Dashboardu

1. Przeczytaj `Zadania/Dashboard.md`.
2. Wybierz sekcję wg terminu (tabela w config.md). Nagłówki dopasowuj **po tekście, ignorując emoji** —
   sekcja „Dzisiaj” ma w nagłówku zmienną datę (`## Dzisiaj, piątek 17.04`), dzień z okna tygodnia to
   `## Wtorek 29.09` (dopasuj po dacie). Stary Dashboard (sprzed `/daily`) może mieć jeszcze
   `## 📅 Ten tydzień` — wtedy wstaw tam. Brak sekcji w pliku → dopisz ją w kolejności z config.md.
   Pod nagłówkiem dnia stoi `_brak zadań_` → **zastąp** tę linię nowym zadaniem.
3. Sformatuj linię (config.md → „Format linii”) i wstaw ją w sekcji wg sortowania: termin rosnąco,
   potem priorytet. Wpisy cykliczne 🔁 zostaw w spokoju.
4. Zaktualizuj `ostatnia_aktualizacja` we frontmatterze (`YYYY-MM-DD HH:MM`).
5. Zapisuj **narzędziem Edit** (jedna zmiana w pliku), nie przez Bash — niektóre hooki blokują zapis `.md` przez Bash.

**Termin w przeszłości** → wstaw do „Zaległe” i ostrzeż: „⚠️ Termin DD.MM już minął.” (nie blokuj).
**Ta sama nazwa już jest w Dashboardzie** (niewykonana) → nie dubluj, powiedz o tym.

## 4. Potwierdzenie

Jedna linia: `✅ Dodane: [nazwa] — [emoji] · [DD.MM lub „bez terminu”] → sekcja [nazwa sekcji]`
(+ ścieżka notatki, jeśli powstała).

## Constraints

- NIE twórz zadania bez nazwy
- NIE twórz plików zadań w `Zadania/w_trakcie/` — ten folder nie jest już używany
- Notatka w `Zadania/notatki/` tylko przy realnych szczegółach od usera
- Po odhaczeniu `[x]` archiwizację robi `/daily`, nie ten skill

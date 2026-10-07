---
name: daily
description: Codzienna aktualizacja Dashboardu - archiwizacja odhaczonych, zadania cykliczne, przesunięcie zadań między sekcjami wg terminu, krótki raport
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Bash", "Edit", "Glob"]
---

# Daily — Codzienna aktualizacja Dashboardu

Zadania żyją jako **linie w `Zadania/Dashboard.md`** (bez osobnych plików). Daily porządkuje tę listę:
archiwizuje odhaczone, dorzuca cykliczne i przestawia zadania do sekcji wg terminu. Nie planuje dnia.

**Konfiguracja:** [config.md](config.md) — ścieżki, format linii, sekcje, emoji, sortowanie.
**Szablon raportu:** [report-template.md](report-template.md).

---

## SEKCJA 1: Wczytaj Dashboard i rozbierz linie

1. Pobierz datę i dzień tygodnia **z systemu** (nie licz sam):
   ```bash
   date +%Y-%m-%d; date +%A; date +%H:%M
   ```
   Mapowanie: Monday→poniedziałek, Tuesday→wtorek, Wednesday→środa, Thursday→czwartek, Friday→piątek, Saturday→sobota, Sunday→niedziela
2. Przeczytaj `Zadania/Dashboard.md`. Weź WSZYSTKIE linie zadań `- [ ] …` i `- [x] …` spod nagłówków
   `##` (sekcje zadań, także starych z emoji). Pomiń frontmatter, banner między markerami
   `%% inbox:banner:* %%`, nagłówki i znaczniki pustego dnia `_brak zadań_`.
3. Każdą linię rozbierz wg „Parsowanie linii” w config.md na: stan (`[ ]`/`[x]`), cykliczne (🔁) tak/nie,
   nazwa (z ewentualnym linkiem 📎 — zachowaj go bez zmian), priorytet, termin.
4. **Linie dopisane ręcznie** bez emoji albo bez daty są pełnoprawnymi zadaniami: brak emoji = 🟢,
   brak daty = bez terminu. Nie odrzucaj ich.
5. Linie nieczytelne (np. zwykły tekst bez checkboxa) zostaw na swoim miejscu, na końcu sekcji
   „Bez terminu”, i dodaj ostrzeżenie do raportu.

---

## SEKCJA 2: Archiwizacja odhaczonych (AUTO)

**ŹRÓDŁO PRAWDY:** `[x]` w Dashboardzie = zadanie wykonane. Bez pytania o potwierdzenie.

1. Każdą odhaczoną linię **nie-cykliczną** dopisz na końcu `Zadania/zrobione/YYYY-MM.md` (miesiąc dzisiejszej
   daty; brak pliku → utwórz z nagłówkiem `# Zrobione — MM.YYYY`) w formacie:
   `- [x] Nazwa [link 📎 jeśli był] — [emoji] · termin DD.MM · zrobione DD.MM` (bez terminu → pomiń „termin DD.MM”).
   „Zrobione” = dzisiejsza data (moment archiwizacji).
2. Odhaczone cykliczne `- [x] 🔁` NIE trafiają do archiwum — po prostu znikają.
3. Usuń odhaczone linie z listy zadań do dashboardu.
4. **Zgodność wstecz:** linia ze starym linkiem `[[w_trakcie/plik|Tytuł]]` → archiwizuj ją tak samo; jeśli
   plik `Zadania/w_trakcie/plik.md` istnieje, ustaw w nim `status: zrobione` i przenieś go do
   `Zadania/zrobione/YYYY-MM/` (utwórz folder). Nowych plików w `w_trakcie/` nie twórz.

---

## SEKCJA 3: Zadania cykliczne (AUTO)

1. Przeczytaj `Zadania/cykliczne/recurring.md`. Sparsuj tabelę: **Nazwa**, **Harmonogram**, **Priorytet**, **Projekt**.
2. Harmonogram pasuje do **dzisiejszej daty**, gdy:
   - `co [dzień tygodnia]` → dziś jest ten dzień,
   - `co dzień` → zawsze,
   - `[N]. dnia miesiąca` → dziś jest N. dzień miesiąca,
   - `ostatni dzień miesiąca` → jutro jest 1. dzień miesiąca.

   Harmonogram bywa wpisany ręcznie, swoimi słowami — interpretuj go po znaczeniu, nie po literze:
   „W każdy poniedziałek” = `co poniedziałek`, „1-ego dnia każdego miesiąca” / „Każdego 20 dnia miesiąca”
   = `N. dnia miesiąca`, „Co 2 środę każdego miesiąca” = druga środa miesiąca. Priorytet „ważne” = `wazne`.
   Harmonogram, którego nie da się jednoznacznie odczytać → pomiń i wypisz w raporcie jako ostrzeżenie.
3. Pasujące → lista `cykliczne_dzis` (bez duplikatu, jeśli taka linia 🔁 już jest w Dashboardzie niewykonana).
4. **Carry-over:** niewykonane `- [ ] 🔁` z Dashboardu dopasuj po nazwie do `recurring.md`:
   - `co dzień` → pomiń (wstrzyknie się dziś na świeżo),
   - już w `cykliczne_dzis` → pomiń,
   - nazwy nie ma w `recurring.md` → pomiń (usunięte z cyklicznych),
   - reszta → `cykliczne_zalegle`.

---

## SEKCJA 4: Regeneracja Dashboard.md

1. **Przypisz sekcje** wg „Sekcje Dashboardu” w config.md (to przesuwa zadania wraz z upływem czasu):
   - `## Zaległe` — termin < dziś + `cykliczne_zalegle` (ZAWSZE na górze)
   - `## Dzisiaj, [dzień_tygodnia] DD.MM` — termin = dziś + `cykliczne_dzis`
   - `## [Dzień_tygodnia] DD.MM` — po jednym na każdy dzień z **okna tygodnia** (config.md); pusty dzień → `_brak zadań_`
   - `## Później` — termin poza oknem tygodnia (także sobota i niedziela)
   - `## Bez terminu` — brak terminu
   Daty dni z okna policz **z systemu**, nie w pamięci, np. `date -v+1d +'%A %d.%m'` (macOS) /
   `date -d '+1 day' +'%A %d.%m'` (Linux) — dla każdego dnia osobno. Rok terminu ustal wg „Rok terminu” w config.md.
2. **Sortuj** w sekcji: termin rosnąco → priorytet (pilne → wazne → normalne). Cykliczne na końcu sekcji.
3. **Formatuj** każdą linię od nowa wg „Format linii” w config.md (wszystkie jako `- [ ]`). Nazwę i link 📎
   przepisz dokładnie tak, jak były — nie poprawiaj treści usera.
4. **Skomponuj plik** i zapisz go **jedną operacją Write** (sync-job Team OS czyta plik co minutę):

   a) Frontmatter:
      ```yaml
      ---
      ostatnia_aktualizacja: YYYY-MM-DD HH:MM
      cssclasses: dashboard-todo
      ---
      ```
   b) Markery bannera Team OS — ZAWSZE obecne. Treść zależy od tego, czy działa Skrzynka:
      - istnieje `Zadania/Skrzynka.md` → **przepisz bez zmian to, co jest dziś między markerami**
        (sync Team OS aktualizuje to co minutę); gdy między markerami jest pusto, wstaw placeholder:
        ```
        📥 **Inbox:** 0 nowych · [[Skrzynka|otwórz]]   📤 **Delegowane:** 0 w toku
        ```
      - brak `Zadania/Skrzynka.md` → same markery, bez treści (w Obsidianie niewidoczne).
      ```
      %% inbox:banner:start %%
      [treść wg reguły wyżej]
      %% inbox:banner:end %%
      ```
   c) `# Dashboard` → `## Zaległe` → `## Dzisiaj, …` → `## [Dzień] DD.MM` (każdy dzień z okna) → `## Później` → `## Bez terminu`
      (pusty dzień z okna: nagłówek + `_brak zadań_`; pozostałe puste sekcje: sam nagłówek).

   **Markery są obowiązkowe** — sync Team OS pisze między nimi; bez nich banner zniknie także wtedy,
   gdy Skrzynka zostanie podłączona później. `cssclasses: dashboard-todo` podpina snippet z `/onboard`.

---

## SEKCJA 5: Raport

Krótki raport wg [report-template.md](report-template.md). Bez rekomendacji i bez pytań.

---

## Constraints

- Źródłem zadań jest wyłącznie Dashboard — NIE skanuj `Zadania/w_trakcie/` i nie twórz tam plików
- Nie gub linii: każda niewykonana linia z wejścia musi trafić do jakiejś sekcji (policz przed i po zapisie)
- Pliki `.md` zmieniaj narzędziami Edit/Write, nie przez Bash (`sed -i`, `>`) — niektóre hooki blokują zapis `.md` przez Bash. `mkdir -p`/`mv` przez Bash są OK
- Frontmatter `ostatnia_aktualizacja`: YYYY-MM-DD HH:MM; daty w liniach i raporcie: DD.MM

---

## Przepływ

```
[Start] → 📖 Dashboard (linie) → 📦 [x] → zrobione/YYYY-MM.md → 🔁 cykliczne
        → 📝 regeneracja Dashboard.md (sekcje wg terminu, dni tygodnia osobno) → 📊 raport → [Koniec]
```

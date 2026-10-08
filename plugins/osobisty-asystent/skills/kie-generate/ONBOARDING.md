# Onboarding — kie-generate

Instrukcja dla Claude'a: jak przeprowadzić nowego użytkownika przez konfigurację skilla `kie-generate` na jego systemie (Mac/Windows/Linux).

**Wywołanie:** user mówi "skonfiguruj kie-generate" / "onboarding kie-generate" / "uruchom kie-generate setup" / "zrób mi setup kie-generate".

## Zasady działania

1. **Idempotentność** — za każdym uruchomieniem sprawdzaj stan na żywo. Jak krok już zrobiony → ✅ skip i komunikat "już skonfigurowane". Nic nie pamiętamy między sesjami.
2. **Bez realnych call testowych** — nie palimy kasy na weryfikację kluczy. Pytamy "dodałeś?" i sprawdzamy tylko, że klucz jest w `.env`.
3. **Pliki skilla są tylko do odczytu** — nie edytujesz `SKILL.md` ani skryptów (w pluginie aktualizacja i tak by je nadpisała). Ustawienia usera idą do `.env`, brand do `.claude/kie-brand.md` w workspace.
4. **Komunikacja krótka, konkretna** — każdy krok: co sprawdzam → wynik → co dalej. Bez wstępów.

## Kroki

### 1. Python 3

**Check** (pomija atrapę `python3` ze Sklepu Microsoft na Windowsie):
```bash
PYTHON=""
for cand in python3 python; do
  p=$(command -v "$cand" 2>/dev/null) || continue
  case "$p" in *WindowsApps*) continue;; esac
  PYTHON="$p"; break
done
[ -n "$PYTHON" ] && "$PYTHON" --version || echo "BRAK"
```

- Jeśli wersja ≥ 3.8 → ✅ "Python OK: {wersja}"
- Jeśli `BRAK` lub starsza → poinformuj usera:
  - **Mac:** instalator `.pkg` z python.org (GUI). Jeśli Homebrew już
    istnieje i user woli tę drogę, alternatywnie `brew install python3`;
    nie zakładaj ani nie instaluj Homebrew tylko dla tego skilla
  - **Windows:** pobierz z python.org, zaznacz "Add to PATH" przy instalacji
  - **Linux:** `sudo apt install python3` (Debian/Ubuntu) lub odpowiednik
- Po instalacji user musi **zrestartować terminal**, potem re-run onboardingu

### 2. Biblioteka `requests`

**Check** (z `$PYTHON` z kroku 1):
```bash
"$PYTHON" -c "import requests; print(requests.__version__)"
```

- Jeśli działa → ✅ "requests OK: {wersja}"
- Jeśli `ModuleNotFoundError` → zapytaj usera: "Zainstalować `requests`? [tak/nie]"
  - Jeśli tak → `"$PYTHON" -m pip install requests`
  - Jeśli nie → stop, poinformuj że skill nie zadziała bez tej biblioteki

### 3. Plik `.env` w workspace

**Zasada:** Claude **nie tworzy** i **nie edytuje** pliku `.env`. User sam robi to w swoim edytorze. My tylko sprawdzamy przez `grep`, czy klucze są wypełnione.

**Check:**
```bash
test -f .env && echo "EXISTS" || echo "MISSING"
```

- Jeśli istnieje → ✅ "Plik .env znaleziony"
- Jeśli nie istnieje → **nie twórz pliku samodzielnie**. Poproś usera:

```
Brakuje pliku .env w głównym folderze workspace'u. Utwórz go sam (dowolnym edytorem)
w lokalizacji: {pwd}/.env

Daj znać, jak plik będzie gotowy — wrócę do sprawdzania.
```

Pauza, czekaj na potwierdzenie od usera, potem re-check.

### 4. `KIE_API_KEY`

**Check:** (sprawdza, czy linia istnieje I ma niepustą wartość po `=`)
```bash
grep -qE "^KIE_API_KEY=.+" .env && echo "SET" || echo "MISSING"
```

- Jeśli SET → ✅ "KIE_API_KEY w .env — skip"
- Jeśli MISSING → **najpierw zapytaj:**

```
Czy ktoś w Twojej firmie już korzysta z tego skilla (grafiki przez Kie.ai)?
[tak / nie]
```

  - **tak** → wyświetl:

```
W takim razie klucz już istnieje — poproś administratora o klucz Kie.ai
(firmowy menedżer haseł albo bezpieczny kanał, nie zwykły czat).
Potem otwórz .env w swoim edytorze i dodaj linię (wklej klucz po znaku =):

   KIE_API_KEY=xxxxxxxxxxxx

Zapisz plik. Daj znać, jak skończysz — sprawdzę, czy klucz jest na miejscu.
```

  - **nie** → wyświetl:

```
Aby zdobyć klucz Kie.ai:

1. Wejdź na https://kie.ai → Sign up (email + hasło)
2. Dashboard → API Keys → Create API Key
3. Doładuj konto (np. ~$5 na start; GPT Image 2.5 kosztuje kilka centów za obrazek,
   aktualny cennik jest na https://kie.ai)
4. Otwórz .env w swoim edytorze i dodaj linię (wklej klucz po znaku =):

   KIE_API_KEY=xxxxxxxxxxxx

Zapisz plik. Daj znać, jak skończysz — sprawdzę, czy klucz jest na miejscu.
```

- **Nie wypisuj ani nie zapisuj klucza sam** — user robi to ręcznie w `.env`.
- Po odpowiedzi "gotowe"/"tak" → re-check (`grep` raz jeszcze)
  - Jeśli SET → ✅ przejdź dalej
  - Jeśli nadal MISSING → "Nie widzę klucza. Sprawdź, czy zapisałeś plik i czy linia ma format `KIE_API_KEY=...` (bez spacji, bez cudzysłowów)"
- "nie" → zatrzymaj onboarding, poinformuj, że user może dokończyć później re-runem

### 5. `IMGBB_API_KEY`

Najpierw zapytaj, czy user chce używać `edit`, `compose` albo
`remove-bg`.
Jeśli potrzebuje tylko `generate` i wideo → pomiń cały krok; te tryby nie wymagają ImgBB.

**Check:**
```bash
grep -qE "^IMGBB_API_KEY=.+" .env && echo "SET" || echo "MISSING"
```

- Jeśli SET → ✅ "IMGBB_API_KEY w .env — skip"
- Jeśli MISSING → ta sama logika co w kroku 4: jeśli ktoś w firmie już korzysta ze skilla — klucz od administratora; jeśli nie — **wyświetl userowi:**

```
ImgBB to darmowy hosting do obrazków referencyjnych (dla edit/compose/remove-bg).
Bez karty, 2 minuty setupu.

1. Wejdź na https://imgbb.com → Sign up (email + hasło)
2. Wejdź na https://api.imgbb.com → "Get API key" (przycisk pod opisem)
3. Otwórz .env w swoim edytorze i dodaj linię (wklej klucz po znaku =):

   IMGBB_API_KEY=xxxxxxxxxxxx

Zapisz plik. Daj znać, jak skończysz.
```

- Re-check po "gotowe" (analogicznie do kroku 4). Claude nie edytuje `.env`.

### 6. Brand (opcjonalny)

**Check:** `test -f .claude/kie-brand.md && head -3 .claude/kie-brand.md`

- Plik istnieje → ✅ skip („brand już skonfigurowany, zmienisz go, edytując `.claude/kie-brand.md`”).
- Brak → zapytaj: „Chcesz zapisać swój brand (kolory, styl), żeby grafiki były spójne? [tak/nie]”. **nie** → skip.
- **tak** → pytaj po jednym:
  1. Jak nazywa się Twoja marka / projekt?
  2. Jakie 1–3 kolory są kluczowe? (nazwy albo hex, np. „głęboki zielony #2D5016 + kremowy”)
  3. Jaki styl wizualny Ci pasuje? (minimalistyczny / bogaty w detale, nowoczesny / retro, korporacyjny / luźny / premium)
  4. Do czego głównie używasz grafik? (posty, miniatury YouTube, prezentacje, strona, reklamy)
  5. *(opcjonalnie)* Czego unikać? (np. „żadnych neonowych mózgów”, „bez gradientów”)
- Wygeneruj `.claude/kie-brand.md` z sekcjami: Marka, Kolory, Styl wizualny, Zastosowanie, Czego unikać. **Pokaż draft przed zapisem**, po akceptacji zapisz (to plik usera w workspace, nie plik skilla — tu zapis jest OK).

### 7. Lokalizacja zapisu grafik

Domyślnie skill zapisuje do `Marketing/media/`, jeśli taki folder istnieje w workspace, a w przeciwnym razie do `media/` (zakłada go przy pierwszym zapisie).

- Zapytaj: "Grafiki mają trafiać do {domyślna ścieżka}? [tak/inna]"
- **tak** → ✅ skip
- **inna** → poproś, żeby user sam dopisał do `.env` linię (ścieżka względna od głównego folderu workspace'u):

```
KIE_OUTPUT_DIR=grafiki/ai/
```

  Po "gotowe" sprawdź `grep -qE "^KIE_OUTPUT_DIR=.+" .env`. Folderu nie musisz zakładać — skill zrobi to przy pierwszym zapisie.

### 8. Podsumowanie

Wyświetl userowi finalny status:

```
✅ kie-generate — setup ukończony

Co masz skonfigurowane:
- Python {wersja} + requests {wersja}
- Plik .env z KIE_API_KEY{ oraz IMGBB_API_KEY, jeśli wybrano edit/compose/remove-bg}
- Brand: {nazwa z .claude/kie-brand.md albo „bez brandu”}
- Zapis grafik: {ścieżka}

Pierwszy test — powiedz po prostu:
"wygeneruj grafikę z napisem 'Hello World' na kremowym tle w kratkę"

Jeśli coś nie zadziała przy pierwszym użyciu:
- 401 → sprawdź KIE_API_KEY (literówka, spacja, cudzysłów w .env)
- 402 → brak środków na koncie Kie.ai (napisz do administratora albo doładuj swoje konto)
- błąd ImgBB (tylko edit/compose/remove-bg) → sprawdź IMGBB_API_KEY
```

## Obsługa błędów podczas onboardingu

- **Brak uprawnień do pip install** → `"$PYTHON" -m pip install --user requests` albo `--break-system-packages` (na niektórych Linuxach)
- **User w innej lokalizacji niż workspace** — sprawdź `pwd` na początku; jeśli brak `.obsidian/` lub `.env` → poproś o przejście do folderu workspace'u i re-run
- **User podaje klucz w złym formacie** (np. z cudzysłowami, spacjami) — pokaż przykład prawidłowego formatu `.env`: `KLUCZ=wartość` bez spacji przed `=`, bez cudzysłowów (chyba że wartość ma spacje)

## Czego NIE robić

- ❌ Nie instaluj nic bez pytania usera (`pip install`, `brew install`)
- ❌ **Nie twórz pliku `.env` za usera** — user sam tworzy w swoim edytorze
- ❌ **Nie edytuj `.env`** (nie dopisuj, nie zmieniaj, nie zapisuj kluczy za usera) — wszystkie modyfikacje `.env` robi user ręcznie. Claude tylko `grep`-uje, żeby sprawdzić, czy klucze są wypełnione, nie czyta wartości
- ❌ Nie robisz realnego calla do Kie.ai ani ImgBB, żeby zweryfikować klucze (user sam zobaczy przy pierwszym użyciu)
- ❌ Nie edytuj plików skilla (`SKILL.md`, skrypty) — aktualizacja pluginu i tak by je nadpisała; brand żyje w `.claude/kie-brand.md`
- ❌ Nie wypisuj kluczy API na ekran (nawet częściowo) — bezpieczeństwo

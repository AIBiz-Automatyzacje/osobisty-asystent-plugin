---
name: skill-scout
description: Przegląda Twoje rozmowy z Claude Code z ostatnich dni i wyłapuje powtarzalną ręczną robotę (ta sama prośba co najmniej 3 razy), którą warto zamienić w nowy skill albo dopisać do istniejącego. Wynik to raport HTML z kandydatami posortowanymi po zaoszczędzonym czasie. Używaj, gdy user pyta, co warto zautomatyzować albo opakować w skill, albo prosi o przegląd powtarzalnej roboty.
allowed-tools: ["Read", "Write", "Bash", "Glob"]
disable-model-invocation: true
argument-hint: "[dni: 7 (domyślnie) | 14 | 21 | 30]"
---

# Skill Scout

Czytasz prośby, które user zleca asystentowi, i szukasz w nich powtarzalnej ręcznej roboty, którą da się zamienić w skill. Niczego nie budujesz i nie zmieniasz poza raportem i plikiem stanu w `Zasoby/raporty/skill-scout/` — decyzję, co opakować, podejmuje user.

## 1. Zbierz prośby

Okno domyślnie 7 dni; argument `14`, `21` albo `30` je nadpisuje.

```bash
PYTHON=""
for cand in python3 python; do
  p=$(command -v "$cand" 2>/dev/null) || continue
  case "$p" in *WindowsApps*) continue;; esac   # atrapa Pythona ze Sklepu Microsoft
  PYTHON="$p"; break
done
mkdir -p .claude/tmp
"$PYTHON" {baseDir}/scripts/parse_intents.py --days "${DAYS:-7}" --out .claude/tmp/scout-intents.json
```

Skrypt wypisuje na stderr liczbę sesji i próśb. Przy `count: 0` powiedz, że w tym oknie nie ma materiału, i zakończ. Świeżo po instalacji to normalne — scout ma sens po tygodniu pracy z asystentem.

## 2. Znajdź kandydatów

Materiał: `.claude/tmp/scout-intents.json` (lista `{date, time, text}`) i plik stanu `Zasoby/raporty/skill-scout/_proposed.json`, jeśli istnieje. Do oceny „nowy skill czy rozbudowa istniejącego” użyj listy skilli dostępnych w tej sesji — obejmuje skille z pluginów i z `.claude/skills/`.

Grupuj prośby po intencji, nie po identycznych słowach: „wrzuć X na Drive i daj link” i „daj link do pliku na dysku” to ten sam proces. Kandydatem jest proces, który pojawił się **co najmniej 3 razy** w oknie i ma powtarzalne kroki ze stałym wejściem i wyjściem. Jednorazowa praca projektowa, decyzje i pisanie konkretnego tekstu kandydatami nie są. Skill wołany przez `/nazwa` też nie — chyba że user robi coś ręcznie obok niego; wtedy to kandydat na rozbudowę tego skilla.

Kandydat, którego `slug` jest już w `_proposed.json`, nie wraca do sekcji nowych. Generator sam pokaże go niżej, w historii.

## 3. Zapisz dane i wygeneruj raport

Nowych kandydatów zostaw najwyżej 7, najmocniejszych pod względem częstotliwości i czasu. Zapisz `Zasoby/raporty/skill-scout/data/YYYY-MM-DD.json`:

```json
{
  "date": "YYYY-MM-DD",
  "window_days": 7,
  "stats": { "intents": 312, "sessions": 41 },
  "candidates": [
    {
      "slug": "raport-tygodnia",
      "title": "Tygodniowy raport sprzedaży z arkusza",
      "type": "new",
      "update_target": null,
      "freq": 4,
      "minutes_per_run": 20,
      "what": "Co tydzień zbierasz liczby z arkusza i piszesz krótkie podsumowanie. Stałe wejście i wyjście.",
      "evidence": ["zrób podsumowanie sprzedaży (01.10)", "raport z arkusza na piątek (06.10)"]
    }
  ]
}
```

- `type`: `new` albo `update` (wtedy `update_target` = nazwa rozbudowywanego skilla).
- `freq`: ile razy proces pojawił się w oknie (policzone z dowodów).
- `minutes_per_run`: szacunek, ile minut zajmuje jeden przebieg ręcznie. To szacunek — raport podaje go jako przybliżenie.
- `evidence`: 2–4 krótkie cytaty z datą, żeby user zobaczył powtarzalność.

Oszczędność i priorytet (`freq × minutes_per_run`) liczy generator. Odpal go **przed** krokiem 4, bo czyta historię z `_proposed.json` w stanie sprzed dopisania nowych:

```bash
node {baseDir}/scripts/generate-raport.mjs Zasoby/raporty/skill-scout/data/$(date +%F).json
```

Raport: `Zasoby/raporty/skill-scout/Raporty/raport-aktualny.html` (+ kopia z datą).

## 4. Zaktualizuj plik stanu

Dopisz nowych kandydatów do `proposed` w `_proposed.json` (te same pola co w danych + `first_proposed: YYYY-MM-DD`). Plik istnieje → dołącz, nie nadpisuj; slug już obecny → pomiń.

## 5. Zadanie i podsumowanie

Gdy pojawił się co najmniej jeden nowy kandydat, dodaj zadanie skillem `utworz-zadanie`, żeby raport nie przepadł w Zasobach: `Przejrzyj N kandydatów na skille | normalne | dzisiaj | Zasoby/raporty/skill-scout/Raporty/raport-aktualny.html`.

W czacie krótko: okno i liczba przejrzanych próśb, ilu nowych kandydatów, najmocniejszy jeden lub dwa, ścieżka do raportu. Na koniec usuń `.claude/tmp/scout-intents.json`.

## Uruchamianie z Pulsa

Skill działa też bez człowieka jako claude-job (np. co tydzień). Ustaw `CLAUDE_CRON_WORKSPACE` na folder vaulta — parser i generator czytają tę zmienną i z niej biorą ścieżki. Zadanie z kroku 5 trafi do `Dashboard.md`, więc raport zobaczysz przy `/daily`.

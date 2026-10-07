# Osobisty Asystent AI

Plugin Akademii Automatyzacji, który stawia Twojego osobistego asystenta AI w Obsidian + Claude Code. Wpisujesz jedną komendę, przechodzisz rozmowę, a asystent sam buduje Ci gotową przestrzeń do pracy: Twój profil, swój charakter i listę zadań.

## Co dostajesz

Wizard `/onboard` przeprowadza Cię przez wywiad i tworzy:

- `persona.md` — Twój profil (kim jesteś, jak pracujesz, jak chcesz rozmawiać z AI)
- `soul.md` — charakter asystenta dopasowany do Ciebie
- `biznes.md` — kontekst Twojej firmy lub pracy (opcjonalny)
- `environment.md` — wykryte środowisko komputera
- `Zadania/Dashboard.md` — lista zadań (jedno zadanie = jedna linia) i folder `Zasoby/`
- `CLAUDE.md` — mapa, która spina to wszystko w całość

Skille do codziennej pracy:

- `/daily` — poranne porządki: archiwizuje odhaczone zadania, dorzuca cykliczne, układa Dashboard według terminów
- `/utworz-zadanie` — dopisuje zadanie do Dashboardu (nazwa, priorytet, termin)
- `/memory-update` — aktualizuje `NOW.md` (bieżący kontekst pracy) z Twoich rozmów
- `/reflect` — analizuje sesje i proponuje poprawki w profilu i stylu asystenta
- `/skill-scout` — raz w tygodniu wyłapuje powtarzalną robotę, którą warto zamienić w skill

Zaawansowane (dalsze moduły kursu): `/zdalna-sesja`, `/deleguj`, `/plugin-zespolowy` — opis niżej.

## Czego potrzebujesz

- **Subskrypcja Claude** (wystarczy najtańszy plan) — https://claude.com/pricing
- Komputer z macOS albo Windowsem (Obsidian w telefonie nie ma terminala)

Resztę doinstaluje skrypt z kroku 1.

## Instalacja

### 1. Przygotuj komputer (jedna komenda)

Skrypt sprawdza i doinstalowuje wszystko, czego potrzebuje asystent: Git, Python, Node.js, GitHub CLI, Obsidian i Claude Code. To, co już masz, zostawia w spokoju, więc możesz go odpalać wielokrotnie.

**macOS** — otwórz Terminal (⌘ Spacja → „Terminal”) i wklej:

```
curl -fsSL https://raw.githubusercontent.com/AIBiz-Automatyzacje/osobisty-asystent-plugin/main/scripts/przygotuj.sh | bash
```

**Windows** — otwórz PowerShell (Start → wpisz „PowerShell”, zwykłe uruchomienie, nie jako administrator) i wklej:

```
irm https://raw.githubusercontent.com/AIBiz-Automatyzacje/osobisty-asystent-plugin/main/scripts/przygotuj.ps1 | iex
```

Po skończeniu zamknij okno i otwórz nowe — dopiero nowe widzi świeżo zainstalowane programy.

### 2. Vault i wtyczki w Obsidianie

1. Otwórz Obsidiana i utwórz nowy vault (to po prostu folder na Twoje pliki).
2. **Ustawienia → Wtyczki społeczności → Włącz** (jeśli widzisz tryb ograniczony), potem **Przeglądaj** i zainstaluj + włącz trzy wtyczki:
   - **Terminal** (autor: polyipseity) — terminal w Obsidianie
   - **BRAT** — instaluje wtyczki prosto z GitHuba
   - **Hidden Folders Access** — pokazuje ukryty folder `.claude`, w którym żyją pliki asystenta
3. Paleta komend (`Cmd + P` / `Ctrl + P`) → **BRAT: Add a beta plugin for testing** → wklej `AIBiz-Automatyzacje/obsidian-claude-launcher` → **Add plugin**.
4. W lewym pasku pojawi się ikonka Claude Code Launchera. Kliknij ją — w vaultcie otworzy się sesja Claude Code.

Szczegóły launchera: https://github.com/AIBiz-Automatyzacje/obsidian-claude-launcher

### 3. Plugin asystenta

W sesji Claude Code wpisz:

```
/plugin marketplace add AIBiz-Automatyzacje/osobisty-asystent-plugin
```

```
/plugin install osobisty-asystent@osobisty-asystent
```

Zamknij sesję i otwórz nową (ikonka launchera), żeby skille się wczytały.

### 4. Onboarding

Wpisz:

```
/onboard
```

Przejdź całą rozmowę (ok. 15–20 minut). Odpowiadaj tak dokładnie, jak potrafisz — im więcej powiesz, tym lepiej asystent się do Ciebie dopasuje. Po skończonym onboardingu masz gotowy system. `NOW.md` powstanie sam przy pierwszym `/memory-update`.

Wygląd listy zadań i Skrzynki zmienił się po aktualizacji pluginu? `/onboard --refresh-theme` odświeża same style, bez ponownego wywiadu.

## Zaawansowane — asystent w kieszeni (Poziom 2)

- `/zdalna-sesja` — odpala i pilnuje sesji Claude Code na Twoim serwerze (VPS) z lokalnego komputera. Uruchamiasz nazwane sesje, które żyją w tle (`tmux`) i sterujesz nimi z telefonu przez Remote Control — bez wchodzenia ręcznie na serwer.

Ten skill zakłada, że masz już asystenta postawionego w chmurze (VPS + Obsidian Sync + Puls — z lekcji Poziomu 2). W pliku `.env` w roocie vaulta dodaj, jak dostać się do serwera:

```
VPS_SSH=vps          # alias z ~/.ssh/config (ma przypięty klucz) — zalecane
# albo, dla świeżego serwera z logowaniem na root:
VPS_HOST=<ip-serwera>
VPS_RUN_AS=claude
```

Wymaga działającego dostępu SSH do VPS oraz Claude Code w wersji ≥ 2.1.51 na serwerze (Remote Control). Komendy: `new <nazwa>` (nowa sesja), `list` (żywe sesje), `kill <nazwa>`, `attach <nazwa>`.

## Moduł C — Team OS

- `/deleguj` — wiadomości i zadania między asystentami członków zespołu przez wspólną Skrzynkę (wymaga Pulsa i huba Team OS).
- `/plugin-zespolowy` — buduje i utrzymuje wspólny plugin Waszego zespołu:
  - `init` — stawia repo pluginu od zera: manifesty, README z instrukcją instalacji dla zespołu, strażnik sekretów (skill bez klucza nie wystartuje) oraz mechanikę **kontekstu firmowego**: skille `kontekst-sygnaly` i `kontekst-firmowy` plus hook, który rozdaje `company-context.md` wszystkim przy starcie sesji.
  - `add <skill>` — przenosi skill z Twojego `.claude/skills/` do pluginu, z audytem przed kopiowaniem: wklejone klucze i sztywne ścieżki nie przejdą.
  - `check` — raport driftu: co masz lokalnie, a czego nie ma w pluginie (i odwrotnie).

Wymaga zalogowanego GitHub CLI (`gh auth login` + `gh auth setup-git`). Reszta instrukcji — w README, które `init` generuje dla Twojego zespołu.

---

Akademia Automatyzacji — https://akademiaautomatyzacji.com

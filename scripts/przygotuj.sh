#!/bin/bash
# =====================================================================
#  Osobisty Asystent AI — przygotowanie komputera (macOS)
#
#  Sprawdza, czy masz wszystko, czego potrzebuje asystent, i doinstalowuje
#  braki: narzędzia Xcode (git + python3), Node.js, GitHub CLI, Obsidian,
#  Claude Code. Na końcu pyta, czy zalogować GitHuba (potrzebny do kopii
#  zapasowej vaulta).
#
#  Uruchomienie (Terminal):
#    curl -fsSL https://raw.githubusercontent.com/AIBiz-Automatyzacje/osobisty-asystent-plugin/main/scripts/przygotuj.sh | bash
#
#  Tylko sprawdzenie, bez instalowania:
#    curl -fsSL https://raw.githubusercontent.com/AIBiz-Automatyzacje/osobisty-asystent-plugin/main/scripts/przygotuj.sh | bash -s -- --tylko-sprawdz
#
#  Skrypt można odpalać wielokrotnie — to, co już jest, zostawia w spokoju.
# =====================================================================

set -u

TYLKO_SPRAWDZ=0
for arg in "$@"; do
  case "$arg" in
    --tylko-sprawdz|--check) TYLKO_SPRAWDZ=1 ;;
  esac
done

NODE_MIN=18
TMP_DIR="$(mktemp -d -t asystent-przygotuj)"
trap 'rm -rf "$TMP_DIR"' EXIT

# Pytania czytamy z klawiatury (/dev/tty), bo przy `curl | bash` standardowe
# wejście zajmuje sam skrypt. Brak terminala = tryb bez pytań.
MA_TTY=0
if [ -r /dev/tty ] && (exec </dev/tty) 2>/dev/null; then MA_TTY=1; fi

zapytaj() {  # zapytaj "Pytanie" domyslna(t/n) → zwraca 0 dla tak
  local pytanie="$1" domyslna="$2" odp=""
  if [ "$MA_TTY" -ne 1 ]; then return 1; fi
  if [ "$domyslna" = "t" ]; then printf "%s [T/n] " "$pytanie"; else printf "%s [t/N] " "$pytanie"; fi
  read -r odp </dev/tty || odp=""
  odp="$(printf '%s' "$odp" | tr '[:upper:]' '[:lower:]')"
  [ -z "$odp" ] && odp="$domyslna"
  [ "$odp" = "t" ] || [ "$odp" = "tak" ] || [ "$odp" = "y" ] || [ "$odp" = "yes" ]
}

naglowek() { printf "\n\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  ✅ %s\n" "$1"; }
brak() { printf "  ❌ %s\n" "$1"; }
uwaga(){ printf "  ⚠️  %s\n" "$1"; }

# ---------------------------------------------------------------------
#  Wykrywanie
# ---------------------------------------------------------------------

# Bez narzędzi Xcode /usr/bin/git i /usr/bin/python3 to atrapy, które zamiast
# działać otwierają okno instalacji — dlatego najpierw pytamy xcode-select.
ma_xcode() { xcode-select -p >/dev/null 2>&1; }

ma_git() {
  local p; p="$(command -v git 2>/dev/null)" || return 1
  if [ "$p" = "/usr/bin/git" ]; then ma_xcode; else return 0; fi
}

ma_python() {
  local p; p="$(command -v python3 2>/dev/null)" || return 1
  if [ "$p" = "/usr/bin/python3" ]; then ma_xcode; else return 0; fi
}

node_major() { node --version 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/'; }
ma_node() {
  command -v node >/dev/null 2>&1 || return 1
  local m; m="$(node_major)"
  [ -n "$m" ] && [ "$m" -ge "$NODE_MIN" ]
}

ma_gh() { command -v gh >/dev/null 2>&1; }

CLAUDE_LOCAL="$HOME/.local/bin/claude"
ma_claude() { command -v claude >/dev/null 2>&1; }
claude_poza_path() { ! ma_claude && [ -x "$CLAUDE_LOCAL" ]; }

ma_obsidian() { [ -d "/Applications/Obsidian.app" ] || [ -d "$HOME/Applications/Obsidian.app" ]; }

BRAKI=()

sprawdz_wszystko() {
  BRAKI=()
  if ma_xcode; then ok "Narzędzia Xcode (git, python3)"; else brak "Narzędzia Xcode (git, python3)"; BRAKI+=(xcode); fi
  if ma_git; then ok "Git: $(git --version 2>/dev/null | awk '{print $3}')"; else brak "Git"; fi
  if ma_python; then ok "Python: $(python3 --version 2>&1 | awk '{print $2}')"; else brak "Python 3"; fi
  if ma_node; then
    ok "Node.js: $(node --version)"
  elif command -v node >/dev/null 2>&1; then
    brak "Node.js $(node --version) — za stary, potrzebny co najmniej v$NODE_MIN"; BRAKI+=(node)
  else
    brak "Node.js"; BRAKI+=(node)
  fi
  if ma_gh; then
    if gh auth status >/dev/null 2>&1; then ok "GitHub CLI: $(gh --version | head -1 | awk '{print $3}') (zalogowany)"
    else ok "GitHub CLI: $(gh --version | head -1 | awk '{print $3}')"; uwaga "GitHub CLI nie jest zalogowany (potrzebne do kopii zapasowej)"; fi
  else
    brak "GitHub CLI (gh)"; BRAKI+=(gh)
  fi
  if ma_claude; then
    ok "Claude Code: $(claude --version 2>/dev/null | head -1)"
  elif claude_poza_path; then
    brak "Claude Code jest zainstalowany, ale terminal go nie widzi (brak w PATH)"; BRAKI+=(claude_path)
  else
    brak "Claude Code"; BRAKI+=(claude)
  fi
  if ma_obsidian; then ok "Obsidian"; else brak "Obsidian"; BRAKI+=(obsidian); fi
}

# ---------------------------------------------------------------------
#  Instalacja
# ---------------------------------------------------------------------

pobierz() { curl -fsSL --retry 3 -o "$2" "$1"; }

# Adres pierwszego pliku z najnowszego wydania na GitHubie, którego nazwa pasuje do wzorca.
github_asset() {  # github_asset owner/repo regex
  curl -fsSL "https://api.github.com/repos/$1/releases/latest" \
    | grep -o '"browser_download_url": *"[^"]*"' \
    | sed -E 's/.*"(https[^"]*)"/\1/' \
    | grep -E "$2" | head -1
}

sudo_raz() {
  if ! sudo -n true 2>/dev/null; then
    echo "  Za chwilę Mac poprosi o hasło (to samo, którym się logujesz). Znaki się nie wyświetlają — wpisz i Enter."
    sudo -v </dev/tty || return 1
  fi
}

instaluj_xcode() {
  naglowek "→ Narzędzia Xcode (git + python3)"
  xcode-select --install >/dev/null 2>&1
  echo "  Na ekranie pojawiło się okno: kliknij „Zainstaluj”, potem „Zgadzam się”."
  echo "  Czekam, aż instalacja się skończy (zwykle 5–15 minut)…"
  local i=0
  until ma_xcode; do
    sleep 10; i=$((i + 10))
    if [ "$i" -ge 2700 ]; then
      brak "Narzędzia Xcode nadal się nie zainstalowały. Dokończ instalację i odpal skrypt jeszcze raz."
      return 1
    fi
  done
  ok "Narzędzia Xcode zainstalowane"
}

instaluj_node() {
  naglowek "→ Node.js (wersja LTS)"
  local wersja
  wersja="$(curl -fsSL https://nodejs.org/dist/index.json | grep -o '"version":"v[0-9.]*"[^}]*"lts":"[^"]*"' | head -1 | sed -E 's/.*"version":"(v[0-9.]+)".*/\1/')"
  if [ -z "$wersja" ]; then brak "Nie udało się sprawdzić najnowszej wersji Node.js (brak internetu?)"; return 1; fi
  echo "  Pobieram Node.js $wersja…"
  pobierz "https://nodejs.org/dist/$wersja/node-$wersja.pkg" "$TMP_DIR/node.pkg" || { brak "Pobieranie Node.js nie powiodło się"; return 1; }
  sudo_raz || return 1
  sudo installer -pkg "$TMP_DIR/node.pkg" -target / >/dev/null || { brak "Instalacja Node.js nie powiodła się"; return 1; }
  export PATH="/usr/local/bin:$PATH"
  ok "Node.js $wersja zainstalowany"
}

instaluj_gh() {
  naglowek "→ GitHub CLI (gh)"
  local url; url="$(github_asset cli/cli '_macOS_universal\.pkg$')"
  if [ -z "$url" ]; then brak "Nie znalazłem instalatora GitHub CLI"; return 1; fi
  echo "  Pobieram $(basename "$url")…"
  pobierz "$url" "$TMP_DIR/gh.pkg" || { brak "Pobieranie GitHub CLI nie powiodło się"; return 1; }
  sudo_raz || return 1
  sudo installer -pkg "$TMP_DIR/gh.pkg" -target / >/dev/null || { brak "Instalacja GitHub CLI nie powiodła się"; return 1; }
  export PATH="/usr/local/bin:$PATH"
  ok "GitHub CLI zainstalowany"
}

instaluj_obsidian() {
  naglowek "→ Obsidian"
  local url; url="$(github_asset obsidianmd/obsidian-releases '/Obsidian-[0-9.]+\.dmg$')"
  if [ -z "$url" ]; then brak "Nie znalazłem instalatora Obsidiana"; return 1; fi
  echo "  Pobieram $(basename "$url")…"
  pobierz "$url" "$TMP_DIR/obsidian.dmg" || { brak "Pobieranie Obsidiana nie powiodło się"; return 1; }
  local mnt="$TMP_DIR/obsidian-dmg"; mkdir -p "$mnt"
  hdiutil attach -nobrowse -quiet -mountpoint "$mnt" "$TMP_DIR/obsidian.dmg" || { brak "Nie udało się otworzyć pliku .dmg"; return 1; }
  local cel="/Applications"
  if ! cp -R "$mnt/Obsidian.app" "$cel/" 2>/dev/null; then
    sudo_raz && sudo cp -R "$mnt/Obsidian.app" "$cel/" || { hdiutil detach -quiet "$mnt"; brak "Kopiowanie Obsidiana do Aplikacji nie powiodło się"; return 1; }
  fi
  hdiutil detach -quiet "$mnt"
  ok "Obsidian zainstalowany (Aplikacje → Obsidian)"
}

dopisz_path_claude() {
  local linia='export PATH="$HOME/.local/bin:$PATH"'
  local plik="$HOME/.zshrc"
  case "${SHELL:-}" in */bash) plik="$HOME/.bash_profile" ;; esac
  if ! grep -qs '\.local/bin' "$plik"; then
    printf '\n# Claude Code\n%s\n' "$linia" >> "$plik"
    ok "Dopisałem ~/.local/bin do $(basename "$plik") — działa w każdym nowym oknie Terminala"
  fi
  export PATH="$HOME/.local/bin:$PATH"
}

instaluj_claude() {
  naglowek "→ Claude Code"
  curl -fsSL https://claude.ai/install.sh | bash || { brak "Instalator Claude Code zgłosił błąd"; return 1; }
  dopisz_path_claude
  ma_claude && ok "Claude Code zainstalowany"
}

# ---------------------------------------------------------------------
#  Start
# ---------------------------------------------------------------------

# Testy: `PRZYGOTUJ_TYLKO_FUNKCJE=1 source przygotuj.sh` wczytuje same funkcje.
if [ -n "${PRZYGOTUJ_TYLKO_FUNKCJE:-}" ]; then return 0 2>/dev/null || exit 0; fi

if [ "$(uname -s)" != "Darwin" ]; then
  echo "Ten skrypt jest dla macOS. Na Windowsie otwórz PowerShell i wklej:"
  echo "  irm https://raw.githubusercontent.com/AIBiz-Automatyzacje/osobisty-asystent-plugin/main/scripts/przygotuj.ps1 | iex"
  exit 1
fi

printf "\n\033[1mOsobisty Asystent AI — sprawdzam Twój komputer\033[0m\n"
echo "macOS $(sw_vers -productVersion), procesor $(uname -m)"

naglowek "Stan przed instalacją"
sprawdz_wszystko

if [ "${#BRAKI[@]}" -eq 0 ]; then
  naglowek "Wszystko jest na miejscu 🎉"
elif [ "$TYLKO_SPRAWDZ" -eq 1 ]; then
  naglowek "Czegoś brakuje (❌ wyżej). Żeby doinstalować, odpal skrypt bez --tylko-sprawdz."
  exit 1
elif [ "$MA_TTY" -ne 1 ]; then
  naglowek "Czegoś brakuje (❌ wyżej), a nie mogę zapytać o zgodę na instalację. Odpal skrypt w oknie Terminala."
  exit 1
else
  echo ""
  if zapytaj "Zainstalować brakujące rzeczy teraz?" t; then
    for b in "${BRAKI[@]}"; do
      case "$b" in
        xcode)       instaluj_xcode ;;
        node)        instaluj_node ;;
        gh)          instaluj_gh ;;
        obsidian)    instaluj_obsidian ;;
        claude)      instaluj_claude ;;
        claude_path) naglowek "→ Claude Code do PATH"; dopisz_path_claude ;;
      esac
    done
    naglowek "Stan po instalacji"
    sprawdz_wszystko
  else
    echo "OK, nic nie instaluję."
  fi
fi

# Logowanie do GitHuba — opcjonalne, potrzebne w lekcji o kopii zapasowej.
if ma_gh && ! gh auth status >/dev/null 2>&1 && [ "$TYLKO_SPRAWDZ" -ne 1 ]; then
  echo ""
  if zapytaj "Zalogować się teraz do GitHuba? (potrzebne do kopii zapasowej, możesz zrobić to później)" n; then
    echo "  Wybieraj: GitHub.com → HTTPS → Yes → Login with a web browser. Kod skopiuj do przeglądarki."
    gh auth login -h github.com -p https -w </dev/tty && gh auth setup-git && ok "GitHub zalogowany"
  fi
fi

naglowek "Co dalej"
if [ "${#BRAKI[@]}" -eq 0 ]; then
  echo "  1. Zamknij ten Terminal (⌘Q) i otwórz nowy — dopiero nowe okno widzi świeżo zainstalowane programy."
  echo "  2. Otwórz Obsidiana i wróć do lekcji."
else
  echo "  Część rzeczy dalej brakuje (❌ wyżej). Zamknij Terminal (⌘Q), otwórz nowy i odpal skrypt jeszcze raz."
  echo "  Jeśli znowu się nie uda, wklej cały wynik w komentarzu pod lekcją."
  exit 1
fi

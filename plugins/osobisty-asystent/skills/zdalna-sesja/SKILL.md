---
name: zdalna-sesja
description: Zarządzanie zdalnymi sesjami Claude Code (tmux + Remote Control) na VPS z poziomu lokalnego komputera — bez ręcznego wchodzenia na serwer. Odpala nazwane sesje (możesz mieć kilka równolegle), listuje żywe, ubija i pokazuje jak się podłączyć. Używaj gdy user mówi — "odpal zdalną sesję", "nowa sesja na VPS/serwerze", "uruchom claude na serwerze", "postaw sesję marketing/research na VPS", "pokaż/wylistuj sesje na serwerze", "jakie sesje chodzą na VPS", "ubij sesję na VPS", "zamknij zdalną sesję", "sesja remote control", "podłącz się do sesji na serwerze". Sesje działają w tle na VPS i sterujesz nimi z telefonu/weba przez Remote Control.
allowed-tools: ["Bash", "Read"]
argument-hint: "[new <nazwa> | list | kill <nazwa> | attach <nazwa>]"
---

# zdalna-sesja — zdalne sesje Claude Code na VPS

Odpala i pilnuje sesji Claude Code na serwerze **z lokalnego komputera**. Nie wchodzisz ręcznie na VPS — jedna komenda stawia nazwaną sesję w `tmux`, w której Claude startuje od razu z Remote Control. Możesz mieć kilka sesji naraz (np. `marketing`, `research`, `klient-x`) i sterować każdą z telefonu lub weba.

## Model połączenia (dlaczego tak)

`ssh root@<VPS> → su - claude → tmux → claude --remote-control`

- Wchodzimy na VPS jako **root** (klucz SSH), ale Claude leci pod userem **`claude`** — root ma zablokowane `--dangerously-skip-permissions`.
- Sesja żyje w `tmux`, więc działa dalej po zamknięciu Twojego terminala.
- `--remote-control <nazwa>` włącza sterowanie z telefonu/weba i od razu nazywa sesję.
- Sesja tmux i sesja Remote Control mają **tę samą nazwę** — łatwo je skojarzyć.

## Konfiguracja (jednorazowo)

Skill czyta dane serwera z `.env` w roocie vaulta. Wymagane jest JEDNO z dwóch:

```
VPS_HOST=<tailscale-ip-serwera>     # świeży VPS po B1: login jako root, Claude pod userem claude
VPS_SSH=vps                          # albo alias z ~/.ssh/config (login od razu jako claude, bez su)
```

`VPS_HOST` sprawdzisz na VPS komendą `tailscale ip -4`.

Opcjonalne (mają rozsądne domyślne):

```
VPS_USER=root                        # user SSH przy VPS_HOST (domyślnie root)
VPS_RUN_AS=claude                    # user, pod którym chodzi Claude (przy logowaniu jako root domyślnie claude)
VPS_VAULT_PATH=/home/claude/vault    # katalog roboczy sesji (domyślnie /home/claude/vault)
```

Starsza nazwa `VPS_REMOTE_USER` działa tak samo jak `VPS_RUN_AS`.

Wymóg wstępny: klucz SSH działa do VPS po Tailscale IP (jak przy instalacji z lekcji B1).

## Komendy

Wszystko przez skrypt `scripts/vps-session.js` (Node, zero zależności):

| Cel | Komenda |
|-----|---------|
| Nowa nazwana sesja | `node scripts/vps-session.js new <nazwa>` |
| Żywe sesje na VPS | `node scripts/vps-session.js list` |
| Ubij sesję | `node scripts/vps-session.js kill <nazwa>` |
| Podgląd w terminalu | `node scripts/vps-session.js attach <nazwa>` |
| Podgląd komendy bez łączenia | dowolna akcja + `--dry-run` |

Nazwa sesji: litery, cyfry, `-` i `_` (max 40 znaków) — walidowane, żeby nie dało się wstrzyknąć komendy.

## Jak działać (dla asystenta)

1. Odpalaj komendy przez **Bash**, z katalogu skilla albo pełną ścieżką do `scripts/vps-session.js`.
2. **`new`** — po sukcesie powiedz userowi, że sesja o danej nazwie działa i można się podłączyć z telefonu/weba przez Remote Control (ta sama nazwa).
3. **`list`** — pokaż surowy output tmux (nazwy + czy przypięte).
4. **`kill`** — potwierdź którą sesję ubijasz zanim odpalisz, jeśli nazwa niejednoznaczna.
5. **`attach`** — skill tylko **wypisuje** komendę; user wkleja ją sam w swoim terminalu (attach jest interaktywny, wymaga TTY). Wyjście z podglądu bez ubijania sesji: `Ctrl+B`, potem `D`.
6. Gdy `VPS_HOST` nie jest ustawiony — poproś usera o dopisanie do `.env` (patrz Konfiguracja), nie zgaduj adresu.
7. Przy diagnozie budowanej komendy używaj `--dry-run` — pokazuje pełny `ssh` i skrypt wykonywany na VPS bez łączenia z serwerem.

## Uwagi

- Sesja to `exec claude ...` w tmux — gdy Claude się zamknie (`/exit`), sesja tmux znika sama.
- `list` przy zerowej liczbie sesji zwraca `(brak aktywnych sesji)` zamiast błędu.
- Skill NIE trzyma żadnych sekretów — tylko adres serwera w `.env` (poza gitem).

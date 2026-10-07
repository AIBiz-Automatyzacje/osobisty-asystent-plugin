---
name: deleguj
description: Team OS — WEWNĘTRZNA skrzynka Twojego zespołu przez Pulsa (claude-cron). Wysyła zadania i pytania do innych osób z zespołu, które też mają Pulsa (Skrzynka.md), odpowiada w wątkach ze Skrzynki i je zamyka; obsługuje załączniki. Użyj TYLKO, gdy adresatem jest ktoś z zespołu i user chce to wysłać przez skrzynkę / Team OS / Pulsa albo odpisać na wiadomość ze Skrzynki (np. „deleguj to na…”, „wyślij przez skrzynkę do…”, „odpisz w wątku”, „zamknij wątek”). NIE używaj do wiadomości, maili ani ofert do klientów, firm i innych osób spoza zespołu — to zwykła korespondencja, nie Team OS. Wymaga zainstalowanego Pulsa.
---

# Skill `deleguj` — Team OS

API dla Claude do komunikacji między członkami teamu. User mówi naturalnym językiem, Ty rozpoznajesz intent (`task` / `query` / `reply` / `close`) i wywołujesz właściwą subkomendę.

## Rozpoznawanie typu z natural language

| User mówi | Typ |
|-----------|-----|
| "wyślij zadanie", "deleguj X", "poproś żeby zrobił Z", "zrób X przez Anię", "przekaż do walidacji" | **task** |
| "spytaj X o Y", "zapytaj czy", "dowiedz się od Z", pytanie z "?" w treści | **query** |
| "odpisz na thread", "odpowiedz X że Y", "wracaj do tematu" (jest thread_id) | **reply** |
| "zamknij wątek", "skończ thread", "to już załatwione" | **close** |

Jeśli intent niejednoznaczny — zapytaj usera krótko ("task czy query?").

**Najpierw sprawdź adresata.** Skill służy wyłącznie do komunikacji wewnątrz zespołu przez Pulsa. Adresat to klient,
firma albo ktokolwiek spoza zespołu → to nie ten skill: przerwij i pomóż napisać zwykłą wiadomość/maila.
Nie wiesz, czy osoba jest w zespole → zapytaj jednym zdaniem.

**Brak Pulsa** (pusty `$PULS_HOME`) → nie próbuj niczego instalować ani obchodzić. Powiedz userowi jednym zdaniem:
„Wewnętrzna skrzynka działa tylko z zainstalowanym Pulsem — tę wiadomość wyślij do zespołu zwykłym kanałem firmowym.”

## Subkomendy

### `send` — nowa wiadomość (task lub query)

```
[ -n "$PULS_HOME" ] || { echo "Brak PULS_HOME — zaktualizuj Pulsa (re-run instalatora). Bez tego nie da się wysłać wiadomości komendą."; exit 1; }
node "$PULS_HOME/scripts/inbox/send.mjs" \
  --to <nick> \
  --title "<krótki tytuł>" \
  --content "<pełna treść>" \
  --type task|query
```

⚠️ **Treść dłuższa niż jedna linia albo z cudzysłowami idzie PLIKIEM, nie `--content`.** Zapisz ją do pliku tymczasowego i podaj `--content-file`:

```
node "$PULS_HOME/scripts/inbox/send.mjs" \
  --to <nick> \
  --title "<krótki tytuł>" \
  --content-file /tmp/tresc.md \
  --type task|query
```

Powód: znaki `"` w wartości `--content` rozbijają jeden argument na kilka (PowerShell 5.1 nie escapuje ich przed przekazaniem do `node.exe`), co potrafi obciąć wiadomość wysłaną z Windowsa. Plik nie przechodzi przez parser linii poleceń, więc nic go nie ruszy. `--content` zostaw dla krótkich, jednolinijkowych treści bez cudzysłowów. Skrypt od tej pory wywala się z błędem zamiast po cichu wysłać obciętą wiadomość, ale nie licz na to — dawaj plik od razu.

⚠️ **`--type` jest OBOWIĄZKOWE** — ZAWSZE przekazuj jawnie `--type task` albo `--type query`. Skrypt nie zakłada żadnego defaultu i odrzuci wywołanie bez `--type`. To zapobiega cichemu wysłaniu pytania (`query`) jako zadania (`task`) — odbiorca dostaje inny render/banner/checkbox.

**Załączniki: `--attach <ścieżka>`** — flagę można podać wiele razy (jeden plik = jedna flaga):

```
node "$PULS_HOME/scripts/inbox/send.mjs" \
  --to <nick> \
  --title "<tytuł>" \
  --content-file /tmp/tresc.md \
  --type task \
  --attach /ścieżka/do/pliku.pdf \
  --attach /ścieżka/do/drugiego.png
```

Limit **25 MB na pojedynczy plik**, sprawdzany PRZED wysyłką — nie ma limitu na liczbę plików. Katalogów nie da się załączyć. Skrypt wyliczy sumę kontrolną, wgra bajty na hub i dopiero potem utworzy wiadomość: **jeśli którykolwiek plik nie przejdzie, wiadomość NIE powstaje** (nie ma stanu „wysłane bez załącznika"). Ten sam plik wysłany drugi raz nie jedzie przez sieć ponownie — hub rozpoznaje go po sumie.

Gdy plik jest za duży, skrypt powie to wprost i **nie wyśle niczego** — nie próbuj dzielić pliku ani obchodzić limitu; poinformuj usera i zapytaj, co zrobić (mniejsza wersja, link do Drive).

**Zwraca JSON:** `{ id, thread_id, created_at, title, to_user, type }`

**Po sukcesie** Claude NIE edytuje `Skrzynka.md` ręcznie — pull-job zrobi to przy następnym runie (max 1 min). Po prostu poinformuj usera: `📤 Wysłano [task|query] do <to_user>: <title>`.

### `reply` — odpowiedź na wiadomość w threadzie

```
[ -n "$PULS_HOME" ] || { echo "Brak PULS_HOME — zaktualizuj Pulsa (re-run instalatora). Bez tego nie da się odpowiedzieć komendą."; exit 1; }
node "$PULS_HOME/scripts/inbox/reply.mjs" \
  --thread-id <uuid> \
  --content "..." \
  [--title "Re: ..."]
```

⚠️ Ta sama zasada co przy `send`: treść wielolinijkowa albo z cudzysłowami → `--content-file /tmp/tresc.md` zamiast `--content`.

`--attach <ścieżka>` działa tak samo jak w `send` (wielokrotnie, limit 25 MB na plik) — możesz odpowiedzieć w wątku, dokładając pliki.

Adresata wyprowadza z wątku (oryginalny nadawca task/query; gdy wątek założyłeś sam — jego odbiorca). `thread_id` widać w `Skrzynka.md` w callouts jako Obsidian comment `%% thread:<uuid> %%` (w callout otrzymanej wiadomości pełna forma to `%% id:<id> thread:<uuid> %%`).

Gdy wątek jest już domknięty (nie ma go w skrzynce), podaj adresata jawnie: `--to <nick>`.

**Zwraca:** `{ id, thread_id, to_user, title, type: 'reply' }`

### `close` — zamknięcie threadu bez odpowiedzi

```
[ -n "$PULS_HOME" ] || { echo "Brak PULS_HOME — zaktualizuj Pulsa (re-run instalatora) albo ustaw PULS_HOME na katalog instalacji. Bez tego nie da się domknąć wątku komendą; użyj checkboxa w Skrzynce."; exit 1; }
node "$PULS_HOME/scripts/inbox/close.mjs" --thread-id <uuid>
```

⚠️ Skrypt mieszka **w repo Pulsa**, nie w vaultcie — dzięki temu domknięcie komendą archiwizuje nitkę tym samym kodem co odhaczenie checkboxa w Skrzynce. **Nie wołaj `node` bez guardu na `PULS_HOME`** — bez zmiennej dostaniesz nieczytelne `MODULE_NOT_FOUND` zamiast informacji, co naprawić.

Domyka wiadomości wątku **zaadresowane do Ciebie** (akcja `Zapoznane`). Znikną z Otrzymanych w Skrzynce, a cała nitka trafi do `Zasoby/inbox-archive/YYYY-MM.md`. Twoje wysłane delegacje zostają w Delegowanych — task zamyka odbiorca checkboxem „Zrobione", nie nadawca z drugiej strony. Idempotentne: powtórzone wywołanie zwraca `closed: 0` i **nie dopisuje drugiego wpisu do archiwum**.

**Zwraca:** `{ thread_id, closed, archived }` (albo dodatkowo `note`, gdy nie było czego domykać)

## Odbieranie załączników

Załącznik przychodzi w Skrzynce jako wiersz pod treścią wiadomości, w jednym z trzech stanów:

| Co widzisz | Znaczenie |
|---|---|
| `- [ ] Pobierz — 📎 nazwa · rozmiar` | bajty czekają na hubie, u Ciebie ich jeszcze nie ma |
| `📎 nazwa` + podgląd pliku | pobrane, plik leży w `Zasoby/inbox-zalaczniki/RRRR-MM/` |
| `📎 … · wygasł` | bajty skasowane przez retencję — poproś nadawcę o ponowne wysłanie |

**Pobranie = odhaczenie checkboxa „Pobierz” w `Skrzynka.md`** — przy najbliższym syncu (max 1 min) plik zjedzie na dysk, a wiersz zamieni się w podgląd. Odhaczyć może user albo Ty: gdy user o to prosi albo gdy plik jest potrzebny do zadania, które robisz (np. blueprint do wgrania), zamień w tej jednej linii `- [ ] Pobierz` na `- [x] Pobierz` i nic więcej w pliku nie ruszaj. Potem poczekaj na sync i sprawdź, czy plik leży w `Zasoby/inbox-zalaczniki/RRRR-MM/` — dopiero wtedy mów, że jest pobrany.

Trzy rzeczy, o których musisz wiedzieć, żeby nie wprowadzać usera w błąd:

- **Pobranie jest akcją wyłącznie lokalną.** Nie idzie do huba i **nie domyka wątku** — wiadomość dalej czeka na odpowiedź albo na „Zrobione". Nie mów userowi, że odhaczenie „Pobierz" załatwia sprawę.
- **Nazwa pliku na dysku ma doklejony fragment sumy** (`raport (a1b2c3d4).pdf`) — tak samo nazwany plik od dwóch osób się nie nadpisze. Szukając pliku, nie zakładaj gołej nazwy.
- **Maszyna z rolą `agent` nie pobiera nigdy** (VPS, auto-reply). To nie awaria — katalog załączników jest wyłączony z synchronizacji vaulta.

Bajty żyją na hubie **14 dni po domknięciu wątku**, twardo **90 dni od wysłania**. Po tym zostaje sam wpis „wygasł" — treść wiadomości zostaje, znika tylko plik.

## Natural language examples

| User mówi | Subkomenda | Args |
|-----------|------------|------|
| "wyślij Ani profil X do walidacji" | `send` | `--to ania --title "Walidacja profilu X" --content "..." --type task` |
| "spytaj Anię, czy skończył LP" | `send` | `--to ania --title "Status LP" --content "Czy skończyłeś?" --type query` |
| "odpisz Ani w threadzie abc123 że zrobione" | `reply` | `--thread-id abc123 --content "Zrobione"` |
| "zamknij wątek abc123" | `close` | `--thread-id abc123` (skrypt z `$PULS_HOME/scripts/inbox/`) |
| "wyślij Filipowi ten raport z załącznikiem" | `send` | `--to filip --title "Raport" --content-file /tmp/t.md --type task --attach /ścieżka/raport.pdf` |
| "odpisz w wątku abc123 i dorzuć screeny" | `reply` | `--thread-id abc123 --content "..." --attach /ścieżka/1.png --attach /ścieżka/2.png` |

## Wymagania środowiska

- `INBOX_HUB_URL` + `INBOX_TOKEN` — konfiguracja skrzynki zapisana przez instalator Pulsa po wklejeniu kodu zaproszenia. Skill szuka jej w tej kolejności: `INBOX_ENV_FILE` (jawna ścieżka) → `$PULS_HOME/data/inbox.env` → wskaźnik `~/.claude-cron-home` (stała nazwa pliku z katalogiem instalacji, zapisywana przez instalator) i jego `data/inbox.env` → `.env` w workspace (instalacje sprzed przeniesienia sekretu poza vault; czytany, nigdy zapisywany). `PULS_HOME` ustawia instalator w sekcji `env` pliku `{workspace}/.claude/settings.json`, więc działa w sesjach Claude Code z tego workspace'u; wskaźnik ratuje pozostałe procesy. Brak konfiguracji = **re-run instalatora Pulsa**, nigdy ręczne wpisywanie tokenu do pliku w vaulcie (agent auto-reply czyta to drzewo z niezaufanym promptem).
- **Bez `INBOX_USER`** — tożsamość wyprowadza hub z tokenu, klient jej nie deklaruje. Dlatego nie da się wysłać wiadomości „w cudzym imieniu" podmieniając zmienną.
- Zero zależności npm — klient huba (`scripts/inbox/inbox-client.mjs` w repo Pulsa) stoi na wbudowanym `fetch`. **Wszystkie trzy komendy (send/reply/close) wołają skrypty z `$PULS_HOME/scripts/inbox/`** — jedna kopia kodu, objęta `npm test` repo (lokalne kopie skryptów w vaultcie rozjeżdżały się z repo, dlatego ich nie ma).

## Co NIE robić

- Nie zgaduj treści — jeśli user nie powiedział co przekazać, zapytaj.
- Nie wysyłaj duplikatów — jeśli user potwierdza już wysłaną delegację, tylko poinformuj o statusie.
- **Nie edytuj `Skrzynka.md` ręcznie** — hub jest source of truth, pull-job renderuje plik co 1 min. Jedyny wyjątek: odhaczenie „Pobierz” przy załączniku (patrz „Odbieranie załączników”).
- Nie myl `task` z `query` — jeśli user pyta o coś, to query (nie zadanie do wykonania).
- **Nie odhaczaj „Zrobione” za usera** — to wysyła potwierdzenie i zamyka wątek; gdy user każe zamknąć wątek, użyj `close`. „Pobierz” możesz odhaczyć sam (akcja lokalna), ale nie ogłaszaj pobrania, zanim plik nie pojawi się na dysku.
- **Nie obchodź limitu 25 MB** dzieleniem pliku ani kompresją bez pytania — powiedz userowi i zapytaj, co dalej.

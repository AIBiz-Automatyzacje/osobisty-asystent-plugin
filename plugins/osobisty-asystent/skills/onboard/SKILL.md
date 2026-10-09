---
name: onboard
description: Jednorazowy wizard setup Osobistego Asystenta AI — imię i forma zwracania się, wywiad, generacja persona.md, soul.md, opcjonalnie biznes.md i content/voice-of-tone.md, zawsze content/ai-writing-patterns.md, struktura folderów, CLAUDE.md. Tryb --refresh-theme odświeża same snippety CSS (motyw Skrzynki i Dashboardu) na już skonfigurowanym systemie
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Edit", "Glob", "Bash", "AskUserQuestion"]
---

# Onboard — Setup Osobistego Asystenta AI

Jednorazowy wizard, który prowadzi usera przez konfigurację Personal OS. Wywiad → generacja plików kontekstowych → struktura folderów → CLAUDE.md.

**Czas:** ~10-15 minut
**Dla kogo:** każdy, także osoba nietechniczna — pytania i przykłady nie zakładają programowania ani tworzenia treści
**Wynik:** persona.md, soul.md, opcjonalnie biznes.md, CLAUDE.md, struktura folderów

---

## TRYBY WYWOŁANIA

Sprawdź argumenty **zanim** wejdziesz w KROK 0 — tryb `--refresh-theme` celowo omija gateway
(uruchamia się na systemie JUŻ skonfigurowanym, bo tam właśnie motyw się rozjeżdża).

| Wywołanie | Co robi |
|-----------|---------|
| `/onboard` (bez argumentów) | Pełny wizard — kroki 0 → 14 |
| `/onboard --refresh-theme` | **Tylko** odświeżenie motywu (snippety CSS). Zero pytań, zero generacji plików kontekstowych — patrz „TRYB: --refresh-theme" na dole tego pliku |

Nieznany argument → powiedz userowi, jakie tryby istnieją, i **nie** startuj wizardu.

### Wspólny pattern: generacja → review → zapis

Kroki 7, 8, 9 używają tego samego workflow:
1. Wygeneruj plik na podstawie zebranych danych
2. Wyświetl pełną zawartość userowi
3. Zapytaj: "Przeczytaj i powiedz co zmienić."
4. Jeśli user chce zmiany → popraw i pokaż ponownie (bez limitu iteracji)
5. Jeśli user akceptuje → zapisz do docelowej ścieżki (utwórz folder jeśli nie istnieje)

---

## KROK 0: GATEWAY CHECK

1. Sprawdź czy istnieje `.claude/.onboarded`
2. Jeśli **TAK** → wyświetl i STOP:

```
System już skonfigurowany ✅

Pliki kontekstowe: .claude/rules/persona.md, soul.md
Jeśli chcesz zresetować i przejść onboarding od nowa → usuń plik .claude/.onboarded
```

3. Jeśli **NIE** → kontynuuj do kroku 0.5

---

## KROK 0.5: WYKRYCIE ŚRODOWISKA

Wykryj środowisko maszyny RAZ i zapisz wynik — skille korzystają z tego pliku zamiast wykrywać środowisko od nowa w każdej sesji (i od nowa się mylić).

1. Uruchom (Bash):

```bash
UNAME=$(uname -s 2>/dev/null || echo unknown)
case "$UNAME" in
  Darwin) OS="macOS";;
  Linux) OS="Linux";;
  MINGW*|MSYS*|CYGWIN*) OS="Windows";;
  *) OS="$UNAME";;
esac
# Python — pomiń stub MS Store (WindowsApps)
PYTHON=""
for cand in python3 python; do
  p=$(command -v "$cand" 2>/dev/null) || continue
  case "$p" in *WindowsApps*) continue;; esac
  PYTHON="$p"; break
done
PY_VER=$([ -n "$PYTHON" ] && "$PYTHON" --version 2>&1 || echo BRAK)
NODE=$(command -v node 2>/dev/null || echo BRAK)
NODE_VER=$(node --version 2>/dev/null || echo "-")
echo "OS: $OS"
echo "PYTHON: ${PYTHON:-BRAK} ($PY_VER)"
echo "NODE: $NODE ($NODE_VER)"
```

2. Zapisz wynik do `.claude/rules/environment.md` (utwórz folder jeśli trzeba):

```markdown
# Środowisko — wykryte przez /onboard ([dzisiejsza data YYYY-MM-DD])

- **System:** [OS]
- **Python:** `[pełna ścieżka]` ([wersja]) — do skryptów używaj TEJ ścieżki
- **Node:** `[ścieżka]` ([wersja])
```

Jeśli OS = Windows, dopisz na końcu:

```markdown
- ⚠️ **Windows:** `python3` ze Sklepu Microsoft to stub — NIE używaj. Pliki tymczasowe
  zapisuj w `.claude/tmp/` (NIE w `/tmp` — ścieżka MSYS, niewidoczna dla narzędzia Read).
```

3. Jeśli Python = BRAK → poinformuj usera, że część skilli wymaga Pythona (instalacja: https://python.org, na Windows zaznaczyć "Add to PATH") — ale **kontynuuj onboarding**, nie blokuj.

---

## KROK 1: POWITANIE + IMIĘ I FORMA

Wyświetl tekst (NIE AskUserQuestion — to intro):

```
👋 Cześć! Zaraz ustawimy Twojego asystenta AI pod Ciebie.

Co się stanie:
1. Pogadamy — kilka pytań o Ciebie i Twoją pracę (~10-15 min)
2. Zapiszę Twój profil (persona.md) — asystent czyta go na start każdej rozmowy
3. Zapiszę charakter asystenta (soul.md) — jak ma z Tobą rozmawiać
4. Założę foldery i listę zadań w Obsidianie
5. Zapiszę CLAUDE.md — mapę całego systemu

Nie ma złych odpowiedzi, a wszystko da się potem poprawić. Zaczynamy 🚀
```

**Potem pytanie otwarte** (zwykły tekst):

> Jak masz na imię?

Czekaj na odpowiedź. Potem **AskUserQuestion — 2 pytania:**

| # | Pytanie | Header | Opcje (label · description) |
|---|---------|--------|-----------------------------|
| 1 | [Imię], w jakiej formie mam się do Ciebie zwracać? | Forma | **Żeńska** · „zrobiłaś”, „jesteś gotowa” · **Męska** · „zrobiłeś”, „jesteś gotowy” · **Neutralna** · bez form rodzajowych („udało się”, „gotowe”) |
| 2 | A jak asystent ma mówić o sobie? | Asystent | **Męski** · „zrobiłem”, „sprawdziłem” · **Żeński** · „zrobiłam”, „sprawdziłam” · **Neutralny** · bez form rodzajowych („gotowe”, „sprawdzone”) |

`multiSelect: false`

**Od tej chwili WSZYSTKIE pytania i komunikaty wizardu piszesz w wybranej formie** — także
teksty pytań z tego pliku, które są zapisane bezosobowo lub w formie przykładowej (przerób je
w locie), a o sobie mówisz w rodzaju z pytania 2. Form **nie zgaduj z imienia** — pytasz
zawsze. Imię i formę zapisz do kontekstu: trafiają do persona.md (sekcja 1) i obowiązują
asystenta w każdej rozmowie. Rodzaj asystenta trafia do soul.md (KROK 9).

---

## KROK 2: KIM JESTEŚ

**Pytanie otwarte** (zwykły tekst, NIE AskUserQuestion — potrzebna rozbudowana odpowiedź):

> Opowiedz o sobie — czym się zajmujesz, w jakiej firmie i na jakim stanowisku?
> Co jest Twoim głównym zadaniem na co dzień?

Czekaj na odpowiedź. Jeśli zbyt krótka → dopytaj o konkret („Możesz dać przykład typowego zadania?”).

Potem **jedno opcjonalne dopytanie** (zwykły tekst):

> Jeśli chcesz, dopisz, czym zajmowałaś/zajmowałeś się wcześniej zawodowo — pomaga to
> asystentowi dobierać przykłady. Możesz też pominąć.

(Formę w dopytaniu dopasuj do wyboru z kroku 1.) Pominięcie = sekcja „Tło zawodowe” w personie zostaje krótka.

Zapisz odpowiedź do kontekstu (użyjesz w kroku 7).

---

## KROK 3: STYL KOMUNIKACJI

**AskUserQuestion — 4 pytania na raz:**

| # | Pytanie | Header | Opcje (label · description) |
|---|---------|--------|-----------------------------|
| 1 | Jak formalnie ma gadać AI? | Formalność | **Luźno (1-2/5)** · Jak z kumplem, humor, zero dystansu · **Pośrodku (3/5)** · Naturalnie, bez sztywności ale bez wulgaryzmów · **Profesjonalnie (4-5/5)** · Biznesowo, precyzyjnie, z dystansem |
| 2 | Jak podejmujesz decyzje? | Analityczność | **Intuicja** · Czuję co jest dobre, nie potrzebuję danych · **Mix** · Dane tam gdzie ważne, intuicja w reszcie · **Dane i liczby** · Fakty, metryki, porównania — bez tego nie ruszam |
| 3 | Jak wolisz dostawać odpowiedzi? | Format | **Krótko** · Mięso, zero wody · **Z opcjami do wyboru** · 3-5 wariantów z trade-offami · **Z przykładami** · Pokaż na przykładzie, potem teoria · **Szczegółowo** · Pełen kontekst, wyjaśnienia |
| 4 | Jak chcesz feedback od AI? | Feedback | **Prosto w twarz** · Bez owijania, jeśli słabe to słabe · **Konstruktywnie** · Wskaż problem i zaproponuj rozwiązanie · **Delikatnie** · Sugestie zamiast krytyki |

Wszystkie pytania: `multiSelect: false`

Zapisz odpowiedzi do kontekstu.

---

## KROK 4: WARTOŚCI I PRACA

**Pytanie otwarte** (jedno, wieloczęściowe):

> Teraz kilka pytań o to jak pracujesz:
>
> 1. Jakie masz twarde zasady w pracy? Czego ZAWSZE się trzymasz?
>    (np. „odpisuję klientom tego samego dnia”, „najpierw fakty, potem decyzja”)
> 2. Czego NIGDY nie akceptujesz?
>    (np. „obiecywania rzeczy, których nie zrobimy”, „bałaganu w ustaleniach”)
> 3. Z jakich programów i narzędzi korzystasz na co dzień?
>    (np. Facebook, Messenger, Gmail, arkusze Google, Excel, Canva, CRM, telefon)
> 4. Nad czym teraz pracujesz? Jakie są Twoje główne zadania lub projekty?
> 5. W jakie dni i w jakich godzinach zwykle pracujesz?
>    (np. „pon-pt 8:00-16:00”, „różnie, najczęściej popołudniami”)

Jeśli odpowiedź ogólnikowa → dopytaj: "Możesz dać konkretny przykład?"
Odpowiedź z punktu 5 trafia do persona.md (sekcja „Rytm i organizacja pracy”).

Zapisz do kontekstu.

---

## KROK 5: RELACJA Z AI + FRUSTRACJE

**AskUserQuestion — 1 pytanie:**

| # | Pytanie | Header | Opcje (label · description) |
|---|---------|--------|-----------------------------|
| 1 | Jak widzisz AI? | Relacja z AI | **Partner** · Współpracownik na równi, ma opinię, calloutuje błędy · **Narzędzie** · Robisz co mówię, bez inicjatywy · **Mentor** · Prowadzi, uczy, podpowiada kierunek · **Asystent** · Pomaga, wspiera, wykonuje polecenia |

`multiSelect: false`

**Potem pytanie otwarte:**

> Dwa ważne pytania — im szczerzej, tym lepiej AI się do Ciebie dostosuje:
>
> 1. Co Cię WKURZA w AI / chatbotach? Co robią, czego nie znosisz?
>    (np. "zaczyna od Świetne pytanie!", "pisze za dużo", "nie ma opinii")
>
> 2. Jak chcesz żeby TWOJE AI z Tobą rozmawiało? Jaki ton, jaki styl?
>    (np. "jak kumpel", "bez bullshitu", "z humorem", "profesjonalnie ale luźno")

Zapisz do kontekstu.

---

## KROK 6: MOTYWATORY + BLOKERY

**Pytanie otwarte:**

> Ostatnia runda — o Twoją energię:
>
> 1. Przy jakiej pracy czas leci Ci najszybciej? Co daje Ci satysfakcję?
>    (np. „domknięta sprzedaż”, „rozmowa z klientem”, „uporządkowana tabela”)
> 2. Co zabiera Ci najwięcej energii?
>    (np. „powtarzanie tego samego”, „chaos w wiadomościach”, „długie maile”)
> 3. *(opcjonalnie)* Czy jest coś, w czym asystent ma Ci pomagać pilnować się?
>    (np. „odkładam trudne telefony”, „gubię terminy”, „za długo poprawiam”) —
>    możesz pominąć.

Punkt 3 jest opcjonalny: pominięcie = sekcja „Blokery” w personie zostaje pusta. Nie naciskaj.

**Potem AskUserQuestion — 1 pytanie:**

| # | Pytanie | Header | Opcje (label · description) |
|---|---------|--------|-----------------------------|
| 1 | Masz wyniki testów osobowości? | Testy | **Tak, wkleję** · Gallup, MBTI, DISC, cokolwiek — wklej w następnej wiadomości · **Nie mam** · Pomijamy — nie jest wymagane |

`multiSelect: false`

Jeśli "Tak, wkleję" → czekaj na wklejenie wyników. Potem kontynuuj.
Jeśli "Nie mam" → kontynuuj od razu.

---

## KROK 7: GENERACJA persona.md

1. Przeczytaj `prompt-persona.md` z tego skilla (ten sam folder co SKILL.md)
2. Na podstawie WSZYSTKICH odpowiedzi z kroków 2-6 wygeneruj persona.md zgodnie z instrukcjami z prompt-persona.md
3. Zastosuj pattern: generacja → review → zapis (ścieżka: `.claude/rules/persona.md`)

---

## KROK 8: KONTEKST BIZNESOWY (opcjonalny)

**AskUserQuestion — 1 pytanie:**

| # | Pytanie | Header | Opcje (label · description) |
|---|---------|--------|-----------------------------|
| 1 | Chcesz dodać kontekst biznesowy? AI lepiej zrozumie Twój świat zawodowy. | Biznes | **Tak** · Opowiem o firmie/projekcie — AI będzie lepiej dopasowane · **Nie, pomiń** · Dodasz później jeśli będziesz chcieć |

`multiSelect: false`

**Jeśli TAK:**

Pytanie otwarte:

> Opowiedz o swoim biznesie/pracy:
>
> 1. Czym się zajmujesz zawodowo? (firma, branża, model)
> 2. Kto jest Twoim klientem/odbiorcą?
> 3. Na jakich platformach/kanałach działasz?
> 4. Jaki masz stack technologiczny?

Wygeneruj `biznes.md` z sekcjami:
- Działalność (firma, branża, model, skala)
- Grupa docelowa
- Platformy i kanały
- Stack technologiczny
- Aktualne projekty (jeśli wspomniał)

Zastosuj pattern: generacja → review → zapis (ścieżka: `.claude/rules/biznes.md`)

**Jeśli NIE** → pomiń, kontynuuj do kroku 9. Zapamiętaj że biznes.md nie powstał (potrzebne w krokach 12 i 14).

---

## KROK 9: GENERACJA soul.md

**AskUserQuestion — 2 pytania:**

| # | Pytanie | Header | Opcje (label · description) |
|---|---------|--------|-----------------------------|
| 1 | Humor i przeklinanie w AI? | Humor | **Pełen luz** · Humor + przeklinanie kiedy pasuje · **Humor tak, przeklinanie nie** · Luźny ton, ale bez wulgaryzmów · **Profesjonalnie** · Zero humoru w pracy, rzeczowo i na temat |
| 2 | AI ma mieć mocne opinie? | Opinie | **Mocne** · Calloutuje błędy, nie jest yes-manem, mówi wprost · **Wyważone** · Wskazuje lepszą opcję, ale nie narzuca · **Neutralne** · Fakty na stole, user decyduje |

Wszystkie: `multiSelect: false`

**Potem pytanie otwarte:**

> Ostatnie pytanie: opisz swoimi słowami, jaki „charakter” ma mieć Twój asystent.
>
> Na przykład:
> - „jak ogarnięta osoba z biura, która pilnuje terminów i przypomina o sprawach”
> - „jak doświadczony handlowiec, który podpowiada, jak odpisać klientowi”
> - „jak cierpliwy nauczyciel, który tłumaczy krok po kroku, bez trudnych słów”
> - „jak redaktor, który poprawia moje teksty i mówi wprost, co jest słabe”
> - „jak kolega z pracy, z którym można pogadać na luzie”
> - „jak mentor, który nie oszczędza krytyki, ale zawsze ma rozwiązanie”
>
> Albo cokolwiek innego — tu nie ma złej odpowiedzi.

**Generacja:**

1. Przeczytaj `prompt-soul.md` z tego skilla
2. Wygeneruj soul.md na podstawie:
   - persona.md (cały profil wygenerowany w kroku 7)
   - biznes.md (jeśli utworzony w kroku 8)
   - Odpowiedzi z tego kroku (humor, opinie, charakter)
3. Zastosuj pattern: generacja → review → zapis (ścieżka: `.claude/rules/soul.md`)

---

## KROK 9B: VOICE OF TONE (opcjonalny — wymaga próbek)

Plik `content/voice-of-tone.md` opisuje JAK user pisze treści. Tworzymy go **TYLKO** jeśli
user pisze content **I dostarczy próbki** — bez realnych tekstów byłby zmyślony i bezużyteczny.

**AskUserQuestion — 1 pytanie:**

| # | Pytanie | Header | Opcje (label · description) |
|---|---------|--------|-----------------------------|
| 1 | Tworzysz treści (posty, maile, wpisy) i chcesz, żeby AI pisało Twoim głosem? | Voice | **Tak, mam próbki** · Wkleję 5-15 swoich tekstów — AI wyłapie styl · **Tak, ale później** · Tworzę content, dorzucę próbki kiedy indziej · **Nie tworzę treści** · Pomiń — nie dotyczy mnie |

`multiSelect: false`

**Jeśli "Tak, mam próbki":**
1. Poproś: *"Wklej 5-15 swoich tekstów (posty/maile/wpisy) — im więcej, tym lepiej AI złapie styl."*
2. Czekaj na wklejenie. Jeśli <5 próbek → poproś o więcej albo zaproponuj wariant "później".
3. Przeczytaj `prompt-voice-of-tone.md` z tego skilla.
4. Wygeneruj `content/voice-of-tone.md` zgodnie z instrukcją z prompta.
5. Pattern: generacja → review → zapis (ścieżka: `.claude/rules/content/voice-of-tone.md`).

**Jeśli "Tak, ale później" lub "Nie tworzę treści":**
Pomiń. Zapamiętaj, że voice-of-tone NIE powstał (potrzebne w kroku 12). Jeśli "później" →
powiedz: *"Spoko — skill `/reflect` zbuduje go z czasem z Twoich tekstów."*

**NIEZALEŻNIE od odpowiedzi (zawsze, bez pytania):**
Skopiuj `templates/ai-writing-patterns.md` z tego skilla do `.claude/rules/content/ai-writing-patterns.md`
(`mkdir -p` na folder). To uniwersalny, statyczny dokument referencyjny (wzorce usuwania artefaktów AI
z polskich tekstów) — NIE jest personalizowany i NIE zależy od voice-of-tone. Kopiuj 1:1, BEZ
dopisywania frontmattera `paths` — ma ładować się zawsze (każdy mail i wiadomość to tekst dla odbiorcy).
*(Plik zasiewa też hook `seed-base-files` przy starcie sesji, gdyby onboarding był pomijany.)*

---

## KROK 10: STRUKTURA FOLDERÓW

**Utwórz automatycznie (bez pytania):**

```
Zadania/
├── Dashboard.md          ← skopiuj z templates/Dashboard.md, zamień {{DATE}} na dzisiejszą datę YYYY-MM-DD
├── projekty/             ← notatki projektowe (nie zadania)
├── zrobione/             ← archiwum odhaczonych (/daily dopisuje zrobione/YYYY-MM.md)
└── cykliczne/
    └── recurring.md      ← skopiuj z templates/recurring.md

Zasoby/

.obsidian/snippets/
├── dashboard-todo.css    ← skopiuj z templates/dashboard-todo.css
└── skrzynka.css          ← skopiuj z templates/skrzynka.css
```

Pliki template'ów: przeczytaj z folderu `templates/` w tym skillu i skopiuj do docelowych lokalizacji.

**Snippety CSS (wygląd systemu zadań):** po skopiowaniu obu plików do `.obsidian/snippets/`
dopisz `"dashboard-todo"` i `"skrzynka"` do listy `enabledCssSnippets` w `.obsidian/appearance.json`
(utwórz plik z `{"enabledCssSnippets": ["dashboard-todo", "skrzynka"]}`, jeśli nie istnieje).
Jeśli plik już istnieje — **dopisz brakujące wpisy do istniejącej listy**, nie podmieniaj jej
(user ma tam własne snippety). Jeśli Obsidian jest otwarty, użytkownik może musieć odświeżyć
listę: Ustawienia → Wygląd → Fragmenty CSS → ikona odświeżania.

**⚠️ Wymagana wersja Obsidiana — sprawdź i powiedz userowi wprost.**
Snippet `skrzynka.css` stoi na selektorze CSS `:has()` (13 użyć), który działa dopiero
na silniku Chromium 105+. Na starszym Obsidianie karty Skrzynki renderują się jako surowe
callouty — awatary na tekście, brak kart, checkbox przyklejony. To nie jest błąd snippetu
i **nie naprawia się go przepisywaniem CSS**: lekarstwem jest aktualizacja Obsidiana.

1. Poproś usera o sprawdzenie: **Ustawienia → Ogólne → Sprawdź aktualizacje** (wersja aplikacji
   jest w tym samym miejscu; na Obsidianie ≥ 1.4 problem nie występuje).
2. Wypisz jedną linię śladu: `✅ Obsidian zaktualizowany — potwierdzone przez usera` albo
   `⚠️ Obsidian nieaktualny — Skrzynka będzie wyglądać surowo do czasu aktualizacji`.
3. Nie blokuj onboardingu — reszta systemu działa niezależnie od wersji.

**Uwaga (Team OS):** markery `%% inbox:banner %%` w Dashboardzie i plik `Zadania/Skrzynka.md`
obsługuje Puls (claude-cron) — Skrzynkę tworzy sam przy pierwszym runie joba inbox (self-heal),
NIE twórz jej ręcznie. Bez Pulsa markery są niewidoczne w Obsidianie i niczemu nie przeszkadzają.
Jak działa Skrzynka — patrz „Skrzynka Team OS — flow" na dole tego pliku.

**AskUserQuestion — 1 pytanie, multiSelect:**

| # | Pytanie | Header | multiSelect | Opcje (label · description) |
|---|---------|--------|-------------|-----|
| 1 | Jakie dodatkowe foldery chcesz? | Foldery | true | **Marketing/** · Wpisy i grafiki — do contentu i social media · **Notatki/** · Spotkania, rozmowy, braindumpy · **Brudnopis.md** · Szybkie notatki, scratch pad — jeden plik na wszystko |

Utwórz wybrane:
- `Marketing/` → utwórz subfoldery: `wpisy/` i `media/`
- `Notatki/` → utwórz subfoldery: `spotkania/`
- `Brudnopis.md` → pusty plik z nagłówkiem `# Brudnopis`

Zapamiętaj co zostało utworzone (potrzebne w kroku 12).

**Voice-of-tone a `Marketing/`:** jeśli w kroku 9B powstał `.claude/rules/content/voice-of-tone.md`
ORAZ user wybrał `Marketing/` → dopisz na początek pliku frontmatter:

```yaml
---
paths:
  - "Marketing/**/*"
---
```

Wtedy styl pisania ładuje się sam tylko przy pracy w `Marketing/` (poza nim — na żądanie, patrz
tabela on-demand w CLAUDE.md). Bez `Marketing/` plik zostaje bez frontmattera i ładuje się zawsze.

---

## KROK 11: PRZEGLĄD SKILLI

**Wyświetl tekst (bez pytań):**

```
📦 Twój system ma 7 wbudowanych skilli — działają od razu:

/daily            — codzienne porządki: archiwizacja zrobionych zadań,
                    regeneracja dashboardu, raport co nowego
/memory-update    — aktualizuje NOW.md (bieżący kontekst pracy) z logów
                    sesji — dzięki temu AI wie nad czym pracujesz
/reflect          — odpal po sesji, AI analizuje rozmowę i kalibruje
                    Twoje pliki kontekstowe (persona.md, soul.md, voice-of-tone.md)
/utworz-zadanie   — dopisuje zadanie do Dashboardu: nazwa, priorytet,
                    termin (możesz też dopisać linię ręcznie)
/koniec-sesji     — na koniec pracy nad projektem zapisuje, gdzie skończyłeś,
                    i daje prompt do wklejenia na start następnej sesji
/skill-scout      — raz w tygodniu przegląda Twoje logi i wyławia powtarzalną
                    ręczną robotę, którą warto opakować w kolejny skill
/kie-generate     — grafiki i wideo AI (wymaga klucza Kie.ai — powiedz
                    „skonfiguruj kie-generate”, gdy będziesz chciał zacząć)

Wszystkie działają od razu — wystarczy wpisać /nazwa w Claude Code.
Dodatkowe skille (email, social media...) to osobny
materiał — możesz je doinstalować w dowolnym momencie.
```

---

## KROK 12: GENERACJA CLAUDE.md

1. Przeczytaj `template-claude.md` z tego skilla
2. Wypełnij placeholder'y:

**{{RULES_LIST}}** — tabela z plikami w `.claude/rules/`:

| Plik | Opis | Kiedy się ładuje |
|------|------|-----------------|
| `rules/persona.md` | Profil użytkownika, styl komunikacji, wartości | Zawsze |
| `rules/soul.md` | Osobowość AI, charakter, styl myślenia | Zawsze |
| `rules/environment.md` | Wykryte środowisko maszyny (OS, Python, node) | Zawsze |
| `rules/NOW.md` | Bieżący kontekst pracy (tworzy i aktualizuje `/memory-update`) | Zawsze |
| `rules/biznes.md` | Kontekst biznesowy (firma, branża, stack, platformy) | Zawsze |
| `rules/content/voice-of-tone.md` | Styl pisania treści (posty, maile) | Przy pracy w `Marketing/**` (frontmatter `paths`); bez `Marketing/` — zawsze |
| `rules/content/ai-writing-patterns.md` | Wzorce usuwania artefaktów AI z tekstów | Zawsze; stosowany przy self-checku gotowego tekstu |

Wiersz NOW.md wpisuj ZAWSZE, nawet jeśli plik jeszcze nie istnieje —
powstanie przy pierwszym `/memory-update`.
Pomiń wiersz `rules/biznes.md` jeśli user nie utworzył go w kroku 8.
Pomiń `content/voice-of-tone.md` jeśli nie został utworzony w kroku 9B.
Wiersz `content/ai-writing-patterns.md` wpisuj ZAWSZE (plik kopiowany bezwarunkowo w kroku 9B / seed hookiem).

**{{ON_DEMAND}}** — akapit + tabela, co czytać jawnie (Read) w jakiej sytuacji:

```
`ai-writing-patterns.md` stosujesz na etapie self-checku gotowego draftu — wczytany jako wzór
PRZED pisaniem podsuwa frazy, których ma pilnować.
[TYLKO gdy voice-of-tone ma `paths`:] `rules/content/voice-of-tone.md` ładuje się sam przy pracy
na ścieżkach `Marketing/**`; poza `Marketing/` wczytujesz go jawnie wg tabeli.

| Sytuacja | Wczytaj (Read) |
|----------|----------------|
| Poprawiasz/piszesz JAKIKOLWIEK tekst użytkownika | `rules/content/ai-writing-patterns.md` (self-check draftu) |
| Mail lub wiadomość do klienta/partnera | `rules/content/ai-writing-patterns.md` |
| Post, wpis, reklama poza `Marketing/` [TYLKO gdy voice-of-tone ma `paths`] | + `rules/content/voice-of-tone.md` |
```

Nie ma voice-of-tone → pomiń zdanie i wiersz o nim.

**{{SKILLS_LIST}}** — lista 7 skilli core:

```
**Workflow / Zarządzanie:**
- `daily` - codzienna aktualizacja systemu zadań (archiwizacja, regeneracja dashboardu, raport)
- `memory-update` - aktualizacja NOW.md (bieżący kontekst pracy) z logów sesji
- `reflect` - walidacja obserwacji o użytkowniku → aktualizacja plików kontekstowych
- `utworz-zadanie` - tworzenie nowego zadania w systemie Obsidian
- `koniec-sesji` - zapis stanu projektu do `_KONTEKST.md` + prompt wznowieniowy
- `skill-scout` - tygodniowy przegląd logów: wykrywa powtarzalną ręczną robotę do opakowania w skill
- `kie-generate` - grafiki i wideo AI przez Kie.ai (klucz w `.env`, brand w `.claude/kie-brand.md`)
```

**{{FOLDER_STRUCTURE}}** — mapa workspace na podstawie FAKTYCZNIE utworzonych folderów:

```
- `.claude/` - konfiguracja Claude Code
- `Zadania/` - system zarządzania zadaniami
  - `Dashboard.md` - lista zadań (jedno zadanie = jedna linia)
  - `projekty/` - jeden folder na projekt; stan projektu w `projekty/<projekt>/_KONTEKST.md` (prowadzi go `/koniec-sesji`)
  - `notatki/` - szczegóły do zadań (kontakt, dane, kroki), linkowane z linii zadania jako 📎; folder powstaje przy pierwszej notatce
  - `zrobione/` - archiwum wykonanych zadań (`YYYY-MM.md`)
  - `cykliczne/recurring.md` - zadania cykliczne
- `Zasoby/` - baza wiedzy: tu zapisujesz wszystko, co user podsyła do zachowania (linki, artykuły, transkrypcje filmów, research, materiały) i stąd odpowiadasz na pytania o te materiały. Domyślne miejsce zapisu, gdy user nie wskaże innego
```

Dodaj `Marketing/`, `Notatki/`, `Brudnopis.md` jeśli zostały wybrane w kroku 10.

**{{CONVENTIONS}}** — konwencje systemu:

```
- Pliki markdown w formacie Obsidian
- Checkboxy w formacie `- [ ]` / `- [x]`

### System zadań

- **Zadanie = jedna linia w `Zadania/Dashboard.md`:** `- [ ] Nazwa — 🔴 · DD.MM` — dodawaj przez `/utworz-zadanie` albo ręcznie; `/daily` archiwizuje odhaczone i przestawia sekcje wg terminu
- **Priorytety:** 🔴 pilne | 🟡 wazne | 🟢 normalne
- **Bez plików zadań** — notatka w `Zadania/notatki/` z linkiem 📎 w linii tylko wtedy, gdy są szczegóły do zachowania (kontakt, dane, kroki)
```

3. Zapisz do `.claude/CLAUDE.md`
4. Wyświetl krótkie podsumowanie: "CLAUDE.md wygenerowany — zawiera rules, skille, strukturę folderów i konwencje."

---

## KROK 13: SPRAWDZENIE PLIKÓW

Sprawdź, czy każdy folder wymieniony w CLAUDE.md istnieje i czy router wskazuje wszystkie utworzone pliki z `.claude/rules/`; braki uzupełnij. Treści persona.md i soul.md po akceptacji nie zmieniaj — rozjazd między nimi zgłoś userowi.

**Ślad walidacji jest OBOWIĄZKOWY** — po wykonaniu checków wypisz userowi wynik,
jedna linia per check (`✅ persona ↔ soul — spójne` / `⚠️ Anty-wzorce — dopisałem 2 punkty do soul.md`).
Bez wypisanego śladu NIE przechodź do kroku 14.

---

## KROK 14: FINALIZACJA

1. Zapisz flagę `.claude/.onboarded`:

```
onboarded: true
date: [dzisiejsza data YYYY-MM-DD]
version: 1.0
```

2. Wyświetl podsumowanie:

```
✅ Personal OS skonfigurowany!

Utworzone pliki:
📄 .claude/rules/persona.md — Twój profil
📄 .claude/rules/soul.md — osobowość AI
📄 .claude/rules/environment.md — środowisko maszyny (OS, Python, node)
📄 .claude/rules/biznes.md — kontekst biznesowy [TYLKO jeśli utworzony]
📄 .claude/rules/content/voice-of-tone.md — styl pisania treści [TYLKO jeśli utworzony]
📄 .claude/rules/content/ai-writing-patterns.md — wzorce unikania "AI voice" w tekstach
📄 .claude/CLAUDE.md — router systemu
📁 Zadania/ — lista zadań (Dashboard) i zadania cykliczne
📁 Zasoby/ — materiały
📁 [dodatkowe foldery jeśli wybrane]

Co dalej:
1. Pogadaj z AI o czymkolwiek — poczuj różnicę w stylu
2. Po kilku sesjach odpal /reflect — AI się skalibruje
3. Wpisz /daily rano — system posprząta i pokaże co na dziś
```

Pomiń linijkę z biznes.md jeśli nie został utworzony.

---

## Constraints

- **Jednorazowy** — po zapisaniu `.onboarded` skill się blokuje (krok 0)
- **Nie wymyślaj** — persona i soul bazują TYLKO na odpowiedziach usera
- **Review obowiązkowy** — persona.md i soul.md MUSZĄ być pokazane userowi do akceptacji przed zapisem
- **Iteracja** — jeśli user chce zmiany → popraw i pokaż ponownie, bez limitu iteracji
- **Templates z tego skilla** — pliki do Zadania/ kopiuj z `templates/` w tym skillu, NIE twórz od zera.
  Pliki `.md` kopiuj przez Read + Write, nie `cp` — niektóre pluginy (np. hook `md-guard`) blokują
  zapis `.md` przez Bash. Pliki `.css` i `.json` możesz kopiować `cp`
- **Foldery** — twórz wszystkie potrzebne foldery automatycznie (mkdir -p)
- **Język** — pisz w języku w jakim mówi user (jeśli po polsku → wszystko po polsku)

---

## Skrzynka Team OS — flow

Kontekst dla usera i dla Ciebie, gdy ktoś pyta „skąd się bierze Skrzynka" albo „czemu moje
odhaczenie zniknęło". Sama Skrzynka **nie jest** produktem tego skilla — generuje ją Puls
(claude-cron). Onboarding dostarcza tylko **motyw** (snippety CSS).

**Co się dzieje co minutę** — script-job Pulsa „Team OS — inbox sync" robi `push` → `pull`
w jednym procesie (kolejność jest istotna: najpierw wysyła Twoje odhaczenia, dopiero potem
przerysowuje plik):

| Krok | Co robi | Czego dotyka |
|------|---------|--------------|
| `push` | Czyta **odhaczone** checkboxy z sekcji „Otrzymane". `- [x] Zrobione` (zadanie) → zgłasza wykonanie do huba, nadawca dostaje potwierdzenie. `- [x] Zapoznane` (pytanie/odpowiedź) → domyka wątek bez odpowiedzi. Zamkniętą nitkę dopisuje do archiwum | `Zadania/Skrzynka.md` (odczyt), `Zasoby/inbox-archive/YYYY-MM.md` (zapis, jeden blok na wątek — ponowne domknięcie **podmienia** blok, nie dokłada duplikatu) |
| `pull` | Pobiera aktywne wątki z huba i **przepisuje w całości** bloki między markerami: `%% inbox:items:start/end %%` (Otrzymane) i `%% delegated:items:start/end %%` (Wysłane). Każdy wątek = jedna zwijana karta z nitką wiadomości i JEDNYM checkboxem. Brakujące klucze frontmattera (w tym `cssclasses: [skrzynka]`) domergowuje przy każdym przebiegu — wartości już obecne zostawia nietknięte. Zapisuje **tylko przy realnej zmianie treści** | `Zadania/Skrzynka.md` (blok między markerami + frontmatter), `Zadania/Dashboard.md` (banner top 3 między `%% inbox:banner:start/end %%`) |

**Co robi user:** odhacza checkbox w karcie. Tyle. Odpowiadanie i delegowanie idzie przez
skill `/deleguj`.

**Czego user NIE powinien ruszać:** markerów `%% … %%` (bez nich job nie wie, gdzie pisać —
i przestaje aktualizować sekcję), linii `%% id:… thread:… %%` pod checkboxem (identyfikuje
wiadomość) ani treści między markerami — jest regenerowana i ręczne zmiany znikną przy
najbliższym przebiegu. Reszta pliku (własne notatki poza blokami) jest bezpieczna.

**Motyw i renderer to para.** Snippet `skrzynka.css` stylizuje dokładnie te klasy, które emituje
renderer Pulsa; rozjazd wersji psuje wygląd na maszynie, która ma starszy plik. Puls pilnuje tego
sam — job „Puls — kontrola spójności" porównuje snippet w vaultcie z szablonem w tym skillu
i przy różnicy wystawia zadanie z komendą naprawczą `/onboard --refresh-theme`.

---

## TRYB: `--refresh-theme`

Wywołanie: `/onboard --refresh-theme`. Odświeża **wyłącznie motyw**. Uruchamiaj bez pytań
wstępnych i **bez** gateway checku z KROKU 0 — ten tryb z definicji działa na systemie już
skonfigurowanym.

**Kroki:**

1. Skopiuj z `templates/` do `.obsidian/snippets/`, **nadpisując**:
   - `dashboard-todo.css`
   - `skrzynka.css`
2. Upewnij się, że `.obsidian/appearance.json` ma `"dashboard-todo"` i `"skrzynka"` w liście
   `enabledCssSnippets` — **dopisz brakujące**, nie podmieniaj listy (user ma tam własne snippety).
   Brak pliku → utwórz z `{"enabledCssSnippets": ["dashboard-todo", "skrzynka"]}`.
3. Jeśli `Zadania/Skrzynka.md` istnieje i **nie ma** klucza `cssclasses` we frontmatterze —
   dopisz `cssclasses: [skrzynka]`. Klucz już obecny zostaw **nietknięty**, nawet gdy ma inną
   wartość (user mógł dołożyć własne klasy). Bez pliku → pomiń; Puls dopisze klucz sam przy
   najbliższym syncu.
4. Powiedz userowi, żeby przeładował snippety: Ustawienia → Wygląd → Fragmenty CSS → ikona
   odświeżania. Jeśli karty dalej wyglądają surowo — to wersja Obsidiana (patrz KROK 10,
   wymaganie `:has()` / Chromium 105+), nie snippet.
5. Wypisz ślad: które pliki nadpisałeś, co dopisałeś do `appearance.json`, czy `cssclasses`
   było już na miejscu.

**Czego ten tryb NIE dotyka** (mów to userowi, gdy pyta, czy jest bezpieczny):

- treści `Zadania/Skrzynka.md` — wiadomości, odhaczone checkboxy i markery zostają,
- archiwum `Zasoby/inbox-archive/`, Dashboardu, zadań ani żadnego pliku w `Zadania/`
  poza ewentualnym jednym kluczem frontmattera z punktu 3,
- plików kontekstowych (`persona.md`, `soul.md`, `CLAUDE.md`, `voice-of-tone.md`),
- flagi `.claude/.onboarded` — tryb jej nie tworzy i nie kasuje.

**Świadomy koszt:** punkt 1 **nadpisuje** snippety, więc ręczne przeróbki CSS w vaultcie
przepadają. Jeśli user takie ma — powiedz o tym **przed** kopiowaniem i pozwól mu zrobić kopię.

---
name: kie-generate
description: Generuje grafiki I WIDEO AI przez Kie.ai — grafiki (Nano Banana 2 / Nano Banana Pro / GPT Image 2.5) oraz wideo/animacje czterema silnikami do wyboru i porównania (Kling 3.0, Seedance 2.0, Seedance 2.5 do 30 s, MiniMax H3; text-to-video i image-to-video z first/end frame). Używaj gdy user chce wygenerować grafikę, obrazek, wideo, animację, klip, rolkę AI, ożywić grafikę, zrobić seamless loop, animować postać/pixel-art albo porównać kilka modeli wideo na tym samym promptcie. Interaktywnie pyta o prompt i parametry, zapisuje do folderu na grafiki w workspace lub wskazanej lokalizacji.
allowed-tools: ["Bash", "Read", "Write", "Glob"]
---

# Kie Generate

Skill do generowania grafik AI przez API Kie.ai.

## Wybór modelu

Domyślnie używaj **GPT Image 2.5 Sunburst** (`gpt-image-2.5` → `gpt-image-2-5-sunburst-*` w API Kie) — wariant „optimized for quality”, wyższa jakość niż GPT Image 2, ta sama cena co Flare, wolniejszy. Skrypt automatycznie wybiera text-to-image lub image-to-image w zależności od tego czy podano `--image`. **Flare** (`gpt-image-2.5-flare`) to mniejszy, szybszy wariant o jakości GPT Image 2 — używaj tylko gdy user prosi o szybkość albo robi wiele iteracji roboczych. GPT Image-2 (2.0) wycofany 15.09.2026.

Przełączaj się tylko gdy user wprost o to poprosi:

| User mówi | Przekaż `--model` |
|-----------|-------------------|
| (nic, default) | `gpt-image-2.5` (Sunburst) |
| "flare", "szybko", "szybszy model", "robocza wersja" | `gpt-image-2.5-flare` |
| "Nano", "Nano Banana", "banana" | `nano-banana-2` |
| "pro", "wyższa jakość", "lepiej" | `nano-banana-pro` |

**GPT Image 2.5 ograniczenia:** brak `--format` (API go ignoruje), krótsza lista ratio (bez 1:4, 1:8, 4:1, 8:1). `--resolution` 1K/2K/4K działa (cennik: 1K $0.03, 2K $0.05, 4K $0.08). Skrypt sprawdza magic bytes odpowiedzi: przy rozjeździe bezpiecznie zmienia rozszerzenie, a z `--strict-format` przerywa bez zapisu. Jeśli format ma być gwarantowany (np. PNG do dalszego kroku), przełącz na `nano-banana-2` i użyj `--strict-format`.

## Wymagania

W `.env` workspace'u:

| Zmienna | Opis | Tryby |
|---------|------|-------|
| `KIE_API_KEY` | Klucz API Kie.ai (kie.ai) | wszystkie |
| `IMGBB_API_KEY` | Klucz API ImgBB (imgbb.com/api) — temporary hosting reference images | `edit`, `compose`, `remove-bg` |

Biblioteki Python: `requests`.

**Pierwsza konfiguracja:** jeśli user prosi o "setup", "konfigurację", "onboarding kie-generate" — przeprowadź go przez checklistę z [ONBOARDING.md](ONBOARDING.md).

## Tryby pracy

| Tryb | Opis | Kiedy użyć |
|------|------|------------|
| `generate` | text → image | Nowa grafika od zera |
| `edit` | image + instruction → image | Modyfikacja istniejącej grafiki |
| `compose` | multiple images + instruction → image | Łączenie elementów z kilku obrazków |
| `remove-bg` | image → image (transparent) | Usunięcie tła z grafiki |

## Workflow

1. **Rozpoznaj tryb** na podstawie inputu użytkownika:
   - Brak obrazków → `generate`
   - 1 obrazek + instrukcja edycji → `edit`
   - 2+ obrazków + instrukcja → `compose`
   - Użytkownik prosi o usunięcie tła → `remove-bg`

2. **Zapytaj o szczegóły** (jeśli nie podane):
   - Co ma być na grafice? (prompt)
   - Proporcje? (domyślnie 1:1, dla social media często 16:9)
   - Rozdzielczość? (1K/2K/4K, domyślnie 1K)
   - Gdzie zapisać? (domyślnie wg sekcji „Domyślna lokalizacja”)

3. **Zbuduj prompt** według zasad z [prompting-guide.md](prompting-guide.md):
   - 7-elementowa struktura (styl, scena, subject, kamera, światło, tekstury, negacje)
   - Blok `TEXT CONTENT TO DISPLAY` jeśli są konkretne teksty — napisy generuje się razem z grafiką

4. **Zastosuj brand**, jeśli grafika dotyczy marki usera i w workspace istnieje `.claude/kie-brand.md` (tworzy go onboarding skilla) — wczytaj go i trzymaj się kolorów, stylu i listy „czego unikać”. Pliku nie ma → generuj bez brandu.

5. **Wywołaj skrypt** i poinformuj o wyniku

## Użycie skryptu

> **Cross-platform Python:** Przed uruchomieniem skryptów ustaw interpreter (na Windows `python3` to stub ze Sklepu Microsoft):
> ```bash
> PYTHON=""
> for cand in python3 python; do
>   p=$(command -v "$cand" 2>/dev/null) || continue
>   case "$p" in *WindowsApps*) continue;; esac
>   PYTHON="$p"; break
> done
> [ -z "$PYTHON" ] && PYTHON=python
> ```

```bash
# Generate (text → image) — domyślnie GPT Image 2.5
$PYTHON {baseDir}/scripts/kie_image.py generate "prompt" output.png
$PYTHON {baseDir}/scripts/kie_image.py generate "prompt" output.png --ratio 16:9 --resolution 2K --task-file task.json

# Generate z Nano Banana Pro (starszy model)
$PYTHON {baseDir}/scripts/kie_image.py generate "prompt" output.png --model nano-banana-pro

# Generate / edit z GPT Image 2.5 (skrypt sam wybiera text-to-image vs image-to-image)
$PYTHON {baseDir}/scripts/kie_image.py generate "prompt" output.png --model gpt-image-2.5 --ratio 16:9 --resolution 2K
$PYTHON {baseDir}/scripts/kie_image.py edit "instruction" output.png --image input.png --model gpt-image-2.5

# Edit (image + instruction → image)
$PYTHON {baseDir}/scripts/kie_image.py edit "instruction" output.png --image input.png

# Compose (multiple images → image)
$PYTHON {baseDir}/scripts/kie_image.py compose "instruction" output.png --image img1.png --image img2.png

# Remove background
$PYTHON {baseDir}/scripts/kie_image.py remove-bg input.png output.png

# Odzysk obrazu po przerwanym pollingu — nie tworzy drugiego taska
$PYTHON {baseDir}/scripts/kie_image.py recover <task_id> output.png
$PYTHON {baseDir}/scripts/kie_image.py recover --task-file task.json
```

## Parametry

| Parametr | Opcje | Domyślnie |
|----------|-------|-----------|
| `--model` | nano-banana-2, nano-banana-pro, gpt-image-2.5 (Sunburst), gpt-image-2.5-flare | gpt-image-2.5 |
| `--ratio` | 1:1, 1:4*, 1:8*, 2:3, 3:2, 3:4, 4:1*, 4:3, 4:5, 5:4, 8:1*, 9:16, 16:9, 21:9, auto | 1:1 |
| `--resolution` | 1K, 2K, 4K | 1K |
| `--format` | png, jpg | png |
| `--task-file` | ścieżka JSON; atomowy zapis task_id przed pollingiem | brak |
| `--strict-format` | przerwij bez zapisu, gdy magic bytes ≠ rozszerzenie | off |

*\* Proporcje 1:4, 1:8, 4:1, 8:1 — dostępne tylko w Nano Banana 2*
*\* GPT Image 2.5 ignoruje `--format`; ratio musi być z listy: auto, 1:1, 5:4, 9:16, 21:9, 16:9, 4:3, 3:2, 4:5, 3:4, 2:3*

## Proporcje - kiedy które

| Proporcja | Użycie |
|-----------|--------|
| `1:1` | Instagram post, avatar |
| `16:9` | YouTube thumbnail, banner, X post |
| `9:16` | Instagram/TikTok story, reel |
| `4:3` | Prezentacja |

## Domyślna lokalizacja

Folder zapisu (sprawdź w tej kolejności, ścieżki względne od głównego folderu workspace'u):
1. `KIE_OUTPUT_DIR` z `.env` workspace'u (`grep -E '^KIE_OUTPUT_DIR=' .env`), jeśli ustawione,
2. `Marketing/media/`, jeśli taki folder istnieje,
3. w przeciwnym razie `media/` (utwórz przy pierwszym zapisie, `mkdir -p`).

Nazwy opisowe, np. `post-automatyzacja-2026-01-23.png`, `infografika-korzysci-ai.png`.

## Jak działa upload reference images

Dla trybów `edit`, `compose`, `remove-bg` Kie.ai wymaga publicznego URL-a dla inputowych obrazków. Skrypt uploaduje plik do **ImgBB** (TTL 1h, auto-delete), dostaje publiczny URL i przekazuje go do API. Limit: **32 MB** na plik. Retry 3× z exponential backoff przy błędach 5xx/sieci. Tryb `generate` nie używa ImgBB i nie wymaga `IMGBB_API_KEY`.

## Obsługa błędów

**Kie.ai:**

| Kod | Znaczenie |
|-----|-----------|
| 401 | Sprawdź `KIE_API_KEY` |
| 402 | Brak środków na koncie Kie.ai |
| 429 | Rate limit — poczekaj |

**ImgBB:**

| Sytuacja | Rozwiązanie |
|----------|-------------|
| `IMGBB_API_KEY not configured` | Dodaj klucz do `.env` (imgbb.com/api) |
| `File too large: X MB (limit 32 MB)` | Skompresuj lub zmniejsz rozdzielczość przed uploadem |
| `ImgBB upload failed after 3 attempts` | Problem sieci/API ImgBB — spróbuj ponownie za chwilę |

---

## Wideo — Kling 3.0 · Seedance 2.0 · Seedance 2.5 · MiniMax H3

Do generowania wideo i animacji służy osobny skrypt `scripts/kie_video.py` (ten sam flow API co grafiki: createTask → recordInfo → download). Wymaga tylko `KIE_API_KEY` — obrazy wejściowe uploaduje przez natywny magazyn kie.ai (nie ImgBB).

Cztery silniki za jednym interfejsem — po to, żeby ten sam prompt puścić kilkoma modelami i porównać wynik:

| `--model` | Model w API | Sterowanie jakością | Dźwięk | Uwagi |
|-----------|-------------|---------------------|--------|-------|
| `kling` (default) | `kling-3.0/video` | `--mode std/pro/4K` | tak | 3-15 s, aspect 16:9 / 9:16 / 1:1 |
| `seedance` | `bytedance/seedance-2` | `--resolution 480p/720p/1080p/4k` | tak | 4-15 s, aspect też 4:3, 21:9, `adaptive` |
| `seedance25` | `bytedance/seedance-2-5` | `--resolution 480p/720p` | tak | **4-30 s** — jedyny silnik z klipami dłuższymi niż 15 s; aspect domyślnie `adaptive`, obraz do 30 MB. Cena beta: 720p ~$0.315/s bez wideo wejściowego |
| `minimax` | `minimax-h3/image-to-video`<br>`minimax-h3/text-to-video` | `--resolution 768P/2K` | nie | 4-15 s, obraz do 30 MB; **i2v nie przyjmuje `--aspect-ratio`** (kadr bierze z klatki) |

`kie_video.py models` wypisuje tę ściągę w terminalu, bez wywoływania API.

Skrypt waliduje kombinacje przed wysłaniem taska — `--mode` przy Seedance, `--resolution` przy Klingu czy `--sound` przy MiniMaksie kończą się czytelnym błędem, a nie spalonym zleceniem. Różnice, które builder ukrywa: Kling bierze klatki jako listę `image_urls`, pozostałe dwa jako osobne `first_frame_url` / `last_frame_url`; `duration` to string w Klingu, a integer w reszcie.

**Porównanie silników na jednym promptcie:**

```bash
for M in kling seedance seedance25 minimax; do
  $PYTHON {baseDir}/scripts/kie_video.py image-to-video "opis ruchu" out_$M.mp4 \
    --model $M --first sprite.png --end sprite.png --duration 5 &
done; wait
```

### Kiedy używać

| User mówi | Komenda |
|-----------|---------|
| "wygeneruj wideo", "zrób klip", opis sceny bez obrazka | `generate` (text-to-video) |
| "ożyw tę grafikę", "animuj postać", ma obraz startowy | `image-to-video` |
| "seamless loop", "zapętlona animacja pixel-art" | `image-to-video` z `--first` = `--end` (ten sam plik) |
| "długi klip", "wideo powyżej 15 sekund" | `--model seedance25 --duration 16-30` (jedyny silnik z takim zakresem) |
| "porównaj modele", "zrób to drugim modelem", "który silnik lepszy" | ta sama komenda z różnym `--model` |
| "jakie mamy modele wideo" | `models` |
| polling się urwał, mam task_id | `recover` |

### Komendy

> Ustaw interpreter `$PYTHON` tym samym blokiem co przy grafikach (pomija atrapę Pythona ze Sklepu Microsoft).

```bash
# Lista silników i ich parametrów (bez wywołania API)
$PYTHON {baseDir}/scripts/kie_video.py models

# Text → video
$PYTHON {baseDir}/scripts/kie_video.py generate "prompt sceny" out.mp4 --duration 5 --aspect-ratio 16:9
$PYTHON {baseDir}/scripts/kie_video.py generate "prompt sceny" out.mp4 --model seedance --resolution 1080p
$PYTHON {baseDir}/scripts/kie_video.py generate "prompt sceny" out.mp4 --model seedance25 --duration 20

# Image → video: first frame + opcjonalny end frame
$PYTHON {baseDir}/scripts/kie_video.py image-to-video "opis ruchu" out.mp4 --first frame.png --aspect-ratio 16:9 --task-file video-task.json
$PYTHON {baseDir}/scripts/kie_video.py image-to-video "opis ruchu" out.mp4 --first start.png --end koniec.png --aspect-ratio 1:1
$PYTHON {baseDir}/scripts/kie_video.py image-to-video "opis ruchu" out.mp4 --model minimax --first start.png --resolution 2K

# Odzysk po przerwanym pollingu (NIE płacisz drugi raz)
$PYTHON {baseDir}/scripts/kie_video.py recover <task_id> out.mp4
$PYTHON {baseDir}/scripts/kie_video.py recover --task-file video-task.json
```

### Parametry wideo

| Parametr | Opcje | Domyślnie |
|----------|-------|-----------|
| `--model` | kling, seedance, seedance25, minimax | kling |
| `--duration` | 3–15 s (Kling) · 4–15 s (Seedance 2.0, MiniMax) · 4–30 s (Seedance 2.5) | 5 |
| `--aspect-ratio` | zależnie od silnika — patrz tabela wyżej | 16:9 (generate) / brak (image-to-video) |
| `--resolution` | Seedance 2.0: 480p/720p/1080p/4k · Seedance 2.5: 480p/720p · MiniMax: 768P/2K | 720p / 2K |
| `--mode` | **tylko Kling:** std (720p), pro (1080p), 4K | std |
| `--sound` | flaga — Kling i oba Seedance (MiniMax nie generuje dźwięku) | off |
| `--task-file` | atomowy JSON z task_id zapisany przed pollingiem | brak |

### Jak działa image_urls (first / end frame)

W trybie single-shot: `--first` = klatka początkowa (index 0), `--end` = klatka końcowa (index 1). Dla image-to-video podaj jawne `--aspect-ratio` (wyjątek: MiniMax, który bierze kadr z klatki); skrypt nie zgaduje 1:1. Obrazy: **prawdziwy JPG/PNG**, limit zależy od silnika. Plik WebP podszywający się pod `.png` jest odrzucany przed płatnym taskiem — skrypt nie instaluje ani nie zakłada `ffmpeg`.

### Przykład: zapętlona animacja (seamless loop)

Keyframe 1024×1024 (1:1), ten sam plik jako first i end frame daje płynną zapętloną animację (np. postać pixel-art):

```bash
$PYTHON {baseDir}/scripts/kie_video.py image-to-video \
  "pixel-art egg character, subtle idle bounce animation, seamless loop, retro game sprite" \
  egg_idle_loop.mp4 --first egg.png --end egg.png --duration 5 --aspect-ratio 1:1 --mode std
```

### Ważne o wideo

- **Rendery są WOLNE.** Polling ma budżet 40 min. Z `--task-file` task_id jest zapisany atomowo NATYCHMIAST po createTask i przed pollingiem; stdout nadal pokazuje `>>> RECOVERY`. Po przerwaniu użyj `recover`, nigdy ponownego `generate`.
- **Ceny (orientacyjnie):** std ~27 kredytów/s, 4K ~30 kredytów/s → wideo 5s std ≈ 135 kredytów. Nieudane taski nie zjadają kredytów.
- Uruchamiaj generację wideo w tle (`run_in_background`) albo z dużym timeoutem — nie blokuj sesji na 40 min.

---

## Referencje

- Zasady tworzenia promptów: [prompting-guide.md](prompting-guide.md)
- Brand usera: `.claude/kie-brand.md` w workspace (tworzy onboarding, krok 6)

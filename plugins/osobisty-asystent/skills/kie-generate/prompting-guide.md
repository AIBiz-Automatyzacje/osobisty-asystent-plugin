# Kie.ai Prompting Guide

Zasady tworzenia skutecznych promptów do grafik (domyślny model: GPT Image 2.5; te same zasady działają dla Nano Banana).

---

## Struktura promptu (7 elementów)

| # | Element | Słowa kluczowe (EN) |
|---|---------|---------------------|
| 1 | Style & Art Direction | photorealistic, hyper-detailed, Pixar-style, anime, watercolor, oil painting |
| 2 | Scene Description | environment, atmosphere, mood |
| 3 | Main Subject (Hero) | central object/character with specific details |
| 4 | Camera, Lens & Cinematic | focal length (35mm, 85mm), aperture (f/1.8), perspective |
| 5 | Lighting Details | soft lighting, golden hour, rim light, volumetric rays, neon glow |
| 6 | Texture, Color & Material | glossy, matte, pastel tones, metallic surfaces |
| 7 | Negative Prompts (semantic) | describe what you WANT, not what to avoid |

---

## Zasady techniczne

| Zasada | ❌ Źle | ✅ Dobrze |
|--------|--------|-----------|
| Szczegółowość | "fantasy armor" | "ornate elven plate armor, etched with silver leaf patterns" |
| Semantyczne negacje | "no cars in the scene" | "empty, deserted street with no signs of traffic" |
| Warstwowe opisy | "nice room" | "cozy coffee shop, warm wooden tones, gentle light leaks" |

**Nie przeładowuj stylu** - max 3-4 zdania dla opisu wizualnego.

---

## Słownik kamery i oświetlenia

**Perspektywa:** aerial, worm's-eye, over-the-shoulder, extreme close-up, wide shot, low angle

**Obiektyw:** 35mm (szeroki), 50mm (naturalny), 85mm (portret), shallow DOF, f/1.8, f/2.8

**Oświetlenie:** golden hour, blue hour, rim lighting, backlight, soft diffused, volumetric fog, neon glow

**Color grading:** teal & orange, noir palette, pastel diffusion, muted tones, high contrast

---


## Szablon edycji (gdy są obrazki wejściowe)

```
Using the provided image of [subject], [add/remove/modify] [element].
Ensure the change [integrates with original lighting/style/composition].
Keep [specific elements] unchanged.
```

---

## Zachowanie treści tekstowych

Teksty, które użytkownik podał do umieszczenia na grafice (nagłówki, listy, skróty klawiszowe), przepisz do promptu słowo w słowo i w komplecie — ile pozycji na wejściu, tyle w bloku `TEXT CONTENT TO DISPLAY`. Optymalizować możesz styl, kolory i kompozycję, nie treść.

| Typ contentu | Działanie |
|--------------|-----------|
| Style, efekty, kolory | Można optymalizować |
| Konkretne teksty do wyświetlenia | Zachowaj 1:1 |
| Listy z opisami | Przepisz każdy element |
| Skróty klawiszowe | Dokładnie jak podał użytkownik |

### Format dla grafik z tekstem

```
[opis stylu i kompozycji]

TEXT CONTENT TO DISPLAY:
[SECTION: Nazwa sekcji]
• Element 1: "dokładny tekst"
• Element 2: "dokładny tekst"
```

Listy nie zastępuj streszczeniem typu "lists all...".

---

## Ograniczenia

- ❌ Nie wymyślaj treści których nie znasz (logo, teksty z załączników)
- ❌ Nie skracaj treści użytkownika
- ❌ Nie dodawaj elementów których użytkownik nie wymienił
- ❌ Nie przeładowuj stylu
- ✅ Zawsze zachowuj PEŁNĄ treść tekstową użytkownika

---

## Przykłady

### Przykład 1: Nowa grafika z brandem

**Input:** "stwórz post na Instagram o automatyzacji w biznesie" (use_brand: true)

**Output:**
```
Halftone black-and-white print collage on warm cream grid paper (#FAF8F4, thin 32px grid lines): a laptop and printed flowchart sheets on a desk, exactly one orange (#E8590C) element — a marker stripe. No people, no glow, no gradients.
```

### Przykład 2: Infografika z konkretnymi elementami

**Input:** "infografika przedstawiająca 3 korzyści z automatyzacji: oszczędność czasu, redukcja błędów, skalowalność" (use_brand: true)

**Output:**
```
Clean infographic design, light editorial print aesthetic. Three distinct icon sections arranged vertically on warm cream grid paper background (#FAF8F4). Each section with bold ink-black (#141414) uppercase label and orange (#E8590C) accent elements. Minimalist flat design, subtle grid pattern, sharp focus, balanced composition.

TEXT CONTENT TO DISPLAY:
• Section 1: "Oszczędność czasu" with clock icon
• Section 2: "Redukcja błędów" with checkmark shield icon
• Section 3: "Skalowalność" with upward graph icon
```

### Przykład 3: Edycja istniejącego obrazu

**Input:** "usuń tło i wstaw gradient niebiesko-fioletowy" (has_images: true)

**Output:**
```
Using the provided image, remove the background completely. Replace with smooth gradient transitioning from deep blue (#1a1a4e) to rich purple (#4a1a6b). Ensure the subject maintains original lighting and edges blend naturally with new background. Keep all foreground elements unchanged.
```

### Przykład 4: Grafika z listą komend

**Input:** "Stwórz grafikę z listą 5 komend: /help - pomoc, /new - nowa sesja, /clear - wyczyść, /model - zmień model, /exit - wyjdź" (use_brand: true)

**Output:**
```
Horizontal infographic, light editorial print aesthetic. Warm cream background (#FAF8F4) with subtle grid pattern in #E5E1D8. Bold ink-black (#141414) title top-center with orange (#E8590C) accent. Clean list layout with monospace font for commands. Minimalist flat design, sharp focus, developer tool aesthetic.

TEXT CONTENT TO DISPLAY:
• /help – pomoc
• /new – nowa sesja
• /clear – wyczyść
• /model – zmień model
• /exit – wyjdź
```

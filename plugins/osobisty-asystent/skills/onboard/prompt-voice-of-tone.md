# Instrukcja generacji content/voice-of-tone.md

Plik opisujący JAK user pisze treści (posty, maile, wpisy). Używany przy generowaniu
contentu, żeby AI pisało jego głosem — nie generycznie.

## ⚠️ Warunek wstępny: PRÓBKI (bez nich nie generuj)

Styl ekstrahujemy z REALNYCH tekstów, nie z deklaracji. Bez materiału ten plik byłby
zmyślony i bezużyteczny.

- **Masz min. 5 próbek** (posty / maile / wpisy usera) → generuj.
- **Mniej niż 5 albo brak** → NIE generuj. Powiedz userowi: *"Voice-of-tone tworzymy
  z Twoich tekstów — wróćmy do tego, gdy będziesz mieć kilka postów. Skill `/reflect`
  zbuduje go z czasem."* i pomiń.

## Co robisz

1. Przeanalizuj próbki. Szukaj POWTARZALNYCH wzorców (jednorazowe pomiń):
   - ton i charakterystyka głosu
   - słownictwo charakterystyczne (słowa/frazy które wracają) oraz czego user NIE używa
   - typy otwarć (hooki) — jak zaczyna teksty
   - struktury (jak buduje post: problem→rozwiązanie? lista? historia?)
   - formatowanie (emoji, akapity, długość zdań, listy)
   - czego unika (sztuczność, korpomowa, konkretne słowa)
2. Wygeneruj plik wg struktury poniżej — **tylko to, co realnie widać w próbkach**.
3. Sekcje DATA-DRIVEN (skuteczność/ranking) zostaw jako placeholder — dojrzeją przez
   `/reflect`. Na starcie nie masz danych o konwersji.

## Struktura pliku

```markdown
# VOICE OF TONE — [IMIĘ]

## QUICK REFERENCE
[1-3 zdania: esencja głosu. Jak brzmi ten człowiek w jednym akapicie.]

## TOŻSAMOŚĆ GŁOSU
### Kim jest autor (gdy pisze)
[Perspektywa, pozycja — ekspert? praktyk? partner?]
### Relacja z odbiorcą
[Jak traktuje czytelnika — per "ty"? z dystansem? jak kumpla?]
### Wartości komunikowane
[Co przewija się w treści jako światopogląd]

## TON I JĘZYK
### Charakterystyka
[3-5 cech tonu wyciągniętych z próbek — np. bezpośredni, konkretny, ironiczny]
### Słownictwo
| Używaj | Unikaj |
|--------|--------|
| [słowa/frazy charakterystyczne z próbek] | [czego user NIE używa / jawnie odrzuca] |
### Dynamika zdań
[Długość, rytm, czy tnie krótko czy buduje długie — z próbek]

## HOOKI (otwarcia)
[Typy otwarć ZAOBSERWOWANE w próbkach, z przykładem każdego.
NIE wymyślaj rankingu skuteczności — na starcie nie ma danych o metrykach.]

## STRUKTURY POSTÓW
[Formaty które user realnie stosuje, z krótkim opisem każdego.]

## FORMATOWANIE
[Jak formatuje: emoji (jakie, do czego), akapity, listy, długość. Z próbek.]

## ANTY-WZORCE
[Czego user NIE robi / czego unika — z próbek i jawnych deklaracji.
Np. "nie zaczyna od pytania retorycznego", "zero korpomowy".]

## SKUTECZNOŚĆ WG DANYCH
*[Placeholder — uzupełniane przez /reflect, gdy nazbiera się danych o tym,
które hooki i struktury działają. Na razie puste.]*

---
*Wygenerowane z [N] próbek: [data]. Żywy dokument — rośnie z każdą analizą.*
```

## Zasady generacji

1. **Tylko z próbek** — zero zmyślania stylu, zero generycznych porad copywriterskich
2. **Min. 5 próbek** — inaczej skip (patrz warunek wstępny)
3. **Krótko na starcie** — to v0. Plik urośnie z danymi (/reflect)
4. **Powtarzalność** — wzorzec musi wracać w kilku próbkach, nie być jednorazowy
5. **Język usera** — jeśli pisze po polsku → voice-of-tone po polsku
6. **Zapis:** `.claude/rules/content/voice-of-tone.md` (utwórz folder `content/` jeśli brak)
7. **Bez frontmattera przy zapisie** — krok 10 onboardu dopisze `paths` (ładowanie tylko przy
   pracy w `Marketing/`), jeśli user wybierze ten folder. Bez `Marketing/` plik zostaje bez
   `paths` i ładuje się zawsze.

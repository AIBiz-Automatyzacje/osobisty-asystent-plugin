# Szablon raportu /daily

Raport jest krótki — to potwierdzenie porządku, nie plan dnia.

```
✅ Dashboard odświeżony — [DD.MM]
Zarchiwizowane: [n] ([nazwa], [nazwa], …)
Cykliczne na dziś: [n]
⚠️ Zaległe: [n] ([nazwa] od DD.MM, [nazwa] (cykliczne), …)
Dzisiaj [n] · Tydzień [n] · Później [n] · Bez terminu [n]
```

Zasady:
- Linię „Zarchiwizowane” pokazuj tylko gdy n > 0.
- Linię „Cykliczne na dziś” pokazuj tylko gdy n > 0.
- Linię „Zaległe” pokazuj tylko gdy n > 0; przy więcej niż 5 pozycjach wymień 5 i dopisz „+N”.
  Zaległe cykliczne (bez terminu) opisuj „[nazwa] (cykliczne)”.
- Linia z licznikami — zawsze.
- Nazwy w raporcie bez linków `[[…]]` — sam tekst.
- Ostrzeżenia (linie nieczytelne) → na końcu `⚠️ Nie rozpoznano: [linia]`.

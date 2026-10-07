# CLAUDE.md

## Rules (auto-loaded)

Pliki w `.claude/rules/` ładują się automatycznie do system promptu — bez instrukcji, bez Read na starcie sesji.

{{RULES_LIST}}

### Wczytywanie kontekstu on-demand

{{ON_DEMAND}}

**Kolejność przy tekstach:** najpierw draft (w stylu z `voice-of-tone.md`, jeśli istnieje), POTEM self-check wg `ai-writing-patterns.md` jako osobny przebieg redaktorski — przed pokazaniem draftu, nie po korekcie.

## Konfiguracja Claude Code (.claude/)

Folder `.claude/` zawiera konfigurację Claude Code dla tego workspace:

| Element | Zawartość |
|---------|-----------|
| `skills/` | Skille do specjalistycznych zadań (wywoływane przez /nazwa) |
| `rules/` | Pliki kontekstowe ładowane automatycznie |

### Dostępne skille (skills/)

{{SKILLS_LIST}}

## Opis workspace'u

[Krótki opis — co to za projekt/workspace]

## Struktura katalogów

{{FOLDER_STRUCTURE}}

## Konwencje

{{CONVENTIONS}}

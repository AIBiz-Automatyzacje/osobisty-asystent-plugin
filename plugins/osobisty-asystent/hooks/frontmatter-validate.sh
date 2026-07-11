#!/bin/bash
# Walidacja YAML frontmatter w plikach Zadania/
# Hook: PostToolUse (Write|Edit)

FILE=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')

# Tylko Zadania/*.md
case "$FILE" in
  */Zadania/*.md) ;;
  *) exit 0 ;;
esac

# Pomiń dashboardy, szablony, cykliczne
case "$FILE" in
  */.szablony/*|*/to_do.md|*/recurring.md) exit 0 ;;
esac

# Wyciągnij frontmatter (między pierwszymi dwoma ---)
FRONT=$(awk '/^---$/{n++; next} n==1{print} n>=2{exit}' "$FILE" 2>/dev/null)

ERRORS=""

if [ -z "$FRONT" ]; then
  ERRORS="Brak YAML frontmatter. "
else
  echo "$FRONT" | grep -q '^status:' || ERRORS="${ERRORS}Brak 'status'. "
  echo "$FRONT" | grep -q '^priorytet:' || ERRORS="${ERRORS}Brak 'priorytet'. "
  echo "$FRONT" | grep -q '^termin:' || ERRORS="${ERRORS}Brak 'termin'. "

  STATUS=$(echo "$FRONT" | grep '^status:' | sed 's/^status: *//')
  if [ -n "$STATUS" ] && [ "$STATUS" != "w_trakcie" ] && [ "$STATUS" != "zrobione" ]; then
    ERRORS="${ERRORS}Status '$STATUS' nieprawidłowy (w_trakcie/zrobione). "
  fi

  PRIORYTET=$(echo "$FRONT" | grep '^priorytet:' | sed 's/^priorytet: *//')
  if [ -n "$PRIORYTET" ] && [ "$PRIORYTET" != "pilny" ] && [ "$PRIORYTET" != "istotny" ] && [ "$PRIORYTET" != "normalny" ] && [ "$PRIORYTET" != "niski" ]; then
    ERRORS="${ERRORS}Priorytet '$PRIORYTET' nieprawidłowy (pilny/istotny/normalny/niski). "
  fi
fi

if [ -n "$ERRORS" ]; then
  jq -n --arg err "⚠️ Frontmatter: ${ERRORS}Wymagane: status (w_trakcie/zrobione), priorytet (pilny/istotny/normalny/niski), termin (YYYY-MM-DD)." \
    '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$err}}'
fi

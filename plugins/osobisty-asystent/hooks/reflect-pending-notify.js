#!/usr/bin/env node
// SessionStart hook — sygnalizuje oczekujące propozycje reflecta (_reflect-pending.md).
//
// Raz na start sesji (nie spam per-prompt). Gating: tylko vaulty Personal OS
// (projekt ma .claude/rules/ — projekty kodowe pomijamy). Nie blokuje sesji.

const fs = require('fs');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
// Nowa lokalizacja poza rules/ (rules/ ładuje się do kontekstu każdej sesji);
// stara .claude/rules/ zostaje jako fallback dla instalacji sprzed zmiany.
const pending = [
  path.join(projectDir, '.claude', '_reflect-pending.md'),
  path.join(projectDir, '.claude', 'rules', '_reflect-pending.md'),
].find((p) => fs.existsSync(p));

try {
  if (pending) {
    const content = fs.readFileSync(pending, 'utf8');
    const count = (content.match(/^## /gm) || []).length;
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext:
          `[Reflect] Masz ${count} oczekujących propozycji kalibracji w ` +
          `${path.relative(projectDir, pending)}. Gdy będzie dobry moment (nie przerywaj ` +
          `bieżącego zadania), zaproponuj userowi przegląd — zaznacza checkboxy przy ` +
          `zmianach, które chce, i odpala /reflect apply (nanosi zaznaczone, kasuje plik).`,
      },
    }));
  }
} catch (err) {
  process.stderr.write(`reflect-pending-notify: ${err.message}\n`);
}

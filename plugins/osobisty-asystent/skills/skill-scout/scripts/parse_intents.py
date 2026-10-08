#!/usr/bin/env python3
"""
parse_intents.py — Ekstrakcja PRÓŚB usera z logów sesji Claude Code.

W przeciwieństwie do parsera reflect (USER + ASSISTANT, dialog),
ten skrypt wyciąga TYLKO wiadomości usera — bo skill-scout szuka
powtarzającej się ręcznej roboty, którą user ZLECA, a nie tego
co odpowiada asystent. Każda prośba dostaje datę, żeby downstream
LLM mógł policzyć ile razy w oknie pojawił się ten sam typ roboty.

Filtruje noise: komendy systemowe/skille, ładowanie SKILL.md,
krótkie wiadomości, czyste wklejki/loga (heurystyka długości).

Usage:
    python3 parse_intents.py [--days N] [--out plik.json]

    --days   Okno w dniach (domyślnie: 7)
    --out    Ścieżka pliku JSON wyjściowego (domyślnie: stdout)

Output (JSON):
    {"window_days": N, "cutoff": "...", "sessions": M, "count": K,
     "intents": [{"date": "YYYY-MM-DD", "time": "HH:MM", "text": "..."}]}
Statystyki idą na stderr.
"""

import os
import sys
import json
import datetime
import argparse

# Cross-platform: wymuś UTF-8 stdout (Windows cp1250 → UnicodeEncodeError przy PL/emoji)
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

# ── Config ──────────────────────────────────────────────────

MIN_MSG_LENGTH = 12       # krótsze prośby odsiewamy (szum typu "ok", "tak")
MAX_MSG_LENGTH = 600      # długie prośby tniemy — intencja zwykle w pierwszych zdaniach
MAX_INTENTS = 1200        # twardy limit, żeby raport nie eksplodował

SYSTEM_COMMANDS = {
    '/clear', '/daily', '/help', '/compact', '/cost', '/doctor',
    '/init', '/login', '/logout', '/config', '/mcp', '/memory',
    '/review', '/status', '/vim', '/model', '/permissions',
    '/terminal-setup', '/listen', '/fast', '/plugin', '/skill-scout',
}

# ── Functions ───────────────────────────────────────────────

def get_sessions_dirs():
    """Wszystkie katalogi sesji dla tego workspace (łącznie z podkatalogami CWD)."""
    cwd = os.environ.get('SKILL_SCOUT_WORKSPACE',
                         os.environ.get('CLAUDE_CRON_WORKSPACE', os.getcwd()))
    workspace_id = (cwd.replace('/', '-')
                       .replace('\\', '-')
                       .replace(':', '-')
                       .replace(' ', '-')
                       .replace('_', '-'))
    if cwd.startswith('/') and not workspace_id.startswith('-'):
        workspace_id = '-' + workspace_id

    projects_base = os.path.expanduser("~/.claude/projects/")
    if not os.path.isdir(projects_base):
        raise FileNotFoundError(f"Projects directory not found: {projects_base}")

    dirs = []
    for entry in os.listdir(projects_base):
        full = os.path.join(projects_base, entry)
        if os.path.isdir(full) and entry.startswith(workspace_id):
            if '-ralph-worktrees-' in entry:
                continue
            dirs.append(full)

    if not dirs:
        raise FileNotFoundError(f"No sessions directories found matching: {workspace_id}")
    return dirs


def parse_args():
    parser = argparse.ArgumentParser(description='Ekstrakcja próśb usera z logów sesji')
    parser.add_argument('--days', type=int, default=7, help='Okno w dniach (domyślnie 7)')
    parser.add_argument('--out', type=str, default=None, help='Plik JSON wyjściowy (domyślnie stdout)')
    return parser.parse_args()


def get_session_files(sessions_dirs, cutoff):
    sessions = []
    seen_ids = set()
    for sessions_dir in sessions_dirs:
        for f in os.listdir(sessions_dir):
            if not f.endswith('.jsonl') or f in seen_ids:
                continue
            seen_ids.add(f)
            path = os.path.join(sessions_dir, f)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            if mtime >= cutoff:
                sessions.append((mtime, path))
    sessions.sort()
    return sessions


def extract_text_from_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [b.get('text', '') for b in content
                 if isinstance(b, dict) and b.get('type') == 'text']
        return '\n'.join(texts)
    return ''


def is_system_command(text):
    first_line = text.strip().split('\n')[0].strip().lower()
    return any(first_line == cmd or first_line.startswith(cmd + ' ') for cmd in SYSTEM_COMMANDS)


def is_noise(text):
    """Wklejki/logi/komendy/meta — nie są intencją procesu."""
    stripped = text.strip()
    if 'Base directory for this skill:' in stripped:
        return True
    if stripped.startswith('---\nname:'):
        return True
    if stripped.startswith('<') and stripped.endswith('>'):  # czyste tagi systemowe
        return True
    # Wklejka logu/kodu: dużo linii, mało zdań → to nie prośba
    if stripped.count('\n') > 25:
        return True
    return False


def parse_user_intents(path, ts):
    """Zwróć listę próśb usera (string) z jednej sesji."""
    intents = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get('type') != 'user' or entry.get('userType') != 'external':
                continue
            msg = entry.get('message', {})
            content = msg.get('content', '') if isinstance(msg, dict) else (msg if isinstance(msg, str) else '')
            text = extract_text_from_content(content).strip()
            if (not text or len(text) < MIN_MSG_LENGTH
                    or is_system_command(text) or is_noise(text)):
                continue
            if len(text) > MAX_MSG_LENGTH:
                text = text[:MAX_MSG_LENGTH] + ' […]'
            intents.append(text)
    return intents


def main():
    args = parse_args()
    cutoff = datetime.datetime.now() - datetime.timedelta(days=args.days)

    try:
        sessions_dirs = get_sessions_dirs()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    sessions = get_session_files(sessions_dirs, cutoff)
    if not sessions:
        print(f"Brak sesji od {cutoff.strftime('%Y-%m-%d %H:%M')}", file=sys.stderr)
        result = {"window_days": args.days, "cutoff": cutoff.strftime('%Y-%m-%d %H:%M'),
                  "sessions": 0, "count": 0, "intents": []}
        _emit(result, args.out)
        sys.exit(0)

    all_intents = []
    session_count = 0
    for mtime, path in sessions:
        items = parse_user_intents(path, mtime)
        if not items:
            continue
        session_count += 1
        date = mtime.strftime('%Y-%m-%d')
        time = mtime.strftime('%H:%M')
        for text in items:
            all_intents.append({"date": date, "time": time, "text": text})
            if len(all_intents) >= MAX_INTENTS:
                break
        if len(all_intents) >= MAX_INTENTS:
            break

    print(f"Sesje: {session_count} | Prośby usera: {len(all_intents)} | "
          f"Okno: {args.days}d (od {cutoff.strftime('%Y-%m-%d')})", file=sys.stderr)

    result = {
        "window_days": args.days,
        "cutoff": cutoff.strftime('%Y-%m-%d %H:%M'),
        "sessions": session_count,
        "count": len(all_intents),
        "intents": all_intents,
    }
    _emit(result, args.out)


def _emit(result, out):
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(payload)
        print(f"→ zapisano {result['count']} próśb do {out}", file=sys.stderr)
    else:
        print(payload)


if __name__ == '__main__':
    main()

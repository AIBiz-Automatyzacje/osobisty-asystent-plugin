#!/usr/bin/env python3
"""
parse_sessions.py — Parser logow sesji Claude Code

Wyciaga czysty dialog (user + assistant text) z plikow .jsonl.
Filtruje noise: tool_use, progress, file-history, krotkie wiadomosci, komendy systemowe.

Usage:
    python3 parse_sessions.py [--since "YYYY-MM-DD HH:MM"] [--days N]

    --since   Parsuj sesje od podanego timestampu
    --days    Parsuj sesje z ostatnich N dni (domyslnie: 1)
              Jesli podano --since, --days jest ignorowane

Output: czysty dialog na stdout, statystyki na stderr
"""

import os
import re
import sys
import json
import datetime
import argparse

# Cross-platform: wymuś UTF-8 stdout (Windows cp1250 → UnicodeEncodeError przy emoji/PL)
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

# ── Config ──────────────────────────────────────────────────

MIN_MSG_LENGTH = 10  # wiadomosci krotsze sa filtrowane
MAX_ASSISTANT_LENGTH = 2000  # truncate dlugich odpowiedzi
MAX_PAIRS = 500  # limit par user+assistant

SYSTEM_COMMANDS = {
    '/clear', '/daily', '/help', '/compact', '/cost', '/doctor',
    '/init', '/login', '/logout', '/config', '/mcp', '/memory',
    '/review', '/status', '/vim', '/model', '/permissions',
    '/terminal-setup', '/listen', '/fast',
}

# ── Functions ───────────────────────────────────────────────

def get_sessions_dirs():
    """Detect all sessions directories for the workspace (including subdirs).

    Claude Code stores sessions per CWD, so workspace launched from
    /workspace vs /workspace/Zadania creates separate session dirs.
    This function finds ALL matching dirs to avoid missing sessions.
    """
    cwd = os.environ.get('MEMORY_UPDATE_WORKSPACE', os.getcwd())
    # Claude Code converts path to ID — KAŻDY znak niealfanumeryczny → '-'
    # (nie tylko /, \, :, spacja, _ — także !, ., #, ~ itd.)
    # Leading '-' powstaje sam: '/Users/...' → '-Users-...', 'C:\...' → 'C--...'
    workspace_id = re.sub(r'[^A-Za-z0-9]', '-', cwd)

    projects_base = os.path.expanduser("~/.claude/projects/")
    if not os.path.isdir(projects_base):
        raise FileNotFoundError(f"Projects directory not found: {projects_base}")

    # Find all dirs that start with this workspace ID
    # This catches both /workspace and /workspace/Zadania etc.
    dirs = []
    for entry in os.listdir(projects_base):
        full = os.path.join(projects_base, entry)
        if os.path.isdir(full) and entry.startswith(workspace_id):
            # Skip ralph worktrees — those are temp agent sessions
            if '-ralph-worktrees-' in entry:
                continue
            dirs.append(full)

    if not dirs:
        raise FileNotFoundError(f"No sessions directories found matching: {workspace_id}")

    return dirs


def parse_args():
    parser = argparse.ArgumentParser(description='Parse Claude Code session logs')
    parser.add_argument('--since', type=str,
                        help='Parse sessions since timestamp (YYYY-MM-DD or YYYY-MM-DD HH:MM)')
    parser.add_argument('--days', type=int, default=1,
                        help='Parse sessions from last N days (default: 1)')
    parser.add_argument('--stats-json', type=str, default=None,
                        help='Write stats as JSON to this file (in addition to stderr text)')
    return parser.parse_args()


def get_cutoff_time(args):
    if args.since:
        for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d'):
            try:
                return datetime.datetime.strptime(args.since, fmt)
            except ValueError:
                continue
        print(f"Error: invalid date format: {args.since}", file=sys.stderr)
        print("Expected: YYYY-MM-DD or YYYY-MM-DD HH:MM", file=sys.stderr)
        sys.exit(1)
    return datetime.datetime.now() - datetime.timedelta(days=args.days)


def get_session_files(sessions_dirs, cutoff):
    """Get .jsonl files modified after cutoff from all session dirs, sorted by mtime."""
    sessions = []
    seen_ids = set()
    for sessions_dir in sessions_dirs:
        for f in os.listdir(sessions_dir):
            if not f.endswith('.jsonl'):
                continue
            # Deduplicate by filename (session UUID) in case of overlaps
            if f in seen_ids:
                continue
            seen_ids.add(f)
            path = os.path.join(sessions_dir, f)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            if mtime >= cutoff:
                sessions.append((mtime, path))
    sessions.sort()
    return sessions


def extract_text_from_content(content):
    """Extract plain text from message content (string or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                texts.append(block.get('text', ''))
        return '\n'.join(texts)
    return ''


def is_system_command(text):
    """Check if message is a system command or skill invocation."""
    stripped = text.strip()
    first_line = stripped.split('\n')[0].strip().lower()
    for cmd in SYSTEM_COMMANDS:
        if first_line == cmd or first_line.startswith(cmd + ' '):
            return True
    return False


def is_skill_load(text):
    """Check if message is a skill SKILL.md being loaded into context."""
    stripped = text.strip()
    if 'Base directory for this skill:' in stripped:
        return True
    if stripped.startswith('---\nname:'):
        return True
    return False


def parse_session(path):
    """Parse a single session file, return list of (role, text) tuples."""
    dialog = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get('type')

            # User messages
            if entry_type == 'user' and entry.get('userType') == 'external':
                msg = entry.get('message', {})
                if isinstance(msg, dict):
                    content = msg.get('content', '')
                elif isinstance(msg, str):
                    content = msg
                else:
                    continue

                text = extract_text_from_content(content)
                if not text or len(text.strip()) < MIN_MSG_LENGTH:
                    continue
                if is_system_command(text):
                    continue
                if is_skill_load(text):
                    continue
                dialog.append(('USER', text.strip()))

            # Assistant messages — only text blocks
            elif entry_type == 'assistant':
                msg = entry.get('message', {})
                if not isinstance(msg, dict):
                    continue
                content = msg.get('content', '')
                text = extract_text_from_content(content)
                if not text or len(text.strip()) < 20:
                    continue
                if len(text) > MAX_ASSISTANT_LENGTH:
                    text = text[:MAX_ASSISTANT_LENGTH] + '\n[...truncated]'
                dialog.append(('ASSISTANT', text.strip()))

    return dialog


def main():
    args = parse_args()
    cutoff = get_cutoff_time(args)

    try:
        sessions_dirs = get_sessions_dirs()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {len(sessions_dirs)} session dir(s): {[os.path.basename(d) for d in sessions_dirs]}", file=sys.stderr)
    sessions = get_session_files(sessions_dirs, cutoff)

    if not sessions:
        print(f"Brak sesji od {cutoff.strftime('%Y-%m-%d %H:%M')}", file=sys.stderr)
        sys.exit(0)

    output_lines = []
    session_count = 0
    user_msg_count = 0
    total_pairs = 0

    # `sessions` jest posortowane ROSNACO po mtime, wiec `break` na MAX_PAIRS wycinal
    # dni NAJSWIEZSZE - przy --days 7 w raporcie zostawaly same najstarsze sesje.
    # Idziemy od najnowszej; komunikat "starsze sesje pominiete" stal sie przy okazji prawdziwy.
    for mtime, path in reversed(sessions):
        dialog = parse_session(path)
        if not dialog:
            continue

        # Pomijamy sesje-automaty: jedno wejscie uzytkownika, ktore NIE jest rozmowa.
        # Dwa zrodla takich sesji:
        #   * wywolanie skilla slash-komenda -> tekst zawiera <command-name>
        #   * job crona odpalony przez `claude -p "<dlugi prompt>"` -> zwykly tekst,
        #     wiec rozpoznajemy go po dlugosci (prompty jobow maja tysiace znakow,
        #     a czlowiek, ktory napisal tylko raz, pisze krotko)
        # Zmierzone na jednej dobie przed ta zmiana: 63 z 67 sesji to byly prompty jobow,
        # czyli 89% wyjscia parsera. Poza kosztem tokenow zafalszowywalo to wynik - plik
        # kontekstu karmil sie opisami dzialania wlasnych automatow zamiast praca uzytkownika.
        PROG_PROMPTU_AUTOMATU = 1200
        _users = [t for r, t in dialog if r == 'USER']
        if len(_users) <= 1 and (
            not _users
            or '<command-name>' in _users[0]
            or len(_users[0]) > PROG_PROMPTU_AUTOMATU
        ):
            continue

        session_count += 1
        user_count = sum(1 for role, _ in dialog if role == 'USER')
        user_msg_count += user_count

        output_lines.append(f"\n{'='*60}")
        output_lines.append(
            f"SESJA: {mtime.strftime('%Y-%m-%d %H:%M')} | "
            f"{user_count} wiadomosci usera"
        )
        output_lines.append(f"{'='*60}\n")

        for role, text in dialog:
            output_lines.append(f"[{role}]: {text}\n")
            if role == 'USER':
                total_pairs += 1

        # Limit total pairs
        if total_pairs >= MAX_PAIRS:
            output_lines.append(f"\n[...limit {MAX_PAIRS} par osiagniety, starsze sesje pominiete]")
            break

    # Stats to stderr
    earliest = sessions[0][0].strftime('%H:%M')
    latest = sessions[-1][0].strftime('%H:%M')
    print(
        f"Sesje: {session_count} | "
        f"Wiadomosci usera: {user_msg_count} | "
        f"Zakres: {cutoff.strftime('%Y-%m-%d %H:%M')} do teraz | "
        f"Godziny: {earliest}–{latest}",
        file=sys.stderr
    )

    # Optional JSON stats to file
    if args.stats_json:
        stats = {
            "sessions": session_count,
            "user_messages": user_msg_count,
            "cutoff": cutoff.strftime('%Y-%m-%d %H:%M'),
            "earliest": sessions[0][0].strftime('%Y-%m-%d %H:%M'),
            "latest": sessions[-1][0].strftime('%Y-%m-%d %H:%M'),
        }
        with open(args.stats_json, 'w') as sf:
            json.dump(stats, sf)

    # Dialog to stdout
    print('\n'.join(output_lines))


if __name__ == '__main__':
    main()

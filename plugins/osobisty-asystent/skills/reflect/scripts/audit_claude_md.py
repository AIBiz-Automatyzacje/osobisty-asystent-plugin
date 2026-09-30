#!/usr/bin/env python3
"""
audit_claude_md.py — twarde sprawdzenie CLAUDE.md wzgledem dysku

Nie ocenia tresci, tylko fakty, ktore da sie sprawdzic bez LLM:
  1. sciezki w `backtickach` wskazuja na istniejace pliki/foldery,
  2. komendy `/skill` odpowiadaja zainstalowanym skillom,
  3. deklarowana liczba skilli ("27 skilli") zgadza sie z .claude/skills/,
  4. foldery glowne workspace'u sa opisane w CLAUDE.md.

Usage:
    python3 audit_claude_md.py [--root DIR]

--root domyslnie: MEMORY_UPDATE_WORKSPACE albo CWD.
Output: raport markdown na stdout (pusta sekcja = brak rozjazdow).
Exit code zawsze 0 — raport jest materialem dla reflecta, nie testem.
"""

import os
import re
import sys
import glob
import argparse

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

# Szablony w sciezkach (YYYY-MM, <osoba>, NN - Kurs, *.md) — nie da sie ich sprawdzic na dysku
PLACEHOLDER = re.compile(r"YYYY|MM-DD|DD\.MM|WNN|\bNN\b|<[^>]+>|\*|\{|\}|\[|\]")
BACKTICK = re.compile(r"`([^`\n]+)`")
SKILL_COUNT = re.compile(r"(\d+)\s+skill", re.IGNORECASE)
SLASH_CMD = re.compile(r"^/([a-z0-9][a-z0-9-]*(?::[a-z0-9][a-z0-9-]*)?)$")


def find_claude_md(root):
    """Zwraca liste istniejacych CLAUDE.md projektu (root i .claude/)."""
    return [p for p in (os.path.join(root, "CLAUDE.md"), os.path.join(root, ".claude", "CLAUDE.md"))
            if os.path.isfile(p)]


def skill_dirs(root):
    """Katalogi, w ktorych moga lezec skille: projekt, globalne, pluginy."""
    home = os.path.expanduser("~")
    dirs = [os.path.join(root, ".claude", "skills"), os.path.join(home, ".claude", "skills")]
    dirs += glob.glob(os.path.join(home, ".claude", "plugins", "**", "skills"), recursive=True)
    return [d for d in dirs if os.path.isdir(d)]


def skill_exists(name, dirs):
    # plugin:skill → sprawdzamy sama nazwe skilla (prefiks pluginu nie jest katalogiem)
    base = name.split(":")[-1]
    return any(os.path.isfile(os.path.join(d, base, "SKILL.md")) for d in dirs)


def check_paths(tokens, root):
    top_level = {n for n in os.listdir(root) if not n.startswith(".")} | {".claude"}
    missing = []
    for tok in tokens:
        path = tok.strip()
        if " " in path and not any(path.startswith(t + "/") for t in top_level):
            continue  # komenda albo zdanie, nie sciezka
        if PLACEHOLDER.search(path) or "://" in path:
            continue
        if path.startswith("~/"):
            full = os.path.expanduser(path)
        elif "/" in path and path.split("/")[0] in top_level:
            full = os.path.join(root, path)
        else:
            continue  # sama nazwa pliku bez folderu — nie wiemy gdzie szukac
        if not os.path.exists(full.rstrip("/")):
            missing.append(path)
    return missing


def audit(root):
    files = find_claude_md(root)
    out = ["# Audyt CLAUDE.md (twarde fakty)", ""]
    if not files:
        out.append("Brak CLAUDE.md w projekcie — nic do sprawdzenia.")
        return "\n".join(out)

    text = "\n".join(open(f, encoding="utf-8").read() for f in files)
    tokens = sorted(set(BACKTICK.findall(text)))
    out.append("Pliki: " + ", ".join(os.path.relpath(f, root) for f in files))
    out.append("")

    missing = check_paths(tokens, root)
    out.append("## Ścieżki, których nie ma na dysku")
    out += [f"- `{p}`" for p in missing] or ["- (brak)"]
    out.append("")

    dirs = skill_dirs(root)
    unknown = [t for t in tokens if SLASH_CMD.match(t) and not skill_exists(SLASH_CMD.match(t).group(1), dirs)]
    out.append("## Komendy /skill bez zainstalowanego skilla")
    out.append("(skill mógł zostać usunięty albo to wbudowana komenda — do sprawdzenia)")
    out += [f"- `{t}`" for t in unknown] or ["- (brak)"]
    out.append("")

    local_dir = os.path.join(root, ".claude", "skills")
    actual = len(glob.glob(os.path.join(local_dir, "*", "SKILL.md")))
    claimed = [int(n) for n in SKILL_COUNT.findall(text)]
    out.append("## Liczba skilli w projekcie")
    wrong = [n for n in claimed if n != actual]
    if wrong:
        out.append(f"- CLAUDE.md podaje {', '.join(map(str, wrong))}, w `.claude/skills/` jest {actual}")
    else:
        out.append(f"- (zgodna albo niepodana; na dysku: {actual})")
    out.append("")

    top = sorted(n for n in os.listdir(root)
                 if os.path.isdir(os.path.join(root, n)) and not n.startswith("."))
    undocumented = [n for n in top if n not in text]
    out.append("## Foldery główne nieopisane w CLAUDE.md")
    out += [f"- `{n}/`" for n in undocumented] or ["- (brak)"]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("MEMORY_UPDATE_WORKSPACE", os.getcwd()))
    args = ap.parse_args()
    print(audit(os.path.abspath(args.root)))


if __name__ == "__main__":
    main()

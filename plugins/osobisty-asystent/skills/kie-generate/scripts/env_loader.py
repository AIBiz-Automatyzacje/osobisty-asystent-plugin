"""
Self-contained .env loader — kopia w każdym skillu (NIE importuje z `_shared/`).

Działa lokalnie i na VPS (odporne na symlink .claude → vault-git/.claude).
Plugin celowo trzyma kopie per skill, żeby każdy skill działał samodzielnie.

Usage (z `scripts/your_script.py`):
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from env_loader import find_workspace, load_env

    WORKSPACE = find_workspace(script_path=__file__)
    load_env(WORKSPACE)
"""

import os
from pathlib import Path


def find_workspace(script_path=None):
    """Znajdź workspace Obsidian — odporny na symlinki i relokację.

    Szuka markera .obsidian/ lub .env idąc w górę od:
    1. cwd (Claude CLI ustawia cwd na workspace)
    2. Lokalizacja skryptu (dla bezpośredniego wywołania)
    3. Fallback: wykrywanie symlinka .claude → vault-git/.claude
    """
    if script_path:
        script_path = Path(script_path).resolve()

    # 1 & 2: walkup od cwd i script path
    starts = [Path.cwd()]
    if script_path:
        starts.append(script_path.parent)

    for start in starts:
        current = start
        while current != current.parent:
            if (current / ".obsidian").is_dir() or (current / ".env").is_file():
                return current
            current = current.parent

    # 3: symlink detection — __dirname w vault-git, .env w vault
    if script_path:
        path_str = str(script_path)
        claude_idx = path_str.find("/.claude/")
        if claude_idx == -1:
            claude_idx = path_str.find("\\.claude\\")
        if claude_idx != -1:
            git_root = Path(path_str[:claude_idx])
            home = Path(os.environ.get("HOME", os.environ.get("USERPROFILE", "")))
            if home.is_dir():
                try:
                    for entry in home.iterdir():
                        claude_link = entry / ".claude"
                        try:
                            if claude_link.is_symlink():
                                target = claude_link.resolve()
                                if target == git_root / ".claude":
                                    if (entry / ".env").is_file() or (entry / ".obsidian").is_dir():
                                        return entry
                        except (OSError, ValueError):
                            pass
                except OSError:
                    pass

    # 4: ostateczny fallback — 4x parent od typowego scripts/skill/skills/.claude/workspace
    if script_path:
        return script_path.parents[4]

    return Path.cwd()


def load_env(workspace=None):
    """Załaduj .env z workspace'u do os.environ (nie nadpisuje istniejących)."""
    if workspace is None:
        workspace = find_workspace()
    env_path = Path(workspace) / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key not in os.environ:
            os.environ[key] = val

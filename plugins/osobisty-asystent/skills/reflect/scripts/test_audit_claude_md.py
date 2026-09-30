#!/usr/bin/env python3
"""Testy audit_claude_md.py. Odpalaj z katalogu scripts/: python3 test_audit_claude_md.py"""

import os
import tempfile
import unittest
from unittest import mock

import audit_claude_md as a


def write(path, text=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.home = tempfile.TemporaryDirectory()  # pusty HOME: globalne skille nie mieszają
        self.env = mock.patch.dict(os.environ, {"HOME": self.home.name})
        self.env.start()
        os.makedirs(os.path.join(self.root, "Zadania"))
        write(os.path.join(self.root, ".claude", "skills", "daily", "SKILL.md"))
        write(os.path.join(self.root, ".claude", "skills", "puls", "SKILL.md"))

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()
        self.home.cleanup()

    def run_audit(self, claude_md):
        write(os.path.join(self.root, ".claude", "CLAUDE.md"), claude_md)
        return a.audit(self.root)

    def section(self, report, title):
        return report.split("## " + title)[1].split("\n## ")[0]

    def test_no_claude_md(self):
        self.assertIn("Brak CLAUDE.md", a.audit(self.root))

    def test_missing_path_reported_existing_not(self):
        write(os.path.join(self.root, "Zadania", "Dashboard.md"))
        r = self.run_audit("`Zadania/Dashboard.md` i `Zadania/Stary.md`")
        sec = self.section(r, "Ścieżki")
        self.assertIn("Zadania/Stary.md", sec)
        self.assertNotIn("Dashboard.md", sec)

    def test_placeholders_and_commands_ignored(self):
        r = self.run_audit("`Zadania/YYYY-MM.md` `Zadania/<osoba>/` `cd Zadania && ls` `.env`")
        self.assertIn("- (brak)", self.section(r, "Ścieżki"))

    def test_unknown_skill(self):
        r = self.run_audit("`/daily` `/puls` `/usuniety` `/aibiz:puls`")
        sec = self.section(r, "Komendy")
        self.assertIn("/usuniety", sec)
        self.assertNotIn("/daily", sec)
        self.assertNotIn("/aibiz:puls", sec)

    def test_skill_count_mismatch(self):
        r = self.run_audit("Mamy 5 skilli.")
        self.assertIn("podaje 5, w `.claude/skills/` jest 2", r)

    def test_skill_count_match(self):
        r = self.run_audit("Mamy 2 skille.")
        self.assertIn("zgodna", self.section(r, "Liczba"))

    def test_undocumented_folder(self):
        os.makedirs(os.path.join(self.root, "Nowy"))
        r = self.run_audit("`Zadania/` opisane")
        sec = self.section(r, "Foldery")
        self.assertIn("Nowy/", sec)
        self.assertNotIn("Zadania/", sec)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.main_script = Path(__file__).resolve().parent.parent / "main.py"

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(self.main_script), *args],
            capture_output=True,
            text=True,
        )

    def test_no_arguments_shows_help(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Available Commands", result.stdout)

    def test_root_help(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("clean-empty-dirs", result.stdout)

    def test_clean_empty_dirs_subcommand(self):
        nested = self.base / "d1" / "d2"
        nested.mkdir(parents=True)

        # Dry run via CLI
        result = self.run_cli("clean-empty-dirs", str(self.base), "-n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Would remove 2 empty directories", result.stdout)
        self.assertTrue(nested.exists())

        # Real deletion via CLI
        result = self.run_cli("clean-empty-dirs", str(self.base))
        self.assertEqual(result.returncode, 0)
        self.assertIn("Removed 2 empty directories", result.stdout)
        self.assertFalse((self.base / "d1").exists())

    def test_clean_empty_dirs_alias(self):
        nested = self.base / "sub"
        nested.mkdir()

        result = self.run_cli("delete-empty-dirs", str(self.base))
        self.assertEqual(result.returncode, 0)
        self.assertIn("Removed 1 empty directory", result.stdout)
        self.assertFalse(nested.exists())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from utils.fs_utils import delete_empty_directories


class TestFSUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_nested_empty_directories(self):
        nested = self.base / "a" / "b" / "c"
        nested.mkdir(parents=True)

        count = delete_empty_directories(self.base, dry_run=False, verbose=False)
        self.assertEqual(count, 3)
        self.assertFalse((self.base / "a").exists())
        self.assertTrue(self.base.exists())

    def test_directory_with_files_preserved(self):
        folder = self.base / "with_files"
        subfolder = folder / "empty_sub"
        subfolder.mkdir(parents=True)
        (folder / "file.txt").write_text("sample content")

        count = delete_empty_directories(self.base, dry_run=False, verbose=False)
        self.assertEqual(count, 1)
        self.assertFalse(subfolder.exists())
        self.assertTrue(folder.exists())
        self.assertTrue((folder / "file.txt").exists())

    def test_dry_run_does_not_delete(self):
        nested = self.base / "a" / "b" / "c"
        nested.mkdir(parents=True)

        count = delete_empty_directories(self.base, dry_run=True, verbose=False)
        self.assertEqual(count, 3)
        self.assertTrue(nested.exists())

    def test_delete_root_option(self):
        empty_root = self.base / "target_root"
        empty_root.mkdir()

        # Without delete_root
        count = delete_empty_directories(empty_root, delete_root=False, verbose=False)
        self.assertEqual(count, 0)
        self.assertTrue(empty_root.exists())

        # With delete_root
        count = delete_empty_directories(empty_root, delete_root=True, verbose=False)
        self.assertEqual(count, 1)
        self.assertFalse(empty_root.exists())

    def test_invalid_path(self):
        non_existent = self.base / "does_not_exist"
        count = delete_empty_directories(non_existent, verbose=False)
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()

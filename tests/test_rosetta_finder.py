#   ---------------------------------------------------------------------------------
#   Copyright (c) Microsoft Corporation. All rights reserved.
#   Licensed under the MIT License. See LICENSE in project root for information.
#   ---------------------------------------------------------------------------------
"""This is a sample python file for testing functions from the source code."""
from __future__ import annotations

from rosetta_finder import RosettaFinder, RosettaBinary

import unittest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Literal


class TestRosettaBinary(unittest.TestCase):
    def test_from_filename_valid(self):
        dirname = "/path/to/rosetta/bin"

        valid_filenames = [
            "rosetta_scripts.linuxgccrelease",
            "rosetta_scripts.mpi.macosclangdebug",
            "rosetta_scripts.static.linuxgccrelease",
            "rosetta_scripts.default.macosclangdebug",
            "rosetta_scripts.cxx11threadserialization.linuxgccrelease",  # Docker serial
            "rosetta_scripts",  # Docker serial
        ]

        for filename in valid_filenames:
            with self.subTest(filename=filename):
                rosetta_binary = RosettaBinary.from_filename(dirname, filename)
                self.assertEqual(rosetta_binary.dirname, dirname)
                self.assertEqual(rosetta_binary.binary_name, "rosetta_scripts")
                self.assertIn(rosetta_binary.mode, [None, "mpi", "static", "default", "cxx11threadserialization"])
                self.assertIn(rosetta_binary.os, [None, "linux", "macos"])
                self.assertIn(rosetta_binary.compiler, [None, "gcc", "clang"])
                self.assertIn(rosetta_binary.release, [None, "release", "debug"])
                # Test filename property
                self.assertEqual(rosetta_binary.filename, filename)
                # Test full_path property
                expected_full_path = os.path.join(dirname, filename)
                self.assertEqual(rosetta_binary.full_path, expected_full_path)

    def test_from_filename_invalid(self):
        dirname = "/path/to/rosetta/bin"

        invalid_filenames = [
            "rosetta_scripts.windowsgccrelease",  # Invalid OS
            "rosetta_scripts.linuxgcc",  # Missing release
            "rosetta_scripts.mpi.linuxgccbeta",  # Invalid release
            "rosetta_scripts.linuxgccrelease.exe",  # Extra extension
            "rosetta_scripts.cxx11threadserialization..linuxgccrelease",  # Typo
            "rosetta_scripts.",  # Ending dot
            "/rosetta_scripts",  # Leading slash
        ]

        for filename in invalid_filenames:
            with self.subTest(filename=filename):
                with self.assertRaises(ValueError):
                    RosettaBinary.from_filename(dirname, filename)


class TestRosettaFinder(unittest.TestCase):
    @patch("os.environ")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.iterdir")
    def test_find_binary_success(self, mock_iterdir, mock_is_dir, mock_exists, mock_environ):
        # Set up the mocks
        mock_environ.get.return_value = "/mock/rosetta/bin"  # Mock ROSETTA_BIN
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Mock files in the directory
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.name = "rosetta_scripts.linuxgccrelease"

        mock_iterdir.return_value = [mock_file]

        finder = RosettaFinder()
        rosetta_binary = finder.find_binary("rosetta_scripts")

        self.assertIsInstance(rosetta_binary, RosettaBinary)
        self.assertEqual(rosetta_binary.binary_name, "rosetta_scripts")
        self.assertEqual(rosetta_binary.mode, None)
        self.assertEqual(rosetta_binary.os, "linux")
        self.assertEqual(rosetta_binary.compiler, "gcc")
        self.assertEqual(rosetta_binary.release, "release")
        self.assertEqual(rosetta_binary.dirname, "/mock/rosetta/bin")
        expected_full_path = "/mock/rosetta/bin/rosetta_scripts.linuxgccrelease"
        self.assertEqual(rosetta_binary.full_path, expected_full_path)

    @patch("os.environ")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.iterdir")
    def test_find_binary_not_found(self, mock_iterdir, mock_is_dir, mock_exists, mock_environ):
        # Set up the mocks
        mock_environ.get.return_value = "/mock/rosetta/bin"  # Mock ROSETTA_BIN
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Mock empty directory
        mock_iterdir.return_value = []

        finder = RosettaFinder()
        with self.assertRaises(FileNotFoundError):
            finder.find_binary("rosetta_scripts")

    @patch("sys.platform", "linux")
    def test_unsupported_os(self):
        with patch("sys.platform", "win32"):
            with self.assertRaises(EnvironmentError):
                RosettaFinder()


if __name__ == "__main__":
    unittest.main()

#   ---------------------------------------------------------------------------------
#   Copyright (c) Microsoft Corporation. All rights reserved.
#   Licensed under the MIT License. See LICENSE in project root for information.
#   ---------------------------------------------------------------------------------
"""
This is a configuration file for pytest containing customizations and fixtures.

In VSCode, Code Coverage is recorded in config.xml. Delete this file to reset reporting.
"""

from __future__ import annotations

import os
from typing import List
import warnings

import pytest
from _pytest.nodes import Item


def pytest_collection_modifyitems(items: list[Item]):
    for item in items:
        if "spark" in item.nodeid:
            item.add_marker(pytest.mark.spark)
        elif "_int_" in item.nodeid:
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def unit_test_mocks(monkeypatch: None):
    """Include Mocks here to execute all commands offline and fast."""
    pass


def no_rosetta():
    import subprocess

    result = subprocess.run(
        ["whichrosetta", "rosetta_scripts"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    # Check that the command was successful
    has_rosetta_installed = "rosetta_scripts" in result.stdout
    warnings.warn(UserWarning(f"Rosetta Installed: {has_rosetta_installed} - {result.stdout}"))
    return not has_rosetta_installed


def github_rosetta_test():
    return os.environ.get("GITHUB_ROSETTA_TEST", "NO") == "YES"

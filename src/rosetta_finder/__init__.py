#   -------------------------------------------------------------
#   Copyright (c) Microsoft Corporation. All rights reserved.
#   Licensed under the MIT License. See LICENSE in project root for information.
#   -------------------------------------------------------------
"""Python Package Template"""
from __future__ import annotations
from .rosetta_finder import RosettaBinary, RosettaFinder, main

__all__ = ["RosettaFinder", "RosettaBinary", "main"]

__version__ = "0.0.2"

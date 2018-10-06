# Unit tests for cleaner
#
# SPDX-License-Identifier: GPL-2.0

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scorpy import core

import pytest

def test_requireversion_major():
  assert core.requireVersion(0)

def test_requireversion_major_and_minor():
  assert core.requireVersion(0, 5)

def test_requireversion_full():
  assert core.requireVersion(0, 5, 0)

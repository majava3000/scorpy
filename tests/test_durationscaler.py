# Unit tests for durationScaler
#
# SPDX-License-Identifier: GPL-2.0
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scorpy import core
from scorpy import testing

import pytest

@pytest.fixture
def in1():
  return testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A...B...C...D..."))

@pytest.fixture
def single():
  return testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A")) 

# single unit input, 0.2 scaler
def test_dscaler_annihilation(single):
  r = core.durationScaler(single, 0.2)
  # this will result in an empty sequence
  assert testing.segiterToShortcode(r) == ""

def test_dscaler_unity(single):
  r = core.durationScaler(single, 1)
  assert testing.segiterToShortcode(r) == "A"

# same as example1
def test_dscaler_identity(in1):
  r = core.durationScaler(in1, 1)
  assert testing.segiterToShortcode(r) == testing.segiterToShortcode(in1)

def test_dscaler_doublesingle(single):
  r = core.durationScaler(single, 2)
  assert testing.segiterToShortcode(r) == "A."

def test_dscaler_example2(in1):
  r = core.durationScaler(in1, 2)
  assert testing.segiterToShortcode(r) == "A.......B.......C.......D......."

def test_dscaler_example3(in1):
  # 6 = 4 * 1.5
  r = core.durationScaler(in1, 1.5)
  assert testing.segiterToShortcode(r) == "A.....B.....C.....D....."

def test_dscaler_example4(in1):
  # 2 = 4 * 0.5
  r = core.durationScaler(in1, 0.5)
  assert testing.segiterToShortcode(r) == "A.B.C.D."

def test_dscaler_example5(in1):
  # TODO: potential miscalculation here
  r = core.durationScaler(in1, 1/3.0)
  assert testing.segiterToShortcode(r) == "ABCD."

def test_dscaler_example6(in1):
  # TODO: potential miscalculation here
  r = core.durationScaler(in1, 1/6.0)
  assert testing.segiterToShortcode(r) == "BD"

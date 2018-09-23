# Unit tests for cleaner
#
# SPDX-License-Identifier: GPL-2.0
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scorpy import core
from scorpy import testing

import pytest

# this allows us to use symbols as is, without messing stuff us. only useful
# for examples though
B = 66
Y = 89
n = 110

@pytest.fixture
def input_():
  return testing.makeSimpleTrack('input', testing.shortcodeToSegiter("00110.1.0.01.111100000101"))

def test_cleaner_plain(input_):
  #  input: 00110.1.0.01.111100000101
  # result: 0.1.0.1.0..1.....0....101
  r = core.cleaner(input_)
  assert testing.segiterToShortcode(r) == "0.1.0.1.0..1.....0....101"

def test_tester_short():
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("0"))
  #  input: 0
  # result: 0
  r = core.cleaner(input_)
  assert testing.segiterToShortcode(r) == "0"

def test_tester_short2():
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("0."))
  #  input: 0.
  # result: 0.
  r = core.cleaner(input_)
  assert testing.segiterToShortcode(r) == "0."

def test_tester_shortreps():
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("00"))
  #  input: 00
  # result: 0.
  r = core.cleaner(input_)
  assert testing.segiterToShortcode(r) == "0."

def test_tester_longreps():
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("0000000000000000"))
  #  input: 0000000000000000
  # result: 0...............
  r = core.cleaner(input_)
  assert testing.segiterToShortcode(r) == "0..............."

def test_tester_long_and_invert():
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("00000000000000001"))
  #  input: 00000000000000001
  # result: 0...............1
  r = core.cleaner(input_)
  assert testing.segiterToShortcode(r) == "0...............1"

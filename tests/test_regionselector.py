# Unit tests for regionSelector
#
# SPDX-License-Identifier: GPL-2.0

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scorpy import core
from scorpy import testing

import pytest

@pytest.fixture
def input_():
  return testing.makeSimpleTrack('input', testing.shortcodeToSegiter("ABCD.E.F.G..H..I.."))

#   input: ABCD.E.F.G..H..I..
# result1: A
# result2: DE
# result3: G
# result4: ABCD.E.F.G..H..I..
# result4: I


def test_regionselector_example1(input_):
  #  input: ABCD.E.F.G..H..I..
  # result: A
  r = core.regionSelector(input_, 0, 1)
  assert testing.segiterToShortcode(r) == "A"

def test_regionselector_example2(input_):
  #  input: ABCD.E.F.G..H..I..
  # result: DE
  r = core.regionSelector(input_, 4, 6)
  assert testing.segiterToShortcode(r) == "DE"

def test_regionselector_example3(input_):
  #  input: ABCD.E.F.G..H..I..
  # result: G
  r = core.regionSelector(input_, 10, 11)
  assert testing.segiterToShortcode(r) == "G"

def test_regionselector_example4(input_):
  #  input: ABCD.E.F.G..H..I..
  # result: ABCD.E.F.G..H..I..
  r = core.regionSelector(input_, 0, 100)
  assert testing.segiterToShortcode(r) == testing.segiterToShortcode(input_)

def test_regionselector_example5(input_):
  #  input: ABCD.E.F.G..H..I..
  # result: I
  r = core.regionSelector(input_, 17, 100)
  assert testing.segiterToShortcode(r) == "I"

# all empty matches will be short-circuited, so no need to test others
def test_regionselector_empty(input_):
  #  input: ABCD.E.F.G..H..I..
  # result: 
  r = core.regionSelector(input_, 0, 0)
  assert testing.segiterToShortcode(r) == ""

def test_regionselector_nonempty_mid(input_):
  #  input: ABCD.E.F.G..H..I..
  # result: G
  r = core.regionSelector(input_, 10, 11)
  assert testing.segiterToShortcode(r) == "G"

def test_regionselector_nonempty_mid2(input_):
  #  input: ABCD.E.F.G..H..I..
  # result: G.
  r = core.regionSelector(input_, 10, 12)
  assert testing.segiterToShortcode(r) == "G."

def test_regionselector_nonempty_mid3(input_):
  #  input: ABCD.E.F.G..H..I..
  # result: G..
  r = core.regionSelector(input_, 9, 12)
  assert testing.segiterToShortcode(r) == "G.."

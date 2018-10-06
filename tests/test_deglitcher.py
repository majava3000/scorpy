# Unit tests for deglitcher
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
  return testing.makeSimpleTrack('input', testing.shortcodeToSegiter("ABC.D.E..F..G...H..I..."))

def test_deglicher_zero(input_):
  #   input: ABC.D.E..F..G...H..I...
  #  result: ABC.D.E..F..G...H..I...
  r = core.deglitcher(input_, 0)
  assert testing.segiterToShortcode(r) == "ABC.D.E..F..G...H..I..."

def test_deglitcher_default(input_):
  # threshold=1, A and B will be merged forward into C
  #   input: ABC.D.E..F..G...H..I...
  #  result: C...D.E..F..G...H..I...
  r = core.deglitcher(input_)
  assert testing.segiterToShortcode(r) == "C...D.E..F..G...H..I..."

def test_deglitcher_trailingshort():
  # threshold=1, trailing should be unmodified
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("AB.A"))
  #   input: AB.A
  #  result: B..A
  r = core.deglitcher(input_)
  assert testing.segiterToShortcode(r) == "B..A"

def test_deglitcher_single():
  # threshold=1, no modification
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A"))
  #   input: A
  #  result: A
  r = core.deglitcher(input_)
  assert testing.segiterToShortcode(r) == "A"

def test_deglitcher_single2():
  # threshold=1, no modification
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A."))
  #   input: A.
  #  result: A.
  r = core.deglitcher(input_)
  assert testing.segiterToShortcode(r) == "A."

def test_deglitcher_all_under_threshold(input_):
  #   input: ABC.D.E..F..G...H..I...
  #  result: I......................
  r = core.deglitcher(input_, 4)
  assert testing.segiterToShortcode(r) == "I......................"

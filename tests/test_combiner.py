# Unit tests for combiner
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
  return testing.makeSimpleTrack('in1', testing.shortcodeToSegiter("A...B...C..."))

@pytest.fixture
def in2():
  return testing.makeSimpleTrack('in2', testing.shortcodeToSegiter("A..B..C..D.."))

@pytest.fixture
def in3():
  return testing.makeSimpleTrack('in3', testing.shortcodeToSegiter("A.B.C.D.A.B."))

def test_combiner_identity1(in1):
  r = core.combiner(in1)
  assert testing.segiterToShortcode(r) == "A...B...C..."

# single input, single min dur input
def test_combiner_single1():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A"))
  r = core.combiner(in1)
  assert testing.segiterToShortcode(r) == "A"

# single input, single >1 dur input
def test_combiner_single2():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A."))
  r = core.combiner(in1)
  assert testing.segiterToShortcode(r) == "A."

# single input, multiple single duration inputs
def test_combiner_single3():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("ABCDABCD"))
  r = core.combiner(in1)
  assert testing.segiterToShortcode(r) == "ABCDABCD"

# two inputs, both minimum dur, same value
def test_combiner_short1():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A"))
  in2 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A"))
  r = core.combiner(in1, in2)
  assert testing.segiterToShortcode(r) == "[AA]"

# two inputs, both minimum dur, diff value
# check that order is correct
def test_combiner_short2():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A"))
  in2 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("B"))
  r = core.combiner(in1, in2)
  assert testing.segiterToShortcode(r) == "[AB]"

# two inputs, both minimum dur, multiple segments, rep values, diff values
def test_combiner_medium1():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("AA"))
  in2 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("BB"))
  r = core.combiner(in1, in2)
  assert testing.segiterToShortcode(r) == "[AB][AB]"

# two inputs, both minimum dur, multiple segments, rep values, alt values
def test_combiner_medium2():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("AB"))
  in2 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("BA"))
  r = core.combiner(in1, in2)
  assert testing.segiterToShortcode(r) == "[AB][BA]"

# single split by two
def test_combiner_split1():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A."))
  in2 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("BB"))
  r = core.combiner(in1, in2)
  assert testing.segiterToShortcode(r) == "[AB][AB]"

# single split by two
def test_combiner_split2():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A."))
  in2 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("AB"))
  r = core.combiner(in1, in2)
  assert testing.segiterToShortcode(r) == "[AA][AB]"

# single split by two
def test_combiner_split3():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A.."))
  in2 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("AB."))
  r = core.combiner(in1, in2)
  assert testing.segiterToShortcode(r) == "[AA][AB]."

# single split by two, trailing short
def test_combiner_split4():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A.."))
  in2 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("A.B"))
  r = core.combiner(in1, in2)
  assert testing.segiterToShortcode(r) == "[AA].[AB]"

# documentation example
def test_combiner_example(in1, in2, in3):
  r = core.combiner(in1, in2, in3)
  assert testing.segiterToShortcode(r) == "[AAA].[AAB][ABB][BBC].[BCD].[CCA][CDA][CDB]."

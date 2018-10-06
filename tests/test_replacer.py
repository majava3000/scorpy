# Unit tests for replacer
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
A = 65
B = 66
Y = 89
n = 110

@pytest.fixture
def input_():
  return testing.makeSimpleTrack('input', testing.shortcodeToSegiter("ABCA.B.C.A..B..C..A..."))

def test_replacer_set_dur_to_one(input_):
  #  input: ABCA.B.C.A..B..C..A...
  # result: ABCABCABCA
  r = core.replacer(input_, core.FILTER_ALWAYS_TRUE, lambda _, v: ( (1, v), ) )
  assert testing.segiterToShortcode(r) == "ABCABCABCA"

def test_replacer_always_false_filter(input_):
  #  input: ABCA.B.C.A..B..C..A...
  # result: ABCA.B.C.A..B..C..A...
  r = core.replacer(input_, core.FILTER_ALWAYS_FALSE, lambda _, v: ( (1, v), ) )
  assert testing.segiterToShortcode(r) == "ABCA.B.C.A..B..C..A..."

# rest of the tests follow the examples
def test_replacer_example2(input_):
  #  input: ABCA.B.C.A..B..C..A...
  # result: ABCAnBnCnAn.Bn.Cn.An..
  # split segments into two, conserving duration
  r = core.replacer(input_, lambda dur, _: (dur >= 2), lambda dur, v: ( (1, v), (dur-1, n) ) )
  assert testing.segiterToShortcode(r) == "ABCAnBnCnAn.Bn.Cn.An.."

def test_replacer_example3(input_):
  #  input: ABCA.B.C.A..B..C..A...
  # result: ABn.CA.B.n.C.A..B..n.C..A...
  # insert a special segment after each matching one
  r = core.replacer(input_, lambda _, v: (v == B), lambda dur, v: ( (dur, v), (2, n) ) )
  assert testing.segiterToShortcode(r) == "ABn.CA.B.n.C.A..B..n.C..A..."

def test_replacer_example4(input_):
  #  input: ABCA.B.C.A..B..C..A...
  # result: BCB.C.B..C..
  # remove segments with specific value
  r = core.replacer(input_, lambda _, v: (v == A), lambda *_: tuple() )
  assert testing.segiterToShortcode(r) == "BCB.C.B..C.."

# slightly evil
counter =1
def test_replacer_example5(input_):
  #  input: ABCA.B.C.A..B..C..A...
  # result: ABCn.B.C.A..B..C..n...
  # replace every second matching segment
  def repEverySecond(dur, _):
      global counter
      counter += 1
      if counter % 2 == 0:
          # do not modify segment
          return core.VALUE_PASSTHROUGH
      return ( (dur, n), )
  r = core.replacer(input_, lambda _, v: (v == A), repEverySecond )
  assert testing.segiterToShortcode(r) == "ABCn.B.C.A..B..C..n..."

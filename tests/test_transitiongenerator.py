# Unit tests for transitionGenerator
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
  return testing.makeSimpleTrack('input', testing.shortcodeToSegiter("0.R0R0.R0..R0...R0...."))

u = 117
d = 100
R = 82

def test_regionselector_example1(input_):
  #  input: 0.R0R0.R0..R0...R0....
  # result: duR0RduRd0uRd0.uRd0..u
  # equal-weight, minimum durations
  r = core.transitionGenerator(input_, 0, d, u, 1, 1)
  assert testing.segiterToShortcode(r) == "duR0RduRd0uRd0.uRd0..u"

def test_regionselector_example2(input_):
  #  input: 0.R0R0.R0..R0...R0....
  # result: duR0RduRdu.Rd0u.Rd0.u.
  # post-duration is twice as long as pre
  r = r2 = core.transitionGenerator(input_, 0, d, u, 1, 2)
  assert testing.segiterToShortcode(r) == "duR0RduRdu.Rd0u.Rd0.u."

def test_regionselector_example3(input_):
  #  input: 0.R0R0.R0..R0...R0....
  # result: duR0RduRdu.Rd.u.Rd.0u.
  # equal weights, but longer ones, latter will win in odd-tie ins
  r = core.transitionGenerator(input_, 0, d, u, 2, 2)
  assert testing.segiterToShortcode(r) == "duR0RduRdu.Rd.u.Rd.0u."

def test_regionselector_allzero():
  #  input: 0.....................
  # result: d0...................u
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("0....................."))
  r = core.transitionGenerator(input_, 0, d, u, 1, 1)
  assert testing.segiterToShortcode(r) == "d0...................u"

def test_regionselector_allrun():
  #  input: R.....................
  # result: R.....................
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("R....................."))
  r = core.transitionGenerator(input_, 0, d, u, 1, 1)
  assert testing.segiterToShortcode(r) == "R....................."

def test_regionselector_allzero_short():
  #  input: 0
  # result: 0
  input_ = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("0"))
  r = core.transitionGenerator(input_, 0, d, u, 1, 1)
  assert testing.segiterToShortcode(r) == "0"

# This won't work. Issue 26 created for this.
# def test_regionselector_only_pre(input_):
#   #  input: 0.R0R0.R0..R0...R0....
#   # result: 0
#   r = core.transitionGenerator(input_, 0, d, u, 1, 0)
#   assert testing.segiterToShortcode(r) == "d0RdRd0Rd0.Rd0..Rd0..."

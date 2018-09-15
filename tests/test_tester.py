import sys
sys.path += [".."]

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
  return testing.makeSimpleTrack('input', testing.shortcodeToSegiter("ABCA.B.C.A..B..C.."))

def test_tester_plain(input_):
  #   input: ABCA.B.C.A..B..C..
  # result1: 0000.1.0.0..0..0..
  r = core.tester(input_, lambda dur, v: (v == B and dur == 2))
  assert testing.segiterToShortcode(r) == "0000.1.0.0..0..0.."

def test_tester_plain_replace(input_):
  #   input: ABCA.B.C.A..B..C..
  # result2: nnnn.Y.n.n..n..n..
  r = core.tester(input_, lambda dur, v: (v == B and dur == 2), (Y, n))
  assert testing.segiterToShortcode(r) == "nnnn.Y.n.n..n..n.."

def test_tester_passthrough_positive(input_):
  #   input: ABCA.B.C.A..B..C..
  # result3: nnnA.B.C.n..n..n..
  r = core.tester(input_, lambda dur, v: (dur == 2), (core.VALUE_PASSTHROUGH, n))
  assert testing.segiterToShortcode(r) == "nnnA.B.C.n..n..n.."

def test_tester_passthrough_negative(input_):
  #   input: ABCA.B.C.A..B..C..
  # result4: ABCY.Y.Y.A..B..C..
  r = core.tester(input_, lambda dur, v: (dur == 2), (Y, core.VALUE_PASSTHROUGH))
  assert testing.segiterToShortcode(r) == "ABCY.Y.Y.A..B..C.."

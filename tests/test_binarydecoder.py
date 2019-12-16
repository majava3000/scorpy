# Unit tests for binaryDecoder
#
# SPDX-License-Identifier: GPL-2.0
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scorpy import core
from scorpy import testing

import pytest

def test_bindec_identity1():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("_"))
  r = core.binaryDecoder(in1)
  assert testing.segiterToShortcode(r) == "_"


def test_bindec_identity2():
  in1 = testing.makeSimpleTrack('input', testing.shortcodeToSegiter("0."))
  r = core.binaryDecoder(in1)
  assert testing.segiterToShortcode(r) == "0."

# documentation example
def test_bindec_example():
  bit2 = testing.makeSimpleTrack('bit2', testing.shortcodeToSegiter("0...1...001."))
  bit1 = testing.makeSimpleTrack('bit1', testing.shortcodeToSegiter("0.1.0.1.001."))
  bit0 = testing.makeSimpleTrack('bit0', testing.shortcodeToSegiter("01010101001."))

  r = core.binaryDecoder(core.combiner(bit2, bit1, bit0))
  assert testing.segiterToShortcode(r) == "01234567007."

def test_single_twodim():
  bit1 = testing.makeSimpleTrack('bit1', testing.shortcodeToSegiter("0.."))
  bit0 = testing.makeSimpleTrack('bit0', testing.shortcodeToSegiter("0.."))

  r = core.binaryDecoder(core.combiner(bit1, bit0))
  assert testing.segiterToShortcode(r) == "0.."

def test_single_threedim():
  bit2 = testing.makeSimpleTrack('bit2', testing.shortcodeToSegiter("1.."))
  bit1 = testing.makeSimpleTrack('bit1', testing.shortcodeToSegiter("1.."))
  bit0 = testing.makeSimpleTrack('bit0', testing.shortcodeToSegiter("1.."))

  r = core.binaryDecoder(core.combiner(bit2, bit1, bit0))
  assert testing.segiterToShortcode(r) == "7.."

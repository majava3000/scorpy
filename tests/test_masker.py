# Unit tests for masker
#
# SPDX-License-Identifier: GPL-2.0
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scorpy import core
from scorpy import testing

import pytest

v = 118

def test_masker_short1():
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("1"))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("0"))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "1"

def test_masker_short2():
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("1"))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("1"))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "v"

def test_masker_short3():
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("1."))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("0."))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "1."

def test_masker_short4():
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("1."))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("1."))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "v."

def test_masker_identity_negative1():
  # tests with clean mask
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("A..B..C..D"))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("0........."))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "A..B..C..D"

def test_masker_identity_negative2():
  # tests with max dirty mask
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("A..B..C..D"))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("0000000000"))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "AAABBBCCCD"

def test_masker_identity_positive1():
  # clean mask
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("A..B..C..D"))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("1........."))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "v..v..v..v"

def test_masker_identity_positive2():
  # max dirty mask
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("A..B..C..D"))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("1111111111"))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "vvvvvvvvvv"

def test_masker_example():
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("A..B..C..D"))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("0.1....0.."))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "A.vv..vC.D"

def test_masker_example2():
  data = testing.makeSimpleTrack('data', testing.shortcodeToSegiter("A..B..C..D."))
  mask = testing.makeSimpleTrack('mask', testing.shortcodeToSegiter("101....0..1"))
  r = core.masker(data, mask, v)
  assert testing.segiterToShortcode(r) == "vAvv..vC.Dv"

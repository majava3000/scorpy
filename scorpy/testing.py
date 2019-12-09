#
# Testing support functions
#
# SPDX-License-Identifier: GPL-2.0
#

import scorpy.core as core

import types

# convert a shorthand signal notation into segiter suitable to be used with
# either BinaryTrack or UnsignedTrack constructor/segsegments (depending on
# values). By default each input code corresponds to duration of 1, but can be
# overridden with uniform expansion factor
#
# Input:
# - '0' and '1' represented as integers 0 and 1 (default duration of
#   duractionFactor)
# - Any other character is converted into ordinal representation (ASCII only)
# - '.' extends the duration of previous value by duractionFactor
#
# NOTE:
# - Input 'AA' is not the same as 'A.'. First encodes two segments of same
#   duration, while latter encodes a single segment with extended duration.
#
# Returns an segiter from the data
# TODO: Support multidimensional shortcodes
def shortcodeToSegiter(str, durationFactor=1):
  # this will be a list of [val, count] entries (RLE with C,V convention)
  ret = []
  for c in str:
    if c == '.':
      # repeat of the previous code
      # TODO: convert into a suitable exception instead
      assert(len(ret) > 0) # must have something to repeat
      ret[-1][0] += durationFactor
      continue
    if c in "01":
      ret.append([durationFactor, ord(c)-ord('0')])
    else:
      ret.append([durationFactor, ord(c)])
  return iter(ret)

# given value in shortcode, return char that represents it
def shortcodeValueToChar(v):
  if v in range(10):
    v += ord('0')
  v = chr(v)
  return v

# Given segiter, return shortcode string from it
# No duration reduction is supported by this encoder
# Multidimensional output is supported by grouping with braces
def segiterToShortcode(segiter):
  # 0 and 1 mapped into '0' and '1'
  # rest mapped via chr
  # single segment duration encoded with repeating dots
  ret = []
  for comps in segiter:
    dur = None
    if len(comps) == 2:
      dur, v = comps
      #print(dur, v)
      # if v in (0, 1):
      #   v += ord('0')
      # v = chr(v)
      ret.append(shortcodeValueToChar(v))
    else:
      # multidimensional shortcode
      dur, values = comps[0], comps[1:]
      vStr = ''.join(map(shortcodeValueToChar, values))
      ret.append("[%s]" % vStr)

    for _ in range(dur-1):
      ret.append(".")

  return ''.join(ret)

# make a single line describing the wavedrom description of the track
# 0-1 are converted to 0 and 1, emitted as data literals
# if zeroAndOneAreSpecial is set, then they're not emitted via data
# format mechanism, otherwise numbers go via char conversion
def segiterToWavedrom(segiter, name, zeroAndOneAreSpecial=True):
  # we'll collect the wave and data part separately
  # wave will not contain the z prefix nor suffix at this point
  wave = []
  # data will contain only the non A-Bs
  data = []
  isMultidim = False
  for comps in segiter:
    if len(comps) == 2:
      # single dimension segiter
      dur, v = comps
      if v < 2 and zeroAndOneAreSpecial:
        # emit 0 or 1, no data
        wave.append(chr(ord('0') + v))
      elif v < 10:
        # numeric value
        wave.append('=')
        data.append(chr(ord('0') + v))
      else:
        wave.append('=')
        data.append(chr(v))
      while dur > 1:
        wave.append('.')
        dur -= 1
    else:
      isMultidim = True
      dur, values = comps[0], comps[1:]
      # TODO: replace 0/1 data with ordinal of '0' and '1'
      # multidimensional track (assuming A, B, C here, 0 or 1 not supported)
      vStr = ''.join(map(chr, comps[1:]))
      wave.append('=')
      data.append(vStr)
      while dur > 1:
        wave.append('.')
        dur -= 1
  wave = ''.join(wave)
  data = "', '".join(data)

  # the z prefix and suffix are added here
  ret = "{ name: '%s', wave: 'z%sz'" % (name, wave)
  if len(data) > 0:
    ret += ", data: ['%s']" % data
  ret += "},"

  return ret

# TODO: add support for inputTrack as tuple to indicate multiple input
#       mode (also document this function and what the expected types
#       are since existing protocol is single inputTrack and multiple results)
def resultAsWavedrom(inputTrack, resultTracks, label=None, useNarrow=True, combineOutputs=False, zeroAndOneAreSpecial=3):
  ret = ['{signal: [']
  inputZeroAndOneAreSpecial = zeroAndOneAreSpecial & 1 > 0
  resultZeroAndOneAreSpecial = zeroAndOneAreSpecial & 2 > 0
  if type(inputTrack) in (types.ListType, types.TupleType):
    for i in inputTrack:
      ret.append('  '+segiterToWavedrom(i, i.name, inputZeroAndOneAreSpecial))
  else:
    ret.append('  '+segiterToWavedrom(inputTrack, inputTrack.name, inputZeroAndOneAreSpecial))
  ret.append(r'  {},')
  if combineOutputs:
    ret.append(r"  ['result',")
  for rIndex in range(len(resultTracks)):
    rt = resultTracks[rIndex]
    # default to 'r' as the output name if dealing with segiters instead
    # of tracks
    n = "r"
    # if multiple outputs, use r0.. format instead
    if len(resultTracks) > 1:
      n = "r%u" % rIndex
    if hasattr(rt, 'name'):
      n = rt.name
    ret.append('  '+segiterToWavedrom(rt, n, resultZeroAndOneAreSpecial))
  labelText = ''
  if label is not None:
    labelText = ", text: '%s'" % label
  configText = "  config: { skin: 'default' },\n"
  if useNarrow:
    configText = "  config: { skin: 'narrow' },\n"
  if combineOutputs:
    ret.append(r"  ],")
  ret.append("""  ],
  head: { tick: -1%s },
%s}
""" % (labelText, configText))
  return '\n'.join(ret)

def makeSimpleTrack(label, segiter):
  return core.UnsignedTrack(label, 1, 8, fromSegiter=segiter)

#
# Testing support functions
#
# SPDX-License-Identifier: GPL-2.0
#

import scorpy.core as core

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

# Given segiter, return shortcode string from it
# No duration reduction is supported by this encoder
def segiterToShortcode(segiter):
  # 0 and 1 mapped into '0' and '1'
  # rest mapped via chr
  # single segment duration encoded with repeating dots
  ret = []
  for dur, v in segiter:
    #print(dur, v)
    if v in (0, 1):
      v += ord('0')
    v = chr(v)
    ret.append(v)
    for _ in range(dur-1):
      ret.append(".")
  return ''.join(ret)

# make a single line describing the wavedrom description of the track
# 0-1 are converted to 0 and 1, emitted as data literals
def segiterToWavedrom(segiter, name):
  # we'll collect the wave and data part separately
  # wave will not contain the z prefix nor suffix at this point
  wave = []
  # data will contain only the non A-Bs
  data = []
  for dur, v in segiter:
    if v < 2:
      # emit 0 or 1, no data
      wave.append(chr(ord('0') + v))
    else:
      wave.append('=')
      data.append(chr(v))
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
def resultAsWavedrom(inputTrack, resultTracks, label=None):
  ret = ['{signal: [']
  ret.append('  '+segiterToWavedrom(inputTrack, inputTrack.name))
  ret.append(r'  {},')
  for rt in resultTracks:
    ret.append('  '+segiterToWavedrom(rt, rt.name))
  labelText = ''
  if label is not None:
    labelText = ", text: '%s'" % label
  ret.append("""  ],
  head: { tick: -1%s },
  config: { skin: 'narrow' },
}
""" % labelText)
  return '\n'.join(ret)

def makeSimpleTrack(label, segiter):
  return core.UnsignedTrack(label, 1, 8, fromSegiter=segiter)

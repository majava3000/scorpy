#!/usr/bin/env python
#
# binaryDecoder example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    name = 'binaryDecoder'
    args = getArgs(name)

    bit2 = makeSimpleTrack('bit2', shortcodeToSegiter("0...1...001."))
    bit1 = makeSimpleTrack('bit1', shortcodeToSegiter("0.1.0.1.001."))
    bit0 = makeSimpleTrack('bit0', shortcodeToSegiter("01010101001."))

    # NOTE: r is multidimensional (3) segiter, so special processing
    # required with the doIt call below (can't use narrow style either)
    # example-start-here
    r = core.binaryDecoder(core.combiner(bit2, bit1, bit0))
    # example-end-here
    # print(tuple(r))
    # right, shortcode-generation is a bit of a problem with numbers.
    # in this case we'd like to emit numbers also for the 0-1 so we'll need some
    # special support for this. perhaps it would be enough to stop default 0-1 -> shortcut generation?

    doIt(args, [bit2, bit1, bit0], [r], name, useNarrow=True, zeroAndOneAreSpecial=1)

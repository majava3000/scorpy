#!/usr/bin/env python
#
# combiner example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    name = 'combiner'
    args = getArgs(name)

    in1 = makeSimpleTrack('in1', shortcodeToSegiter("A...B...C..."))
    in2 = makeSimpleTrack('in2', shortcodeToSegiter("A..B..C..D.."))
    in3 = makeSimpleTrack('in3', shortcodeToSegiter("A.B.C.D.A.B."))

    # NOTE: r is multidimensional (3) segiter, so special processing
    # required with the doIt call below (can't use narrow style either)
    # example-start-here
    r = core.combiner(in1, in2, in3)
    # example-end-here

    # splitResults for wavedrom, otherwise keep in multi-dim
    doIt(args, [in1, in2, in3], r, name, useNarrow=True, splitResults=(args.mode != MODE_SHORTCODE))

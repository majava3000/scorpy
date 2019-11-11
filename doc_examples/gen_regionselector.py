#!/usr/bin/env python
#
# regionSelector example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    name = 'regionSelector'
    args = getArgs(name)

    input_ = makeSimpleTrack('input', shortcodeToSegiter("ABCD.E.F.G..H..I.."))

    # these two anchors are used by the include to actually get the python
    # specific bit of the output. make sure that only one indent level is here
    # (tab=4)
    # example-start-here
    r1 = core.regionSelector(input_, 0, 1)
    r2 = core.regionSelector(input_, 4, 6)
    r3 = core.regionSelector(input_, 10, 11)
    r4 = core.regionSelector(input_, 0, 100)
    r5 = core.regionSelector(input_, 17, 100)
    # example-end-here

    r1 = makeSimpleTrack('r1', r1)
    r2 = makeSimpleTrack('r2', r2)
    r3 = makeSimpleTrack('r3', r3)
    r4 = makeSimpleTrack('r4', r4)
    r5 = makeSimpleTrack('r4', r5)

    # do magic. supports shortcode, wavedrom and docint modes. the label is used
    # only for wavedrom output mode. tuple is necessary for the results
    doIt(args, input_, [r1, r2, r3, r4, r5], name)

#!/usr/bin/env python
#
# tester example generator/code
#
# SPDX-License-Identifier: GPL-2.0

from __future__ import print_function
from common import *

if __name__ == '__main__':
    args = getArgs('tester')

    input_ = makeSimpleTrack('input', shortcodeToSegiter("ABCA.B.C.A..B..C.."))

    # this allows us to use symbols as is, without messing stuff us. only useful
    # for examples though
    B = 66
    Y = 89
    n = 110

    # these two anchors are used by the include to actually get the python
    # specific bit of the output. make sure that only one indent level is here
    # (tab=4)
    # example-start-here
    r1 = core.tester(input_, lambda dur, v: (v == B and dur == 2))
    r2 = core.tester(input_, lambda dur, v: (v == B and dur == 2), (Y, n))
    r3 = core.tester(input_, lambda dur, v: (dur == 2), (core.VALUE_PASSTHROUGH, n))
    r4 = core.tester(input_, lambda dur, v: (dur == 2), (Y, core.VALUE_PASSTHROUGH))
    # example-end-here

    r1 = makeSimpleTrack('result1', r1)
    r2 = makeSimpleTrack('result2', r2)
    r3 = makeSimpleTrack('result3', r3)
    r4 = makeSimpleTrack('result4', r4)

    # do magic. supports shortcode, wavedrom and docint modes. the label is used
    # only for wavedrom output mode. tuple is necessary for the results
    doIt(args, input_, [r1, r2, r3, r4], 'tester')
